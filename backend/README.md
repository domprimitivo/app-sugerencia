# Aprendiz Mileforum - Backend

## Arquitectura del Sistema

**Portal Episódico**: Interfaz entre profesionales/empresas y modelos de IA especializados.

**Filosofía**: "Caja con agujeros" - Ligera en interfaz, capaz de manejar datos densos.

**Modo de Operación**: DUAL (Cloud + Local)

### Motores

| Motor | Tipo | Descripción |
|-------|------|-------------|
| **Aprendiz** | Unipersonal | Modelo multicefalar con aprendizaje micro-operacional |
| **RAG** | Empresa | Agentes de procesamiento documental |

---

## Estructura de Carpetas

```
/backend/
├── server.py              # FastAPI principal
├── config.json            # Configuración dual (modo, dominio)
├── requirements.txt       # Dependencias Python
├── .env                   # Variables de entorno
├── uploads/               # Documentos subidos temporalmente
├── README.md              # Este archivo
│
└── aprendiz_motor/        # [MÓDULO DE IA]
    ├── __init__.py
    ├── notebook_engine.py # Interfaz del modelo Aprendiz
    ├── modelos/           # Modelos .pth (6 unipersonales)
    │   ├── abogado.pth
    │   ├── arquitecto.pth
    │   ├── contador.pth
    │   ├── consultor_pyme.pth
    │   ├── diseno_producto.pth
    │   └── operaciones.pth
    │
    └── rag_agents/        # Agentes RAG para empresas
        ├── __init__.py
        └── processor.py
```

---

## Dominios Disponibles (12)

### Unipersonales (6)
| ID | Nombre | Motor |
|----|--------|-------|
| `abogado` | Abogado | Aprendiz |
| `arquitecto` | Arquitecto | Aprendiz |
| `contador` | Contador | Aprendiz |
| `consultor_pyme` | Consultor PyME | Aprendiz |
| `diseno_producto` | Diseño Producto | Aprendiz |
| `operaciones` | Operaciones | Aprendiz |

### Empresas (6)
| ID | Nombre | Motor |
|----|--------|-------|
| `clinica` | Clínica | RAG |
| `hotel` | Hotel | RAG |
| `restaurante` | Restaurante | RAG |
| `retail` | Retail | RAG |
| `fabrica` | Fábrica | RAG |
| `logistica` | Logística | RAG |

---

## API Endpoints

### Configuración
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/` | Info del sistema |
| GET | `/api/config` | Obtener configuración actual |
| POST | `/api/config/inicializar` | Configurar dominio (permanente) |
| GET | `/api/dominios` | Lista de dominios disponibles |

### Expedientes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/expedientes` | Crear expediente |
| GET | `/api/expedientes` | Listar expedientes |
| GET | `/api/expedientes/{id}` | Obtener expediente |
| POST | `/api/expedientes/{id}/documentos` | Subir documento (embudo) |
| GET | `/api/expedientes/{id}/documentos` | Listar documentos |
| POST | `/api/expedientes/{id}/procesar` | Procesar con motor IA |

### Decisiones y Sincronizaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/sincronizaciones/{id}/decision` | Registrar decisión TCL |
| GET | `/api/decisiones` | Listar decisiones |
| POST | `/api/sincronizaciones` | Crear evento de sync |

### Motor
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/motor/estado` | Estado del motor IA |

### Landing Page
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/register` | Registro de usuarios |
| GET | `/api/registrations` | Listar registros |
| POST | `/api/analytics/track` | Tracking de eventos |
| GET | `/api/analytics/summary` | Resumen analytics |

---

## Respuesta del Procesamiento

### Unipersonal (Motor Aprendiz)

```json
{
  "expediente_id": "uuid",
  "heads": {
    "trigo": 0.75,
    "cobre": 0.62,
    "petroleo": 0.88
  },
  "estados": {
    "campos": 0.71,
    "tension": 0.45,
    "coherencia": 0.83,
    "resiliencia": 0.67,
    "indice_telos": 0.79
  },
  "sugerencia_tcl": "Texto con recomendación...",
  "procesado_en": "local" | "cloud"
}
```

### Empresa (Motor RAG)

```json
{
  "expediente_id": "uuid",
  "resumen": "Texto con resumen del análisis...",
  "documentos_procesados": [
    {"id": "doc_1", "nombre": "archivo.pdf", "status": "procesado"}
  ],
  "total_documentos": 3
}
```

---

## Configuración (config.json)

```json
{
  "modo": "cloud" | "local",
  "tipo_dominio": "unipersonal" | "empresa" | null,
  "dominio_id": "abogado" | null,
  "dominio_nombre": "Abogado" | null,
  "configurado": true | false
}
```

**IMPORTANTE**: El dominio es permanente por diseño arquitectónico.

---

## Variables de Entorno (.env)

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="mileforum_db"
CORS_ORIGINS="*"
```

---

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

---

## Integración del Motor (Para Desarrolladores)

### Motor Aprendiz (notebook_engine.py)

La clase `AprendizMileforum` debe:

1. Cargar modelo `.pth` del dominio
2. Implementar `ejecutar_episodio(documentos_texto, tipo_consulta)`
3. Retornar: `heads`, `estados`, `sugerencia_tcl`

```python
from aprendiz_motor import inicializar_motor, ejecutar_episodio

# Inicializar
inicializar_motor({"dominio_id": "abogado"})

# Ejecutar
resultado = ejecutar_episodio("texto...", "analisis")
```

### Motor RAG (rag_agents/processor.py)

La clase `RAGProcessor` debe:

1. Indexar documentos por dominio empresarial
2. Implementar `procesar_expediente(id, documentos)`
3. Retornar: `resumen`, `documentos_procesados`

---

## Glosario

| Término | Descripción |
|---------|-------------|
| **Portal Episódico** | Interfaz que registra "episodios" (expedientes) |
| **Embudo de Ingesta** | Zona de drag & drop para documentos |
| **Doble Hélice** | Visualización de estados (predicción + realidad) |
| **Heads** | Componentes del modelo: trigo, cobre, petroleo |
| **Estados** | campos, tension, coherencia, resiliencia, indice_telos |
| **Sugerencia TCL** | "Thought-Chain Logic" - Output textual del modelo |
| **Sesión Itinerante** | Reentrenamiento temporal sin persistencia |

---

## Prioridades de Desarrollo

1. **CRÍTICO**: Integrar modelo real (.pth), llamada a API externa
2. **IMPORTANTE**: Empaquetado Tauri, Python embebido
3. **MEDIO**: Portal cliente, suscripciones
4. **BAJO**: Optimizaciones, caché, logs avanzados

---

## Contacto

Para dudas sobre la lógica de negocio y términos no convencionales,
consultar la documentación filosófica del proyecto.
