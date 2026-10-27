# Vercel Hobby deployment

This configuration deploys the existing FastAPI backend and Vite frontend together.
Vercel Services is beta and available on all plans. Hobby is for personal,
non-commercial use. No paid feature or automatic upgrade is configured here.
This is deployment preparation, not a verified hosted release.

## Import

Push vercel.json, .vercelignore, backend/.python-version and this guide to GitHub.
Import shabarish1112/P.A.T.H with repository root ./ and preset Services.
Keep both backend and frontend services. The frontend calls /api on the same origin;
leave VITE_API_URL unset. The API and health paths route to FastAPI; other paths
route to Vite with an index.html fallback for direct navigation.

## Private environment settings

Configure these in Vercel, never in GitHub files or chat. Use a separate database
and secrets for preview deployments if previews are enabled.

| Name | Value |
| --- | --- |
| MONGO_URI | Atlas mongodb+srv connection string with URL-encoded database-user password |
| MONGO_DB | path |
| JWT_SECRET | Unique cryptographically random secret, at least 32 characters |
| ENVIRONMENT | production |
| DOCS_ENABLED | false |
| CORS_ORIGINS | Exact HTTPS origin of the deployment |
| MAX_UPLOAD_MB | 4 |
| MAX_ROWS | 4000 |
| ML_MAX_ROWS | 4000 |
| ML_N_JOBS | 1 |
| NUMBA_CACHE_DIR | /tmp/numba-cache |

Generate JWT_SECRET privately with a password manager or Python secrets.token_urlsafe(48).
Do not use a memorable password or copy a published example. Never use VITE_ for
backend secrets: Vite exposes those variables to browsers.

## Atlas and first administrator

The database user must have the collection/index/validator permissions required by
backend/app/db/mongo.py. Bootstrap with a privileged identity, then use the existing
least-privilege provisioning guidance in docs/DEPLOYMENT_SECURITY.md. A basic
readWrite role alone may not support validator migrations. Do not use your Atlas
account password as the database-user password.

Add the required deployment egress addresses to Atlas Network Access. Adding your
computer's IP only does not allow Vercel to connect. Do not silently open access to
0.0.0.0/0; that is a deliberate network exposure decision. Free-plan network access
must be resolved before declaring the deployment working.

From a trusted local terminal in backend/, temporarily configure the same Atlas
MONGO_URI and JWT_SECRET privately, then run:

```powershell
.\.venv\Scripts\python.exe scripts/create_user.py --email YOUR_EMAIL --role admin
```

Enter the new application password at the private prompts. Do not add a public
bootstrap endpoint or default administrator credentials. This script initializes
collections and indexes. Use a separate disposable database for tests.

## Important free-plan constraints

- Vercel limits function request/response payloads to 4.5 MB. The 4 MB application
  upload setting leaves room for multipart overhead; the old local 25 MB setting
  is not suitable here. Direct-to-storage uploads are needed to restore larger files.
- A Hobby invocation is limited to 300 seconds. The existing FastAPI BackgroundTasks
  model jobs are not durable workers; interruption or timeout can leave jobs needing
  recovery. Small-data limits reduce load but do not guarantee completion. A durable
  queue/worker adaptation is required before relying on unattended model processing.
- In-memory analytics caches are per instance; invalidation is not shared across
  scaled instances. Configure a shared Redis service before multi-user operation,
  or implement a no-cache mode. Do not assume WORKERS=1 prevents platform scaling.
- The daily in-process retention loop is not a durable serverless scheduler. Verify
  Mongo TTL indexes and use an authenticated scheduled task for retention sweeps.
- Python scientific dependencies may exceed the standard function bundle limit.
  Inspect the deployment build; do not enable a paid tier to bypass a failed build.
- Never upload real government or personal records while the deployment is unverified.

## Verification after deployment

1. Confirm both services build, and record the deployment URL and source commit.
2. Check /health/live and /health/ready; ready must reach Atlas successfully.
3. Open /login directly, sign in, refresh the page, and verify session renewal.
4. With synthetic data only, upload a small CSV, run a model, and verify completed
   results, investigation navigation and a saved review after a browser refresh.
5. Verify reviewer/analyst permission boundaries and administrator-only operations.
6. Inspect runtime logs for safe errors and check the free-plan usage dashboard.

A green frontend build does not verify Atlas connectivity or model execution.

References:
- https://vercel.com/docs/services/config-reference
- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/plans/hobby
