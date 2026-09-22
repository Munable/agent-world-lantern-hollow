$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
}
# Retry installation after an interrupted setup; an existing venv is not proof of success.
& $python -c "from importlib.metadata import distributions; import sys; v={d.metadata['Name'].lower():d.version for d in distributions()}; sys.exit(v.get('agent-world-lantern-hollow') != '0.1.0' or v.get('agent-world') != '0.12.0')" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Run this script again to retry.' }
}
Write-Host 'Lantern Hollow: http://127.0.0.1:8840'
& $python -m lantern_hollow.server
if ($LASTEXITCODE -ne 0) { throw 'The local server stopped with an error.' }
