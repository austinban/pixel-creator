#!/usr/bin/env python3
"""A kit of ruined buildings for the isometric ground, in the building kit's stone and the rocks' footprint model: broken walls, corners and tees, an arch, heaps of fallen stone and bare foundation floors, each plain and overgrown (vines, moss and mushrooms) for the corrupted maps.

Every piece stands on whole ground cells and is one sprite that covers them, anchored at the middle of its bounding box on the ground (as the rocks and the buildings are; see tools/buildings.py for the projection:
x runs down and to the right, y down and to the left, 16 pixels up a level).

    WALLS      half a cell thick, running along x or y, broken along the top; 0.5, 1 and 2 levels at their highest. They are cover and line-of-sight blockers, never walkable:
               low (0.5, a unit can fire over it), high (1) and full (2, it blocks sight)
    CORNERS    two arms meeting, four turns, at 1 and 2 levels; TEES    a wall with a stub, four turns, at 1 level
    ARCH       a gateway through a wall: two piers and a corbelled arch broken at one side (2 levels)
    HEAPS      mounds of fallen stone, 1 x 1 to 2 x 2 and L; low cover, not walkable
    FLOORS     the footing of a lost building: flagstones half a level above the ground with a few flags gone, 1 x 1 to 2 x 2 and L; WALKABLE (top at 0.5)
    OVERGROWN  the same pieces with vines, moss and small mushrooms on them (suffix -grown)

`make_lowstructures.py` shares this file's renderer, material paint and preview.

    python3 tools/make_ruins.py --preview previews/ruins.png      every piece at 2x on its footprint, walkable ones marked, and the measured flat top of each walkable cell printed
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
import buildings as bd  # noqa: E402
from buildings import Solid, plane, hashed  # noqa: E402
from make_rocks import rect, lshape, rnd, seed_of, WALK_MIN, LEVEL, MARGIN  # noqa: E402

FOLDER = 'ruins'
CATEGORY = 'Ruins'
Q = 1.0 / 16


def q(v):
    """Round a height to a whole pixel."""
    return round(v / Q) * Q


# --- solids and their paint ---------------------------------------------------------------------
class Blk(Solid):
    """A box that remembers its bounds, so a material can paint edges and seams."""

    def __init__(self, x0, x1, y0, y1, z0, z1, style, seed=0, decay=None, grow=0.0, features=None, colour=None):
        super().__init__([((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)], style, features, decay=decay)
        self.b = (x0, x1, y0, y1, z0, z1)
        self.top = z1
        self.seed = seed
        self.grow = grow
        self.colour = colour


def px(v):
    return int(math.floor(v * LEVEL + 1e-6))


def leafy(lit, a, b, salt):
    return bd.leaf(lit, a, b, salt)


def decorate(solid, face, a, b, colour):
    for item in solid.decay:
        only, kind = item if isinstance(item, tuple) else (None, item)
        if only in (None, face):
            colour = bd.overlay(kind, face == 'R', a, b, colour)
    return colour


def paint_rubble(s, face, P):
    x, y, z = P
    if face == 'top':
        a, b = px(x), px(y)
        ramp = 'qpqrpq'
    else:
        a, b = (px(y) if face == 'R' else px(x)), px(z)
        ramp = 'plpqlp' if face == 'R' else 'lklplk'
    h = hashed(a // 2 + (s.seed & 0xFF), b // 2, 5 + (s.seed & 0x3F))
    colour = ramp[h % len(ramp)]
    x0, x1, y0, y1, z0, z1 = s.b
    if face == 'top' and (px(x) == px(x0) or px(x) == px(x1) - 1 or px(y) == px(y0) or px(y) == px(y1) - 1):
        colour = 'l'
    elif face != 'top' and (px(z) == px(z0)):
        colour = 'k'
    if hashed(a, b, 9 + (s.seed & 0xFF)) % 47 == 0:
        colour = 'k'
    if face == 'top' and hashed(a // 2, b // 2, 77 + (s.seed & 0xFF)) % 100 < 6 + 40 * s.grow:
        return leafy(True, a, b, 4)
    if face != 'top':
        colour = decorate(s, face, a, b, colour)
    return colour


def paint_flag(s, face, P):
    x, y, z = P
    if face != 'top':
        a, b = (px(y) if face == 'R' else px(x)), px(z)
        return decorate(s, face, a, b, bd.stone(face, a, b, True))
    a, b = px(x), px(y)
    row = b // 8
    col, c = divmod(a + (4 if row % 2 else 0), 8)
    r = b % 8
    if r == 7 or c == 7:                                             # a joint, mossy when it is overgrown
        return leafy(True, a, b, 2) if hashed(a, b, 3 + (s.seed & 0xFF)) % 100 < 20 + 60 * s.grow else 'l'
    h = hashed(col, row, 11 + (s.seed & 0xFF)) % 9
    base = 'q' if h < 4 else 'p' if h < 7 else 'r'
    if h == 8 and (a + b) % 5 == 0:
        base = 'l'
    if hashed(a // 2, b // 2, 41 + (s.seed & 0xFF)) % 100 < 4 + 38 * s.grow:
        return leafy(True, a, b, 6)
    return base


def paint_cap(s, face, P):
    x, y, z = P
    return {'top': 'y', 'R': 'j', 'L': 'i'}[face] if (px(x) + px(y)) % 5 else 't'


def paint_stem(s, face, P):
    return {'top': 'C', 'R': 'C', 'L': 'b'}[face]


CUSTOM = {'rubble': paint_rubble, 'flag': paint_flag, 'cap': paint_cap, 'stem': paint_stem}


def register(name, fn):
    CUSTOM[name] = fn


def paint_any(solid, n, P):
    face = bd.face_of(n)
    if face is None:
        return None
    fn = CUSTOM.get(solid.style)
    if fn is not None:
        return fn(solid, face, P)
    if face in ('R', 'L', 'top'):
        return bd.paint(solid, face, P, True)
    return bd.paint(solid, face, P, True)


# --- rendering -----------------------------------------------------------------------------------
def render(solids, cells, outline=True):
    """(rows, anchor, (fx, fy)): the pieces as palette-role rows, `16 (fx + fy) + 2 MARGIN` wide, with the anchor at the middle of the bounding footprint on the ground."""
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    zmax = max(s.top for s in solids)
    oy = int(math.ceil(LEVEL * zmax)) + 4
    w = 16 * (fx + fy) + 2 * MARGIN
    h = 8 * (fx + fy) + oy + 2
    ox = 16 * fy + MARGIN
    grid = [['.'] * w for _ in range(h)]
    for py in range(h):
        for pxl in range(w):
            sx, sy = pxl + 0.5, py + 0.5
            a, b = (sx - ox) / 16.0, (sy - oy) / 8.0
            origin = ((a + b) / 2, (b - a) / 2, 0.0)
            hits = []
            for s in solids:
                got = s.hit(origin)
                if got:
                    hits.append((got[0], got[1], s))
            hits.sort(key=lambda t: -t[0])
            for t, n, s in hits:
                colour = paint_any(s, n, (origin[0] + t, origin[1] + t, t))
                if colour:
                    grid[py][pxl] = colour
                    break
    out = [r[:] for r in grid]
    if outline:
        for y in range(h):
            for x in range(w):
                if grid[y][x] != '.':
                    continue
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] != '.':
                        out[y][x] = 'O'
                        break
    return [''.join(r) for r in out], (8 * (fx + fy) + MARGIN, oy + 4 * (fx + fy)), (fx, fy)


def top_cover(solids, heights):
    """For each cell with a walkable top level `heights[cell]`: the share of its area (8 x 8 samples) where the picture's surface is a flat top at that level."""
    n = 8
    out = {}
    for (i, j), hz in sorted(heights.items()):
        got = 0
        for a in range(n):
            for b in range(n):
                x, y = i + (a + 0.5) / n, j + (b + 0.5) / n
                best = None
                for s in solids:
                    g = s.hit((x - hz, y - hz, 0.0))
                    if g and (best is None or g[0] > best[0]):
                        best = (g[0], g[1], s)
                if best and abs(best[0] - hz) < 1e-6 and best[1][2] > 0.99 and bd.face_of(best[1]) == 'top':
                    got += 1
        out[(i, j)] = got / (n * n)
    return out


