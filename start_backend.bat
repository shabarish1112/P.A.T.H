@echo off
setlocal
cd /d "%~dp0backend"
if not exist .venv\Scripts\python.exe (
  echo Backend virtual environment is missing. Run: py -3.14 -m venv .venv
  exit /b 1
)
if not exist .env (
  echo ERROR: backend\.env is missing. Copy .env.example manually, replace every example value, and retry.
  exit /b 1
)
.venv\Scripts\python.exe -c "import fastapi, uvicorn, pymongo" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Backend dependencies are missing. From the backend folder run:
  echo .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
