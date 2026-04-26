# AccessOps Architecture

AccessOps is an IAM/IGA-inspired access governance platform. The current implementation covers secure registration, JWT authentication, server-side RBAC, access request approval, provisioning lifecycle tracking, audit logging, backend CI, and a basic Next.js UI.

## Architecture Goals

| Goal | Implementation |
|---|---|
| Secure registration | Public registration creates only `REQUESTER`; browser-supplied role is rejected. |
| Server-side authorization | Backend RBAC dependencies enforce roles; UI is never authority. |
| Access request workflow | Requester creates; approver/admin approves or rejects. |
| Provisioning lifecycle | Approval and provisioning are separate lifecycle states. |
| Auditability | Approval, rejection, and provisioning emit audit events. |
| Migration discipline | Alembic owns database schema changes. |
| CI validation | GitHub Actions runs Postgres, Alembic, and pytest. |

## High-Level Design

```mermaid
flowchart LR
    User[Requester / Approver / Admin]
    UI[Next.js UI]
    API[FastAPI Backend]
    Auth[JWT Auth]
    RBAC[RBAC + Policy]
    DB[(PostgreSQL)]
    Audit[Audit Events]
    Alembic[Alembic]
    CI[GitHub Actions]

    User --> UI
    UI --> API
    API --> Auth
    API --> RBAC
    API --> DB
    API --> Audit
    Audit --> DB
    Alembic --> DB
    CI --> Alembic
    CI --> API
```

## Backend Low-Level Design

```mermaid
flowchart TD
    main[app/main.py]
    auth[routers/auth.py]
    req[routers/requests.py]
    useradmin[routers/user_admin.py]
    rbac[core/rbac.py]
    policy[core/policy.py]
    jwt[core/jwt.py]
    sec[core/security.py]
    schemas[schemas]
    models[models]
    audit[services/audit_service.py]
    db[db/session.py]
    pg[(PostgreSQL)]

    main --> auth
    main --> req
    main --> useradmin
    auth --> jwt
    auth --> sec
    auth --> schemas
    req --> rbac
    req --> policy
    req --> audit
    req --> schemas
    useradmin --> rbac
    schemas --> models
    models --> pg
    db --> pg
    audit --> pg
```

## Modules

| Module | Purpose |
|---|---|
| `app/main.py` | FastAPI app, CORS, router registration, health check. |
| `app/routers/auth.py` | Register/login; registration assigns `REQUESTER` server-side. |
| `app/routers/requests.py` | Create/list/pending/approve/reject/provision request APIs. |
| `app/routers/user_admin.py` | Protected role-management endpoint. |
| `app/core/rbac.py` | JWT extraction and role guards. |
| `app/core/policy.py` | Business checks such as self-approval prevention. |
| `app/models` | SQLAlchemy persistence model. |
| `app/schemas` | Pydantic request/response contracts. |
| `app/services/audit_service.py` | Audit event persistence. |
| `alembic/versions` | Schema migrations. |
| `accessops-ui` | Next.js UI. |
| `.github/workflows/backend-ci.yml` | Backend CI workflow. |

## Runtime Request Flow

```mermaid
sequenceDiagram
    autonumber
    actor Requester
    participant UI as Next.js UI
    participant API as FastAPI
    participant RBAC as RBAC/Policy
    participant DB as PostgreSQL
    participant Audit as Audit Service

    Requester->>UI: Submit access request
    UI->>API: POST /requests
    API->>RBAC: Validate JWT and role
    RBAC-->>API: Allowed
    API->>DB: Insert request
    API-->>UI: PENDING + NOT_STARTED

    actor Approver
    Approver->>UI: Approve request
    UI->>API: PATCH /requests/{id}/approve
    API->>RBAC: Check APPROVER/ADMIN and no self-approval
    API->>DB: status=APPROVED, provisioning_status=QUEUED
    API->>Audit: access_request.approved
    Audit->>DB: Insert audit event
    API-->>UI: APPROVED + QUEUED

    actor Admin
    Admin->>UI: Mark provisioned
    UI->>API: PATCH /requests/{id}/provision
    API->>RBAC: Check ADMIN
    API->>DB: provisioning_status=PROVISIONED
    API->>Audit: access_request.provisioned
    Audit->>DB: Insert audit event
    API-->>UI: APPROVED + PROVISIONED
```

