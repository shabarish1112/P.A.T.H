# P.A.T.H. second-round remediation report

Date: 2026-10-21 (Asia/Calcutta).

This is a source remediation, not a verified production deployment. The Docker
client is installed but its Linux engine pipe is absent. No production push,
deployment or destructive operation on a production database was performed.

The user-requested cleanup removed local environment files and local Mongo data.
Recreate private configuration and the first admin before starting the project.
Tooling used for verification was kept outside the repository. Local versions:
Python 3.14.6, Node 24.19.0, Docker CLI 29.6.1, isolated MongoDB 8.3.8.

## Requirement evidence

| ID | Status | Evidence |
|---|---|---|
| A1 | DONE | Runtime/secrets/cache cleanup; .gitignore; both .dockerignore files; tracked-file and final physical-tree checks. |
| A2 | DONE | Separate infra/mongo.env.example, backend/.env.example and frontend/.env.example; all three Compose files; README matrix. |
| A3 | DONE | 27 default detectors; 3 planted findings; scan and enforcing hook exit 0; CI secret-scan job. |
| A4 | DONE | docs/SECRET_ROTATION.md covers JWT/session, root/app Mongo, Redis, admin and TLS rotation and shared archives. |
| B1 | DONE | PyJWT 2.15.1 in runtime lock; full Python audit exit 0; auth/security tests pass. |
| B2 | DONE | requirements.in / requirements-dev.in and universal hashed locks; hash-enforced install passed; Dockerfile --require-hashes. |
| B3 | DONE | Tailwind 4.3.3 / @tailwindcss/postcss and PostCSS 8.5.31; clean npm ci, build and audit exit 0. |
| B4 | DONE | Six base-image digests plus Trivy digest; all external Actions SHA-pinned; Dependabot for pip/npm/Docker/Actions. |
| B5 | DONE | docs/licenses/python.json and npm.json; scripts/check_licenses.py passed for 576 records; empty GPL/AGPL allowlist; CI policy. |
| C1 | DONE | ruff check . and ruff format --check . exit 0 with original rules. |
| C2 | DONE | mypy app exit 0 (63 source files); narrowed auth user, validated serializers, lifespan/handlers and FastAPI subclass override. |
| C3 | DONE | npm run lint and npm run format:check exit 0; formatted multi-line JSX. |
| D1 | DONE | Starlette 1.9.0 + httpx2 2.16.0 pinned; supported TestClient; filterwarnings=error unchanged. |
| D2 | DONE | Reserved-domain and 404/422 fixtures fixed; as_utc and atomic expiry checks; portable detail queries; model test now requires completion. |
| D3 | DONE | 54 backend tests pass, coverage 88.57%; security, rollback, bounds, retention, lease and admin tests. |
| D4 | DONE | E2E discovery excluded; vi.hoisted mock; explicit file-form submit; complete frontend coverage gates pass unchanged. |
| E1 | DONE | Configurable Uvicorn trusted proxies/workers; Caddy fixed private IP; email+IP and per-IP exponential throttles; spoof tests. |
| E2 | DONE | Atomic consume; replay audit/session revocation; token versions fence concurrent reuse; concurrent-consumption and revocation tests. |
| E3 | DONE | Self/last-admin guards under lease; change/reset endpoints; forced-change UI; audits; reset/password/role tests. |
| E4 | DONE | Expiring owner-fenced model leases with heartbeat; scheduling failure cleanup; stale-job recovery; crash/owner/audit-failure tests. |
| E5 | DONE | Custom scoped role in JS and local privileged provisioner; real MongoDB 8.3.8 allowed audit insert/find and denied update/delete/drop; app readiness passed. |
| E6 | DONE | Startup/daily leased cascade for inactive datasets, transactions, anomalies, runs and linked reviews; count logs; cascade test. |
| E7 | DONE | Streaming TextIO CSV parsing; MAX_ROWS; 500-row staging batches; ready/activate last; rollback tests; bounded ML cursor and authoritative row guard. |
| E8 | DONE | No request user_email; validated request IDs; validation payloads omit input values; privacy regression test. |
| E9 | PARTIAL | Redis password/private network, proxy/worker config, TLS-aware bootstrap design and single-flight StrictMode restore implemented. Docker requireTLS/Redis runtime not run. |
| F1 | PARTIAL | All local backend/frontend/secret gates pass; Actionlint passes. Docker build and container Playwright jobs could not run without engine. |
| F2 | PARTIAL | Release needs reusable CI; builds, HIGH/CRITICAL scan, retained CycloneDX SBOMs precede push. Trivy/image build/push not executed locally. |
| F3 | PARTIAL | Production Compose config exit 0; smoke.py implements 200/401/403 checks. Container smoke cannot run; real Mongo readiness/401 and integration role tests passed. |
| F4 | DONE | CI/release concurrency, job permissions and dependency caching; checksum-verified Actionlint v1.7.12 exit 0. |
| G1 | DONE | README prerequisites/exact pinned versions, Docker/manual setup, environment matrix, first admin, quality commands, architecture and troubleshooting. |
| G2 | DONE | Regenerated docs/openapi.json and Postman collection with new endpoints and bearer auth; endpoint/schema assertions passed; API role table updated. |
| G3 | DONE | Privacy docs cover daily cascade, no request emails and DB-enforced audit immutability; legal-review framing retained. |
| G4 | DONE | SECURITY.md explicit reporting-contact placeholder and response-timeline template; must be filled before production. |

