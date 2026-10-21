# P.A.T.H. model card

## Intended use

P.A.T.H. ranks unusual public-fund disbursals for human audit triage. It is not a fraud classifier and must not be used as an automated legal, disciplinary, eligibility, payment-blocking, or accounting decision-maker.

## Models

- **IF**: scikit-learn Isolation Forest baseline.
- **EIF-lite**: random normalized hyperplane projection followed by Isolation Forest. It approximates the motivation of Extended Isolation Forest but is **not** the Hariri et al. algorithm implementation.
- **DIF-lite**: randomized ReLU representation followed by Isolation Forest. It approximates representation enrichment but is **not** Xu et al.'s Deep Isolation Forest implementation.

The UI and API retain these `-lite` limitations in documentation even though stable API identifiers are `eif` and `dif` for compatibility.

## Scores and labels

Higher screening score means more isolated relative to the supplied population. Percentile labels are population-relative: top 1% Critical, next 4% High, next 10% Medium, next 20% Low, remainder Normal. Top-K separately limits investigator workload.

## Explainability

`PATH Insight` exposes contextual ratios and activity measures such as amount-vs-agency/vendor/scheme baselines, vendor 30-day frequency, utilization, and payment gap. These are explanatory features, not causal proof.

## Limitations

- Unsupervised scores depend on data quality, feature engineering, peer composition, seasonality, and model parameters.
- Genuine emergency, year-end, policy-change, or large legitimate purchases can rank highly.
- Ground-truth fraud labels are usually incomplete; PR-AUC/Precision@K/Recall@K are only calculated when an explicit evaluation label is present.
- Dimensionality reduction is visualization support, not evidence of wrongdoing.
- Human due process and authoritative source records remain necessary.
