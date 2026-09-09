"""
Iteration 10 backend tests:
- Trajectories per active domain (fabrica) with same semáforo
- POST /api/lazo/evaluar ASESORIA/AGENCIA; AGENCIA includes ingesta_tiempo_real
- CSV + XLSX ingestion via /expedientes -> /documentos -> /procesar
- Real-time ingestion OPTIONAL: no error when empty; webhook links to AGENCIA
"""
import io
import os
import pytest
import requests
import csv
import openpyxl

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        # Load from /app/frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.strip().split("=", 1)[1]
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

KPIS_NOMINAL = {
    "Permeabilidad": 0.50,
    "Tensión TR": 0.20,
    "Sutura": 0.30,
    "Retorno al Suelo": 0.80,
    "Estancamiento": 0.20,
    "Ruptura de Fase": 0.20,
    "Resonancia": 0.40,
}

EXPECTED_KPIS = ["Permeabilidad", "Tensión TR", "Sutura", "Retorno al Suelo",
                 "Estancamiento", "Ruptura de Fase", "Resonancia"]

FABRICA_KEYWORDS = ["línea", "producción", "cuello de botella", "planta", "turno"]


@pytest.fixture
def session():
    s = requests.Session()
    return s


# ── 1. GET /api/lazo/dominio — trayectorias en lenguaje fábrica ─────────
def test_lazo_dominio_fabrica_trayectorias(session):
    r = session.get(f"{API}/lazo/dominio")
    assert r.status_code == 200, r.text
    data = r.json()
    # Same semáforo — 7 KPIs
    assert set(data["kpis_nombres"]) == set(EXPECTED_KPIS)
    for k in EXPECTED_KPIS:
        assert k in data["kpis_umbrales"]
    # Geodesicas in domain language (fabrica)
    geo = data["geodesicas"]
    assert "gamma_0" in geo
    nombres_join = " ".join(geo[g]["nombre"].lower() for g in geo)
    assert any(k in nombres_join for k in FABRICA_KEYWORDS), \
        f"Trajectory names don't look like 'fabrica': {nombres_join}"
    # Explicit expected phrases from spec
    assert "línea" in geo["gamma_0"]["nombre"].lower() or "régimen nominal" in geo["gamma_0"]["nombre"].lower()


# ── 2. POST /api/lazo/evaluar ASESORIA ──────────────────────────────────
def test_lazo_evaluar_asesoria(session):
    r = session.post(f"{API}/lazo/evaluar", json={"modo": "ASESORIA", "kpis": KPIS_NOMINAL})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["modo"] == "ASESORIA"
    assert "geodesica_sugerida" in data
    nombre = data["geodesica_sugerida"]["nombre"].lower()
    assert any(k in nombre for k in FABRICA_KEYWORDS + ["régimen", "operación"]), \
        f"ASESORIA geodesica not in fabrica language: {nombre}"
    # ASESORIA should NOT include ingesta_tiempo_real
    assert "ingesta_tiempo_real" not in data


# ── 3. POST /api/lazo/evaluar AGENCIA — ingesta_tiempo_real presente ────
def test_lazo_evaluar_agencia_has_ingesta_tiempo_real(session):
    r = session.post(f"{API}/lazo/evaluar", json={"modo": "AGENCIA", "kpis": KPIS_NOMINAL})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["modo"] == "AGENCIA"
    assert "ingesta_tiempo_real" in data
    itr = data["ingesta_tiempo_real"]
    assert "disponible" in itr and "total" in itr and "items" in itr
    assert isinstance(itr["items"], list)
    # geodesica in fabrica language
    nombre = data["geodesica_sugerida"]["nombre"].lower()
    assert any(k in nombre for k in FABRICA_KEYWORDS + ["régimen", "operación"]), \
        f"AGENCIA geodesica not in fabrica language: {nombre}"


# ── 4. Webhook OPCIONAL: enviar y volver a evaluar ──────────────────────
def test_webhook_fabrica_links_to_agencia(session):
    # Enviar webhook
    payload = {"fuente": "sensor", "texto": "vibracion alta prensa 4"}
    r = session.post(f"{API}/ingesta/webhook/fabrica", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("estado") == "completado"

    # Volver a evaluar AGENCIA → disponible=True y total>=1
    r2 = session.post(f"{API}/lazo/evaluar", json={"modo": "AGENCIA", "kpis": KPIS_NOMINAL})
    assert r2.status_code == 200, r2.text
    itr = r2.json()["ingesta_tiempo_real"]
    assert itr["disponible"] is True
    assert itr["total"] >= 1


# ── 5. Ingesta CSV + XLSX ───────────────────────────────────────────────
@pytest.fixture
def expediente_id(session):
    r = session.post(f"{API}/expedientes",
                     json={"nombre": "TEST_ingesta_csv_xlsx", "descripcion": "test"})
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    yield eid
    session.delete(f"{API}/expedientes/{eid}")


def _make_xlsx_bytes():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(["turno", "produccion", "defectos"])
    ws.append(["mañana", 120, 3])
    ws.append(["tarde", 95, 7])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def _make_csv_bytes():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["prensa", "vibracion", "temp"])
    w.writerow(["prensa4", "alta", 78])
    w.writerow(["prensa1", "normal", 65])
    return buf.getvalue().encode("utf-8")


def test_ingesta_csv_xlsx(session, expediente_id):
    # Upload xlsx
    xlsx_bytes = _make_xlsx_bytes()
    r = session.post(
        f"{API}/expedientes/{expediente_id}/documentos",
        files={"file": ("datos.xlsx", xlsx_bytes,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text

    # Upload csv
    csv_bytes = _make_csv_bytes()
    r = session.post(
        f"{API}/expedientes/{expediente_id}/documentos",
        files={"file": ("datos.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 200, r.text

    # Procesar
    r = session.post(f"{API}/expedientes/{expediente_id}/procesar",
                     json={"tipo_consulta": "analisis"})
    assert r.status_code == 200, r.text
    data = r.json()

    # documentos_procesados should list both
    docs_proc = data.get("documentos_procesados") or data.get("documentos") or []
    # Some responses nest inside "resultado"
    if not docs_proc and "resultado" in data:
        docs_proc = data["resultado"].get("documentos_procesados", [])
    # Fallback: check any mention of filenames
    dump = str(data).lower()
    assert "datos.xlsx" in dump, f"xlsx not in processed output: {dump[:400]}"
    assert "datos.csv" in dump, f"csv not in processed output: {dump[:400]}"
    # No '[Archivo binario]' surrogate
    assert "archivo binario" not in dump, "Binary fallback used → extraction failed"

    # suggested_action_label / asistente
    has_assistant = ("suggested_action_label" in dump or
                     "asistente" in dump or
                     "accion_sugerida" in dump)
    assert has_assistant, f"No assistant/suggested action in response: {dump[:600]}"
