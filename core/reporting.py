import csv
import json
from pathlib import Path
from typing import Any

from channel.emulator import ChannelReport
from core.metrics import calculate_metrics
from core.packet import CombatPacket


def build_report(
    scenario_name: str,
    total_packets: list[CombatPacket],
    baseline_report: ChannelReport,
    adaptive_report: ChannelReport,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    baseline_metrics = calculate_metrics(total_packets, baseline_report.delivered_packets)
    adaptive_metrics = calculate_metrics(total_packets, adaptive_report.delivered_packets)

    return {
        "scenario": scenario_name,
        "parameters": parameters,
        "baseline": _pack_metrics(baseline_metrics, baseline_report),
        "adaptive": _pack_metrics(adaptive_metrics, adaptive_report),
        "delta": _build_delta(baseline_metrics, adaptive_metrics),
    }


def save_json_report(report: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv_report(report: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for mode in ["baseline", "adaptive"]:
        for key, value in report[mode].items():
            rows.append({"scenario": report["scenario"], "mode": mode, "metric": key, "value": value})

    for key, value in report["delta"].items():
        rows.append({"scenario": report["scenario"], "mode": "delta", "metric": key, "value": value})

    with output_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["scenario", "mode", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


def _pack_metrics(metrics: dict[str, Any], report: ChannelReport) -> dict[str, Any]:
    packed = dict(metrics)
    packed.update(
        {
            "used_bandwidth": report.used_bandwidth,
            "bandwidth_bytes": report.bandwidth_bytes,
            "channel_utilization": report.utilization,
            "dropped_by_bandwidth": len(report.dropped_by_bandwidth),
            "dropped_by_loss": len(report.dropped_by_loss),
        }
    )
    return packed


def _build_delta(baseline_metrics: dict[str, Any], adaptive_metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "delivery_rate_gain": adaptive_metrics["delivery_rate"] - baseline_metrics["delivery_rate"],
        "critical_delivery_rate_gain": adaptive_metrics["critical_delivery_rate"] - baseline_metrics["critical_delivery_rate"],
        "sent_size_reduction_bytes": baseline_metrics["sent_size"] - adaptive_metrics["sent_size"],
        "sent_size_reduction_ratio": _safe_ratio(
            baseline_metrics["sent_size"] - adaptive_metrics["sent_size"],
            baseline_metrics["sent_size"],
        ),
    }


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
