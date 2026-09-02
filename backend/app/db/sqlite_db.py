"""
c
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

DB_PATH = Path("data/mileforum.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── Context manager para conexiones ─────────────────────────────
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # devuelve dicts
    conn.execute("PRAGMA journal_mode=WAL")  # más rápido
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Inicialización de tablas ─────────────────────────────────────
def init_db():
    """Crea todas las tablas si no existen."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS expedientes (
            id              TEXT PRIMARY KEY,
            dominio         TEXT NOT NULL,
            tipo            TEXT NOT NULL DEFAULT 'unipersonal',
            modo            TEXT NOT NULL DEFAULT 'cloud',
            titulo          TEXT,
            estado          TEXT NOT NULL DEFAULT 'activo',
            fase_actual     INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            metadata        TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS documentos (
            id              TEXT PRIMARY KEY,
            expediente_id   TEXT NOT NULL,
            nombre_archivo  TEXT NOT NULL,
            tipo_archivo    TEXT,
            size_bytes      INTEGER,
            ruta_local      TEXT,
            features_json   TEXT DEFAULT '{}',
            procesado       INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (expediente_id) REFERENCES expedientes(id)
        );

        CREATE TABLE IF NOT EXISTS sincronizaciones (
            id              TEXT PRIMARY KEY,
            expediente_id   TEXT NOT NULL,
            run_id          TEXT,
            dominio         TEXT,
            fase_numero     INTEGER,
            fase_nombre     TEXT,
            tension         REAL,
            resilencia      REAL,
            coherencia      REAL,
            trigo           REAL,
            cobre           REAL,
            petroleo        REAL,
            accion_sugerida TEXT,
            confianza       REAL,
            snapshot_json   TEXT DEFAULT '{}',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (expediente_id) REFERENCES expedientes(id)
        );

        CREATE TABLE IF NOT EXISTS decisiones (
            id              TEXT PRIMARY KEY,
            sincronizacion_id TEXT NOT NULL,
            expediente_id   TEXT NOT NULL,
            tipo            TEXT NOT NULL,
            accion_ejecutada TEXT,
            corrección      TEXT,
            log_discrepancia TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (sincronizacion_id) REFERENCES sincronizaciones(id),
            FOREIGN KEY (expediente_id) REFERENCES expedientes(id)
        );

        CREATE INDEX IF NOT EXISTS idx_docs_exp
            ON documentos(expediente_id);
        CREATE INDEX IF NOT EXISTS idx_sinc_exp
            ON sincronizaciones(expediente_id);
        CREATE INDEX IF NOT EXISTS idx_dec_exp
            ON decisiones(expediente_id);
        """)


# ── EXPEDIENTES ───────────────────────────────────────────────────
def crear_expediente(id: str, dominio: str, tipo: str = "unipersonal",
                     modo: str = "cloud", titulo: str = None) -> dict:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO expedientes
            (id, dominio, tipo, modo, titulo, estado, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'activo', ?, ?)
        """, (id, dominio, tipo, modo, titulo or id, now, now))
    return obtener_expediente(id)


def obtener_expediente(id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM expedientes WHERE id = ?", (id,)
        ).fetchone()
    return dict(row) if row else None


def listar_expedientes(dominio: str = None, limite: int = 50) -> list:
    with get_conn() as conn:
        if dominio:
            rows = conn.execute(
                "SELECT * FROM expedientes WHERE dominio=? ORDER BY updated_at DESC LIMIT ?",
                (dominio, limite)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM expedientes ORDER BY updated_at DESC LIMIT ?",
                (limite,)
            ).fetchall()
    return [dict(r) for r in rows]


def actualizar_fase_expediente(id: str, fase: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE expedientes SET fase_actual=?, updated_at=?
            WHERE id=?
        """, (fase, datetime.utcnow().isoformat(), id))


# ── DOCUMENTOS ────────────────────────────────────────────────────
def registrar_documento(id: str, expediente_id: str, nombre: str,
                        tipo: str, size: int, ruta: str,
                        features: dict) -> dict:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO documentos
            (id, expediente_id, nombre_archivo, tipo_archivo,
             size_bytes, ruta_local, features_json, procesado, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (id, expediente_id, nombre, tipo, size, ruta,
              json.dumps(features), now))
    return obtener_documento(id)


def obtener_documento(id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM documentos WHERE id=?", (id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["features"] = json.loads(d.pop("features_json", "{}"))
    return d


def listar_documentos(expediente_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos WHERE expediente_id=? ORDER BY created_at DESC",
            (expediente_id,)
        ).fetchall()
    docs = []
    for r in rows:
        d = dict(r)
        d["features"] = json.loads(d.pop("features_json", "{}"))
        docs.append(d)
    return docs


# ── SINCRONIZACIONES ─────────────────────────────────────────────
def registrar_sincronizacion(expediente_id: str, snapshot: dict) -> dict:
    """
    Guarda el resultado del motor (fase, hélice, acción sugerida).
    Corresponde al paso 'Almacena Archivos/Metadata' del diagrama.
    """
    now = datetime.utcnow().isoformat()
    helice = snapshot.get("helice", {})
    inputs = snapshot.get("inputs", {})
    fase   = snapshot.get("fase", {})
    sid    = snapshot.get("run_id", f"sinc_{now}")

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sincronizaciones
            (id, expediente_id, run_id, dominio, fase_numero, fase_nombre,
             tension, resilencia, coherencia, trigo, cobre, petroleo,
             accion_sugerida, confianza, snapshot_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sid, expediente_id,
            snapshot.get("run_id"),
            snapshot.get("dominio"),
            fase.get("numero"), fase.get("nombre"),
            helice.get("tension"), helice.get("resilencia"),
            helice.get("coherencia"),
            inputs.get("trigo"), inputs.get("cobre"), inputs.get("petroleo"),
            snapshot.get("accion_sugerida"),
            snapshot.get("confianza"),
            json.dumps(snapshot),
            now
        ))

    actualizar_fase_expediente(expediente_id, fase.get("numero", 0))
    return {"id": sid, "expediente_id": expediente_id, **snapshot}


def listar_sincronizaciones(expediente_id: str) -> list:
    """Devuelve la trayectoria completa de un expediente."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM sincronizaciones
            WHERE expediente_id=?
            ORDER BY created_at ASC
        """, (expediente_id,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["snapshot"] = json.loads(d.pop("snapshot_json", "{}"))
        result.append(d)
    return result


# ── DECISIONES ────────────────────────────────────────────────────
def registrar_decision(sincronizacion_id: str, expediente_id: str,
                       tipo: str, accion: str = None,
                       correccion: str = None,
                       log_discrepancia: str = None) -> dict:
    """
    tipo: 'confirmar' | 'rechazar' | 'abstencion'
    Corresponde a la Fase 3 del diagrama de secuencia.
    """
    now = datetime.utcnow().isoformat()
    did = f"dec_{expediente_id}_{now}"
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO decisiones
            (id, sincronizacion_id, expediente_id, tipo,
             accion_ejecutada, corrección, log_discrepancia, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (did, sincronizacion_id, expediente_id, tipo,
              accion, correccion, log_discrepancia, now))
    return {
        "id": did, "sincronizacion_id": sincronizacion_id,
        "expediente_id": expediente_id, "tipo": tipo,
        "accion_ejecutada": accion, "created_at": now
    }


def listar_decisiones(expediente_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM decisiones WHERE expediente_id=?
            ORDER BY created_at DESC
        """, (expediente_id,)).fetchall()
    return [dict(r) for r in rows]
