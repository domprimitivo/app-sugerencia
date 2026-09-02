"""
Compresión Geométrica — Códec MOCG (100% local, soberano).

Puerto compacto y fiel del notebook `mocg_codec_geometrico.ipynb`.
Python puro + numpy. Sin gradio, plotly ni scipy.

Dos funciones en un solo proceso:
  1. Ordenar y comprimir: clasifica por contenido → normaliza → manifold
     incremental → comprime en tres capas (íntegra · inferible · geométrica)
     + reporte de forma con los eventos que NO entraron (anomalías).
  2. Descomprimir: reconstrucción exacta desde la capa íntegra (lossless).

El paquete comprimido lleva un marcador para poder ALTERNAR:
si ya está comprimido se descomprime; si no, se comprime.
"""

import json
import re
import csv
import gzip
import base64
import hashlib
import uuid
import time
import io
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

import numpy as np

# Marcador del formato del paquete comprimido
CODEC_MARKER = "MOCG_CODEC_V1"

FILE_TYPES = {
    'apache_log':   'Apache/Nginx access log (CLF)',
    'syslog':       'Syslog',
    'csv_generic':  'CSV genérico',
    'jsonlines':    'JSONLines',
    'json_object':  'JSON objeto/array',
    'text_generic': 'Texto genérico',
    'binary':       'Binario',
    'unknown':      'Formato no reconocido',
}

_RE_CLF = re.compile(r'^[\d\.]+\s+\S+\s+\S+\s+\[\d{2}/\w+/\d{4}')
_RE_CLF_FULL = re.compile(
    r'(?P<ip>[\d\.]+|[\da-fA-F:]+)\s+\S+\s+\S+\s+'
    r'\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\d+|-)'
    r'(?:\s+"(?P<ref>[^"]*)"\s+"(?P<ua>[^"]*)")?'
    r'(?:\s+(?P<rt>[\d\.]+))?'
)
_RE_SYSLOG = re.compile(r'^\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}|^<\d+>\d{4}-\d{2}-\d{2}')


# ─── Clasificación por contenido (no por extensión) ──────────────────────────
def detectar_tipo(nombre: str, datos: bytes) -> str:
    try:
        texto = datos.decode('utf-8')
    except Exception:
        return 'binary'
    lineas = [l.strip() for l in texto.split('\n') if l.strip()][:10]
    if not lineas:
        return 'unknown'
    first = lineas[0]
    try:
        obj = json.loads(texto)
        return 'json_object' if isinstance(obj, (dict, list)) else 'unknown'
    except Exception:
        pass
    # ¿JSONLines? (varias líneas JSON independientes)
    json_lines = 0
    for l in lineas:
        try:
            json.loads(l)
            json_lines += 1
        except Exception:
            break
    if json_lines >= 2:
        return 'jsonlines'
    if _RE_CLF.match(first):
        return 'apache_log'
    if _RE_SYSLOG.match(first):
        return 'syslog'
    if ',' in first and len(lineas) >= 2 and all(',' in l for l in lineas[:3]):
        return 'csv_generic'
    return 'text_generic'


# ─── Evento normalizado (átomo del códec) ────────────────────────────────────
@dataclass
class NormalizedEvent:
    event_id:    str
    timestamp:   float
    source_file: str
    file_type:   str
    entity_id:   str
    action:      str
    object_id:   str
    result:      str
    severity:    str
    dims:        Dict[str, float] = field(default_factory=dict)


def _sev_from_status(status: int) -> str:
    if status < 400:
        return 'low'
    if status < 500:
        return 'medium'
    return 'high'