class Piece:
    def __init__(self, id, label, cells, build, heights=None, cover=None, kind='', grown=False):
        self.id, self.label, self.cells, self.build = id, label, set(cells), build
        self.heights = heights or {}                       # cell -> the level of its walkable top
        self.cover_kind = cover                            # 'low', 'high' or 'full' for a sight blocker, else None
        self.kind, self.grown = kind, grown
        self._done = None

    def solids(self):
        return self.build(seed_of(self.id))

    def done(self):
        if self._done is None:
            sol = self.solids()
            rows, anchor, size = render(sol, self.cells)
            cov = top_cover(sol, self.heights) if self.heights else {}
            self._done = (rows, anchor, size, cov)
        return self._done

    @property
    def walkable(self):
        cov = self.done()[3]
        return bool(cov) and min(cov.values()) >= WALK_MIN

    @property
    def levels(self):
        sol = self.solids()
        return round(max(s.top for s in sol), 2)


def finish(pieces, category, folder):
    out = []
    for p in pieces:
        rows, anchor, (fx, fy), cov = p.done()
        make = family(category, len(rows[0]), len(rows), anchor, place='ground', folder=folder)
        extra = {}
        if p.heights:
            extra['top_cover'] = {f'{i},{j}': round(v, 2) for (i, j), v in cov.items()}
            extra['cell_levels'] = {f'{i},{j}': v for (i, j), v in sorted(p.heights.items())}
        if p.cover_kind:
            extra['cover'] = p.cover_kind
        out.append(make(p.id, p.label, 'still', [rows], footprint={'size': [fx, fy], 'cells': [list(c) for c in sorted(p.cells)]},
                        walkable=p.walkable, levels=p.levels, piece=p.kind, overgrown=p.grown, **extra))
    return out


