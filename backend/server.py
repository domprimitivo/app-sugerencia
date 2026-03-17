from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Available domains
VALID_DOMAINS = [
    "abogado", "arquitecto", "contador", "consultor_pyme",
    "diseno_producto", "operaciones", "clinica", "hotel",
    "restaurante", "retail", "fabrica", "logistica"
]

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Registration Models
class RegistrationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    domain: str
    
class Registration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    domain: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Analytics Models
class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[dict] = None

class AnalyticsEventStored(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Routes
@api_router.get("/")
async def root():
    return {"message": "Mileforum API - Tu operación, tu modelo"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Registration endpoints
@api_router.post("/register", response_model=Registration)
async def register_user(input: RegistrationCreate):
    # Validate domain
    if input.domain not in VALID_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Dominio inválido. Opciones: {', '.join(VALID_DOMAINS)}")
    
    # Check if email already exists
    existing = await db.registrations.find_one({"email": input.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    registration = Registration(
        name=input.name,
        email=input.email,
        domain=input.domain
    )
    
    doc = registration.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.registrations.insert_one(doc)
    return registration

@api_router.get("/registrations", response_model=List[Registration])
async def get_registrations():
    registrations = await db.registrations.find({}, {"_id": 0}).to_list(1000)
    
    for reg in registrations:
        if isinstance(reg['created_at'], str):
            reg['created_at'] = datetime.fromisoformat(reg['created_at'])
    
    return registrations

@api_router.get("/domains")
async def get_domains():
    return {
        "domains": [
            {"id": "abogado", "name": "Abogado", "icon": "Scale", "category": "profesional"},
            {"id": "arquitecto", "name": "Arquitecto", "icon": "Ruler", "category": "profesional"},
            {"id": "contador", "name": "Contador", "icon": "Calculator", "category": "profesional"},
            {"id": "consultor_pyme", "name": "Consultor PyME", "icon": "Briefcase", "category": "profesional"},
            {"id": "diseno_producto", "name": "Diseño Producto", "icon": "PenTool", "category": "profesional"},
            {"id": "operaciones", "name": "Operaciones", "icon": "Settings", "category": "profesional"},
            {"id": "clinica", "name": "Clínica", "icon": "Stethoscope", "category": "empresa"},
            {"id": "hotel", "name": "Hotel", "icon": "Bed", "category": "empresa"},
            {"id": "restaurante", "name": "Restaurante", "icon": "Utensils", "category": "empresa"},
            {"id": "retail", "name": "Retail", "icon": "ShoppingBag", "category": "empresa"},
            {"id": "fabrica", "name": "Fábrica", "icon": "Factory", "category": "empresa"},
            {"id": "logistica", "name": "Logística", "icon": "Truck", "category": "empresa"}
        ]
    }

# Analytics endpoints
@api_router.post("/analytics/track")
async def track_event(event: AnalyticsEvent):
    event_stored = AnalyticsEventStored(
        event_type=event.event_type,
        event_data=event.event_data
    )
    
    doc = event_stored.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.analytics_events.insert_one(doc)
    return {"status": "tracked", "event_id": event_stored.id}

@api_router.get("/analytics/events", response_model=List[AnalyticsEventStored])
async def get_analytics_events():
    events = await db.analytics_events.find({}, {"_id": 0}).to_list(1000)
    
    for event in events:
        if isinstance(event['timestamp'], str):
            event['timestamp'] = datetime.fromisoformat(event['timestamp'])
    
    return events

@api_router.get("/analytics/summary")
async def get_analytics_summary():
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    
    results = await db.analytics_events.aggregate(pipeline).to_list(100)
    
    summary = {item["_id"]: item["count"] for item in results}
    return {"summary": summary}

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
