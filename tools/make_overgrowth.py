#!/usr/bin/env python3
"""The Overgrowth map: ground, vines, flowers and a floor generator for a climbing node map (floating mossy islands in a purple void, a flower on every node).

It is a second look for the same job as tools/make_nodemap.py (a Slay-the-Spire-style floor map), with no water and no roads. Everything is palette roles.

THE GROUND is a dual grid like the node map's: land-or-void cells, and a 16 x 16 tile on every corner between four cells, picked by which corners are land (TL 1, TR 2, BL 4, BR 8).
A tile is drawn from a smooth field (its four corners blended), so two tiles always join. On top of that:
    * a LIP and a RIM: the land's edge is a dark moss lip on its south and sides and a light rim on its north;
    * a CLIFF: under every south-facing edge the island ends in earth with roots hanging from it. The cliff is part of the tile that has the edge, and when it is long enough to
      run past the bottom of that tile, the rest is in a SPILL tile (16 of them, one for each tile above), drawn one row down and UNDER the ground layer, so land always covers it;
    * six FULL tiles (corner bits 15) that differ only inside their middle (clover, leaf litter and flowers, root veins, pebbles, glowing moss), so open ground is not flat.
THE DECOR is loose: mushrooms, crystals, rocks, ferns, bushes, wisps, hanging vines (they hang from the cliff lip) and root tendrils that cross the ground (32 x 32, several shapes).
THE FLOWERS are the nodes: a battle bud, an event flame, an elite eye, a shop marigold, a rest lotus, a treasure bulb, a mystery orchid and the summit's fire lotus, 4 frames each.
THE GENERATOR makes a floor: paths climb from the bottom to the boss, types are dealt out by rules, islands and winding vine bridges are carved round them, and floating islets are
scattered in the void. A layout is a seed and a preset; the same seed gives the same floor.

    python3 tools/make_overgrowth.py --preview previews/overgrowth.png     the tiles, the decor, the flowers and three floors
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

TILE = 16
BANK = 0.06
TL, TR, BL, BR = 1, 2, 4, 8
CLIFF = 9                  # rows of earth under a south edge
ROOT = 6                   # how much further a root hangs
MAX_DROP = CLIFF + ROOT + 1

GREEN = ('z', 'A', 'B', 's')
GROUND = dict(base='B', speck='s', light='A', tuft='z', rim='z', lip='s', side='s')
EARTH = ('B', 's', 's', 'l', 'g', 'g', 'w', 'w', 'x')          # the cliff face, top to bottom: moss shading into dark earth
ROOT_ROLES = ('b', 'a', 'g')        # the twisted roots: lit, mid, shadow
CLIFF_ROOTS = ('a', 'e', 'g')       # the roots in the cliff: quieter than the loose ones


def hashed(x, y, salt=0):
    n = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


def smooth(u):
    return u * u * (3 - 2 * u)


def vnoise(x, y, salt=0):
    """Smooth value noise, 0 to 1, with one lattice point per unit."""
    x0, y0 = math.floor(x), math.floor(y)
    u, v = smooth(x - x0), smooth(y - y0)
    a, b = hashed(x0, y0, salt) / 65535, hashed(x0 + 1, y0, salt) / 65535
    c, d = hashed(x0, y0 + 1, salt) / 65535, hashed(x0 + 1, y0 + 1, salt) / 65535
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def pnoise(x, y, period, salt=0):
    """Value noise that wraps every `period` lattice units, so a texture made from it repeats seamlessly."""
    x0, y0 = math.floor(x), math.floor(y)
    u, v = smooth(x - x0), smooth(y - y0)
    h = lambda a, b: hashed(a % period, b % period, salt) / 65535
    return (h(x0, y0) * (1 - u) + h(x0 + 1, y0) * u) * (1 - v) + (h(x0, y0 + 1) * (1 - u) + h(x0 + 1, y0 + 1) * u) * v


# --- a small canvas to draw on -------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def put(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def rows(self):
        return [''.join(r) for r in self.g]

    def outline(self, role='O'):
        solid = {(x, y) for y in range(self.h) for x in range(self.w) if self.g[y][x] != '.'}
        for x, y in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in solid:
                    self.put(x + dx, y + dy, role)

    def sparks(self, points, role):
        """A few bright pixels on empty ground, for glow."""
        for x, y in points:
            if self.get(x, y) == '.':
                self.put(x, y, role)


def ramp_at(ramp, v):
    return ramp[0 if v > 0.72 else 1 if v > 0.46 else 2 if v > 0.24 else 3]


def ball(cv, cx, cy, rx, ry, ramp, light=(-0.55, -0.75), only=None):
    """A shaded ellipsoid."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = nx * nx + ny * ny
            if d <= 1.0:
                nz = math.sqrt(max(0.0, 1 - d))
                v = 0.5 + 0.45 * (-(nx * light[0] + ny * light[1])) + 0.3 * (nz - 0.5)
                if only is None or only(x, y):
                    cv.put(x, y, ramp_at(ramp, v))


def petal(cv, bx, by, vx, vy, length, width, ramp, pointed=1.0, vein=False, base_w=0.0, edge=True):
    """A petal or a leaf from (bx, by) along (vx, vy): pointed or round, shaded across and along, with an optional midrib."""
    n = math.hypot(vx, vy) or 1.0
    ax, ay = vx / n, vy / n
    px, py = -ay, ax
    R = int(length + width) + 2
    for y in range(int(by) - R, int(by) + R + 1):
        for x in range(int(bx) - R, int(bx) + R + 1):
            rx, ry = x + 0.5 - bx, y + 0.5 - by
            s = (rx * ax + ry * ay) / length
            t = rx * px + ry * py
            if s < 0 or s > 1:
                continue
            body = (4 * s * (1 - s)) ** 0.62 if pointed >= 1.0 else math.sqrt(max(0.0, 1 - (2 * s - 1) ** 2)) ** (0.9 / max(pointed, 0.3))
            hw = width / 2 * (base_w + (1 - base_w) * body)
            if abs(t) > hw:
                continue
            lat = t / max(hw, 0.01)
            v = 0.52 + 0.3 * (-lat * (-0.55 * px - 0.75 * py) * 1.4) + 0.32 * (s - 0.45)
            ch = ramp_at(ramp, v)
            if edge and hw - abs(t) < 0.9 and s < 0.96 and t * (-0.55 * px - 0.75 * py) < 0:
                ch = ramp[min(3, ramp.index(ch) + 1)] if ch in ramp else ch                                   # the shadow edge, so overlapping petals read apart
            if vein and abs(t) < 0.5 and 0.12 < s < 0.85:
                ch = ramp[min(3, ramp.index(ch) + 1)] if ch in ramp else ch
            cv.put(x, y, ch)


