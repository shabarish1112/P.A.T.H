# Deployment security

## Trusted proxies and login throttling

The backend starts through `python -m app.run`. `HOST`, `WORKERS` and
`FORWARDED_ALLOW_IPS` configure Uvicorn. Local defaults bind loopback and trust only
loopback proxies. The production private network assigns Caddy `172.30.0.10`; only
that address is trusted by the backend. If this subnet conflicts with your network,
change both the network address and trusted-proxy list together. Never expose a
backend that trusts `*`, and never use forwarded headers directly in application
code. The edge must overwrite forwarded client addresses rather than trust a
client-supplied chain. Caddy's default reverse proxy does this.

Login throttles use the effective transport client IP plus normalized email, and a
second per-IP counter spans emails. After five failures the account/IP pair backs
off exponentially (30 seconds up to 15 minutes); twenty failures across emails
trigger the per-IP backoff. Counters expire. To recover a locked administrator,
wait for backoff or have an authorized database operator clear only that user's
specific login counter after identity verification; never disable authentication.

## Database permissions and migration

`infra/mongo-init/app-user.js` creates a collection-scoped custom role. Audit events
allow only `insert`, `find` and `listIndexes`. Runtime credentials cannot update,
delete or drop audit history, or change audit indexes. The privileged bootstrap
creates audit validators and TTL indexes. The Mongo TTL monitor can still expire
events; the application needs no delete privilege for it. Other collections allow
only the actions the application uses, not database-wide `readWrite`.

On an existing volume, back up first, connect interactively as a DB administrator
and load `/docker-entrypoint-initdb.d/app-user.js`. Remove the old database-wide
role by using this script's `updateUser` migration before restarting APIs. Do not
delete production volumes to migrate permissions. `infra/verify-audit-role.js`
checks insert/read and mutation boundaries inside the Mongo service after bootstrap.

The official pinned Mongo image uses a loopback-only initialization daemon with
`allowTLS` when certificates are configured, then restarts the final daemon with
`requireTLS`. Initialization scripts therefore use that private initialization
connection. Existing-volume administrative maintenance must explicitly pass TLS
CA/client certificate options; never turn off final-daemon TLS to run migration.
This image/TLS startup path still requires a Docker integration check.

## Redis, sessions and operational limits

Redis has no published port and runs only on the private network. Set a unique
password in `infra/redis.env`, and put the matching authenticated `REDIS_URL` in
`backend/.env`; URL-encode credentials. Multiple API workers must use Redis.

Refresh-token consumption is atomic. Reuse invalidates the user's sessions and
adds a security audit event. Role changes, deactivation and password changes
invalidate access-token versions and revoke refresh sessions. Password reset is
admin-only and requires a password change before further application access.
Administrators cannot deactivate/demote themselves or remove the last active admin.

Model jobs use renewable, owner-fenced leases. Workers heartbeat both the lease
and job timestamp; stale jobs are failed at startup. Set `MODEL_LOCK_SECONDS` above
normal scheduling delays. Uploads stage rows in batches and activate last, rolling
back on failure. `MAX_ROWS`, `MAX_UPLOAD_MB` and `ML_MAX_ROWS` bound resource use.
Uploads beyond model limits can be stored but cannot start an oversized model run.
Retention runs at startup and daily under a database lease and logs deletion counts.

## Release gates

Release calls reusable CI first. Images are built locally, scanned by a digest-pinned
Trivy image with HIGH/CRITICAL failures blocking publication, and get CycloneDX
SBOMs retained as release workflow artifacts. Only then are images pushed. There
are no vulnerability exceptions and no image-signing claim; keyless cosign signing
is not configured. Production owners must verify image/TLS/E2E gates before deploying.

## HTTPS edge

`docker-compose.prod.yml` exposes only Caddy on ports 80/443. Caddy redirects HTTP to HTTPS automatically for a valid `DOMAIN`, obtains/renews certificates, and adds HSTS. Backend and Mongo remain on a private Docker network.

## Mongo transport encryption

Production Mongo starts with `--tlsMode requireTLS`. Place these operator-generated files under `secrets/tls/` (never commit them):

- `ca.pem` — internal CA public certificate
- `mongo.pem` — Mongo server certificate + private key, SAN covering `mongo`
- `app.pem` — client certificate + private key if mutual TLS is required by your deployment

The backend uses `MONGO_TLS_CA_FILE=/run/tls/ca.pem` and `MONGO_TLS_CERT_KEY_FILE=/run/tls/app.pem`.

## At-rest encryption

Choose one production control and document it in your deployment record:

1. MongoDB Atlas encryption at rest with a customer-managed KMS key; or
2. MongoDB Enterprise encrypted storage engine; or
3. self-managed Mongo data volume on LUKS/dm-crypt or cloud block storage encrypted with KMS (for example EBS KMS), with snapshots encrypted under the same or stronger policy.

Do not claim application-level encryption substitutes for encrypted storage. Backups and replicas require equivalent controls.

## Field-level encryption guidance

Vendor identifiers may identify natural persons in some datasets. If an operator must store sensitive identifiers, prefer MongoDB Client-Side Field Level Encryption / Queryable Encryption with a KMS-managed data-encryption key. Keep `search_key` free of raw sensitive identifiers when this mode is enabled; use an approved deterministic tokenization/search strategy instead.

## Production docs

Swagger and OpenAPI routes are disabled automatically when `ENVIRONMENT=production`, independent of `DOCS_ENABLED`.
