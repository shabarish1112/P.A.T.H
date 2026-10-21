# Third-party license inventory

Full transitive inventories, including development dependencies:

- [Python](docs/licenses/python.json), generated with pip-licenses.
- [npm](docs/licenses/npm.json), generated with license-checker.

Run `python scripts/check_licenses.py` to reject unapproved GPL/AGPL entries.
The version-specific allowlist is `docs/licenses/allowlist.json` and is currently
empty. Inventory review is required before release; this is not legal advice.

Regenerate from the locked environment with `pip-licenses --format=json --with-urls
--output-file=docs/licenses/python.json` and `cd frontend && npx license-checker
--json > ../docs/licenses/npm.json`. Remove local filesystem paths from the npm
report before committing.
