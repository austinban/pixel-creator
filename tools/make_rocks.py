#!/usr/bin/env python3
"""A kit of rocks on the isometric ground, of different footprints and heights, in the ground tiles' projection and the cool stone ramp with a little moss.

Every rock stands on whole ground cells and is one sprite that covers them, with the anchor at the middle of its bounding footprint on the ground (as the buildings do).
The footprint is a set of cells (x runs down and to the right, y down and to the left; see tools/buildings.py): a block of 1 x 1, 1 x 2, 2 x 1, 2 x 2, 1 x 3, 3 x 1, or an L.

    LEDGES    flat tops, a whole number of levels high (1 level = 16 pixels = the ground's step), that a unit can stand and walk on: the top is level across every cell of the
              footprint, with the cliff below it in coarse strata, moss on the lip and on the top
    CRAGS     not walkable: each cell rises to its own broken peak, so a crag is a cluster with valleys between, from a low boulder to a tall massif

    SLABS     the natural version of a ledge: worn, rounded stone cut flat at a whole level, so it is still walkable, with no stacked courses
    STONES    the natural version of a crag: boulders, a standing stone, outcrops and scree of smooth overlapping lumps, not walkable

NE/SE do not matter: a rock has no front. An L comes in four turns, named for the cell of its 2 x 2 box that is empty (n is the back corner of the diamond, e the right, s the front, w the left).

    python3 tools/make_rocks.py --preview previews/rocks.png      every rock at 2x on its footprint, walkable ones marked
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from buildings import Solid, plane, norm, hashed  # noqa: E402

FOLDER = 'rocks'
CATEGORY = 'Nature'
LEVEL = 16
MARGIN = 6
LIGHT = norm((0.55, 0.15, 0.8))          # towards the light: the right wall lit, the left wall shaded, the top brightest (as the buildings are)
RAMP = [(0.80, 'r'), (0.62, 'q'), (0.44, 'p'), (0.27, 'l'), (0.12, 'k'), (-9, 'w')]
MOSS = [(0.62, 'z'), (0.38, 'A'), (-9, 'B')]


# --- footprints ----------------------------------------------------------------------------------
def rect(fx, fy):
    return {(i, j) for i in range(fx) for j in range(fy)}


def lshape(missing, n=2):
    cells = rect(n, n)
    cells.discard({'n': (0, 0), 'e': (n - 1, 0), 'w': (0, n - 1), 's': (n - 1, n - 1)}[missing])
    return cells


def long_l(turn):
    """Four cells: an arm of three and a foot of one, in four turns."""
    base = {(0, 0), (0, 1), (0, 2), (1, 2)}
    for _ in range(turn):
        base = {(2 - j, i) for i, j in base}
    return {(i - min(c[0] for c in base), j - min(c[1] for c in base)) for i, j in base}


# (id, label, cells, kind, levels). A ledge is `levels` high and flat; a crag's `levels` is its tallest peak.
SHAPES = []
for lv in (1, 2):
    SHAPES += [(f'rock-ledge-1x1-h{lv}', f'Rock ledge 1 x 1, {lv} high', rect(1, 1), 'ledge', lv),
               (f'rock-ledge-1x2-h{lv}', f'Rock ledge 1 x 2, {lv} high', rect(1, 2), 'ledge', lv),
               (f'rock-ledge-2x1-h{lv}', f'Rock ledge 2 x 1, {lv} high', rect(2, 1), 'ledge', lv),
               (f'rock-ledge-2x2-h{lv}', f'Rock ledge 2 x 2, {lv} high', rect(2, 2), 'ledge', lv)]
SHAPES += [('rock-ledge-1x3-h1', 'Rock ledge 1 x 3, 1 high', rect(1, 3), 'ledge', 1), ('rock-ledge-3x1-h1', 'Rock ledge 3 x 1, 1 high', rect(3, 1), 'ledge', 1),
           ('rock-ledge-1x3-h2', 'Rock ledge 1 x 3, 2 high', rect(1, 3), 'ledge', 2), ('rock-ledge-3x1-h2', 'Rock ledge 3 x 1, 2 high', rect(3, 1), 'ledge', 2)]
for lv in (1, 2):
    for m in 'nesw':
        SHAPES.append((f'rock-ledge-l-{m}-h{lv}', f'Rock ledge, L (empty {m}), {lv} high', lshape(m), 'ledge', lv))
for t in range(4):
    SHAPES.append((f'rock-ledge-l4-{t}-h1', f'Rock ledge, long L (turn {t}), 1 high', long_l(t), 'ledge', 1))
SHAPES += [('rock-crag-1x1-a', 'Boulder', rect(1, 1), 'crag', 0.75), ('rock-crag-1x1-b', 'Crag', rect(1, 1), 'crag', 1.7), ('rock-crag-1x1-c', 'Tall crag', rect(1, 1), 'crag', 2.6),
           ('rock-crag-1x2', 'Crag ridge 1 x 2', rect(1, 2), 'crag', 2.2), ('rock-crag-2x1', 'Crag ridge 2 x 1', rect(2, 1), 'crag', 2.2),
           ('rock-crag-2x2', 'Massif 2 x 2', rect(2, 2), 'crag', 3.2), ('rock-crag-1x3', 'Long ridge 1 x 3', rect(1, 3), 'crag', 1.9), ('rock-crag-3x1', 'Long ridge 3 x 1', rect(3, 1), 'crag', 1.9)]
for m in 'nesw':
    SHAPES.append((f'rock-crag-l-{m}', f'Scree, L (empty {m})', lshape(m), 'crag', 1.5))


WALK = ('ledge', 'slab')
STYLE = {'ledge': 'block', 'crag': 'block', 'slab': 'natural', 'stone': 'natural'}
NATURAL = []
for lv in (1, 2):
    NATURAL += [(f'rock-slab-1x1-h{lv}', f'Worn slab 1 x 1, {lv} high', rect(1, 1), 'slab', lv),
                (f'rock-slab-1x2-h{lv}', f'Worn slab 1 x 2, {lv} high', rect(1, 2), 'slab', lv),
                (f'rock-slab-2x1-h{lv}', f'Worn slab 2 x 1, {lv} high', rect(2, 1), 'slab', lv),
                (f'rock-slab-2x2-h{lv}', f'Worn slab 2 x 2, {lv} high', rect(2, 2), 'slab', lv)]
NATURAL += [('rock-slab-1x3-h1', 'Worn slab 1 x 3, 1 high', rect(1, 3), 'slab', 1), ('rock-slab-3x1-h1', 'Worn slab 3 x 1, 1 high', rect(3, 1), 'slab', 1)]
for m in 'nesw':
    NATURAL.append((f'rock-slab-l-{m}-h1', f'Worn slab, L (empty {m}), 1 high', lshape(m), 'slab', 1))
NATURAL += [('rock-stone-boulder', 'Boulder', rect(1, 1), 'stone', 0.8), ('rock-stone-round', 'Round stone', rect(1, 1), 'stone', 1.3),
            ('rock-stone-standing', 'Standing stone', rect(1, 1), 'stone', 2.5),
            ('rock-stone-pair-1x2', 'Stone pair 1 x 2', rect(1, 2), 'stone', 1.4), ('rock-stone-pair-2x1', 'Stone pair 2 x 1', rect(2, 1), 'stone', 1.4),
            ('rock-stone-cluster', 'Stone cluster 2 x 2', rect(2, 2), 'stone', 2.0),
            ('rock-stone-outcrop-1x3', 'Outcrop 1 x 3', rect(1, 3), 'stone', 1.6), ('rock-stone-outcrop-3x1', 'Outcrop 3 x 1', rect(3, 1), 'stone', 1.6)]
for m in 'nesw':
    NATURAL.append((f'rock-stone-scree-{m}', f'Scree, L (empty {m})', lshape(m), 'stone', 1.2))
SHAPES += NATURAL


def seed_of(id):
    n = 0
    for ch in id:
        n = (n * 131 + ord(ch)) & 0xFFFFFF
    return n


# --- the solids ----------------------------------------------------------------------------------
class Rock(Solid):
    def __init__(self, planes, top, seed, walk):
        super().__init__(planes, 'stone')
        self.top, self.seed, self.walk = top, seed, walk


def rnd(seed, *k):
    return hashed(seed & 0xFFFF, (sum(k[i] * (31 ** i) for i in range(len(k))) + (seed >> 16)) & 0xFFFF) / 65535.0


def cell_solid(cells, i, j, kind, levels, seed):
    """One cell as a convex solid: vertical where it meets another cell, leaning in (and chamfered at the outer corners) where it is open, and a flat top or a broken peak."""
    s = seed + i * 977 + j * 1301
    h = levels
    walk = kind == 'ledge'
    lean = (lambda k: 0.015 + 0.035 * rnd(s, k)) if walk else (lambda k: 0.04 + 0.16 * rnd(s, k))
    planes = [((0, 0, -1), 0.0)]
    exposed = {}
    for k, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        exposed[(dx, dy)] = (i + dx, j + dy) not in cells
    x0, x1, y0, y1 = i, i + 1, j, j + 1
    out = 0.04 if walk else 0.02
    sides = (((1, 0), (x1 + out, 0.5, 0), (1, 0, 0)), ((-1, 0), (x0 - out, 0.5, 0), (-1, 0, 0)),
             ((0, 1), (0.5, y1 + out, 0), (0, 1, 0)), ((0, -1), (0.5, y0 - out, 0), (0, -1, 0)))
    for k, (d, pt, n) in enumerate(sides):
        if exposed[d]:
            t = lean(k)
            planes.append(plane((n[0], n[1], t), (pt[0] if n[0] else i + 0.5, pt[1] if n[1] else j + 0.5, 0)))
        else:
            planes.append(((float(n[0]), float(n[1]), 0.0), (x1 if n[0] > 0 else -x0 if n[0] < 0 else y1 if n[1] > 0 else -y0)))
    # chamfer the outer corners, a little for a ledge, more for a crag
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        if exposed[(sx, 0)] and exposed[(0, sy)]:
            c = (0.1 + 0.1 * rnd(s, 9 + sx + 2 * sy)) if walk else (0.2 + 0.2 * rnd(s, 9 + sx + 2 * sy))
            cx = x1 if sx > 0 else x0
            cy = y1 if sy > 0 else y0
            planes.append(plane((sx, sy, 0.1 + (0.05 if walk else 0.3)), (cx - sx * c / 2, cy - sy * c / 2, 0)))
    if walk:
        planes.append(((0.0, 0.0, 1.0), float(h)))
    else:
        px, py = i + 0.5 + (rnd(s, 20) - 0.5) * 0.4, j + 0.5 + (rnd(s, 21) - 0.5) * 0.4
        ph = h * (0.78 + 0.22 * rnd(s, 22))
        a0 = rnd(s, 23) * math.pi
        for k in range(5):
            th = a0 + k * 2 * math.pi / 5 + (rnd(s, 30 + k) - 0.5) * 0.9
            phi = math.radians(14 + 30 * rnd(s, 40 + k))
            planes.append(plane((math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)), (px, py, ph)))
        for k in range(5):                       # broken facets lower down: planes that take a corner off the rock
            th = rnd(s, 60 + k) * 2 * math.pi
            phi = math.radians(40 + 35 * rnd(s, 70 + k))
            r = 0.2 + 0.25 * rnd(s, 80 + k)
            zz = ph * (0.35 + 0.5 * rnd(s, 90 + k))
            planes.append(plane((math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)), (px + r * math.cos(th), py + r * math.sin(th), zz)))
        planes.append(((0.0, 0.0, 1.0), ph + 0.01))
        h = ph
    return Rock(planes, h, s, walk)


def build_solids(cells, kind, levels, seed):
    return [cell_solid(cells, i, j, kind, levels, seed) for i, j in sorted(cells)]


class Blob:
    """A lump: an ellipsoid turned about the vertical, widest at the ground (so it never undercuts), cut by flat facets (`planes`, each (outward normal, offset)) and,
    for a slab, cut flat at `cut`, a level top."""

    def __init__(self, c, r, yaw, seed, cut=None, top=None, planes=None):
        self.c, self.r, self.yaw, self.cut = c, r, yaw, cut
        self.seed = seed
        self.planes = planes or []
        self.top = top if top is not None else (cut if cut is not None else c[2] + r[2])
        self.walk = cut is not None
        self.natural = True
        self.cs, self.sn = math.cos(yaw), math.sin(yaw)

    def hit(self, origin):
        ox, oy, oz = origin[0] - self.c[0], origin[1] - self.c[1], origin[2] - self.c[2]
        cs, sn = self.cs, self.sn
        lx, ly = ox * cs + oy * sn, -ox * sn + oy * cs
        dx, dy = (cs + sn), (-sn + cs)
        rx, ry, rz = self.r
        o = (lx / rx, ly / ry, oz / rz)
        d = (dx / rx, dy / ry, 1.0 / rz)
        a = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
        b = o[0] * d[0] + o[1] * d[1] + o[2] * d[2]
        c = o[0] * o[0] + o[1] * o[1] + o[2] * o[2] - 1
        disc = b * b - a * c
        if disc <= 0:
            return None
        sq = math.sqrt(disc)
        t0, t1 = (-b - sq) / a, (-b + sq) / a
        face = None
        if self.cut is not None and self.cut < t1:
            t1, face = self.cut, (0.0, 0.0, 1.0)
        for n, off in self.planes:
            nv = n[0] + n[1] + n[2]
            na = n[0] * origin[0] + n[1] * origin[1] + n[2] * origin[2]
            t = (off - na) / nv if abs(nv) > 1e-9 else None
            if t is None:
                if na > off:
                    return None
                continue
            if nv > 0:
                if t < t1:
                    t1, face = t, n
            elif t > t0:
                t0 = t
        if t1 <= 0 or t0 >= t1:
            return None
        if face is not None:
            return t1, face
        px, py, pz = lx + t1 * dx, ly + t1 * dy, oz + t1
        gx, gy, gz = px / (rx * rx), py / (ry * ry), pz / (rz * rz)
        return t1, norm((gx * cs - gy * sn, gx * sn + gy * cs, gz))


def facets(s, c, r, count, lo=0.72, hi=0.92, elev=(8, 70), yaw=0.0):
    """Flat cuts into an ellipsoid at c with radii r: planes at random directions, each a fraction of the way out, so the lump gets sharp edges and corners."""
    out = []
    a0 = rnd(s, 200) * 2 * math.pi
    for k in range(count):
        th = a0 + k * 2 * math.pi / count + (rnd(s, 210 + k) - 0.5) * 0.9
        e = math.radians(elev[0] + (elev[1] - elev[0]) * rnd(s, 220 + k))
        n = norm((math.cos(e) * math.cos(th), math.cos(e) * math.sin(th), math.sin(e)))
        sup = math.sqrt((r[0] * n[0]) ** 2 + (r[1] * n[1]) ** 2 + (r[2] * n[2]) ** 2)
        f = lo + (hi - lo) * rnd(s, 230 + k)
        out.append((n, n[0] * c[0] + n[1] * c[1] + n[2] * c[2] + f * sup))
    return out


def build_slab(cells, levels, seed):
    """A lump for every cell, one on every edge between two cells and one on every corner inside, all cut at the same level, so the top is one flat piece. The footprint's
    open sides are cut flat and lean in a little going up, and its outer corners are chamfered, so the slab has straight faces and sharp corners, never a belly."""
    h = float(levels)
    # the open edges: (axis, sign, coord) -> plane, with spans along the edge
    edges = {}
    for i, j in cells:
        for ax, sg, di, dj in ((0, 1, 1, 0), (0, -1, -1, 0), (1, 1, 0, 1), (1, -1, 0, -1)):
            if (i + di, j + dj) in cells:
                continue
            coord = (i + 1 if sg > 0 else i) if ax == 0 else (j + 1 if sg > 0 else j)
            key = (ax, sg, coord)
            span = (j, j + 1) if ax == 0 else (i, i + 1)
            edges.setdefault(key, []).append(span)
    ep = {}
    for key, spans in edges.items():
        ax, sg, coord = key
        k = seed + ax * 7 + (sg + 1) * 13 + coord * 31
        lean = (0.02 + 0.08 * rnd(k, 1)) / h
        out = 0.03 * rnd(k, 2)
        n = (sg * 1.0 if ax == 0 else 0.0, sg * 1.0 if ax == 1 else 0.0, lean)
        pt = (coord + sg * out if ax == 0 else 0.0, coord + sg * out if ax == 1 else 0.0, 0.0)
        ep[key] = plane(n, pt)
    pts = {}
    for i, j in cells:
        pts[(i + 0.5, j + 0.5)] = ('cell', i, j)
        for dx, dy in ((1, 0), (0, 1)):
            if (i + dx, j + dy) in cells:
                pts[(i + 0.5 + dx / 2, j + 0.5 + dy / 2)] = ('edge', i, j)
        if all((i + a, j + b) in cells for a, b in ((1, 0), (0, 1), (1, 1))):
            pts[(i + 1.0, j + 1.0)] = ('corner', i, j)
    blobs = []
    for idx, ((x, y), (kind, i, j)) in enumerate(sorted(pts.items())):
        sd = seed + idx * 53
        r = 0.8 + 0.04 * rnd(sd, 1)
        planes = []
        for (ax, sg, coord), pl in ep.items():
            for lo, hi in edges[(ax, sg, coord)]:
                along = y if ax == 0 else x
                inside = (x < coord + 1e-6 if sg > 0 else x > coord - 1e-6) if ax == 0 else (y < coord + 1e-6 if sg > 0 else y > coord - 1e-6)
                if inside and lo - 0.01 <= along <= hi + 0.01:
                    planes.append(pl)
                    break
        if kind == 'cell':                                         # the outer corners: a chamfer
            for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if (i + sx, j) not in cells and (i, j + sy) not in cells:
                    c = 0.1 + 0.14 * rnd(sd, 9 + sx + 2 * sy)
                    cx = i + 1 if sx > 0 else i
                    cy = j + 1 if sy > 0 else j
                    planes.append(plane((sx, sy, 0.08), (cx - sx * c / 2, cy - sy * c / 2, 0)))
        if kind == 'cell':                                         # broken faces: cuts into the sides, and a chip off one top corner
            exposed = [k for k in range(4) if (i + ((1, -1, 0, 0)[k]), j + ((0, 0, 1, -1)[k])) not in cells]
            if exposed:
                for k in range(2):
                    th = rnd(sd, 300 + k) * 2 * math.pi
                    n = norm((math.cos(th) * 0.9, math.sin(th) * 0.9, 0.25 + 0.3 * rnd(sd, 310 + k)))
                    planes.append((n, n[0] * x + n[1] * y + n[2] * h + 0.5 + 0.14 * rnd(sd, 320 + k) - 0.3 * n[2] * min(h, 1.0) - 0.12 * n[2] * max(h - 1.0, 0.0)))
                th = (rnd(sd, 330) * 4 // 1) * math.pi / 2 + math.pi / 4
                n = norm((math.cos(th), math.sin(th), 0.9))
                planes.append((n, n[0] * x + n[1] * y + n[2] * h + 0.3 + 0.06 * rnd(sd, 331)))
        blobs.append(Blob((x, y, 0.0), (r, r, h * 2.6), rnd(sd, 5) * math.pi, sd, cut=h, planes=planes))
    return blobs


def build_stones(cells, levels, seed, id):
    blobs = []
    if id.endswith('standing'):                       # a menhir: a broad foot narrowing to a blunt, cut head
        sd = seed
        c, r = (0.5, 0.5, 0.0), (0.46, 0.36, levels * 1.25)
        blobs.append(Blob(c, r, 0.5, sd, top=levels, planes=facets(sd, c, r, 6, 0.8, 0.93, (6, 55)) + [((0.0, 0.0, 1.0), levels)]))
        c2, r2 = (0.76, 0.34, 0.0), (0.26, 0.2, 0.45)
        blobs.append(Blob(c2, r2, 1.2, sd + 2, top=0.45, planes=facets(sd + 2, c2, r2, 4, 0.8, 0.95, (10, 60))))
        c3, r3 = (0.26, 0.7, 0.0), (0.2, 0.16, 0.3)
        blobs.append(Blob(c3, r3, 2.0, sd + 4, top=0.3, planes=facets(sd + 4, c3, r3, 4, 0.8, 0.95, (10, 60))))
        return blobs
    for i, j in sorted(cells):
        sd = seed + i * 977 + j * 1301
        hk = levels * (0.6 + 0.4 * rnd(sd, 1))
        rxy = 0.4 + 0.14 * rnd(sd, 2)
        cx, cy = i + 0.5 + (rnd(sd, 3) - 0.5) * 0.2, j + 0.5 + (rnd(sd, 4) - 0.5) * 0.2
        c, r = (cx, cy, 0.0), (rxy, rxy * (0.75 + 0.3 * rnd(sd, 5)), hk * 1.12)
        blobs.append(Blob(c, r, rnd(sd, 6) * math.pi, sd, top=hk, planes=facets(sd, c, r, 6, 0.7, 0.9, (10, 72))))
        for k in range(2):                               # lumps leaning against it, lower
            ang = rnd(sd, 10 + k) * 2 * math.pi
            hs = hk * (0.35 + 0.35 * rnd(sd, 12 + k))
            rr = 0.22 + 0.12 * rnd(sd, 14 + k)
            c2, r2 = (cx + 0.33 * math.cos(ang), cy + 0.33 * math.sin(ang), 0.0), (rr, rr * (0.75 + 0.3 * rnd(sd, 16 + k)), hs * 1.1)
            blobs.append(Blob(c2, r2, rnd(sd, 18 + k) * math.pi, sd + 7 + k, top=hs, planes=facets(sd + 7 + k, c2, r2, 4, 0.7, 0.9, (10, 72))))
    return blobs


DARKER = {'r': 'q', 'q': 'p', 'p': 'l', 'l': 'k', 'k': 'w', 'w': 'w', 'z': 'A', 'A': 'B', 'B': 's', 's': 's'}


def paint_natural(b, n, P):
    x, y, z = P
    cell = 3.0
    fx, fy, fz = (int(math.floor(v * LEVEL / cell)) for v in P)
    amp = 0.1 if (b.cut is not None and n[2] > 0.99) else 0.2
    nx = n[0] + (hashed(fx & 0xFFFF, fy & 0xFFFF, (fz + 5) & 0xFF) / 65535.0 - 0.5) * amp * 2
    ny = n[1] + (hashed(fy & 0xFFFF, fz & 0xFFFF, (fx + 9) & 0xFF) / 65535.0 - 0.5) * amp * 2
    nz = n[2] + (hashed(fz & 0xFFFF, fx & 0xFFFF, (fy + 3) & 0xFF) / 65535.0 - 0.5) * amp
    m = norm((nx, ny, nz))
    lum = m[0] * LIGHT[0] + m[1] * LIGHT[1] + m[2] * LIGHT[2]
    ix, iy, iz = (int(math.floor(v * LEVEL)) for v in P)
    r = hashed(ix & 0xFFFF, iy & 0xFFFF, (iz + b.seed) & 0xFFFF) / 65535.0
    lum += (r - 0.5) * 0.06
    if z < 0.22:
        lum -= (0.22 - z) * 0.9                                                   # shadow where the stone meets the ground
    if hashed(ix, iy, iz + 41) % 53 == 0:
        lum -= 0.3                                                                # a pit
    mv = hashed(fx & 0xFFFF, fy & 0xFFFF, (fz + b.seed) & 0xFF) / 65535.0
    if m[2] > 0.5 and mv > (0.9 if b.cut is not None and n[2] > 0.99 else 0.8):
        return ramp_of(MOSS, lum)
    if z < 0.12 and r > 0.8:
        return ramp_of(MOSS, lum - 0.1)
    return ramp_of(RAMP, lum)


# --- paint --------------------------------------------------------------------------------------
def ramp_of(table, v):
    for lo, role in table:
        if v >= lo:
            return role
    return table[-1][1]


def paint(rock, n, P):
    x, y, z = P
    nz = n[2]
    lum = n[0] * LIGHT[0] + n[1] * LIGHT[1] + nz * LIGHT[2]
    if nz > 0.93:
        a, b = int(math.floor(x * LEVEL)), int(math.floor(y * LEVEL))
        wall = False
    elif nz > 0.4:
        a, b = int(math.floor(x * LEVEL)), int(math.floor(y * LEVEL + z * 6))
        wall = False
    else:
        hn = math.hypot(n[0], n[1]) or 1
        along = (x * -n[1] + y * n[0]) / hn
        a, b = int(math.floor(along * LEVEL)), int(math.floor(z * LEVEL))
        wall = True
    r = hashed(a & 0xFFFF, b & 0xFFFF, rock.seed & 0xFFF) / 65535.0
    lum += (r - 0.5) * (0.07 if wall else (0.05 if nz > 0.93 else 0.12))
    if wall:
        # strata: courses of stone 4 to 7 pixels thick, each with its own tone, and a dark seam under some
        course = (b + hashed(a // 11, 5, rock.seed & 0xFF) % 4) // 5
        lum += (hashed(course, a // 9, 3 + (rock.seed & 0xFF)) / 65535.0 - 0.5) * 0.24
        if (b + hashed(a // 11, 5, rock.seed & 0xFF) % 4) % 5 == 0 and hashed(a // 4, b, 9) % 3:
            lum -= 0.2
        if hashed(a // 7, b // 5, 31 + (rock.seed & 0xFF)) % 17 == 0 and (a + b) % 3 == 0:
            lum -= 0.2                                  # a short crack
    m = hashed(a // 3, b // 3, 77 + (rock.seed & 0xFF)) / 65535.0
    if nz > 0.4:
        if m > (0.86 if rock.walk and nz > 0.93 else 0.8) or (hashed(a, b, 5) % 61 == 0 and not (rock.walk and nz > 0.93)):
            return ramp_of(MOSS, lum)
    else:
        depth = (rock.top - z) * LEVEL
        length = 2 + hashed(a // 2, 1, 13 + (rock.seed & 0xFF)) % 8
        if depth < length and hashed(a // 2, 4, rock.seed & 0xFF) % 3 == 0 and nz >= 0:
            return ramp_of(MOSS, lum - 0.05)
    return ramp_of(RAMP, lum)


# --- the picture --------------------------------------------------------------------------------
def render(cells, kind, levels, seed, id=''):
    """(rows, anchor, (fx, fy)) for the rock: size 16 (fx + fy) + 2 margin across."""
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    if kind == 'slab':
        solids = build_slab(cells, levels, seed)
    elif kind == 'stone':
        solids = build_stones(cells, levels, seed, id)
    else:
        solids = build_solids(cells, kind, levels, seed)
    zmax = max(s.top for s in solids)
    oy = int(math.ceil(LEVEL * zmax)) + 4
    w = 16 * (fx + fy) + 2 * MARGIN
    h = 8 * (fx + fy) + oy + 2
    ox = 16 * fy + MARGIN
    grid = [['.'] * w for _ in range(h)]
    who = [[None] * w for _ in range(h)]
    depth = [[0.0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            sx, sy = px + 0.5, py + 0.5
            a, b = (sx - ox) / 16.0, (sy - oy) / 8.0
            origin = ((a + b) / 2, (b - a) / 2, 0.0)
            best = None
            for k, s in enumerate(solids):
                got = s.hit(origin)
                if got and (best is None or got[0] > best[0] + 1e-9):
                    best = (got[0], got[1], s, k)
            if best is None:
                continue
            t, n, s, k = best
            P = (origin[0] + t, origin[1] + t, t)
            grid[py][px] = paint_natural(s, n, P) if getattr(s, 'natural', False) else paint(s, n, P)
            who[py][px] = k
            depth[py][px] = P[0] + P[1] + P[2]
    if kind in ('slab', 'stone'):                                  # a dark seam where one lump stands in front of another
        for y in range(h):
            for x in range(w):
                if who[y][x] is None:
                    continue
                for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and who[ny][nx] is not None and who[ny][nx] != who[y][x] and depth[y][x] < depth[ny][nx] - (0.32 if kind == 'slab' else 0.12):
                        grid[y][x] = (DARKER[grid[y][x]] if kind == 'slab' else DARKER[DARKER[grid[y][x]]]) if grid[y][x] in DARKER else grid[y][x]
                        break
    out = [r[:] for r in grid]
    for y in range(h):
        for x in range(w):
            if grid[y][x] != '.':
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] != '.':
                    out[y][x] = 'O'
                    break
    anchor = (8 * (fx + fy) + MARGIN, oy + 4 * (fx + fy))
    return [''.join(r) for r in out], anchor, (fx, fy)


_CACHE = {}


def rock_rows(id):
    if id not in _CACHE:
        for sid, label, cells, kind, levels in SHAPES:
            if sid == id:
                _CACHE[id] = render(cells, kind, levels, seed_of(id), id)
    return _CACHE[id]


def top_cover(id, cells, kind, levels):
    """For a rock with a flat top: the share of each cell's area (8 x 8 samples) where the top is the flat level plane, as {(i, j): 0..1}."""
    seed = seed_of(id)
    solids = build_slab(cells, levels, seed) if kind == 'slab' else build_solids(cells, kind, levels, seed)
    h, n = float(levels), 8
    out = {}
    for i, j in sorted(cells):
        got = 0
        for a in range(n):
            for b in range(n):
                x, y = i + (a + 0.5) / n, j + (b + 0.5) / n
                best = None
                for s in solids:
                    g = s.hit((x - h, y - h, 0.0))
                    if g and (best is None or g[0] > best[0]):
                        best = g
                got += bool(best and abs(best[0] - h) < 1e-6 and best[1][2] > 0.99)
        out[(i, j)] = got / (n * n)
    return out


