#!/usr/bin/env python3
"""Stone and plank bridges to cross a gap, in the ground tiles' projection (a voxel renderer: tools/voxelkit.py), each one sprite covering its whole footprint of 1 cell across and 3 or 5 along.

    arch       a stone arch bridge: one arch (3 cells) or two (5), solid abutments at each end, a low kerb on the front edge and a tall parapet along the back (the camera sees the front,
               so a unit crossing is never hidden), a post at each corner
    broken     the 5-cell arch with the middle crumbled away: ragged stubs either side of a gap, rubble at its foot. The two halves can be walked, the cells in the gap cannot.
    plank      a rotted plank bridge on posts and beams with a rope rail along the back only, like the older `bridge`: planks missing, others half gone, moss on the rest
    corrupt    the arch bridge in plum and lavender stone, grown over with vines and small mushrooms

The deck is exactly 1 level (16 pixels) above the ground the bridge stands on, so it meets a ledge or a bank of that height (the older `bridge` hangs a few pixels below the land).
x runs down and to the right (SE) and y down and to the left (SW): `bridge-arch-3x1` runs along x, `bridge-arch-1x3` along y. The footprint, `walkable` and `top_cover` are as for the rocks:
a cell's cover is the share of it that is deck or planks, and a bridge is walkable when every cell has at least 0.6.

    python3 tools/make_bridges.py --preview previews/bridges.png      every bridge, then the stairs and ramps, at 2x on their cells
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxelkit as vk  # noqa: E402
from assetkit import family, write_json  # noqa: E402
from buildings import hashed  # noqa: E402

FOLDER = 'bridges'
CATEGORY = 'Bridges'
DK = 16                      # the deck: one level up
NZ = DK + 14
WALK_MIN = 0.6
V = vk.PX

# stone in plum and lavender for the corrupted bridge: the same table shape as buildings.STONE
CORRUPT = {'R': dict(base='l', alt=('p', 'k'), mortar='k', lit='p'), 'L': dict(base='k', alt=('l', 'w'), mortar='w', lit='l'),
           'top': dict(base='l', alt=('p', 'k'), mortar='k', lit='p')}
KINDS = {'arch': 'Stone arch bridge', 'broken': 'Broken stone bridge', 'plank': 'Rotted plank bridge', 'corrupt': 'Overgrown stone bridge'}
PIECES = [('arch', 3), ('arch', 5), ('broken', 5), ('plank', 3), ('plank', 5), ('corrupt', 3), ('corrupt', 5)]


def pid(kind, length, axis):
    fx, fy = (length, 1) if axis == 'x' else (1, length)
    return f'bridge-{kind}-{fx}x{fy}'


def arches(length):
    if length == 3:
        return [(24, 14, 12)]
    return [(24, 14, 12), (56, 14, 12)]


class Builder:
    def __init__(self, length, axis):
        self.L, self.axis = length, axis
        self.U = V * length
        fx, fy = (length, 1) if axis == 'x' else (1, length)
        self.sc = vk.Scene(fx, fy, NZ)

    def put(self, u, v, k, m):
        i, j = (u, v) if self.axis == 'x' else (v, u)
        self.sc.set(i, j, k, m)

    def get(self, u, v, k):
        i, j = (u, v) if self.axis == 'x' else (v, u)
        return self.sc.get(i, j, k)

    def to_uv(self, i, j):
        return (i, j) if self.axis == 'x' else (j, i)


# --- the stone bridges ---------------------------------------------------------------------------------
def stone_bridge(length, axis, kind):
    b = Builder(length, axis)
    U = b.U
    ar = arches(length)
    g0, g1 = int(U * 0.4), int(U * 0.6)
    for u in range(U):
        for v in range(V):
            for k in range(DK):
                solid, ring, theta = True, False, 0.0
                for c, a, hc in ar:
                    du, dk = (u + 0.5 - c) / a, (k + 0.5) / hc
                    r2 = du * du + dk * dk
                    if r2 < 1 and abs(du) < 1:
                        solid = False
                    elif r2 < 1.5 and abs(du) < 1.25:
                        ring, theta = True, math.atan2(dk, du)
                if not solid:
                    continue
                if kind == 'broken':
                    jl = hashed(v // 2, k // 3, 5) % 9 - 4
                    jr = hashed(v // 2, k // 3, 9) % 9 - 4
                    if g0 + jl < u < g1 + jr:
                        continue
                m = vk.M_STONE
                if k == DK - 1:
                    m = vk.M_DECK
                elif ring:
                    t = theta / (math.pi / 9)
                    m = vk.M_MORTAR if t - int(t) < 0.12 else (vk.M_RING_A if int(t) % 2 else vk.M_RING_B)
                b.put(u, v, k, m)
    # the parapet along the back, a kerb on the front, a post at each corner
    for u in range(U):
        for v in range(V):
            top = 0
            if v < 2:
                top = 5
            if v >= V - 2:
                top = 2
            if u < 4 or u >= U - 4:
                if v < 4:
                    top = 9
                elif v >= V - 4:
                    top = 4
            for k in range(DK, DK + top):
                if b.get(u, v, DK - 1):
                    b.put(u, v, k, vk.M_PARAPET)
    if kind == 'broken':
        for u in range(g0 - 10, g1 + 10):
            for v in range(V):
                if b.get(u, v, DK - 1) == 0:
                    h = hashed(u // 3, v // 3, 21) % 5
                    for k in range(0, h if g0 + 2 < u < g1 - 2 or h > 2 else 0):
                        if hashed(u, v, k + 40) % 4:
                            b.put(u, v, k, vk.M_RUBBLE)
    if kind == 'corrupt':
        grow(b)
    return b


def mushroom(b, u, v, k0, r, h, salt):
    """A small mushroom standing at (u, v) on height k0: a stalk 2 across and h high, a cap of radius r in two layers, a spot or two."""
    for k in range(k0, k0 + h):
        for du in (0, 1):
            for dv in (0, 1):
                b.put(u + du, v + dv, k, vk.M_STALK)
    for layer, rr in ((0, r), (1, r - 1)):
        for du in range(-rr, rr + 2):
            for dv in range(-rr, rr + 2):
                if (du - 0.5) ** 2 + (dv - 0.5) ** 2 <= (rr + 0.5) ** 2:
                    spot = layer == 1 and hashed(u + du, v + dv, salt) % 4 == 0 and abs(du) + abs(dv) > 0
                    b.put(u + du, v + dv, k0 + h + layer, vk.M_SPOT if spot else vk.M_CAP)


def grow(b):
    """Vines hanging over the front edge and mushrooms on the kerb, the parapet and the deck's corners."""
    U = b.U
    for u in range(U):
        if hashed(u // 2, 3, 11) % 5 == 0:
            length = 4 + hashed(u, 5, 12) % 9
            for k in range(DK - length, DK):
                if b.get(u, V - 1, k):
                    b.put(u, V, k, vk.M_VINE)
        if hashed(u // 3, 4, 13) % 7 == 0:
            for k in range(DK + 1, DK + 6):
                if b.get(u, 0, k) == vk.M_PARAPET:
                    b.put(u, -1, k, vk.M_VINE)
    spots = [(12, 0, DK + 5, 3, 3), (34, 0, DK + 5, 2, 2), (52, 0, DK + 5, 3, 3), (20, V - 2, DK + 2, 2, 2), (44, V - 2, DK + 2, 2, 3), (2, 2, DK + 9, 2, 2)]
    for n, (u, v, k0, r, h) in enumerate(spots):
        if u < U - 4 and b.get(u, v, k0 - 1):
            mushroom(b, u, v, k0, r, h, 50 + n)
    if b.L == 5:
        for u, v, k0, r, h in ((66, 0, DK + 5, 2, 2), (72, V - 2, DK + 2, 3, 3)):
            if b.get(u, v, k0 - 1):
                mushroom(b, u, v, k0, r, h, 90 + u)


# --- the plank bridge ----------------------------------------------------------------------------------
def plank_bridge(length, axis):
    b = Builder(length, axis)
    U = b.U
    pitch = 4
    nplank = U // pitch
    holes = set()
    half = {}
    for n in range(2, nplank - 2):
        h = hashed(n, length, 7) % 11
        if h == 0 and (n - 1) not in holes:
            holes.add(n)
        elif h == 1:
            half[n] = (0, 8) if hashed(n, 3, 8) % 2 else (8, 16)
    for u in range(4):                                       # a sill of stone at each end, where the planks rest on the bank
        for v in range(V):
            for k in range(DK - 2):
                b.put(u, v, k, vk.M_STONE)
                b.put(U - 1 - u, v, k, vk.M_STONE)
    for u in range(U):
        n = u // pitch
        for v in range(V):
            for k in (DK - 2, DK - 1):
                if n in holes or (n in half and half[n][0] <= v < half[n][1]):
                    continue
                b.put(u, v, k, vk.M_PLANK)
    for u in range(U):                                       # beams under the deck on either side
        for v in list(range(2, 5)) + list(range(11, 14)):
            for k in range(DK - 5, DK - 2):
                b.put(u, v, k, vk.M_BEAM)
    posts = [2] + [2 + 24 * m for m in range(1, (U - 4) // 24 + 1)] + [U - 5]
    posts = sorted(set(p for p in posts if 2 <= p <= U - 4))
    for p in posts:
        for du in (0, 1):
            for dv in (0, 1):
                for k in range(0, DK + 9):
                    b.put(p + du, 2 + dv, k, vk.M_POST)      # back posts stand above the deck
                for k in range(0, DK - 2):
                    b.put(p + du, 12 + dv, k, vk.M_POST)     # front posts hold it up from below
    for lo, hi in zip(posts, posts[1:]):                      # a rope along the back between the posts, sagging, frayed in one place
        span = hi - lo
        for height in (DK + 7, DK + 4):
            if hashed(lo, height, 6) % 6 == 0:
                continue
            for u in range(lo + 2, hi):
                sag = int(round(2.0 * math.sin(math.pi * (u - lo) / float(span))))
                b.put(u, 2, height - sag, vk.M_ROPE)
    return b


# --- paint -----------------------------------------------------------------------------------------------
def stone_painter(pal, moss, axis, corrupt=False):
    def paint(m, face, i, j, k):
        a, c = vk.face_coords(face, i, j, k)
        r = vk.hrole(i, j, k, 1, 100)
        wall = 'R' if face == 'x' else 'L'
        if m in (vk.M_RING_A, vk.M_RING_B, vk.M_MORTAR):
            ring = {'z': ('r', 'q', 'p'), 'x': ('r', 'q', 'p'), 'y': ('q', 'p', 'k')}[face]
            if corrupt:
                ring = {'z': ('p', 'l', 'k'), 'x': ('p', 'l', 'k'), 'y': ('p', 'l', 'w')}[face]
            return ring[2] if m == vk.M_MORTAR else (ring[0] if m == vk.M_RING_A else ring[1])
        if m == vk.M_VINE:
            return 'z' if r < 15 and face != 'y' else ('A' if face != 'y' else ('B' if r % 3 else 's'))
        if m == vk.M_STALK:
            return 't' if face != 'y' else 'C'
        if m == vk.M_CAP:
            return {'z': 'j', 'x': 'y', 'y': 'h'}[face]
        if m == vk.M_SPOT:
            return 't'
        if m == vk.M_RUBBLE:
            return stone_role_face(pal, face, a, c)
        if m == vk.M_PARAPET and face == 'z':
            return ('p' if corrupt else 'r') if r % 5 else ('l' if corrupt else 'q')
        if m == vk.M_DECK and face == 'z':
            return vk.stone_role(pal, 'top', a, c)
        role = stone_role_face(pal, face, a, c)
        if r < moss + (14 if k < 5 else 0) + (8 if face == 'z' else 0):
            return vk.moss_role(face, r)
        return role
    return paint


def stone_role_face(pal, face, a, c):
    return vk.stone_role(pal, 'top' if face == 'z' else ('R' if face == 'x' else 'L'), a, c)


def plank_painter(axis):
    top_roles = 'efeaf'
    def paint(m, face, i, j, k):
        u = i if axis == 'x' else j
        r = vk.hrole(i, j, k, 2, 100)
        if m == vk.M_STONE or m == vk.M_DECK:
            return vk.stone_role(vk.PAL, 'top' if face == 'z' else ('R' if face == 'x' else 'L'), *vk.face_coords(face, i, j, k))
        if m == vk.M_PLANK:
            n = u // 4
            if face == 'z':
                if u % 4 == 3:
                    return 'x'
                if hashed(n, 2, 3) % 6 == 0 and hashed(i, j, 3) % 3 == 0:
                    return 'A'                                         # moss on some planks
                return ('g', 'f', 'e', 'f', 'g')[hashed(n, 9) % 5] if r % 7 else 'a'
            return ('f' if face == 'x' else 'g') if hashed(n, 4) % 3 else ('g' if face == 'x' else 'w')
        if m == vk.M_BEAM:
            return {'z': 'f', 'x': 'g', 'y': 'w'}[face]
        if m == vk.M_POST:
            return {'z': 'e', 'x': 'f', 'y': 'g'}[face] if r % 9 else 'w'
        if m == vk.M_ROPE:
            return {'z': 'C', 'x': 'b', 'y': 'c'}[face]
        return 'x'
    return paint


# --- the pieces ----------------------------------------------------------------------------------------
_CACHE = {}


def piece(kind, length, axis):
    key = (kind, length, axis)
    if key not in _CACHE:
        sid = pid(kind, length, axis)
        if kind == 'plank':
            b = plank_bridge(length, axis)
            painter = plank_painter(axis)
        else:
            b = stone_bridge(length, axis, kind)
            painter = stone_painter(CORRUPT if kind == 'corrupt' else vk.PAL, 10 if kind == 'corrupt' else 4, axis, kind == 'corrupt')
        rows, anchor = vk.render(b.sc, painter)
        fx, fy = b.sc.fx, b.sc.fy
        cells = {(i, j) for i in range(fx) for j in range(fy)}
        cover = vk.walk_cover(b.sc, cells)
        label = f'{KINDS[kind]}, {length} cells, along {"x (SE)" if axis == "x" else "y (SW)"}'
        walkable = min(cover.values()) >= WALK_MIN
        _CACHE[key] = dict(id=sid, label=label, rows=rows, anchor=anchor, size=(fx, fy), cells=sorted(cells), cover=cover, walkable=walkable, kind=kind, axis=axis,
                           walkable_cells=sorted(c for c, v in cover.items() if v >= WALK_MIN))
    return _CACHE[key]


def pieces():
    return [piece(kind, length, axis) for kind, length in PIECES for axis in ('x', 'y')]


def build_assets():
    """Fourteen stills in category Bridges: arch (3 and 5), broken arch (5), plank (3 and 5) and overgrown arch (3 and 5), each along x and along y."""
    out = []
    for p in pieces():
        make = family(CATEGORY, len(p['rows'][0]), len(p['rows']), p['anchor'], place='ground', folder=FOLDER)
        fx, fy = p['size']
        out.append(make(p['id'], p['label'], 'still', [p['rows']], footprint={'size': [fx, fy], 'cells': [list(c) for c in p['cells']]},
                        walkable=p['walkable'], levels=1, style='bridge', run=p['axis'],
                        top_cover={f'{i},{j}': round(v, 2) for (i, j), v in p['cover'].items()},
                        walkable_cells=[list(c) for c in p['walkable_cells']]))
    return out


def write_package(folder):
    write_json(folder, 'bridges.json', 'The bridges in this folder. See README.md beside this file.',
               {'deck_levels': 1, 'walk_min': WALK_MIN, 'margin': vk.MARGIN,
                'bridges': {p['id']: {'label': p['label'], 'file': f"{p['id']}.png", 'size': list(p['size']), 'cells': [list(c) for c in p['cells']], 'run': p['axis'],
                                       'walkable': p['walkable'], 'walkable_cells': [list(c) for c in p['walkable_cells']]} for p in pieces()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--no-stairs', action='store_true', help='leave the stairs and ramps out of the preview')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        ps = pieces()
        for p in ps:
            print(f"{p['id']:24s} {'WALK' if p['walkable'] else 'no  '} min {min(p['cover'].values()):.2f}  cover {[round(v, 2) for v in p['cover'].values()]}")
        if not args.no_stairs:
            import make_stairs
            ps = ps + make_stairs.pieces()
        vk.sheet(ps, args.preview, title='bridges, then stairs and ramps: green = walkable')
        print('the bridges ->', args.preview)


if __name__ == '__main__':
    main()
