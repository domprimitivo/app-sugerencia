"""Tests for POST /api/flujo/ejecutar-dominio y GET /api/flujo/dominios."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

POLOS = ["Permeabilidad", "Tensión TR", "Sutura", "Retorno al Suelo",
         "Estancamiento", "Ruptura de Fase", "Resonancia"]

DOMINIOS = ["dom_restaurante_v1", "dom_retail_v1", "dom_hotel_v1",
            "dom_fabrica_v1", "dom_logistica_v1", "dom_clinica_v1"]


def test_get_dominios():
    r = requests.get(f"{BASE_URL}/api/flujo/dominios", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "empresariales" in data
    assert "demostracion" in data
    assert len(data["empresariales"]) == 6
    ids = [d["domain_id"] for d in data["empresariales"]]
    for did in DOMINIOS:
        assert did in ids, f"Falta {did}"
    demo_ids = [d["domain_id"] for d in data["demostracion"]]
    assert "dom_fermentacion_lotes_v1" in demo_ids


@pytest.mark.parametrize("domain_id", DOMINIOS + ["dom_fermentacion_lotes_v1"])
def test_ejecutar_dominio(domain_id):
    r = requests.post(
        f"{BASE_URL}/api/flujo/ejecutar-dominio",
        data={"domain_id": domain_id, "modo": "ASESORIA"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["dominio"]["domain_id"] == domain_id
    kpis = d["kpis_holograficos"]
    for polo in POLOS:
        assert polo in kpis, f"Falta KPI {polo} en {domain_id}"
        assert 0.0 <= kpis[polo] <= 1.0
    disc = d["metricas_discretas"]
    for polo in POLOS:
        assert polo in disc
        assert isinstance(disc[polo], list)
        assert len(disc[polo]) > 0
        for item in disc[polo]:
            assert "signal" in item and "valor" in item and "norm" in item
    fc = d["features_control"]
    for key in ["viable", "suelo_firme", "coherente", "c_viabilidad",
                "firmeza_suelo_R", "delta_coherencia"]:
        assert key in fc
    lazo = d["lazo"]
    assert "estado_general" in lazo
    assert "geodesica_sugerida" in lazo and "nombre" in lazo["geodesica_sugerida"]
    assert "kpis" in lazo
    for polo in POLOS:
        assert polo in lazo["kpis"]
        assert "estado" in lazo["kpis"][polo]
        assert "valor" in lazo["kpis"][polo]


def test_kpis_distintos_entre_dominios():
    """Cada dominio debe dar KPIs propios (distintos entre sí)."""
    firmas = {}
    for did in DOMINIOS:
        r = requests.post(
            f"{BASE_URL}/api/flujo/ejecutar-dominio",
            data={"domain_id": did, "modo": "ASESORIA"},
            timeout=30,
        )
        assert r.status_code == 200
        firmas[did] = tuple(round(v, 3) for v in r.json()["kpis_holograficos"].values())
    # verifica que no todos son idénticos
    assert len(set(firmas.values())) >= 4, f"KPIs muy repetidos: {firmas}"