def package(folder, pieces, name, about):
    recs = {}
    for p in pieces:
        rows, anchor, (fx, fy), cov = p.done()
        recs[p.id] = {'label': p.label, 'file': f'{p.id}.png', 'kind': p.kind, 'size': [fx, fy], 'cells': [list(c) for c in sorted(p.cells)],
                      'walkable': p.walkable, 'levels': p.levels, 'overgrown': p.grown,
                      **({'cover': p.cover_kind} if p.cover_kind else {}),
                      **({'cell_levels': {f'{i},{j}': v for (i, j), v in sorted(p.heights.items())}, 'top_cover': {f'{i},{j}': round(v, 2) for (i, j), v in cov.items()}} if p.heights else {})}
    write_json(folder, name, about, {'level': LEVEL, 'walk_min': WALK_MIN, 'margin': MARGIN, 'pieces': recs})


# --- ruins ---------------------------------------------------------------------------------------
THICK = (0.25, 0.75)


def wall_run(axis, lo, hi, h, seed, grown, thick=THICK, floor=0.0, decay=None):
    """A broken wall from lo to hi along `axis` ('x' or 'y'): 3 to 5 stretches, none shorter than h / 2, at least one up to h and most above 0.6 h."""
    n = 3 + int(rnd(seed, 1) * 3)
    cuts = sorted([lo, hi] + [lo + (hi - lo) * (k + 0.4 + 0.5 * rnd(seed, 10 + k)) / n for k in range(1, n)])
    top = [1.0] + [0.62 + 0.38 * rnd(seed, 20 + k) for k in range(len(cuts) - 2)]
    top[int(rnd(seed, 3) * len(top))] = 1.0
    out = []
    for k in range(len(cuts) - 1):
        hk = q(floor + h * top[k]) if k < len(top) else q(floor + h * 0.7)
        if hi - lo < 0.3:
            hk = q(floor + h)
        a0, a1 = cuts[k], cuts[k + 1]
        bounds = (a0, a1, thick[0], thick[1]) if axis == 'x' else (thick[0], thick[1], a0, a1)
        out.append(Blk(*bounds, floor, hk, 'stone', seed + k, decay=decay))
    return out


