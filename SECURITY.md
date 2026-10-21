# Security Policy

Do not open public issues for suspected vulnerabilities that could expose credentials, personal data, authorization bypasses, injection flaws, or cryptographic weaknesses.

Report privately to the security contact designated by the organization operating this deployment. Include affected version, reproduction steps, impact, and whether production data was accessed. Operators should acknowledge reports promptly and follow their own incident-response and legal notification obligations.

P.A.T.H. ships no default credentials. Rotate JWT signing keys, Mongo credentials, TLS keys, and any external secrets after suspected compromise. Revoke refresh tokens for affected users and preserve audit logs for investigation.
# Reporting contact and timeline template

**PLACEHOLDER - deployment owner must replace before production:**
`<REAL_SECURITY_REPORTING_CONTACT>` (monitored security email or private advisory URL).
Do not use a public issue to disclose credentials or exploitable details.

Expected response targets (confirm with the operator): acknowledge within 2 business
days, provide initial triage within 5 business days, and agree on a severity-based
remediation/disclosure timeline. These are a template, not an established SLA.
