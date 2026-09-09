"""Tests for POST /api/embudo/registrar-resultado (navegación geométrica)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def config_hotel(api):
    r = api.get(f"{BASE_URL}/api/config")
    assert r.status_code == 200
    data = r.json()
    assert data.get("configurado") is True
    assert data.get("dominio_id") == "hotel"
    return data


def _evaluar(api, modo):
    kpis = {
        "Permeabilidad": 0.65, "Tensión TR": 0.25, "Sutura": 0.20,
        "Retorno al Suelo": 0.75, "Estancamiento": 0.15,
        "Ruptura de Fase": 0.20, "Resonancia": 0.25,
    }
    r = api.post(f"{BASE_URL}/api/lazo/evaluar", json={"modo": modo, "kpis": kpis})
    assert r.status_code == 200, r.text
    return kpis, r.json()


@pytest.mark.parametrize("modo", ["ASESORIA", "AGENCIA"])
def test_registrar_resultado_navegacion(api, config_hotel, modo):
    kpis, resultado = _evaluar(api, modo)
    r = api.post(f"{BASE_URL}/api/embudo/registrar-resultado",
                 json={"modo": modo, "kpis": kpis, "resultado": resultado})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") == "registrado"
    assert isinstance(body.get("expediente_id"), str) and len(body["expediente_id"]) > 0
    res = body.get("resultado") or {}
    asistente = res.get("asistente") or {}
    assert asistente.get("suggested_action_label"), f"Falta suggested_action_label: {asistente}"

    # GET expedientes lista el nuevo con nombre "Navegación <modo> ..."
    exps = api.get(f"{BASE_URL}/api/expedientes").json()
    match = [e for e in exps if e["id"] == body["expediente_id"]]
    assert match, "Expediente no aparece en /api/expedientes"
    assert match[0]["estado"] == "completado"
    assert match[0]["nombre"].startswith(f"Navegación {modo}")
