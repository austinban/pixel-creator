#!/usr/bin/env python3
"""Stairs and ramps that carry a unit up to a rock ledge, in the ledges' stone and the ground's projection (a voxel renderer: tools/voxelkit.py).

    stair        a run of stone steps up one level (over 2 cells: 4 steps of 4 pixels) or two levels (over 3 cells: 8 steps of 4 pixels)
    ramp         the same runs as a smooth stone slope
    ledge-ramp   a ramp up one level (over 1 cell) or two levels (over 2 cells) that ends in a ledge cell with a flat top at that level, so it joins the rock ledges as one piece

Each comes up toward each of the four sides: `se` (up toward +x, down and to the right), `nw`, `sw` (up toward +y, down and to the left) and `ne`. The low end is at the ground and the high end
is exactly 1 or 2 levels up, flush with a ledge of that height. Every column of the surface is stone a unit can stand on, so the whole footprint is walkable.

    python3 tools/make_stairs.py --preview previews/stairs.png
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxelkit as vk  # noqa: E402
from assetkit import family, write_json  # noqa: E402

FOLDER = 'stairs'
CATEGORY = 'Stairs'
STEP = 4                                # the height of a step, in pixels
DIRS = ('se', 'nw', 'sw', 'ne')         # the way up
LEVELS = (1, 2)
KINDS = ('stair', 'ramp', 'ledge-ramp')
WALK_MIN = 0.6


def spec(kind, lv, d):
    """(id, label, cells, run in cells, flat cells at the top) of a piece."""
    if kind == 'ledge-ramp':
        run, flat = lv, 1
        total = run + flat
    else:
        run, flat = (2 if lv == 1 else 3), 0
        total = run
    label = {'stair': 'Stone stairs', 'ramp': 'Stone ramp', 'ledge-ramp': 'Ledge with a ramp'}[kind]
    fx, fy = (total, 1) if d in ('se', 'nw') else (1, total)
    return f'stair-{kind}-h{lv}-{d}' if kind != 'stair' else f'stair-h{lv}-{d}', f'{label}, {lv} up, rising toward {d.upper()}', fx, fy, total, flat


def heights(kind, lv, total):
    """The height in voxels of the top of each column along the run, from the low end."""
    U = vk.PX * total
    H = vk.PX * lv
    out = []
    for u in range(U):
        if kind == 'stair':
            depth = U // (H // STEP)
            out.append((u // depth + 1) * STEP)
        elif kind == 'ramp':
            out.append(max(1, int(H * (u + 1) / float(U) + 0.5)))
        else:
            run = U - vk.PX
            out.append(max(1, int(H * (u + 1) / float(run) + 0.5)) if u < run else H)
    return out


def to_world(d, u, v, U):
    """The footprint's own (i, j) of the column at u along the run (from the low end) and v across it."""
    return {'se': (u, v), 'nw': (U - 1 - u, v), 'sw': (v, u), 'ne': (v, U - 1 - u)}[d]


def from_world(d, i, j, U):
    return {'se': (i, j), 'nw': (U - 1 - i, j), 'sw': (j, i), 'ne': (j, U - 1 - i)}[d]


def build(kind, lv, d):
    sid, label, fx, fy, total, flat = spec(kind, lv, d)
    U = vk.PX * total
    ht = heights(kind, lv, total)
    sc = vk.Scene(fx, fy, vk.PX * lv + 6)
    for u in range(U):
        for v in range(vk.PX):
            i, j = to_world(d, u, v, U)
            for k in range(ht[u]):
                sc.set(i, j, k, vk.M_DECK if k == ht[u] - 1 else vk.M_STONE)
    return sc, ht, U


def painter(kind, lv, d, sc, ht, U):
    pal = vk.PAL

    def paint(m, face, i, j, k):
        a, b = vk.face_coords(face, i, j, k)
        r = vk.hrole(i, j, k, 3, 100)
        if face != 'z':
            if r < 6 and k < 6:
                return vk.moss_role(face, r)
            return vk.stone_role(pal, 'R' if face == 'x' else 'L', a, b)
        u, v = from_world(d, i, j, U)
        if r < 5:
            return vk.moss_role('z', r)
        if vk.lip_is_exposed(sc, i, j, k):
            return 'r' if r % 5 else 'q'                      # the lit lip of a step, of the ramp's edge and of the ledge
        if kind == 'stair' or (kind == 'ledge-ramp' and u >= U - vk.PX):
            return 'q' if r % 7 else 'p'
        return 'p' if u % 4 == 0 else ('q' if r % 6 else 'r')   # a ramp: a joint every four pixels
    return paint


_CACHE = {}


def piece(kind, lv, d):
    key = (kind, lv, d)
    if key not in _CACHE:
        sid, label, fx, fy, total, flat = spec(kind, lv, d)
        sc, ht, U = build(kind, lv, d)
        rows, anchor = vk.render(sc, painter(kind, lv, d, sc, ht, U))
        cells = {(i, j) for i in range(fx) for j in range(fy)}
        cover = vk.walk_cover(sc, cells)
        _CACHE[key] = dict(id=sid, label=label, rows=rows, anchor=anchor, size=(fx, fy), cells=sorted(cells), cover=cover,
                           walkable=min(cover.values()) >= WALK_MIN, levels=lv, up=d, kind=kind, run=total - flat, flat=flat)
    return _CACHE[key]


def pieces():
    return [piece(k, lv, d) for k in KINDS for lv in LEVELS for d in DIRS]


def build_assets():
    """Twenty-four stills in category Stairs: stair, ramp and ledge-ramp, 1 and 2 levels, up toward each of se, nw, sw and ne."""
    out = []
    for p in pieces():
        make = family(CATEGORY, len(p['rows'][0]), len(p['rows']), p['anchor'], place='ground', folder=FOLDER)
        fx, fy = p['size']
        out.append(make(p['id'], p['label'], 'still', [p['rows']], footprint={'size': [fx, fy], 'cells': [list(c) for c in p['cells']]},
                        walkable=p['walkable'], levels=p['levels'], style='block',
                        top_cover={f'{i},{j}': round(v, 2) for (i, j), v in p['cover'].items()},
                        connector={'kind': p['kind'], 'up': p['up'], 'rise_levels': p['levels'], 'run_cells': p['run'], 'flat_cells': p['flat']}))
    return out


def write_package(folder):
    write_json(folder, 'stairs.json', 'The stairs and ramps in this folder. See README.md beside this file.',
               {'step': STEP, 'walk_min': WALK_MIN, 'margin': vk.MARGIN,
                'pieces': {p['id']: {'label': p['label'], 'file': f"{p['id']}.png", 'size': list(p['size']), 'cells': [list(c) for c in p['cells']], 'up': p['up'],
                                      'rise_levels': p['levels'], 'run_cells': p['run'], 'flat_cells': p['flat'], 'walkable': p['walkable']} for p in pieces()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        ps = pieces()
        vk.sheet(ps, args.preview, title='stairs, ramps and ledge ramps: green = walkable')
        for p in ps:
            print(f"{p['id']:28s} {'WALK' if p['walkable'] else 'no  '} min {min(p['cover'].values()):.2f}")
        print('the stairs ->', args.preview)


if __name__ == '__main__':
    main()