def line(cv, x0, y0, x1, y1, ch, thick=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        for ox in range(thick):
            for oy in range(thick):
                cv.put(int(x) + ox, int(y) + oy, ch)


# --- the ground --------------------------------------------------------------------------------
def field(bits, x, y):
    u, v = (x + 0.5) / TILE, (y + 0.5) / TILE
    return ((bits & TL > 0) * (1 - u) * (1 - v) + (bits & TR > 0) * u * (1 - v) + (bits & BL > 0) * (1 - u) * v + (bits & BR > 0) * u * v)


def land_grid(bits):
    return [[field(bits, x, y) > 0.5 for x in range(TILE)] for y in range(TILE)]


STYLES = 5            # cliff styles: each tile picks one, and they all end the same at the tile's left and right sides, so any two join


def drop_of(x, style=0):
    """How far the cliff goes down a column. A style gives a tile its own ragged edge and roots; columns 0 and 15 are the same in every style, so neighbours always join."""
    if x in (0, TILE - 1):
        return CLIFF - 1
    h = hashed(x, style, 5)
    depth = CLIFF - 3 + (h % 4) + (1 if hashed(x - 1, style, 5) % 4 > 2 else 0)
    return depth


def root_columns(style):
    """The columns of a style that a twisted root (two pixels wide) hangs from, each with its length."""
    out = {}
    r = random.Random(style * 977 + 13)
    x = 1 + r.randrange(3)
    while x < TILE - 2:
        length = CLIFF + 1 + r.randrange(ROOT + 2)
        out[x] = out[x + 1] = min(length, 14)
        x += 2 + r.randrange(4, 8)
    return out


def cliff_pixel(x, d, depth, style=0):
    """The pixel d rows under the edge (0 is the first row of earth) in a column that goes `depth` down."""
    if d >= depth:
        return None
    h = hashed(x, style, 9)
    if x in root_columns(style) and d >= 1:
        twist = (d + (x % 2) * 2) % 4 < 2
        return CLIFF_ROOTS[0] if twist and d < depth - 1 else CLIFF_ROOTS[1] if d < depth - 1 else CLIFF_ROOTS[2]          # a twisted root
    if d == 0:
        return 'A' if h % 3 == 0 else 'B'
    if d == 1 and h % 4 == 0:
        return 'A'                                                                                                     # moss dripping over
    if d == 2 and h % 7 == 0:
        return 'B'
    return EARTH[min(d, len(EARTH) - 1)] if d < depth - 1 else 'x'


def column_depth(x, style):
    return root_columns(style).get(x) or drop_of(x, style)


def ground_tile(bits, variant=0, style=0):
    """One 16 x 16 ground tile as roles, '.' where it is open void. Full tiles come in several variants (see FULL_VARIANTS)."""
    g = GROUND
    land = land_grid(bits)
    cv = Canvas(TILE, TILE)
    for y in range(TILE):
        for x in range(TILE):
            f = field(bits, x, y)
            if f <= 0.5:
                continue
            if f > 0.5 + BANK:
                h = hashed(x % TILE, y % TILE)
                ch = g['base']
                if h % 17 == 0:
                    ch = g['speck']
                elif h % 23 == 0:
                    ch = g['light']
                elif h % 61 == 0:
                    ch = g['tuft']
            else:
                u, v = (x + 0.5) / TILE, (y + 0.5) / TILE
                gy = (1 - u) * ((bits & BL > 0) - (bits & TL > 0)) + u * ((bits & BR > 0) - (bits & TR > 0))
                ch = g['rim'] if gy > 0.15 else g['lip']
            cv.put(x, y, ch)
    for x in range(TILE):
        depth = column_depth(x, style)
        for y in range(TILE):
            if land[y][x] and (y + 1 >= TILE or not land[y + 1][x]):
                if y + 1 >= TILE:
                    continue                                                                                   # runs on into the next tile
                d = 0
                while y + 1 + d < TILE and not land[y + 1 + d][x]:
                    ch = cliff_pixel(x, d, depth, style)
                    if ch is None:
                        break
                    cv.put(x, y + 1 + d, ch)
                    d += 1
    if bits == 15 and variant >= PLAIN:
        decorate_full(cv, variant - PLAIN + 1)
    return cv.rows()


def spill_tile(bits, style=0):
    """What a tile's cliff leaves over the bottom of it: drawn one row down, under the ground layer."""
    land = land_grid(bits)
    cv = Canvas(TILE, TILE)
    for x in range(TILE):
        depth = column_depth(x, style)
        for y in range(TILE):
            if land[y][x] and (y + 1 >= TILE or not land[y + 1][x]):
                for d in range(depth):
                    r = y + 1 + d - TILE
                    if r >= 0:
                        ch = cliff_pixel(x, d, depth, style)
                        if ch:
                            cv.put(x, r, ch)
    return cv.rows()


FULL_VARIANTS = ['plain moss', 'clover', 'leaf litter and flowers', 'root veins', 'pebbles', 'glowing moss']
PLAIN = 1


def decorate_full(cv, variant):
    """Variants of the all-land tile change only the middle (3 pixels in from every side stay as they are), so every variant joins every neighbour."""
    if variant == 0:
        return
    r = random.Random(variant * 101)
    inner = lambda x, y: 3 <= x <= TILE - 4 and 3 <= y <= TILE - 4
    if variant == 1:
        for cx, cy in ((5, 6), (10, 5), (8, 10)):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                if inner(cx + dx, cy + dy):
                    cv.put(cx + dx, cy + dy, 'A' if (dx, dy) != (0, 0) else 'z')
    elif variant == 2:
        for _ in range(7):
            x, y = r.randint(3, TILE - 4), r.randint(3, TILE - 4)
            cv.put(x, y, r.choice('zzA'))
        for x, y, ch in ((6, 7, 'j'), (11, 9, 't'), (5, 11, 'd')):
            cv.put(x, y, ch)
    elif variant == 3:
        pts = [(3, 9), (5, 8), (7, 8), (9, 7), (11, 6), (12, 5)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            line(cv, x0, y0, x1, y1, 'g')
        for x, y in pts[1:-1]:
            if inner(x, y - 1):
                cv.put(x, y - 1, 'f')
    elif variant == 4:
        for cx, cy, ch in ((5, 6, 'p'), (10, 9, 'l'), (8, 5, 'q')):
            cv.put(cx, cy, ch)
            cv.put(cx + 1, cy, ch)
            cv.put(cx, cy + 1, 'k')
    elif variant == 5:
        for x, y, ch in ((5, 5, 'o'), (10, 6, 'r'), (7, 10, 'o'), (11, 11, 'r'), (4, 9, 'q')):
            cv.put(x, y, ch)


# --- decor: loose pieces ----------------------------------------------------------------------------
CAPS = {'purple': ('v', 'f', 'g', 'w'), 'blue': ('r', 'o', 'n', 'm'), 'red': ('E', 'F', 'G', 'x')}
STEM = ('t', 'C', 'p', 'l')


def mushroom(kind, size=1, frame=0):
    """A mushroom cluster, 24 x 24, anchored at (12, 21)."""
    cv = Canvas(24, 24)
    spots = {'purple': ((11, 20, 7.5, 5.6), (4, 21, 4.2, 3.4), (19, 21, 4.4, 3.5), (15, 17, 3.4, 2.8)),
             'blue': ((11, 20, 6.5, 5.0), (5, 21, 4.2, 3.2), (18, 20, 3.6, 3.0)),
             'red': ((9, 20, 7.2, 5.6), (18, 21, 4.6, 3.6))}[kind]
    for sx, sy, rw, rh in sorted(spots, key=lambda s: s[1]):
        top = sy - rh * 1.7
        ball(cv, sx, sy - rh * 0.55, rw * 0.26 + 0.6, rh * 0.95, STEM)
        ball(cv, sx, top + rh * 0.55, rw, rh * 0.7, CAPS[kind])
        for k in range(3 if rw > 5 else 1):
            dx, dy = ((-0.45, -0.2), (0.35, 0.05), (0.0, -0.45))[k]
            x, y = int(sx + dx * rw), int(top + rh * 0.55 + dy * rh)
            if cv.get(x, y) != '.':
                cv.put(x, y, 't' if kind != 'blue' else 'r')
                if rw > 5:
                    cv.put(x + 1, y, 't' if kind != 'blue' else 'r')
    cv.outline()
    return cv.rows()


def crystal(kind, frame=0):
    """A cluster of crystals, 16 x 16, anchored at (8, 14)."""
    cv = Canvas(16, 16)
    ramp = {'violet': ('t', 'v', 'l', 'k'), 'cyan': ('t', 'o', 'n', 'm')}[kind]
    for bx, lean, length, width in ((5, -0.35, 8, 4), (11, 0.3, 7, 3.6), (8, 0.0, 11, 5)):
        petal(cv, bx, 14, lean * 8, -length, length, width, ramp, pointed=1.0)
    cv.outline()
    return cv.rows()


def rock(variant=0):
    cv = Canvas(16, 16)
    if variant == 0:
        ball(cv, 8, 11, 6, 4, ('q', 'p', 'l', 'k'))
        ball(cv, 8, 8.2, 4, 1.7, ('z', 'A', 'B', 's'), only=lambda x, y: y < 10)
    else:
        ball(cv, 6, 11.5, 4, 3, ('q', 'p', 'l', 'k'))
        ball(cv, 11, 12, 3.3, 2.4, ('p', 'l', 'k', 'x'))
        ball(cv, 6, 9.6, 2.7, 1.2, ('z', 'A', 'B', 's'), only=lambda x, y: y < 11)
    cv.outline()
    return cv.rows()


def fern(variant=0):
    cv = Canvas(16, 16)
    for a in (-62, -34, -8, 20, 48):
        r = math.radians(a + variant * 7)
        petal(cv, 8, 14, math.sin(r) * 9, -math.cos(r) * 9, 9, 3.4, ('z', 'A', 'B', 's'), vein=True)
    cv.outline()
    return cv.rows()


def bush(variant=0):
    """A leafy shrub, 32 x 32, anchored at (16, 28)."""
    cv = Canvas(32, 32)
    flowers = ('j', 'v') if variant == 0 else ('d', 't')
    angles = (-75, -48, -22, 0, 22, 48, 75) if variant == 0 else (-68, -35, -8, 14, 40, 66)
    for i, a in enumerate(sorted(angles, key=abs, reverse=True)):
        r = math.radians(a)
        L = 13 + (hashed(i, variant) % 4)
        petal(cv, 16, 28, math.sin(r) * L, -math.cos(r) * L * 0.9, L, 8, ('z', 'A', 'B', 's'), vein=True)
    ball(cv, 16, 26, 7, 3, ('A', 'B', 's', 'D'))
    for k in range(5):
        x, y = 8 + hashed(k, variant, 3) % 17, 11 + hashed(k, variant, 4) % 12
        if cv.get(x, y) != '.':
            cv.put(x, y, flowers[k % 2])
            cv.put(x + 1, y, flowers[k % 2])
    cv.outline()
    return cv.rows()


def wisp(frame):
    """A will-o'-the-wisp: a blue flame, 4 frames, 16 x 16 anchored at (8, 14)."""
    cv = Canvas(16, 16)
    sway = (0, 1, 0, -1)[frame]
    h = (9, 10, 9, 8)[frame]
    petal(cv, 8, 14, sway * 1.5, -h, h, 7, ('t', 'o', 'n', 'm'), pointed=1.0, base_w=0.35)
    petal(cv, 8, 14, sway, -h * 0.55, h * 0.55, 3.4, ('t', 't', 'r', 'o'), pointed=1.0, base_w=0.3)
    cv.outline('m')
    cv.sparks(((3, 6 + frame % 2), (13, 8 - frame % 2), (12 - frame, 2 + frame)), 'o')
    return cv.rows()


def strand(cv, pts, ramp=ROOT_ROLES, thick=3):
    """A thick root along a path: lit on top (or the left when it runs up and down), mid in the middle, shadowed below."""
    for k, (x, y) in enumerate(pts):
        a, b = pts[max(0, k - 2)], pts[min(len(pts) - 1, k + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) >= abs(dy):
            for i in range(thick):
                cv.put(int(x), int(y) + i, ramp[min(2, i * 3 // thick)] if (k // 3) % 3 else ramp[min(2, i * 3 // thick + (1 if i == 0 else 0))])
        else:
            for i in range(thick):
                cv.put(int(x) + i, int(y), ramp[min(2, i * 3 // thick)] if (k // 3) % 3 else ramp[min(2, i * 3 // thick + (1 if i == 0 else 0))])


def twist(cv, pts, thick=2):
    """Two roots wound round each other along a path."""
    n = len(pts)
    a, b = [], []
    for k, (x, y) in enumerate(pts):
        p, q = pts[max(0, k - 1)], pts[min(n - 1, k + 1)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        off = 1.7 * math.sin(k * 0.62)
        a.append((x + nx * off, y + ny * off))
        b.append((x - nx * off, y - ny * off))
    strand(cv, b, thick=thick)
    strand(cv, a, thick=thick)


def leaf_at(cv, x, y, side, size=6, ramp=GREEN):
    petal(cv, x, y, side * size * 0.9, -size * 0.5, size, size * 0.55, ramp, vein=True)


def vine_hang(variant):
    """A root vine hanging from a cliff lip, 20 x 34 anchored at (10, 0) (the top): a twisted pair of roots with leaves and now and then a blossom."""
    cv = Canvas(20, 34)
    length = (16, 24, 32, 20, 29, 13)[variant % 6]
    r = random.Random(variant + 3)
    ph = r.random() * 6
    sw, fr = ((3.0, 0.33), (1.6, 0.5), (3.6, 0.25))[variant % 3]
    pts = [(10 + sw * math.sin(y * fr + ph) * min(1, y / 5), y) for y in range(length)]
    twist(cv, pts)
    for i in range(5, length - 2, 6):
        x, y = pts[i]
        leaf_at(cv, x, y, 1 if (i // 6) % 2 == 0 else -1, 6)
    x, y = pts[-1]
    if variant % 3 == 2:
        for dx, dy, ch in ((0, 1, 'v' if variant < 3 else 'o'), (1, 1, 'f' if variant < 3 else 'r'), (-1, 2, 'v' if variant < 3 else 'o'), (0, 2, 'j' if variant < 3 else 't'), (0, 3, 'v' if variant < 3 else 'o')):
            cv.put(int(x) + dx, int(y) + dy, ch)
    cv.outline('x')
    return cv.rows()


def moss_drape(variant):
    """Moss hanging off a cliff lip in a trail of leaves and drops, 12 x 28 anchored at (6, 0) (the top)."""
    cv = Canvas(12, 28)
    r = random.Random(variant * 31 + 5)
    length = (9, 14, 20, 26)[variant % 4]
    x = 6.0
    for y in range(length):
        x += r.uniform(-0.5, 0.5)
        x = max(3.0, min(8.0, x))
        w = 1.0 + (1.2 if y % 5 in (1, 2) else 0.0) * (1 - y / (length + 2))
        for k in range(-int(w), int(w) + 1):
            cv.put(int(x) + k, y, 'A' if k == -int(w) and y % 2 else 'B' if abs(k) < w else 's')
    for i in range(2, length - 2, 4):
        side = 1 if (i // 4 + variant) % 2 else -1
        petal(cv, 6 + side, i, side * 4.2, 2.6, 4.6, 2.8, GREEN, edge=False)
    cv.put(int(x), length, 'A')
    cv.put(int(x), length + 1, 'z' if variant % 2 else 'B')
    cv.outline('D')
    return cv.rows()


def tendril(variant):
    """A twisted root lying over open ground, with leaves, 32 x 32 (transparent round it)."""
    cv = Canvas(32, 32)
    r = random.Random(variant * 17 + 1)
    x0, y0 = r.choice((2, 4)), r.randint(8, 22)
    ang = r.uniform(-0.5, 0.5)
    pts = []
    x, y = x0, y0
    for i in range(64):
        x += math.cos(ang) * 0.5
        y += math.sin(ang) * 0.5
        ang += 0.2 * math.sin(i * 0.17 + variant * 1.3) + r.uniform(-0.06, 0.06)
        if not (2 < x < 29 and 2 < y < 28):
            break
        pts.append((x, y))
    twist(cv, pts)
    for i in range(7, len(pts) - 4, 9):
        x, y = pts[i]
        leaf_at(cv, x, y, 1 if (i // 9) % 2 else -1, 6)
    if variant % 2:
        x, y = pts[len(pts) // 2]
        for dx, dy, ch in ((0, -1, 'j'), (1, -1, 'y'), (-1, 0, 'j'), (0, 0, 't')):
            cv.put(int(x) + dx, int(y) + dy - 3, ch)
    cv.outline('x')
    return cv.rows()


def moss_patch(variant):
    """A loose patch of ground cover, 32 x 32, laid over open ground so the tile seams do not show: lighter moss with leaf flecks, or a darker hollow, with a dithered edge."""
    cv = Canvas(32, 32)
    dark = variant >= 3
    rx, ry = 10 + (variant * 3) % 5, 8 + (variant * 5) % 4
    for y in range(32):
        for x in range(32):
            nx, ny = (x + 0.5 - 16) / rx, (y + 0.5 - 16) / ry
            d = math.hypot(nx, ny) * (0.8 + 0.4 * vnoise(x / 5.0, y / 5.0, 40 + variant))
            h = hashed(x, y, 50 + variant)
            if d < 0.6 or (d < 0.95 and (x + y) % 2 == 0 and d < 0.62 + 0.38 * (h % 5) / 4):
                if dark:
                    cv.put(x, y, 'D' if h % 5 == 0 else 's')
                else:
                    cv.put(x, y, 'z' if h % 13 == 0 else 'B' if h % 7 == 0 else 'A')
    if not dark:
        for k in range(5):
            x, y = 9 + hashed(k, variant, 7) % 14, 10 + hashed(k, variant, 8) % 12
            if cv.get(x, y) != '.':
                cv.put(x, y, 'z')
                cv.put(x + 1, y - 1, 'z')
    return cv.rows()


def tone_patch(variant):
    """A big soft patch of lighter (variants 0-3) or deeper (4-7) moss, 40 x 40, laid over open ground. It has its own speckle and a ragged, thinning edge, so it blends into the moss
    under it and breaks up the 16 pixel tiles."""
    cv = Canvas(40, 40)
    dark = variant >= 4
    rx, ry = 13 + (variant * 2) % 4, 10 + (variant * 3) % 4
    for y in range(40):
        for x in range(40):
            nx, ny = (x + 0.5 - 20) / rx, (y + 0.5 - 20) / ry
            d = math.hypot(nx, ny) * (0.85 + 0.3 * vnoise(x / 8.0, y / 8.0, 70 + variant))
            h = hashed(x, y, 80 + variant)
            if d < 0.55 or (d < 1.0 and h % 100 < (1.0 - d) / 0.45 * 100):
                if dark:
                    cv.put(x, y, 'D' if h % 6 == 0 else 'B' if h % 11 == 0 else 's')
                else:
                    cv.put(x, y, 'z' if h % 19 == 0 else 'B' if h % 5 == 0 else 'A')
    return cv.rows()


DECOR = []


def decor_assets_spec():
    """(id suffix, label, w, h, anchor, frames builder list)"""
    spec = []
    for kind in ('purple', 'blue', 'red'):
        spec.append((f'mushroom-{kind}', f'Mushrooms ({kind})', 24, 24, (12, 21), [mushroom(kind)]))
    for kind in ('violet', 'cyan'):
        spec.append((f'crystal-{kind}', f'Crystals ({kind})', 16, 16, (8, 14), [crystal(kind)]))
    spec.append(('rock', 'Rocks (2)', 16, 16, (8, 14), [rock(0), rock(1)]))
    spec.append(('fern', 'Ferns (2)', 16, 16, (8, 14), [fern(0), fern(1)]))
    spec.append(('bush', 'Bushes (2)', 32, 32, (16, 28), [bush(0), bush(1)]))
    spec.append(('wisp', 'Wisp (animated)', 16, 16, (8, 14), [wisp(f) for f in range(4)]))
    spec.append(('vine-hang', 'Hanging root vines (6), anchored at the top', 20, 34, (10, 0), [vine_hang(v) for v in range(6)]))
    spec.append(('moss-drape', 'Hanging moss (4), anchored at the top', 12, 28, (6, 0), [moss_drape(v) for v in range(4)]))
    spec.append(('tendril', 'Root tendrils (4)', 32, 32, (16, 16), [tendril(v) for v in range(4)]))
    spec.append(('moss-patch', 'Moss patches (3 light, 2 dark hollows)', 32, 32, (16, 16), [moss_patch(v) for v in range(5)]))
    spec.append(('tone-patch', 'Big moss patches (4 lighter, 4 deeper)', 40, 40, (20, 20), [tone_patch(v) for v in range(8)]))
    return spec


# --- the node flowers -------------------------------------------------------------------------------


ACCENT = {'battle': 'z', 'event': 'o', 'elite': 'E', 'shop': 'd', 'rest': 't', 'treasure': 'v', 'mystery': 'j', 'boss': 'a'}


def pad(cv, cx, cy, rx=8.5, ry=3.2, accent='z'):
    """The clearing a flower stands in: dark earth with a ring of the flower's own colour, so it stands out from the moss."""
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if d <= 1.0:
                if d > 0.88:
                    cv.put(x, y, accent)
                elif d > 0.74:
                    cv.put(x, y, 'x')
                else:
                    cv.put(x, y, 'D' if (x * 3 + y) % 9 else 'k')


def base_leaves(cv, cx, cy):
    for a in (-80, 80, -58, 58):
        r = math.radians(a)
        petal(cv, cx, cy, math.sin(r) * 7, -math.cos(r) * 3.2, 7, 3.2, GREEN)


def rings(cv, bx, by, specs, frame):
    """Draw petal rings back to front. A ring is (count, start deg, spread, lift, length, width, ramp, pointed, squash)."""
    items = []
    for count, start, spread, lift, length, width, ramp, pointed, squash in specs:
        for k in range(count):
            a = math.radians(start + 360 * k / count)
            vx = math.cos(a) * spread
            vy = math.sin(a) * spread * squash - lift
            items.append((math.sin(a) * squash if spread else 0, vx, vy, length, width, ramp, pointed))
    for _, vx, vy, length, width, ramp, pointed in sorted(items, key=lambda i: i[0]):
        petal(cv, bx, by, vx, vy, length, width, ramp, pointed=pointed, vein=True)


def flower_body(kind, frame, size, cx, base, sway, pulse):
    """The flower itself on a blank canvas (no clearing under it): returns (canvas, glow point or None)."""
    cv = Canvas(size, size)
    glow = None
    base_leaves(cv, cx, base - 1)
    if kind == 'battle':
        for a, L, w in ((-50, 13, 5.2), (50, 13, 5.2), (-27, 17, 5.6), (27, 17, 5.6), (-8, 19, 5.8), (9, 19, 5.8)):
            r = math.radians(a)
            petal(cv, cx, base - 1, math.sin(r) * L * 0.62 + sway * 0.5, -math.cos(r) * L, L, w, GREEN, vein=True)
        petal(cv, cx, base - 1, sway * 0.4, -16, 16, 5.2, ('t', 'z', 'A', 'B'), vein=True)
        cv.put(cx - 1, base - 12, 't')
        cv.put(cx - 1, base - 11, 't')
    elif kind == 'event':
        for a, L, w in ((-34, 15, 7.5), (34, 15, 7.5)):
            r = math.radians(a)
            petal(cv, cx, base - 1, math.sin(r) * L * 0.7 + sway * 0.4, -math.cos(r) * L, L, w, ('r', 'o', 'n', 'm'), vein=True)
        petal(cv, cx, base - 1, sway * 0.6, -20, 20, 8.5, ('t', 'r', 'o', 'n'), vein=True)
        petal(cv, cx, base - 2, sway * 0.5, -11, 11, 4.6, ('t', 't', 'r', 'o'), base_w=0.35, edge=False)
        glow = (cx, base - 20, 'o' if pulse else 'r')
    elif kind == 'elite':
        petals = [(7, -90, 11.5, 2.5, 11, 6.4, ('E', 'F', 'G', 'x'), 1.0, 0.5)]
        cy = base - 9
        rings(cv, cx, cy, petals, frame)
        ball(cv, cx, cy - 1, 6.0, 4.5, ('G', 'G', 'x', 'x'))
        ball(cv, cx, cy - 1, 4.4, 3.4, ('t', 't', 'C', 'C'))
        ball(cv, cx + (sway or 0) * 0.5, cy - 1, 2.0, 2.0, ('E', 'E', 'F', 'G'))
        cv.put(cx + (sway or 0) // 1, cy - 2, 'O')
        cv.put(cx + (sway or 0) // 1, cy - 1, 'O')
        for y in range(base - 5, base):
            cv.put(cx, y, 'B')
    elif kind == 'shop':
        cy = base - 6
        rings(cv, cx, cy, [(8, -90, 11.5, 0.5, 10, 6.2, ('b', 'a', 'e', 'g'), 0.7, 0.5), (8, -67, 7.5, 1.5, 8.5, 5.4, ('d', 'd', 'b', 'a'), 0.7, 0.5)], frame)
        ball(cv, cx, cy - 1, 4.6, 3.3, ('b', 'a', 'e', 'e'))
        ball(cv, cx, cy - 1.5, 3.5, 2.4, ('t', 'd', 'b', 'b'))
        cv.put(cx - 1, cy - 2, 'a')
        cv.put(cx, cy - 2, 'a')
        cv.put(cx, cy - 1, 'a')
        glow = (cx, cy - 8, 'd' if pulse else 'b')
    elif kind == 'rest':
        cy = base - 4
        rings(cv, cx, cy, [(8, -90, 11, 1.5, 11, 6.4, ('t', 'C', 'q', 's'), 1.0, 0.5), (6, -60, 6.5, 6.5, 12, 6.2, ('t', 't', 'C', 'q'), 1.0, 0.4)], frame)
        petal(cv, cx, cy - 1, sway * 0.6, -9, 9, 5.2, ('d', 'b', 'a', 'e'), base_w=0.3)
        petal(cv, cx, cy - 1, sway * 0.4, -5, 5, 2.8, ('t', 'd', 'd', 'b'), base_w=0.3)
        glow = (cx, cy - 10, 'd' if pulse else 'b')
    elif kind == 'treasure':
        for a, L, w in ((-62, 11, 8), (62, 11, 8), (-33, 14, 9), (33, 14, 9)):
            r = math.radians(a)
            petal(cv, cx, base - 1, math.sin(r) * L * 0.55, -math.cos(r) * L, L, w, ('v', 'f', 'g', 'w'), pointed=0.8, vein=True)
        petal(cv, cx, base - 1, 0, -17, 17, 9.5, ('v', 'v', 'f', 'g'), pointed=0.8, vein=True)
        ball(cv, cx, base - 17, 2.8, 2.2, ('t', 'd', 'b', 'a'))
        ball(cv, cx, base - 12, 2.0, 1.6, ('t', 'o', 'n', 'm'))
        glow = (cx, base - 20, 'd' if pulse else 'b')
    elif kind == 'mystery':
        cy = base - 11 - (1 if pulse == 2 else 0)
        petal(cv, cx, base - 2, 0, -7, 7, 2.4, ('B', 'B', 's', 's'))
        rings(cv, cx, cy, [(3, -90, 10, 3.5, 12, 8, ('j', 'y', 'i', 'h'), 1.0, 0.7), (2, 30, 6, -2, 9, 7, ('y', 'i', 'h', 'h'), 1.0, 0.7)], frame)
        petal(cv, cx, cy + 3, sway * 0.8, 5, 7, 6, ('t', 'r', 'q', 's'), pointed=0.8, base_w=0.2)
        for x, y in ((cx, cy - 2), (cx + 1, cy - 2), (cx + 1, cy - 1), (cx, cy), (cx - 1, cy), (cx, cy + 2)):
            cv.put(x + (1 if frame == 1 else -1 if frame == 3 else 0), y, 't')
        glow = (cx, cy - 8, 'j' if pulse else 'y')
    elif kind == 'boss':
        cy = base - 3
        for a, L in ((-78, 17), (78, 17), (-58, 22), (58, 22), (-38, 26), (38, 26), (-19, 29), (19, 29), (0, 31)):
            r = math.radians(a)
            petal(cv, cx, cy, math.sin(r) * L * 0.8 + sway * 0.6, -math.cos(r) * L, L, 10, ('d', 'a', 'E', 'G'), pointed=1.0, vein=True)
        for a, L in ((-44, 14), (44, 14), (-18, 19), (18, 19), (0, 22)):
            r = math.radians(a)
            petal(cv, cx, cy, math.sin(r) * L * 0.7 + sway * 0.4, -math.cos(r) * L, L, 8, ('t', 'd', 'b', 'a'), pointed=1.0)
        ball(cv, cx, cy - 4, 5, 3.4, ('t', 't', 'd', 'b'))
        for i, (ex, ey) in enumerate(((cx - 8, base - 28), (cx + 9, base - 25), (cx - 2, base - 33), (cx + 4, base - 30))):
            cv.put(ex, ey - (frame + i) % 4, 'd' if i % 2 else 't')
        glow = (cx, base - 18, 'a' if pulse else 'E')
    cv.outline()
    return cv, glow


STATES = {'idle': dict(frames=4, fps=4, loop=True), 'hover': dict(frames=4, fps=8, loop=True), 'click': dict(frames=6, fps=12, loop=False), 'used': dict(frames=1, fps=0, loop=False)}
LUMA = lambda rgb: 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]


def dull(ch):
    """The used state's colours: petals fade to ash and stone, leaves go a step darker."""
    if ch in '.O':
        return ch
    if ch in 'zABsD':
        return {'z': 'A', 'A': 'B', 'B': 's', 's': 'D', 'D': 'D'}[ch]
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}[ch]
    L = LUMA(rgb)
    return 'C' if L > 190 else 'p' if L > 125 else 'l' if L > 85 else 'k' if L > 55 else 'x'


def ring(cv, cx, cy, rx, ry, role, keep=1, phase=0):
    """A dotted ellipse of light on empty pixels (keep: one pixel in this many is drawn)."""
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if abs(d - 1.0) * ry < 0.62 and (x + y + phase) % keep == 0 and cv.get(x, y) == '.':
                cv.put(x, y, role)


def flower(kind, frame=0, state='idle'):
    """One node flower in one state: (w, h, anchor, rows). 48 x 48 anchored at (24, 34); the summit is 64 x 64 anchored at (32, 50).
    idle sways slightly (4 frames, loops); hover lifts and blazes (4, loops); click squashes, springs up and bursts a ring of light (6, plays once); used is faded to ash and still (1)."""
    boss = kind == 'boss'
    size = 64 if boss else 48
    cx, base = size // 2, (50 if boss else 34)
    sway = (0, 1, 0, -1)[frame % 4]
    pulse = (0, 1, 2, 1)[frame % 4]
    if state == 'hover':
        sway, pulse = (0, 2, 0, -2)[frame], (1, 2, 1, 2)[frame]
    elif state in ('click', 'used'):
        sway, pulse = 0, (1 if state == 'click' else 0)
    dy = {'idle': (0, 0, 0, 0), 'hover': (-1, -2, -2, -1), 'click': (1, -1, -4, -3, -1, 0), 'used': (2,)}[state][frame]
    body, glow = flower_body(kind, frame, size, cx, base, sway, pulse)
    if state == 'used':
        body.g = [[dull(ch) for ch in row] for row in body.g]
    out = Canvas(size, size)
    rx, ry = (23 if boss else 15.3), (8.5 if boss else 6.4)
    pad(out, cx, base, rx, ry, 'k' if state == 'used' else ACCENT[kind])
    out.outline()
    accent = ACCENT[kind]
    if state == 'hover':
        for k in range(8):                                      # motes of light circling the clearing
            a = 2 * math.pi * (k / 8 + frame / 16)
            out.put(int(cx + math.cos(a) * (rx + 2)), int(base + math.sin(a) * (ry + 2)), 't' if k % 2 else accent)
    elif state == 'click':
        grow = (0.0, 0.0, 0.12, 0.24, 0.34, 0.42)[frame] * (0.7 if boss else 1.0)
        if frame >= 2:
            ring(out, cx, base, rx * (1 + grow), ry * (1 + grow), accent, keep=(1, 1, 2, 3)[frame - 2], phase=frame)
        reach = (0, 0, 5, 10, 14, 17)[frame] * (1.5 if boss else 1.0)
        if frame >= 2:
            for k in range(10):                                 # sparks flung out from the bloom
                a = 2 * math.pi * k / 10 + 0.3
                out.put(int(cx + math.cos(a) * reach), int(base - 11 + math.sin(a) * reach * 0.7), 't' if k % 2 else accent)
    for y in range(size):
        for x in range(size):
            if body.g[y][x] != '.':
                ox, oy = x, y + dy
                if 0 <= oy < size:
                    out.g[oy][ox] = body.g[y][x]
    if glow and state != 'used':
        gx, gy, role = glow
        gy += dy
        wide = (11 if boss else 8) + (3 if state in ('hover', 'click') else 0)
        out.sparks(((gx - wide + frame, gy - 2), (gx + wide - frame, gy), (gx - wide + 3, gy + 4 - frame), (gx + wide - 2, gy - 5 + frame), (gx + (frame - 1) * 3, gy - 7 - frame)), role)
    return size, size, (cx, base), out.rows()


FLOWER_KINDS = [('battle', 'Battle - a leaf bud'), ('event', 'Event - a blue flame flower'), ('elite', 'Elite - an eye flower'), ('shop', 'Shop - a marigold with a coin'),
                ('rest', 'Rest - a lotus with an ember'), ('treasure', 'Treasure - a gem bulb'), ('mystery', 'Mystery - an orchid'), ('boss', 'Summit - the fire lotus')]


# --- the floor generator ----------------------------------------------------------------------------
PRESETS = {
    'climb': dict(lanes=5, floors=8, paths=4, dx=9, dy=9, jitter=2, wander=1.3, node_r=(2.8, 3.1, 3.4), boss_r=5.6),
    'tall': dict(lanes=4, floors=11, paths=3, dx=10, dy=8, jitter=2, wander=1.6, node_r=(2.7, 3.0, 3.3), boss_r=5.8),
    'wide': dict(lanes=7, floors=6, paths=5, dx=8, dy=10, jitter=2, wander=1.0, node_r=(2.6, 2.9, 3.2), boss_r=6.0),
    'tangle': dict(lanes=6, floors=8, paths=6, dx=8, dy=8, jitter=3, wander=2.0, node_r=(2.5, 3.0, 3.5), boss_r=5.6),
}
MARGIN = 9


def make_paths(lanes, floors, paths, rng):
    """Paths climb from the bottom floor to the top one, a lane left, straight or right a floor, and never cross. Returns (nodes, edges) as (floor, lane) pairs."""
    nodes, edges = set(), set()
    starts = rng.sample(range(lanes), min(paths, lanes))
    for lane in starts:
        at = lane
        for floor in range(floors - 1):
            options = [l for l in (at - 1, at, at + 1) if 0 <= l < lanes]
            rng.shuffle(options)
            options = [l for l in options if l == at or ((floor, l), (floor + 1, at)) not in edges]
            nxt = options[0] if options else at
            edges.add(((floor, at), (floor + 1, nxt)))
            nodes.update({(floor, at), (floor + 1, nxt)})
            at = nxt
    top = floors - 1
    boss = (top, lanes // 2)
    for a, b in list(edges):
        if b[0] == top:
            edges.discard((a, b))
            edges.add((a, boss))
    return {n for n in nodes if n[0] < top} | {boss}, edges


def assign_types(nodes, edges, floors, rng):
    """Deal out the kinds: battles at the bottom, a treasure in the middle, a rest before the boss, elites and shops later; no two of a kind in a row."""
    kinds = {}
    parents = {}
    for a, b in edges:
        parents.setdefault(b, []).append(a)
    special = ('elite', 'shop', 'rest')
    for node in sorted(nodes, key=lambda n: (n[0], n[1])):
        floor = node[0]
        if floor == floors - 1:
            kinds[node] = 'boss'
        elif floor == floors - 2:
            kinds[node] = 'rest'
        elif floor == 0:
            kinds[node] = 'battle'
        elif floor == floors // 2:
            kinds[node] = 'treasure'
        else:
            bag = ['battle'] * 44 + ['event'] * 24 + ['mystery'] * 8
            if floor >= 2:
                bag += ['elite'] * 11 + ['shop'] * 6 + ['rest'] * 7
            mine = [k for k in bag if not any(kinds.get(p) == k and k in special + ('event',) for p in parents.get(node, []))]
            kinds[node] = rng.choice(mine or bag)
    return kinds


def blob(land, cx, cy, r, rng, wobble=0.22):
    p1, p2 = rng.random() * 6.28, rng.random() * 6.28
    h, w = len(land), len(land[0])
    for y in range(max(0, int(cy - r * 1.5 - 2)), min(h, int(cy + r * 1.5 + 3))):
        for x in range(max(0, int(cx - r * 1.5 - 2)), min(w, int(cx + r * 1.5 + 3))):
            dx, dy = x - cx, y - cy
            th = math.atan2(dy, dx)
            re = r * (1 + wobble * math.sin(3 * th + p1) + wobble * 0.6 * math.sin(5 * th + p2))
            if dx * dx + dy * dy <= re * re:
                land[y][x] = True


def generate(seed=7, preset='climb', **over):
    """A floor: dict with the node kinds and places, the edges, the land cells and the size. Same seed, same floor."""
    p = dict(PRESETS[preset])
    p.update(over)
    rng = random.Random(seed)
    nodes, edges = make_paths(p['lanes'], p['floors'], p['paths'], rng)
    kinds = assign_types(nodes, edges, p['floors'], rng)
    width = (p['lanes'] - 1) * p['dx'] + 2 * MARGIN
    height = (p['floors'] - 1) * p['dy'] + 2 * MARGIN
    land = [[False] * width for _ in range(height)]
    centre = {}
    for (floor, lane) in sorted(nodes):
        jx, jy = rng.randint(-p['jitter'], p['jitter']), rng.randint(-p['jitter'], p['jitter'])
        if floor == p['floors'] - 1:
            jx, jy = 0, 0
        centre[(floor, lane)] = (MARGIN + lane * p['dx'] + jx, MARGIN + (p['floors'] - 1 - floor) * p['dy'] + jy)
    for a, b in sorted(edges):
        (x0, y0), (x1, y1) = centre[a], centre[b]
        amp = rng.uniform(0.4, 1.0) * p['wander'] * rng.choice((-1, 1))
        ph = rng.random() * 3
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / ln, (x1 - x0) / ln
        steps = int(ln * 3) + 1
        for i in range(steps + 1):
            t = i / steps
            off = amp * math.sin(math.pi * t) * math.cos(ph + 2.2 * math.pi * t)
            r = 0.95 + 0.3 * math.sin(t * 9 + ph)
            blob_pt = (x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off)
            for yy in range(int(blob_pt[1] - r - 1), int(blob_pt[1] + r + 2)):
                for xx in range(int(blob_pt[0] - r - 1), int(blob_pt[0] + r + 2)):
                    if 0 <= xx < width and 0 <= yy < height and (xx - blob_pt[0]) ** 2 + (yy - blob_pt[1]) ** 2 <= r * r:
                        land[yy][xx] = True
    for node, (cx, cy) in sorted(centre.items()):
        boss = kinds[node] == 'boss'
        blob(land, cx, cy, p['boss_r'] if boss else rng.choice(p['node_r']), rng, 0.16 if boss else 0.22)
    # floating islets and lumps of earth scattered in the void, not touching the main land
    near = lambda x, y, d: any(land[yy][xx] for yy in range(max(0, y - d), min(height, y + d + 1)) for xx in range(max(0, x - d), min(width, x + d + 1)))
    for _ in range(int(width * height / 160)):
        x, y = rng.randint(3, width - 4), rng.randint(3, height - 4)
        if not near(x, y, 4):
            blob(land, x, y, rng.choice((1.1, 1.5, 1.9, 2.4)), rng, 0.3)
    return dict(seed=seed, preset=preset, params=p, kinds=kinds, centre=centre, edges=sorted(edges), land=land, width=width, height=height)


# --- drawing a floor (a reference composer, and the preview) -----------------------------------------------
def rgb_of():
    return {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}


def draw_rows(img, rgb, rows, ox, oy):
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch != '.' and 0 <= ox + x < img.width and 0 <= oy + y < img.height:
                img.putpixel((ox + x, oy + y), rgb[ch] + (255,))


def cell_at(land, x, y):
    return 0 <= y < len(land) and 0 <= x < len(land[0]) and land[y][x]


VOID = 256


def void_tile(seed=1, size=VOID):
    """The void behind the islands: a seamless dark purple with a faint haze and a few stars, 256 x 256, repeated across the whole map."""
    cv = Canvas(size, size)
    for y in range(size):
        for x in range(size):
            n = pnoise(x / 64.0, y / 64.0, size // 64, seed) * 0.62 + pnoise(x / 32.0, y / 32.0, size // 32, seed + 2) * 0.38
            cv.put(x, y, 'w' if n > 0.64 and (x + y) % 2 == 0 else 'x')
            hh = hashed(x, y, 99)
            if hh % 211 == 0:
                cv.put(x, y, 'v' if hh % 3 else 'o')
            elif hh % 977 == 1:
                cv.put(x, y, 't')
    return cv.rows()


def full_variant(h):
    return h % PLAIN if h % 100 < 70 else PLAIN + (h // 100) % (len(FULL_VARIANTS) - PLAIN)


def build_plan(layout):
    """Everything a game needs to draw a floor from the sheets: for every tile corner its shape (bits), cliff style, full-tile variant and tone; the loose pieces to lay over the ground
    (moss patches, decor, hanging vines and moss) as ids with the pixel the sprite's anchor goes on; the nodes and the routes between them. Same layout, same plan."""
    land, W, H, seed = layout['land'], layout['width'], layout['height'], layout['seed']
    bits, style, full = [], [], []
    for j in range(H + 1):
        brow, srow, frow = '', '', ''
        for i in range(W + 1):
            b = TL * cell_at(land, i - 1, j - 1) + TR * cell_at(land, i, j - 1) + BL * cell_at(land, i - 1, j) + BR * cell_at(land, i, j)
            h = hashed(i, j, seed)
            brow += '0123456789abcdef'[b]
            srow += str(h % STYLES)
            frow += str(full_variant(h) if b == 15 else 0)
        bits.append(brow), style.append(srow), full.append(frow)
    centre = layout['centre']
    rng = random.Random(seed * 7 + 3)
    near_node = lambda x, y, r: any((x - cx) ** 2 + (y - cy) ** 2 < r * r for cx, cy in centre.values())
    route_cells = set()
    for a, b in layout['edges']:
        for (x, y) in route_points(layout, a, b):
            route_cells.add((x // TILE, y // TILE))
    interior = [(x, y) for y in range(1, H - 1) for x in range(1, W - 1) if all(cell_at(land, x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    rng.shuffle(interior)
    spec = {sp[0]: sp for sp in decor_assets_spec()}
    placements = []
    tp_taken = set()
    for (x, y) in interior:
        n = vnoise(x / 3.2, y / 2.8, seed)
        if (n < 0.44 or n > 0.60) and rng.random() < 0.7 and not any((x + dx, y + dy) in tp_taken for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            variant = (4 if n < 0.44 else 0) + rng.randrange(4)
            placements.append(dict(layer='tone', id='tone-patch', frame=variant, x=x * TILE + 8 + rng.randint(-4, 4), y=y * TILE + 8 + rng.randint(-4, 4)))
            tp_taken.add((x, y))
    for (x, y) in interior:
        if rng.random() < 0.4:
            n = len(spec['moss-patch'][5])
            placements.append(dict(layer='patch', id='moss-patch', frame=rng.randrange(n), x=x * TILE + 8 + rng.randint(-5, 5), y=y * TILE + 8 + rng.randint(-5, 5)))
    taken = set()
    for (x, y) in interior:
        if (x, y) in route_cells or near_node(x, y, 3.4) or any((x + dx, y + dy) in taken for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        if rng.random() > 0.55:
            continue
        kind = rng.choice(['mushroom-purple', 'mushroom-blue', 'mushroom-red', 'crystal-violet', 'crystal-cyan', 'rock', 'fern', 'bush', 'tendril', 'tendril', 'wisp'])
        frames = spec[kind][5]
        frame = 0 if kind == 'wisp' else rng.randrange(len(frames))
        px, py = x * TILE + 8 + rng.randint(-3, 3), y * TILE + 8 + rng.randint(-2, 2)
        if kind == 'tendril':
            px, py = x * TILE + 8, y * TILE + 8
        placements.append(dict(layer='decor', id=kind, frame=frame, x=px, y=py))
        taken.add((x, y))
    for y in range(H):
        for x in range(W):
            if cell_at(land, x, y) and not cell_at(land, x, y + 1):
                px = x * TILE + rng.randint(0, 2)
                while px < x * TILE + TILE - 1:
                    if rng.random() < 0.18 + 0.5 * vnoise(px / 40.0, y * 0.7, 3):
                        if rng.random() < 0.38:
                            placements.append(dict(layer='hang', id='vine-hang', frame=rng.randrange(6), x=px, y=(y + 1) * TILE - 1))
                        else:
                            placements.append(dict(layer='hang', id='moss-drape', frame=rng.randrange(4), x=px, y=(y + 1) * TILE - 2))
                    px += rng.randint(3, 8)
    nodes = [dict(floor=f, lane=l, kind=layout['kinds'][(f, l)], x=cx, y=cy, px=int((cx + 0.5) * TILE), py=int((cy + 0.5) * TILE) + 4)
             for (f, l), (cx, cy) in sorted(centre.items())]
    routes = []
    for a, b in layout['edges']:
        pts = route_points(layout, a, b)
        routes.append(dict(a=list(a), b=list(b), x0=pts[0][0], y0=pts[0][1], x1=pts[-1][0], y1=pts[-1][1], n=len(pts) - 1))
    return dict(bits=bits, style=style, full=full, placements=placements, nodes=nodes, routes=routes)


def draw_tiles(img, rgb, plan, layer):
    """The ground ('ground') or its cliff spill ('spill') from a plan, the way the README says: one tile on every corner."""
    sprites = ground_sprites()
    for j, brow in enumerate(plan['bits']):
        for i, ch in enumerate(brow):
            b = int(ch, 16)
            st = int(plan['style'][j][i])
            if layer == 'spill' and 0 < b < 15:
                draw_rows(img, rgb, sprites['spill'][(st, b)], i * TILE - TILE // 2, (j + 1) * TILE - TILE // 2)
            elif layer == 'ground' and b:
                rows = sprites['full'][int(plan['full'][j][i])] if b == 15 else sprites['ground'][(st, b)]
                draw_rows(img, rgb, rows, i * TILE - TILE // 2, j * TILE - TILE // 2)


_GROUND = {}


def ground_sprites():
    """Every ground tile, built once: ground[(style, bits)], full[variant], spill[(style, bits)]."""
    if not _GROUND:
        _GROUND.update(ground={}, full={}, spill={})
        for st in range(STYLES):
            for b in range(1, 15):
                _GROUND['ground'][(st, b)] = ground_tile(b, 0, st)
                _GROUND['spill'][(st, b)] = spill_tile(b, st)
        for v in range(len(FULL_VARIANTS)):
            _GROUND['full'][v] = ground_tile(15, v)
    return _GROUND


def render(layout, frame=0, with_flowers=True, progress=None, layers=('void', 'spill', 'ground', 'pieces', 'routes', 'nodes'), plan=None, hover=None):
    """A floor drawn the way a game should draw it from the plan: void, spill, ground, loose pieces, routes, flowers. `progress` is {'visited': [...], 'current': node};
    `hover` is a node drawn in its hover state."""
    from PIL import Image
    rgb = rgb_of()
    plan = plan or build_plan(layout)
    W, H = layout['width'], layout['height']
    img = Image.new('RGBA', (W * TILE, H * TILE), (0, 0, 0, 255))
    if 'void' in layers:
        vt = void_tile()
        for y in range(0, img.height, VOID):
            for x in range(0, img.width, VOID):
                draw_rows(img, rgb, vt, x, y)
    if 'spill' in layers:
        draw_tiles(img, rgb, plan, 'spill')
    if 'ground' in layers:
        draw_tiles(img, rgb, plan, 'ground')
    if 'pieces' in layers:
        spec = {sp[0]: sp for sp in decor_assets_spec()}
        for pc in plan['placements']:
            sp = spec[pc['id']]
            f = pc['frame'] if pc['id'] != 'wisp' else frame % 4
            draw_rows(img, rgb, sp[5][f], pc['x'] - sp[4][0], pc['y'] - sp[4][1])
    visited = set(map(tuple, progress['visited'])) if progress else set()
    current = tuple(progress['current']) if progress else None
    if 'routes' in layers:
        order = ('off', 'default', 'used')
        states = []
        for r in plan['routes']:
            a, b = tuple(r['a']), tuple(r['b'])
            st = 'used' if progress and a in visited and b in visited else 'default' if (not progress or a == current) else 'off'
            states.append((order.index(st), r, st))
        for _, r, st in sorted(states, key=lambda t: t[0]):
            pts = [(int(r['x0'] + (r['x1'] - r['x0']) * i / r['n']), int(r['y0'] + (r['y1'] - r['y0']) * i / r['n'])) for i in range(r['n'] + 1)]
            for x, y, role in path_pixels(pts, st, frame % PATH_STATES[st]['frames']):
                if 0 <= x < img.width and 0 <= y < img.height:
                    img.putpixel((x, y), rgb[role] + (255,))
    if 'nodes' in layers and with_flowers:
        for nd in sorted(plan['nodes'], key=lambda n: n['py']):
            key = (nd['floor'], nd['lane'])
            st = 'used' if key in visited else 'hover' if hover == key else 'idle'
            w, h, (ax, ay), rows = flower(nd['kind'], frame % STATES[st]['frames'], st)
            draw_rows(img, rgb, rows, nd['px'] - ax, nd['py'] - ay)
    return img


PATH_STATES = {'default': dict(frames=4, fps=6), 'off': dict(frames=1, fps=0), 'used': dict(frames=4, fps=4)}
PATH_SPACING = {'default': 8, 'off': 9, 'used': 1}


def path_shape(state, x, y, k, frame):
    """The pixels one point of a route lays down, before the outline: {(x, y): role}. k is the point's number along the route."""
    shape = {}
    if state == 'default':
        if k % 8 == 0:
            pos = (k // 8 + frame) % 4
            core, ring = ('t', 'd') if pos == 0 else ('d', 'b') if pos in (1, 3) else ('b', 'a')
            for dx in range(3):
                for dy in range(3):
                    shape[(x + dx - 1, y + dy - 1)] = core if (dx, dy) == (1, 1) else 'a' if dx == 2 and dy == 2 else ring
    elif state == 'off':
        if k % 9 == 0:
            shape.update({(x, y): 'l', (x + 1, y): 'k', (x, y + 1): 'k', (x + 1, y + 1): 'k'})
    else:
        shape[(x, y)] = 'r' if k % 5 else 'o'
        shape.setdefault((x + 1, y), 'q')
        shape.setdefault((x, y + 1), 'q')
        if (k - frame * 5) % 20 == 0:
            shape.update({(x, y): 't', (x + 1, y): 'r', (x, y - 1): 'o', (x - 1, y): 'o', (x, y + 2): 'r', (x + 1, y + 1): 'r'})
    return shape


def outlined(shape):
    """A shape with a one pixel dark outline round it, as a list of (x, y, role), outline first."""
    ring = {(x + dx, y + dy) for (x, y) in shape for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(shape)
    return [(x, y, 'x') for (x, y) in sorted(ring)] + [(x, y, role) for (x, y), role in shape.items()]


def path_pixels(points, state, frame=0):
    """The pixels of a route that goes through `points` (one per pixel along it, from one node to the next), as (x, y, role), every state with a dark outline so it reads on the moss.
    default: the way you can go, 3 x 3 amber dots every 8 pixels with a bright pulse that runs along them (4 frames);
    off: the way you cannot, a few small dark unlit dots every 9 pixels (1 frame); used: the way you came, a solid minty trail with a sparkle sliding along it (4 frames)."""
    shape = {}
    for k, (x, y) in enumerate(points):
        shape.update(path_shape(state, x, y, k, frame))
    return outlined(shape)


def route_points(layout, a, b):
    """Pixels along an edge, following the bridge's wobble."""
    centre = layout['centre']
    (x0, y0), (x1, y1) = centre[a], centre[b]
    x0, y0, x1, y1 = (x0 + 0.5) * TILE, (y0 + 0.5) * TILE, (x1 + 0.5) * TILE, (y1 + 0.5) * TILE
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    return [(int(x0 + (x1 - x0) * i / n), int(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


# --- the assets: category "Overgrowth map", ids overgrowth-*, folder sprites/assets/overgrowth/ ------------------------------------------
CATEGORY = 'Overgrowth map'
FOLDER = 'overgrowth'
EXAMPLES = (('climb', 7), ('tall', 21), ('wide', 5), ('tangle', 4))
FORMAT = 1
SPILL_NOTE = 'drawn one row below its ground tile, under the ground layer'
STATE_NOTES = {'idle': 'loops, a slight sway', 'hover': 'loops, lifted and blazing, motes of light circling the clearing',
               'click': 'plays once, then go back to idle (or used, if the node is done): squash, spring up, a ring of light and sparks bursts out',
               'used': 'one still frame, faded to ash: the node has been done'}
PATH_NOTES = {'default': 'the way you can go: 3 x 3 amber dots every 8 pixels along the route, a bright pulse runs along them (4 frames)',
              'off': 'the way you cannot go: a small dark unlit dot every 9 pixels (1 frame)',
              'used': 'the way you came: a solid mint trail, 2 pixels wide with a dark outline, a sparkle sliding along it (4 frames)'}


def blank(w, h):
    return ['.' * w] * h


def build_assets():
    """The Overgrowth map's assets: ground sheets, the cliff spill, the void, loose decor, the node flowers in four states, and the route pieces."""
    from assetkit import family
    out = []
    plain = family(CATEGORY, TILE, TILE, (TILE // 2, TILE // 2), place='none', folder=FOLDER)
    names = [f'style {st}, bits {b}' for st in range(STYLES) for b in range(16)]
    ground = [blank(TILE, TILE) if b == 0 else ground_tile(15, 0) if b == 15 else ground_tile(b, 0, st) for st in range(STYLES) for b in range(16)]
    out.append(plain('overgrowth-ground', 'Overgrowth map - ground tiles (row = cliff style 0-4, column = corner bits 0-15)', 'variants', ground, names=names, cols=16, rows=STYLES,
                     overgrowth={'role': 'ground', 'bits': {'TL': TL, 'TR': TR, 'BL': BL, 'BR': BR}, 'styles': STYLES}))
    out.append(plain('overgrowth-full', 'Overgrowth map - full ground tiles (bits 15) with something in the middle', 'variants', [ground_tile(15, v) for v in range(len(FULL_VARIANTS))],
                     names=FULL_VARIANTS, cols=len(FULL_VARIANTS), rows=1, overgrowth={'role': 'full'}))
    spill = [blank(TILE, TILE) if b in (0, 15) else spill_tile(b, st) for st in range(STYLES) for b in range(16)]
    out.append(plain('overgrowth-spill', 'Overgrowth map - cliff spill tiles (' + SPILL_NOTE + ')', 'variants', spill, names=names, cols=16, rows=STYLES,
                     overgrowth={'role': 'spill', 'note': SPILL_NOTE}))
    big = family(CATEGORY, VOID, VOID, (0, 0), place='none', folder=FOLDER)
    out.append(big('overgrowth-void', 'Overgrowth map - the void (256 x 256, seamless, repeated across the whole map)', 'still', [void_tile()], overgrowth={'role': 'void'}))
    for sid, label, w, h, anchor, frames in decor_assets_spec():
        fam = family(CATEGORY, w, h, anchor, place='none', folder=FOLDER)
        if sid == 'wisp':
            out.append(fam('overgrowth-' + sid, 'Overgrowth map - ' + label, 'animation', frames, fps=6, overgrowth={'role': 'decor', 'piece': sid}))
        else:
            out.append(fam('overgrowth-' + sid, 'Overgrowth map - ' + label, 'variants', frames, names=[f'{sid} {k + 1}' for k in range(len(frames))], overgrowth={'role': 'decor', 'piece': sid}))
    for kind, label in FLOWER_KINDS:
        for state, info in STATES.items():
            frames = [flower(kind, f, state) for f in range(info['frames'])]
            w, h, anchor, _ = frames[0]
            fam = family(CATEGORY, w, h, anchor, place='none', folder=FOLDER)
            rows = [fr[3] for fr in frames]
            note = {'node': kind, 'state': state, 'plays': 'once' if not info['loop'] and info['frames'] > 1 else 'loops' if info['frames'] > 1 else 'still', 'note': STATE_NOTES[state]}
            out.append(fam(f'overgrowth-node-{kind}-{state}', f'Overgrowth map - {label} - {state}', 'animation' if len(rows) > 1 else 'still', rows, fps=info['fps'], overgrowth={'role': 'node', **note}))
    dots = [outlined(path_shape('default', 2, 2, 0, f)) for f in range(4)]
    to_rows = lambda pix, w, h: [''.join(next((r for (x, y, r) in pix if x == xx and y == yy), '.') for xx in range(w)) for yy in range(h)]
    pf = family(CATEGORY, 5, 5, (2, 2), place='none', folder=FOLDER)
    out.append(pf('overgrowth-path-default', 'Overgrowth map - route, default: the way you can go (4 pulse phases)', 'animation', [to_rows(d, 5, 5) for d in dots], fps=6,
                  overgrowth={'role': 'path', 'state': 'default', 'note': PATH_NOTES['default']}))
    pf = family(CATEGORY, 4, 4, (1, 1), place='none', folder=FOLDER)
    out.append(pf('overgrowth-path-off', 'Overgrowth map - route, off: the way you cannot go', 'still', [to_rows(outlined(path_shape('off', 1, 1, 0, 0)), 4, 4)],
                  overgrowth={'role': 'path', 'state': 'off', 'note': PATH_NOTES['off']}))
    pf = family(CATEGORY, 7, 7, (3, 3), place='none', folder=FOLDER)
    used = [to_rows(outlined(path_shape('used', 3, 3, 1, 1)), 7, 7), to_rows(outlined(path_shape('used', 3, 3, 0, 1)), 7, 7), to_rows(outlined(path_shape('used', 3, 3, 0, 0)), 7, 7)]
    out.append(pf('overgrowth-path-used', 'Overgrowth map - route, used: a step of trail, a bright step, the sparkle', 'variants', used, names=['trail step', 'bright step (every 5th)', 'sparkle'],
                  overgrowth={'role': 'path', 'state': 'used', 'note': PATH_NOTES['used']}))
    return out


def layout_json(layout, plan=None):
    """A floor as the game reads it: the nodes, the routes, the land, and the plan for the sheets (see the folder's README)."""
    plan = plan or build_plan(layout)
    return {
        'format': FORMAT, 'seed': layout['seed'], 'preset': layout['preset'], 'tile': TILE,
        'cells': [layout['width'], layout['height']], 'size': [layout['width'] * TILE, layout['height'] * TILE],
        'land': [''.join('#' if c else '.' for c in row) for row in layout['land']],
        'nodes': plan['nodes'],
        'edges': [{'from': r['a'], 'to': r['b'], 'x0': r['x0'], 'y0': r['y0'], 'x1': r['x1'], 'y1': r['y1'], 'n': r['n']} for r in plan['routes']],
        'tiles': {'bits': plan['bits'], 'style': plan['style'], 'full': plan['full']},
        'pieces': plan['placements'],
    }


README = """# Overgrowth map

Tiles, pieces and flowers for a floor-choosing map, like Slay the Spire's, set in a purple void: floating mossy islands joined by vine bridges, and a **flower on every node**. It has no
water and no roads. It is the second look for the same job as the water-and-islands `nodemap-*` set, and does not replace it. Everything here shares the `overgrowth-` prefix, and on the Assets page it
is the **Overgrowth map** category. `tools/make_overgrowth.py` makes it, and is also the **floor generator**.

| File | What it is |
|---|---|
| `overgrowth-ground.png` | 16 x 5 tiles of 16 x 16: column = corner bits (0 is empty), row = cliff style 0-4 |
| `overgrowth-full.png` | 6 variants of the all-land tile (bits 15), with something in the middle |
| `overgrowth-spill.png` | The same grid: the rest of a cliff that ran past the bottom of its tile (drawn **under** the ground layer) |
| `overgrowth-void.png` | The void: 256 x 256, seamless, repeated across the whole map |
| `overgrowth-tone-patch.png`, `-moss-patch.png`, `-mushroom-*.png`, `-crystal-*.png`, `-rock.png`, `-fern.png`, `-bush.png`, `-tendril.png`, `-wisp.png`, `-vine-hang.png`, `-moss-drape.png` | Loose pieces to lay over the ground (each sheet's cell size and anchor are in `manifest.json` and `overgrowth.json`) |
| `overgrowth-node-KIND-STATE.png` | The 8 node flowers (battle, event, elite, shop, rest, treasure, mystery, boss) in 4 states: idle, hover, click, used |
| `overgrowth-path-default.png`, `-off.png`, `-used.png` | The route pieces in their three states |
| `overgrowth.json` | All the numbers below in one file, for the app to read |
| `example-PRESET.json`, `example-climb.png`, `example-tall.png` | Four finished floors (`climb`, `tall`, `wide`, `tangle`) as layout files, and two of them drawn |

## A floor is a layout file

`example-climb.json` is the whole recipe for one floor, and `make_overgrowth.py --layout out.json --seed N --preset NAME` makes another (same seed and preset, same floor). It has:

- `land`: one string per row of **cells** (16 x 16 pixels), `#` is land, `.` is void. `cells` is the width and height, `size` the pixels.
- `nodes`: `floor` and `lane`, the `kind`, the cell `x`, `y`, and `px`, `py`: the pixel the flower's **anchor** goes on.
- `edges`: from node to node (`[floor, lane]`), with the route's two ends in pixels (`x0, y0` to `x1, y1`) and `n`, the number of pixel steps along it.
- `tiles`: three grids of strings, one character per **corner** `(i, j)` with `0 <= i <= width` and `0 <= j <= height`: `bits` (a hex digit, 0-f), `style` (0-4) and `full` (the variant of the full tile).
- `pieces`: the loose pieces, in the order to draw them: `layer` (`tone`, `patch`, `decor`, `hang`), `id` (the sheet, without `overgrowth-`), `frame`, and `x`, `y`, the pixel the sprite's anchor goes on.

## Drawing it, from the bottom

1. **Void**: repeat `overgrowth-void.png` over the whole map.
2. **Spill**: for every corner tile with `bits` 1-14, draw the spill tile (column `bits`, row `style`) with its top left at `(i * 16 - 8, (j + 1) * 16 - 8)`: one row **down**.
3. **Ground**: for every corner tile with `bits` other than 0, draw the ground tile (column `bits`, row `style`) with its top left at `(i * 16 - 8, j * 16 - 8)`. When `bits` is 15, draw the variant `full` of `overgrowth-full.png` instead.
4. **Pieces**, in order: `tone`, `patch`, `decor`, `hang`. Put each sprite's anchor on `(x, y)`. The `wisp` is an animation (6 fps); the others are one frame, picked by `frame`.
5. **Routes**: along each edge, one point per pixel step: `(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)` for `k = 0..n` (floor each). Draw them in the state the node says, see below.
6. **Nodes**: the flower for the node's `kind` and state, with its anchor on `(px, py)`. Draw the nodes from the top of the map down.

Turn smoothing off and scale by whole numbers only. The dual grid (a tile for every corner between four cells, picked by which are land) is the same as the node map's: TL 1, TR 2, BL 4, BR 8.

## States

A node is one of **idle** (default; loops), **hover** (loops), **click** (plays once, then idle, or used), or **used**. The numbers are in `overgrowth.json`.

| State | Frames | fps | Notes |
|---|---|---|---|
| idle | 4 | 4 | loops, a slight sway |
| hover | 4 | 8 | loops, lifted and blazing, motes of light circling the clearing |
| click | 6 | 12 | **plays once**: squash, spring up, a ring of light and sparks bursts out |
| used | 1 | - | faded to ash: the node is done |

Each flower stands in a dark clearing ringed in its own colour, so it stands out from the moss. Cells are 48 x 48 with the anchor at (24, 34), except the **boss** (the summit), 64 x 64 at (32, 50).

A **route** has three states, and the app decides which applies. A way you have taken is **used**, the ways open from where you are are **default**, and the rest are **off**:

| State | What it looks like |
|---|---|
| default | 3 x 3 amber dots every 8 pixels, a bright pulse runs along them (4 frames, 6 fps; dot number `n` shows phase `(n + frame) % 4` of `overgrowth-path-default`) |
| off | a small dark unlit dot every 9 pixels (`overgrowth-path-off`) |
| used | a solid mint line, 2 pixels wide with a dark outline (`overgrowth-path-used`: a step, a bright step on every 5th pixel, and the sparkle on every 20th, moving 5 pixels a frame, 4 frames, 4 fps) |

## Ground, in short

- **Ground** is a dual grid: a 16 x 16 tile on every corner between four cells. Tile edges always agree, so any two tiles join.
- **Cliffs** hang under every south edge, in 5 styles. Every style ends the same at its left and right sides, so a tile joins any style next to it. A cliff that runs past the bottom of its tile continues in the **spill** tile.
- **Variety**: the `full` tiles differ only in their middle; the `tone` and `patch` pieces lay big soft patches of lighter and deeper moss and small patches over the open ground, and only where they fit inside an island, so they never hang over an edge.
"""


def write_package(folder, seed=7):
    """Beside the sheets: overgrowth.json (the numbers), a README for the app, four example layouts and two drawn floors."""
    import json
    from assetkit import write_json
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for preset, sd in EXAMPLES:
        lay = generate(sd, preset)
        (folder / f'example-{preset}.json').write_text(json.dumps(layout_json(lay)))
    for preset, sd in EXAMPLES[:2]:
        render(generate(sd, preset)).save(folder / f'example-{preset}.png')
    decor = {sid: dict(size=[w, h], anchor=list(a), frames=len(fr), fps=6 if sid == 'wisp' else 0) for sid, _, w, h, a, fr in decor_assets_spec()}
    nodes = {}
    for kind, label in FLOWER_KINDS:
        w, h, a, _ = flower(kind, 0, 'idle')
        nodes[kind] = dict(label=label, size=[w, h], anchor=list(a), accent=ACCENT[kind], states={s: dict(frames=i['frames'], fps=i['fps'], loops=i['loop'] and i['frames'] > 1, sheet=f'overgrowth-node-{kind}-{s}.png', note=STATE_NOTES[s]) for s, i in STATES.items()})
    write_json(folder, 'overgrowth.json', 'How an app uses the Overgrowth map sheets in this folder. See README.md beside this file for the whole story.', {
        'format': FORMAT, 'tile': TILE, 'bits': {'TL': TL, 'TR': TR, 'BL': BL, 'BR': BR},
        'tilePosition': 'the tile on the corner between cells (i-1, j-1), (i, j-1), (i-1, j) and (i, j) has its top left at (i * 16 - 8, j * 16 - 8); a spill tile is one row down: (i * 16 - 8, (j + 1) * 16 - 8)',
        'ground': {'sheet': 'overgrowth-ground.png', 'columns': 16, 'rows': STYLES, 'index': 'column = bits, row = style', 'styles': STYLES,
                   'full': {'sheet': 'overgrowth-full.png', 'variants': FULL_VARIANTS}, 'spill': {'sheet': 'overgrowth-spill.png', 'note': SPILL_NOTE}},
        'void': {'sheet': 'overgrowth-void.png', 'size': VOID},
        'decor': decor, 'nodes': nodes,
        'paths': {'states': {s: dict(frames=i['frames'], fps=i['fps'], spacing=PATH_SPACING[s], note=PATH_NOTES[s]) for s, i in PATH_STATES.items()},
                  'sheets': {'default': 'overgrowth-path-default.png', 'off': 'overgrowth-path-off.png', 'used': 'overgrowth-path-used.png'},
                  'points': 'one per pixel step from (x0, y0) to (x1, y1): floor(x0 + (x1 - x0) * k / n), k = 0..n'},
        'presets': {k: {a: b for a, b in v.items()} for k, v in PRESETS.items()},
        'drawOrder': ['void (repeated)', 'spill tiles (one row down)', 'ground tiles', 'pieces: tone, patch, decor, hang', 'routes', 'nodes, top of the map first'],
    })
    (folder / 'README.md').write_text(README)


# --- the preview ------------------------------------------------------------------------------------------
def sheet_of(items, cols, scale, bg=(47, 26, 69, 255), labels=None, cell=None):
    from PIL import Image, ImageDraw
    rgb = rgb_of()
    cw = max(len(r[0]) for r in items) if cell is None else cell[0]
    ch = len(items[0]) if cell is None else cell[1]
    rows = (len(items) + cols - 1) // cols
    img = Image.new('RGBA', (cols * (cw * scale + 6) + 6, rows * (ch * scale + 18) + 6), bg)
    d = ImageDraw.Draw(img)
    for n, tile in enumerate(items):
        t = Image.new('RGBA', (len(tile[0]), len(tile)), (0, 0, 0, 0))
        draw_rows(t, rgb, tile, 0, 0)
        ox, oy = 6 + (n % cols) * (cw * scale + 6), 6 + (n // cols) * (ch * scale + 18)
        img.alpha_composite(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (ox, oy + 12))
        if labels:
            d.text((ox, oy), labels[n], fill=(235, 232, 245, 255))
    return img


def demo_progress(layout, steps=3):
    """A walk up from the bottom floor, for showing the three route states and the used flowers together."""
    first = min((n for n in layout['centre'] if n[0] == 0), key=lambda n: n[1])
    visited, at = [first], first
    for _ in range(steps):
        nxt = sorted(b for a, b in layout['edges'] if a == at)
        if not nxt:
            break
        at = nxt[0]
        visited.append(at)
    return dict(visited=visited, current=at)


def preview(path, seeds=(7, 21, 4)):
    from PIL import Image
    stem = str(path).replace('.png', '')
    rgb = rgb_of()
    # the tiles over the void, with their spill tiles under, and the full variants
    items, labels = [], []
    for b in range(1, 16):
        items.append(ground_tile(b))
        labels.append(f'tile {b}')
    sheet = sheet_of(items, 8, 5, labels=labels)
    # to see a tile as it is used, composite on void; the sheet already has the void colour
    sheet.save(stem + '-tiles.png')
    var = sheet_of([ground_tile(15, v) for v in range(len(FULL_VARIANTS))], 5, 5, labels=FULL_VARIANTS)
    var.save(stem + '-full-variants.png')
    decor_items, decor_labels = [], []
    for sid, label, w, h, anchor, frames in decor_assets_spec():
        for k, fr in enumerate(frames):
            decor_items.append(fr)
            decor_labels.append(f'{sid} {k}')
    # decor on a moss ground
    moss = [''.join('B' if hashed(x, y) % 9 else 's' for x in range(40)) for y in range(40)]
    from PIL import ImageDraw
    d_sheet = sheet_of([ground_tile(15) for _ in decor_items], 1, 1, labels=None) if False else None
    dec = sheet_of(decor_items, 8, 4, bg=(18, 96, 62, 255), labels=decor_labels, cell=(32, 32))
    dec.save(stem + '-decor.png')
    fl_items, fl_labels = [], []
    for kind, label in FLOWER_KINDS:
        for state, info in STATES.items():
            for f in range(info['frames']):
                fl_items.append(flower(kind, f, state)[3])
                fl_labels.append(f'{kind} {state[:2]}{f}')
    sheet_of(fl_items, 15, 3, bg=(14, 62, 58, 255), labels=fl_labels, cell=(64, 64)).save(stem + '-flowers.png')
    for seed, preset in zip(seeds, ('climb', 'tall', 'tangle')):
        lay = generate(seed, preset)
        render(lay).save(f'{stem}-floor-{preset}-{seed}.png')
        render(lay, progress=demo_progress(lay, 4)).save(f'{stem}-floor-{preset}-{seed}-progress.png')
    # the three route states, on a straight, a diagonal and a wavy run, every frame
    from PIL import Image as _I
    rgb = rgb_of()
    runs = [[(4 + i, 8) for i in range(56)], [(4 + i, 4 + i // 2 * 1) for i in range(56)] and [(4 + i, 3 + int(i * 0.45)) for i in range(56)], [(4 + i, 8 + int(4 * math.sin(i / 7.0))) for i in range(56)]]
    cols = sum(info['frames'] for info in PATH_STATES.values())
    strip = _I.new('RGBA', (cols * 66 + 4, 3 * 34 + 4), rgb['B'] + (255,))
    ox = 2
    for st, info in PATH_STATES.items():
        for f in range(info['frames']):
            for r, run in enumerate(runs):
                for x, y, role in path_pixels(run, st, f):
                    if 0 <= x < 64 and 0 <= y < 32:
                        strip.putpixel((ox + x, 2 + r * 34 + y), rgb[role] + (255,))
            ox += 66
    strip.resize((strip.width * 3, strip.height * 3), _I.NEAREST).save(stem + '-paths.png')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--preset', default='climb', choices=sorted(PRESETS))
    parser.add_argument('--floor', type=Path, help='render one floor of this seed and preset')
    parser.add_argument('--layout', type=Path, help='write the layout file for this seed and preset')
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
        print('wrote the tile, decor and flower sheets and three floors beside', args.preview)
    if args.floor:
        render(generate(args.seed, args.preset)).save(args.floor)
        print('wrote', args.floor)
    if args.layout:
        import json
        args.layout.write_text(json.dumps(layout_json(generate(args.seed, args.preset))))
        print('wrote', args.layout)


if __name__ == '__main__':
    main()
