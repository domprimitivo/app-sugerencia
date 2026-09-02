"""
Persistencia local soberana.

Centraliza la escritura de archivos en el disco local de la instalacion
(junto al ejecutable / carpeta del backend). 100% local: sin nube, sin
servicios de terceros. Todos los datos del cliente permanecen en su maquina.
"""

import shutil
from pathlib import Path


def guardar_bytes(ruta, datos: bytes) -> Path:
    """Escribe bytes en una ruta local y la devuelve."""
    ruta = Path(ruta)
    with open(ruta, "wb") as f:
        f.write(datos)
    return ruta


def guardar_stream(ruta, stream) -> Path:
    """Copia un stream de lectura a una ruta local y la devuelve."""
    ruta = Path(ruta)
    with open(ruta, "wb") as f:
        shutil.copyfileobj(stream, f)
    return ruta
