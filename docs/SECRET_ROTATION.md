# Secret rotation

A previously shared project archive must be treated as compromised. Rotate every
credential that was included in it or shared separately. Deleting files does not
revoke credentials. Never put real values in source control, issue reports or logs.

1. Stop application traffic and take an encrypted database backup outside the
   checkout. Inventory all deployments and secret stores; do not print their values.
2. Generate a new cryptographically random JWT signing secret of at least 32 bytes.
   Update `JWT_SECRET` in each backend secret store and restart all API workers
   together. All existing access tokens become invalid. Delete/revoke all stored
   refresh sessions as well so they cannot issue tokens signed with the new key.
   All users must sign in again. Never retain the exposed signing key as a fallback.
3. Connect to MongoDB over TLS as an authorized administrator. Use `passwordPrompt()`
   with `db.changeUserPassword` to rotate the root password; do not pass passwords
   on the shell command line. Update only `infra/mongo.env` or its secret store.
   Mongo initialization environment changes do not modify an existing database user.
4. Rotate the application database user's password the same way in the `path`
   database. Update `PATH_APP_PASSWORD` in the Mongo secret store and the
   URL-encoded password in backend `MONGO_URI`. Restart APIs and verify readiness.
   The backend must never receive the root account's credentials.
5. Rotate Redis's password in its secret store and backend `REDIS_URL` together;
   restart Redis and API workers. Keep Redis off public networks.
6. Change the local administrator password using the authenticated change-password
   endpoint or an administrator reset. Revoke sessions and remove any saved local
   login files. Provision fresh development users; never reuse published passwords.
7. Generate new TLS private keys and certificates through your certificate issuer.
   Revoke exposed certificates where supported; deploy renewed server/client
   certificates and CA trust in a staged overlap, then remove obsolete trust.
   Restart MongoDB, API clients and the edge proxy; verify certificate validation.
8. Verify login, logout, refresh, database readiness, role boundaries and TLS from
   every deployment. Review audit events for unexpected activity and retain an
   incident record containing identifiers and timestamps, never secret values.

Do not restore secrets from an old archive or add them to Git history. Fresh
environment files must be created outside distributable artifacts and excluded by
both Git and Docker build contexts.
