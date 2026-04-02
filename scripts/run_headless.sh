#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v xvfb-run >/dev/null 2>&1; then
  echo "xvfb-run is not installed. Install it with: sudo apt-get install -y xvfb" >&2
  exit 1
fi

exec xvfb-run -a python -m lumbago_app.main "$@"
