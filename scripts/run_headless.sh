#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN=""
if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "Nie znaleziono interpretera Python (python3/python)." >&2
  exit 1
fi

if [[ "${LUMBAGO_HEADLESS_MODE:-auto}" == "offscreen" ]]; then
  exec env QT_QPA_PLATFORM=offscreen "$PYTHON_BIN" -m lumbago_app.main "$@"
fi

if command -v xvfb-run >/dev/null 2>&1; then
  exec xvfb-run -a "$PYTHON_BIN" -m lumbago_app.main "$@"
fi

echo "xvfb-run nie jest zainstalowany — uruchamiam fallback QT_QPA_PLATFORM=offscreen." >&2
echo "Aby użyć Xvfb: sudo apt-get install -y xvfb" >&2
exec env QT_QPA_PLATFORM=offscreen "$PYTHON_BIN" -m lumbago_app.main "$@"
