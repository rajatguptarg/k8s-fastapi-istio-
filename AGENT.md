# AGENT.md

Guidelines for AI agents working in this repository.

This document explains the project layout, architectural principles, and guardrails you must follow when editing or generating code. [fastapi.tiangolo](https://fastapi.tiangolo.com/tutorial/bigger-applications/)

***

## 1. Repository Overview

Top-level layout (simplified):

```text
k8s-fastapi-istio/
├── apps/
│   ├── webapp1/        # FastAPI service 1
│   └── webapp2/        # FastAPI service 2
├── helm/               # Helm charts for k8s deployments
│   ├── webapp1/
│   └── webapp2/
└── istio/              # Istio service mesh config (mTLS, authz, routing)
```

Each app is an FastAPI project with clear separation of concerns (API, services, models, core). All Kubernetes, Helm, and Istio config must live under `helm/` and `istio/`, not embedded as raw `kubectl` manifests.

When you add or modify code, keep this separation and folder layout intact. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_bc56ec9c-ad0b-4376-a03b-decdde87248d/18ef6c94-a194-4451-9b27-4d0cae4fad66/kubernetes-in-action.pdf)

***

## 2. Application Structure (per FastAPI App)

Each service (`apps/webapp1`, `apps/webapp2`) follows this pattern:

```text
apps/<service>/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── <resource>.py      # HTTP routing only
│   ├── core/
│   │   ├── config.py              # Pydantic settings-based config
│   │   └── logging.py             # Centralized logging setup
│   ├── database/                  # (webapp1 only, later)
│   │   └── schema.py
│   ├── models/
│   │   └── <resource>.py          # Pydantic request/response schemas
│   ├── services/
│   │   └── <resource>_service.py  # Business logic
│   └── main.py                    # App entrypoint, router registration
├── tests/
│   └── api/
│       └── v1/
│           └── test_<resource>.py # Mirrors app/api/v1
├── .env.example
├── Dockerfile
├── pyproject.toml
└── uv.lock (optional)
```

**Do not** introduce new top-level layers (e.g., `repositories/`, `routers/`) unless explicitly requested; extend within this structure instead. [dev](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6)

***

## 3. Design Principles

### 3.1 Thin Routers, Fat Services

