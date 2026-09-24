"""Pruebas rápidas del contrato local; no requieren workspace ni credenciales."""

from pathlib import Path

from data_access import load_local_gold


def test_local_gold_contract() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data" / "generated"
    datasets = load_local_gold(data_dir)
    assert set(datasets) == {
        "network_hourly",
        "site_daily",
        "customer_360",
        "customer_product_daily",
        "incident_impact",
    }
    assert all(not frame.empty for frame in datasets.values())
    assert {"avg_latency_ms", "avg_availability_pct"}.issubset(datasets["network_hourly"].columns)
    assert {"risk_level", "customer_segment"}.issubset(datasets["customer_360"].columns)
    assert {"product_name", "billed_revenue_clp"}.issubset(
        datasets["customer_product_daily"].columns
    )


if __name__ == "__main__":
    test_local_gold_contract()
    print("Contrato local Customer 360 validado correctamente.")
