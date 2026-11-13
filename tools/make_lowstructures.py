#!/usr/bin/env python3
"""A kit of low structures a unit can climb onto and take cover behind, for the town and farm maps: haybale stacks, stepped crate piles, market stalls, open sheds, carts and wagons.

Same model as the rocks and the ruins (tools/make_rocks.py, tools/make_ruins.py, which this file shares its renderer and preview with): every piece stands on whole ground cells and is one sprite covering them,
anchored at the middle of its bounding box on the ground; each cell of a walkable piece has a flat top at a whole level (1 or 2, 16 pixels each), and a piece is walkable when every cell's flat top is at least 60 percent
of the cell. A stepped piece has a different level on different cells, one level apart, so a unit climbs it step by step (`cell_levels` in its record). The taller cell is always the one at the back (toward -x and -y): a taller cell in front would hide the lower one and the measured flat top would fall.

    HAY        stacks of bales (a bale is half a level): 1 x 1 to 2 x 2, 1 or 2 high, and stepped ones
    CRATES     stepped piles of crates and kegs (not the ground sheet's single `Crates`, which are one cell each)
    STALLS     a canvas roof at 1 level on four posts, an open front with a counter (walkable on the roof), and a sloping-awning stall (cover, not walkable)
    SHEDS      a hut with a flat plank roof and one open side, an alcove to shelter in (walkable on the roof, 1 or 2 high)
    CARTS      a hay cart, a crate cart and wagons, loaded to a flat top at 1 level (walkable on the load)

    python3 tools/make_lowstructures.py --preview previews/low-structures.png      every piece at 2x on its footprint, walkable ones marked, the measured flat top printed
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildings as bd  # noqa: E402
from buildings import Solid, plane, hashed  # noqa: E402
import make_ruins as mr  # noqa: E402
from make_ruins import Blk, Piece, px, q, rnd  # noqa: E402
from make_rocks import rect, lshape  # noqa: E402

FOLDER = 'low-structures'
CATEGORY = 'Low structures'


# --- materials -----------------------------------------------------------------------------------
def local(s, face, P):
    """(a, b, a0, a1, b0, b1): the pixel on the face along it and across it, and the face's own extent in the same pixels."""
    x, y, z = P
    x0, x1, y0, y1, z0, z1 = s.b
    if face == 'top':
        return px(x), px(y), px(x0), px(x1) - 1, px(y0), px(y1) - 1
    if face == 'R':
        return px(y), px(z), px(y0), px(y1) - 1, px(z0), px(z1) - 1
    return px(x), px(z), px(x0), px(x1) - 1, px(z0), px(z1) - 1


