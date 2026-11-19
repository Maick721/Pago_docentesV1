@echo off
setlocal
pushd "%~dp0backend"
if not exist "..\.venv\Scripts\python.exe" (
  echo No existe el entorno Python. Ejecuta primero scripts\setup.ps1 desde la raiz del repositorio.
  popd
  exit /b 1
)
..\.venv\Scripts\python.exe -m pytest tests\pagos_docentes -q %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
