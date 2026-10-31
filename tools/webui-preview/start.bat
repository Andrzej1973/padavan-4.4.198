@echo off
setlocal
pushd "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 server.py
) else (
  python server.py
)
if errorlevel 1 (
  popd
  pause
  exit /b 1
)
popd