WALK_MIN = 0.6           # a rock is walkable when every one of its cells has at least this much flat top


def walk_info(id, cells, kind, levels):
    """(walkable, {cell: cover}) for a rock: a ledge or slab whose every cell has at least WALK_MIN flat top; a crag or stone is never walkable."""
    if kind not in WALK:
        return False, {}
    cover = top_cover(id, cells, kind, levels)
    return min(cover.values()) >= WALK_MIN, cover


def build_assets():
    out = []
    for sid, label, cells, kind, levels in SHAPES:
        rows, anchor, (fx, fy) = rock_rows(sid)
        make = family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)
        walkable, cover = walk_info(sid, cells, kind, levels)
        extra = {'top_cover': {f'{i},{j}': round(v, 2) for (i, j), v in cover.items()}} if cover else {}
        out.append(make(sid, label, 'still', [rows], footprint={'size': [fx, fy], 'cells': [list(c) for c in sorted(cells)]},
                        walkable=walkable, levels=levels, style=STYLE[kind], **extra))
    return out


def write_package(folder):
    rocks = {}
    for sid, label, cells, kind, levels in SHAPES:
        walkable, cover = walk_info(sid, cells, kind, levels)
        rocks[sid] = {'label': label, 'file': f'{sid}.png', 'style': STYLE[kind], 'size': [max(c[0] for c in cells) + 1, max(c[1] for c in cells) + 1],
                      'cells': [list(c) for c in sorted(cells)], 'walkable': walkable, 'levels': levels,
                      **({'top_cover': {f'{i},{j}': round(v, 2) for (i, j), v in cover.items()}} if cover else {})}
    write_json(folder, 'rocks.json', 'The rock kit in this folder. See README.md beside this file.',
               {'level': LEVEL, 'walk_min': WALK_MIN, 'margin': MARGIN, 'rocks': rocks})


