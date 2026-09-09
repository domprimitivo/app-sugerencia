"""Tests for the silent assistant (aprendiz) flow in company domain 'hotel'."""
import os
import io
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
DOM = "hotel"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    return s


# --- Motor estado ---
def test_motor_estado_empresa(session):
    r = session.get(f"{API}/motor/estado", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("tipo_dominio") == "empresa", data


# --- Basics for unipersonal not broken ---
def test_dominios_and_config(session):
    r1 = session.get(f"{API}/dominios", timeout=30)
    assert r1.status_code == 200
    r2 = session.get(f"{API}/config", timeout=30)
    assert r2.status_code == 200


@pytest.fixture(scope="module")
def asistente_obj(session):
    # Create expediente
    r = session.post(f"{API}/expedientes", json={
        "nombre": "TEST_asistente",
        "descripcion": "test flujo asistente"
    }, timeout=30)
    assert r.status_code in (200, 201), r.text
    exp_id = r.json()["id"]

    # Upload .txt
    files = {"file": ("nota.txt", io.BytesIO(b"incidencia en check-in, cliente esperando"), "text/plain")}
    r = session.post(f"{API}/expedientes/{exp_id}/documentos", files=files, timeout=60)
    assert r.status_code in (200, 201), r.text

    # Procesar
    r = session.post(f"{API}/expedientes/{exp_id}/procesar",
                     json={"tipo_consulta": "analisis"}, timeout=120)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "asistente" in body, body
    a = body["asistente"]
    for k in ["node_id", "dominio", "suggested_action_id", "suggested_action_label",
              "phase", "phase_probs", "clarity", "R_score", "soft_tags", "confianza"]:
        assert k in a, f"missing key {k} in asistente: {a}"
    assert a["dominio"] == DOM
    return a


def test_procesar_incluye_asistente(asistente_obj):
    assert asistente_obj["suggested_action_label"]


def test_decision_confirmar(session, asistente_obj):
    r = session.post(f"{API}/aprendiz/{DOM}/decision-asistente", json={
        "sugerencia": asistente_obj,
        "decision": "confirmar",
    }, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "registrado"
    assert data.get("user_accepted") is True
    evt = data.get("evento") or {}
    ae = evt.get("action_execution") or {}
    assert ae.get("user_accepted_suggestion") is True
    assert ae.get("action_known") is True


def test_decision_corregir_sin_texto(session, asistente_obj):
    r = session.post(f"{API}/aprendiz/{DOM}/decision-asistente", json={
        "sugerencia": asistente_obj,
        "decision": "corregir",
        "correccion": ""
    }, timeout=60)
    assert r.status_code == 400, r.text


def test_decision_corregir(session, asistente_obj):
    r = session.post(f"{API}/aprendiz/{DOM}/decision-asistente", json={
        "sugerencia": asistente_obj,
        "decision": "corregir",
        "correccion": "activar protocolo X"
    }, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("user_accepted") is False
    evt = data.get("evento") or {}
    ae = evt.get("action_execution") or {}
    assert ae.get("action_label") == "activar protocolo X"
    assert ae.get("action_known") is False
    le = evt.get("learning_event") or {}
    assert le.get("type") == "correction"


def test_lista_decisiones(session):
    r = session.get(f"{API}/aprendiz/{DOM}/decisiones", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("total", 0) > 0
    items = data.get("registros") or data.get("decisiones") or data.get("items") or []
    assert len(items) > 0
    first = items[0]
    assert "timestamp" in first, first


def test_ajuste_estado(session):
    r = session.get(f"{API}/aprendiz/{DOM}/ajuste/estado", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("intervalo_dias") == 50
    assert "activado_en" in data
    assert "proximo_ajuste" in data


def test_ajuste_ejecutar(session):
    r = session.post(f"{API}/aprendiz/{DOM}/ajuste/ejecutar", timeout=180)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok", data
    assert data.get("estado") == "completado", data
    assert data.get("modelo_reemplazado") is True, data
    prom = data.get("artefactos_promovidos") or []
    assert any("policy_adapter.pt" in str(x) for x in prom), prom