def base_rubble(cells_box, seed, grown, sides=('x1', 'y1')):
    """A few small fallen stones at the foot of the wall, on its lit sides."""
    out = []
    for k in range(4):
        side = sides[k % len(sides)]
        t = 0.1 + 0.8 * rnd(seed, 40 + k)
        sz = 0.1 + 0.1 * rnd(seed, 50 + k)
        hz = q(0.06 + 0.14 * rnd(seed, 60 + k))
        if side == 'x1':
            x0, y0 = 0.77 + 0.03 * rnd(seed, 70 + k), min(t, 1 - sz)
            out.append(Blk(x0, x0 + sz, y0, y0 + sz, 0, hz, 'rubble', seed + 90 + k, grow=grown))
        else:
            y0, x0 = 0.77 + 0.03 * rnd(seed, 70 + k), min(t, 1 - sz)
            out.append(Blk(x0, x0 + sz, y0, y0 + sz, 0, hz, 'rubble', seed + 90 + k, grow=grown))
    return out


def mushrooms(spots, seed, n=4):
    """Little mushrooms at (x, y, z) spots: a cream stem and a magenta cap."""
    out = []
    for k, (x, y, z) in enumerate(spots[:n]):
        sz = 0.08 + 0.05 * rnd(seed, 300 + k)
        sh = q(0.06 + 0.05 * rnd(seed, 310 + k))
        out.append(Blk(x - 0.02, x + 0.02, y - 0.02, y + 0.02, z, z + sh, 'stem', seed))
        out.append(Blk(x - sz / 2, x + sz / 2, y - sz / 2, y + sz / 2, z + sh, z + sh + 0.05, 'cap', seed))
    return out


def grow(solids, seed, extra_spots=()):
    """The same solids overgrown: vines and moss on every stone face, moss on the tops, and mushrooms on the highest tops and at the foot."""
    for s in solids:
        if isinstance(s, Blk) and s.style in ('stone',):
            s.decay = list(s.decay) + [('vines-low' if hashed(s.seed, 1) % 2 else 'vines-hang') if hashed(s.seed, 2) % 3 else 'vines-heavy', 'mossy']
        if isinstance(s, Blk):
            s.grow = 1.0
    cand = sorted([s for s in solids if isinstance(s, Blk) and s.style in ('stone', 'rubble', 'flag') and s.top >= 0.2], key=lambda s: -s.top)
    spots = []
    for k, s in enumerate(cand[:5]):
        x0, x1, y0, y1, z0, z1 = s.b
        if x1 - x0 > 0.14 and y1 - y0 > 0.14:
            spots.append((x0 + (x1 - x0) * (0.3 + 0.4 * rnd(seed, 330 + k)), y0 + (y1 - y0) * (0.3 + 0.4 * rnd(seed, 340 + k)), z1))
    spots += list(extra_spots)
    return solids + mushrooms(spots, seed, 5)


def foot_spots(seed):
    return [(0.82 + 0.1 * rnd(seed, 350), 0.2 + 0.6 * rnd(seed, 351), 0.0), (0.2 + 0.6 * rnd(seed, 352), 0.82 + 0.1 * rnd(seed, 353), 0.0)]


