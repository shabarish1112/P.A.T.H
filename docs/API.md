# P.A.T.H. API

Investigation evidence is available for every active-dataset transaction, including records outside the saved Top-K alerts and before a model run. `analysis_status` is `selected`, `not_selected`, or `not_analyzed`. Saved alerts retain their original signals, scores, priority and rank. Other records receive on-demand payment comparisons calculated from the uploaded data using the existing feature definitions; their score, priority and rank remain null. Reading details does not train a model, add an alert, or record a review.

Transaction detail, anomaly results and analysis-summary records now include an additive `explanation` object from one shared deterministic module: `headline`, optional `support`, `check_first`, `amount_display`, `tags` and typed evidence `signals` (label, baseline/value text, multiple, strength and help). Existing raw fields are unchanged. Transaction detail also returns `total_transactions`, `review_actor_email`, `review_changed_at` and `review_note`. See [the investigation implementation report](INVESTIGATION_EXPLANATIONS.md) for calculation semantics and verification.

All endpoints except health, login, and refresh require `Authorization: Bearer <access-token>`. Access tokens expire after 15 minutes by default. Refresh is performed with a rotating HttpOnly cookie.

| Method | Endpoint | Roles | Purpose |
|---|---|---|---|
| GET | `/health`, `/health/live`, `/health/ready` | public | liveness/readiness |
| POST | `/api/auth/login` | public | OAuth2 password-form login |
| POST | `/api/auth/refresh` | public | rotate refresh token |
| POST | `/api/auth/logout` | authenticated | revoke current refresh token |
| GET | `/api/auth/me` | authenticated | validate session |
| GET/POST/PATCH | `/api/users` | admin | user management |
| GET | `/api/datasets` | analyst/reviewer/admin | dataset versions |
| POST | `/api/datasets/upload` | admin | stream/validate/activate CSV |
| DELETE | `/api/datasets/{id}` | admin | delete inactive dataset |
| GET | `/api/transactions` | analyst/reviewer/admin | cursor-paged transactions |
| GET | `/api/transactions/{id}` | analyst/reviewer/admin | transaction + anomaly + latest review |
| POST | `/api/models/run` | analyst/reviewer/admin | queue model background job |
| GET | `/api/models/jobs/{id}` | analyst/reviewer/admin | job status/progress |
| GET | `/api/anomalies` | analyst/reviewer/admin | active-run Top-K anomalies |
| GET | `/api/analytics/insights` | analyst/reviewer/admin | plain-language dataset/run narrative and up to five critical records |
| GET | `/api/analytics/summary` | analyst/reviewer/admin | real computed dashboard summary |
| GET | `/api/analytics/trend` | analyst/reviewer/admin | current/previous flagged trend |
| GET | `/api/analytics/breakdown` | analyst/reviewer/admin | grouped active anomalies |
| GET | `/api/reviews` | analyst/reviewer/admin | active-run validation events |
| PUT | `/api/reviews/{transaction_id}` | reviewer/admin | append human decision |
| GET | `/api/audit` | admin | audit events |

Standard error body:

```json
{"error":{"code":"HTTP_403","message":"Insufficient permissions","request_id":"..."}}
```

Common status codes: 401 unauthenticated, 403 role denied, 404 resource missing, 409 state conflict, 413 upload too large, 422 validation error, 429 login lockout.

## Session and password endpoints

| Endpoint | Role | Behavior |
|---|---|---|
| POST /api/auth/change-password | Any authenticated user | Current password required; new password 12-128 characters; invalidates sessions; sign in again |
| POST /api/users/{user_id}/reset-password | Admin | Resets another user; revokes sessions; forces change at next login |
| PATCH /api/users/{user_id} | Admin | Role/active changes revoke sessions; self-demotion and last-admin removal return 409 |

Auth user responses now include `must_change_password`. Reset users can access only
auth/me, auth/change-password and auth/logout until changed. Refresh replay returns
401, revokes sessions and writes an audit event. Upload row and model row bounds
return 413. Invalid request IDs are replaced with generated IDs.

OpenAPI defines OAuth2 password bearer security. Login uses form fields `username`
(email) and `password`; refresh uses the HttpOnly cookie, not a body token.

## Guided analysis

`GET /api/analytics/insights` returns `status` (`no_dataset`, `not_analyzed`, or `ready`), dataset/run identifiers, transaction/alert/critical counts, a narrative, and up to five ranked `critical_records`. Each record includes its ID, amount in paise, agency, vendor, score, and factual `signals` derived from stored features. Counts cover all returned alerts, not just the five displayed records. The response uses `Cache-Control: private, no-store`.

Critical priority means a score at or above the run's 99th percentile, including ties. Observed comparison features are context, not causal feature attribution or a legal finding. No external language-model API is called. Analysis, anomaly lists, transaction context, and review lists only attach an active run when it belongs to the active dataset; an upload awaiting a completed run is not described using previous-dataset results.

Reviews remain append-only events created by `PUT /api/reviews/{transaction_id}`. The UI preserves the existing statuses and permissions and displays actual events returned by `GET /api/reviews` for the active run. It does not create mock events or treat machine flags as human decisions.