## Definition-of-done command tails

Python commands used `python -m <tool>` from an isolated external runtime. This
preserves the clean source tree while executing the same tools/configuration. No
coverage thresholds, warning policies, lint selections or failing tests were removed.

### backend lint — exit 0

`python -m ruff check .`

```text
All checks passed!
```

### backend format — exit 0

`python -m ruff format --check .`

```text
81 files already formatted
```

### backend types — exit 0

`python -m mypy app`

```text
Success: no issues found in 63 source files
```

### backend tests — exit 0

`python -m pytest`

```text
app\services\review_service.py           29      1    97%   67
app\services\transaction_service.py      29      5    83%   33, 38-41
app\services\user_service.py             52      7    87%   27-28, 38, 42, 58, 65, 67
-------------------------------------------------------------------
TOTAL                                  1969    225    89%
Required test coverage of 85% reached. Total coverage: 88.57%
54 passed in 16.94s
```

### Python audit — exit 0

`python -m pip_audit -r backend/requirements.lock`

```text
No known vulnerabilities found
```

### frontend lint — exit 0

`npm run lint`

```text
npm notice run path-frontend@1.0.0 lint
npm notice run eslint src tests e2e --max-warnings=0
```

### frontend format — exit 0

`npm run format:check`

```text
Checking formatting...
All matched files use Prettier code style!
npm notice run path-frontend@1.0.0 format:check
npm notice run prettier --check .
```

### frontend tests — exit 0

`npm test`

```text

=============================== Coverage summary ===============================
Statements   : 91.69% ( 475/518 )
Branches     : 80% ( 232/290 )
Functions    : 91.95% ( 160/174 )
Lines        : 94.81% ( 439/463 )
================================================================================
npm notice run path-frontend@1.0.0 test
npm notice run vitest run --coverage
```

### frontend build — exit 0

`npm run build`

```text
dist/assets/index-18-bdtIR.css             17.05 kB │ gzip:  4.97 kB
dist/assets/rolldown-runtime-WkwZ5CU-.js    0.59 kB │ gzip:  0.36 kB
dist/assets/index-_806F4SI.js              36.24 kB │ gzip: 10.21 kB
dist/assets/router-DEtIVqIN.js             39.74 kB │ gzip: 14.25 kB
dist/assets/react-7VJPxFFw.js             218.75 kB │ gzip: 68.26 kB

✓ built in 941ms
npm notice run path-frontend@1.0.0 build
npm notice run vite build
```

### npm audit — exit 0

`npm audit --audit-level=high`

```text
found 0 vulnerabilities
```

### Clean frontend installation — exit 0