def wall_piece(axis, h, length=1):
    def make(seed, grown=False):
        d = ['worn'] if rnd(seed, 80) > 0.45 else None
        sol = wall_run(axis, 0.0, float(length), h, seed, grown, decay=d) if axis == 'x' else wall_run(axis, 0.0, float(length), h, seed, grown, decay=d)
        return sol
    return make


def long_wall(axis, h, n):
    """A wall n cells long: the run is drawn across the whole footprint."""
    def make(seed):
        d = ['worn'] if rnd(seed, 80) > 0.45 else None
        sol = wall_run(axis, 0.0, float(n), h, seed, 0.0, decay=d)
        return sol + base_rubble(None, seed, 0.0)
    return make


def corner_solids(arms, h, seed):
    """Two arms from a post at the middle: arms is a pair of (axis, sign)."""
    cx = (0.25, 0.75)
    post = Blk(0.25, 0.75, 0.25, 0.75, 0, q(h), 'stone', seed, decay=['worn'] if rnd(seed, 80) > 0.5 else None)
    out = [post]
    for k, (axis, sign) in enumerate(arms):
        lo, hi = (0.75, 1.0) if sign > 0 else (0.0, 0.25)
        n = 2 + k
        cuts = [lo, lo + (hi - lo) * 0.5, hi] if sign > 0 else [lo, lo + (hi - lo) * 0.5, hi]
        for m in range(2):
            a0, a1 = cuts[m], cuts[m + 1]
            hm = q(h * (0.55 + 0.4 * rnd(seed, 100 + 10 * k + m)))
            if (m == 1 and sign > 0) or (m == 0 and sign < 0):
                hm = q(h * (0.55 + 0.25 * rnd(seed, 100 + 10 * k + m)))        # the end of an arm is lower
            out.append(Blk(a0, a1, 0.25, 0.75, 0, hm, 'stone', seed + 5 + m, decay=['worn'] if rnd(seed, 200 + k) > 0.6 else None) if axis == 'x'
                       else Blk(0.25, 0.75, a0, a1, 0, hm, 'stone', seed + 5 + m, decay=['worn'] if rnd(seed, 200 + k) > 0.6 else None))
    return out + base_rubble(None, seed, 0.0)


CARD = {'se': ('x', 1), 'sw': ('y', 1), 'nw': ('x', -1), 'ne': ('y', -1)}      # +x is SE, +y is SW


def tee_solids(stem, h, seed):
    """A wall along the axis at right angles to `stem`, with a stub going out of its middle in the direction `stem`."""
    axis, sign = CARD[stem]
    run_axis = 'y' if axis == 'x' else 'x'
    sol = wall_run(run_axis, 0.0, 1.0, h, seed, 0.0, decay=['worn'] if rnd(seed, 80) > 0.5 else None)
    lo, hi = (0.75, 1.0) if sign > 0 else (0.0, 0.25)
    hm = q(h * 0.7)
    sol.append(Blk(lo, hi, 0.25, 0.75, 0, hm, 'stone', seed + 33) if axis == 'x' else Blk(0.25, 0.75, lo, hi, 0, hm, 'stone', seed + 33))
    return sol + base_rubble(None, seed, 0.0)


