# Contributing

1. Create a branch from `main`.
2. Never commit `.env`, TLS material, credentials, production data, or exported personal data.
3. Install dev dependencies with `pip install -r backend/requirements-dev.txt` and `npm ci` in `frontend`.
4. Run `pre-commit install` once.
5. Before a pull request, run `make lint`, `make test`, and `make audit`.
6. Changes to authorization, dataset validation, model semantics, retention, or review decisions require tests and documentation.
7. Preserve the product principle **Unusual != Fraudulent** in UI, API, and documentation.

Pull requests must pass CI with zero lint errors, backend coverage >=85%, frontend coverage >=80%, dependency audits, secret scanning, E2E, and Docker builds.
