"""
Tests for Compresión Geométrica (MOCG codec) endpoints:
- POST /api/compresion/toggle (compress + decompress round-trip)
- POST /api/compresion/sistema/hotel (system compression)
"""
import os
import io
import json
import base64
import hashlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend/.env
    envp = "/app/frontend/.env"
    if os.path.exists(envp):
        with open(envp) as fh:
            for ln in fh:
                if ln.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"


def _sample_jsonl_bytes(n=15):
    lines = []
    for i in range(n):
        obj = {
            "timestamp": f"2026-01-{(i%28)+1:02d} 10:00:00",
            "entity_id": f"user-{i % 3}",
            "action": "login" if i % 2 == 0 else "logout",
            "result": "failure" if i > 12 else "success",
            "severity": "high" if i > 12 else "low",
            "value": i * 1.5,
        }
        lines.append(json.dumps(obj))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _sample_csv_bytes():
    return b"timestamp,entity_id,action,result,severity,size\n" + \
           b"\n".join(
               f"2026-01-01 10:00:0{i},ip-{i%2},GET,success,low,{100+i}".encode()
               for i in range(10)
           )


class TestCompresionToggle:
    """POST /api/compresion/toggle round-trip tests"""

    def test_comprimir_multiples_archivos(self):
        files = [
            ("files", ("events.jsonl", _sample_jsonl_bytes(), "application/x-ndjson")),
            ("files", ("data.csv", _sample_csv_bytes(), "text/csv")),
        ]
        r = requests.post(f"{API}/compresion/toggle", files=files, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["accion"] == "comprimido"
        assert data.get("marker") == "MOCG_CODEC_V1"
        sr = data["shape_report"]
        assert sr["n_events_total"] >= 2
        assert "n_in_form" in sr and "n_out_form" in sr
        assert isinstance(sr["file_types"], dict)
        assert "compression" in sr and "ratio" in sr["compression"]
        assert "top_anomalous" in sr
        # Paquete presente y con marker
        pq = data["paquete"]
        assert pq["marker"] == "MOCG_CODEC_V1"
        assert "layers" in pq and "integra" in pq["layers"]

    def test_round_trip_descomprimir(self):
        # 1. Comprimir
        original_jsonl = _sample_jsonl_bytes()
        original_csv = _sample_csv_bytes()
        files = [
            ("files", ("events.jsonl", original_jsonl, "application/x-ndjson")),
            ("files", ("data.csv", original_csv, "text/csv")),
        ]
        r = requests.post(f"{API}/compresion/toggle", files=files, timeout=60)
        assert r.status_code == 200
        paquete = r.json()["paquete"]

        # 2. Re-subir paquete como .json → descomprime
        pkg_bytes = json.dumps(paquete).encode("utf-8")
        files2 = [("files", ("paquete.mocg.json", pkg_bytes, "application/json"))]
        r2 = requests.post(f"{API}/compresion/toggle", files=files2, timeout=60)
        assert r2.status_code == 200, r2.text
        d2 = r2.json()
        assert d2["accion"] == "descomprimido"
        assert d2["integridad_ok"] is True
        assert d2["n_archivos"] == 2
        # Verify all sha256_ok true and reconstructed bytes match original
        names_to_original = {"events.jsonl": original_jsonl, "data.csv": original_csv}
        for a in d2["archivos"]:
            assert a["sha256_ok"] is True
            recon = base64.b64decode(a["datos_b64"])
            assert recon == names_to_original[a["nombre"]], f"mismatch on {a['nombre']}"


class TestCompresionSistemaHotel:
    """POST /api/compresion/sistema/hotel"""

    def test_hotel_sistema(self):
        r = requests.post(f"{API}/compresion/sistema/hotel", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["accion"] == "comprimido"
        sr = data["shape_report"]
        assert sr["n_events_total"] >= 2, f"expected >=2 events, got {sr['n_events_total']}"
        assert "jsonlines" in sr["file_types"], f"file_types={sr['file_types']}"