def arch_solids(axis, seed):
    """A gateway: the wall runs along `axis` and the opening goes through it. Piers up to 1.75 levels, a corbelled arch springing at 1.0, broken on one side."""
    out = []
    r = 0.22
    spring = 1.0
    top = 1.75
    broken_side = 1 if rnd(seed, 1) > 0.5 else -1
    z = 0.0
    step = 2 * Q
    slices = int(top / step)
    for k in range(slices):
        z0, z1 = k * step, (k + 1) * step
        zm = (z0 + z1) / 2
        half = r if zm < spring else math.sqrt(max(0.0, r * r - (zm - spring) ** 2))
        for side in (-1, 1):
            zt = z1
            if side == broken_side and zm > 1.45:                    # that pier has fallen away above here
                continue
            if side == broken_side and zm > 1.2:
                zt = z1 if hashed(k, 7, seed & 0xFF) % 3 else z0
            lo, hi = (0.0, 0.5 - half) if side < 0 else (0.5 + half, 1.0)
            if hi - lo <= 0.001 or zt <= z0:
                continue
            bounds = (lo, hi, 0.25, 0.75) if axis == 'x' else (0.25, 0.75, lo, hi)
            out.append(Blk(*bounds, z0, zt, 'stone', seed + k, decay=['worn'] if k % 5 == 0 else None))
        if half <= 0.005 and zm < top and zm >= spring:                      # the keystone block closing the crown
            if broken_side != 0 and zm < 1.45:
                bounds = (0.5 - 0.06, 0.5 + 0.06, 0.25, 0.75) if axis == 'x' else (0.25, 0.75, 0.5 - 0.06, 0.5 + 0.06)
                out.append(Blk(*bounds, z0, z1, 'stone', seed + 70 + k))
    return out + base_rubble(None, seed, 0.0)


def heap_solids(cells, seed, peak):
    """Fallen stone: on every cell a mound of rubble boxes, a few cut blocks lying about, highest in the middle of the footprint."""
    out = []
    cx = sum(i + 0.5 for i, _ in cells) / len(cells)
    cy = sum(j + 0.5 for _, j in cells) / len(cells)
    for i, j in sorted(cells):
        s = seed + i * 977 + j * 1301
        for k in range(5):
            w = 0.34 + 0.3 * rnd(s, k)
            d = 0.34 + 0.3 * rnd(s, 10 + k)
            x = i + 0.5 + (rnd(s, 20 + k) - 0.5) * 0.45
            y = j + 0.5 + (rnd(s, 30 + k) - 0.5) * 0.45
            near = 1.0 - min(1.0, math.hypot(x - cx, y - cy) / 1.1)
            hz = q(0.1 + (peak - 0.1) * (0.35 + 0.65 * near) * (0.55 + 0.45 * rnd(s, 40 + k)))
            x0, y0 = max(i + 0.02, x - w / 2), max(j + 0.02, y - d / 2)
            x1, y1 = min(i + 0.98, x + w / 2), min(j + 0.98, y + d / 2)
            out.append(Blk(x0, x1, y0, y1, 0, hz, 'rubble', s + k))
            if hz > 0.3 and k < 3:                                              # a smaller lump on top of the big ones
                sx, sy = (x1 - x0) * 0.5, (y1 - y0) * 0.5
                out.append(Blk(x0 + sx * 0.4, x0 + sx * 1.4, y0 + sy * 0.4, y0 + sy * 1.4, hz, q(hz + 0.12), 'rubble', s + 50 + k))
        for k in range(2):                                                      # a cut block
            w, d = 0.2 + 0.1 * rnd(s, 60 + k), 0.14 + 0.08 * rnd(s, 70 + k)
            x, y = i + 0.15 + 0.5 * rnd(s, 80 + k), j + 0.15 + 0.5 * rnd(s, 90 + k)
            out.append(Blk(x, min(i + 0.98, x + w), y, min(j + 0.98, y + d), 0, q(0.12 + 0.1 * rnd(s, 100 + k)), 'stone', s + 120 + k, decay=['worn']))
    return out


