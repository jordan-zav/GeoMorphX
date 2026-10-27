# Run from the repository through DEVRESOURCES_RUN.cmd powershell -File scripts\validate_package.ps1
$ErrorActionPreference = 'Stop'
if (-not $env:DEVRESOURCES_SESSION) { throw 'Ejecute este script mediante DEVRESOURCES_RUN.cmd.' }
$repoPath = Split-Path -Parent $PSScriptRoot
$wheelDir = Join-Path $env:DEVRESOURCES_SESSION 'wheels'
$targetDir = Join-Path $env:DEVRESOURCES_ROOT 'Builds\GeoMorphX\cargo'
python -m maturin build --release --out $wheelDir --target-dir $targetDir -j 2
if ($LASTEXITCODE -ne 0) { throw 'Fallo la compilacion del paquete.' }
$wheels = @(Get-ChildItem -LiteralPath $wheelDir -Filter '*.whl')
if ($wheels.Count -ne 1) { throw 'Se esperaba exactamente un wheel.' }
$venvPath = Join-Path $env:DEVRESOURCES_SESSION 'validation-env'
python -m venv --system-site-packages $venvPath
if ($LASTEXITCODE -ne 0) { throw 'Fallo la creacion del entorno aislado.' }
$validationPython = Join-Path $venvPath 'Scripts\python.exe'
& $validationPython -m pip install --no-deps $wheels[0].FullName
if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion del wheel.' }
Push-Location $env:DEVRESOURCES_SESSION
try {
    & $validationPython -c 'import geomorphx; from geomorphx import geomorphx_core_rs; print(geomorphx.__file__)'
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la importacion del paquete instalado o de Rust.' }
    & $validationPython -m pytest (Join-Path $repoPath 'tests') --import-mode=importlib -q
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas del paquete instalado.' }
    & (Join-Path $venvPath 'Scripts\geomorphx.exe') --help
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el comando instalado.' }
} finally {
    Pop-Location
}
