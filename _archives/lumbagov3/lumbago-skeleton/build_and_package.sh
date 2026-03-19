#!/usr/bin/env bash
set -euo pipefail
echo "Building images and packaging distribution..."
docker build -t lumbago/backend:local -f backend/Dockerfile backend || true
docker build -t lumbago/frontend:local -f frontend/Dockerfile frontend || true
TMPDIR="/tmp/lumbago_build_artifacts"
rm -rf "$TMPDIR" || true
mkdir -p "$TMPDIR"
cp -r backend "$TMPDIR"/backend
cp -r frontend "$TMPDIR"/frontend
cd /tmp
zip -r /mnt/data/lumbago-distribution.zip lumbago_build_artifacts || true
echo "Created /mnt/data/lumbago-distribution.zip"
