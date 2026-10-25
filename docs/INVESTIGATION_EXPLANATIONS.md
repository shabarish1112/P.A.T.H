# Plain-language investigation update

## Result

Summary records, transaction details and alert API responses use one deterministic Python explanation module. The frontend renders its output. Raw API fields remain compatible. No model, scoring, ranking, training, CSV or dependency changes were introduced. No LLM is used.

Analysis Summary remains below the original dashboard elements. Investigation now includes an explanation and first check, comparison evidence, strength labels, bars, expandable keyboard-accessible help, date-only formatting, financial year, review order, secondary score detail and persistent review controls. Existing server permissions and separation-of-duties rules are preserved.

## Findings, assumptions and decisions

- **Conflicting example:** strongest-first takes priority, following the user's clarification. TX-002562 leads with the 12x agency/scheme comparison, supports it with the 7.7x vendor comparison and recommends checking the sanction and approval.
- **Baselines:** feature engineering computes full-dataset vendor/agency/scheme means, including this payment. These are not earlier-invoices-only averages. Runs retain rounded ratios, not original means. Summary and transaction detail recompute the same means from the active uploaded dataset. When a mean is not supplied, the shared module derives amount/ratio and explicitly marks it approximate. Zero/missing/non-finite ratios never cause division by zero.
- **Equal ratios:** the supplied 4,000-row CSV has exactly one scheme per agency: Education/School Upgrade, Health/Primary Health, Public Works/Road Renewal, Rural Development/Rural Works, Water Resources/Water Supply. Agency and scheme groups contain the same records, so their averages match. This is a dataset property, not a calculation bug. Equal stored ratios are merged; different real baselines remain identified within that row.
- **365 sentinel:** `app/ml/features.py` assigns 365 when no earlier vendor payment exists. A real gap can also equal 365. History sorted by date and insertion order distinguishes them, matching feature engineering's stable ordering. Display says “First payment on record” only when verified, “365 days (about 1 year)” for a real gap, and “Earlier payment history unavailable” when unknown. Stored values remain unchanged. The live TX-002562 record was confirmed as its vendor's first payment in this upload.
- **Scheme utilization:** cumulative scheme payments through this record in its financial year divided by the largest supplied sanctioned amount for that scheme/year. It is not an independently verified scheme budget. The fixture's 0.0632 displays as 6.3%.
- **Critical:** the existing top-score quantile, including ties; not a confirmed finding. Its definition and the disclaimer appear once per report; investigation exposes the Critical definition through keyboard-accessible badge help.
- **Counts:** the 30-day window includes this payment. Below three payments, evidence remains visible as Normal but narrative omits the frequency. Counts are not claimed to be unusually frequent without a comparison baseline.
- **Presentation strengths:** named constants use 2x, 5x and 10x. These do not change model priorities. Decimal half-up rounding uses one decimal under 10 and whole multiples from 10. Amounts use lakh/crore in explanations and Indian currency formatting in context.
- **Length:** full names remain in the header/context. For extremely long names, the headline refers to “This payment” rather than truncating names. Supporting text is omitted when necessary to remain below 60 words.
- **Review actions:** “Confirm for investigation” maps to existing `Confirmed Finding`; “Mark as explained” to `False Alert`; “Escalate” to `Escalated`. Notes, latest reviewer and timestamps use existing persisted review records.
- **Dates:** formatting preserves the supplied calendar date; audit timestamps still show actual date/time.

## Files created/changed for this update

| File | Change |
| --- | --- |
| `backend/app/schemas/explanations.py` | New typed narrative and evidence contracts. |
| `backend/app/services/payment_explanation.py` | New shared wording, thresholds, rounding and evidence rules. |
| `backend/app/services/insight_service.py` | Replaces separate summary wording with the common explanation. |
| `backend/app/services/transaction_service.py` | Adds shared explanation, count and latest review metadata. |
| `backend/app/services/anomaly_service.py` | Adds the shared explanation to alert responses. |
| `backend/app/repositories/transactions.py` | Reads real comparison means and verifies first-payment history. |
| `backend/app/schemas/analytics.py` | Adds explanation/priority; preserves legacy fields. |
| `backend/app/schemas/anomalies.py` | Adds structured explanation. |
| `backend/app/schemas/transactions.py` | Adds explanation, count and review metadata. |
| `backend/tests/test_payment_explanation.py` | Rounding, amounts, thresholds, nulls, plurals, ordering, sentinel, long names and prohibited-word tests. |
| `backend/tests/test_insights.py` | Summary/detail consistency and persisted review metadata checks. |
| `frontend/src/components/PaymentExplanation.jsx` | Shared narrative, evidence rows and report notice. |
| `frontend/src/components/AnalysisSummary.jsx` | Compact identity/priority row and shared narrative. |
| `frontend/src/pages/Investigation.jsx` | Accessible explanation/evidence and clearer saved-review workflow. |
| `frontend/src/lib.js` | Date-only formatter without timezone shifts. |
| `frontend/src/index.css` | Scoped evidence/help styles using existing theme tokens. |
| `frontend/tests/fixtures/investigation.json` | TX-002562 fixture produced by the shared Python module. |
| `frontend/tests/PaymentExplanation.test.jsx` | Evidence, units, missing explanation and date checks. |
| `frontend/tests/AppFlows.test.jsx` | Review action persistence and last-change display test. |
| `docs/openapi.json` | Regenerated additive API contracts. |
| `docs/API.md` | Documents the common explanation response. |
| `docs/INVESTIGATION_EXPLANATIONS.md` | This report. |

## Commands and results

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m ruff format --check app tests
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/export_openapi.py
```

Lint/format passed; mypy checked 66 source files. Full suite: 79 tests passed, 90.11% coverage. After one final long-name guard, all 21 explanation tests passed.

From `frontend`:

```powershell
npm run lint
npx vitest run --coverage --maxWorkers=1
npm run build
```

Lint, production build and targeted Prettier checks passed. All 26 tests passed; line coverage 93.42%, branch coverage 80.86%. This JavaScript frontend has no separate TypeScript type-check command.

From project root:

```powershell
node .local/investigation-check.cjs
git diff --check
```

Edge checks opened `/investigation/TX-002562` on Vite port 5173 at 1440, 1024 and 390 widths, both themes. Passed: summary parity/link, date, first-payment text, singular count, 6.3% unit, keyboard help, no blank buttons, no page overflow, non-Critical/unscored records, review save/reload and no console/page errors. Browser mutations used isolated API fixtures; live reviews were untouched. Screenshots are in `.local/investigation-check/`.

A read-only check of the actual uploaded TX-002562 independently confirmed the 12x/7.7x comparisons and first-payment status. The idle backend was restarted and its new schema/readiness verified.

## Limits and remaining decisions

No required user decision remains. The optional scheme-payment plot was omitted. Browser persistence used isolated fixtures; backend integration tests verified real repository persistence and permissions without changing live user review records. No deployment was performed. Refresh the browser to use the updated local app.
