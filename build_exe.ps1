# Builds the Windows desktop program, output\release\OoT-Remake-Rando.exe, plus a zip with the tester guide.
# Everything it installs goes into .\build (its own Python environment); nothing is installed system-wide.
# Run:  powershell -ExecutionPolicy Bypass -File build_exe.ps1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (Get-Command py -ErrorAction SilentlyContinue) { $pyExe = 'py'; $pyArgs = @('-3') }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $pyExe = 'python'; $pyArgs = @() }
else { throw 'Python 3 is not installed: https://www.python.org/downloads/' }
Write-Host "Using $(& $pyExe @pyArgs --version)"

$venv = Join-Path $PSScriptRoot 'build\venv'
$vpy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $vpy)) {
    Write-Host 'Creating the build environment in .\build\venv ...'
    & $pyExe @pyArgs -m venv $venv
    if ($LASTEXITCODE) { throw 'Could not create the Python environment' }
}
Write-Host 'Installing pywebview, PyInstaller and zstandard into the build environment ...'
& $vpy -m pip install --disable-pip-version-check --upgrade pip pywebview pyinstaller zstandard
if ($LASTEXITCODE) { throw 'pip install failed' }

$version = (& $vpy -c "from lib.build import VERSION; print(VERSION)").Trim()
# the logic worlds are loaded by name at run time, so list them for PyInstaller
$worlds = Get-ChildItem (Join-Path $PSScriptRoot 'logic\*.py') | Where-Object Name -ne '__init__.py' | ForEach-Object { '--hidden-import'; "logic.$($_.BaseName)" }
Write-Host "Building OoT-Remake-Rando.exe (version $version) ..."
& $vpy -m PyInstaller --noconfirm --clean --onefile --windowed --name OoT-Remake-Rando `
    --paths "$PSScriptRoot" --add-data "$PSScriptRoot\web;web" --collect-submodules logic --hidden-import zstandard @worlds `
    --distpath "$PSScriptRoot\output\release" --workpath "$PSScriptRoot\build\pyinstaller" --specpath "$PSScriptRoot\build" `
    "$PSScriptRoot\app.py"
if ($LASTEXITCODE) { throw 'PyInstaller failed' }

$exe = Join-Path $PSScriptRoot 'output\release\OoT-Remake-Rando.exe'
$zip = Join-Path $PSScriptRoot "output\release\OoT-Remake-Rando-$version-windows.zip"
Compress-Archive -Force -Path $exe, (Join-Path $PSScriptRoot 'README_TESTERS.md') -DestinationPath $zip
Write-Host ''
Write-Host "Done: $exe"
Write-Host "Zip for testers: $zip"
