"""Smoke test headless da App Streamlit com os CSVs locais."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
app = AppTest.from_file(str(ROOT / "apps/network-monitor/app.py"), default_timeout=60)
app.run()

assert not app.exception, [str(item.value) for item in app.exception]
assert app.title[0].value == "📡 Monitor de qualidade de rede"
assert len(app.metric) == 4
assert app.metric[0].label == "Latencia media"
print("Smoke test da App concluido com sucesso.")

