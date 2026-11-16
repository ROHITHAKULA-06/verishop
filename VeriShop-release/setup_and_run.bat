@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "BACKEND=%ROOT%verishop-backend"
set "FRONTEND=%ROOT%verishop-frontend"
set "VENV=%BACKEND%\.venv"

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3.10 or newer was not found. Install Python and enable the PATH option.
    pause
    exit /b 1
  )
  set "PY=python"
)

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 18 or newer was not found. Install Node.js, then run this file again.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo npm was not found. Reinstall Node.js with npm enabled, then run this file again.
  pause
  exit /b 1
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo Python 3.10 or newer is required. Install Python 3.11 for the smoothest setup.
  pause
  exit /b 1
)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)"
if errorlevel 1 (
  echo Node.js 18 or newer is required.
  pause
  exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
  echo Creating backend virtual environment...
  %PY% -m venv "%VENV%"
  if errorlevel 1 goto :failed
)

echo Installing backend dependencies. This can take several minutes on first run...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%VENV%\Scripts\python.exe" -m pip install -r "%BACKEND%\requirements.txt"
if errorlevel 1 goto :failed

if not exist "%BACKEND%\.env" (
  copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
  if errorlevel 1 goto :failed
  echo Created backend .env from .env.example.
)

if not exist "%FRONTEND%\node_modules\vite\bin\vite.js" (
  echo Installing frontend dependencies. This can take a few minutes...
  pushd "%FRONTEND%"
  call npm ci
  if errorlevel 1 (popd & goto :failed)
  popd
)

 echo Starting VeriShop API and frontend in separate windows...
start "VeriShop Backend - API" cmd /k "cd /d ""%BACKEND%"" && set DEBUG=false && ""%VENV%\Scripts\python.exe"" run.py"
start "VeriShop Frontend - Vite" cmd /k "cd /d ""%FRONTEND%"" && npm run dev -- --host 127.0.0.1"

echo Waiting for both servers to become ready...
set /a ATTEMPTS=0
:wait_for_servers
set /a ATTEMPTS+=1
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health -TimeoutSec 2 | Out-Null; Invoke-WebRequest -UseBasicParsing http://localhost:5173 -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 goto :servers_ready
if %ATTEMPTS% GEQ 90 goto :servers_timeout
timeout /t 1 /nobreak >nul
goto :wait_for_servers

:servers_ready
start "" "http://localhost:5173"
echo VeriShop is opening at http://localhost:5173
echo Keep both VeriShop terminal windows open while using the app.
pause
exit /b 0

:servers_timeout
echo Setup finished, but a server did not become ready within 90 seconds. Check the two server windows for errors.
start "" "http://localhost:5173"
pause
exit /b 1

:failed
echo Setup failed. Read the error above, check your internet connection and Python/Node versions, then run this file again.
pause
exit /b 1
