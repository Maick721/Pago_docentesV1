@echo off
setlocal
pushd "%~dp0frontend"
if not exist "node_modules" (
  echo No existen las dependencias de Angular. Ejecuta primero scripts\setup.ps1 desde la raiz del repositorio.
  popd
  exit /b 1
)
call npm.cmd start -- %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
