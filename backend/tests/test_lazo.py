"""Tests for the Lazo Generico endpoints (Pantalla de Claridad)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend .env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break


@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- GET /api/lazo/dominio ---
def test_get_dominio(client):
    r = client.get(f"{BASE_URL}/api/lazo/dominio", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "CVD Grafeno"
    assert isinstance(data["kpis_nombres"], list)
    assert len(data["kpis_nombres"]) == 7
    assert "Permeabilidad" in data["kpis_nombres"]
    assert "Resonancia" in data["kpis_nombres"]
    assert "kpis_umbrales" in data
    assert "geodesicas" in data
    for g in ["gamma_0", "gamma_1", "gamma_2", "gamma_3", "gamma_4"]:
        assert g in data["geodesicas"]


# --- POST /api/lazo/evaluar ASESORIA nominal ---
NOMINAL = {
    "Permeabilidad": 0.65, "Tensión TR": 0.25, "Sutura": 0.20,
    "Retorno al Suelo": 0.75, "Estancamiento": 0.15, "Ruptura de Fase": 0.20,
    "Resonancia": 0.25,
}

AUTOENGANO = {
    "Permeabilidad": 0.55, "Tensión TR": 0.60, "Sutura": 0.65,
    "Retorno al Suelo": 0.45, "Estancamiento": 0.50, "Ruptura de Fase": 0.55,
    "Resonancia": 0.25,
}


def test_evaluar_asesoria_nominal(client):
    r = client.post(
        f"{BASE_URL}/api/lazo/evaluar",
        json={"modo": "ASESORIA", "kpis": NOMINAL},
        timeout=15,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["modo"] == "ASESORIA"
    assert d["estado_general"] == "NOMINAL"
    assert d["requiere_autorizacion"] is True
    assert d["geodesica_sugerida"]["nombre"] == "Mantener vector de estado nominal"
    assert "kpis" in d and "Permeabilidad" in d["kpis"]


def test_evaluar_agencia_autoengano(client):
    r = client.post(
        f"{BASE_URL}/api/lazo/evaluar",
        json={"modo": "AGENCIA", "kpis": AUTOENGANO},
        timeout=15,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["modo"] == "AGENCIA"
    assert "hermano_corto" in d
    assert "hermano_mediano" in d
    assert "hermano_largo" in d
    assert "requiere_cenit" in d
    assert "ejecutar_autonomamente" in d
    # AUTOENGANO preset triggers autoengano OR fallo_pegado
    assert d["requiere_cenit"] is True
    assert d["ejecutar_autonomamente"] is False


def test_evaluar_agencia_nominal_autonomo(client):
    r = client.post(
        f"{BASE_URL}/api/lazo/evaluar",
        json={"modo": "AGENCIA", "kpis": NOMINAL},
        timeout=15,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["modo"] == "AGENCIA"
    assert d["ejecutar_autonomamente"] is True
    assert d["requiere_cenit"] is False
