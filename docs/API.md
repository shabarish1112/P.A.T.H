# P.A.T.H. API

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
