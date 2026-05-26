from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.mixed_stream_generator import MixedStreamGenerator
from adapters.telemetry_adapter import TelemetryAdapter
from channel.emulator import ChannelEmulator, ChannelReport
from core.compression import CompressionController
from core.deduplication import DeduplicationController, TelemetryAggregator
from core.importance import ImportanceScorer
from core.metrics import calculate_metrics
from core.packet import CombatPacket, PacketType
from core.reporting import build_report, save_csv_report, save_html_report, save_json_report
from core.scheduler import PriorityScheduler


SCENARIOS: dict[str, dict[str, float | int]] = {
    "normal": {"count": 100, "bandwidth": 2600, "loss": 0.00},
    "overload": {"count": 150, "bandwidth": 1600, "loss": 0.02},
    "emergency": {"count": 200, "bandwidth": 1100, "loss": 0.08},
}


@dataclass(frozen=True)
class ExperimentResult:
    scenario_name: str
    parameters: dict[str, Any]
    prepared_packets: list[CombatPacket]
    baseline_report: ChannelReport
    adaptive_report: ChannelReport
    report: dict[str, Any]


def prepare_packets(packets: list[CombatPacket]) -> list[CombatPacket]:
    scorer = ImportanceScorer()
    compressor = CompressionController()
    telemetry_adapter = TelemetryAdapter()
    prepared: list[CombatPacket] = []

    for packet in packets:
        packet.priority = scorer.score(packet)

        if packet.packet_type in [PacketType.TARGET_COORDS, PacketType.UAV_TELEMETRY]:
            packet = telemetry_adapter.pack(packet)
        else:
            packet = compressor.compress(packet)

        prepared.append(packet)

    return prepared


def run_baseline(packets: list[CombatPacket], bandwidth_bytes: int, loss_probability: float, seed: int) -> ChannelReport:
    channel = ChannelEmulator(
        bandwidth_bytes=bandwidth_bytes,
        loss_probability=loss_probability,
        seed=seed,
    )
    return channel.transmit_with_report(packets)


def run_adaptive(packets: list[CombatPacket], bandwidth_bytes: int, loss_probability: float, seed: int) -> ChannelReport:
    deduplicator = DeduplicationController()
    aggregator = TelemetryAggregator(keep_every=3)
    scheduler = PriorityScheduler()

    optimized = deduplicator.deduplicate(packets)
    optimized = aggregator.aggregate(optimized)
    optimized = scheduler.schedule(optimized)

    channel = ChannelEmulator(
        bandwidth_bytes=bandwidth_bytes,
        loss_probability=loss_probability,
        seed=seed,
    )
    return channel.transmit_with_report(optimized)


def resolve_scenario(
    scenario_name: str,
    count: int | None = None,
    bandwidth: int | None = None,
    loss: float | None = None,
) -> tuple[str, int, int, float]:
    if scenario_name not in SCENARIOS:
        allowed = ", ".join(SCENARIOS.keys())
        raise ValueError(f"unknown scenario '{scenario_name}', allowed: {allowed}")

    scenario = SCENARIOS[scenario_name]
    resolved_count = int(count if count is not None else scenario["count"])
    resolved_bandwidth = int(bandwidth if bandwidth is not None else scenario["bandwidth"])
    resolved_loss = float(loss if loss is not None else scenario["loss"])

    if resolved_count <= 0:
        raise ValueError("count must be positive")
    if resolved_bandwidth <= 0:
        raise ValueError("bandwidth must be positive")
    if not 0.0 <= resolved_loss <= 1.0:
        raise ValueError("loss must be between 0.0 and 1.0")

    return scenario_name, resolved_count, resolved_bandwidth, resolved_loss


def run_experiment(
    scenario_name: str = "overload",
    count: int | None = None,
    bandwidth: int | None = None,
    loss: float | None = None,
    seed: int = 42,
) -> ExperimentResult:
    scenario_name, resolved_count, resolved_bandwidth, resolved_loss = resolve_scenario(
        scenario_name=scenario_name,
        count=count,
        bandwidth=bandwidth,
        loss=loss,
    )

    generator = MixedStreamGenerator(seed=seed)
    packets = generator.generate(count=resolved_count)
    prepared_packets = prepare_packets(packets)

    baseline_report = run_baseline(
        prepared_packets,
        bandwidth_bytes=resolved_bandwidth,
        loss_probability=resolved_loss,
        seed=seed,
    )
    adaptive_report = run_adaptive(
        prepared_packets,
        bandwidth_bytes=resolved_bandwidth,
        loss_probability=resolved_loss,
        seed=seed,
    )

    parameters = {
        "count": resolved_count,
        "bandwidth": resolved_bandwidth,
        "loss": resolved_loss,
        "seed": seed,
    }
    report = build_report(
        scenario_name=scenario_name,
        total_packets=prepared_packets,
        baseline_report=baseline_report,
        adaptive_report=adaptive_report,
        parameters=parameters,
    )

    return ExperimentResult(
        scenario_name=scenario_name,
        parameters=parameters,
        prepared_packets=prepared_packets,
        baseline_report=baseline_report,
        adaptive_report=adaptive_report,
        report=report,
    )


def save_reports(result: ExperimentResult, export_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(export_dir)
    json_path = output_dir / f"{result.scenario_name}_report.json"
    csv_path = output_dir / f"{result.scenario_name}_report.csv"
    html_path = output_dir / f"{result.scenario_name}_report.html"

    save_json_report(result.report, json_path)
    save_csv_report(result.report, csv_path)
    save_html_report(result.report, html_path)

    return {"json": json_path, "csv": csv_path, "html": html_path}


def format_console_report(title: str, total_packets: list[CombatPacket], report: ChannelReport) -> str:
    metrics = calculate_metrics(total_packets, report.delivered_packets)
    lines = [
        "",
        title,
        "=" * len(title),
        f"Всего входных пакетов:           {metrics['total_packets']}",
        f"Доставлено пакетов:              {metrics['delivered_packets']}",
        f"Доля доставки:                   {metrics['delivery_rate']:.3f}",
        f"Критических во входном потоке:   {metrics['total_critical']}",
        f"Критических доставлено:          {metrics['delivered_critical']}",
        f"Доля доставки критических:       {metrics['critical_delivery_rate']:.3f}",
        f"Сырой объём, байт:               {metrics['raw_size']}",
        f"Переданный объём, байт:          {metrics['sent_size']}",
        f"Коэффициент сжатия raw/sent:     {metrics['compression_ratio']:.3f}",
        f"Использовано канала, байт:       {report.used_bandwidth}/{report.bandwidth_bytes}",
        f"Загрузка канала:                 {report.utilization:.3f}",
        f"Отброшено из-за полосы:          {len(report.dropped_by_bandwidth)}",
        f"Потеряно случайно:               {len(report.dropped_by_loss)}",
    ]
    return "\n".join(lines)
