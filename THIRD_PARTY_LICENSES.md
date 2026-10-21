# Third-party license inventory

P.A.T.H. uses the MIT license because it is short, permissive, and compatible with the permissive licenses used by the direct runtime dependencies below. This inventory covers direct dependencies; CI should regenerate/verify the full transitive inventory before each release using `pip-licenses` and the npm lockfile.

## Python runtime

| Package | License family |
|---|---|
| FastAPI | MIT |
| Uvicorn | BSD-3-Clause |
| PyMongo | Apache-2.0 |
| Pydantic / pydantic-settings | MIT |
| PyJWT | MIT |
| argon2-cffi | MIT |
| NumPy | BSD-3-Clause |
| SciPy | BSD-3-Clause |
| scikit-learn | BSD-3-Clause |
| redis-py | MIT |
| python-json-logger | BSD-2-Clause |
| umap-learn | BSD-3-Clause |

## Frontend/runtime and tooling

| Package | License family |
|---|---|
| React / React DOM | MIT |
| React Router | MIT |
| Vite / Vitest | MIT |
| Tailwind CSS | MIT |
| ESLint and plugins | MIT |
| Prettier | MIT |
| Testing Library | MIT |
| MSW | MIT |
| Playwright | Apache-2.0 |

No direct dependency listed above introduces GPL/AGPL reciprocal terms. This is a software inventory, not legal advice; release owners must review the generated transitive report and organizational policy.

Generation commands:

```bash
pip-licenses --format=markdown --with-urls --with-license-file --no-license-path
npm query ':root > *' --json
```