def _parse_ts(raw: str) -> float:
    for fmt in ('%d/%b/%Y:%H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(raw.strip(), fmt).timestamp()
        except Exception:
            continue
    return time.time()


def _norm_apache(line: str, src: str) -> Optional[NormalizedEvent]:
    m = _RE_CLF_FULL.match(line.strip())
    if not m:
        return None
    status = int(m.group('status'))
    rt = float(m.group('rt')) if m.group('rt') else 0.0
    size = int(m.group('size')) if m.group('size') != '-' else 0
    return NormalizedEvent(
        event_id=str(uuid.uuid4())[:8], timestamp=_parse_ts(m.group('time')),
        source_file=src, file_type='apache_log', entity_id=m.group('ip'),
        action=m.group('method').upper(), object_id=(m.group('path') or '/').split('?')[0],
        result='success' if status < 400 else 'failure', severity=_sev_from_status(status),
        dims={'status_code': status / 599, 'response_time': min(rt / 10.0, 1.0),
              'response_size': min(size / 100000, 1.0), 'is_error': float(status >= 400)},
    )


def _norm_generic_obj(obj: dict, src: str, ftype: str) -> NormalizedEvent:
    ts_raw = obj.get('timestamp') or obj.get('time') or obj.get('ts') or ''
    if isinstance(ts_raw, (int, float)):
        ts = float(ts_raw)
    elif isinstance(ts_raw, str) and ts_raw:
        ts = _parse_ts(ts_raw)
    else:
        ts = time.time()
    entity = str(obj.get('entity_id') or obj.get('client_ip') or obj.get('src_ip')
                 or obj.get('user') or obj.get('id') or 'anon')
    action = str(obj.get('action') or obj.get('method') or obj.get('event') or 'event')
    result = str(obj.get('result') or obj.get('status') or 'unknown')
    sev = str(obj.get('severity') or 'low').lower()
    if sev not in ('low', 'medium', 'high', 'critical'):
        sev = 'low'
    dims = {k: float(v) for k, v in obj.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return NormalizedEvent(
        event_id=str(uuid.uuid4())[:8], timestamp=ts, source_file=src, file_type=ftype,
        entity_id=entity, action=action, object_id=str(obj.get('object_id', '')),
        result='failure' if 'fail' in result.lower() or 'error' in result.lower() else 'success',
        severity=sev, dims=dims,
    )


def normalizar_archivo(nombre: str, datos: bytes, ftype: str) -> List[NormalizedEvent]:
    eventos: List[NormalizedEvent] = []
    try:
        texto = datos.decode('utf-8')
    except Exception:
        texto = ''
    if ftype == 'apache_log':
        for line in texto.split('\n'):
            if line.strip():
                e = _norm_apache(line, nombre)
                if e:
                    eventos.append(e)
    elif ftype == 'jsonlines':
        for line in texto.split('\n'):
            if line.strip():
                try:
                    eventos.append(_norm_generic_obj(json.loads(line), nombre, ftype))
                except Exception:
                    continue
    elif ftype == 'json_object':
        try:
            obj = json.loads(texto)
            if isinstance(obj, list):
                for it in obj:
                    if isinstance(it, dict):
                        eventos.append(_norm_generic_obj(it, nombre, ftype))
            elif isinstance(obj, dict):
                eventos.append(_norm_generic_obj(obj, nombre, ftype))
        except Exception:
            pass
    elif ftype == 'csv_generic':
        try:
            reader = csv.DictReader(io.StringIO(texto))
            for row in reader:
                eventos.append(_norm_generic_obj(dict(row), nombre, ftype))
        except Exception:
            pass
    else:
        # syslog / texto / binario / desconocido → un evento mínimo por archivo
        eventos.append(NormalizedEvent(
            event_id=str(uuid.uuid4())[:8], timestamp=time.time(), source_file=nombre,
            file_type=ftype, entity_id=nombre, action='file', object_id=nombre,
            result='unknown', severity='low',
            dims={'size': min(len(datos) / 1_000_000, 1.0)},
        ))
    return eventos


# ─── Manifold incremental (8D) ───────────────────────────────────────────────
CODEC_DIMS = ['error_rate', 'severity_score', 'action_diversity', 'temporal_regularity',
              'volume_anomaly', 'dissonance_mean', 'failure_streak', 'off_hours_ratio']
SEV_WEIGHTS = {'low': 0.1, 'medium': 0.3, 'high': 0.6, 'critical': 1.0}


@dataclass
class EntityContext:
    entity_id: str
    n_events: int = 0
    n_fail: int = 0
    actions: set = field(default_factory=set)
    vector: np.ndarray = field(default_factory=lambda: np.full(8, 0.1, dtype=np.float32))
    baseline: np.ndarray = field(default_factory=lambda: np.full(8, 0.1, dtype=np.float32))
    last_ts: float = 0.0
    dis_history: List[float] = field(default_factory=list)


class IncrementalManifold:
    ALPHA = 0.05
    DIS_THRESH = 0.35
    MIN_EVENTS = 10

    def __init__(self):
        self._entities: Dict[str, EntityContext] = {}
        self._ts_window: Dict[str, list] = defaultdict(list)
        self._fail_streak: Dict[str, int] = defaultdict(int)

    def _vector(self, evt: NormalizedEvent, ctx: EntityContext) -> np.ndarray:
        tsw = self._ts_window[evt.entity_id]
        tsw.append(evt.timestamp)
        if len(tsw) > 50:
            tsw.pop(0)
        # regularidad temporal
        if len(tsw) >= 3:
            difs = np.diff(sorted(tsw))
            reg = 1.0 / (1.0 + float(np.std(difs)) / (float(np.mean(difs)) + 1e-6))
        else:
            reg = 0.5
        if evt.result == 'failure':
            self._fail_streak[evt.entity_id] += 1
        else:
            self._fail_streak[evt.entity_id] = 0
        error_rate = ctx.n_fail / max(ctx.n_events, 1)
        sev = SEV_WEIGHTS.get(evt.severity, 0.1)
        diversity = min(len(ctx.actions) / 10.0, 1.0)
        volume = min(ctx.n_events / 500.0, 1.0)
        dis_mean = float(np.mean(ctx.dis_history)) if ctx.dis_history else 0.1
        streak = min(self._fail_streak[evt.entity_id] / 10.0, 1.0)
        dt = datetime.fromtimestamp(evt.timestamp, tz=timezone.utc)
        off_hours = float(dt.hour < 8 or dt.hour >= 20)
        return np.array([error_rate, sev, diversity, reg, volume,
                         dis_mean, streak, off_hours], dtype=np.float32)

    def process_event(self, evt: NormalizedEvent):
        ctx = self._entities.get(evt.entity_id)
        if ctx is None:
            ctx = EntityContext(entity_id=evt.entity_id)
            self._entities[evt.entity_id] = ctx
        ctx.n_events += 1
        ctx.actions.add(evt.action)
        if evt.result == 'failure':
            ctx.n_fail += 1
        ctx.vector = self._vector(evt, ctx)
        ctx.last_ts = evt.timestamp

        if ctx.n_events < self.MIN_EVENTS:
            # aprendizaje del baseline (aún inestable)
            ctx.baseline = (1 - self.ALPHA) * ctx.baseline + self.ALPHA * ctx.vector
            dis = float(np.linalg.norm(ctx.vector - ctx.baseline))
            ctx.dis_history.append(dis)
            return dis, False

        dis = float(np.linalg.norm(ctx.vector - ctx.baseline)) / np.sqrt(8)
        ctx.dis_history.append(dis)
        is_anom = dis > self.DIS_THRESH
        if not is_anom:
            # solo lo normal actualiza el baseline (no se contamina con anomalías)
            ctx.baseline = (1 - self.ALPHA) * ctx.baseline + self.ALPHA * ctx.vector
        return dis, is_anom


# ─── Compresor en tres etapas ────────────────────────────────────────────────
def _layer_inferible(events, manifold):
    if not events:
        return []
    vecs = []
    for evt in events:
        ctx = manifold._entities.get(evt.entity_id)
        vecs.append(ctx.vector if ctx is not None else np.zeros(8, dtype=np.float32))
    X = np.array(vecs, dtype=np.float32)
    Xc = X - X.mean(axis=0)
    try:
        cov = np.cov(Xc.T)
        vals, vecs_pc = np.linalg.eigh(cov)
        idx = np.argsort(vals)[::-1][:2]
        proj = Xc @ vecs_pc[:, idx]
    except Exception:
        proj = Xc[:, :2]
    out = []
    for i, evt in enumerate(events):
        p = proj[i] if i < len(proj) else np.zeros(2)
        out.append({'event_id': evt.event_id, 'timestamp': round(evt.timestamp, 1),
                    'entity_id': evt.entity_id, 'pc1': round(float(p[0]), 4),
                    'pc2': round(float(p[1]), 4) if len(p) > 1 else 0.0,
                    'result': evt.result, 'severity': evt.severity})
    return out


def _layer_geometrica(events, manifold, dis_map):
    out = []
    for evt in events:
        ctx = manifold._entities.get(evt.entity_id)
        pos = ctx.vector.tolist() if ctx is not None else [0.0] * 8
        out.append({'entity_id': evt.entity_id,
                    'pos': [round(x, 4) for x in pos],
                    'dis': round(dis_map.get(evt.event_id, 0.0), 4)})
    return out


def comprimir(archivos: List[dict], org_id: str = 'ORG-001', bimester: str = '',
              dis_threshold: float = 0.35) -> dict:
    """
    archivos: lista de {'nombre': str, 'datos': bytes}
    Devuelve el paquete comprimido (dict serializable a JSON) con marcador,
    tres capas y el reporte de forma.
    """
    # ── Capa íntegra (lossless): originales gzip+base64 ──
    integra = []
    original_bytes = 0
    for a in archivos:
        datos = a['datos']
        original_bytes += len(datos)
        integra.append({
            'nombre': a['nombre'],
            'sha256': hashlib.sha256(datos).hexdigest(),
            'gz_b64': base64.b64encode(gzip.compress(datos)).decode('ascii'),
        })

    # ── Clasificar + normalizar ──
    all_events: List[NormalizedEvent] = []
    file_types: Dict[str, int] = defaultdict(int)
    for a in archivos:
        ftype = detectar_tipo(a['nombre'], a['datos'])
        file_types[ftype] += 1
        all_events.extend(normalizar_archivo(a['nombre'], a['datos'], ftype))
    all_events.sort(key=lambda e: e.timestamp)

    # ── Manifold incremental ──
    manifold = IncrementalManifold()
    manifold.DIS_THRESH = dis_threshold
    dis_map: Dict[str, float] = {}
    anomalies = []
    sev_count = defaultdict(int)
    for evt in all_events:
        dis, is_anom = manifold.process_event(evt)
        dis_map[evt.event_id] = dis
        if is_anom:
            ctx = manifold._entities.get(evt.entity_id)
            hot = {}
            if ctx is not None:
                diff = np.abs(ctx.vector - ctx.baseline)
                hot = {CODEC_DIMS[i]: round(float(diff[i]), 4)
                       for i in range(8) if diff[i] > dis_threshold}
            sev_count[evt.severity] += 1
            anomalies.append({'event_id': evt.event_id, 'timestamp': evt.timestamp,
                              'entity_id': evt.entity_id, 'action': evt.action,
                              'severity': evt.severity, 'dissonance': round(dis, 4),
                              'hot_dims': hot, 'source_file': evt.source_file})

    n_total = len(all_events)
    n_out = len(anomalies)
    n_in = n_total - n_out

    inferible = _layer_inferible(all_events, manifold)
    geometrica = _layer_geometrica(all_events, manifold, dis_map)

    paquete = {
        'marker': CODEC_MARKER,
        'org_id': org_id,
        'bimester': bimester,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'n_files': len(archivos),
        'layers': {
            'integra': integra,        # reconstrucción exacta
            'inferible': inferible,    # relaciones geométricas (PCA 2D)
            'geometrica': geometrica,  # forma pura + disonancia
        },
        'shape_report': {
            'org_id': org_id, 'bimester': bimester,
            'n_files': len(archivos), 'n_events_total': n_total,
            'n_in_form': n_in, 'n_out_form': n_out,
            'pct_in_form': round(100 * n_in / n_total, 1) if n_total else 0.0,
            'file_types': dict(file_types),
            'anomaly_severity': dict(sev_count),
            'top_anomalous': sorted(
                [{'entity': a['entity_id'], 'dis': a['dissonance'],
                  'hot_dims': list(a['hot_dims'].keys())} for a in anomalies],
                key=lambda x: x['dis'], reverse=True)[:10],
            'anomalies': anomalies,
            'manifold': {'n_entities': len(manifold._entities)},
        },
    }

    # ratio de compresión (íntegra comprimida vs original)
    codec_bytes = len(json.dumps(paquete).encode('utf-8'))
    paquete['shape_report']['compression'] = {
        'original_bytes': original_bytes,
        'codec_bytes': codec_bytes,
        'ratio': round(original_bytes / codec_bytes, 2) if codec_bytes else 0.0,
    }
    return paquete


def es_paquete_comprimido(datos: bytes) -> bool:
    """Detecta si los bytes son un paquete del códec (para alternar)."""
    try:
        obj = json.loads(datos.decode('utf-8'))
        return isinstance(obj, dict) and obj.get('marker') == CODEC_MARKER
    except Exception:
        return False


def descomprimir(paquete: dict) -> List[dict]:
    """
    Reconstrucción exacta (lossless) desde la capa íntegra.
    Devuelve lista de {'nombre': str, 'datos': bytes, 'sha256_ok': bool}.
    """
    if paquete.get('marker') != CODEC_MARKER:
        raise ValueError("No es un paquete de compresión geométrica válido.")
    salida = []
    for item in paquete.get('layers', {}).get('integra', []):
        datos = gzip.decompress(base64.b64decode(item['gz_b64']))
        sha_ok = hashlib.sha256(datos).hexdigest() == item.get('sha256')
        salida.append({'nombre': item['nombre'], 'datos': datos, 'sha256_ok': sha_ok})
    return salida
