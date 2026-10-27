# Public analysis and optional accounts

## Routes and boundaries

| Browser route | Access | Purpose |
| --- | --- | --- |
| / | Everyone | Upload a CSV and run a real model |
| /results/:analysisId | Originating browser | View and download temporary results |
| /signup, /login | Everyone | Optional accounts |
| /workspace and existing staff routes | Existing staff roles | Shared institutional dataset, reviews and administration |

Do not remove require_role from staff endpoints. Public analysis uses separate
public_analyses documents and never changes active_dataset_id, staff transactions,
model_runs or reviews. Result IDs alone do not grant access: a signed, expiring,
HttpOnly SameSite=Strict guest cookie must match the stored session. Expired records
are excluded immediately and removed asynchronously by MongoDB's TTL index.

POST /api/public/analyze accepts a UTF-8 CSV multipart file and a model query
parameter (if, eif, dif). It reuses validate_csv_rows, engineer_features and run_model.
Models run synchronously, not as unreliable serverless background tasks. The response
contains up to 50 ranked candidates and row-validation issues. GET
/api/public/analyses/{id} reloads only that browser's unexpired result. Downloads are
JSON generated from that same response. The sample CSV is explicitly synthetic.

Limits are enforced server-side: at most 4 MB, 4,000 rows, 100 trees, no UMAP,
one public analysis at a time and six requests per network address per hour.
GET /api/public/limits exposes the deployment's effective limits. Invalid upload
attempts also consume quota. Shared networks share a quota; a public launch may
need a trusted-edge limiter or bot protection. Limits constrain, but do not guarantee,
Vercel's 300-second execution budget. A timeout can leave a lease occupied until expiry.

## Accounts

POST /api/auth/signup accepts only email and password (12-128 characters). Extra
fields such as role are rejected. The server always creates a member, never a staff
role. Existing Argon2 hashing, short-lived in-memory access tokens, HttpOnly refresh
cookies, refresh rotation, logout and session revocation are reused. Registration
has an atomic per-address limit of ten attempts per hour and a unique email index.
Account email ownership is not yet verified; password recovery is not included.

Members can use public analysis but cannot read institutional transactions, review
cases or access user/audit administration. Frontend guards are for navigation;
backend role checks remain the authorization boundary.

## Future history and settings

Users retain stable MongoDB IDs and created_at. Each result includes a nullable
user_id assigned only from a verified active access token, never request input.
This is a foundation for a future account-scoped history repository and preferences
collection. Guest results are not silently migrated to accounts. Current results
expire after 24 hours even when signed in; no permanent-history UI is claimed.

## Migration and deployment

initialize_database adds the member user-schema value, public_analyses validator,
TTL index on expire_at, and user_id/created_at index. Existing users and data are
preserved. The Docker initializer and scripts/provision_mongo.py grant the new
collection to pathApplication. Existing restricted Mongo installations must rerun
the documented privileged provision_database procedure before starting updated code;
editing initialization scripts alone does not update an existing Mongo volume.
Atlas credentials must likewise allow the validator and index migration.

Do not roll back to a user validator that rejects member while member accounts
exist. Disabling the public routes is a safe application rollback; preserve new
user records and let temporary results expire.

Use an independent database for previews and tests. Keep production JWT_SECRET
stable across deployments so guest and account cookies remain valid. No new paid
services, credentials or packages are required. Test the Vercel production build,
Atlas migration and guest upload in a private browser before declaring release ready.

## Verification commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m ruff check app tests
cd ..\frontend
npm run lint
npm test
npm run build
```
