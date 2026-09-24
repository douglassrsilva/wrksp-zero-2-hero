"""Smoke test headless de la App Streamlit con los CSV locales."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
app = AppTest.from_file(str(ROOT / "apps/network-monitor/app.py"), default_timeout=60)
app.run()

assert not app.exception, [str(item.value) for item in app.exception]
assert app.title[0].value == "📡 Monitor de experiencia móvil"
assert len(app.tabs) == 0
assert len(app.selectbox) == 1
assert app.selectbox[0].label == "Región"
assert len(app.metric) == 3
assert [metric.label for metric in app.metric] == [
    "Disponibilidad media",
    "Latencia media",
    "Clientes activos",
]
assert len(app.dataframe) == 1
assert "Esta versión es intencionalmente simple" in app.info[0].value
print("Smoke test de la App inicial finalizado correctamente.")
