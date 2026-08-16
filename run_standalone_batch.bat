@echo off
setlocal

REM GeoMorphX standalone batch launcher
REM Usage examples:
REM   run_standalone_batch.bat compute-batch --dem-dir data\dems --out-dir outputs --recursive --method rrim_plus --save-debug
REM   run_standalone_batch.bat benchmark-batch --dem-dir data\dems --out-dir benchmarks\batch --recursive

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

set "PY_EXE="
if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
    set "PY_EXE=%SCRIPT_DIR%\.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY_EXE=python"
    ) else (
        where py >nul 2>nul
        if %errorlevel%==0 (
            set "PY_EXE=py -3.11"
        ) else (
            echo [GeoMorphX] No se encontro Python en PATH.
            set "EXIT_CODE=1"
            popd
            exit /b %EXIT_CODE%
        )
    )
)

%PY_EXE% -c "import numpy" >nul 2>nul
if not %errorlevel%==0 (
    echo [GeoMorphX] Faltan dependencias de Python ^(numpy y otras^).
    echo Ejecuta:
    echo   python -m pip install -e .[raster]
    set "EXIT_CODE=1"
) else (
    %PY_EXE% -m standalone_app %*
    set "EXIT_CODE=%errorlevel%"
)

popd
exit /b %EXIT_CODE%
