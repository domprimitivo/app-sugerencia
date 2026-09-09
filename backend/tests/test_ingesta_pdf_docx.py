"""
Test: extraccion PDF/DOCX + free-text con etiqueta en el embudo.
Verifica que server.extraer_texto_documento devuelve texto real y que
procesar_expediente lo incluye en documentos_procesados.
"""
import io
import os
import pytest
import requests
from reportlab.pdfgen import canvas
from docx import Document

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL required"

PDF_TEXT = "linea 2 detenida por falla de motor urgente"
DOCX_TEXT = "reporte diario mantenimiento correctivo turno noche"


def _build_pdf_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def _build_docx_bytes(text: str) -> bytes:
    d = Document()
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def expediente_id(api):
    r = api.post(f"{BASE_URL}/api/expedientes", json={
        "nombre": "TEST_ingesta_pdf_docx",
        "descripcion": "Prueba PDF+DOCX+texto"
    })
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    yield eid
    api.delete(f"{BASE_URL}/api/expedientes/{eid}")


def test_upload_pdf(api, expediente_id):
    pdf_bytes = _build_pdf_bytes(PDF_TEXT)
    r = api.post(
        f"{BASE_URL}/api/expedientes/{expediente_id}/documentos",
        files={"file": ("incidencia.pdf", pdf_bytes, "application/pdf")}
    )
    assert r.status_code == 200, r.text
    assert r.json()["documento"]["nombre"] == "incidencia.pdf"


def test_upload_docx(api, expediente_id):
    docx_bytes = _build_docx_bytes(DOCX_TEXT)
    r = api.post(
        f"{BASE_URL}/api/expedientes/{expediente_id}/documentos",
        files={"file": ("reporte.docx", docx_bytes,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert r.status_code == 200, r.text


def test_upload_txt_etiqueta(api, expediente_id):
    contenido = "Etiqueta: cumpleaños\n\nMañana es el cumpleaños de Juan del equipo de mantenimiento"
    r = api.post(
        f"{BASE_URL}/api/expedientes/{expediente_id}/documentos",
        files={"file": ("escritura_libre.txt", contenido.encode("utf-8"), "text/plain")}
    )
    assert r.status_code == 200


def test_procesar_extrae_texto(api, expediente_id):
    r = api.post(
        f"{BASE_URL}/api/expedientes/{expediente_id}/procesar",
        json={"tipo_consulta": "analisis"}
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # Debe tener documentos_procesados (dominio empresa: fabrica)
    assert "documentos_procesados" in data, f"campos: {list(data.keys())}"
    assert data["total_documentos"] == 3, data["total_documentos"]

    # Concatenar todo el contenido reportado por RAG
    dp = data["documentos_procesados"]
    todo = " ".join(str(d) for d in dp)
    # No debe estar el marcador "[Archivo binario:"
    assert "[Archivo binario:" not in todo, f"PDF/DOCX se perdieron como binario: {todo[:500]}"


def test_procesar_expediente_estado_completado(api, expediente_id):
    r = api.get(f"{BASE_URL}/api/expedientes/{expediente_id}")
    assert r.status_code == 200
    assert r.json()["estado"] == "completado"


def test_extraccion_directa_backend():
    """Verifica que la funcion extraer_texto_documento devuelva texto real."""
    import sys
    sys.path.insert(0, "/app/backend")
    from server import extraer_texto_documento
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        pdf_path = Path(td) / "a.pdf"
        pdf_path.write_bytes(_build_pdf_bytes(PDF_TEXT))
        out = extraer_texto_documento(pdf_path, "application/pdf", "a.pdf")
        assert PDF_TEXT.split()[0] in out, f"PDF extract failed: {out!r}"
        assert not out.startswith("[Archivo binario"), out

        docx_path = Path(td) / "b.docx"
        docx_path.write_bytes(_build_docx_bytes(DOCX_TEXT))
        out2 = extraer_texto_documento(
            docx_path,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "b.docx"
        )
        assert DOCX_TEXT.split()[0] in out2, f"DOCX extract failed: {out2!r}"
        assert not out2.startswith("[Archivo binario"), out2
