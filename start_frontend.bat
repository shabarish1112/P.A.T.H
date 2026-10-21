@echo off
setlocal
cd /d "%~dp0frontend"
if not exist node_modules (
  echo node_modules is missing. Run npm ci first.
  exit /b 1
)
npm run dev
