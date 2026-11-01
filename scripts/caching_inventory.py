"""Read-only caching baseline; run from repo root: python3 scripts/caching_inventory.py."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    operations = []
    for path in sorted((ROOT / 'backend/app').rglob('*.py')):
        tree = ast.parse(path.read_text())
        prefix = ''
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'APIRouter':
                prefix = next((ast.literal_eval(k.value) for k in node.keywords if k.arg == 'prefix'), '')
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in {'get', 'post', 'patch', 'put', 'delete'}:
                    operations.append({'method': decorator.func.attr.upper(), 'path': prefix + ast.literal_eval(decorator.args[0]), 'source': str(path.relative_to(ROOT)), 'handler': node.name})
    assets = {}
    for name in ['uis/backoffice/operational-incidents/app.js', 'uis/backoffice/operational-incidents/select-field.js', 'frontend/app/page.js']:
        data = (ROOT / name).read_bytes()
        assets[name] = {'source_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    return {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'method': 'Static inventory, source bytes only; not transferred/compressed bytes or timings', 'operations': operations, 'assets': assets}


if __name__ == '__main__':
    print(json.dumps(inventory(), indent=2))