`cd frontend && npm ci --no-fund`

```text

added 482 packages, and audited 483 packages in 2m

found 0 vulnerabilities
npm warn install-scripts 1 package had install scripts blocked because they are not covered by allowScripts:
npm warn install-scripts   msw@2.11.6 (postinstall: node -e "import('./config/scripts/postinstall.js').catch(() => void 0)")
npm warn install-scripts
npm warn install-scripts Run `npm install-scripts ls` to review, or `npm install-scripts approve <pkg>` to allow.
```

### Secret scanning — exit 0

```text
detect-secrets scan --baseline .secrets.baseline: exit 0
Default plugins: 27
Planted-secret test passed: 3 findings; values suppressed.
Enforcing secret hook exit: 0
```

Windows scan paths were normalized to forward slashes so the baseline is portable
to Linux CI. The enforcing hook requires the baseline to be staged; it was staged
before running the hook. Detected baseline entries are synthetic test fixtures and
example/export-only credentials; no real credentials are included.

### Configuration and independent checks — exit 0

```text
docker compose -f docker-compose.prod.yml config --quiet: exit 0
Actionlint v1.7.12: exit 0
License policy passed for 576 dependency records.
OpenAPI/Postman endpoint and auth-scheme validation: passed
Real MongoDB: audit insert/find allowed; update/delete/drop denied
Real MongoDB: application startup and readiness passed with least-privilege role
```

Compose used `--quiet` so environment values cannot enter logs. Runtime checks used
a disposable authenticated MongoDB outside the source tree, not a production DB.

## Unverified environment-dependent checks

Docker Engine is unavailable: `docker info` reports the missing
`dockerDesktopLinuxEngine` named pipe. `act` and Go are not installed. Actionlint
was downloaded from its official release and verified against its published SHA256.

On a machine with a working engine, create fresh private configuration and run:

```bash
docker build -t path-backend:verify backend
docker build -t path-frontend:verify frontend
docker compose -f docker-compose.prod.yml config --quiet
# In CI, ci_env.py supplies disposable credentials and the workflow provisions admin.
docker compose -f docker-compose.test.yml up --build -d
python scripts/smoke.py
cd frontend && npm run e2e
```

`smoke.py` and Playwright require E2E_EMAIL and E2E_PASSWORD for an existing
administrator; supply them privately without committing/logging values. Validate
production requireTLS bootstrap with operator-generated certificates. Check Redis
authentication and trusted-proxy transport behavior through the actual edge. The
release workflow's pinned Trivy scans and SBOM generation must succeed before push.
Signing is not configured. Replace the security reporting contact before production.

## API-client-visible behavior changes

- Auth user responses include `must_change_password`; reset users are restricted to
  auth/me, auth/change-password and auth/logout until they change their password.
- New POST /api/auth/change-password and POST /api/users/{user_id}/reset-password.
  A password change revokes sessions and requires sign-in again.
- Refresh replay returns 401, revokes user sessions and appends an audit event.
  Role changes/deactivation also revoke tokens immediately using a token version.
- Self-demotion/deactivation and removal of the last active admin return 409.
- Login backoff is per email+transport IP and separately across emails per IP.
- Upload/model row bounds return 413; uploads activate only after successful staging.
- Invalid X-Request-ID values are replaced. Validation errors omit submitted input
  values. Existing public response shapes are otherwise retained.

## Commits

A: 725a6dd; B: 3fc5d2e; C: b4bf164; D: 79b95dc; E: 859ad02;
F: 01a36a1; G: 013aec0. Final evidence, cleanup and small validation follow-ups are
recorded in the section H commit. The checkout originally had no Git metadata; Git
was initialized using the user's configured author identity. No remote was created.

## Final source hygiene

```text
Physical source-tree hygiene: PASS
Tracked-file hygiene: PASS (only environment examples match)
Whitespace check: 0
```

Generated dependencies, build output, local credentials, Mongo data and caches
were removed after verification. The disposable external MongoDB was stopped and
its data removed. The final source package intentionally does not contain an
installed runtime; use the documented fresh setup commands.
