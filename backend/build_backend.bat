@echo off
REM ===================================================================
REM  build_backend.bat  -  Compila el backend FastAPI a un .exe local
REM  (PyInstaller --onefile). App 100%% LOCAL / OFFLINE.
REM
REM  Estrategia de rutas (coherente con _resolver_root_dir() en server.py):
REM    - El .exe persiste y lee sus datos JUNTO al ejecutable (sys.frozen).
REM    - Por eso los ASSETS de solo-lectura NO se incrustan con --add-data:
REM      se COPIAN al lado del .exe dentro de dist\ al final del build.
REM    - La BD (mileforum.db) y uploads/ se crean junto al .exe en runtime.
REM
REM  Requisitos: python + pip install pyinstaller y requirements.txt.
REM  Ejecutar desde la carpeta backend\ en Windows.
REM ===================================================================

echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist aprendiz_backend.spec del aprendiz_backend.spec

echo Compilando Backend con PyInstaller (aprendiz_backend.exe)...
pyinstaller --onefile ^
  --name aprendiz_backend ^
  --collect-all torch ^
  --collect-all uvicorn ^
  --collect-all pdfplumber ^
  --collect-all openpyxl ^
  --collect-all docx ^
  --collect-all nbclient ^
  --collect-all nbformat ^
  --collect-all ipykernel ^
  --collect-all papermill ^
  --hidden-import=aprendiz_motor ^
  --hidden-import=aprendiz_motor.rag_agents ^
  --hidden-import=lazo_generico ^
  --hidden-import=flujo_kpis ^
  --hidden-import=asistente_aprendiz ^
  --hidden-import=aprendiz_inferencia ^
  --hidden-import=ajuste_bimestral ^
  --hidden-import=compresion_geometrica ^
  --hidden-import=local_storage ^
  server.py

if not exist dist\aprendiz_backend.exe (
  echo.
  echo *** ERROR: la compilacion fallo. Revisa el log de PyInstaller. ***
  pause
  exit /b 1
)

echo.
echo Copiando assets de solo-lectura junto al ejecutable (dist\)...
REM Catalogos del flujo empresarial (clientes, dominios, cucurucho, params, memoria)
if exist flujo             xcopy /e /i /y flujo             dist\flujo
REM Bundles (modelos .zip / .pt de dominios) y datos del aprendiz
if exist bundles           xcopy /e /i /y bundles           dist\bundles
if exist aprendiz_data     xcopy /e /i /y aprendiz_data     dist\aprendiz_data
REM Modelos del motor unipersonal (notebook_engine busca .\modelos junto al exe)
if exist modelos           xcopy /e /i /y modelos           dist\modelos
REM Configuracion inicial del dominio y activador
if exist config.json               copy /y config.json               dist\config.json
if exist mileforum_activador.json  copy /y mileforum_activador.json  dist\mileforum_activador.json

echo.
echo Compilacion finalizada.
echo   Ejecutable:  dist\aprendiz_backend.exe
echo   Assets:      dist\flujo, dist\bundles, dist\aprendiz_data, dist\modelos
echo   (mileforum.db y uploads\ se crean junto al .exe en el primer arranque)
pause
