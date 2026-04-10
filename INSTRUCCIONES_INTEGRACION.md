# INSTRUCCIONES DE INTEGRACIÓN — Mileforum F-02

Este archivo documenta cómo se integraron los archivos desarrollados en F-02 al repositorio domprimitivo/app-embudo.

---

## Archivos que REEMPLAZAN stubs existentes

Estos archivos ya existían en el repositorio pero devolvían valores inventados. Se reemplazaron con implementaciones reales.

### 1. Backend/aprendiz_motor/notebook_engine.py
- Acción: REEMPLAZAR el archivo existente
- Qué hace: Carga el bundle .zip real, ejecuta el modelo GRU, infiere la fase y activa las cabezas especializadas
- Commit: F-02: reemplazar notebook_engine stub con motor real

### 2. Backend/aprendiz_motor/__init__.py
- Acción: REEMPLAZAR el archivo existente
- Qué hace: Exporta inicializar_motor, ejecutar_episodio y obtener_estado_motor
- Commit: F-02: reemplazar __init__ aprendiz_motor con exportaciones reales

### 3. Backend/aprendiz_motor/rag_agents/processor.py
- Acción: REEMPLAZAR el archivo existente
- Qué hace: Pipeline de 9 agentes, lee cucurucho JSON, calcula Doble Hélice, genera narrativa TCL
- Commit: F-02: reemplazar processor.py RAG con pipeline real

### 4. Backend/aprendiz_motor/rag_agents/__init__.py
- Acción: REEMPLAZAR el archivo existente
- Qué hace: Exporta inicializar_rag y procesar_expediente
- Commit: F-02: reemplazar __init__ rag_agents con exportaciones reales

---

## Archivos NUEVOS que no existían en el repositorio

Estos archivos se crearon desde cero y se agregaron en las rutas indicadas.

### 5. Backend/aprendiz_motor/bundle_loader.py
- Acción: CREAR en Backend/aprendiz_motor/
- Qué hace: Abre los bundles .zip, carga PyTorch, normaliza features, ejecuta inferencia real
- Commit: F-02: agregar bundle_loader.py nuevo

### 6. Backend/App/db/sqlite_db.py
- Acción: CREAR carpeta db/ dentro de App/ y colocar el archivo
- Qué hace: Base de datos local SQLite con 4 tablas: expedientes, documentos, sincronizaciones, decisiones
- Commit: F-02: agregar sqlite_db.py nuevo

### 7. Backend/App/modo_dual.py
- Acción: CREAR en Backend/App/
- Qué hace: Gestor de modo dual — enruta entre API cloud y motor local con fallback automático
- Commit: F-02: agregar modo_dual.py nuevo

### 8. Backend/App/config_arranque.json
- Acción: CREAR en Backend/App/
- Qué hace: Configuración del modo del sistema. Cambiar "modo": "local" o "modo": "api"
- Commit: F-02: agregar config_arranque.json nuevo

---

## Documentación

### 9. Mileforum_Documentacion_Tecnica_v2.docx
- Acción: SUBIR a la raíz del repositorio
- Qué es: Documentación técnica completa del sistema actualizada a F-02
- Commit: F-01: documentación técnica completa v2.0

---

## Verificación final

Con todos los archivos subidos, verificar:
1. GET /api/motor/estado → bundle_cargado: true
2. POST /api/config/inicializar → configurado: true
3. GET /docs → Swagger disponible
