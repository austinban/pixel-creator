#!/usr/bin/env python3
"""A graveyard and a place of ritual for the Gravemoor map: gravestones, cairns, bones, an obelisk, a rune altar and plinth, spirit lanterns, an iron fence and gate, and ritual circles on the ground.

Each standing thing is a small 3D model of boxes, posts and rounded lumps in the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level, the right face lit), in the stone ramp with
a little moss and the shared palette, with the one-pixel outline. They have no front: one picture each, except where a piece runs along an axis (the fence and the gate, in x and y).

    gravestones   round-topped, a cross, one leaning, one broken with its top lying beside it
    cairns        a tall stack and a small one
    bones         a skull among bones, a rib cage, and a scatter
    obelisk       a tall four-sided stone with glowing runes on the two faces the camera sees
    rune altar    a stone table (2 x 1 and 1 x 2) with runes cut in its flat top, which can be stood on, and a rune plinth with a crystal
    lanterns      a spirit-lantern post and a low stone lantern, each four frames of flicker and drifting glow
    iron          a graveyard fence section and a gate, each running along x or along y, joining at the cell's edges
    circles       RITUAL CIRCLES: glowing flat decals on the ground, 2 x 2, 3 x 3 and 4 x 4 cells, with a ring of runes and a star

    python3 tools/make_graveyard.py --preview previews/graveyard.png     every piece at 2x, the lanterns as strips
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
import propkit as pk  # noqa: E402
from propkit import Ellipsoid, Frustum, Poly, box, taper, lean_slab, cut_top, rnd, size_for  # noqa: E402

FOLDER = 'graveyard'
CATEGORY = 'Graveyard'
WALK_MIN = 0.6
FPS = 6
STONE = ('q', 'p', 'l', 'k')
DARK = ('p', 'l', 'k', 'w')
IRON = ('l', 'k', 'w', 'x')
BONE = ('t', 'C', 'c', 'g')
GLOW = 'o'


# --- marks: the painted detail on a body -----------------------------------------------------
def stone_mark(moss=0.0):
    def mark(body, p, n, step, px, py):
        if n[2] > 0.5 and moss and pk.hashed(px // 2, py // 2, 7) / 65535.0 > 1 - moss:
            return 'z' if step == 0 else 'A'
        if step < 3 and pk.hashed(px, py, 3) % 23 == 0:
            return body.mat[step + 1]
        if step > 0 and pk.hashed(px, py, 5) % 31 == 0:
            return body.mat[step - 1]
        return None
    return mark


GLYPHS = [['010', '111', '010', '010', '010'], ['101', '101', '111', '001', '001'], ['111', '001', '010', '100', '111'],
          ['110', '011', '110', '011', '110'], ['010', '101', '111', '101', '010'], ['100', '111', '010', '111', '001']]


def runes(spots, moss=0.0, role=GLOW):
    """Glowing glyphs (3 x 5 pixels) cut into the faces the camera sees: spots are (face 'R' or 'L', along, z of the glyph's top, glyph number), where along is measured to the right on the screen."""
    base = stone_mark(moss)

    def mark(body, p, n, step, px, py):
        for face, a0, z0, g in spots:
            if face == 'R' and n[0] > 0.7:
                u = -p[1]
            elif face == 'L' and n[1] > 0.7:
                u = p[0]
            else:
                continue
            a = int(math.floor(u * 16)) - int(round(a0 * 16))
            b = int(round(z0 * 16)) - int(math.floor(p[2] * 16)) - 1
            if 0 <= a < 3 and 0 <= b < 5 and GLYPHS[g][b][a] == '1':
                return role
        return base(body, p, n, step, px, py)
    return mark


def engrave(face, a0, a1, z0, z1, shape='cross'):
    """A carving, a shade darker than the stone, cut into a broad face: a cross, or a plain panel's border."""
    base = stone_mark(0.1)

    def mark(body, p, n, step, px, py):
        if face == 'R' and n[0] > 0.7:
            u = -p[1]
        elif face == 'L' and n[1] > 0.7:
            u = p[0]
        else:
            u = None
        if u is not None and a0 <= u <= a1 and z0 <= p[2] <= z1:
            um, zm = (a0 + a1) / 2, (z0 + z1) / 2
            if shape == 'cross' and (abs(u - um) < 0.035 or (abs(p[2] - (z0 + (z1 - z0) * 0.62)) < 0.035 and abs(u - um) < (a1 - a0) / 2)):
                return body.mat[min(3, step + 2)]
        return base(body, p, n, step, px, py)
    return mark


def skull_mark(c, r):
    def mark(body, p, n, step, px, py):
        qx, qy, qz = (p[0] - c[0]) / r, (p[1] - c[1]) / r, (p[2] - c[2]) / r
        if qx > 0.45 and 0.0 < qz < 0.5 and (abs(qy - 0.42) < 0.24 or abs(qy + 0.42) < 0.24):
            return 'x'
        if qx > 0.7 and abs(qy) < 0.12 and -0.3 < qz < 0.02:
            return 'x'
        if step < 3 and pk.hashed(px, py, 4) % 19 == 0:
            return body.mat[step + 1]
        return None
    return mark


# --- gravestones -------------------------------------------------------------------------------
def gravestone_round():
    return [box(-0.3, 0.3, -0.3, 0.3, 0, 0.1, DARK, mark=stone_mark(0.25)),
            box(-0.07, 0.07, -0.24, 0.24, 0.1, 0.72, STONE, mark=engrave('R', -0.2, 0.2, 0.25, 0.68)),
            Ellipsoid(STONE, (0, 0, 0.72), (0.07, 0.24, 0.24), lo=0.72, mark=stone_mark(0.2))], 1.1


def gravestone_cross():
    return [box(-0.28, 0.28, -0.28, 0.28, 0, 0.14, DARK, mark=stone_mark(0.3)),
            box(-0.085, 0.085, -0.085, 0.085, 0.14, 1.08, STONE, mark=stone_mark(0.2)),
            box(-0.085, 0.085, -0.3, 0.3, 0.64, 0.84, STONE, mark=stone_mark(0.2))], 1.25


def gravestone_leaning():
    return [Ellipsoid(('A', 'B', 's', 'D'), (0, 0, 0.0), (0.33, 0.33, 0.12), lo=0.0, mark=stone_mark(0.0)),
            lean_slab(0, 0, 0.05, 0.98, 0.065, 0.25, -0.24, STONE, lean_axis='y', mark=engrave('R', -0.2, 0.2, 0.25, 0.9)),
            Ellipsoid(STONE, (0.0, 0.34, 0.07), (0.1, 0.1, 0.07), lo=0.0, mark=stone_mark(0.4))], 1.15


def gravestone_broken():
    top = cut_top(box(-0.07, 0.07, -0.26, 0.26, 0.06, 0.78, STONE, mark=stone_mark(0.35)), 0.1, 0.8, 1.0, 0.0, 0.0, 0.52)
    return [box(-0.3, 0.3, -0.3, 0.3, 0, 0.08, DARK, mark=stone_mark(0.3)), top,
            box(0.12, 0.34, -0.12, 0.2, 0.0, 0.1, STONE, mark=stone_mark(0.4)),          # the piece that fell
            Ellipsoid(STONE, (0.3, 0.3, 0.05), (0.09, 0.07, 0.05), lo=0.0, mark=stone_mark(0.2)),
            Ellipsoid(STONE, (-0.28, -0.3, 0.04), (0.07, 0.07, 0.04), lo=0.0, mark=stone_mark(0.2))], 0.95


# --- cairns -----------------------------------------------------------------------------------
def cairn(tall):
    rs = (0.4, 0.33, 0.27, 0.2, 0.14, 0.09) if tall else (0.3, 0.22, 0.14)
    out = []
    z = 0.0
    for k, r in enumerate(rs):
        rz = 0.13 if tall else 0.11
        ox, oy = 0.05 * (rnd(77, k) - 0.5) * 2, 0.05 * (rnd(78, k) - 0.5) * 2
        out.append(Ellipsoid(STONE if k % 2 else DARK, (ox, oy, z + rz * 0.6), (r * 1.1, r * (0.9 + 0.2 * rnd(79, k)), rz), lo=z - 0.02, mark=stone_mark(0.3)))
        z += rz * 1.3
    out.append(Ellipsoid(STONE, (0.34, 0.3, 0.05), (0.09, 0.08, 0.05), lo=0.0, mark=stone_mark(0.1)))
    return out, z + 0.2


# --- bones ------------------------------------------------------------------------------------
def bone(x, y, z, rx, ry, rz):
    return Ellipsoid(BONE, (x, y, z), (rx, ry, rz), lo=0.0, mark='speckle')


def bones_skull():
    c = (0.0, 0.02, 0.2)
    out = [Ellipsoid(BONE, c, (0.19, 0.17, 0.17), lo=0.0, mark=skull_mark(c, 0.19)),
           Ellipsoid(BONE, (0.1, 0.02, 0.08), (0.1, 0.1, 0.07), lo=0.0, mark=skull_mark((0.1, 0.02, 0.08), 0.1)),
           bone(-0.2, 0.3, 0.05, 0.3, 0.045, 0.045), bone(0.25, -0.3, 0.05, 0.045, 0.3, 0.045), bone(-0.36, -0.22, 0.04, 0.2, 0.04, 0.04),
           bone(0.05, 0.42, 0.04, 0.04, 0.17, 0.04), bone(0.38, 0.2, 0.04, 0.12, 0.035, 0.035), bone(-0.1, -0.38, 0.035, 0.1, 0.03, 0.03)]
    for bx, by in ((-0.42, 0.3), (0.45, -0.3), (-0.5, -0.22), (0.2, 0.46)):
        out.append(Ellipsoid(BONE, (bx, by, 0.05), (0.06, 0.06, 0.05), lo=0.0, mark='speckle'))
    return out, 0.6


def bones_ribs():
    out = [bone(0.0, 0.0, 0.07, 0.05, 0.46, 0.05)]
    for k in range(5):
        y = -0.32 + k * 0.16
        rr = 0.3 - 0.03 * abs(k - 2)
        for s in range(11):
            a = math.pi * s / 10
            out.append(Ellipsoid(BONE, (rr * math.cos(a), y, 0.06 + rr * 0.75 * math.sin(a)), (0.055, 0.045, 0.055), lo=0.0, mark='speckle'))
    out += [bone(0.42, -0.4, 0.04, 0.2, 0.04, 0.04), bone(-0.4, 0.4, 0.04, 0.04, 0.18, 0.04)]
    return out, 0.7


def bones_scatter():
    out = []
    for k in range(9):
        x, y = (rnd(41, k) - 0.5) * 0.9, (rnd(42, k) - 0.5) * 0.9
        along = rnd(43, k) > 0.5
        ln = 0.1 + 0.2 * rnd(44, k)
        out.append(bone(x, y, 0.04, ln if along else 0.04, 0.04 if along else ln, 0.04))
    out.append(Ellipsoid(BONE, (-0.2, 0.2, 0.1), (0.1, 0.1, 0.09), lo=0.0, mark=skull_mark((-0.2, 0.2, 0.1), 0.1)))
    return out, 0.4


# --- obelisk, altar, plinth ------------------------------------------------------------------
def obelisk():
    spots = [(f, a, z, g) for f in ('R', 'L') for a, z, g in ((-0.045, 1.95, 0), (-0.045, 1.6, 4), (-0.045, 1.25, 2), (-0.045, 0.9, 5), (-0.045, 0.55, 1))]
    # the shaft narrows from 0.24 to 0.15; runes sit on its middle, so give a face its own along origin: R faces are measured in -y, L in x
    spots = [(f, -0.045 if f == 'L' else -0.045, z, g) for f, a, z, g in spots]
    mark = runes(spots, moss=0.18)
    return [box(-0.42, 0.42, -0.42, 0.42, 0, 0.16, DARK, mark=stone_mark(0.3)), box(-0.33, 0.33, -0.33, 0.33, 0.16, 0.3, DARK, mark=stone_mark(0.3)),
            taper(0, 0, 0.3, 2.3, 0.24, 0.24, 0.15, 0.15, DARK, mark=mark), taper(0, 0, 2.3, 2.85, 0.15, 0.15, 0.01, 0.01, STONE, mark=stone_mark(0.0))], 2.95


def altar(along_x):
    fx, fy = (2, 1) if along_x else (1, 2)
    hx, hy = (1.0, 0.5) if along_x else (0.5, 1.0)
    cx = cy = 0.0

    def top_mark(body, p, n, step, px, py):
        if n[2] > 0.9:
            # a long channel and a ring with a spoke, glowing, cut into the top
            u, v = (p[0], p[1]) if along_x else (p[1], p[0])
            r = math.hypot(u, v)
            if abs(r - 0.2) < 0.03 or (abs(v) < 0.022 and 0.2 < abs(u) < 0.78) or (abs(u) < 0.022 and abs(v) < 0.2) or (abs(abs(u) - 0.78) < 0.03 and abs(v) < 0.16):
                return GLOW
        return stone_mark(0.1)(body, p, n, step, px, py)
    runes_front = runes([('R', -0.05, 0.62, 3)], moss=0.15)
    base = box(-hx, hx, -hy, hy, 0.0, 0.22, DARK, mark=stone_mark(0.25))
    slab = box(-hx + 0.08, hx - 0.08, -hy + 0.06, hy - 0.06, 0.22, 1.0, STONE, mark=top_mark)
    if along_x:
        slab = Poly(slab.solid.planes, STONE, c=(0, 0), mark=lambda b, p, n, s, px, py: top_mark(b, p, n, s, px, py) if n[2] > 0.9 else runes([('L', -0.05, 0.7, 3), ('L', 0.3, 0.7, 1)], moss=0.15)(b, p, n, s, px, py))
    else:
        slab = Poly(slab.solid.planes, STONE, c=(0, 0), mark=lambda b, p, n, s, px, py: top_mark(b, p, n, s, px, py) if n[2] > 0.9 else runes([('R', -0.05, 0.7, 3), ('R', 0.3, 0.7, 1)], moss=0.15)(b, p, n, s, px, py))
    return [base, slab], 1.1, (fx, fy)


def plinth():
    crystal = ('r', 'o', 'o', 'q')
    return [box(-0.3, 0.3, -0.3, 0.3, 0, 0.14, DARK, mark=stone_mark(0.25)),
            taper(0, 0, 0.14, 0.78, 0.22, 0.22, 0.17, 0.17, STONE, mark=runes([('R', -0.045, 0.62, 5), ('L', -0.045, 0.62, 2)], moss=0.15)),
            Frustum(DARK, (0, 0), 0.78, 1.0, 0.18, 0.3, mark=stone_mark(0.1)),
            Frustum(('x', 'x', 'w', 'x'), (0, 0), 0.92, 1.01, 0.22, 0.22),
            taper(0, 0, 1.01, 1.55, 0.1, 0.1, 0.012, 0.012, ('r', 'o', 'o', 'q'), glow=True)], 1.65


# --- lanterns (four frames) --------------------------------------------------------------------
LAMP_FRAMES = 4
GLOWS = [('r', 'o'), ('t', 'r'), ('r', 'o'), ('o', 'q')]


def lantern_post(frame):
    g = GLOWS[frame]
    out = [Ellipsoid(IRON, (0, 0, 0.0), (0.16, 0.16, 0.14), lo=0.0, mark=stone_mark(0)),
           Frustum(IRON, (0, 0), 0.0, 1.55, 0.075, 0.055, mark='speckle'),
           box(-0.15, 0.15, -0.15, 0.15, 1.55, 1.62, IRON),
           box(-0.095, 0.095, -0.095, 0.095, 1.62, 1.98, g + g, glow=True),
           taper(0, 0, 1.98, 2.22, 0.17, 0.17, 0.02, 0.02, IRON)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(box(sx * 0.13 - 0.03, sx * 0.13 + 0.03, sy * 0.13 - 0.03, sy * 0.13 + 0.03, 1.62, 1.98, IRON))
    return out, 2.3


def lantern_stone(frame):
    g = GLOWS[frame]

    def window(body, p, n, step, px, py):
        if 0.57 < p[2] < 0.82:
            if n[0] > 0.7 and abs(p[1]) < 0.07:
                return g[0] if step < 2 else g[1]
            if n[1] > 0.7 and abs(p[0]) < 0.07:
                return g[0] if step < 2 else g[1]
        return stone_mark(0.2)(body, p, n, step, px, py)
    return [box(-0.2, 0.2, -0.2, 0.2, 0, 0.1, DARK, mark=stone_mark(0.3)), taper(0, 0, 0.1, 0.5, 0.1, 0.1, 0.09, 0.09, STONE, mark=stone_mark(0.2)),
            box(-0.2, 0.2, -0.2, 0.2, 0.5, 0.9, STONE, mark=window), taper(0, 0, 0.9, 1.2, 0.3, 0.3, 0.03, 0.03, DARK, mark=stone_mark(0.2))], 1.3


def halo(rows, frame, centre, radius, pool):
    """The light a lantern throws: a dithered halo in the air round its flame and a dimmer pool on the ground, drawn only where nothing else is, then the wisps."""
    grid = [list(r) for r in rows]
    h, w = len(grid), len(grid[0])
    cx, cy = centre
    r = radius + (0, 1, 0, -1)[frame]
    for y in range(h):
        for x in range(w):
            if grid[y][x] != '.':
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < r and (x + y + frame) % 2 == 0 and (x + 2 * frame) % 2 == 0 and d > r * 0.45:
                grid[y][x] = 'q' if d < r * 0.78 else 's'
            gx, gy = (x + 0.5 - pool[0]) / pool[2], (y + 0.5 - pool[1]) / (pool[2] / 2)
            if grid[y][x] == '.' and gx * gx + gy * gy < 1 and (x + 2 * y + frame) % 4 == 0:
                grid[y][x] = 's' if gx * gx + gy * gy < 0.5 else 'D'
    for k in range(2):                                    # a wisp of spirit drifting up
        wx = cx + (-1) ** k * (3 + 2 * math.sin(frame + k * 2)) + (frame - 1.5) * (0.8 if k else -0.8)
        wy = cy - 3 - ((frame + 2 * k) % 4) * 2.5
        for dx, dy, role in ((0, 0, 'r'), (0, 1, 'o')):
            x, y = int(wx) + dx, int(wy) + dy
            if 0 <= x < w and 0 <= y < h and grid[y][x] == '.':
                grid[y][x] = role
    return pk.add_outline([''.join(r) for r in grid])


def lantern_rows(kind, frame):
    if kind == 'post':
        bodies, tall = lantern_post(frame)
        w, h, anchor = size_for(1, 1, tall, pad=14)
        rows = pk.render(bodies, w, h, anchor, outline=False)
        return halo(rows, frame, (anchor[0], anchor[1] - 1.8 * 16), 11, (anchor[0], anchor[1], 14)), anchor
    bodies, tall = lantern_stone(frame)
    w, h, anchor = size_for(1, 1, tall, pad=14)
    rows = pk.render(bodies, w, h, anchor, outline=False)
    return halo(rows, frame, (anchor[0], anchor[1] - 0.72 * 16), 9, (anchor[0], anchor[1], 12)), anchor


# --- iron: fence and gate ------------------------------------------------------------------------
def bar(x, y, h, along_x, r=0.05):
    return Frustum(IRON, (x, y), 0.0, h, r, r * 0.8, mark=None)


def fence(along_x):
    out = []
    for k in range(7):
        t = -0.45 + k * 0.15
        x, y = (t, 0.0) if along_x else (0.0, t)
        out.append(bar(x, y, 0.92, along_x))
        out.append(Ellipsoid(IRON, (x, y, 0.92), (0.05, 0.05, 0.1), lo=0.9))
    out.append(box(-0.5, 0.5, -0.03, 0.03, 0.2, 0.27, IRON) if along_x else box(-0.03, 0.03, -0.5, 0.5, 0.2, 0.27, IRON))
    out.append(box(-0.5, 0.5, -0.03, 0.03, 0.66, 0.73, IRON) if along_x else box(-0.03, 0.03, -0.5, 0.5, 0.66, 0.73, IRON))
    return out, 1.1


def gate(along_x):
    out = []

    def at(t, s=0.0):
        return (t, s) if along_x else (s, t)

    for sgn in (-1, 1):                                        # the stone pillars, with a capstone
        lo, hi = (0.34, 0.5) if sgn > 0 else (-0.5, -0.34)
        out.append(box(lo, hi, -0.1, 0.1, 0.0, 1.35, STONE, mark=stone_mark(0.2)) if along_x else box(-0.1, 0.1, lo, hi, 0.0, 1.35, STONE, mark=stone_mark(0.2)))
        cx, cy = at((lo + hi) / 2)
        out.append(Ellipsoid(STONE, (cx, cy, 1.35), (0.11, 0.11, 0.12), lo=1.34, mark=stone_mark(0.1)))
    for k in range(5):                                         # the iron doors, tall in the middle
        t = -0.28 + k * 0.14
        top = 0.8 + 0.3 * (1 - (t / 0.34) ** 2)
        x, y = at(t)
        out.append(Frustum(IRON, (x, y), 0.0, top, 0.05, 0.04))
        out.append(Ellipsoid(IRON, (x, y, top), (0.05, 0.05, 0.09), lo=top - 0.02))
    out.append(box(-0.34, 0.34, -0.03, 0.03, 0.22, 0.28, IRON) if along_x else box(-0.03, 0.03, -0.34, 0.34, 0.22, 0.28, IRON))
    out.append(box(-0.34, 0.34, -0.03, 0.03, 0.62, 0.68, IRON) if along_x else box(-0.03, 0.03, -0.34, 0.34, 0.62, 0.68, IRON))
    return out, 1.6


# --- ritual circles -----------------------------------------------------------------------------
RUNE_PAT = [lambda u, v: abs(u - 0.5) < 0.16, lambda u, v: math.hypot(u - 0.5, v - 0.5) < 0.22, lambda u, v: abs(u - 0.5) > 0.2 and abs(u - 0.5) < 0.4,
            lambda u, v: abs(u - v) < 0.16, lambda u, v: abs((u - 0.5) * 2 - (v - 0.5) * 2 * (1 if v < 0.5 else -1)) < 0.3 and v > 0.1, lambda u, v: v < 0.28 or abs(u - 0.5) < 0.12]


def circle_painter(n):
    w, h = 32 * n, 16 * n
    ax, ay = w // 2, h // 2
    Rx, Ry = 16 * math.sqrt(2) * (n / 2) * 0.97, 8 * math.sqrt(2) * (n / 2) * 0.97
    nsec = (12, 18, 24)[n - 2]
    star_pts = 5 if n == 2 else 6

    def rho_of(dx, dy):
        return math.hypot(dx / Rx, dy / Ry)

    def near_ring(dx, dy, r0, half):
        rho = rho_of(dx, dy)
        if rho < 1e-6:
            return False
        grad = math.hypot(dx / (Rx * Rx), dy / (Ry * Ry)) / rho
        return abs(rho - r0) / grad <= half

    segs = []
    if star_pts == 5:
        pts = [(ax + Rx * 0.7 * math.cos(-math.pi / 2 + 2 * math.pi * k / 5), ay + Ry * 0.7 * math.sin(-math.pi / 2 + 2 * math.pi * k / 5)) for k in range(5)]
        segs = [(pts[k], pts[(k + 2) % 5]) for k in range(5)]
    else:
        for off in (0, 1):
            pts = [(ax + Rx * 0.7 * math.cos(-math.pi / 2 + math.pi * (off + 2 * k) / 3), ay + Ry * 0.7 * math.sin(-math.pi / 2 + math.pi * (off + 2 * k) / 3)) for k in range(3)]
            segs += [(pts[k], pts[(k + 1) % 3]) for k in range(3)]
    candles = [(ax + Rx * 0.83 * math.cos(a), ay + Ry * 0.83 * math.sin(a)) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)] if n == 4 else []

    def paint(X, Y, px, py):
        x, y = px + 0.5, py + 0.5
        dx, dy = x - ax, y - ay
        rho = rho_of(dx, dy)
        for cx, cy in candles:
            d = math.hypot(x - cx, (y - cy) * 1.5)
            if d < 1.2:
                return 'd'
            if d < 2.4:
                return 'x'
        glow = None
        if near_ring(dx, dy, 0.985, 0.55) or near_ring(dx, dy, 0.93, 0.5):
            glow = GLOW
        elif near_ring(dx, dy, 0.72 if n > 2 else 0.8, 0.5) and n > 2:
            glow = GLOW
        elif rho < 0.24 and near_ring(dx, dy, 0.24, 0.55):
            glow = GLOW
        elif 0.74 <= rho < 0.915 and n > 2:
            th = math.atan2(dy / Ry, dx / Rx) % (2 * math.pi)
            sec = th / (2 * math.pi) * nsec
            u, v = sec - int(sec), (rho - 0.74) / (0.915 - 0.74)
            g = pk.hashed(int(sec), n, 19) % len(RUNE_PAT)
            if RUNE_PAT[g](u, v):
                glow = GLOW
        if glow is None:
            for (x0, y0), (x1, y1) in segs:
                d, t = (lambda a, b, c, e, f, g_: (math.hypot(a - (c + max(0, min(1, ((a - c) * (f - c) + (b - e) * (g_ - e)) / ((f - c) ** 2 + (g_ - e) ** 2 or 1))) * (f - c)),
                                                               b - (e + max(0, min(1, ((a - c) * (f - c) + (b - e) * (g_ - e)) / ((f - c) ** 2 + (g_ - e) ** 2 or 1))) * (g_ - e))), 0))(x, y, x0, y0, x1, y1)
                if d <= 0.62:
                    glow = GLOW
                    break
            if rho < 0.07 or (n == 4 and near_ring(dx, dy, 0.45, 0.5)):
                glow = GLOW
        if glow:
            return 'r' if pk.hashed(px, py, 2) % 7 == 0 else glow
        # a dark underlay hugging the glow so it reads on any ground
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pass
        return None
    return paint


def circle_rows(n):
    painter = circle_painter(n)
    rows, anchor = pk.decal(n, n, painter)
    # the underlay: a dark pixel on every empty pixel that touches the glow
    h, w = len(rows), len(rows[0])
    out = [list(r) for r in rows]
    for y in range(h):
        for x in range(w):
            if rows[y][x] == '.' and any(0 <= x + dx < w and 0 <= y + dy < h and rows[y + dy][x + dx] in 'ro' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'x'
    return [''.join(r) for r in out], anchor


# --- the assets ------------------------------------------------------------------------------------
STANDING = [
    ('gravestone-round', 'Gravestone, round-topped', gravestone_round, (1, 1)),
    ('gravestone-cross', 'Gravestone, a stone cross', gravestone_cross, (1, 1)),
    ('gravestone-leaning', 'Gravestone, leaning', gravestone_leaning, (1, 1)),
    ('gravestone-broken', 'Gravestone, broken', gravestone_broken, (1, 1)),
    ('cairn-tall', 'Cairn, tall', lambda: cairn(True), (1, 1)),
    ('cairn-small', 'Cairn, small', lambda: cairn(False), (1, 1)),
    ('bones-skull', 'Bones, a skull among them', bones_skull, (1, 1)),
    ('bones-ribs', 'Bones, a rib cage', bones_ribs, (1, 1)),
    ('bones-scatter', 'Bones, scattered', bones_scatter, (1, 1)),
    ('obelisk', 'Obelisk, with runes', obelisk, (1, 1)),
    ('rune-plinth', 'Rune plinth with a crystal', plinth, (1, 1)),
]


def standing_rows(builder, fp):
    got = builder()
    bodies, tall = got[0], got[1]
    fx, fy = got[2] if len(got) > 2 else fp
    w, h, anchor = size_for(fx, fy, tall, pad=10)
    return pk.render(bodies, w, h, anchor), anchor, (fx, fy), bodies


def altar_cover(along_x):
    bodies, tall, (fx, fy) = altar(along_x)
    cells = {(i, j) for i in range(fx) for j in range(fy)}
    return pk.top_cover(bodies, cells, lambda i, j: 1.0)


def build_assets():
    out = []
    for name, label, builder, fp in STANDING:
        rows, anchor, (fx, fy), bodies = standing_rows(builder, fp)
        out.append(family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)(
            name, label, 'still', [rows], footprint={'size': [fx, fy], 'cells': [[i, j] for i in range(fx) for j in range(fy)]}, blocks=True))
    for along_x, name in ((True, 'rune-altar-2x1'), (False, 'rune-altar-1x2')):
        bodies, tall, (fx, fy) = altar(along_x)
        w, h, anchor = size_for(fx, fy, tall, pad=10)
        rows = pk.render(bodies, w, h, anchor)
        cover = altar_cover(along_x)
        out.append(family(CATEGORY, w, h, anchor, place='ground', folder=FOLDER)(
            name, f'Rune altar {fx} x {fy}', 'still', [rows], footprint={'size': [fx, fy], 'cells': [[i, j] for i in range(fx) for j in range(fy)]},
            walkable=min(cover.values()) >= WALK_MIN, levels=1, top_cover={f'{i},{j}': round(v, 2) for (i, j), v in sorted(cover.items())}))
    for kind, label in (('post', 'Spirit lantern post'), ('stone', 'Spirit lantern, stone')):
        frames = [lantern_rows(kind, f)[0] for f in range(LAMP_FRAMES)]
        anchor = lantern_rows(kind, 0)[1]
        out.append(family(CATEGORY, len(frames[0][0]), len(frames[0]), anchor, place='ground', folder=FOLDER)(
            f'spirit-lantern-{kind}', f'{label} (animation)', 'animation', frames, fps=FPS, footprint={'size': [1, 1], 'cells': [[0, 0]]}, blocks=True, light=True))
    for along_x in (True, False):
        for name, label, builder in (('iron-fence', 'Iron fence', fence), ('graveyard-gate', 'Graveyard gate', gate)):
            bodies, tall = builder(along_x)
            w, h, anchor = size_for(1, 1, tall, pad=8)
            rows = pk.render(bodies, w, h, anchor)
            out.append(family(CATEGORY, w, h, anchor, place='ground', folder=FOLDER)(
                f'{name}-{"x" if along_x else "y"}', f'{label}, along {"x" if along_x else "y"}', 'still', [rows], footprint={'size': [1, 1], 'cells': [[0, 0]]},
                runs_along='x' if along_x else 'y', opens=name == 'graveyard-gate', blocks=True))
    for n in (2, 3, 4):
        rows, anchor = circle_rows(n)
        out.append(family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)(
            f'ritual-circle-{n}', f'Ritual circle, {n} x {n}', 'still', [rows], footprint={'size': [n, n], 'cells': [[i, j] for i in range(n) for j in range(n)]}, decal=True))
    return out