- `app/api/v1/*.py` files:
  - Define HTTP routes (`APIRouter`, path operations).
  - Parse/validate HTTP input and map to Pydantic models.
  - Delegate all business logic to services via `Depends`. [fastapi.tiangolo](https://fastapi.tiangolo.com/tutorial/dependencies/)
  - Contain **no business rules**, persistence logic, or domain decisions.

- `app/services/*.py`:
  - Contain **all business logic** (the “seam” between HTTP and persistence). [t-roller](https://t-roller.com/blog/fastapi-project-structure-best-practices-1761202317414)
  - May call:
    - internal domain logic,
    - database layer (`app/database/`),
    - other services (via HTTP) using configuration from `core.config`.

If you need to add or change logic, prefer editing `services/` first, then wiring from `api/`.

### 3.2 Config Management

- Use `pydantic-settings` `BaseSettings` subclasses in `app/core/config.py`. [fastapi.tiangolo](https://fastapi.tiangolo.com/ja/advanced/settings/)
- All environment-dependent parameters must go into settings:
  - service URLs (e.g., `webapp1_base_url`, `webapp2_base_url`),
  - environment, debug flags,
  - DB DSNs (future).
- Load from `.env` for local use; rely on real environment variables in Kubernetes.
- Never hard-code secrets or environment-specific URLs in code or Helm templates.

When you need a new config value:
1. Add it to `Settings` in `core/config.py`.
2. Expose it via `get_settings()` (cached).
3. Inject settings in routes/services using `Depends(get_settings)`.

### 3.3 Logging

- `app/core/logging.py` defines the **single** logging entrypoint.
- `main.py` must always call `configure_logging()` exactly once on startup.
- Other modules obtain loggers via:

  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

- Do not use `print()` for runtime logs.

If switching to structured/JSON logging later, do it centrally in `core/logging.py`.

### 3.4 Dependency Injection

- Use FastAPI’s built-in `Depends` and `Annotated` (preferred). [fastapi.tiangolo](https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/)
- Services are injected via small factory functions in the router modules, e.g.:

  ```python
  def get_user_service() -> UserService:
      return UserService()
  ```

- For tests, override dependencies via `app.dependency_overrides`.

Do **not** introduce an external DI framework unless explicitly requested.

***

## 4. Testing Guidelines

- Test layout mirrors `app/` layout:

  ```text
  apps/<service>/tests/api/v1/test_<resource>.py
  ```

- Use FastAPI `TestClient` for HTTP-level tests. [fastapi.tiangolo](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- Prefer small, focused tests:
  - happy path,
  - validation errors,
  - simple edge cases.

- For now, services can be tested in-memory; once DB integration exists, use:
  - in-memory SQLite,
  - per-test setup/teardown,
  - no calls to production infrastructure.

When changing APIs, **update or add tests in the mirrored path**.

***

## 5. Kubernetes, Helm, and Istio

### 5.1 Helm

- All Kubernetes manifests must be defined as **Helm templates** under `helm/<service>/`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_bc56ec9c-ad0b-4376-a03b-decdde87248d/54589923-e2d0-4b3b-ada9-1c0a7f517dcf/k8s-book.pdf)
- Each service has:
  - `Chart.yaml`
  - `values.yaml`
  - `templates/deployment.yaml`
  - `templates/service.yaml`
  - optional: `templates/ingress.yaml`, `templates/serviceaccount.yaml`, etc.

Rules:

- Do not add raw manifests outside Helm charts.
- Keep app configuration coming from:
  - environment variables wired from `values.yaml`,
  - or ConfigMaps/Secrets (if added later).
- Probes (`/health`) must use the health endpoint defined in `main.py`.

### 5.2 Service Naming / DNS

- In-cluster DNS naming follows `svc-name.namespace.svc.cluster.local`. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_bc56ec9c-ad0b-4376-a03b-decdde87248d/18ef6c94-a194-4451-9b27-4d0cae4fad66/kubernetes-in-action.pdf)
- Use this pattern in config defaults:
  - WebApp1 config: `webapp2_base_url = "http://webapp2.default.svc.cluster.local"`.
  - WebApp2 config: `webapp1_base_url = "http://webapp1.default.svc.cluster.local"`.

When you change service names or namespaces, update:
- Helm `Service` names,
- config defaults,
- any tests that rely on the URLs.

### 5.3 Istio

Istio configuration lives in `istio/` as separate manifests:

- `gateway.yaml` – external entrypoint.
- `virtualservices.yaml` – HTTP routing for webapp1/webapp2.
- `peerauthentications.yaml` – mTLS mode (STRICT for services).
- `authorizationpolicies.yaml` – access control via **principals**. [redhat](https://www.redhat.com/en/blog/service-mesh-mtls)

Rules:

- mTLS should be **STRICT** for app-to-app communication.
- AuthorizationPolicy must:
  - select apps via `matchLabels` (e.g., `app: webapp1`),
  - restrict `from` sources by **service account principal**, e.g.:

    ```yaml
    principals: ["cluster.local/ns/default/sa/webapp2"]
    ```

- Do not hard-code IPs; always use DNS and service accounts.

Any change affecting identity or labels must be reflected in these policies.

***

## 6. Agent Workflow Expectations

When implementing a change:

1. **Locate the correct layer**
   - New HTTP endpoint → `app/api/v1/*.py` + corresponding `services/*.py` and `models/*.py`.
   - New business rule → `services/*.py`.
   - New configuration → `core/config.py` + Helm `values.yaml` (if k8s-related).
   - Mesh/security behavior → files under `istio/`.

2. **Respect boundaries**
   - No business logic in routers.
   - No direct DB access from routers; route → service → DB.
   - No cross-cutting concern (logging/config) implemented ad hoc.

3. **Keep docs and tests in sync**
   - When you add/modify endpoints, update or add tests in `tests/api/v1`.
   - If the change is structural, update this `AGENTS.md` if it affects how agents should reason about the project.

4. **No silent conventions**
   - If you introduce a new pattern (e.g., background tasks, new config sections, new Helm values), document it here in a new section.

***

## 7. Things You Must Not Do

- Do not:
  - Add global mutable state for services.
  - Hard-code environment-specific values (URLs, secrets, credentials) in code.
  - Bypass Helm by committing raw `kubectl apply` manifests.
  - Mix unrelated concerns (e.g., call HTTP services from models, or add DB code in routers).
  - Introduce new dependencies or frameworks without justification in comments and alignment with the existing stack.

***

## 8. Quick Reference

- FastAPI “bigger applications” / multi-file structure: routers + central app. [fastapiinteractive](https://www.fastapiinteractive.com/fastapi-basics/34-bigger-applications)
- Pydantic settings for config and `.env` loading. [fastapi.tiangolo](https://fastapi.tiangolo.com/advanced/settings/)
- Service-layer + API-layer separation for scalable projects. [dev](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6)
- Kubernetes manifests via Helm only. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_bc56ec9c-ad0b-4376-a03b-decdde87248d/54589923-e2d0-4b3b-ada9-1c0a7f517dcf/k8s-book.pdf)
- Service mesh security via Istio mTLS and AuthorizationPolicy. [redhat](https://www.redhat.com/en/blog/service-mesh-mtls)

If a future change conflicts with this document, update `AGENTS.md` first, then adjust code to match.
