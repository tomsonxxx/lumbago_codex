#!/usr/bin/env bash
set -euo pipefail

# Lightweight Linux diagnostic for PyQt6 runtime deps and app smoke run.
# Usage:
#   bash scripts/check_pyqt_linux.sh
#   INSTALL_DEPS=1 bash scripts/check_pyqt_linux.sh
#   INSTALL_DEPS=1 WITH_MULTIMEDIA=1 bash scripts/check_pyqt_linux.sh

if [[ "${OSTYPE:-}" != linux* ]]; then
  echo "Ten skrypt jest przeznaczony dla Linux."
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Brak polecenia python w PATH."
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Brak apt-get. Skrypt wspiera tylko Debian/Ubuntu."
  exit 1
fi

CORE_DEPS=(
  libegl1
  libglib2.0-0
  libdbus-1-3
  libfontconfig1
  libx11-6
  libx11-xcb1
  libxext6
  libxrender1
  libxkbcommon0
  libxkbcommon-x11-0
  libxcb1
  libxcb-cursor0
  libxcb-icccm4
  libxcb-image0
  libxcb-keysyms1
  libxcb-randr0
  libxcb-render0
  libxcb-render-util0
  libxcb-shape0
  libxcb-shm0
  libxcb-xfixes0
)

MULTIMEDIA_DEPS=(
  libasound2
  libpulse0
  gstreamer1.0-plugins-base
  gstreamer1.0-plugins-good
)

if [[ "${WITH_MULTIMEDIA:-0}" == "1" ]]; then
  DEPS=("${CORE_DEPS[@]}" "${MULTIMEDIA_DEPS[@]}")
else
  DEPS=("${CORE_DEPS[@]}")
fi

echo "=== Sprawdzanie pakietow systemowych ==="
MISSING=()
for pkg in "${DEPS[@]}"; do
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "OK  $pkg"
  else
    echo "MISS $pkg"
    MISSING+=("$pkg")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  echo
  echo "Brakuje pakietow: ${MISSING[*]}"
  if [[ "${INSTALL_DEPS:-0}" == "1" ]]; then
    echo "Instaluje brakujace pakiety..."
    sudo apt-get update
    sudo apt-get install -y "${MISSING[@]}"
  else
    echo "Aby zainstalowac automatycznie uruchom:"
    if [[ "${WITH_MULTIMEDIA:-0}" == "1" ]]; then
      echo "  INSTALL_DEPS=1 WITH_MULTIMEDIA=1 bash scripts/check_pyqt_linux.sh"
    else
      echo "  INSTALL_DEPS=1 bash scripts/check_pyqt_linux.sh"
    fi
  fi
fi

echo
echo "=== Test importu PyQt6 ==="
python - <<'PY'
from PyQt6 import QtWidgets
print("PyQt6 GUI import OK")
PY

echo
echo "=== Smoke test aplikacji (bez multimedia) ==="
LUMBAGO_SAFE_MODE=1 \
LUMBAGO_DISABLE_MULTIMEDIA=1 \
LUMBAGO_SMOKE_SECONDS=2 \
python -m lumbago_app.main

echo
echo "Gotowe: diagnostyka zakonczona."
