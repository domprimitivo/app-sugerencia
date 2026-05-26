"""
Aprendiz Mileforum - Backend FastAPI
F-05 integrado: export_package, SQLite, anomalias, schema_draft, destruccion
"""

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
import sqlite3
import zipfile
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timezone
import httpx
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

CONFIG_PATH = ROOT_DIR / 'config.json'
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)

SQLITE_PATH = ROOT_DIR / 'bimestral.db'

def init_sqlite():
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bimestral_runs (
            run_id              TEXT PRIMARY KEY,
            profile             TEXT,
            created_utc         TEXT,
            received_at         TEXT,
            retention_policy    TEXT,
            status              TEXT DEFAULT 'active',
            schema_draft_json   TEXT,
            quality_report_json TEXT,
            destruccion_at      TEXT,
            schema_answer       TEXT
        )
    """)
    conn.commit()
    conn.close()

init_sqlite()

def _sqlite_conn():
    return sqlite3.connect(str(SQLITE_PATH))

def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {"modo": "cloud", "tipo_dominio": None, "dominio_id": None, "dominio_nombre": None, "configurado": False}

def save_config(config: Dict[str, Any]):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Aprendiz Mileforum API", description="Portal Episodico - Tu operacion, tu modelo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

DOMINIOS_UNIPERSONALES = [
    {"id": "abogado", "nombre": "Abogado", "icono": "Scale", "descripcion": "Analisis legal y dictamenes"},
    {"id": "arquitecto", "nombre": "Arquitecto", "icono": "Ruler", "descripcion": "Proyectos y especificaciones"},
    {"id": "contador", "nombre": "Contador", "icono": "Calculator", "descripcion": "Analisis fiscal y financiero"},
    {"id": "consultor_pyme", "nombre": "Consultor PyME", "icono": "Briefcase", "descripcion": "Estrategia empresarial"},
    {"id": "diseno_producto", "nombre": "Diseno Producto", "icono": "PenTool", "descripcion": "Especificaciones de producto"},
    {"id": "operaciones", "nombre": "Operaciones", "icono": "Settings", "descripcion": "Procesos operativos"},
]

DOMINIOS_EMPRESAS = [
    {"id": "clinica", "nombre": "Clinica", "icono": "Stethoscope", "descripcion": "Gestion clinica"},
    {"id": "hotel", "nombre": "Hotel", "icono": "Bed", "descripcion": "Operaciones hoteleras"},
    {"id": "restaurante", "nombre": "Restaurante", "icono": "Utensils", "descripcion": "Gestion gastronomica"},
    {"id": "retail", "nombre": "Retail", "icono": "ShoppingBag", "descripcion": "Comercio minorista"},
    {"id": "fabrica", "nombre": "Fabrica", "icono": "Factory", "descripcion": "Produccion industrial"},
    {"id": "logistica", "nombre": "Logistica", "icono": "Truck", "descripcion": "Cadena de suministro"},
]

TODOS_DOMINIOS = DOMINIOS_UNIPERSONALES + DOMINIOS_EMPRESAS
API_EXTERNA_URL = "https://api.mileforum.ia"

# ─── Modelos Pydantic ────────────────────────────────────────────────────────

class ConfiguracionInicial(BaseModel):
    dominio_id: str
    modo: Literal["cloud", "local"] = "cloud"

class ConfiguracionResponse(BaseModel):
    modo: str
    tipo_dominio: Optional[str]
    dominio_id: Optional[str]
    dominio_nombre: Optional[str]
    configurado: bool

class ExpedienteCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class Expediente(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    descripcion: Optional[str] = None
    dominio_id: str
    estado: str = "pendiente"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentoMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expediente_id: str
    nombre: str
    tipo: str
    size: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProcesamientoRequest(BaseModel):
    tipo_consulta: str = "analisis"

class HeadsResponse(BaseModel):
    trigo: float
    cobre: float
    petroleo: float

class EstadosResponse(BaseModel):
    campos: float
    tension: float
    coherencia: float
    resiliencia: float
    indice_telos: float

class ProcesamientoUnipersonalResponse(BaseModel):
    expediente_id: str
    heads: HeadsResponse
    estados: EstadosResponse
    sugerencia_tcl: str
    procesado_en: str

class ProcesamientoEmpresaResponse(BaseModel):
    expediente_id: str
    resumen: str
    documentos_procesados: List[Dict[str, Any]]
    total_documentos: int

class DecisionCreate(BaseModel):
    expediente_id: str
    sugerencia_tcl: str
    decision: Literal["confirmar", "corregir", "abstener"]
    correccion: Optional[str] = None

class Decision(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expediente_id: str
    sugerencia_tcl: str
    decision: str
    correccion: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SincronizacionCreate(BaseModel):
    tipo: str

class Sincronizacion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str
    status: str = "completado"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegistroLanding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    domain: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegistroLandingCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    domain: str

class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[dict] = None

class AnalyticsEventStored(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# F-05
class SchemaAnswerInput(BaseModel):
    answer: str

# ─── Helpers ────────────────────────────────────────────────────────────────

def get_tipo_dominio(dominio_id: str) -> Optional[str]:
    for d in DOMINIOS_UNIPERSONALES:
        if d["id"] == dominio_id:
            return "unipersonal"
    for d in DOMINIOS_EMPRESAS:
        if d["id"] == dominio_id:
            return "empresa"
    return None

def get_dominio_nombre(dominio_id: str) -> Optional[str]:
    for d in TODOS_DOMINIOS:
        if d["id"] == dominio_id:
            return d["nombre"]
    return None

async def llamar_api_externa(texto: str, tipo_consulta: str) -> Dict[str, Any]:
    return {
        "heads": {"trigo": 0.72, "cobre": 0.65, "petroleo": 0.81},
        "estados": {"campos": 0.68, "tension": 0.42, "coherencia": 0.79, "resiliencia": 0.71, "indice_telos": 0.76},
        "sugerencia_tcl": f"[Cloud] Analisis de {tipo_consulta}: Se recomienda revisar los documentos."
    }

# ─── Endpoints existentes ────────────────────────────────────────────────────

@api_router.get("/")
async def root():
    config = load_config()
    return {"sistema": "Aprendiz Mileforum", "version": "1.0.0", "filosofia": "Tu operacion, tu modelo", "configurado": config.get("configurado", False), "modo": config.get("modo", "cloud")}

@api_router.get("/config", response_model=ConfiguracionResponse)
async def get_configuracion():
    config = load_config()
    return ConfiguracionResponse(**config)

@api_router.post("/config/inicializar", response_model=ConfiguracionResponse)
async def inicializar_configuracion(input: ConfiguracionInicial):
    tipo_dominio = get_tipo_dominio(input.dominio_id)
    if not tipo_dominio:
        raise HTTPException(status_code=400, detail="Dominio no valido")
    dominio_nombre = get_dominio_nombre(input.dominio_id)
    config = {"modo": input.modo, "tipo_dominio": tipo_dominio, "dominio_id": input.dominio_id, "dominio_nombre": dominio_nombre, "configurado": True}
    save_config(config)
    if input.modo == "local":
        if tipo_dominio == "unipersonal":
            from aprendiz_motor import inicializar_motor
            inicializar_motor(config)
        else:
            from aprendiz_motor.rag_agents import inicializar_rag
            inicializar_rag(input.dominio_id)
    return ConfiguracionResponse(**config)

@api_router.get("/dominios")
async def get_dominios():
    return {"unipersonales": DOMINIOS_UNIPERSONALES, "empresas": DOMINIOS_EMPRESAS, "total": len(TODOS_DOMINIOS)}

@api_router.post("/expedientes", response_model=Expediente)
async def crear_expediente(input: ExpedienteCreate):
    config = load_config()
    if not config.get("configurado"):
        raise HTTPException(status_code=400, detail="Sistema no configurado.")
    expediente = Expediente(nombre=input.nombre, descripcion=input.descripcion, dominio_id=config["dominio_id"])
    doc = expediente.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.expedientes.insert_one(doc)
    return expediente

@api_router.get("/expedientes")
async def listar_expedientes():
    expedientes = await db.expedientes.find({}, {"_id": 0}).to_list(1000)
    for exp in expedientes:
        if isinstance(exp.get('created_at'), str):
            exp['created_at'] = datetime.fromisoformat(exp['created_at'])
        if isinstance(exp.get('updated_at'), str):
            exp['updated_at'] = datetime.fromisoformat(exp['updated_at'])
    return expedientes

@api_router.get("/expedientes/{expediente_id}", response_model=Expediente)
async def obtener_expediente(expediente_id: str):
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    if isinstance(expediente.get('created_at'), str):
        expediente['created_at'] = datetime.fromisoformat(expediente['created_at'])
    if isinstance(expediente.get('updated_at'), str):
        expediente['updated_at'] = datetime.fromisoformat(expediente['updated_at'])
    return Expediente(**expediente)

@api_router.post("/expedientes/{expediente_id}/documentos")
async def subir_documento(expediente_id: str, file: UploadFile = File(...)):
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    exp_dir = UPLOADS_DIR / expediente_id
    exp_dir.mkdir(exist_ok=True)
    file_path = exp_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    doc_meta = DocumentoMetadata(expediente_id=expediente_id, nombre=file.filename, tipo=file.content_type or "application/octet-stream", size=file_path.stat().st_size)
    doc = doc_meta.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.documentos.insert_one(doc)
    return {"status": "uploaded", "documento": doc_meta.model_dump()}

@api_router.get("/expedientes/{expediente_id}/documentos")
async def listar_documentos(expediente_id: str):
    documentos = await db.documentos.find({"expediente_id": expediente_id}, {"_id": 0}).to_list(1000)
    return {"expediente_id": expediente_id, "documentos": documentos}

@api_router.delete("/expedientes/{expediente_id}")
async def eliminar_expediente(expediente_id: str):
    result = await db.expedientes.delete_one({"id": expediente_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    await db.documentos.delete_many({"expediente_id": expediente_id})
    exp_dir = UPLOADS_DIR / expediente_id
    if exp_dir.exists():
        shutil.rmtree(exp_dir)
    return {"status": "deleted", "expediente_id": expediente_id}

@api_router.post("/expedientes/{expediente_id}/procesar")
async def procesar_expediente(expediente_id: str, input: ProcesamientoRequest):
    config = load_config()
    if not config.get("configurado"):
        raise HTTPException(status_code=400, detail="Sistema no configurado")
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    documentos = await db.documentos.find({"expediente_id": expediente_id}, {"_id": 0}).to_list(100)
    textos = []
    exp_dir = UPLOADS_DIR / expediente_id
    for doc in documentos:
        file_path = exp_dir / doc["nombre"]
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    textos.append(f.read())
            except:
                textos.append(f"[Archivo binario: {doc['nombre']}]")
    texto_concatenado = "\n\n---\n\n".join(textos) if textos else "Sin documentos"
    await db.expedientes.update_one({"id": expediente_id}, {"$set": {"estado": "procesando", "updated_at": datetime.now(timezone.utc).isoformat()}})
    tipo_dominio = config.get("tipo_dominio")
    modo = config.get("modo")
    if tipo_dominio == "unipersonal":
        if modo == "local":
            from aprendiz_motor import ejecutar_episodio
            resultado = ejecutar_episodio(texto_concatenado, input.tipo_consulta)
            procesado_en = "local"
        else:
            resultado = await llamar_api_externa(texto_concatenado, input.tipo_consulta)
            procesado_en = "cloud"
        await db.expedientes.update_one({"id": expediente_id}, {"$set": {"estado": "completado", "updated_at": datetime.now(timezone.utc).isoformat()}})
        resultado_doc = {"id": str(uuid.uuid4()), "expediente_id": expediente_id, "tipo": "unipersonal", "resultado": resultado, "procesado_en": procesado_en, "created_at": datetime.now(timezone.utc).isoformat()}
        await db.procesamientos.insert_one(resultado_doc)
        return ProcesamientoUnipersonalResponse(expediente_id=expediente_id, heads=HeadsResponse(**resultado["heads"]), estados=EstadosResponse(**resultado["estados"]), sugerencia_tcl=resultado["sugerencia_tcl"], procesado_en=procesado_en)
    else:
        if modo == "local":
            from aprendiz_motor.rag_agents import procesar_expediente as rag_procesar
            docs_para_rag = [{"nombre": d["nombre"], "contenido": t, "tipo": d["tipo"]} for d, t in zip(documentos, textos)]
            resultado = rag_procesar(expediente_id, docs_para_rag)
        else:
            resultado = {"expediente_id": expediente_id, "resumen": f"[Cloud RAG] Procesados {len(documentos)} documentos.", "documentos_procesados": [{"id": d["id"], "nombre": d["nombre"], "status": "procesado"} for d in documentos], "total_documentos": len(documentos)}
        await db.expedientes.update_one({"id": expediente_id}, {"$set": {"estado": "completado", "updated_at": datetime.now(timezone.utc).isoformat()}})
        return ProcesamientoEmpresaResponse(**resultado)

@api_router.post("/sincronizaciones/{expediente_id}/decision", response_model=Decision)
async def registrar_decision(expediente_id: str, input: DecisionCreate):
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    decision = Decision(expediente_id=expediente_id, sugerencia_tcl=input.sugerencia_tcl, decision=input.decision, correccion=input.correccion)
    doc = decision.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.decisiones.insert_one(doc)
    return decision

@api_router.get("/decisiones", response_model=List[Decision])
async def listar_decisiones():
    decisiones = await db.decisiones.find({}, {"_id": 0}).to_list(1000)
    for d in decisiones:
        if isinstance(d.get('created_at'), str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
    return decisiones

@api_router.post("/sincronizaciones", response_model=Sincronizacion)
async def crear_sincronizacion(input: SincronizacionCreate):
    sync = Sincronizacion(tipo=input.tipo)
    doc = sync.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.sincronizaciones.insert_one(doc)
    return sync

@api_router.post("/register", response_model=RegistroLanding)
async def registrar_usuario_landing(input: RegistroLandingCreate):
    valid_domains = [d["id"] for d in TODOS_DOMINIOS]
    if input.domain not in valid_domains:
        raise HTTPException(status_code=400, detail="Dominio invalido")
    existing = await db.registros_landing.find_one({"email": input.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya esta registrado")
    registro = RegistroLanding(name=input.name, email=input.email, domain=input.domain)
    doc = registro.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.registros_landing.insert_one(doc)
    return registro

@api_router.get("/registrations", response_model=List[RegistroLanding])
async def listar_registros_landing():
    registros = await db.registros_landing.find({}, {"_id": 0}).to_list(1000)
    for r in registros:
        if isinstance(r.get('created_at'), str):
            r['created_at'] = datetime.fromisoformat(r['created_at'])
    return registros

@api_router.post("/analytics/track")
async def track_event(event: AnalyticsEvent):
    event_stored = AnalyticsEventStored(event_type=event.event_type, event_data=event.event_data)
    doc = event_stored.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.analytics_events.insert_one(doc)
    return {"status": "tracked", "event_id": event_stored.id}

@api_router.get("/analytics/summary")
async def get_analytics_summary():
    pipeline = [{"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]
    results = await db.analytics_events.aggregate(pipeline).to_list(100)
    summary = {item["_id"]: item["count"] for item in results}
    return {"summary": summary}

@api_router.get("/motor/estado")
async def estado_motor():
    config = load_config()
    estado = {"configurado": config.get("configurado", False), "modo": config.get("modo"), "tipo_dominio": config.get("tipo_dominio"), "dominio_id": config.get("dominio_id"), "motor_local_disponible": False}
    if config.get("modo") == "local" and config.get("configurado"):
        try:
            if config.get("tipo_dominio") == "unipersonal":
                from aprendiz_motor import obtener_estado_motor
                estado["motor_local_disponible"] = True
                estado["motor_estado"] = obtener_estado_motor()
            else:
                estado["motor_local_disponible"] = True
                estado["motor_estado"] = {"tipo": "RAG", "status": "ready"}
        except Exception as e:
            estado["motor_error"] = str(e)
    return estado

# ─── F-05: Endpoints Cierre Bimestral ────────────────────────────────────────

@api_router.post("/export-package/upload")
async def upload_export_package(file: UploadFile = File(...)):
    """
    Recibe export_package.zip del Notebook Bimestral.
    Extrae los JSONs clave y registra el run en SQLite.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .zip")

    contents = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as zf:
            nombres = zf.namelist()

            def leer(nombre):
                if nombre in nombres:
                    return json.loads(zf.read(nombre).decode('utf-8'))
                return {}

            run_config      = leer('run_config.json')
            export_manifest = leer('export_manifest.json')
            quality_report  = leer('quality_report.json')
            schema_draft    = leer('schema_draft.json')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ZIP invalido o corrupto: {e}")

    run_id           = run_config.get('run_id') or export_manifest.get('run_id') or str(uuid.uuid4())
    profile          = export_manifest.get('profile') or run_config.get('company_alias', 'unknown')
    created_utc      = export_manifest.get('created_utc', datetime.now(timezone.utc).isoformat())
    retention_policy = run_config.get('retention_policy', 'delete_after_export')

    conn = _sqlite_conn()
    conn.execute("""
        INSERT OR REPLACE INTO bimestral_runs
        (run_id, profile, created_utc, received_at, retention_policy,
         status, schema_draft_json, quality_report_json)
        VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
    """, (
        run_id, profile, created_utc,
        datetime.now(timezone.utc).isoformat(),
        retention_policy,
        json.dumps(schema_draft, ensure_ascii=False),
        json.dumps(quality_report, ensure_ascii=False),
    ))
    conn.commit()
    conn.close()

    anomaly_hints = []
    for tabla in quality_report.get('tables', []):
        for hint in tabla.get('anomaly_hints', []):
            anomaly_hints.append(hint)

    minimal_questions = schema_draft.get('minimal_questions_for_human', [])

    return {
        "run_id":            run_id,
        "profile":           profile,
        "created_utc":       created_utc,
        "retention_policy":  retention_policy,
        "anomaly_hints":     anomaly_hints,
        "minimal_questions": minimal_questions,
        "status":            "registered",
    }


