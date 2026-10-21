# P.A.T.H. Research Alignment

## Main purpose

P.A.T.H. is an **anomaly surveillance and prioritization layer**, not a fraud adjudication system. It consumes authorized public-finance data, ranks statistically unusual disbursals, provides contextual evidence, and sends bounded Top-K cases to human reviewers.

**Principle:** Unusual ≠ Fraudulent.

## Paper-to-prototype mapping

| Research concept | P.A.T.H. implementation |
|---|---|
| Isolation Forest baseline | `backend/app/ml/engine.py` using scikit-learn IsolationForest |
| Extended Isolation Forest comparison | `EIF-lite`: random hyperplane projection + IF; clearly labeled research approximation |
| Deep Isolation Forest comparison | `DIF-lite`: fixed random ReLU representation + IF; clearly labeled research approximation |
| Per-tree path length | `_path_lengths()` extracts estimator decision-path lengths |
| PCA | PCA on standardized path-length matrix |
| UMAP | Optional `umap-learn`; generated from same path-length matrix |
| Contextual features | Agency/scheme/vendor baselines, scheme utilization, vendor frequency, fiscal year end, reversals |
| Dynamic / operational alert threshold | Configurable Top-K alert budget |
| Human validation | Review statuses: Pending Review, Confirmed Finding, False Alert, Escalated |
| Operational evaluation | Precision@K, Recall@K, PR-AUC, investigation yield |
| Human-readable evidence | `PATH Insight` factor breakdown |
| Modular public-finance architecture | FastAPI analytical layer separate from authoritative source systems |

## References from the supplied paper

1. F. T. Liu, K. M. Ting, and Z.-H. Zhou — *Isolation Forest* (2008).
2. S. Hariri, M. C. Kind, and R. J. Brunner — *Extended Isolation Forest* (2021).
3. H. Xu, G. Pang, Y. Wang, and Y. Wang — *Deep Isolation Forest for Anomaly Detection* (2023).
4. W. Hilal, S. A. Gadsden, and J. Yawney — financial fraud anomaly detection review (2022).
5. E. Kehler, J. Paciello, and J. Pane — anomaly detection in public procurement using OCDS (2020).
6. I. T. Jolliffe — *Principal Component Analysis*.
7. L. McInnes et al. — UMAP (2018).
8. IMF — modular financial management information system guidance (2019).
9. IMF — digital solutions guidelines for public financial management (2023).
10. V. Gopalakrishnan — SilIF preprint (2026), treated as emerging evidence.
11. National Informatics Centre — Public Financial Management System (PFMS), India.

## Important academic honesty note

The supplied paper presents a proposed research framework and explicitly says completed empirical results, final dataset details, anomaly counts, and validated performance metrics are not yet established. The prototype therefore ships with synthetic demo data and does not claim production-grade fraud detection performance.