def floor_solids(cells, seed, level=0.5):
    """Flagstones on a footing half a level high: a 4 x 4 of flags on every cell, with some gone along the open edges, and a stub of the old wall on one edge."""
    out = []
    for i, j in sorted(cells):
        s = seed + i * 977 + j * 1301
        for a in range(4):
            for b in range(4):
                edge = ((i - 1, j) not in cells and a == 0) or ((i + 1, j) not in cells and a == 3) or ((i, j - 1) not in cells and b == 0) or ((i, j + 1) not in cells and b == 3)
                if edge and rnd(s, 10 * a + b) < 0.2 and not ((i, j) == min(cells) and a + b == 3):
                    continue
                out.append(Blk(i + a * 0.25, i + a * 0.25 + 0.25, j + b * 0.25, j + b * 0.25 + 0.25, 0, level, 'flag', s + 4 * a + b))
        if (i + 1, j) not in cells and rnd(s, 200) > 0.45:                       # a stub of the wall's footing on an open edge
            out.append(Blk(i + 0.86, i + 1.0, j + 0.15, j + 0.15 + 0.3 * (0.5 + rnd(s, 201)), level, level + 0.22, 'stone', s + 201, decay=['worn']))
    return out


# the pieces
def build_pieces():
    pieces = []

    def add(id, label, cells, fn, heights=None, cover=None, kind='', grown=False):
        pieces.append(Piece(id, label, cells, fn, heights, cover, kind, grown))

    def with_grown(make, seed_extra=0):
        def go(seed):
            return grow(make(seed), seed, foot_spots(seed))
        return go

    cov = {0.5: 'low', 1: 'high', 2: 'full'}
    for h in (0.5, 1, 2):
        for axis in ('x', 'y'):
            hn = {0.5: 'h05', 1: 'h1', 2: 'h2'}[h]
            add(f'ruin-wall-{axis}-{hn}', f'Broken wall along {axis}, {h} high', rect(1, 1), (lambda a, hh: lambda seed: wall_run(a, 0.0, 1.0, hh, seed, 0.0, decay=['worn'] if rnd(seed, 80) > 0.45 else None) + base_rubble(None, seed, 0.0))(axis, h),
                cover=cov[h], kind='wall')
    for h in (1, 2):
        add(f'ruin-wall-2x1-h{h}', f'Long broken wall 2 x 1, {h} high', rect(2, 1), long_wall('x', h, 2), cover=cov[h], kind='wall')
        add(f'ruin-wall-1x2-h{h}', f'Long broken wall 1 x 2, {h} high', rect(1, 2), long_wall('y', h, 2), cover=cov[h], kind='wall')
    for h in (1, 2):
        for name, arms in (('se-sw', (('x', 1), ('y', 1))), ('se-ne', (('x', 1), ('y', -1))), ('nw-sw', (('x', -1), ('y', 1))), ('nw-ne', (('x', -1), ('y', -1)))):
            add(f'ruin-corner-{name}-h{h}', f'Broken corner ({name}), {h} high', rect(1, 1), (lambda ar, hh: lambda seed: corner_solids(ar, hh, seed))(arms, h), cover=cov[h], kind='corner')
    for stem in ('se', 'sw', 'nw', 'ne'):
        add(f'ruin-tee-{stem}-h1', f'Broken tee, stub {stem}, 1 high', rect(1, 1), (lambda st: lambda seed: tee_solids(st, 1, seed))(stem), cover='high', kind='tee')
    for axis in ('x', 'y'):
        add(f'ruin-arch-{axis}', f'Broken arch, wall along {axis}', rect(1, 1), (lambda a: lambda seed: arch_solids(a, seed))(axis), cover='full', kind='arch')
    heaps = [('1x1', rect(1, 1), 0.6), ('1x2', rect(1, 2), 0.7), ('2x1', rect(2, 1), 0.7), ('2x2', rect(2, 2), 0.9)] + [(f'l-{m}', lshape(m), 0.7) for m in 'nesw']
    for name, cells, peak in heaps:
        add(f'ruin-heap-{name}', f'Heap of fallen stone {name}', cells, (lambda c, p: lambda seed: heap_solids(c, seed, p))(cells, peak), cover='low', kind='heap')
    floors = [('1x1', rect(1, 1)), ('1x2', rect(1, 2)), ('2x1', rect(2, 1)), ('2x2', rect(2, 2))] + [(f'l-{m}', lshape(m)) for m in 'nesw']
    for name, cells in floors:
        add(f'ruin-floor-{name}', f'Foundation floor {name}', cells, (lambda c: lambda seed: floor_solids(c, seed))(cells), heights={c: 0.5 for c in cells}, kind='floor')
    # overgrown: a chosen set
    grown_ids = ['ruin-wall-x-h2', 'ruin-wall-y-h2', 'ruin-wall-x-h1', 'ruin-wall-y-h1', 'ruin-wall-2x1-h2', 'ruin-wall-1x2-h2', 'ruin-corner-se-sw-h2', 'ruin-corner-se-ne-h2',
                 'ruin-corner-nw-sw-h2', 'ruin-corner-nw-ne-h2', 'ruin-tee-se-h1', 'ruin-tee-sw-h1', 'ruin-arch-x', 'ruin-arch-y', 'ruin-heap-1x1', 'ruin-heap-2x2', 'ruin-heap-1x2', 'ruin-floor-2x2',
                 'ruin-floor-1x1', 'ruin-floor-2x1', 'ruin-floor-l-n']
    by = {p.id: p for p in pieces}
    for gid in grown_ids:
        p = by[gid]
        add(gid + '-grown', p.label + ', overgrown', p.cells, (lambda base: lambda seed: grow(base.build(seed ^ 0x5A5A), seed, foot_spots(seed)))(p), p.heights, p.cover_kind, p.kind, True)
    return pieces


