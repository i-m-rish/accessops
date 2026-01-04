# AccessOps — Access Request, Policy & Audit Service

## Context

This project is a small, production-style backend system.

It is NOT intended to replicate SailPoint or any full IAM product.

It exists to demonstrate:
- backend system design
- security-aware workflows
- policy-driven decision making
- auditability and compliance thinking
- async/background job handling
- cloud-ready deployment patterns

The emphasis is on correctness, clarity, and extensibility — not feature breadth.

---

## Problem Statement

In most organizations:
- users request access to systems or roles
- approvals are required based on risk
- decisions must be auditable
- access changes are executed asynchronously

These concerns are often tightly coupled and poorly observable.

This project separates them into:
- request state
- policy evaluation
- approval decisions
- immutable audit events
- async provisioning execution

---

## Goals (Testable)

G1. A user can submit an access request with justification.  
- Verified by API: `POST /requests`

G2. Approvers can approve or reject requests.  
- Verified by role-restricted endpoints

G3. Policy rules determine how many approvals are required.  
- Verified by policy engine unit tests

G4. Every state change is recorded as an immutable audit event.  
- Verified by querying audit logs

G5. Approved requests trigger asynchronous provisioning.  
- Verified by background job execution

G6. The system can be started locally using Docker.  
- Verified by `docker-compose up` and `/health` check

---

## Non-Goals (Explicit)

- Not a full IAM product
- Not a SailPoint replacement
- No UI in v1 (API-first only)
- No real AD / LDAP integration in v1
- No multi-tenant architecture in v1
- No entitlement mining or role discovery

---

## Actors and Roles

### REQUESTER
- submits access requests
- views own requests

### APPROVER
- reviews pending requests
- approves or rejects requests

### ADMIN
- views all requests
- views audit logs

---

## Terminology (Frozen)

- **Access Request**: a request for access to a resource
- **Approval**: a single approve/reject decision
- **Policy Evaluation**: logic that determines required approvals
- **Provisioning**: execution of access change on target system
- **Audit Event**: immutable record of an action

These terms must be used consistently in code, logs, APIs, and database tables.

---

## State vs Event Rule

- `AccessRequest` represents current state.
- `AuditEvent` represents historical facts.
- State may change; events must never change.

Example:
- `AccessRequest.status = APPROVED`
- `AuditEvent = REQUEST_APPROVED` (timestamped, immutable)

---

## Data Model (Core Entities)

### User
- id (uuid)
- email (unique)
- password_hash
- display_name
- role (REQUESTER / APPROVER / ADMIN)
- department (optional)
- created_at

---

### AccessRequest
- id (uuid)
- requester_id (FK → User)
- target_system (string)
- access_item (string)
- justification (text)
- duration_days (optional)
- status (PENDING / IN_REVIEW / APPROVED / REJECTED / EXPIRED / FAILED)
- required_approvals (int)
- approvals_received (int)
- created_at
- updated_at
- decided_at (nullable)

---

### ApprovalDecision
- id (uuid)
- request_id (FK → AccessRequest)
- approver_id (FK → User)
- decision (APPROVE / REJECT)
- comment (optional)
- created_at

Constraint:
- one approver can decide once per request

---

### AuditEvent (Append-Only)
- id (uuid)
- entity_type (string)
- entity_id (uuid)
- event_type (string)
- actor_user_id (nullable)
- payload (json)
- created_at

Rule:
- AuditEvent must never be updated or deleted via the application

---

### ProvisioningJob
- id (uuid)
- request_id (FK → AccessRequest)
- status (QUEUED / RUNNING / SUCCEEDED / FAILED)
- attempts (int)
- last_error (nullable)
- started_at
- finished_at
- created_at

---

## Workflow

### 1. Create Request
- Requester submits access request
- Policy engine evaluates risk and required approvals
- Request status becomes PENDING or IN_REVIEW
- Audit events written:
  - REQUEST_CREATED
  - POLICY_EVALUATED

---

### 2. Approval
- Approvers review pending requests
- Approve or reject decision recorded
- If rejected → request ends immediately
- If approvals reach required count → request APPROVED
- Audit events written:
  - APPROVAL_RECORDED
  - REQUEST_APPROVED or REQUEST_REJECTED

---

### 3. Provisioning (Async)
- Approved requests create a provisioning job
- Background worker executes provisioning (simulated webhook)
- Retries allowed
- On failure → request marked FAILED
- Audit events written:
  - PROVISIONING_STARTED
  - PROVISIONING_SUCCEEDED / PROVISIONING_FAILED

---

## Policy Engine (Deterministic v1)

Rules evaluated on request creation:

1. If access item contains "ADMIN":
   - required_approvals = 2
2. Otherwise:
   - required_approvals = 1
3. Optional risk adjustment based on department mismatch

Policy output stored with request:
- required_approvals
- matched_rules
- baseline_risk (LOW / MEDIUM / HIGH)

---

## API Scope (v1)

Auth:
- POST /auth/register
- POST /auth/login

Requests:
- POST /requests
- GET /requests/me
- GET /requests/{id}

Approvals:
- GET /approvals/pending
- POST /requests/{id}/approve
- POST /requests/{id}/reject

Audit:
- GET /audit

Health:
- GET /health

---

## Security Requirements

- Password hashing (bcrypt/argon2)
- JWT-based authentication
- Role-based access control
- Input validation
- ORM-based DB access
- Audit events immutable

---

## Deployment

- Dockerfile for API
- docker-compose for API + PostgreSQL
- Environment-based configuration
- Local development and cloud-ready structure

---

## Future Enhancements (Optional)

- OIDC integration (Auth0 / Okta / Azure AD)
- Simple UI dashboard
- AI-based risk scoring (advisory only)
- Multi-tenant support
- Real connector integrations
