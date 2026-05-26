import html
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import SCENARIOS, run_experiment
from core.reporting import render_html_report


HOST = "127.0.0.1"
PORT = 8000


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(render_index())
            return

        if parsed.path == "/run":
            self._handle_run(parsed.query)
            return

        self.send_error(404, "Not found")

    def _handle_run(self, query: str) -> None:
        params = parse_qs(query)
        try:
            scenario = _single(params, "scenario", "overload")
            count = _optional_int(params, "count")
            bandwidth = _optional_int(params, "bandwidth")
            loss = _optional_float(params, "loss")
            seed = int(_single(params, "seed", "42"))

            result = run_experiment(
                scenario_name=scenario,
                count=count,
                bandwidth=bandwidth,
                loss=loss,
                seed=seed,
            )
            report_html = render_html_report(result.report)
            page = render_web_page(report_html=report_html, error=None)
            self._send_html(page)
        except Exception as exc:
            page = render_web_page(report_html=None, error=str(exc))
            self._send_html(page, status=400)

    def _send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web_demo] {self.address_string()} - {format % args}")


def render_index() -> str:
    return render_web_page(report_html=None, error=None)


def render_web_page(report_html: str | None, error: str | None) -> str:
    form = render_form()
    error_block = f"<div class='error'>Ошибка: {html.escape(error)}</div>" if error else ""
    report_block = ""
    if report_html is not None:
        report_block = f"""
        <section class="report-frame">
          <h2>Результат эксперимента</h2>
          <iframe srcdoc="{html.escape(report_html, quote=True)}"></iframe>
        </section>
        """

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Адаптив-Боец — web demo</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e5e7eb; }}
    header {{ padding: 28px 36px; background: linear-gradient(135deg, #172554, #0f172a); }}
    h1 {{ margin: 0 0 8px; }}
    main {{ padding: 24px 36px; }}
    .panel {{ background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 20px; margin-bottom: 22px; }}
    label {{ display: block; margin: 12px 0 6px; color: #cbd5e1; }}
    input, select {{ width: 100%; max-width: 360px; padding: 10px; border-radius: 10px; border: 1px solid #475569; background: #020617; color: #e5e7eb; }}
    button {{ margin-top: 18px; padding: 12px 18px; border: 0; border-radius: 12px; background: #22c55e; color: #052e16; font-weight: 700; cursor: pointer; }}
    button:hover {{ background: #86efac; }}
    .hint {{ color: #94a3b8; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
    .error {{ background: #7f1d1d; border: 1px solid #fecaca; padding: 14px; border-radius: 12px; margin-bottom: 16px; }}
    iframe {{ width: 100%; height: 900px; border: 0; border-radius: 16px; background: white; }}
    .report-frame {{ margin-top: 24px; }}
    code {{ background: #1e293b; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <header>
    <h1>Адаптив-Боец</h1>
    <div class="hint">Web-демонстрация адаптивной приоритизации и сжатия информационного потока</div>
  </header>
  <main>
    {error_block}
    {form}
    {report_block}
  </main>
</body>
</html>
"""


def render_form() -> str:
    scenario_options = "".join(
        f"<option value='{html.escape(name)}'>{html.escape(name)}</option>"
        for name in SCENARIOS.keys()
    )
    return f"""
    <section class="panel">
      <h2>Параметры эксперимента</h2>
      <form action="/run" method="get">
        <div class="grid">
          <div>
            <label for="scenario">Сценарий канала</label>
            <select id="scenario" name="scenario">{scenario_options}</select>
            <div class="hint">normal, overload или emergency</div>
          </div>
          <div>
            <label for="count">Число сообщений</label>
            <input id="count" name="count" type="number" min="1" placeholder="по умолчанию из сценария">
          </div>
          <div>
            <label for="bandwidth">Полоса канала, байт</label>
            <input id="bandwidth" name="bandwidth" type="number" min="1" placeholder="по умолчанию из сценария">
          </div>
          <div>
            <label for="loss">Вероятность потери</label>
            <input id="loss" name="loss" type="number" min="0" max="1" step="0.01" placeholder="0.00 .. 1.00">
          </div>
          <div>
            <label for="seed">Seed</label>
            <input id="seed" name="seed" type="number" value="42">
          </div>
        </div>
        <button type="submit">Запустить демонстрацию</button>
      </form>
      <p class="hint">Интерфейс работает локально. Данные никуда не отправляются: расчёт выполняется на вашем компьютере.</p>
    </section>
    """


def _single(params: dict[str, list[str]], key: str, default: str) -> str:
    values = params.get(key)
    if not values or values[0] == "":
        return default
    return values[0]


def _optional_int(params: dict[str, list[str]], key: str) -> int | None:
    value = _single(params, key, "")
    if value == "":
        return None
    return int(value)


def _optional_float(params: dict[str, list[str]], key: str) -> float | None:
    value = _single(params, key, "")
    if value == "":
        return None
    return float(value)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DemoHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"Адаптив-Боец web demo: {url}")
    print("Для остановки нажмите Ctrl+C")
    try:
        webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка web demo")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