PIECES = None


def pieces():
    global PIECES
    if PIECES is None:
        PIECES = build_pieces()
    return PIECES


def build_assets():
    return finish(pieces(), CATEGORY, FOLDER)


def write_package(folder):
    package(folder, pieces(), 'ruins.json', 'The ruined building pieces in this folder. See README.md beside this file.')


# --- preview -------------------------------------------------------------------------------------
def draw_preview(path, plist, scale=2, width=1500, only=None):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    tiles = []
    for p in plist:
        rows, (ax, ay), (fx, fy), cov = p.done()
        im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c != '.':
                    im.putpixel((x, y), rgb[c] + (255,))
        tiles.append((p, im, (ax, ay), (fx, fy), cov))
    margin, x, y, rowh = 14, 14, 14, 0
    placed = []
    for t in tiles:
        im = t[1]
        w, h = max(im.width * scale, 110), im.height * scale + 28
        if x + w > width - margin:
            x, y, rowh = margin, y + rowh + 14, 0
        placed.append((t, x, y))
        x += w + 18
        rowh = max(rowh, h)
    sheet = Image.new('RGBA', (width, y + rowh + 20), (30, 34, 56, 255))
    d = ImageDraw.Draw(sheet)
    for (p, im, (ax, ay), (fx, fy), cov), x, y in placed:
        top = y + 16
        ox = 16 * fy + MARGIN
        oy = ay - 4 * (fx + fy)
        for i, j in p.cells:
            pts = [(ox + 16 * (X - Y), oy + 8 * (X + Y)) for X, Y in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            d.polygon([(x + a * scale, top + b * scale) for a, b in pts], fill=(70, 110, 70, 255) if p.heights else (90, 70, 70, 255), outline=(0, 0, 0, 90))
        sheet.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, top))
        mark = ' WALK' if p.walkable else (' cover:' + p.cover_kind if p.cover_kind else '')
        d.text((x, y), p.id.replace('ruin-', '').replace('low-', '') + mark, fill=(230, 220, 200, 255))
    sheet.save(path)
    for p in plist:
        cov = p.done()[3]
        if cov:
            print(f"{p.id:34s} {'WALK' if p.walkable else 'no  '} cover " + ' '.join(f'{v:.2f}' for v in cov.values()) + f'  (min {min(cov.values()):.2f}, need {WALK_MIN})')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        draw_preview(args.preview, pieces())
        print('the ruins ->', args.preview)


if __name__ == '__main__':
    main()
