#!/usr/bin/env bash
set -euo pipefail
echo "Starting docker-compose prod stack..."
docker-compose -f docker-compose.prod.yml up --build