def write_package(folder):
    write_json(folder, 'graveyard.json', 'The graveyard and ritual pieces in this folder. See README.md beside this file.',
               {'walk_min': WALK_MIN, 'lantern': {'frames': LAMP_FRAMES, 'fps': FPS}, 'circles': {'sizes': [2, 3, 4], 'about': 'flat decals on the ground diamond of n x n cells'}})


# --- preview ----------------------------------------------------------------------------------------
def preview(path):
    items = []
    for name, label, builder, fp in STANDING:
        rows, anchor, fpx, bodies = standing_rows(builder, fp)
        items.append(dict(label=name, frames=[rows], anchor=anchor, fp=fpx))
    for along_x, name in ((True, 'rune-altar-2x1'), (False, 'rune-altar-1x2')):
        bodies, tall, (fx, fy) = altar(along_x)
        w, h, anchor = size_for(fx, fy, tall, pad=10)
        cover = altar_cover(along_x)
        print(f"{name:18s} top_cover " + ' '.join(f'{k[0]},{k[1]}:{v:.2f}' for k, v in sorted(cover.items())) + (' WALK' if min(cover.values()) >= WALK_MIN else ' no'))
        items.append(dict(label=name, frames=[pk.render(bodies, w, h, anchor)], anchor=anchor, fp=(fx, fy), walk=cover))
    for kind in ('post', 'stone'):
        frames = [lantern_rows(kind, f)[0] for f in range(LAMP_FRAMES)]
        items.append(dict(label=f'spirit-lantern-{kind} (4 frames)', frames=frames, anchor=lantern_rows(kind, 0)[1], fp=(1, 1)))
    for along_x in (True, False):
        for name, builder in (('iron-fence', fence), ('graveyard-gate', gate)):
            bodies, tall = builder(along_x)
            w, h, anchor = size_for(1, 1, tall, pad=8)
            items.append(dict(label=f'{name}-{"x" if along_x else "y"}', frames=[pk.render(bodies, w, h, anchor)], anchor=anchor, fp=(1, 1)))
    for n in (2, 3, 4):
        rows, anchor = circle_rows(n)
        items.append(dict(label=f'ritual-circle-{n}', frames=[rows], anchor=anchor, fp=(n, n), ground=(8, 58, 69, 255)))
    pk.contact_sheet(path, items)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the graveyard ->', args.preview)


if __name__ == '__main__':
    main()
