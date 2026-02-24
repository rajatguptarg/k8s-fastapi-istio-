#!/usr/bin/env bash
set -euo pipefail

# Namespaces
ISTIO_NS="istio-system"
WEBAPP1_NS="webapp1"
WEBAPP2_NS="webapp2"

# Install Istio control plane + ingress gateway in istio-system.
kubectl create namespace "${ISTIO_NS}" --dry-run=client -o yaml | kubectl apply -f -
istioctl install -y --set profile=default

# Create namespaces for workloads.
kubectl create namespace "${WEBAPP1_NS}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${WEBAPP2_NS}" --dry-run=client -o yaml | kubectl apply -f -

# Enable automatic sidecar injection in app namespaces.
kubectl label namespace "${WEBAPP1_NS}" istio-injection=enabled --overwrite
kubectl label namespace "${WEBAPP2_NS}" istio-injection=enabled --overwrite

# Deploy apps in separate namespaces.
helm upgrade --install webapp1 helm/webapp1 -n "${WEBAPP1_NS}" --create-namespace
helm upgrade --install webapp2 helm/webapp2 -n "${WEBAPP2_NS}" --create-namespace

# Apply Istio traffic and security configuration.
kubectl apply -f istio/gateway.yaml
kubectl apply -f istio/virtualservices.yaml
kubectl apply -f istio/peerauthentications.yaml
kubectl apply -f istio/authorizationpolicies.yaml

# Ensure workloads are recreated with sidecars.
kubectl rollout restart deployment/webapp1 -n "${WEBAPP1_NS}"
kubectl rollout restart deployment/webapp2 -n "${WEBAPP2_NS}"

kubectl rollout status deployment/webapp1 -n "${WEBAPP1_NS}"
kubectl rollout status deployment/webapp2 -n "${WEBAPP2_NS}"

echo "Istio + webapp1/webapp2 deployed to separate namespaces."
