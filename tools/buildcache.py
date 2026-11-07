"""Rebuild only what changed.

Each unit of tools/registry.py is built once and its assets are kept in `.build-cache/` (not committed). The next run reuses them if nothing the unit depends on
has changed: its module and every tools module it imports (found by reading the imports, so a change to a shared helper rebuilds what uses it), the files in
tools/data, the files or folders the unit says it reads, and any module it loads by name. `--force` on make_assets.py ignores the cache.
"""
import ast
import hashlib
import importlib
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CACHE = TOOLS.parent / '.build-cache'
sys.path.insert(0, str(TOOLS))


def local_imports(module):
    path = TOOLS / f'{module}.py'
    if not path.exists():
        return set()
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
        found.update(n.split('.')[0] for n in names if (TOOLS / f'{n.split(".")[0]}.py').exists())
    return found


def closure(modules):
    seen, todo = set(), list(modules)
    while todo:
        m = todo.pop()
        if m not in seen:
            seen.add(m)
            todo.extend(local_imports(m))
    return sorted(seen)


def feed(h, path):
    path = Path(path)
    if path.is_dir():
        for p in sorted(path.rglob('*')):
            if p.is_file():
                feed(h, p)
    elif path.exists():
        h.update(str(path).encode())
        h.update(path.read_bytes())
    else:
        h.update(b'missing:' + str(path).encode())


def key_of(unit, weapons_dir=None):
    h = hashlib.sha256()
    for m in closure([unit.module, *unit.depends]):
        feed(h, TOOLS / f'{m}.py')
    feed(h, TOOLS / 'data')
    for p in unit.inputs:
        feed(h, p)
    if unit.takes_weapons_dir and weapons_dir:
        feed(h, weapons_dir)
    return h.hexdigest()


def build(unit, weapons_dir=None, force=False):
    """The unit's assets: from the cache if nothing changed (False for fresh), else built now. Returns (assets, from_cache)."""
    key = key_of(unit, weapons_dir)
    path = CACHE / 'units' / f'{unit.name}.json'
    if not force and path.exists() and all(Path(o).exists() for o in unit.outputs):
        saved = json.loads(path.read_text())
        if saved['key'] == key:
            return saved['assets'], True
    fn = getattr(importlib.import_module(unit.module), unit.func)
    assets = fn(weapons_dir) if unit.takes_weapons_dir and weapons_dir else fn()
    assets = json.loads(json.dumps(assets))           # what the cache would give back, so a cached run and a fresh run are the same
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'key': key, 'assets': assets}, separators=(',', ':')))
    return assets, False


_memo = {}


def assets_of(name):
    """The assets of one registry unit by name, from the cache when nothing changed (what the tests use, so a test run does not redraw what it did not touch)."""
    import registry
    if name not in _memo:
        _memo[name] = build(next(u for u in registry.UNITS if u.name == name))[0]
    return _memo[name]