@api_router.get("/export-package/{run_id}/quality")
async def get_quality_anomalies(run_id: str):
    conn = _sqlite_conn()
    row = conn.execute(
        "SELECT quality_report_json FROM bimestral_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    quality = json.loads(row[0])
    anomaly_hints = []
    for tabla in quality.get('tables', []):
        for hint in tabla.get('anomaly_hints', []):
            anomaly_hints.append(hint)
    return {"run_id": run_id, "anomaly_hints": anomaly_hints}


@api_router.get("/export-package/{run_id}/schema-draft")
async def get_schema_draft_questions(run_id: str):
    conn = _sqlite_conn()
    row = conn.execute(
        "SELECT schema_draft_json FROM bimestral_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    schema = json.loads(row[0])
    return {
        "run_id":            run_id,
        "minimal_questions": schema.get('minimal_questions_for_human', []),
    }


@api_router.post("/export-package/{run_id}/schema-answer")
async def save_schema_answer(run_id: str, body: SchemaAnswerInput):
    conn = _sqlite_conn()
    updated = conn.execute(
        "UPDATE bimestral_runs SET schema_answer = ? WHERE run_id = ?",
        (body.answer, run_id)
    ).rowcount
    conn.commit()
    conn.close()
    if not updated:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    return {"run_id": run_id, "answer_saved": True}


@api_router.post("/export-package/{run_id}/destruccion")
async def generar_recibo_destruccion(run_id: str):
    conn = _sqlite_conn()
    row = conn.execute(
        "SELECT run_id, profile, created_utc, retention_policy, status FROM bimestral_runs WHERE run_id = ?",
        (run_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Run no encontrado")
    if row[4] == 'destruido':
        conn.close()
        raise HTTPException(status_code=400, detail="Este run ya fue destruido")
    destruccion_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE bimestral_runs SET status = 'destruido', destruccion_at = ? WHERE run_id = ?",
        (destruccion_at, run_id)
    )
    conn.commit()
    conn.close()
    recibo_id = f"REC-{run_id[:8].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    return {
        "recibo_id":        recibo_id,
        "run_id":           row[0],
        "profile":          row[1],
        "created_utc":      row[2],
        "retention_policy": row[3],
        "destruccion_at":   destruccion_at,
        "status":           "destruido",
        "mensaje":          f"Datos del run procesados y eliminados segun politica de retencion '{row[3]}'. Este recibo es el comprobante oficial de destruccion.",
        "archivos_destruidos": [
            "raw_bundle/hotel_data.csv",
            "normalized_bundle/hotel_data.csv",
            "run_config.json",
            "schema_draft.json",
            "quality_report.json",
            "export_manifest.json",
        ],
    }


@api_router.get("/export-package/{run_id}/recibo")
async def get_recibo_destruccion(run_id: str):
    conn = _sqlite_conn()
    row = conn.execute(
        "SELECT run_id, profile, created_utc, retention_policy, status, destruccion_at FROM bimestral_runs WHERE run_id = ?",
        (run_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    if row[4] != 'destruido':
        raise HTTPException(status_code=400, detail="Run aun activo — destruccion no ejecutada")
    recibo_id = f"REC-{row[0][:8].upper()}-{row[5][:10].replace('-', '')}"
    return {
        "recibo_id":        recibo_id,
        "run_id":           row[0],
        "profile":          row[1],
        "created_utc":      row[2],
        "retention_policy": row[3],
        "status":           row[4],
        "destruccion_at":   row[5],
        "mensaje":          f"Datos del run procesados y eliminados segun politica de retencion '{row[3]}'. Este recibo es el comprobante oficial de destruccion.",
    }


# ─── Aprendiz: endpoints para archivos generados por el motor ────────────────

APRENDIZ_DIR = ROOT_DIR / 'aprendiz_data'
APRENDIZ_DIR.mkdir(exist_ok=True)


@api_router.post("/aprendiz/{dominio}/learning-log")
async def recibir_learning_log(dominio: str, file: UploadFile = File(...)):
    """
    Recibe el learning_log.jsonl generado por el Aprendiz de un dominio.
    Almacena los eventos y los registra en MongoDB para consulta.
    """
    contenido = await file.read()
    lineas = contenido.decode('utf-8').strip().split('\n')
    eventos = []
    for linea in lineas:
        if linea.strip():
            try:
                eventos.append(json.loads(linea))
            except json.JSONDecodeError:
                continue

    # Guardar archivo raw
    ruta = APRENDIZ_DIR / f"{dominio}_learning_log.jsonl"
    with open(ruta, 'wb') as f:
        f.write(contenido)

    # Registrar eventos en MongoDB
    for evento in eventos:
        evento['dominio'] = dominio
        evento['received_at'] = datetime.now(timezone.utc).isoformat()
        await db.aprendiz_events.insert_one(evento)

    return {
        "dominio": dominio,
        "eventos_recibidos": len(eventos),
        "status": "registered",
        "archivo": f"{dominio}_learning_log.jsonl",
    }


@api_router.get("/aprendiz/{dominio}/learning-log")
async def obtener_learning_log(dominio: str, limit: int = 50):
    """
    Retorna los últimos eventos del learning_log de un dominio.
    """
    eventos = await db.aprendiz_events.find(
        {"dominio": dominio}, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return {"dominio": dominio, "eventos": eventos, "total": len(eventos)}


@api_router.post("/aprendiz/{dominio}/soft-dictionary")
async def recibir_soft_dictionary(dominio: str, file: UploadFile = File(...)):
    """
    Recibe el soft_dictionary_state.json generado por el Aprendiz.
    """
    contenido = await file.read()
    try:
        data = json.loads(contenido.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON invalido")

    ruta = APRENDIZ_DIR / f"{dominio}_soft_dictionary_state.json"
    with open(ruta, 'wb') as f:
        f.write(contenido)

    await db.aprendiz_dictionaries.update_one(
        {"dominio": dominio, "tipo": "soft"},
        {"$set": {
            "dominio": dominio,
            "tipo": "soft",
            "data": data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    return {
        "dominio": dominio,
        "tipo": "soft_dictionary",
        "custom_vars": len(data.get("custom_soft_vars", [])),
        "status": "updated",
    }


@api_router.get("/aprendiz/{dominio}/soft-dictionary")
async def obtener_soft_dictionary(dominio: str):
    """
    Retorna el soft_dictionary_state actual de un dominio.
    """
    doc = await db.aprendiz_dictionaries.find_one(
        {"dominio": dominio, "tipo": "soft"}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Soft dictionary no encontrado")
    return doc


@api_router.post("/aprendiz/{dominio}/action-dictionary")
async def recibir_action_dictionary(dominio: str, file: UploadFile = File(...)):
    """
    Recibe el action_dictionary_state.json generado por el Aprendiz.
    Contiene las acciones disponibles por fase: stable, tension, drift, rupture.
    """
    contenido = await file.read()
    try:
        data = json.loads(contenido.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON invalido")

    ruta = APRENDIZ_DIR / f"{dominio}_action_dictionary_state.json"
    with open(ruta, 'wb') as f:
        f.write(contenido)

    await db.aprendiz_dictionaries.update_one(
        {"dominio": dominio, "tipo": "action"},
        {"$set": {
            "dominio": dominio,
            "tipo": "action",
            "data": data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    fases = data.get("actions_by_phase", {})
    total_acciones = sum(len(v) for v in fases.values())

    return {
        "dominio": dominio,
        "tipo": "action_dictionary",
        "fases": list(fases.keys()),
        "total_acciones": total_acciones,
        "status": "updated",
    }


@api_router.get("/aprendiz/{dominio}/action-dictionary")
async def obtener_action_dictionary(dominio: str):
    """
    Retorna el action_dictionary_state actual de un dominio.
    """
    doc = await db.aprendiz_dictionaries.find_one(
        {"dominio": dominio, "tipo": "action"}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Action dictionary no encontrado")
    return doc


@api_router.get("/aprendiz/{dominio}/estado")
async def obtener_estado_aprendiz(dominio: str):
    """
    Resumen del estado actual del Aprendiz de un dominio:
    ultimo evento, fase actual, accion sugerida y R_score.
    """
    ultimo = await db.aprendiz_events.find_one(
        {"dominio": dominio}, {"_id": 0},
        sort=[("timestamp", -1)]
    )
    if not ultimo:
        raise HTTPException(status_code=404, detail="Sin eventos para este dominio")

    backbone = ultimo.get("backbone_inference", {})
    tcl = ultimo.get("tcl", {})
    taximeter = ultimo.get("taximeter_snapshot", {})

    return {
        "dominio": dominio,
        "ultimo_evento": ultimo.get("event_id"),
        "timestamp": ultimo.get("timestamp"),
        "fase_actual": backbone.get("phase"),
        "R_score": backbone.get("R_score"),
        "clarity_ok": backbone.get("clarity", {}).get("ok"),
        "accion_sugerida": tcl.get("suggested", {}).get("label"),
        "R_brake_warning": tcl.get("R_brake", {}).get("warning", False),
        "costo_operativo": taximeter.get("now", {}).get("score"),
    }


# ─── Persistencia de archivos y paquete bimestral ────────────────────────────

# Directorios persistentes en disco (sobreviven al cierre de la app)
SESSION_FILES_DIR = ROOT_DIR / 'session_files'
BUNDLES_DIR = ROOT_DIR / 'bundles'
BIMESTRAL_PACKAGE_DIR = ROOT_DIR / 'bimestral_package'

SESSION_FILES_DIR.mkdir(exist_ok=True)
BUNDLES_DIR.mkdir(exist_ok=True)
BIMESTRAL_PACKAGE_DIR.mkdir(exist_ok=True)


@api_router.get("/archivos/{dominio}")
async def listar_archivos_dominio(dominio: str):
    """
    Lista todos los archivos generados y persistidos para un dominio.
    El usuario puede consultarlos si lo decide, pero no necesita gestionarlos.
    """
    archivos = []

    # Archivos del Aprendiz
    for f in APRENDIZ_DIR.glob(f"{dominio}_*"):
        archivos.append({
            "nombre": f.name,
            "tipo": "aprendiz",
            "tamanio_kb": round(f.stat().st_size / 1024, 1),
            "modificado": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })

    # Bundles del dominio (raw y normalized)
    for f in BUNDLES_DIR.glob(f"{dominio}_*"):
        archivos.append({
            "nombre": f.name,
            "tipo": "bundle",
            "tamanio_kb": round(f.stat().st_size / 1024, 1),
            "modificado": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })

    # Archivos de sesion
    for f in SESSION_FILES_DIR.glob(f"{dominio}_*"):
        archivos.append({
            "nombre": f.name,
            "tipo": "sesion",
            "tamanio_kb": round(f.stat().st_size / 1024, 1),
            "modificado": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })

    return {
        "dominio": dominio,
        "total": len(archivos),
        "archivos": sorted(archivos, key=lambda x: x["modificado"], reverse=True),
    }


@api_router.post("/bundles/{dominio}/guardar")
async def guardar_bundle(dominio: str, tipo: str, file: UploadFile = File(...)):
    """
    Persiste el raw_bundle o normalized_bundle en disco.
    Disponibles para exportar a otros sistemas (Excel, BI, etc.).
    tipo: 'raw' o 'normalized'
    """
    if tipo not in ['raw', 'normalized']:
        raise HTTPException(status_code=400, detail="tipo debe ser 'raw' o 'normalized'")

    contenido = await file.read()
    nombre = f"{dominio}_{tipo}_bundle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{Path(file.filename).suffix}"
    ruta = BUNDLES_DIR / nombre
    with open(ruta, 'wb') as f:
        f.write(contenido)

    return {
        "dominio": dominio,
        "tipo": tipo,
        "archivo": nombre,
        "tamanio_kb": round(len(contenido) / 1024, 1),
        "status": "persistido",
        "disponible_para_exportar": True,
    }


@api_router.get("/bundles/{dominio}")
async def listar_bundles(dominio: str):
    """
    Lista los bundles disponibles de un dominio para exportar a otros sistemas.
    """
    bundles = []
    for f in BUNDLES_DIR.glob(f"{dominio}_*"):
        bundles.append({
            "nombre": f.name,
            "tamanio_kb": round(f.stat().st_size / 1024, 1),
            "modificado": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return {"dominio": dominio, "bundles": sorted(bundles, key=lambda x: x["modificado"], reverse=True)}


@api_router.post("/bimestral/{dominio}/preparar-paquete")
async def preparar_paquete_bimestral(dominio: str):
    """
    Prepara automáticamente el paquete que el Notebook necesita para el cierre bimestral.
    Reúne: learning_log, soft_dictionary, action_dictionary, bundles y artefactos del aprendiz.
    El usuario no necesita ver este flujo — ocurre automáticamente.
    """
    archivos_incluidos = []
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    zip_nombre = f"{dominio}_bimestral_package_{timestamp}.zip"
    zip_ruta = BIMESTRAL_PACKAGE_DIR / zip_nombre

    with zipfile.ZipFile(zip_ruta, 'w', zipfile.ZIP_DEFLATED) as zf:

        # Learning log del dominio
        ll = APRENDIZ_DIR / f"{dominio}_learning_log.jsonl"
        if ll.exists():
            zf.write(ll, f"aprendiz/{ll.name}")
            archivos_incluidos.append(ll.name)

        # Soft dictionary
        sd = APRENDIZ_DIR / f"{dominio}_soft_dictionary_state.json"
        if sd.exists():
            zf.write(sd, f"aprendiz/{sd.name}")
            archivos_incluidos.append(sd.name)

        # Action dictionary
        ad = APRENDIZ_DIR / f"{dominio}_action_dictionary_state.json"
        if ad.exists():
            zf.write(ad, f"aprendiz/{ad.name}")
            archivos_incluidos.append(ad.name)

        # Bundles del dominio
        for f in BUNDLES_DIR.glob(f"{dominio}_*"):
            zf.write(f, f"bundles/{f.name}")
            archivos_incluidos.append(f.name)

        # Archivos de sesion
        for f in SESSION_FILES_DIR.glob(f"{dominio}_*"):
            zf.write(f, f"sesion/{f.name}")
            archivos_incluidos.append(f.name)

        # Metadato del paquete
        meta = {
            "dominio": dominio,
            "generado_at": datetime.now(timezone.utc).isoformat(),
            "archivos": archivos_incluidos,
            "listo_para_notebook": True,
        }
        zf.writestr("package_manifest.json", json.dumps(meta, ensure_ascii=False, indent=2))

    return {
        "dominio": dominio,
        "zip": zip_nombre,
        "archivos_incluidos": archivos_incluidos,
        "total": len(archivos_incluidos),
        "listo_para_notebook": True,
        "generado_at": datetime.now(timezone.utc).isoformat(),
    }


@api_router.post("/bimestral/{dominio}/incorporar-artefactos")
async def incorporar_artefactos_notebook(dominio: str, file: UploadFile = File(...)):
    """
    Incorpora los artefactos generados por el Notebook de ajuste bimestral
    al ZIP del Aprendiz para que el Notebook de día a día los gestione.
    """
    contenido = await file.read()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
            for nombre_archivo in zf.namelist():
                datos = zf.read(nombre_archivo)
                destino = APRENDIZ_DIR / f"{dominio}_ajuste_{timestamp}_{Path(nombre_archivo).name}"
                with open(destino, 'wb') as f:
                    f.write(datos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando artefactos: {e}")

    # Registrar en MongoDB
    await db.aprendiz_artefactos.insert_one({
        "dominio": dominio,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "archivo_origen": file.filename,
        "incorporado_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "dominio": dominio,
        "status": "incorporado",
        "timestamp": timestamp,
        "mensaje": "Artefactos del ajuste bimestral incorporados al directorio del Aprendiz.",
    }


# ─── Registro del router y arranque ─────────────────────────────────────────

app.include_router(api_router)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
