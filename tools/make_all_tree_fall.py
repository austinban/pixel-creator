#!/usr/bin/env python3
"""The All Tree in autumn: the same tree as make_all_tree.py, not corrupted. PREVIEW ONLY for now: nothing here is registered as an asset.

It uses the corrupted tree's own model (make_all_tree.build): the same trunk, hollow, roots, knots and boughs in exactly the same places, 384 x 448, anchored at (192, 336) on a ten by ten tile base.
What changes:

    gone      every mushroom, bracket fungus, toadstool, thorn, glowing eye and spore mote, and the corrupted teal-and-plum ground
    bark      the palette's warmest wood roles (orange, plum, grape, eggplant: the palette has no brown), moss on the roots and the top surfaces
    ground    healthy green turf over dark soil, with fallen leaves
    foliage   clumps of fall leaves along the boughs, at their tips and in the canopy: about 40% yellow, 35% orange and 25% red, mixed in every clump, with a leafy broken edge
    vines     natural green vines winding up the trunk and hanging from the boughs, with small leaves and no thorns
    fairies   nine small glowing fairies drifting round the trunk and boughs, some in front of the tree and some behind it

The loop is 12 frames at 10 a second: the leaves shimmer (a slow wave of brighter and darker steps climbing the tree), the fairies flit on looping paths with a wing flick, and a few leaves drift down. Every period divides 12.

    python3 tools/make_all_tree_fall.py --preview previews/all-tree-fall.png
    python3 tools/make_all_tree_fall.py --png out.png
    python3 tools/make_all_tree_fall.py --animate previews/all-tree-fall-anim.png --gif previews/all-tree-fall-anim.gif
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_all_tree as T  # noqa: E402
from assetkit import family, write_json  # noqa: E402
from make_fungi import hashed, step_of  # noqa: E402

W, H, ANCHOR, AX, AY, FOOT, FRAMES = T.W, T.H, T.ANCHOR, T.AX, T.AY, T.FOOT, T.FRAMES

# bright to dark
BARK = ('a', 'a', 'g', 'w')                       # terracotta orange in the light, plum and grape in the shade: the nearest the palette has to brown (it has none); bark_char() mottles it
YELLOW = ('d', 'd', 'b', 'a')
ORANGE = ('a', 'a', 'e', 'g')
RED = ('e', 'e', 'i', 'h')                          # coral-red lit, crimson and dark magenta in the shade: the nearest the palette has to red
LEAVES = (YELLOW, ORANGE, RED)
VINE_GREEN = ('z', 'A', 'B', 's')
VINE_DARK = ('A', 'B', 's', 'D')
LEAF_GREEN = ('z', 'A', 'B', 'B')
MOSS = T.MOSS
WEIGHTS = (7, 6, 7)                               # 35% yellow, 30% orange, 35% red, in twentieths


# --- the leaves: clumps of ellipsoids with a broken edge -----------------------------------------------------------
def vhash(a, b, salt):
    n = (a.astype(np.int64) * 374761393 + b.astype(np.int64) * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


_CELLS = {}
CELL_W, CELL_H = 6, 5


def cellmap():
    """Organic clusters of leaves over the whole picture: a jittered Voronoi (each cell's point is moved about inside its square and given a weight, so the cells are all sizes and shapes, about six pixels across). For every pixel: the hash of its cluster (`h`) and its offset from the cluster's middle (`dx`, `dy`). Nothing in it repeats on a grid, and it does not depend on the mass a pixel belongs to."""
    if _CELLS:
        return _CELLS
    px = np.arange(W)[None, :] + np.zeros((H, 1), dtype=np.int64)
    py = np.arange(H)[:, None] + np.zeros((1, W), dtype=np.int64)
    ci, cj = px // CELL_W, py // CELL_H
    best = np.full((H, W), np.inf)
    bh, bdx, bdy = np.zeros((H, W), dtype=np.int64), np.zeros((H, W)), np.zeros((H, W))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            i, j = ci + di, cj + dj
            jx, jy = (vhash(i, j, 201) % 1000) / 1000.0, (vhash(i, j, 202) % 1000) / 1000.0
            wt = (vhash(i, j, 203) % 1000) / 1000.0 * 1.6
            dx = px + 0.5 - (i + 0.15 + 0.7 * jx) * CELL_W
            dy = py + 0.5 - (j + 0.15 + 0.7 * jy) * CELL_H
            d = np.hypot(dx, dy * 1.2) - wt
            better = d < best
            best = np.where(better, d, best)
            bh = np.where(better, vhash(i, j, 204), bh)
            bdx, bdy = np.where(better, dx, bdx), np.where(better, dy, bdy)
    _CELLS.update(h=bh, dx=bdx, dy=bdy)
    return _CELLS


class Leafy(T.Ell):
    """A mass of leaves: a lumpy body whose rim is cut into leaf-shaped scallops, with a few bites out of it and a few clusters missing inside (the interior is otherwise whole, so it shades cleanly). Pixels it gives up show what is behind: the sky, a bough, the trunk."""

    def __init__(self, c, radii, hue, seed, group, pure=False):
        super().__init__(LEAVES[hue], c, radii, mark='foliage', group=group)
        self.hue, self.seed, self.pure = hue, seed, pure
        self.scallops = max(7, int(2 * math.pi * max(radii[0], radii[1]) * 16 / 9))
        self.cx = (c[0] - c[1]) * 16 + AX
        self.cy = (c[0] + c[1]) * 8 - 16 * c[2] + AY

    def hit(self, ox, oy):
        t, nx, ny, nz = super().hit(ox, oy)
        px = np.rint((ox - oy) * 16 + AX - 0.5)
        py = np.rint((ox + oy) * 8 + AY - 0.5)
        facing = (nx + ny + nz) / 1.7320508     # the camera looks down the (1, 1, 1) diagonal, so a surface facing it has a normal along it
        ang = np.arctan2(py - self.cy, px - self.cx)
        scallop = 0.5 + 0.5 * np.sin(ang * self.scallops + self.seed)
        bite = 0.30 * np.maximum(0.0, np.sin(ang * 2 + self.seed * 1.3 + 1.0) * np.sin(ang * 3 + self.seed * 0.7))      # a lumpy outline: a few wide bites
        hole = facing < 0.08 + 0.42 * scallop ** 1.5 + bite
        cells = cellmap()
        ix, iy = np.clip(np.nan_to_num(px, nan=0).astype(np.int64), 0, W - 1), np.clip(np.nan_to_num(py, nan=0).astype(np.int64), 0, H - 1)
        gap = (cells['h'][iy, ix] % 100 < 11) & (facing < 0.8)                                                            # a whole cluster missing now and then, so a bough shows through
        return np.where(hole | gap, -np.inf, t), nx, ny, nz


def leaf_pick(body, n, step, px, py):
    """(ramp number, step) of a leaf pixel. Colour is chosen per CLUSTER (see cellmap), never per pixel: a cluster takes its mass's colour about half the time and a random one otherwise, the rim of a mass turns red more often, and a pure mass keeps one colour. A cluster is a step lighter, the same or a step darker than the mass at that spot, with its top left lighter and its lower right darker, so it reads as a bunch of leaves."""
    cells = cellmap()
    h = int(cells['h'][py, px])
    cdx, cdy = float(cells['dx'][py, px]), float(cells['dy'][py, px])
    if body.pure:
        hue = body.hue
    else:
        if h % 100 < 45:
            hue = body.hue
        else:
            v = (h >> 7) % 20
            hue = 0 if v < WEIGHTS[0] else 1 if v < WEIGHTS[0] + WEIGHTS[1] else 2
        facing = (n[0] + n[1] + n[2]) / 1.7320508
        if facing < 0.38 and (h >> 3) % 100 < 30:                       # the rim of a mass: red-edged clumps
            hue = 2
    s = step
    dy = (py - body.cy) / max(8.0, body.r[2] * 16)
    if dy > 0.45:
        s = min(3, s + 1)
    elif dy < -0.55 and s > 0:
        s -= 1
    s = max(0, min(3, s + (0, 0, 1, -1)[(h >> 11) % 4]))
    u = cdx * 0.6 + cdy * 0.8
    if u < -1.5:
        s = max(0, s - 1)
    elif u > 1.9:
        s = min(3, s + 1)
    return hue, s


def cell_centre(x, y):
    """The middle of the cluster a pixel is in, so a whole cluster can shimmer together."""
    cells = cellmap()
    return int(round(x - cells['dx'][y, x])), int(round(y - cells['dy'][y, x]))


def foliage(bodies):
    """Big masses along every bough, more toward the tips, and a heavy canopy across the top edge. Each mass is a few overlapping blobs sitting above and beside the bough, with the odd gap, so the boughs and the trunk still show through and under the leaves."""
    chains = {}
    for b in bodies:
        if b.mark == 'bark' and isinstance(b.group, tuple) and b.group[0] in ('top', 'low'):
            chains.setdefault(b.group, []).append((b.c, b.r[0]))
    out = []
    n = 0
    for key in sorted(chains, key=repr):
        pts = chains[key]
        second = len(key) > 2
        count = (4 if second else 6) if key[0] == 'top' else (2 if second else 4)
        size = 0.8 if second else 0.95
        for k in range(count + 1):
            tip = k == count
            n += 1
            if not tip and k % 5 == 3:                                        # a gap in the leaves, so the bough shows
                continue
            s_ = 1.0 if tip else 0.25 + 0.7 * (k + 0.5) / count
            (cx, cy, ch), rad = pts[min(len(pts) - 1, int(s_ * (len(pts) - 1)))]
            v = (n * 7 + 3) % 20
            hue = 0 if v < WEIGHTS[0] else 1 if v < WEIGHTS[0] + WEIGHTS[1] else 2
            pure = n % 4 == 0                                                 # one mass in four keeps a single colour: a few all-red ones, all-orange, all-yellow
            side = 1 if (n % 2) else -1
            for j in range(6 if tip else 4):
                a = hashed(n, j, 71) % 360
                d = 0.35 + (hashed(n, j, 72) % 100) / 100 * (1.1 if tip else 0.85)
                dz = 0.5 + (hashed(n, j, 73) % 100) / 100 * 1.1
                R = size * (1.45 if tip else 1.1) * (0.8 + (hashed(n, j, 74) % 100) / 100 * 0.45)
                squash = 0.7 + (hashed(n, j, 75) % 100) / 100 * 0.7                       # lumpy, not round: some wide, some tall
                out.append(Leafy((cx + d * math.cos(math.radians(a)) + 0.25 * side, cy + d * math.sin(math.radians(a)), ch + dz), (R * squash, R / squash, 0.78 * R), hue, 31 + n, ('leafclump', n), pure))
    # the canopy: a heavy ring of masses across the top of the picture, where the great boughs go out of view
    for i in range(110):
        phi = math.radians(hashed(i, 1, 81) % 360)
        rho = 2.5 + (hashed(i, 2, 81) % 100) / 100 * 10.0
        h = 17 + (hashed(i, 3, 81) % 100) / 100 * 11.0
        cx, cy = T.trunk_c(h)
        x, y = cx + rho * math.cos(phi), cy + rho * math.sin(phi)
        sy = 8 * (x + y) - 16 * h + AY
        if not -30 < sy < 52:
            continue
        v = hashed(i, 4, 81) % 20
        hue = 0 if v < WEIGHTS[0] else 1 if v < WEIGHTS[0] + WEIGHTS[1] else 2
        R = 1.2 + (hashed(i, 5, 81) % 100) / 100 * 0.9
        squash = 0.7 + (hashed(i, 6, 81) % 100) / 100 * 0.7
        out.append(Leafy((x, y, h), (R * squash, R / squash, 0.78 * R), hue, 400 + i, ('leafclump', 1000 + i), i % 7 == 0))
    return out


def vine_hanging(p, length, ramp, group, sway=0.4):
    out = []
    steps = int(length / 0.14)
    for i in range(steps + 1):
        s = i / steps
        out.append(T.Ell(ramp, (p[0] + sway * math.sin(s * 3 + p[0]) * s, p[1] + sway * 0.6 * math.cos(s * 2.4) * s, p[2] - length * s), (0.1, 0.1, 0.12), mark='vine', group=group))
    for s, side in ((0.5, 1), (0.85, -1)):                                                                 # a couple of small leaves along it
        i = int(s * steps)
        e = out[i]
        out.append(T.Ell(LEAF_GREEN, (e.c[0] + 0.2 * side, e.c[1], e.c[2]), (0.26, 0.2, 0.09), mark='leaf', group=(group, 'l', i)))
    out.append(T.Ell(LEAF_GREEN, (p[0] + sway * math.sin(3 + p[0]), p[1] + sway * 0.6 * math.cos(2.4), p[2] - length - 0.05), (0.2, 0.2, 0.3), mark='leaf', group=(group, 'tip')))
    return out


def build():
    """The tree model: the corrupted tree's trunk, roots, knots and boughs, untouched, plus the ground, vines and foliage."""
    original = T.build()
    keep = [b for b in original if b.mark in ('trunk', 'bark', 'root', 'knot', 'ground')]
    bodies = keep
    bodies += T.vine(20, 1.0, 0.4, 25.0, VINE_GREEN, 'vine1', thorns=False, leaf_ramp=LEAF_GREEN)
    bodies += T.vine(150, 0.85, 0.8, 25.0, VINE_DARK, 'vine2', thorns=False, leaf_ramp=LEAF_GREEN)
    chains = {}
    for b in original:
        if b.mark == 'bark' and isinstance(b.group, tuple) and b.group[0] == 'low' and len(b.group) == 2:
            chains.setdefault(b.group[1], []).append(b.c)
    for i, (key, s, ln, ramp) in enumerate(((0, 0.5, 4.2, VINE_GREEN), (0, 0.8, 3.0, VINE_DARK), (1, 0.45, 4.6, VINE_DARK), (1, 0.75, 3.4, VINE_GREEN), (2, 0.7, 2.6, VINE_GREEN), (3, 0.7, 3.0, VINE_DARK))):
        pts = chains[key]
        x, y, h = pts[min(len(pts) - 1, int(s * (len(pts) - 1)))]
        bodies += vine_hanging((x, y, h - 0.1), ln, ramp, ('hang', i))
    bodies += foliage(original)
    return bodies


# --- colours -------------------------------------------------------------------------------------------------------
def bark_char(s, px, py):
    """Bark: terracotta in the light, mottled with plum where it turns, so it is not a flat orange."""
    k = hashed(px // 2, py // 2, 15)
    if s == 0:
        return 'a' if k % 3 else 'e'
    if s == 1:
        return 'a' if k % 5 < 1 else 'g'
    if s == 2:
        return 'g' if k % 4 else 'w'
    return 'w' if k % 3 else 'x'


def ground_colour(p, px, py):
    x, y = p[0], p[1]
    rho = (abs(x) ** 4 + abs(y) ** 4) ** 0.25
    th = math.atan2(y, x)
    if rho > T.ground_limit(th) - 0.5 and (px + py) % 2 == 0:
        return None
    bx, by = px // 3, py // 2
    if hashed(bx, by, 77) % 13 == 0:                             # a fallen leaf: three pixels across, with a lighter vein
        ramp = LEAVES[(0, 1, 2, 2, 1)[hashed(bx, by, 78) % 5]]
        return ramp[0] if (px % 3 == 1 and py % 2 == 0) else ramp[1 + (py % 2)]
    r = math.hypot(x, y)
    v = T.noise(x, y, 1.0)
    if r < 2.9 + 0.5 * math.sin(th * 3):                         # soil between the roots
        return 'g' if (v > 0.1 and hashed(px, py, 7) % 4) else 'w'
    if v < -0.7:
        return 'B' if hashed(px, py, 8) % 4 else 's'
    if v > 0.5:
        return 'z' if hashed(px, py, 9) % 3 == 0 else 'A'
    return 'A' if hashed(px, py, 10) % 5 else 'B'


def trunk_colour(body, p, n, step, px, py):
    r = BARK
    dx, dy = p[0] - body.c[0], p[1] - body.c[1]
    ang = math.atan2(dy, dx)
    h = p[2]
    R = body.r0
    u = ang * R
    da = (ang - math.radians(45) + math.pi) % (2 * math.pi) - math.pi
    hx, hy = da * R / 1.65, (h - 3.6) / 2.5
    q = hx * hx + hy * hy
    if q < 1.0:                                       # the hollow
        if hy > 0.55 and hx * hx + (hy - 0.55) ** 2 > 0.75:
            return 'w'
        if q > 0.72:
            return 'w' if step < 3 else 'x'
        return 'x'
    if q < 1.42:                                      # its lip
        if step < 2 and hy > -0.2:
            return 'g'
        return 'w' if step < 3 else 'x'
    s = step
    ridge = math.sin(u * 2.4 + 1.3 * math.sin(h * 0.5 + ang * 2.0)) + 0.5 * math.sin(u * 5.1 + h * 0.3)
    if ridge < -0.85:
        s = min(3, s + 1)
    elif ridge > 1.0:
        s = max(0, s - 1)
    elif hashed(px, py, 6) % 14 == 0:
        s = min(3, s + 1)
    tongue = 1.8 + 3.4 * (0.5 + 0.5 * math.sin(u * 2.9 + 1.0)) * (0.5 + 0.5 * math.sin(u * 1.3 + 4.0))
    if h < tongue and hashed(px, py, 13) % 7 != 0:
        return MOSS[min(3, s)]
    if s == 0 and ridge > 0.55:
        return 'a'
    return bark_char(s, px, py)


def colour(body, p, n, step, px, py):
    m = body.mark
    if m == 'ground':
        return ground_colour(p, px, py)
    if m == 'trunk':
        return trunk_colour(body, p, n, step, px, py)
    if m in ('bark', 'root', 'knot'):
        s = step
        if s < 3 and hashed(px, py, 4) % 13 == 0:
            s += 1
        if n[2] > 0.5 and p[2] < 14 and T.noise(p[0] * 2.4, p[1] * 2.4, p[2] * 1.3) > 0.55:
            return MOSS[min(3, s)]
        return bark_char(s, px, py)
    if m == 'foliage':
        hue, s = leaf_pick(body, n, step, px, py)
        return LEAVES[hue][s]
    return body.mat[step]


# --- single leaves, drawn on the picture ------------------------------------------------------------------------------
class Stamp:
    """Stands in for a body: the picture's own leaves (marks `sleaf` and `svein`) are drawn straight on the grid."""
    mat = ()
    rim = None
    spotramp = None

    def __init__(self, mark):
        self.mark = mark


STAMP, VEIN = Stamp('sleaf'), Stamp('svein')
VEIN_COLOUR = ('t', 'd', 'c')                       # a lighter vein down each leaf: cream, yellow, salmon


def leaf_pixels(ang, length, width):
    """Pixels (dx, dy, side, vein) of a pointed leaf that starts at (0, 0) and points along `ang` degrees (0 is right, 90 is down): fat in the middle, pointed at the tip, a vein down it."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    reach = int(length) + 2
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if 0.9 <= u <= length:
                half = width / 2 * math.sin(math.pi * min(1.0, (u - 0.4) / (length - 0.4))) ** 0.7
                if abs(v) <= half + 0.15:
                    out.append((dx, dy, 0 if v < 0 else 1, abs(v) < 0.55 and 1.4 < u < length - 0.6))
    return out


def stamp_leaves(grid):
    """Distinct leaves coming off the masses: hanging from their undersides on a short stem, and sticking out of their sides and tops, in yellow, orange and red."""
    cand = []
    for y in range(12, 330):
        row, below = grid[y], grid[y + 1]
        for x in range(4, W - 4):
            cell = row[x]
            if not cell or cell[3].mark != 'foliage':
                continue
            if below[x] is None:
                cand.append((hashed(x, y, 91), x, y, 90))
            elif row[x + 1] is None:
                cand.append((hashed(x, y, 92), x, y, 0))
            elif row[x - 1] is None:
                cand.append((hashed(x, y, 93), x, y, 180))
            elif grid[y - 1][x] is None:
                cand.append((hashed(x, y, 94), x, y, 270))
    cand.sort()
    taken = []
    made = 0
    for key, x, y, base in cand:
        if made >= 200:
            break
        if any(abs(x - ax) < 9 and abs(y - ay) < 9 for ax, ay in taken):
            continue
        v = hashed(x, y, 95) % 20
        hue = 0 if v < WEIGHTS[0] else 1 if v < WEIGHTS[0] + WEIGHTS[1] else 2
        ang = base + (hashed(x, y, 96) % 61) - 30
        length = 7 + hashed(x, y, 97) % 3
        pixels = leaf_pixels(ang, length, 5 if length < 9 else 6)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        stem = [(x + round(ca * i), y + round(sa * i)) for i in (1,)]
        free = [(x + dx, y + dy, side, vein) for dx, dy, side, vein in pixels if 0 <= x + dx < W and 0 <= y + dy < H and grid[y + dy][x + dx] is None]
        if len(free) < 0.92 * len(pixels):
            continue
        depth = grid[y][x][2] + 0.6
        ramp = LEAVES[hue]
        for sx, sy in stem:
            if grid[sy][sx] is None:
                grid[sy][sx] = (ramp[3], ('sleaf', made), depth, STAMP, (hue, 3))
        for px_, py_, side, vein in free:
            if vein:
                grid[py_][px_] = (VEIN_COLOUR[hue], ('sleaf', made), depth, VEIN, None)
            else:
                grid[py_][px_] = (ramp[2 * side], ('sleaf', made), depth, STAMP, (hue, 2 * side))
        taken.append((x, y))
        made += 1


# --- drawing ---------------------------------------------------------------------------------------------------------
def render(bodies=None, with_grid=False):
    """The picture as role rows. `with_grid` also hands back, for every pixel, (colour, group, depth, body, leaf) where `leaf` is (ramp, step) for a leaf pixel."""
    bodies = bodies or build()
    a = (np.arange(W) + 0.5 - AX) / 16.0
    b = (np.arange(H) + 0.5 - AY) / 8.0
    A, B = np.meshgrid(a, b)
    OX, OY = (A + B) / 2, (B - A) / 2
    depth = np.full((H, W), -np.inf)
    idx = np.full((H, W), -1, dtype=np.int32)
    NX, NY, NZ = np.zeros((H, W)), np.zeros((H, W)), np.zeros((H, W))
    with np.errstate(all='ignore'):
        for i, body in enumerate(bodies):
            x0, x1, y0, y1 = body.box()
            x0, y0, x1, y1 = max(0, int(math.floor(x0))), max(0, int(math.floor(y0))), min(W, int(math.ceil(x1))), min(H, int(math.ceil(y1)))
            if x0 >= x1 or y0 >= y1:
                continue
            t, nx, ny, nz = body.hit(OX[y0:y1, x0:x1], OY[y0:y1, x0:x1])
            sub = depth[y0:y1, x0:x1]
            better = t > sub
            if not better.any():
                continue
            sub[better] = t[better]
            idx[y0:y1, x0:x1][better] = i
            NX[y0:y1, x0:x1][better], NY[y0:y1, x0:x1][better], NZ[y0:y1, x0:x1][better] = nx[better], ny[better], nz[better]
    grid = [[None] * W for _ in range(H)]
    ys, xs = np.nonzero(idx >= 0)
    for y, x in zip(ys.tolist(), xs.tolist()):
        body = bodies[idx[y, x]]
        t = depth[y, x]
        p = (OX[y, x] + t, OY[y, x] + t, t)
        nrm = (NX[y, x], NY[y, x], NZ[y, x])
        step = step_of(nrm)
        c = colour(body, p, nrm, step, x, y)
        if c is not None:
            leaf = leaf_pick(body, nrm, step, x, y) if body.mark == 'foliage' else None
            grid[y][x] = (c, body.group, t, body, leaf)
    stamp_leaves(grid)
    out = [[(c[0] if c else '.') for c in row] for row in grid]
    for y in range(H):
        for x in range(W):
            cell = grid[y][x]
            if not cell or cell[1] == 'ground':
                continue
            for nx_, ny_ in ((x - 1, y), (x, y - 1)):
                other = grid[ny_][nx_] if 0 <= nx_ < W and 0 <= ny_ < H else None
                if other and other[1] != cell[1] and other[1] != 'ground' and other[2] - cell[2] > 0.3:
                    out[y][x] = T.DARKER.get(out[y][x], 'x') if out[y][x] not in 'xDwk' else out[y][x]
    final = [row[:] for row in out]
    for y in range(H):
        for x in range(W):
            if grid[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx_, ny_ = x + dx, y + dy
                    if 0 <= nx_ < W and 0 <= ny_ < H and grid[ny_][nx_] and grid[ny_][nx_][1] != 'ground':
                        final[y][x] = 'O'
                        break
    rows = [''.join(r) for r in final]
    return (rows, grid) if with_grid else rows


# --- the animation ---------------------------------------------------------------------------------------------------
# (centre x, centre y, radius x, radius y, period, phase, laps up and down per loop (2 draws a figure of eight), behind the tree?, colour)
FAIRIES = (
    (118, 330, 14, 9, 12, 0.00, 1, False, 0), (262, 318, 12, 8, 6, 0.30, 2, False, 1), (84, 214, 16, 10, 12, 0.55, 2, True, 2),
    (300, 196, 13, 9, 12, 0.20, 1, False, 0), (190, 150, 15, 8, 12, 0.75, 2, False, 1), (112, 96, 12, 10, 6, 0.10, 1, True, 2),
    (276, 78, 14, 8, 12, 0.40, 2, False, 0), (178, 40, 13, 7, 12, 0.90, 1, True, 1), (40, 330, 10, 8, 4, 0.60, 1, False, 2),
)
FAIRY_COLOURS = (('t', 'r', 'r', 'o'), ('r', 't', 'o', 'n'), ('j', 't', 'c', 'j'))       # body, wings, inner halo, outer halo: cream in mint and cyan, mint in cyan and sky, pink in salmon and hot pink
LEAF_FALL = (0, 3, 7, 12, 18, 25, 33, 42, 52, 63)       # a leaf is in the air for ten of the twelve frames


def fairy_path(spec, f):
    cx, cy, rx, ry, period, phase, laps = spec[:7]
    a = 2 * math.pi * (f / period + phase)
    return round(cx + rx * math.cos(a)), round(cy + ry * math.sin(laps * a) + 1.5 * math.sin(a * 2))


def leaf_spawns(grid, count=14):
    """Where leaves let go: the undersides of the clumps, in a fixed order with room between them."""
    cand = []
    for y in range(30, 300):
        for x in range(8, W - 8):
            cell = grid[y][x]
            if cell and cell[3].mark == 'foliage' and (grid[y + 1][x] is None or grid[y + 1][x][3].mark != 'foliage'):
                cand.append((hashed(x, y, 91), x, y))
    cand.sort()
    out = []
    for _, x, y in cand:
        if len(out) >= count:
            break
        if all(math.hypot(x - ox, y - oy) > 26 for ox, oy, _, _ in out):
            out.append((x, y, (len(out) * 5 + 2) % FRAMES, (0, 2, 1, 2, 0)[len(out) % 5]))
    return out


def build_animation(rows=None, grid=None):
    if rows is None:
        rows, grid = render(with_grid=True)
    spawns = leaf_spawns(grid)
    frames = []
    for f in range(FRAMES):
        g = [list(r) for r in rows]
        # 1. the shimmer: the leaves and vines step along their ramps in a wave that climbs the tree
        for y in range(H):
            for x in range(W):
                cell = grid[y][x]
                if not cell or g[y][x] == 'O':
                    continue
                mark = cell[3].mark
                if mark not in ('foliage', 'vine', 'leaf', 'sleaf'):
                    continue
                w = T.shimmer_wave(*cell_centre(x, y), f) if mark == 'foliage' else T.shimmer_wave(x, y, f)       # a whole cluster steps together, not pixel by pixel
                shift = 0 if abs(w) < 0.45 else (1 if w > 0 else -1) * (2 if (abs(w) > 0.9 and mark == 'foliage') else 1)
                if cell[4]:
                    hue, s = cell[4]
                    g[y][x] = LEAVES[hue][max(0, min(3, s - shift))]
                else:
                    ramp = T.ramp_of(cell[3], g[y][x])
                    if ramp:
                        g[y][x] = ramp[max(0, min(3, ramp.index(g[y][x]) - shift))]

        def put(x, y, c, over=True):
            if 0 <= x < W and 0 <= y < H and g[y][x] != 'O' and (over or g[y][x] == '.'):
                g[y][x] = c
        # 2. leaves tumbling down, ten frames each, swaying left and right and turning through three shapes
        for x0, y0, start, hue in spawns:
            k = (f - start) % FRAMES
            if k >= len(LEAF_FALL):
                continue
            ramp = LEAVES[hue]
            fade = k in (0, len(LEAF_FALL) - 1)
            x = x0 + round(5 * math.sin(k * 0.75 + hue * 2 + x0))
            y = y0 + 3 + LEAF_FALL[k]
            ang = (35, 100, 160)[(k // 2 + hue) % 3] + 20 * (k % 2)
            for dx, dy, side, vein in leaf_pixels(ang, 4.6, 3):
                put(x + dx, y + dy, ramp[2] if fade else (VEIN_COLOUR[hue] if vein else ramp[2 * side]), over=False)
        # 3. the fairies: a wing flick every frame, a glow round each; the ones behind the tree only show beside it
        order = sorted(FAIRIES, key=lambda s: not s[7])
        for spec in order:
            behind = spec[7]
            body, wing, halo_in, halo_out = FAIRY_COLOURS[spec[8]]
            x, y = fairy_path(spec, f)
            up = f % 2 == 0
            wings = ((-1, -1), (-2, -2), (-2, -1), (1, -1), (2, -2), (2, -1)) if up else ((-1, 1), (-2, 1), (-2, 2), (1, 1), (2, 1), (2, 2))
            put_ = (lambda xx, yy, c: put(xx, yy, c, over=False)) if behind else (lambda xx, yy, c: put(xx, yy, c))
            for dy in range(-5, 6):                                                      # the halo: a solid inner glow and a solid outer ring, drawn first and under the rest
                for dx in range(-5, 6):
                    d = math.hypot(dx, dy * 0.9)
                    if d <= 2.6:
                        put(x + dx, y + dy, halo_in, over=not behind)
                    elif d <= 3.7:
                        put(x + dx, y + dy, halo_out, over=not behind)
            for dx, dy in wings:
                put_(x + dx, y + dy, wing)
            put_(x, y - 2, 't')                                                          # the head, the body and the feet: five pixels tall
            for dy in (-1, 0, 1):
                put_(x, y + dy, body)
            put_(x, y + 2, body)
        frames.append([''.join(r) for r in g])
    return frames


CATEGORY = 'Victory Screen'
FOLDER = 'all-tree-fall'
FPS = 10


def build_assets():
    """`all-tree-fall`, the 12-frame loop (leaves shimmering, fairies flitting, leaves falling), and `all-tree-fall-still`, its first frame; 384 x 448, anchored at the middle of the base, in the same cell and anchor as the corrupted tree so one can be swapped for the other."""
    make = family(CATEGORY, W, H, ANCHOR, place='none', folder=FOLDER)
    frames = build_animation()
    return [make('all-tree-fall', 'The All Tree, autumn (animated)', 'animation', frames, fps=FPS),
            make('all-tree-fall-still', 'The All Tree, autumn (still)', 'still', [frames[0]])]


def write_package(folder):
    write_json(folder, 'all-tree-fall.json', 'The autumn All Tree sheets in this folder.',
               {'cell': [W, H], 'anchor': {'x': AX, 'y': AY}, 'frames': FRAMES, 'fps': FPS, 'footprint': [FOOT, FOOT], 'levels': 20,
                'animated': 'all-tree-fall.png', 'still': 'all-tree-fall-still.png', 'sheet': {'cols': 8, 'rows': 2}})


def main():
    parser = argparse.ArgumentParser(description="The All Tree in autumn (preview).")
    parser.add_argument('--preview', type=Path, help='write the still over its footprint, enlarged, plus -base and -top crops')
    parser.add_argument('--png', type=Path, help='write the flat 384 x 448 transparent picture (the first frame) here')
    parser.add_argument('--animate', type=Path, help='write a contact sheet of the 12 frames here')
    parser.add_argument('--gif', type=Path, help='write the looping animation here, and an 8x one of the foot of the tree beside it')
    parser.add_argument('--frame-dir', type=Path, help='also write every frame as a PNG here')
    args = parser.parse_args()
    if not (args.preview or args.png or args.animate or args.gif or args.frame_dir):
        parser.error('say --preview, --png, --animate, --gif or --frame-dir')
    frames = build_animation()
    if args.preview:
        T.preview(args.preview, frames[0])
        print('the autumn All Tree, enlarged ->', args.preview)
    if args.png:
        args.png.parent.mkdir(parents=True, exist_ok=True)
        T.to_image(frames[0]).save(args.png)
        print('the autumn All Tree ->', args.png)
    if args.animate:
        T.write_sheet(args.animate, frames)
        print('the 12 frames, half size ->', args.animate)
    if args.gif:
        T.write_gif(args.gif, T.frame_images(frames))
        T.write_gif(args.gif.with_name(args.gif.stem + '-base.gif'), T.frame_images(frames, 8, T.BASE_CROP))
        print('the looping animation ->', args.gif, 'and', args.gif.with_name(args.gif.stem + '-base.gif'))
    if args.frame_dir:
        args.frame_dir.mkdir(parents=True, exist_ok=True)
        for i, fr in enumerate(frames):
            T.to_image(fr).save(args.frame_dir / f'all-tree-fall-{i:02d}.png')
        print('frames ->', args.frame_dir)


if __name__ == '__main__':
    main()
