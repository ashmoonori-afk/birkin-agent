param(
  [switch]$SkipCheck
)

$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$BirkinExe = Join-Path $VenvDir "Scripts\birkin-codex.exe"

if (-not (Test-Path $PythonExe)) {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    & py -3.11 -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
      & py -m venv $VenvDir
    }
  } else {
    & python -m venv $VenvDir
  }
}

& $PythonExe -m pip install -e $RootDir
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

if (-not $SkipCheck) {
  & $BirkinExe setup
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

Write-Host ""
Write-Host "Birkin Codex is installed in .venv."
Write-Host "For this terminal, run:"
Write-Host "  . .\.venv\Scripts\Activate.ps1"
Write-Host "Then start the Hermes-style chat CLI with:"
Write-Host "  birkin-codex"
