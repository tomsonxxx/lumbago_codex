#!/usr/bin/env bash
set -e
echo "Build and run Docker compose (prod)"
docker-compose -f docker-compose.prod.yml build --pull
docker-compose -f docker-compose.prod.yml up -d
echo "Containers launched."
