#!/usr/bin/env sh
set -eu

PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
INSTALL_UV="${INSTALL_UV:-0}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SKILL_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
# Keep durable state in the active workspace so it survives plugin-cache refreshes.
WORKSPACE="$PWD"
VENV_PATH="$WORKSPACE/.paper-obsidian/.venv"
mkdir -p "$WORKSPACE/.paper-obsidian"

if ! command -v uv >/dev/null 2>&1; then
  if [ "$INSTALL_UV" = "1" ]; then
    echo "Installing uv with the official Astral installer"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found. Re-run with INSTALL_UV=1, or install uv manually first." >&2
  exit 1
fi

uv python install "$PYTHON_VERSION"
uv venv "$VENV_PATH" --python "$PYTHON_VERSION"
PYTHON="$VENV_PATH/bin/python"
uv pip install --python "$PYTHON" -r "$SKILL_ROOT/requirements.txt"
"$PYTHON" "$SKILL_ROOT/scripts/setup_environment.py" --check-only --json-report "$WORKSPACE/.paper-obsidian/environment-check.json"

echo "paper-to-obsidian-skill environment is ready: $VENV_PATH"