# --- preview ------------------------------------------------------------------------------------
def preview(path, scale=2, only=None):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    tiles = []
    for sid, label, cells, kind, levels in (NATURAL if only == 'natural' else [x for x in SHAPES if x not in NATURAL] if only == 'blocks' else SHAPES):
        rows, (ax, ay), (fx, fy) = rock_rows(sid)
        im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c != '.':
                    im.putpixel((x, y), rgb[c] + (255,))
        tiles.append((sid, label, cells, kind, levels, im, (ax, ay), (fx, fy)))
    bg = (30, 34, 56, 255)
    colw = 3 * 16 * 2 * scale // 2 + 70
    margin, x, y, rowh = 14, 14, 14, 0
    W = 1500
    placed = []
    for t in tiles:
        im = t[5]
        w, h = im.width * scale, im.height * scale + 26
        if x + w > W - margin:
            x, y, rowh = margin, y + rowh + 14, 0
        placed.append((t, x, y))
        x += w + 18
        rowh = max(rowh, h)
    sheet = Image.new('RGBA', (W, y + rowh + 20), bg)
    d = ImageDraw.Draw(sheet)
    for (sid, label, cells, kind, levels, im, (ax, ay), (fx, fy)), x, y in placed:
        top = y + 14
        sheet.alpha_composite(Image.new('RGBA', (im.width * scale, im.height * scale), (0, 0, 0, 0)), (x, top))
        # the footprint's cells on the ground, drawn under the rock
        ox = 16 * fy + MARGIN
        oy = ay - 4 * (fx + fy)
        for i, j in cells:
            pts = [(ox + 16 * (i - j), oy + 8 * (i + j)), (ox + 16 * (i + 1 - j), oy + 8 * (i + 1 + j)), (ox + 16 * (i + 1 - j - 1), oy + 8 * (i + 1 + j + 1)), (ox + 16 * (i - j - 1), oy + 8 * (i + j + 1))]
            pts = [(ox + 16 * (X - Y), oy + 8 * (X + Y)) for X, Y in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            d.polygon([(x + p * scale, top + q * scale) for p, q in pts], fill=(70, 110, 70, 255) if kind in WALK else (90, 70, 70, 255), outline=(0, 0, 0, 90))
        sheet.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, top))
        d.text((x, y), f"{sid.replace('rock-', '')} {'WALK' if kind in WALK else ''}", fill=(230, 220, 200, 255))
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--set', choices=('blocks', 'natural'), help='only the blocky set or only the natural one in the preview')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, only=args.set)
        print('the rocks ->', args.preview)


if __name__ == '__main__':
    main()
