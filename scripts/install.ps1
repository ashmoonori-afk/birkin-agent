# Birkin Codex one-line installer for Windows PowerShell.
#
#   irm https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.ps1 | iex
#
# Installs the `birkin-codex` command with uv, pipx, or pip --user.
$ErrorActionPreference = "Stop"

$Repo = if ($env:BIRKIN_REPO) { $env:BIRKIN_REPO } else { "https://github.com/ashmoonori-afk/birkin-agent" }
$Ref = if ($env:BIRKIN_REF) { $env:BIRKIN_REF } else { "main" }
$Spec = "git+$Repo@$Ref"

Write-Host "==> Installing birkin-codex from $Spec"

function Have($Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (Have "uv") {
  Write-Host "    using uv"
  uv tool install --force $Spec
} elseif (Have "pipx") {
  Write-Host "    using pipx"
  pipx install --force $Spec
} elseif (Have "python") {
  Write-Host "    using pip --user"
  python -m pip install --user --upgrade $Spec
} elseif (Have "py") {
  Write-Host "    using pip --user"
  py -3.11 -m pip install --user --upgrade $Spec
  if ($LASTEXITCODE -ne 0) {
    py -m pip install --user --upgrade $Spec
  }
} else {
  Write-Error "Need one of: uv, pipx, python, or py. Install Python 3.11+ first."
  exit 1
}

Write-Host ""
Write-Host "==> Done. Start here:"
Write-Host "    birkin-codex setup wizard"
Write-Host "    birkin-codex"
Write-Host "    birkin-codex web --port 8765"
if (-not (Have "birkin-codex")) {
  Write-Host ""
  Write-Host "Note: if birkin-codex is not found, add your Python/uv/pipx Scripts directory to PATH."
}