## Approval Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: request created
    PENDING --> APPROVED: approve
    PENDING --> REJECTED: reject
    APPROVED --> [*]
    REJECTED --> [*]
```

## Provisioning Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NOT_STARTED: request created
    NOT_STARTED --> QUEUED: approval completed
    QUEUED --> PROVISIONED: admin marks provisioned
    QUEUED --> FAILED: future connector failure
    FAILED --> QUEUED: future retry
    PROVISIONED --> [*]
```

## Entity Relationship Model

```mermaid
erDiagram
    USERS ||--o{ ACCESS_REQUESTS : requests
    USERS ||--o{ ACCESS_REQUESTS : decides
    USERS ||--o{ AUDIT_EVENTS : acts
    ACCESS_REQUESTS ||--o{ AUDIT_EVENTS : audited_by

    USERS {
        uuid id PK
        string email
        string password_hash
        string display_name
        string role
        datetime created_at
    }

    ACCESS_REQUESTS {
        uuid id PK
        uuid requester_id FK
        string resource
        string action
        text justification
        enum status
        enum provisioning_status
        uuid decided_by FK
        datetime decided_at
        datetime provisioned_at
        text provisioning_error
        datetime created_at
    }

    AUDIT_EVENTS {
        uuid id PK
        uuid actor_id FK
        string action
        string entity_type
        uuid entity_id
        json details
        datetime created_at
    }
```

## Entity Table

| Entity | Purpose | Key Fields |
|---|---|---|
| `User` | Authenticated identity. | `email`, `password_hash`, `role`, `display_name`. |
| `AccessRequest` | Access governance request. | `requester_id`, `resource`, `action`, `status`, `provisioning_status`. |
| `AuditEvent` | Governance event trail. | `actor_id`, `action`, `entity_type`, `entity_id`, `details`. |

## API Table

| Method | Path | Role | Purpose |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register requester account. |
| `POST` | `/auth/login` | Public | Return bearer token. |
| `POST` | `/requests` | Authenticated | Create request. |
| `GET` | `/requests` | Authenticated | List own/all requests based on role. |
| `GET` | `/requests/pending` | `APPROVER`, `ADMIN` | View pending approval queue. |
| `PATCH` | `/requests/{id}/approve` | `APPROVER`, `ADMIN` | Approve and queue provisioning. |
| `PATCH` | `/requests/{id}/reject` | `APPROVER`, `ADMIN` | Reject request. |
| `PATCH` | `/requests/{id}/provision` | `ADMIN` | Mark approved request as provisioned. |
| `PATCH` | `/user-admin/users/{user_id}/role` | `ADMIN` | Update user role. |
| `GET` | `/health` | Public | Health check. |

## Lifecycle Matrix

| Approval Status | Provisioning Status | Meaning |
|---|---|---|
| `PENDING` | `NOT_STARTED` | Waiting for approval decision. |
| `APPROVED` | `QUEUED` | Approved, but target access is not confirmed. |
| `APPROVED` | `PROVISIONED` | Approved and marked provisioned. |
| `APPROVED` | `FAILED` | Approved but provisioning failed. |
| `REJECTED` | `NOT_STARTED` | Denied; no provisioning expected. |

## CI Flow

```mermaid
flowchart TD
    Push[Push or PR to main]
    Checkout[Checkout repo]
    Python[Setup Python 3.11]
    PG[Start PostgreSQL service]
    Install[Install requirements]
    Migrate[alembic upgrade head]
    Test[pytest -q]

    Push --> Checkout
    Checkout --> Python
    Push --> PG
    Python --> Install
    PG --> Migrate
    Install --> Migrate
    Migrate --> Test
```

## Local Run Strategy

Use `scripts/run_all.sh` to run backend validation locally. It installs dependencies, runs migrations, and executes tests. Use `--serve` to also start the backend and UI development servers.
