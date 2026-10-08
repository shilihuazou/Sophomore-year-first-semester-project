@echo off
setlocal
title CangQiongPj - Start All Services

set "PROJECT_ROOT=%~dp0"
echo Starting all services. Please wait...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%app\start-services.ps1"
if errorlevel 1 (
    echo.
    echo Startup failed. Review the error message above.
    pause
    exit /b 1
)

echo.
echo All services are ready:
echo   Admin local    http://127.0.0.1:5173/#/login
echo   Team local     http://127.0.0.1:5174/
echo   LAN/public addresses were printed above when configured.
echo   Backend and KQGIS stay local and are reached through the frontend proxies.
echo.

start "" "http://127.0.0.1:5173/#/login"
start "" "http://127.0.0.1:5174/"

echo Browser pages opened. Services will keep running after this window closes.
endlocal
exit /b 0
