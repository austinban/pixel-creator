#!/usr/bin/env python3
"""Writes the terrain sets from tools/sets.py and assets/data.js, three ways:

    assets/sets.js                     window.SETS = {...}, for terrain.html (the random terrain builder reads it)
    sprites/assets/sets/sets.json      the same, for the game
    SETS.md                            the sets and what can be swapped for what, as a table for people

Run it after `tools/make_assets.py`, since it checks every piece named in a set against assets/data.js. `--check` says whether the files on disk are up to date and writes nothing.

    python3 tools/make_sets.py
    python3 tools/make_sets.py --check
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sets as S  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FORMAT = 1
SCATTER_ROLES = ('scatter', 'cover', 'decor', 'hazard')          # what the `scatter` layer may hold
FEATURE_ROLES = ('platform', 'blocker')


def load_data():
    text = (ROOT / 'assets' / 'data.js').read_text()
    return {a['id']: a for a in json.loads(text[text.index('{'):text.rindex('}') + 1])['assets']}


def sheet_id(ground, cell):
    return f"{S.GROUNDS[ground]['sheet']}-{cell[0]}-{cell[1]}"


def problems(data):
    """Everything wrong with the definitions, as a list of strings (empty means fine)."""
    bad = []
    for gid, g in S.GROUPS.items():
        if g['role'] not in S.ROLES:
            bad.append(f'group {gid}: unknown role {g["role"]}')
        if g['fits'] not in ('any', *S.GROUNDS):
            bad.append(f'group {gid}: fits {g["fits"]}')
        if not g.get('pending') and not S.resolve(gid, data):
            bad.append(f'group {gid}: matches no asset in data.js')
        for i in g.get('ids', []):
            if i not in data and not g.get('pending'):
                bad.append(f'group {gid}: {i} is not an asset')
    for a, b in S.TWINS:
        ga, gb = S.GROUPS[a], S.GROUPS[b]
        if ga['role'] != gb['role'] and not (ga['role'] in SCATTER_ROLES and gb['role'] in SCATTER_ROLES):
            bad.append(f'twins {a} and {b} have different roles')
    layer_roles = {'scatter': SCATTER_ROLES, 'features': FEATURE_ROLES, 'water': FEATURE_ROLES}
    for sid, s in S.SETS.items():
        ground = s['ground']
        if ground not in S.GROUNDS:
            bad.append(f'set {sid}: unknown ground {ground}')
            continue
        for cell, w in s['grass']:
            if sheet_id(ground, cell) not in data:
                bad.append(f'set {sid}: grass {sheet_id(ground, cell)} is not an asset')

        def check(layer, gid, roles):
            if gid not in S.GROUPS:
                bad.append(f'set {sid}: unknown group {gid}')
                return
            if S.GROUPS[gid]['role'] not in roles:
                bad.append(f'set {sid}: {gid} is a {S.GROUPS[gid]["role"]}, not for {layer}')
            if not S.fits(gid, ground):
                bad.append(f'set {sid}: {gid} does not fit {ground} ground')
        for layer, roles in layer_roles.items():
            for gid in s.get(layer, {}).get('groups', {}):
                check(layer, gid, roles)
                if layer == 'water' and S.GROUPS[gid].get('on') != 'water':
                    bad.append(f'set {sid}: {gid} is in the water layer but is not placed on water')
                if layer != 'water' and S.GROUPS[gid].get('on') == 'water':
                    bad.append(f'set {sid}: {gid} belongs in the water layer')
        for d in s.get('decals', []):
            check('decals', d['group'], ('decor',))
            if d['on'] not in ('land', 'water', 'shore'):
                bad.append(f'set {sid}: decal {d["group"]} on {d["on"]}')
            if S.GROUPS[d['group']].get('on', 'land') != d['on']:
                bad.append(f'set {sid}: decal {d["group"]} is made for {S.GROUPS[d["group"]].get("on", "land")}, not {d["on"]}')
        for gid in s.get('connectors', []):
            check('connectors', gid, ('connector',))
        for gid in s.get('weather', {}).get('groups', {}):
            check('weather', gid, ('overlay',))
        for gid in s.get('structures', []):
            check('structures', gid, ('structure', 'platform'))
        if s.get('bridge'):
            check('bridge', s['bridge'], ('crossing',))
    return bad


def document(data):
    groups = {gid: dict(label=g['label'], role=g['role'], fits=g['fits'], style=g['style'], note=g.get('note', ''), ids=S.resolve(gid, data), **{k: g[k] for k in ('on', 'flat', 'joins') if k in g},
                        twin=next((b if a == gid else a for a, b in S.TWINS if gid in (a, b)), None)) for gid, g in S.GROUPS.items()}
    sets = {}
    for sid, s in S.SETS.items():
        layer = lambda k: dict(groups=[dict(group=g, weight=w) for g, w in s[k]['groups'].items()])
        sets[sid] = dict(
            label=s['label'], ground=s['ground'], time=s['time'], blurb=s['blurb'], lake=s['lake'], level=s['level'], bridge=s['bridge'],
            grass=[dict(id=sheet_id(s['ground'], c), cell=list(c), weight=w) for c, w in s['grass']],
            scatter=dict(density=s['scatter']['density'], **layer('scatter')),
            features=dict(per100=s['features']['per100'], **layer('features')),
            water=dict(per100=s['water']['per100'], **layer('water')) if s.get('water') else None,
            decals=[dict(d) for d in s.get('decals', [])],
            connectors=list(s.get('connectors', [])),
            structures=list(s.get('structures', [])),
            weather=dict(chance=s['weather']['chance'], **layer('weather')) if s.get('weather') else None)
    return {'format': FORMAT, 'about': 'Terrain sets. See SETS.md and HOW-IT-WORKS.md. Generated by tools/make_sets.py from tools/sets.py; do not edit.',
            'grounds': {k: dict(v) for k, v in S.GROUNDS.items()}, 'roles': S.ROLES, 'groups': groups, 'sets': sets}


def markdown(doc):
    lines = ['# Terrain sets', '',
             'Generated by `tools/make_sets.py` from `tools/sets.py`; do not edit by hand. How it all fits together is in [HOW-IT-WORKS.md](HOW-IT-WORKS.md).', '',
             'A **set** is a look for a whole map: one **ground** (plain or corrupted, the two ground sheets that share a layout cell for cell), a mix of surfaces, and weighted **groups** of pieces for each job.',
             'Every piece in a set fits its ground, and pieces that share a style stay cohesive: blocky beside blocky, natural beside natural.', '',
             '## The sets', '', '| Set | Ground | Time | Lake | What it is |', '|---|---|---|---|---|']
    for sid, s in doc['sets'].items():
        lake = ['none', 'pond', 'lake', 'big lake'][s['lake']] + ('' if not s['lake'] else f", {s['level']}")
        lines.append(f"| **{s['label']}** (`{sid}`) | {s['ground']} | {s['time']} | {lake} | {s['blurb']} |")
    lines += ['', '## What each set is made of', '']
    for sid, s in doc['sets'].items():
        lines.append(f"### {s['label']} (`{sid}`, {s['ground']} ground)")
        lines.append('')
        lines.append('| Job | Groups (weight) |')
        lines.append('|---|---|')
        lines.append('| Scatter (density %d%%) | %s |' % (round(100 * s['scatter']['density']), ', '.join(f"{doc['groups'][g['group']]['label']} ({g['weight']})" for g in s['scatter']['groups'])))
        lines.append('| Features (%s per 100 cells) | %s |' % (s['features']['per100'], ', '.join(f"{doc['groups'][g['group']]['label']} ({g['weight']})" for g in s['features']['groups'])))
        lab = lambda gs: ', '.join(f"{doc['groups'][g['group']]['label']} ({g['weight']})" for g in gs)
        if s['water']:
            lines.append('| In the water (%s per 100 water cells) | %s |' % (s['water']['per100'], lab(s['water']['groups'])))
        if s['decals']:
            lines.append('| Decals | ' + ', '.join(f"{doc['groups'][d['group']]['label']} (on {d['on']}, {d['per100']} per 100)" for d in s['decals']) + ' |')
        if s['bridge']:
            lines.append(f"| Crossing | {doc['groups'][s['bridge']]['label']} |")
        if s['connectors']:
            lines.append('| Stairs and ramps | ' + ', '.join(doc['groups'][g]['label'] for g in s['connectors']) + ' |')
        if s['structures']:
            lines.append('| Structures | ' + ', '.join(doc['groups'][g]['label'] for g in s['structures']) + ' |')
        if s['weather']:
            lines.append('| Weather (%d%% of maps) | %s |' % (round(100 * s['weather']['chance']), lab(s['weather']['groups'])))
        lines.append('')
    lines += ['## The groups', '', '| Group | Role | Fits | Style | Pieces | Used by | Note |', '|---|---|---|---|---|---|---|']
    for gid, g in doc['groups'].items():
        def groups_of(s):
            out = {x['group'] for x in s['scatter']['groups']} | {x['group'] for x in s['features']['groups']} | set(s['structures']) | set(s['connectors']) | {s['bridge']}
            if s['water']:
                out |= {x['group'] for x in s['water']['groups']}
            out |= {d['group'] for d in s['decals']}
            if s['weather']:
                out |= {x['group'] for x in s['weather']['groups']}
            return out
        used = [sid for sid, s in doc['sets'].items() if gid in groups_of(s)]
        lines.append(f"| `{gid}` {g['label']} | {g['role']} | {g['fits']} | {g['style']} | {len(g['ids'])} | {', '.join(used) or '-'} | {g['note']} |")
    lines += ['', '## What swaps for what', '',
              '**Twins** are two looks of the same job with the same footprints: swap one for the other in any map and every rule still holds.', '']
    seen = set()
    for gid, g in doc['groups'].items():
        if g['twin'] and (g['twin'], gid) not in seen:
            seen.add((gid, g['twin']))
            t = doc['groups'][g['twin']]
            lines.append(f"- `{gid}` ({g['style']}) and `{g['twin']}` ({t['style']}): {g['role']}; fits {g['fits']} and {t['fits']}.")
    lines += ['', '**Fits `any`** means the piece is drawn on either ground without a variant: ' + ', '.join(f"`{gid}`" for gid, g in doc['groups'].items() if g['fits'] == 'any') + '.',
              '', '**Fits one ground only:** ' + ', '.join(f"`{gid}` ({g['fits']})" for gid, g in doc['groups'].items() if g['fits'] != 'any') + '. Do not put these in a set on the other ground.', '',
              '## Making a new set', '',
              '1. Pick a ground and say what the place is. Take groups that **fit** it, and keep to one or two styles so it feels like one place.',
              '2. Add it to `SETS` in `tools/sets.py` with weights, a density, how many features per 100 cells, and a default lake and bridge.',
              '3. Run `python3 tools/make_assets.py --png-dir sprites/assets` then `python3 tools/make_sets.py`; the tests check every group exists and fits.',
              '4. Open `terrain.html`, pick the set in the menu and press **New map** a few times. If it looks like a mix of two places, cut a style.', '']
    return '\n'.join(lines)


def game_readme(doc):
    names = ', '.join(f"`{sid}`" for sid in doc['sets'])
    return f'''# Terrain sets, for the game's map generator

`sets.json` (beside this file) says **which pieces belong together**, so a generated map feels like one place instead of a random mix. It is optional: nothing else in `sprites/assets/` depends on it, and nothing the game reads today has changed. It is made by `tools/make_sets.py` from `tools/sets.py`; do not edit it. The same data, as tables for people, is in `SETS.md` at the repo's root, and `HOW-IT-WORKS.md` explains the whole project.

## What is in it

```
format       1; bumped if a key is renamed or the layout changes
grounds      plain and corrupted: the ground sheet name (`ground`, `ground-corrupted`)
roles        what each kind of piece does on a map (scatter, platform, blocker, crossing, cover, structure, decor, hazard)
groups       a group of pieces that are one kind of thing: {{label, role, fits, style, ids, twin, note}}
sets         the looks: {names}
```

A **group**'s `ids` are asset ids from `assets/data.js` (a prefix group lists every match, so a new rock is picked up with no change here). Its `fits` is `plain`, `corrupted` or `any`; its `style` (`natural`, `blocky`, `timber`, `fungal`...) is what keeps a set cohesive; its `twin` is the group that is the same job in another look.

A **set** is: `ground` (which sheet), `time` (a time of day that suits it), `blurb`, `grass` (cells with weights; `id` is the full asset id on that sheet), `lake` (0 none, 1 pond, 2 lake, 3 big), `level` (`sunken` or `flush` water), `bridge` (a group id or null), and these layers:

| Layer | What | How to use it |
|---|---|---|
| `scatter` | one-cell pieces on land: `density` 0 to 1 of cells, weighted groups | per land cell off the shore, roll the density, pick a group by weight, then a piece |
| `features` | multi-cell pieces on land: `per100` per 100 cells | place each where **every cell of its `footprint.cells`** is clear land, off the shore and off other pieces |
| `water` | pieces placed **in** the water (stepping stones, boats): `per100` per 100 water cells | every footprint cell must be water |
| `decals` | flat pieces: `{{group, on: land / water / shore, per100}}`. A group with `joins: "mycelium"` is a vein network | draw after the ground and before anything that stands |
| `connectors` | stairs and ramps | attach to a platform of the same height (see their `connector` field); the game decides where |
| `structures` | groups placed by the game's own rules (the buildings kit, docks) | not scattered |
| `weather` | `chance`, and weighted overlay groups | one per map at most; draw tiled over the map; blend, opacity and scroll are in each overlay's record |

## Heights

The game's height step is **8 pixels** (`BattleGrid.HEIGHT_STEP`, half a block); this project's **level is 16 pixels**, two steps. Rocks, ledges, slabs and stairs are 1 or 2 levels (2 or 4 steps); ruin floors and the water props are half a level (one step). **Sunken water is one step (8 pixels) below the land.** So:

- A **water prop** (`surface: "water"`: docks, stepping stones, boats, pads) is drawn **on the water's surface**, 8 pixels below the land's top face: put its anchor on the water cell's top face as drawn. Its walkable top is half a level above the surface, which is exactly the land's height.
- A **bridge** (`bridges-*`) stands on the **floor of the gap, one level (16 pixels) below the banks**, so its deck (one level above that) meets the bank. Place it over exactly the water cells it crosses (its footprint is 3 or 5 cells); both ends need land.
- Everything else stands on the top face of its cell.

## Using it

1. **Pick a set** for the battle (by encounter, node or at random). Draw the map on its `ground` sheet and lay the surfaces as you do now; draw grass from the set's `grass` cells, by weight. The corrupted sheet has the same layout as the plain one, cell for cell, so water and stone keep their cells and only the sheet changes. Use the corrupted clean turf cells in `grass`, not the mushroom block, for everyday grass.
2. **Draw in three passes:** the ground first, back to front; then the flat decals; then everything that stands, back to front. A piece over several cells is drawn when you reach its **front-most cell** (the largest `i + j`).
3. **Weights** are spread over a group's pieces, so a group of seven is no likelier than a group of two. Pieces of kind `variants` are several looks of one piece: pick a frame at random. A piece that is `walkable: true` has a flat top at `levels` levels; anything else with a footprint blocks every cell of it. `destructibles` have states and a `-destroy` animation; the `-broken` thorn walls are what a thorn wall becomes.
4. **Keep a set to itself.** A set only lists groups that fit its ground, so you can draw any of its pieces without a check. If you mix sets, mix the **twins** (a blocky ledge for a natural slab, a mushroom tree for a tree): they have the same footprints and rules. Do not put a piece that `fits` one ground on the other.

The editor's terrain page (`terrain.html`, the **Set** menu) does exactly this in `terrain.js` (`plan`, `makeSpan`, `planVeins`, `drawPlan`, `pickWeather`): read it as a worked example. The same seed in the same set always gives the same map.

## The sets

''' + '\n'.join(f"- **{s['label']}** (`{sid}`, {s['ground']} ground, {s['time']}): {s['blurb']}" for sid, s in doc['sets'].items()) + '\n'


OUTPUTS = {
    ROOT / 'assets' / 'sets.js': lambda doc: 'window.SETS = ' + json.dumps(doc, separators=(',', ':')) + ';\n',
    ROOT / 'sprites' / 'assets' / 'sets' / 'sets.json': lambda doc: json.dumps(doc, indent=1) + '\n',
    ROOT / 'SETS.md': lambda doc: markdown(doc),
    ROOT / 'sprites' / 'assets' / 'sets' / 'README.md': lambda doc: game_readme(doc),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='say whether the files are up to date, and write nothing')
    args = parser.parse_args()
    data = load_data()
    bad = problems(data)
    if bad:
        print('\n'.join(bad))
        sys.exit(1)
    doc = document(data)
    stale = []
    for path, make in OUTPUTS.items():
        text = make(doc)
        if path.exists() and path.read_text() == text:
            continue
        stale.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if args.check:
        print('up to date' if not stale else 'out of date: ' + ', '.join(str(p.relative_to(ROOT)) for p in stale))
        sys.exit(1 if stale else 0)
    print(f'{len(doc["sets"])} sets, {len(doc["groups"])} groups ->', ', '.join(str(p.relative_to(ROOT)) for p in OUTPUTS))


if __name__ == '__main__':
    main()
