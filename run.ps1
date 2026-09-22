param([ValidateRange(1,65535)][int]$Port = 8840)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$stamp = Join-Path $PSScriptRoot '.venv\lantern-dependencies.sha256'
if (-not (Test-Path $python)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
}
$expected = (Get-FileHash (Join-Path $PSScriptRoot 'pyproject.toml') -Algorithm SHA256).Hash
$installed = if (Test-Path $stamp) { (Get-Content $stamp -Raw).Trim() } else { '' }
if ($installed -ne $expected) {
    & $python -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Run this script again to retry.' }
    Set-Content $stamp $expected
}
Write-Host "Lantern Hollow: http://127.0.0.1:$Port"
& $python -m lantern_hollow.server --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Lantern Hollow stopped with an error.' }
