# Privacy and compliance engineering note

This document maps engineering controls to privacy obligations and risks; it is **not legal advice**. Deployment owners must obtain legal review for their exact data source, governmental mandate, role allocation, notices, retention periods, cross-border processing, breach process, and Data Fiduciary status.

## Data inventory

P.A.T.H. can process transaction IDs, dates, agencies, schemes, vendor/beneficiary labels, districts, monetary values, model scores, contextual features, review notes, user identities, IPs/user agents in refresh-token/login-security records, and administrative audit events.

A vendor or beneficiary name can be personal data when it identifies an individual or sole proprietor. Operators should prefer organization/vendor IDs and minimize free-text personal identifiers.

## Purpose limitation and minimization

The configured purpose is anomaly **screening and audit prioritization**. Do not reuse the dataset for unrelated profiling. The CSV whitelist drops unknown columns, reducing accidental collection. Review notes should not contain unnecessary personal data.

## Access and accountability

RBAC separates analyst, reviewer, and admin privileges. Dataset mutation, user administration, and audit-log access are admin-only. Review actions store the real actor ID/email and request ID. Refresh tokens are hashed and revocable.

## Retention and deletion

- Inactive dataset versions: `DATA_RETENTION_DAYS` (default 365) and never the active version during automatic startup retention cleanup.
- Audit events: `AUDIT_RETENTION_DAYS` via Mongo TTL.
- Refresh tokens and login counters: TTL indexes based on expiry.

Organizations should shorten/extend these only after documented legal/operational review.

## Security safeguards

TLS is terminated by Caddy externally, production Mongo requires TLS internally, credentials are environment-only, passwords use Argon2, JWT access tokens are short lived, rotating refresh tokens are stored hashed, upload sizes are bounded, and security headers/CORS are restrictive.

## DPDP Act / Rules mapping for legal review

India's Digital Personal Data Protection Act, 2023 and the **Digital Personal Data Protection Rules, 2025** form the current framework. MeitY notified the final Rules in November 2025 with phased commencement. Engineering teams should map deployment specifics to the following themes with counsel:

- lawful purpose / lawful basis and any State-processing provisions;
- notice and transparency where applicable;
- reasonable security safeguards;
- personal-data breach processes and notification timing;
- Data Principal rights handling where applicable;
- processor/vendor contracts and access controls;
- retention/erasure once purpose and legal retention needs end;
- special obligations if designated a Significant Data Fiduciary;
- cross-border transfer restrictions if notified.

Official source: Ministry of Electronics and Information Technology, Digital Personal Data Protection Rules, 2025 and enforcement timeline (MeitY, notified November 2025).

Items requiring explicit legal review before production: exact lawful basis, whether vendor identifiers are personal data in the source system, notice exemptions, retention periods, breach reporting workflow, cross-border hosting, and whether a public authority exemption applies.