def paint_hay(s, face, P):
    a, b, a0, a1, b0, b1 = local(s, face, P)
    t = hashed(s.seed, 1) % 3
    if face == 'top':
        base = ('C', 'C', 'd')[t]
        streak, edge = 'd', 'b'
        if a in (a0, a1) or b in (b0, b1):
            return edge
        return streak if hashed(a, b // 2, 5 + (s.seed & 0xFF)) % 4 == 0 else base
    base = {'R': ('d', 'C', 'b'), 'L': ('b', 'd', 'a')}[face][t]
    streak = {'R': 'C', 'L': 'd'}[face]
    dark = {'R': 'a', 'L': 'g'}[face]
    if b == b1:
        return 'C' if face == 'R' else 'd'
    if a in (a0, a1) or b == b0:
        return dark
    span = a1 - a0
    if span > 4 and a in (a0 + max(2, round(span * 0.28)), a1 - max(2, round(span * 0.28))):          # the twine
        return dark
    return streak if hashed(a // 3, b, 9 + (s.seed & 0xFF)) % 5 == 0 else base


def paint_crate(s, face, P):
    a, b, a0, a1, b0, b1 = local(s, face, P)
    if face == 'top':
        if a in (a0, a1) or b in (b0, b1):
            return 'g'
        return 'a' if (b - b0) % 4 == 3 else 'b'
    base, gap, hi = ('a', 'g', 'b') if face == 'R' else ('g', 'x', 'a')
    if a in (a0, a1) or b in (b0, b1):
        return gap
    k = (b - b0) % 4
    if (a - a0) == (b - b0) or (a1 - a) == (b - b0) and (a1 - a0) > 6:                  # a brace
        return hi
    return gap if k == 3 else hi if k == 0 else base


def paint_keg(s, face, P):
    a, b, a0, a1, b0, b1 = local(s, face, P)
    if face == 'top':
        if a in (a0, a1) or b in (b0, b1):
            return 'a'
        return 'g' if (a - a0, b - b0) == ((a1 - a0) // 2, (b1 - b0) // 2) else 'b'
    hoop = b - b0 in (2, 3) or b1 - b in (2, 3)
    if hoop:
        return 'x' if face == 'L' else 'g'
    return ('g' if (a - a0) % 3 == 0 else 'a') if face == 'R' else ('w' if (a - a0) % 3 == 0 else 'g')


def paint_plank(s, face, P):
    a, b, a0, a1, b0, b1 = local(s, face, P)
    if face == 'top':
        if a in (a0, a1) or b in (b0, b1):
            return 'g'
        return 'g' if (b - b0) % 4 == 3 else 'f'
    return ('g' if (b - b0) % 4 == 3 else 'f') if face == 'R' else ('w' if (b - b0) % 4 == 3 else 'g')


def paint_cloth(s, face, P):
    x, y, z = P
    warm = (s.colour or 'warm') == 'warm'
    pair = {'R': ('e', 'C'), 'L': ('f', 'b'), 'top': ('e', 'C')} if warm else {'R': ('q', 'r'), 'L': ('p', 'q'), 'top': ('q', 'r')}
    a = px(y) if face in ('top', 'R') else px(x)
    c = pair[face][(a // 4) % 2]
    if face != 'top':
        x0, x1, y0, y1, z0, z1 = s.b
        if px(z) - px(z0) < 2:                                       # a scalloped hem
            return pair[face][(a // 2) % 2]
    return c


def paint_goods(s, face, P):
    base = s.colour or 'e'
    return {'top': base, 'R': base, 'L': bd.DARKER.get(base, base)}[face]


def paint_wheel(s, face, P):
    x, y, z = P
    x0, x1, y0, y1, z0, z1 = s.b
    if face == 'top':
        return 'g'
    a = px(x) if face == 'L' else px(y)
    a0, a1 = (px(x0), px(x1)) if face == 'L' else (px(y0), px(y1))
    cx, cz = (a0 + a1) / 2, (px(z0) + px(z1)) / 2
    r = (px(z1) - px(z0)) / 2
    dx, dz = a + 0.5 - cx, px(z) + 0.5 - cz
    d = math.hypot(dx, dz)
    if d > r:
        return None
    if d > r - 1.6:
        return 'w' if face == 'L' else 'x'
    if d < 1.7:
        return 'd'
    ang = math.atan2(dz, dx)
    if abs(math.sin(ang * 4)) < 0.34:                                # eight spokes
        return 'g' if face == 'L' else 'f'
    return None


mr.register('hay', paint_hay)
mr.register('crate', paint_crate)
mr.register('keg', paint_keg)
mr.register('plank', paint_plank)
mr.register('cloth', paint_cloth)
mr.register('goods', paint_goods)
mr.register('wheel', paint_wheel)


# --- builders ------------------------------------------------------------------------------------
def stack(levels, kind, seed):
    """Bales or crates, half a level each, filling every cell up to its level; each layer turned across the one below."""
    out = []
    for (i, j), hz in sorted(levels.items()):
        s = seed + i * 977 + j * 1301
        for layer in range(int(round(hz * 2))):
            z0 = layer * 0.5
            top = layer == int(round(hz * 2)) - 1
            if kind == 'hay':
                if (layer + i + j) % 2 == 0:
                    parts = [(i, i + 0.5, j, j + 1), (i + 0.5, i + 1, j, j + 1)]
                else:
                    parts = [(i, i + 1, j, j + 0.5), (i, i + 1, j + 0.5, j + 1)]
                for k, (x0, x1, y0, y1) in enumerate(parts):
                    out.append(Blk(x0, x1, y0, y1, z0, z0 + 0.5, 'hay', s + layer * 7 + k))
            else:
                for a in range(2):
                    for b in range(2):
                        keg = (not top) and rnd(s, layer * 10 + a * 2 + b) < 0.28
                        out.append(Blk(i + a * 0.5, i + a * 0.5 + 0.5, j + b * 0.5, j + b * 0.5 + 0.5, z0, z0 + 0.5, 'keg' if keg else 'crate', s + layer * 11 + a * 2 + b))
    return out


def goods(x, y, z, colours, seed):
    """A little heap of goods on a counter: boxes of a few colours."""
    out = []
    for k, c in enumerate(colours):
        sz = 0.1 + 0.04 * rnd(seed, 500 + k)
        out.append(Blk(x + 0.14 * k, x + 0.14 * k + sz, y + 0.04 * rnd(seed, 510 + k), y + 0.04 * rnd(seed, 510 + k) + sz, z, z + 0.09, 'goods', seed + k, colour=c))
    return out


def stall_flat(cells, warm, seed):
    """A canvas roof at one level on posts, with an open front (+x) and a counter; the roof is the walkable top."""
    n = max(i for i, _ in cells) + 1
    m = max(j for _, j in cells) + 1
    out = []
    for px_ in sorted({0.0, float(n) - 0.07} | ({0.5 * n - 0.035} if n > 1 else set())):
        for py_ in sorted({0.0, float(m) - 0.07}):
            out.append(Blk(px_, px_ + 0.07, py_, py_ + 0.07, 0, 0.92, 'plank', seed))
    out.append(Blk(0.0, 0.05, 0.0, float(m), 0, 0.92, 'plank', seed + 1))                                     # the back
    out.append(Blk(float(n) - 0.28, float(n) - 0.08, 0.1, float(m) - 0.1, 0, 0.45, 'plank', seed + 2))         # the counter
    out += goods(float(n) - 0.3, 0.2, 0.45, ['e', 'd', 'z', 'e'][: 2 + int(m)], seed)
    out.append(Blk(0.0, float(n), 0.0, float(m), 0.92, 1.0, 'cloth', seed + 3, colour='warm' if warm else 'cool'))
    return out


def stall_slope(cells, warm, seed):
    """A sloping awning, high at the back and low at the front, over a counter: cover, but not a top to stand on."""
    n = max(i for i, _ in cells) + 1
    m = max(j for _, j in cells) + 1
    out = []
    for py_ in sorted({0.0, float(m) - 0.07}):
        out.append(Blk(0.0, 0.07, py_, py_ + 0.07, 0, 1.0, 'plank', seed))
        out.append(Blk(float(n) - 0.07, float(n), py_, py_ + 0.07, 0, 0.7, 'plank', seed + 1))
    out.append(Blk(float(n) - 0.34, float(n) - 0.1, 0.1, float(m) - 0.1, 0, 0.42, 'plank', seed + 2))
    out += goods(float(n) - 0.36, 0.2, 0.42, ['d', 'e', 'z', 'd'][: 2 + int(m)], seed)
    k = 0.3 / n
    top = plane((k, 0, 1), (0, 0, 1.0))
    bottom = plane((-k, 0, -1), (0, 0, 0.94))
    cloth = Solid([top, bottom, ((1, 0, 0), float(n)), ((-1, 0, 0), 0.0), ((0, 1, 0), float(m)), ((0, -1, 0), 0.0)], 'cloth')
    cloth.top, cloth.b, cloth.colour, cloth.seed = 1.0, (0, n, 0, m, 0.7, 1.0), 'warm' if warm else 'cool', seed
    return out + [cloth]


def shed(cells, level, open_dir, seed):
    """A hut with a flat plank roof at `level` and one open side (+x = 'se' or +y = 'sw'): an alcove with a crate and a bale in it."""
    n = max(i for i, _ in cells) + 1
    m = max(j for _, j in cells) + 1
    out = []
    t = 0.16
    H = float(level)
    roof = Blk(0.0, float(n), 0.0, float(m), H - 0.12, H, 'plank', seed)
    if open_dir == 'se':                                                       # open to +x: back wall at x = 0, side walls along x
        out += [Blk(0.0, t, 0.0, float(m), 0, H - 0.12, 'wood', seed + 1), Blk(0.0, float(n), 0.0, t, 0, H - 0.12, 'wood', seed + 2), Blk(0.0, float(n), float(m) - t, float(m), 0, H - 0.12, 'wood', seed + 3)]
        for k in range(1, m):
            out.append(Blk(0.0, float(n), k - 0.06, k + 0.06, 0, H - 0.12, 'wood', seed + 4 + k))
        out.append(Blk(t + 0.04, t + 0.4, t + 0.1, t + 0.5, 0, 0.5, 'hay', seed + 9))
        out.append(Blk(t + 0.04, t + 0.34, float(m) - t - 0.4, float(m) - t - 0.1, 0, 0.5, 'crate', seed + 10))
    else:                                                                      # open to +y
        out += [Blk(0.0, float(n), 0.0, t, 0, H - 0.12, 'wood', seed + 1), Blk(0.0, t, 0.0, float(m), 0, H - 0.12, 'wood', seed + 2), Blk(float(n) - t, float(n), 0.0, float(m), 0, H - 0.12, 'wood', seed + 3)]
        for k in range(1, n):
            out.append(Blk(k - 0.06, k + 0.06, 0.0, float(m), 0, H - 0.12, 'wood', seed + 4 + k))
        out.append(Blk(t + 0.1, t + 0.5, t + 0.04, t + 0.4, 0, 0.5, 'hay', seed + 9))
        out.append(Blk(float(n) - t - 0.4, float(n) - t - 0.1, t + 0.04, t + 0.34, 0, 0.5, 'crate', seed + 10))
    return out + [roof]


def wheel(x0, x1, y0, y1, z0, z1, seed):
    return Blk(x0, x1, y0, y1, z0, z1, 'wheel', seed)


def cart(load, along, seed):
    """A one-cell cart along x or y, loaded to a flat top at one level. `load` is 'hay' or 'crates'."""
    out = []
    if along == 'x':
        out.append(Blk(0.04, 0.96, 0.1, 0.9, 0.28, 0.4, 'plank', seed))
        for y0 in (0.03, 0.9):
            out.append(wheel(0.28, 0.72, y0, y0 + 0.07, 0.0, 0.44, seed))
        out += cart_load(load, (0.05, 0.95, 0.1, 0.9), seed)
    else:
        out.append(Blk(0.1, 0.9, 0.04, 0.96, 0.28, 0.4, 'plank', seed))
        for x0 in (0.03, 0.9):
            out.append(wheel(x0, x0 + 0.07, 0.28, 0.72, 0.0, 0.44, seed))
        out += cart_load(load, (0.1, 0.9, 0.05, 0.95), seed)
    return out


def cart_load(load, box, seed):
    x0, x1, y0, y1 = box
    if load == 'hay':
        return [Blk(x0, x1, y0, y1, 0.4, 1.0, 'hay', seed + 7)]
    out = []
    nx = 2 if (x1 - x0) < 1.5 else 4
    ny = 2 if (y1 - y0) < 1.5 else 4
    if (x1 - x0) > (y1 - y0) * 1.5:
        ny = 2
    elif (y1 - y0) > (x1 - x0) * 1.5:
        nx = 2
    for a in range(nx):
        for b in range(ny):
            out.append(Blk(x0 + (x1 - x0) * a / nx, x0 + (x1 - x0) * (a + 1) / nx, y0 + (y1 - y0) * b / ny, y0 + (y1 - y0) * (b + 1) / ny, 0.4, 1.0,
                           'keg' if (a + 2 * b) % 5 == 4 else 'crate', seed + 11 * a + b))
    return out


def wagon(load, along, n, seed):
    """A wagon n cells long along x or y with four wheels, loaded to a flat top at one level."""
    out = []
    L = float(n)
    if along == 'x':
        out.append(Blk(0.04, L - 0.04, 0.1, 0.9, 0.3, 0.42, 'plank', seed))
        for xc in (0.35, L - 0.35):
            for y0 in (0.03, 0.9):
                out.append(wheel(xc - 0.3, xc + 0.3, y0, y0 + 0.07, 0.0, 0.6, seed))
        out += cart_load(load, (0.05, L - 0.05, 0.1, 0.9), seed)
    else:
        out.append(Blk(0.1, 0.9, 0.04, L - 0.04, 0.3, 0.42, 'plank', seed))
        for yc in (0.35, L - 0.35):
            for x0 in (0.03, 0.9):
                out.append(wheel(x0, x0 + 0.07, yc - 0.3, yc + 0.3, 0.0, 0.6, seed))
        out += cart_load(load, (0.1, 0.9, 0.05, L - 0.05), seed)
    return out


def build_pieces():
    P = []

    def add(id, label, cells, fn, heights=None, cover=None, kind=''):
        P.append(Piece(id, label, cells, fn, heights, cover, kind))

    def uniform(cells, h):
        return {c: h for c in cells}

    stacks = [
        ('1x1-h1', 'Haybale stack 1 x 1, 1 high', rect(1, 1), None, 1), ('1x1-h2', 'Haybale stack 1 x 1, 2 high', rect(1, 1), None, 2),
        ('1x2-h1', 'Haybale stack 1 x 2, 1 high', rect(1, 2), None, 1), ('2x1-h1', 'Haybale stack 2 x 1, 1 high', rect(2, 1), None, 1),
        ('2x2-h1', 'Haybale stack 2 x 2, 1 high', rect(2, 2), None, 1),
        ('2x2-stepped', 'Haybale stack 2 x 2, stepped', rect(2, 2), {(0, 0): 2, (1, 0): 1, (0, 1): 1, (1, 1): 1}, None),
        ('2x1-stepped', 'Haybale stack 2 x 1, stepped', rect(2, 1), {(0, 0): 2, (1, 0): 1}, None),
        ('1x2-stepped', 'Haybale stack 1 x 2, stepped', rect(1, 2), {(0, 0): 2, (0, 1): 1}, None),
        ('3x1-stepped', 'Haybale stack 3 x 1, stepped', rect(3, 1), {(0, 0): 2, (1, 0): 1, (2, 0): 1}, None)]
    for name, label, cells, lv, h in stacks:
        heights = lv or uniform(cells, h)
        add(f'low-hay-{name}', label, cells, (lambda hh: lambda seed: stack(hh, 'hay', seed))(heights), heights=heights, kind='hay')
    crates = [
        ('1x1-h1', 'Crate pile 1 x 1, 1 high', rect(1, 1), {(0, 0): 1}), ('1x1-h2', 'Crate pile 1 x 1, 2 high', rect(1, 1), {(0, 0): 2}),
        ('2x1-stepped', 'Crate pile 2 x 1, stepped', rect(2, 1), {(0, 0): 2, (1, 0): 1}), ('1x2-stepped', 'Crate pile 1 x 2, stepped', rect(1, 2), {(0, 0): 2, (0, 1): 1}),
        ('2x2-stepped', 'Crate pile 2 x 2, stepped', rect(2, 2), {(0, 0): 2, (1, 0): 1, (0, 1): 1, (1, 1): 1}),
        ('l-stepped', 'Crate pile, L, stepped', lshape('s'), {(0, 0): 2, (1, 0): 1, (0, 1): 1})]
    for name, label, cells, heights in crates:
        add(f'low-crates-{name}', label, cells, (lambda hh: lambda seed: stack(hh, 'crates', seed))(heights), heights=heights, kind='crates')
    for name, label, cells, warm in (('1x1', 'Market stall 1 x 1, canvas roof (walkable)', rect(1, 1), True), ('1x1-cool', 'Market stall 1 x 1, teal canvas roof (walkable)', rect(1, 1), False),
                                     ('2x1', 'Market stall 2 x 1, canvas roof (walkable)', rect(2, 1), True), ('1x2', 'Market stall 1 x 2, canvas roof (walkable)', rect(1, 2), False)):
        add(f'low-stall-{name}', label, cells, (lambda c, w: lambda seed: stall_flat(c, w, seed))(cells, warm), heights=uniform(cells, 1), kind='stall')
    for name, label, cells, warm in (('slope-1x1', 'Market stall 1 x 1, sloping awning', rect(1, 1), True), ('slope-2x1', 'Market stall 2 x 1, sloping awning', rect(2, 1), False)):
        add(f'low-stall-{name}', label, cells, (lambda c, w: lambda seed: stall_slope(c, w, seed))(cells, warm), cover='high', kind='stall')
    for name, label, cells, lv, d in (('1x1-h1-se', 'Shed 1 x 1, 1 high, open to the SE', rect(1, 1), 1, 'se'), ('1x1-h1-sw', 'Shed 1 x 1, 1 high, open to the SW', rect(1, 1), 1, 'sw'),
                                      ('1x1-h2-se', 'Shed 1 x 1, 2 high, open to the SE', rect(1, 1), 2, 'se'), ('1x1-h2-sw', 'Shed 1 x 1, 2 high, open to the SW', rect(1, 1), 2, 'sw'),
                                      ('2x1-h1-sw', 'Shed 2 x 1, 1 high, open to the SW', rect(2, 1), 1, 'sw'), ('1x2-h1-se', 'Shed 1 x 2, 1 high, open to the SE', rect(1, 2), 1, 'se')):
        add(f'low-shed-{name}', label, cells, (lambda c, l, dd: lambda seed: shed(c, l, dd, seed))(cells, lv, d), heights=uniform(cells, lv), kind='shed')
    for name, label, cells, along, load in (('hay', 'Hay cart (along SE)', rect(1, 1), 'x', 'hay'), ('crates', 'Crate cart (along SW)', rect(1, 1), 'y', 'crates')):
        add(f'low-cart-{name}', label, cells, (lambda a, ld: lambda seed: cart(ld, a, seed))(along, load), heights=uniform(cells, 1), kind='cart')
    for name, label, cells, along, load, n in (('2x1-hay', 'Hay wagon 2 x 1', rect(2, 1), 'x', 'hay', 2), ('2x1-crates', 'Crate wagon 2 x 1', rect(2, 1), 'x', 'crates', 2),
                                               ('1x2-hay', 'Hay wagon 1 x 2', rect(1, 2), 'y', 'hay', 2)):
        add(f'low-wagon-{name}', label, cells, (lambda a, ld, nn: lambda seed: wagon(ld, a, nn, seed))(along, load, n), heights=uniform(cells, 1), kind='wagon')
    return P


PIECES = None


def pieces():
    global PIECES
    if PIECES is None:
        PIECES = build_pieces()
    return PIECES


def build_assets():
    return mr.finish(pieces(), CATEGORY, FOLDER)


def write_package(folder):
    mr.package(folder, pieces(), 'low-structures.json', 'The low climbable structures in this folder. See README.md beside this file.')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        mr.draw_preview(args.preview, pieces())
        print('the low structures ->', args.preview)


if __name__ == '__main__':
    main()
