"""
Aprendiz Mileforum - Backend FastAPI
====================================
Portal Episódico: Interfaz entre profesionales/empresas y modelos de IA especializados.

Filosofía: "Caja con agujeros" - Ligera en interfaz, capaz de manejar datos densos.
Modo de Operación: DUAL (Cloud + Local)

Motores:
- Motor Aprendiz (unipersonales): Modelo multicefalar con aprendizaje micro-operacional
- Motor RAG (empresas): Agentes de procesamiento documental
"""

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timezone
import httpx
import shutil

# Configuración de rutas
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Cargar configuración
CONFIG_PATH = ROOT_DIR / 'config.json'
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)

def load_config() -> Dict[str, Any]:
    """Carga la configuración desde config.json"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {
        "modo": "cloud",
        "tipo_dominio": None,
        "dominio_id": None,
        "dominio_nombre": None,
        "configurado": False
    }

def save_config(config: Dict[str, Any]):
    """Guarda la configuración en config.json"""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(
    title="Aprendiz Mileforum API",
    description="Portal Episódico - Tu operación, tu modelo",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============================================================================
# DOMINIOS DISPONIBLES
# ============================================================================

DOMINIOS_UNIPERSONALES = [
    {"id": "abogado", "nombre": "Abogado", "icono": "Scale", "descripcion": "Análisis legal y dictámenes"},
    {"id": "arquitecto", "nombre": "Arquitecto", "icono": "Ruler", "descripcion": "Proyectos y especificaciones"},
    {"id": "contador", "nombre": "Contador", "icono": "Calculator", "descripcion": "Análisis fiscal y financiero"},
    {"id": "consultor_pyme", "nombre": "Consultor PyME", "icono": "Briefcase", "descripcion": "Estrategia empresarial"},
    {"id": "diseno_producto", "nombre": "Diseño Producto", "icono": "PenTool", "descripcion": "Especificaciones de producto"},
    {"id": "operaciones", "nombre": "Operaciones", "icono": "Settings", "descripcion": "Procesos operativos"},
]

DOMINIOS_EMPRESAS = [
    {"id": "clinica", "nombre": "Clínica", "icono": "Stethoscope", "descripcion": "Gestión clínica"},
    {"id": "hotel", "nombre": "Hotel", "icono": "Bed", "descripcion": "Operaciones hoteleras"},
    {"id": "restaurante", "nombre": "Restaurante", "icono": "Utensils", "descripcion": "Gestión gastronómica"},
    {"id": "retail", "nombre": "Retail", "icono": "ShoppingBag", "descripcion": "Comercio minorista"},
    {"id": "fabrica", "nombre": "Fábrica", "icono": "Factory", "descripcion": "Producción industrial"},
    {"id": "logistica", "nombre": "Logística", "icono": "Truck", "descripcion": "Cadena de suministro"},
]

TODOS_DOMINIOS = DOMINIOS_UNIPERSONALES + DOMINIOS_EMPRESAS

# API Externa (Modo Cloud)
API_EXTERNA_URL = "https://api.mileforum.ia"

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

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
    estado: str = "pendiente"  # pendiente, procesando, completado
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
    tipo_consulta: str = "analisis"  # analisis, revision, dictamen, consulta

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
    procesado_en: str  # "local" o "cloud"

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
    tipo: str  # "subida", "descarga", "actualizacion"

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

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_tipo_dominio(dominio_id: str) -> Optional[str]:
    """Determina si un dominio es unipersonal o empresa"""
    for d in DOMINIOS_UNIPERSONALES:
        if d["id"] == dominio_id:
            return "unipersonal"
    for d in DOMINIOS_EMPRESAS:
        if d["id"] == dominio_id:
            return "empresa"
    return None

def get_dominio_nombre(dominio_id: str) -> Optional[str]:
    """Obtiene el nombre de un dominio"""
    for d in TODOS_DOMINIOS:
        if d["id"] == dominio_id:
            return d["nombre"]
    return None

def verificar_tier(feature_requerido: str) -> bool:
    """
    Verifica si el usuario tiene acceso a una feature según su tier.
    TODO: Implementar verificación real con validador.json
    """
    # Por ahora, permitir todo en desarrollo
    return True

async def llamar_api_externa(texto: str, tipo_consulta: str) -> Dict[str, Any]:
    """
    Llama a la API externa de Mileforum (modo cloud).
    
    TODO: Implementar llamada real cuando la API esté disponible
    """
    # Simulación de respuesta de API externa
    return {
        "heads": {"trigo": 0.72, "cobre": 0.65, "petroleo": 0.81},
        "estados": {
            "campos": 0.68,
            "tension": 0.42,
            "coherencia": 0.79,
            "resiliencia": 0.71,
            "indice_telos": 0.76
        },
        "sugerencia_tcl": f"[Cloud] Análisis de {tipo_consulta}: Se recomienda revisar los documentos principales y validar con criterio profesional."
    }

# ============================================================================
# ENDPOINTS - CONFIGURACIÓN
# ============================================================================

@api_router.get("/")
async def root():
    """Endpoint raíz - información del sistema"""
    config = load_config()
    return {
        "sistema": "Aprendiz Mileforum",
        "version": "1.0.0",
        "filosofia": "Tu operación, tu modelo",
        "configurado": config.get("configurado", False),
        "modo": config.get("modo", "cloud")
    }

@api_router.get("/config", response_model=ConfiguracionResponse)
async def get_configuracion():
    """Obtiene la configuración actual del sistema"""
    config = load_config()
    return ConfiguracionResponse(**config)

@api_router.post("/config/inicializar", response_model=ConfiguracionResponse)
async def inicializar_configuracion(input: ConfiguracionInicial):
    """
    Configura el sistema con un dominio específico.
    IMPORTANTE: El dominio es permanente por diseño arquitectónico.
    """
    tipo_dominio = get_tipo_dominio(input.dominio_id)
    if not tipo_dominio:
        raise HTTPException(status_code=400, detail="Dominio no válido")
    
    dominio_nombre = get_dominio_nombre(input.dominio_id)
    
    config = {
        "modo": input.modo,
        "tipo_dominio": tipo_dominio,
        "dominio_id": input.dominio_id,
        "dominio_nombre": dominio_nombre,
        "configurado": True
    }
    
    save_config(config)
    
    # Inicializar motor según modo y tipo
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
    """Obtiene la lista de todos los dominios disponibles"""
    return {
        "unipersonales": DOMINIOS_UNIPERSONALES,
        "empresas": DOMINIOS_EMPRESAS,
        "total": len(TODOS_DOMINIOS)
    }

# ============================================================================
# ENDPOINTS - EXPEDIENTES
# ============================================================================

@api_router.post("/expedientes", response_model=Expediente)
async def crear_expediente(input: ExpedienteCreate):
    """Crea un nuevo expediente"""
    config = load_config()
    if not config.get("configurado"):
        raise HTTPException(status_code=400, detail="Sistema no configurado. Selecciona un dominio primero.")
    
    expediente = Expediente(
        nombre=input.nombre,
        descripcion=input.descripcion,
        dominio_id=config["dominio_id"]
    )
    
    doc = expediente.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.expedientes.insert_one(doc)
    return expediente

@api_router.get("/expedientes", response_model=List[Expediente])
async def listar_expedientes():
    """Lista todos los expedientes"""
    expedientes = await db.expedientes.find({}, {"_id": 0}).to_list(1000)
    
    for exp in expedientes:
        if isinstance(exp.get('created_at'), str):
            exp['created_at'] = datetime.fromisoformat(exp['created_at'])
        if isinstance(exp.get('updated_at'), str):
            exp['updated_at'] = datetime.fromisoformat(exp['updated_at'])
    
    return expedientes

@api_router.get("/expedientes/{expediente_id}", response_model=Expediente)
async def obtener_expediente(expediente_id: str):
    """Obtiene un expediente por ID"""
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    if isinstance(expediente.get('created_at'), str):
        expediente['created_at'] = datetime.fromisoformat(expediente['created_at'])
    if isinstance(expediente.get('updated_at'), str):
        expediente['updated_at'] = datetime.fromisoformat(expediente['updated_at'])
    
    return Expediente(**expediente)

# ============================================================================
# ENDPOINTS - DOCUMENTOS (Embudo de Ingesta)
# ============================================================================

@api_router.post("/expedientes/{expediente_id}/documentos")
async def subir_documento(
    expediente_id: str,
    file: UploadFile = File(...)
):
    """
    Sube un documento al expediente (Embudo de Ingesta).
    Los documentos se almacenan temporalmente para procesamiento.
    """
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Crear directorio del expediente
    exp_dir = UPLOADS_DIR / expediente_id
    exp_dir.mkdir(exist_ok=True)
    
    # Guardar archivo
    file_path = exp_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Crear metadata
    doc_meta = DocumentoMetadata(
        expediente_id=expediente_id,
        nombre=file.filename,
        tipo=file.content_type or "application/octet-stream",
        size=file_path.stat().st_size
    )
    
    doc = doc_meta.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    
    await db.documentos.insert_one(doc)
    
    return {"status": "uploaded", "documento": doc_meta.model_dump()}

@api_router.get("/expedientes/{expediente_id}/documentos")
async def listar_documentos(expediente_id: str):
    """Lista los documentos de un expediente"""
    documentos = await db.documentos.find(
        {"expediente_id": expediente_id}, 
        {"_id": 0}
    ).to_list(1000)
    
    return {"expediente_id": expediente_id, "documentos": documentos}

# ============================================================================
# ENDPOINTS - PROCESAMIENTO (Doble Hélice / RAG)
# ============================================================================

@api_router.post("/expedientes/{expediente_id}/procesar")
async def procesar_expediente(expediente_id: str, input: ProcesamientoRequest):
    """
    Procesa un expediente con el motor correspondiente.
    
    - UNIPERSONAL: Motor Aprendiz (Doble Hélice) → heads, estados, sugerencia_tcl
    - EMPRESA: Motor RAG → resumen, documentos_procesados
    """
    config = load_config()
    if not config.get("configurado"):
        raise HTTPException(status_code=400, detail="Sistema no configurado")
    
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Obtener documentos del expediente
    documentos = await db.documentos.find(
        {"expediente_id": expediente_id}, 
        {"_id": 0}
    ).to_list(100)
    
    # Leer contenido de documentos
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
    
    # Actualizar estado del expediente
    await db.expedientes.update_one(
        {"id": expediente_id},
        {"$set": {"estado": "procesando", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    tipo_dominio = config.get("tipo_dominio")
    modo = config.get("modo")
    
    if tipo_dominio == "unipersonal":
        # Motor Aprendiz
        if modo == "local":
            from aprendiz_motor import ejecutar_episodio
            resultado = ejecutar_episodio(texto_concatenado, input.tipo_consulta)
            procesado_en = "local"
        else:
            resultado = await llamar_api_externa(texto_concatenado, input.tipo_consulta)
            procesado_en = "cloud"
        
        # Actualizar expediente como completado
        await db.expedientes.update_one(
            {"id": expediente_id},
            {"$set": {"estado": "completado", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Guardar resultado del procesamiento
        resultado_doc = {
            "id": str(uuid.uuid4()),
            "expediente_id": expediente_id,
            "tipo": "unipersonal",
            "resultado": resultado,
            "procesado_en": procesado_en,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.procesamientos.insert_one(resultado_doc)
        
        return ProcesamientoUnipersonalResponse(
            expediente_id=expediente_id,
            heads=HeadsResponse(**resultado["heads"]),
            estados=EstadosResponse(**resultado["estados"]),
            sugerencia_tcl=resultado["sugerencia_tcl"],
            procesado_en=procesado_en
        )
    
    else:
        # Motor RAG (empresas)
        if modo == "local":
            from aprendiz_motor.rag_agents import procesar_expediente as rag_procesar
            docs_para_rag = [{"nombre": d["nombre"], "contenido": t, "tipo": d["tipo"]} 
                           for d, t in zip(documentos, textos)]
            resultado = rag_procesar(expediente_id, docs_para_rag)
        else:
            # Simulación modo cloud para RAG
            resultado = {
                "expediente_id": expediente_id,
                "resumen": f"[Cloud RAG] Procesados {len(documentos)} documentos. Análisis completo disponible.",
                "documentos_procesados": [{"id": d["id"], "nombre": d["nombre"], "status": "procesado"} for d in documentos],
                "total_documentos": len(documentos)
            }
        
        # Actualizar expediente
        await db.expedientes.update_one(
            {"id": expediente_id},
            {"$set": {"estado": "completado", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return ProcesamientoEmpresaResponse(**resultado)

# ============================================================================
# ENDPOINTS - DECISIONES Y SINCRONIZACIONES
# ============================================================================

@api_router.post("/sincronizaciones/{expediente_id}/decision", response_model=Decision)
async def registrar_decision(expediente_id: str, input: DecisionCreate):
    """
    Registra la decisión del usuario sobre una Sugerencia TCL.
    Las decisiones se guardan para reentrenamiento bimestral.
    """
    expediente = await db.expedientes.find_one({"id": expediente_id}, {"_id": 0})
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    decision = Decision(
        expediente_id=expediente_id,
        sugerencia_tcl=input.sugerencia_tcl,
        decision=input.decision,
        correccion=input.correccion
    )
    
    doc = decision.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.decisiones.insert_one(doc)
    return decision

@api_router.get("/decisiones", response_model=List[Decision])
async def listar_decisiones():
    """Lista todas las decisiones registradas"""
    decisiones = await db.decisiones.find({}, {"_id": 0}).to_list(1000)
    
    for d in decisiones:
        if isinstance(d.get('created_at'), str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
    
    return decisiones

@api_router.post("/sincronizaciones", response_model=Sincronizacion)
async def crear_sincronizacion(input: SincronizacionCreate):
    """Registra un evento de sincronización"""
    sync = Sincronizacion(tipo=input.tipo)
    
    doc = sync.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.sincronizaciones.insert_one(doc)
    return sync

# ============================================================================
# ENDPOINTS - LANDING PAGE (Registros y Analytics)
# ============================================================================

@api_router.post("/register", response_model=RegistroLanding)
async def registrar_usuario_landing(input: RegistroLandingCreate):
    """Registro de usuarios desde la landing page"""
    valid_domains = [d["id"] for d in TODOS_DOMINIOS]
    if input.domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Dominio inválido")
    
    existing = await db.registros_landing.find_one({"email": input.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    registro = RegistroLanding(
        name=input.name,
        email=input.email,
        domain=input.domain
    )
    
    doc = registro.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.registros_landing.insert_one(doc)
    return registro

@api_router.get("/registrations", response_model=List[RegistroLanding])
async def listar_registros_landing():
    """Lista registros de la landing page"""
    registros = await db.registros_landing.find({}, {"_id": 0}).to_list(1000)
    
    for r in registros:
        if isinstance(r.get('created_at'), str):
            r['created_at'] = datetime.fromisoformat(r['created_at'])
    
    return registros

@api_router.post("/analytics/track")
async def track_event(event: AnalyticsEvent):
    """Registra un evento de analytics"""
    event_stored = AnalyticsEventStored(
        event_type=event.event_type,
        event_data=event.event_data
    )
    
    doc = event_stored.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.analytics_events.insert_one(doc)
    return {"status": "tracked", "event_id": event_stored.id}

@api_router.get("/analytics/summary")
async def get_analytics_summary():
    """Obtiene resumen de analytics"""
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    
    results = await db.analytics_events.aggregate(pipeline).to_list(100)
    summary = {item["_id"]: item["count"] for item in results}
    return {"summary": summary}

# ============================================================================
# ENDPOINTS - ESTADO DEL MOTOR
# ============================================================================

@api_router.get("/motor/estado")
async def estado_motor():
    """Obtiene el estado del motor de IA"""
    config = load_config()
    
    estado = {
        "configurado": config.get("configurado", False),
        "modo": config.get("modo"),
        "tipo_dominio": config.get("tipo_dominio"),
        "dominio_id": config.get("dominio_id"),
        "motor_local_disponible": False
    }
    
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

# ============================================================================
# CONFIGURACIÓN FINAL
# ============================================================================

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
