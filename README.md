# k8s-fastapi-istio

Two FastAPI services (`webapp1`, `webapp2`) with Kubernetes Helm charts and Istio security policy manifests.

## Project layout

- `apps/webapp1`: User API, calls `webapp2`
- `apps/webapp2`: Item API, calls `webapp1`
- `helm/webapp1`: Helm chart for `webapp1`
- `helm/webapp2`: Helm chart for `webapp2`
- `istio`: Istio policy manifests

## Prerequisites

- Python 3.11+
- `uv` installed
- Docker (optional, for images)
- Kubernetes cluster + Helm + Istio (optional, for K8s deployment)

## Run locally

Use your active `personal` virtualenv:

```bash
source /Users/rajatgupta/.virtualenvs/personal/bin/activate
```

Install dependencies for each app into the active env:

```bash
cd apps/webapp1
uv sync --active

cd ../webapp2
uv sync --active
```

Run each app in separate terminals:

```bash
# terminal 1
cd apps/webapp1
uv run --active uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# terminal 2
cd apps/webapp2
uv run --active uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## API quick checks

```bash
# health
curl http://localhost:8000/health
curl http://localhost:8001/health

# webapp1 users
curl http://localhost:8000/api/v1/users

# webapp2 items
curl http://localhost:8001/api/v1/items
```

Cross-service calls (for local runs, set base URLs if needed in `.env`):

- `webapp1 -> webapp2`: `GET /api/v1/users/call-webapp2`
- `webapp2 -> webapp1`: `GET /api/v1/items/call-webapp1`

## Docker

Build images:

```bash
docker build -t webapp1:v1.0.0 apps/webapp1
docker build -t webapp2:v1.0.0 apps/webapp2
```

## Kubernetes with Helm

Install charts:

```bash
helm upgrade --install webapp1 helm/webapp1
helm upgrade --install webapp2 helm/webapp2
```

Current service ports:

- `webapp1`: service `80` -> container `8000`
- `webapp2`: service `80` -> container `8001`

## Istio

Available manifests:

- `istio/peerauthentications.yaml`: mTLS `STRICT` for namespace `default`
- `istio/authorizationpolicies.yaml`:
  - allow `webapp2` SA to call `webapp1` (`/api/v1/users*`, `/health`)
  - allow `webapp1` SA to call `webapp2` (`/api/v1/items*`, `/health`)

Apply:

```bash
kubectl apply -f istio/peerauthentications.yaml
kubectl apply -f istio/authorizationpolicies.yaml
```

`istio/gateway.yaml` and `istio/virtualservices.yaml` are currently empty placeholders.

## Notes

- `webapp1` chart currently references `include "webapp1.fullname"` but does not yet define it in a `_helpers.tpl`. Add that helper before templating/installing `webapp1`.
