import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import SCENARIOS, format_console_report, run_experiment, save_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Демонстрация MVP Адаптив-Боец")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="overload", help="готовый профиль канала")
    parser.add_argument("--count", type=int, default=None, help="число входных сообщений")
    parser.add_argument("--bandwidth", type=int, default=None, help="полоса канала за цикл, байт")
    parser.add_argument("--loss", type=float, default=None, help="вероятность случайной потери 0..1")
    parser.add_argument("--seed", type=int, default=42, help="seed для воспроизводимости")
    parser.add_argument("--export-dir", type=Path, default=None, help="папка для JSON/CSV/HTML отчёта")
    args = parser.parse_args()

    result = run_experiment(
        scenario_name=args.scenario,
        count=args.count,
        bandwidth=args.bandwidth,
        loss=args.loss,
        seed=args.seed,
    )

    print("АДАПТИВ-БОЕЦ: демонстрация адаптивного управления информационным потоком")
    print(
        "Параметры: "
        f"scenario={result.scenario_name}, "
        f"count={result.parameters['count']}, "
        f"bandwidth={result.parameters['bandwidth']}, "
        f"loss={result.parameters['loss']}, "
        f"seed={result.parameters['seed']}"
    )

    print(format_console_report("Базовая отправка без адаптации", result.prepared_packets, result.baseline_report))
    print(format_console_report("Адаптивная отправка", result.prepared_packets, result.adaptive_report))

    if args.export_dir is not None:
        paths = save_reports(result, args.export_dir)
        print(f"\nОтчёты сохранены:")
        print(f"- {paths['json']}")
        print(f"- {paths['csv']}")
        print(f"- {paths['html']}")


if __name__ == "__main__":
    main()
