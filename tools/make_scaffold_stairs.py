#!/usr/bin/env python3
"""Wooden scaffold stairs and ramps: the same 24 pieces as the stone stairs (tools/make_stairs.py), with the same footprints, heights, directions and anchors, so a map can swap one for the other.

    scaffold-h1-DIR / scaffold-h2-DIR              a run of plank treads up one level (over 2 cells) or two levels (over 3 cells), open between the treads
    scaffold-ramp-h1-DIR / scaffold-ramp-h2-DIR    the same runs as a sloped plank ramp
    scaffold-ledge-ramp-h1-DIR / ...-h2-DIR        a plank ramp that ends in a flat plank deck cell at that height

DIR is the way up, as for the stone: se, nw, sw, ne. Every piece is a timber frame: a stringer under each edge of the treads, posts down to the ground at the ends and at every cell boundary,
cross bracing between them on the side the camera sees, and, on the ramps and ledge ramps only, a rail along the back edge so the treads stay in view (the stepped stairs have none). The treads cover the whole width, so the whole footprint is walkable.
The ground shows through between the posts. Palette roles only, deterministic.

    python3 tools/make_scaffold_stairs.py --preview previews/scaffold-stairs.png
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxelkit as vk  # noqa: E402
import make_stairs as ms  # noqa: E402
from assetkit import family, write_json  # noqa: E402

FOLDER = 'scaffold-stairs'
CATEGORY = 'Stairs'
WALK_MIN = ms.WALK_MIN
PX = vk.PX
TREAD = 2                      # plank thickness, in voxels
V = PX                         # voxels across the run


def spec(kind, lv, d):
    sid, label, fx, fy, total, flat = ms.spec(kind, lv, d)
    sid = sid.replace('stair-', 'scaffold-', 1)
    label = label.replace('Stone stairs', 'Scaffold stairs').replace('Stone ramp', 'Scaffold ramp').replace('Ledge with a ramp', 'Scaffold ledge with a ramp')
    return sid, label, fx, fy, total, flat


def build(kind, lv, d):
    sid, label, fx, fy, total, flat = spec(kind, lv, d)
    U = PX * total
    ht = ms.heights(kind, lv, total)
    sc = vk.Scene(fx, fy, PX * lv + (6 if kind == 'stair' else 14))

    def put(u, v, k, m):
        i, j = ms.to_world(d, u, v, U)
        sc.set(i, j, k, m)
    for u in range(U):
        top = ht[u]
        for v in range(V):                                                       # the treads: planks across the whole width
            for k in range(max(0, top - TREAD), top):
                put(u, v, k, vk.M_PLANK)
        for v in (1, 2, 3, 12, 13, 14):                                            # a stringer under each side, following the slope
            for k in range(max(0, top - TREAD - 3), max(0, top - TREAD)):
                put(u, v, k, vk.M_BEAM)
    posts = sorted(set([2, U - 4] + [PX * n - 1 for n in range(1, total)]))
    for p in posts:
        for du in (0, 1):
            for dv in (0, 1):
                for v0 in (0, 14):
                    for k in range(0, max(1, ht[min(U - 1, p + du)] - TREAD - 3)):
                        put(p + du, v0 + dv, k, vk.M_POST)
    # the rail along the back edge (v = 0): posts standing above the treads, and two rails between them. Ramps and ledge ramps have it; the stepped stairs do not.
    if kind != 'stair':
        for p in posts:
            for du in (0, 1):
                for dv in (0, 1):
                    for k in range(max(0, ht[min(U - 1, p + du)] - TREAD - 3), ht[min(U - 1, p + du)] + 9):
                        put(p + du, dv, k, vk.M_POST)
        for lo, hi in zip(posts, posts[1:]):
            for rail in (4, 8):
                for u in range(lo + 2, hi):
                    put(u, 0, ht[u] + rail, vk.M_BEAM)
    # a brace on the front side between each pair of posts: a diagonal of beam from the lower post's foot to the higher post's tread
    for lo, hi in zip(posts, posts[1:]):
        span = hi - lo - 2
        if span < 6:
            continue
        for s in range(span):
            u = lo + 2 + s
            k = int(round((ht[lo] - TREAD - 4) * (1 - s / float(span)) + 1 * (s / float(span)))) if ht[lo] > 6 else 1
            if 0 <= k < ht[u] - TREAD - 3:
                put(u, 15, k, vk.M_BEAM)
    return sc, ht, U


def painter(d, U):
    def paint(m, face, i, j, k):
        r = vk.hrole(i, j, k, 5, 100)
        u, v = ms.from_world(d, i, j, U)
        if m == vk.M_PLANK:
            n = u // 4
            if face == 'z':
                if u % 4 == 3:
                    return 'g'
                if vk.hrole(n, 2, 3, 5, 6) == 0 and r % 3 == 0:
                    return 'A'                                                    # moss on a plank
                return ('a', 'e', 'a', 'b', 'e')[vk.hrole(n, 9, 0, 5, 5)] if r % 7 else 'b'
            return ('e' if face == 'x' else 'f') if vk.hrole(n, 4, 0, 5, 3) else ('f' if face == 'x' else 'g')
        if m == vk.M_BEAM:
            return {'z': 'e', 'x': 'f', 'y': 'g'}[face] if r % 11 else 'w'
        if m == vk.M_POST:
            return {'z': 'a', 'x': 'e', 'y': 'f'}[face] if r % 9 else 'g'
        return 'x'
    return paint


_CACHE = {}


def piece(kind, lv, d):
    key = (kind, lv, d)
    if key not in _CACHE:
        sid, label, fx, fy, total, flat = spec(kind, lv, d)
        sc, ht, U = build(kind, lv, d)
        rows, anchor = vk.render(sc, painter(d, U))
        cells = {(i, j) for i in range(fx) for j in range(fy)}
        cover = vk.walk_cover(sc, cells)
        _CACHE[key] = dict(id=sid, label=label, rows=rows, anchor=anchor, size=(fx, fy), cells=sorted(cells), cover=cover,
                           walkable=min(cover.values()) >= WALK_MIN, levels=lv, up=d, kind=kind, run=total - flat, flat=flat)
    return _CACHE[key]


def pieces():
    return [piece(k, lv, d) for k in ms.KINDS for lv in ms.LEVELS for d in ms.DIRS]


def build_assets():
    """Twenty-four stills in category Stairs, one for each stone stair, ramp and ledge ramp, in the same footprint, height, direction and anchor, as plank scaffolds."""
    out = []
    for p in pieces():
        make = family(CATEGORY, len(p['rows'][0]), len(p['rows']), p['anchor'], place='ground', folder=FOLDER)
        fx, fy = p['size']
        out.append(make(p['id'], p['label'], 'still', [p['rows']], footprint={'size': [fx, fy], 'cells': [list(c) for c in p['cells']]},
                        walkable=p['walkable'], levels=p['levels'], style='timber',
                        top_cover={f'{i},{j}': round(v, 2) for (i, j), v in p['cover'].items()},
                        connector={'kind': p['kind'], 'up': p['up'], 'rise_levels': p['levels'], 'run_cells': p['run'], 'flat_cells': p['flat']},
                        twin=p['id'].replace('scaffold-', 'stair-', 1)))
    return out


def write_package(folder):
    write_json(folder, 'scaffold-stairs.json', 'The scaffold stairs in this folder. See README.md beside this file.',
               {'step': ms.STEP, 'walk_min': WALK_MIN, 'margin': vk.MARGIN,
                'pieces': {p['id']: {'label': p['label'], 'file': f"{p['id']}.png", 'size': list(p['size']), 'cells': [list(c) for c in p['cells']], 'up': p['up'],
                                      'rise_levels': p['levels'], 'run_cells': p['run'], 'flat_cells': p['flat'], 'walkable': p['walkable'],
                                      'stone_twin': p['id'].replace('scaffold-', 'stair-', 1)} for p in pieces()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        ps = pieces()
        vk.sheet(ps, args.preview, title='scaffold stairs, ramps and ledge ramps: green = walkable')
        for p in ps:
            print(f"{p['id']:30s} {'WALK' if p['walkable'] else 'no  '} min {min(p['cover'].values()):.2f}")
        print('the scaffolds ->', args.preview)


if __name__ == '__main__':
    main()
