import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.mixed_stream_generator import MixedStreamGenerator
from adapters.telemetry_adapter import TelemetryAdapter
from channel.emulator import ChannelEmulator, ChannelReport
from core.compression import CompressionController
from core.deduplication import DeduplicationController, TelemetryAggregator
from core.importance import ImportanceScorer
from core.metrics import calculate_metrics
from core.packet import CombatPacket, PacketType
from core.reporting import build_report, save_csv_report, save_json_report
from core.scheduler import PriorityScheduler


SCENARIOS = {
    "normal": {"count": 100, "bandwidth": 2600, "loss": 0.00},
    "overload": {"count": 150, "bandwidth": 1600, "loss": 0.02},
    "emergency": {"count": 200, "bandwidth": 1100, "loss": 0.08},
}


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


def print_report(title: str, total_packets: list[CombatPacket], report: ChannelReport) -> None:
    metrics = calculate_metrics(total_packets, report.delivered_packets)

    print("\n" + title)
    print("=" * len(title))
    print(f"Всего входных пакетов:           {metrics['total_packets']}")
    print(f"Доставлено пакетов:              {metrics['delivered_packets']}")
    print(f"Доля доставки:                   {metrics['delivery_rate']:.3f}")
    print(f"Критических во входном потоке:   {metrics['total_critical']}")
    print(f"Критических доставлено:          {metrics['delivered_critical']}")
    print(f"Доля доставки критических:       {metrics['critical_delivery_rate']:.3f}")
    print(f"Сырой объём, байт:               {metrics['raw_size']}")
    print(f"Переданный объём, байт:          {metrics['sent_size']}")
    print(f"Коэффициент сжатия raw/sent:     {metrics['compression_ratio']:.3f}")
    print(f"Использовано канала, байт:       {report.used_bandwidth}/{report.bandwidth_bytes}")
    print(f"Загрузка канала:                 {report.utilization:.3f}")
    print(f"Отброшено из-за полосы:          {len(report.dropped_by_bandwidth)}")
    print(f"Потеряно случайно:               {len(report.dropped_by_loss)}")


def resolve_scenario(args: argparse.Namespace) -> tuple[str, int, int, float]:
    scenario = SCENARIOS[args.scenario]
    count = args.count if args.count is not None else scenario["count"]
    bandwidth = args.bandwidth if args.bandwidth is not None else scenario["bandwidth"]
    loss = args.loss if args.loss is not None else scenario["loss"]
    return args.scenario, count, bandwidth, loss


def main() -> None:
    parser = argparse.ArgumentParser(description="Демонстрация MVP Адаптив-Боец")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="overload", help="готовый профиль канала")
    parser.add_argument("--count", type=int, default=None, help="число входных сообщений")
    parser.add_argument("--bandwidth", type=int, default=None, help="полоса канала за цикл, байт")
    parser.add_argument("--loss", type=float, default=None, help="вероятность случайной потери 0..1")
    parser.add_argument("--seed", type=int, default=42, help="seed для воспроизводимости")
    parser.add_argument("--export-dir", type=Path, default=None, help="папка для JSON/CSV отчёта")
    args = parser.parse_args()

    scenario_name, count, bandwidth, loss = resolve_scenario(args)

    generator = MixedStreamGenerator(seed=args.seed)
    packets = generator.generate(count=count)
    prepared_packets = prepare_packets(packets)

    baseline_report = run_baseline(
        prepared_packets,
        bandwidth_bytes=bandwidth,
        loss_probability=loss,
        seed=args.seed,
    )
    adaptive_report = run_adaptive(
        prepared_packets,
        bandwidth_bytes=bandwidth,
        loss_probability=loss,
        seed=args.seed,
    )

    print("АДАПТИВ-БОЕЦ: демонстрация адаптивного управления информационным потоком")
    print(f"Параметры: scenario={scenario_name}, count={count}, bandwidth={bandwidth}, loss={loss}, seed={args.seed}")

    print_report("Базовая отправка без адаптации", prepared_packets, baseline_report)
    print_report("Адаптивная отправка", prepared_packets, adaptive_report)

    report = build_report(
        scenario_name=scenario_name,
        total_packets=prepared_packets,
        baseline_report=baseline_report,
        adaptive_report=adaptive_report,
        parameters={"count": count, "bandwidth": bandwidth, "loss": loss, "seed": args.seed},
    )

    if args.export_dir is not None:
        json_path = args.export_dir / f"{scenario_name}_report.json"
        csv_path = args.export_dir / f"{scenario_name}_report.csv"
        save_json_report(report, json_path)
        save_csv_report(report, csv_path)
        print(f"\nОтчёты сохранены:")
        print(f"- {json_path}")
        print(f"- {csv_path}")


if __name__ == "__main__":
    main()
