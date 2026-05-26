import csv
import html
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


def save_html_report(report: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html_report(report), encoding="utf-8")


def render_html_report(report: dict[str, Any]) -> str:
    scenario = html.escape(str(report["scenario"]))
    parameters = report["parameters"]
    baseline = report["baseline"]
    adaptive = report["adaptive"]
    delta = report["delta"]

    cards = "".join(
        [
            _metric_card("Критических доставлено", baseline["delivered_critical"], adaptive["delivered_critical"], suffix=" пак."),
            _metric_card("Доля доставки критических", baseline["critical_delivery_rate"], adaptive["critical_delivery_rate"], as_percent=True),
            _metric_card("Всего доставлено", baseline["delivered_packets"], adaptive["delivered_packets"], suffix=" пак."),
            _metric_card("Отброшено по полосе", baseline["dropped_by_bandwidth"], adaptive["dropped_by_bandwidth"], suffix=" пак.", lower_is_better=True),
        ]
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Адаптив-Боец — отчёт {scenario}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f6f8fb; }}
    h1, h2 {{ color: #0f172a; }}
    .subtitle {{ color: #475569; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 24px 0; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; box-shadow: 0 6px 18px rgba(15,23,42,0.06); }}
    .label {{ color: #64748b; font-size: 14px; }}
    .big {{ font-size: 28px; font-weight: 700; margin: 8px 0; }}
    .gain {{ color: #166534; font-weight: 700; }}
    .loss {{ color: #991b1b; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 18px rgba(15,23,42,0.06); }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #eaf0f8; }}
    .bar-wrap {{ background: #e2e8f0; border-radius: 999px; overflow: hidden; height: 16px; }}
    .bar {{ background: #2563eb; height: 16px; }}
    .bar.adaptive {{ background: #16a34a; }}
    .note {{ background: #fff7ed; border: 1px solid #fed7aa; padding: 14px; border-radius: 12px; }}
    code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Адаптив-Боец — демонстрационный отчёт</h1>
  <p class="subtitle">Сценарий: <strong>{scenario}</strong>. Сравнение обычной отправки и адаптивной обработки потока.</p>

  <div class="note">
    <strong>Главный вывод:</strong> адаптивный режим отдаёт ограниченный канал более важным сообщениям. В аварийных режимах ключевой показатель — не общее количество пакетов, а доставка критических данных.
  </div>

  <h2>Параметры эксперимента</h2>
  {_parameters_table(parameters)}

  <h2>Ключевые показатели</h2>
  <div class="grid">{cards}</div>

  <h2>Сравнение метрик</h2>
  {_comparison_table(baseline, adaptive)}

  <h2>Визуальное сравнение</h2>
  {_bar_section("Доля доставки критических", baseline["critical_delivery_rate"], adaptive["critical_delivery_rate"], percent=True)}
  {_bar_section("Общая доля доставки", baseline["delivery_rate"], adaptive["delivery_rate"], percent=True)}
  {_bar_section("Загрузка канала", baseline["channel_utilization"], adaptive["channel_utilization"], percent=True)}

  <h2>Прирост относительно baseline</h2>
  {_delta_table(delta)}

  <h2>Как воспроизвести</h2>
  <p>Запуск из корня проекта:</p>
  <pre><code>python experiments/run_demo.py --scenario {scenario} --export-dir reports</code></pre>
</body>
</html>
"""


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


def _format_value(value: Any, as_percent: bool = False) -> str:
    if isinstance(value, float):
        if as_percent:
            return f"{value * 100:.1f}%"
        return f"{value:.3f}"
    return str(value)


def _metric_card(
    title: str,
    baseline_value: Any,
    adaptive_value: Any,
    suffix: str = "",
    as_percent: bool = False,
    lower_is_better: bool = False,
) -> str:
    diff = adaptive_value - baseline_value
    is_good = diff <= 0 if lower_is_better else diff >= 0
    diff_class = "gain" if is_good else "loss"
    sign = "+" if diff >= 0 else ""
    diff_text = _format_value(diff, as_percent=as_percent)
    return f"""
    <div class="card">
      <div class="label">{html.escape(title)}</div>
      <div class="big">{_format_value(adaptive_value, as_percent=as_percent)}{html.escape(suffix)}</div>
      <div>baseline: {_format_value(baseline_value, as_percent=as_percent)}{html.escape(suffix)}</div>
      <div class="{diff_class}">изменение: {sign}{diff_text}{html.escape(suffix)}</div>
    </div>
    """


def _parameters_table(parameters: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
        for key, value in parameters.items()
    )
    return f"<table><tr><th>Параметр</th><th>Значение</th></tr>{rows}</table>"


def _comparison_table(baseline: dict[str, Any], adaptive: dict[str, Any]) -> str:
    metrics = [
        ("delivery_rate", "Доля доставки", True),
        ("critical_delivery_rate", "Доля доставки критических", True),
        ("delivered_packets", "Доставлено пакетов", False),
        ("delivered_critical", "Доставлено критических", False),
        ("sent_size", "Переданный объём, байт", False),
        ("compression_ratio", "Коэффициент сжатия", False),
        ("dropped_by_bandwidth", "Отброшено по полосе", False),
        ("dropped_by_loss", "Случайно потеряно", False),
    ]
    rows = "".join(
        f"<tr><td>{label}</td><td>{_format_value(baseline[key], percent)}</td><td>{_format_value(adaptive[key], percent)}</td></tr>"
        for key, label, percent in metrics
    )
    return f"<table><tr><th>Метрика</th><th>Baseline</th><th>Adaptive</th></tr>{rows}</table>"


def _delta_table(delta: dict[str, Any]) -> str:
    labels = {
        "delivery_rate_gain": "Прирост общей доставки",
        "critical_delivery_rate_gain": "Прирост доставки критических",
        "sent_size_reduction_bytes": "Снижение переданного объёма, байт",
        "sent_size_reduction_ratio": "Снижение переданного объёма, доля",
    }
    percent_keys = {"delivery_rate_gain", "critical_delivery_rate_gain", "sent_size_reduction_ratio"}
    rows = "".join(
        f"<tr><td>{labels.get(key, key)}</td><td>{_format_value(value, key in percent_keys)}</td></tr>"
        for key, value in delta.items()
    )
    return f"<table><tr><th>Показатель</th><th>Значение</th></tr>{rows}</table>"


def _bar_section(title: str, baseline_value: float, adaptive_value: float, percent: bool = False) -> str:
    baseline_width = max(0, min(100, baseline_value * 100 if percent else baseline_value))
    adaptive_width = max(0, min(100, adaptive_value * 100 if percent else adaptive_value))
    return f"""
    <div class="card">
      <h3>{html.escape(title)}</h3>
      <p>Baseline: {_format_value(baseline_value, as_percent=percent)}</p>
      <div class="bar-wrap"><div class="bar" style="width: {baseline_width:.1f}%"></div></div>
      <p>Adaptive: {_format_value(adaptive_value, as_percent=percent)}</p>
      <div class="bar-wrap"><div class="bar adaptive" style="width: {adaptive_width:.1f}%"></div></div>
    </div>
    """
