import tomllib
from pathlib import Path


def test_vercel_manifest_includes_pinned_runtime_dependencies():
    backend = Path(__file__).resolve().parents[1]
    manifest = tomllib.loads((backend / 'pyproject.toml').read_text(encoding='utf-8'))
    runtime_requirements = {
        line.strip()
        for line in (backend / 'requirements.in').read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    }
    assert set(manifest['project']['dependencies']) == runtime_requirements
    assert any(item.startswith('fastapi==') for item in runtime_requirements)
    assert manifest['tool']['vercel']['entrypoint'] == 'app.main:app'
