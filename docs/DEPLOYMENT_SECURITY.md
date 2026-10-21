# Deployment security

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
