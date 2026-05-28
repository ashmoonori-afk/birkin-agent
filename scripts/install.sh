#!/usr/bin/env sh
# Birkin Codex one-line installer for macOS, Linux, and WSL.
#
#   curl -fsSL https://raw.githubusercontent.com/ashmoonori-afk/birkin-agent/main/scripts/install.sh | sh
#
# Installs the `birkin-codex` command with uv, pipx, or pip --user.
set -eu

REPO="${BIRKIN_REPO:-https://github.com/ashmoonori-afk/birkin-agent}"
REF="${BIRKIN_REF:-main}"
SPEC="git+${REPO}@${REF}"

printf '==> Installing birkin-codex from %s\n' "$SPEC"

if command -v uv >/dev/null 2>&1; then
  printf '    using uv\n'
  uv tool install --force "$SPEC"
elif command -v pipx >/dev/null 2>&1; then
  printf '    using pipx\n'
  pipx install --force "$SPEC"
elif command -v python3 >/dev/null 2>&1; then
  printf '    using pip --user\n'
  python3 -m pip install --user --upgrade "$SPEC"
else
  printf '!! Need one of: uv, pipx, or python3. Install Python 3.11+ first.\n' >&2
  exit 1
fi

printf '\n==> Done. Start here:\n'
printf '    birkin-codex setup wizard\n'
printf '    birkin-codex\n'
printf '    birkin-codex web --port 8765\n'
printf '\n'
if ! command -v birkin-codex >/dev/null 2>&1; then
  printf 'Note: if birkin-codex is not found, add your tool bin directory to PATH.\n'
  printf '      Common locations: ~/.local/bin, pipx bin path, or uv tool dir.\n'
fi
