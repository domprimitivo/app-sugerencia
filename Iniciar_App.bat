@echo off
title Lanzador Aprendiz Engine
REM ===================================================================
REM  Iniciar_App.bat  -  Orquesta el arranque y cierre de la app LOCAL.
REM
REM  Layout esperado del paquete distribuible:
REM    Iniciar_App.bat            (este archivo, en la raiz)
REM    backend\dist\aprendiz_backend.exe   (+ flujo\, bundles\, aprendiz_data\, config.json)
REM    app\flutter_app.exe        (interfaz Flutter = visualizacion de toda la app)
REM
REM  1) Levanta el backend (FastAPI/Uvicorn en 127.0.0.1:8001) minimizado.
REM  2) Espera a que el backend responda.
REM  3) Abre la interfaz Flutter y espera a que el usuario la cierre.
REM  4) Al cerrar Flutter, apaga el backend.
REM ===================================================================

echo Iniciando servicios del backend...
start /min "" "%~dp0backend\dist\aprendiz_backend.exe"

echo Esperando a que el backend levante...
timeout /t 3 /nobreak > nul

echo Iniciando interfaz...
start /wait "" "%~dp0app\flutter_app.exe"

echo Cerrando backend...
taskkill /IM aprendiz_backend.exe /F > nul 2>&1
exit
