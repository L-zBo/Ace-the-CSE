@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo  Ace-the-CSE  ^|  Next.js dev server ^(Webpack fallback^)
echo ============================================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [!] Node.js not found in PATH. Install from https://nodejs.org/ first.
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo [*] node_modules not found, running install...
  call npm install
  if errorlevel 1 (
    echo [!] npm install failed.
    pause
    exit /b 1
  )
)

echo [*] Starting dev server at http://localhost:3000
echo [*] Using Webpack because Turbopack currently panics on this project.
echo [*] Press Ctrl+C to stop.
echo.

call npm run dev
endlocal
