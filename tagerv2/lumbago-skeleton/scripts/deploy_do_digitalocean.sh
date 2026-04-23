#!/usr/bin/env bash
set -e
echo "Deploy to DigitalOcean Kubernetes - placeholder script"

# Requirements: doctl, kubectl, jq
# Usage:
# export DO_API_TOKEN=...
# ./scripts/deploy_do_digitalocean.sh <cluster-name> <registry-name>

CLUSTER_NAME=${1:-lumbago-cluster}
REGISTRY=${2:-ghcr.io/REPLACE_OWNER}

if [ -z "$DO_API_TOKEN" ]; then
  echo "Please export DO_API_TOKEN environment variable"
  exit 1
fi

echo "Authenticating doctl..."
doctl auth init -t "$DO_API_TOKEN"

echo "Getting kubeconfig for cluster: $CLUSTER_NAME"
doctl kubernetes cluster kubeconfig save "$CLUSTER_NAME"

echo "Creating secrets (if not exist)"
kubectl apply -f k8s/secrets-template.yaml

echo "Updating images to use REGISTRY=$REGISTRY"
# replace image placeholders
sed -i "s|ghcr.io/REPLACE_OWNER|$REGISTRY|g" k8s/*.yaml

echo "Applying manifests..."
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

echo "Deployment triggered. Monitor via: kubectl get pods -A"
