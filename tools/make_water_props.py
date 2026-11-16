#!/usr/bin/env python3
"""A set of things that live on and beside the water: a wooden dock, a moored rowboat, stepping stones, a small waterfall, lily pads, mushroom pads and shore reeds, with corrupted versions where the corruption would show.

Water sits one height step (8 pixels, half a level) below the ground in the game, so a prop here is drawn on the WATER'S SURFACE: z = 0 in the picture is the surface of a water tile, and the
anchor is the middle of the footprint on it. A thing that is walkable has its flat top half a level (8 pixels) above the surface, which is the height of the land beside it, so a unit steps straight on.
Everything is in the ground's projection (a cell is a 32 x 16 diamond; see tools/buildings.py and tools/prop3d.py), palette roles only, deterministic.

    dock-1x2, -2x1, -1x3, -3x1     a plank pier on piles, flush with the land: walkable along its length (1 x 2 runs down-left, 2 x 1 down-right); a rotted, mushroom-grown `-corrupted` of each
    rowboat-2x1, rowboat-1x2       a rowboat moored at a post: not walkable (its floor is half a level up); the deck is only dressing
    stepping-1x1 (3 variants), -2x1, -1x2, -1x3, -3x1     flat-topped stones standing in the water, one to a cell, flush with the land, so they read as a way across
    waterfall-ne, waterfall-se     a one-cell cliff that water pours over, 6 frames; `-corrupted` of each in the corrupted water's teal
    lily-pads (4 variants), mushroom-pads (4, corrupted)     flat decals on the water: 32 x 16, anchored at the middle
    reeds (3 variants), reeds-sway (4 frames), reeds-corrupted, reeds-corrupted-sway     tufts for the shore: 32 x 32, anchored where they stand

    python3 tools/make_water_props.py --preview previews/water-props.png       every piece at 2x on its footprint (water cells blue), the animations as strips, and the measured flat top of the walkable ones
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
import prop3d as p3  # noqa: E402
from prop3d import Scene, box, prism, noise, tint  # noqa: E402

FOLDER = 'water-props'
CATEGORY = 'Water props'
WALK_MIN = 0.6
DECK = 0.5                                   # the walkable height above the water's surface: the land's. Sunken water is one game step (8 pixels, half a level) under the land.
CLIFF = 1.0                                  # a waterfall's cliff: a full level
CORRUPT_WATER = {'o': 'q', 'n': 's', 'm': 'D', 'k': 'D', 'r': 'r', 't': 'r'}      # the water roles in the corrupted water's teal


# --- helpers ------------------------------------------------------------------------------------
def rect(fx, fy):
    return {(i, j) for i in range(fx) for j in range(fy)}


def watery(painter, hi=0.07, foam='r'):
    """A painter that puts foam where a solid meets the water (its lowest pixels) and wets the row above."""
    def inner(s, n, P):
        role = painter(s, n, P)
        z = P[2]
        if abs(n[2]) < 0.5 and z < hi + 0.06:
            if z < hi:
                return foam if noise(int(P[0] * 16 + P[1] * 16), int(z * 16), 9) > 0.3 else 't'
            return tint(role, 1)
        return role
    return inner


def little_mushroom(sc, x, y, cap=('y', 'j'), stem='t'):
    sc.pixel(x, y, stem)
    sc.pixel(x, y - 1, stem)
    for dx in (-1, 0, 1):
        sc.pixel(x + dx, y - 2, cap[0])
    sc.pixel(x - 1, y - 3, cap[0]) if False else None
    sc.pixel(x, y - 3, cap[1])
    sc.pixel(x - 1, y - 2, cap[1])


# --- the dock -----------------------------------------------------------------------------------
def dock_parts(fx, fy, corrupted, seed):
    """Deck planks 0.14 thick with their top at DECK, stringers under them, and piles at every cell boundary down both sides; a taller mooring post at the far end."""
    along_y = fy > fx
    L = fy if along_y else fx
    mat = 'crate' if corrupted else 'wood'
    worn = 0.85 if corrupted else 0.12
    lo, hi = 0.12, 0.88                                     # the deck's width across, in the cell
    parts = []

    def mk(u0, u1, v0, v1, z0, z1, grain='x', **a):
        x0, x1, y0, y1 = (v0, v1, u0, u1) if along_y else (u0, u1, v0, v1)
        return box(x0, x1, y0, y1, z0, z1, mat, seed + len(parts), grain='y' if (grain == 'x') == along_y else 'x', worn=worn, **a)
    parts.append(mk(0.0, L, lo, hi, DECK - 0.14, DECK))                                      # the deck: boards lie across the run
    parts.append(mk(0.06, L - 0.06, lo + 0.07, lo + 0.17, DECK - 0.3, DECK - 0.14))          # two stringers under it
    parts.append(mk(0.06, L - 0.06, hi - 0.17, hi - 0.07, DECK - 0.3, DECK - 0.14))
    rng = seed
    for k in range(L + 1):
        u = min(max(k, 0.1), L - 0.1) if k in (0, L) else k
        for side, v in ((0, lo + 0.03), (1, hi - 0.03)):
            tall = 1.0 + (0.22 if (side == 0 or k in (0, L)) else 0.06) + 0.04 * noise(k, side, rng)
            x, y = (v, u) if along_y else (u, v)
            parts.append(prism(x, y, 0.055, 6, 0.0, tall if side == 0 else DECK + 0.06, mat, seed + 10 * k + side, turn=0.3, worn=worn, grain='x'))
    # the mooring post at the far end of the run, taller, with a rope coiled round it
    u = 0.12
    x, y = ((hi - 0.1, u) if along_y else (u, hi - 0.1))
    parts.append(prism(x, y, 0.07, 6, 0.0, DECK + 0.5, mat, seed + 99, turn=0.3, worn=worn))
    coil = prism(x, y, 0.1, 6, DECK + 0.18, DECK + 0.3, 'hay', seed + 98, turn=0.3)
    parts.append(coil)
    return parts, along_y, L


def build_dock(fx, fy, corrupted=False):
    seed = 400 + 13 * fx + 7 * fy + (50 if corrupted else 0)
    parts, along_y, L = dock_parts(fx, fy, corrupted, seed)
    sc = Scene(fx, fy, DECK + 0.5, pad=2, up=8)
    sc.draw(parts, watery(p3.paint))
    for k in range(L + 1):                                       # a ripple round the foot of the piles on the near side
        u = min(max(k, 0.1), L - 0.1) if k in (0, L) else k
        v = 0.88 - 0.03
        x, y = (v, u) if along_y else (u, v)
        sc.ripple(x, y, 0.2, 'q' if corrupted else 'o')
    if corrupted:
        for k in range(L * 2):
            u = 0.25 + 0.5 * k + 0.25 * noise(k, 3, seed)
            v = 0.3 + 0.4 * noise(k, 4, seed)
            x, y = (v, u) if along_y else (u, v)
            px, py = sc.project(x, y, DECK)
            little_mushroom(sc, int(px), int(py))
    rows = sc.finish()
    cells = rect(fx, fy)
    cover = p3.top_cover(parts[:3], cells, DECK)
    return dict(rows=rows, anchor=sc.anchor, fx=fx, fy=fy, cells=cells, cover=cover, levels=DECK, style='wood')


# --- the rowboat --------------------------------------------------------------------------------
def build_rowboat(fx, fy):
    along_y = fy > fx
    seed = 700 + fx * 3 + fy
    cx, cy = fx / 2, fy / 2

    def to(u, v):                           # boat space (u along its length, v across) to the prop's x, y
        return (cy + v, cx + u) if False else ((cx + v, cy + u) if along_y else (cx + u, cy + v))

    def swap(planes):
        return [((n[1], n[0], n[2]), d) for n, d in planes] if along_y else planes
    H = 0.55
    half = 0.27
    planes = [((0, 0, 1), H), ((0, 0, -1), 0.0),
              p3.plane((0, 1, -0.4), (0, half - 0.05, 0)), p3.plane((0, -1, -0.4), (0, -half + 0.05, 0)),
              p3.plane((1, 1.05, -0.12), (0.72, 0, 0)), p3.plane((1, -1.05, -0.12), (0.72, 0, 0)),
              p3.plane((-1, 0.18, -0.1), (-0.88, 0, 0)), p3.plane((-1, -0.18, -0.1), (-0.88, 0, 0))]
    # shift to the cell: the planes were written about (0, 0), so add the centre to every offset
    def centred(pl):
        n, d = pl
        c = to(0, 0)
        return (n, d + n[0] * c[0] + n[1] * c[1])
    hull_planes = [centred(pl) for pl in swap(planes)]

    def top_deco(s, n, P, role):
        x, y, z = P
        u, v = ((y - cy), (x - cx)) if along_y else ((x - cx), (y - cy))
        if n[2] > 0.9:
            if abs(v) < half - 0.03 and -0.8 < u < 0.6:                              # inside the boat
                a, b = int(math.floor(u * 16)), int(math.floor(v * 16))
                if abs(u + 0.3) < 0.04 or abs(u - 0.22) < 0.04:
                    return 'a' if b % 2 == 0 else 'e'                                 # a thwart across
                if v < -half + 0.09:
                    return 'e'                                                        # the inner side of the far gunwale, seen from above
                return 'f' if a % 3 else 'g'                                          # floor boards
            return 'a' if noise(int(u * 16), int(v * 16), 5) > 0.2 else 'e'          # the gunwale
        if abs(n[2]) < 0.6 and 0.38 < z < 0.46:
            return 'c'                                                                # a painted stripe
        return None
    hull = p3.Part(hull_planes, 'wood', H, seed, grain='x', worn=0.15, deco=top_deco)
    # a post to moor it to, at the bow end, and a rope from the bow to it
    bx, by = to(0.95, 0.4)
    post = prism(min(bx, fx - 0.08), min(by, fy - 0.08), 0.06, 6, 0.0, 0.75, 'wood', seed + 1, turn=0.3)
    sc = Scene(fx, fy, 0.8, pad=2, up=6)
    sc.draw([hull, post], watery(p3.paint))
    hx, hy = to(0.0, 0.0)
    for k in range(-1, 2):
        sc.ripple(*to(0.45 * k, half + 0.08), 0.16, 'o')
    px, py = sc.project(post.centre[0], post.centre[1], 0.6)
    bow = sc.project(*to(0.8, 0.05), 0.46)
    for t in range(0, 11):                                                            # the rope
        sc.pixel(round(bow[0] + (px - bow[0]) * t / 10), round(bow[1] + (py - bow[1]) * t / 10 + 2 * math.sin(math.pi * t / 10)), 'C')
    rows = sc.finish()
    return dict(rows=rows, anchor=sc.anchor, fx=fx, fy=fy, cells=rect(fx, fy), cover={}, levels=H, style='wood')


# --- stepping stones ----------------------------------------------------------------------------
def build_stepping(cells, seed):
    import make_rocks as mr
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    blobs = []
    for k, (i, j) in enumerate(sorted(cells)):
        s = seed + 31 * k
        c = (i + 0.5 + 0.06 * (mr.rnd(s, 1) - 0.5), j + 0.5 + 0.06 * (mr.rnd(s, 2) - 0.5), 0.0)
        r = (0.5 + 0.08 * mr.rnd(s, 3), 0.5 + 0.08 * mr.rnd(s, 4), DECK * 2.6)
        pl = mr.facets(s, c, r, 6, 0.8, 0.94, (62, 85))
        b = mr.Blob(c, r, mr.rnd(s, 5) * math.pi, s, cut=DECK, top=DECK, planes=pl)
        b.mat = 'stone'
        blobs.append(b)
    sc = Scene(fx, fy, DECK, pad=3, up=4)
    sc.draw(blobs, watery(p3.paint, hi=0.08))
    for b in blobs:
        sc.ripple(b.c[0], b.c[1], 0.62, 'o', inner='r')
    rows = sc.finish()
    cover = p3.top_cover(blobs, cells, DECK)
    return dict(rows=rows, anchor=sc.anchor, fx=fx, fy=fy, cells=set(cells), cover=cover, levels=DECK, style='natural')


# --- the waterfall ------------------------------------------------------------------------------
def build_waterfall(face, frame, frames=6, corrupted=False):
    """A one-cell cliff block of stone, CLIFF high, with water pouring over its lip on `face` ('NE' is the right-hand wall, +x; 'SE' the left, +y) into the pool."""
    seed = 900 + (0 if face == 'NE' else 17)
    t = frame / frames
    lo, hi = 0.28, 0.72                                  # where the sheet is across the wall
    cliff = box(0, 1, 0, 1, 0, CLIFF, 'stone', seed)

    def cliff_deco(s, n, P, role):
        x, y, z = P
        if n[2] > 0.9:
            across, along = (y, x) if face == 'NE' else (x, y)
            if lo <= across < hi:                                                    # the channel the water runs down on the top
                a = int(along * 16)
                k = (a - frame * 2) % 6
                return 'o' if k < 1 else ('n' if k < 4 else 'm')
        return None
    cliff.deco = cliff_deco
    sx0, sx1 = (1.0, 1.07)
    if face == 'NE':
        sheet = box(sx0, sx1, lo, hi, 0.0, CLIFF + 0.02, 'water', seed + 1)
    else:
        sheet = box(lo, hi, sx0, sx1, 0.0, CLIFF + 0.02, 'water', seed + 1)

    def sheet_paint(s, n, P):
        x, y, z = P
        across = y if face == 'NE' else x
        a, b = int(across * 16), int(z * 16)
        if n[2] > 0.9:
            return 'o'
        lum = p3.lum_of(n)
        edge = a == int(lo * 16) or a == int(hi * 16) - 1
        streak = (b + frame * 3 + (a * 5) % 7) % 8
        role = 'n'
        if streak < 1:
            role = 'r'
        elif streak < 3:
            role = 'o'
        elif streak > 6:
            role = 'm'
        if edge:
            role = 'm' if lum < 0.3 else 'n'
        if z > CLIFF - 0.04:
            role = 't'                                                              # the lip
        return role
    sheet.deco = None

    def painter(s, n, P):
        if s is sheet:
            return sheet_paint(s, n, P)
        return p3.paint(s, n, P)
    sc = Scene(1, 1, CLIFF, pad=8, up=4)
    sc.draw([cliff, sheet], painter)
    # foam at the foot of the fall, and rings spreading on the pool
    fx0, fy0 = (1.14, 0.5) if face == 'NE' else (0.5, 1.14)
    cx, cy = sc.project(fx0, fy0)
    for k in range(9):
        a = 2 * math.pi * k / 9 + t * 2
        r = 4 + 3 * math.sin(2 * math.pi * (t + k / 9))
        sc.pixel(round(cx + r * 1.6 * math.cos(a)), round(cy + r * 0.8 * math.sin(a)), 't' if k % 2 else 'r', under=False)
    for k in range(3):
        rr = ((t + k / 3) % 1.0)
        sc.ellipse(cx, cy, 3 + 12 * rr, 1.5 + 6 * rr, 'o' if rr < 0.6 else 'n', skip=lambda a, rr=rr: rr > 0.75 and 0.2 < a < 2.9)
    rows = sc.finish()
    if corrupted:
        rows = [''.join(CORRUPT_WATER.get(c, c) for c in r) for r in rows]
    return dict(rows=rows, anchor=sc.anchor, fx=1, fy=1, cells={(0, 0)}, cover={}, levels=CLIFF, style='block')


# --- pads (flat decals) -------------------------------------------------------------------------
CELL_DECAL = (32, 16)
ANCHOR_DECAL = (16, 8)


def decal():
    return [['.'] * 32 for _ in range(16)]


def put(g, x, y, role):
    if 0 <= x < 32 and 0 <= y < 16:
        g[y][x] = role


def lily(g, cx, cy, rx, ry, notch, seed):
    """A lily pad: a flat ellipse of green with a wedge cut out, lit along its upper left, with veins and a dark rim."""
    for y in range(16):
        for x in range(32):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = math.hypot(dx, dy)
            if d > 1:
                continue
            ang = math.atan2(dy, dx)
            if abs((ang - notch + math.pi) % (2 * math.pi) - math.pi) < 0.22 and d > 0.15:
                continue
            role = 'z' if (dx + dy) < -0.35 else ('A' if (dx + dy) < 0.5 else 'B')
            if d > 0.78:
                role = 'B' if dy > -0.2 else 'A'
            if abs(math.sin((ang - notch) * 3)) < 0.1 and 0.2 < d < 0.85 and role != 'z':
                role = 'z'
            g[y][x] = role


def lotus(g, cx, cy):
    for dx, dy, r in ((-2, 0, 'c'), (2, 0, 'c'), (0, -1, 't'), (-1, -1, 'e'), (1, -1, 'e'), (0, 0, 'd')):
        put(g, cx + dx, cy + dy, r)
    put(g, cx, cy - 2, 'c')


def build_lily(variant, corrupted=False):
    g = decal()
    if not corrupted:
        spec = {0: [(15.5, 8, 6.2, 3.0, 0.6)], 1: [(11, 7, 5.2, 2.6, 2.4), (21, 9.5, 5.5, 2.7, 0.2)],
                2: [(16, 8, 6.5, 3.2, 3.6), (8, 6, 3.5, 1.8, 1.0), (24.5, 10.5, 3.5, 1.8, 5.0)], 3: [(10, 9, 4.4, 2.2, 2.0), (17, 6.5, 4.0, 2.0, 5.5), (23, 10, 4.2, 2.1, 0.3), (14, 11.5, 3.0, 1.5, 4.0)]}[variant]
        for k, (cx, cy, rx, ry, notch) in enumerate(spec):
            lily(g, cx, cy, rx, ry, notch, k)
        if variant in (0, 2):
            lotus(g, 16 if variant == 2 else 13, 7 if variant == 2 else 5)
        # a ripple of the water round it, only in empty pixels
        for x in range(32):
            for y in range(16):
                if g[y][x] == '.' and ((x - 15.5) / 15) ** 2 + ((y - 7.5) / 7.5) ** 2 > 0.82 and ((x - 15.5) / 15) ** 2 + ((y - 7.5) / 7.5) ** 2 < 0.9 and noise(x, y, 4) > 0.55:
                    g[y][x] = 'o'
    else:
        caps = {0: [(15.5, 8, 6.2, 3.0)], 1: [(11, 7, 5.0, 2.5), (21, 9.5, 5.0, 2.5)],
                2: [(16, 8, 6.5, 3.2), (8, 6, 3.2, 1.6), (24.5, 10.5, 3.4, 1.7)], 3: [(10, 9, 4.2, 2.1), (17, 6.5, 4.0, 2.0), (23, 10, 4.2, 2.1), (14, 11.5, 2.8, 1.4)]}[variant]
        for k, (cx, cy, rx, ry) in enumerate(caps):
            for y in range(16):
                for x in range(32):
                    dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                    d = math.hypot(dx, dy)
                    if d > 1:
                        continue
                    role = 'j' if (dx + dy) < -0.4 else ('y' if (dx + dy) < 0.4 else 'h')
                    if d > 0.8:
                        role = 'u' if dy > -0.3 else 'h'
                    g[y][x] = role
            for sx, sy in ((-0.4, -0.2), (0.3, 0.1), (0.0, 0.45)):
                if noise(k, int(sx * 10), 31) > 0.3:
                    put(g, round(cx + sx * rx), round(cy + sy * ry), 't')
        for k in range(5):                                      # spores drifting up off the water
            put(g, 4 + int(noise(k, 1, 12 + variant) * 24), 1 + int(noise(k, 2, 12 + variant) * 12), 'v' if k % 2 else 'q')
    return [''.join(r) for r in g]


# --- reeds --------------------------------------------------------------------------------------
def line(g, x0, y0, x1, y1, role, w=32, h=32):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for k in range(n + 1):
        x, y = round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)
        if 0 <= x < w and 0 <= y < h:
            g[y][x] = role


def build_reeds(variant, frame=0, frames=4, corrupted=False):
    g = [['.'] * 32 for _ in range(32)]
    n = [6, 8, 5][variant]
    sway = math.sin(2 * math.pi * frame / frames) * 1.6
    stalks = []
    for k in range(n):
        bx = 16 + (k - n / 2) * 2.2 + 1.2 * (noise(k, variant, 8) - 0.5)
        by = 25 + 2 * noise(k, variant, 9) - 1
        hgt = 11 + 9 * noise(k, variant, 10) + (3 if k in (n // 2, n // 2 - 1) else 0)
        lean = (noise(k, variant, 11) - 0.5) * 5 + (k - n / 2) * 0.6
        stalks.append((bx, by, hgt, lean))
    base_dark, base_mid, base_light = ('D', 's', 'q') if corrupted else ('B', 'A', 'z')
    for bx, by, hgt, lean in sorted(stalks, key=lambda s: s[1]):
        px, py = bx, by
        top = None
        steps = int(hgt)
        for s in range(steps):
            f = s / steps
            x = bx + lean * f * f + sway * f * f
            y = by - s
            g[int(y)][int(round(x))] = base_dark if s < 2 else (base_mid if (s % 5) else base_light)
            if s > 3 and s % 2 == 0 and 0 <= round(x) + 1 < 32 and g[int(y)][round(x) + 1] == '.':
                g[int(y)][round(x) + 1] = base_mid if s < steps * 0.6 else base_light
            top = (x, y)
        tx, ty = round(top[0]), int(top[1])
        if variant != 1 and noise(int(bx * 3), variant, 5) > 0.35:           # a head on some of them: a cattail, or in the corrupted a glowing spore bulb
            for dy in range(0, 4):
                for dx in (0, 1):
                    xx, yy = tx + dx - (1 if dx else 0) + 0, ty - dy + 1
                    if 0 <= xx < 32 and 0 <= yy < 32:
                        g[yy][xx] = ('j' if dy in (1, 2) else 'y') if corrupted else ('g' if dx == 0 else 'f') if dy else 'w'
            if corrupted:
                put(g, tx + 1, ty - 5, 'v')
    for k in range(6):                                                  # dark mud and a ripple at the foot
        put(g, 9 + k * 3, 26 + (k % 2), 'x' if not corrupted else 'D')
    for k in range(10):
        put(g, 8 + k * 2 + (1 if k % 3 == 0 else 0), 27 if k % 2 else 26, 'o' if not corrupted else 'q') if g[27 if k % 2 else 26][8 + k * 2] == '.' else None
    return [''.join(r) for r in g]


# --- assembling ---------------------------------------------------------------------------------
_CACHE = {}


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


STEPS = [('stepping-2x1', rect(2, 1)), ('stepping-1x2', rect(1, 2)), ('stepping-1x3', rect(1, 3)), ('stepping-3x1', rect(3, 1))]


def pieces():
    """Every asset: (id, label, kind, [piece dicts or frame rows], extra)."""
    out = []
    for fx, fy in ((1, 2), (2, 1), (1, 3), (3, 1)):
        for cor in (False, True):
            d = cached(('dock', fx, fy, cor), lambda fx=fx, fy=fy, cor=cor: build_dock(fx, fy, cor))
            out.append((f'dock-{fx}x{fy}' + ('-corrupted' if cor else ''), f"Dock {fx} x {fy}{', rotted' if cor else ''}", 'still', [d], {}))
    for fx, fy in ((2, 1), (1, 2)):
        d = cached(('boat', fx, fy), lambda fx=fx, fy=fy: build_rowboat(fx, fy))
        out.append((f'rowboat-{fx}x{fy}', f'Rowboat {fx} x {fy}', 'still', [d], {}))
    vs = [cached(('step1', v), lambda v=v: build_stepping({(0, 0)}, 1100 + 41 * v)) for v in range(3)]
    out.append(('stepping-1x1', 'Stepping stone 1 x 1', 'variants', vs, {'names': ['A', 'B', 'C']}))
    for sid, cells in STEPS:
        d = cached((sid,), lambda cells=cells, sid=sid: build_stepping(cells, 1200 + len(sid)))
        out.append((sid, 'Stepping stones ' + sid.split('-')[1].replace('x', ' x '), 'still', [d], {}))
    for face in ('NE', 'SE'):
        for cor in (False, True):
            fr = [cached(('fall', face, f, cor), lambda f=f, face=face, cor=cor: build_waterfall(face, f, 6, cor)) for f in range(6)]
            out.append((f"waterfall-{face.lower()}" + ('-corrupted' if cor else ''), f"Waterfall {face}{', corrupted' if cor else ''}", 'animation', fr, {'fps': 8}))
    out.append(('lily-pads', 'Lily pads', 'variants', [dict(rows=build_lily(v), kind='decal') for v in range(4)], {'names': ['One', 'Two', 'Three', 'Cluster']}))
    out.append(('mushroom-pads', 'Mushroom pads (corrupted)', 'variants', [dict(rows=build_lily(v, True), kind='decal') for v in range(4)], {'names': ['One', 'Two', 'Three', 'Cluster']}))
    for cor in (False, True):
        tag = '-corrupted' if cor else ''
        out.append((f'reeds{tag}', 'Reeds' + (' (corrupted)' if cor else ''), 'variants', [dict(rows=build_reeds(v, 0, 4, cor), kind='reeds') for v in range(3)], {'names': ['Tall', 'Thick', 'Short']}))
        out.append((f'reeds{tag}-sway', 'Reeds swaying' + (' (corrupted)' if cor else ''), 'animation', [dict(rows=build_reeds(0, f, 4, cor), kind='reeds') for f in range(4)], {'fps': 4}))
    return out


def walkable_of(d):
    return bool(d['cover']) and min(d['cover'].values()) >= WALK_MIN


def build_assets():
    out = []
    for sid, label, kind, items, extra in pieces():
        first = items[0]
        if first.get('kind') == 'decal':
            make = family(CATEGORY, 32, 16, ANCHOR_DECAL, place='ground', folder=FOLDER)
            out.append(make(sid, label, kind, [d['rows'] for d in items], footprint={'size': [1, 1], 'cells': [[0, 0]]}, walkable=False, surface='water', **extra))
            continue
        if first.get('kind') == 'reeds':
            make = family(CATEGORY, 32, 32, (16, 25), place='ground', folder=FOLDER)
            fps = extra.get('fps', 0)
            ex = {k: v for k, v in extra.items() if k != 'fps'}
            out.append(make(sid, label, kind, [d['rows'] for d in items], fps=fps, footprint={'size': [1, 1], 'cells': [[0, 0]]}, walkable=False, surface='shore', **ex))
            continue
        rows0 = first['rows']
        make = family(CATEGORY, len(rows0[0]), len(rows0), first['anchor'], place='ground', folder=FOLDER)
        fps = extra.get('fps', 0)
        ex = {k: v for k, v in extra.items() if k != 'fps'}
        walk = walkable_of(first) if kind == 'still' else all(walkable_of(d) for d in items if d['cover'])
        cover = {f'{i},{j}': round(v, 2) for (i, j), v in first['cover'].items()}
        rec = make(sid, label, kind, [d['rows'] for d in items], fps=fps,
                   footprint={'size': [first['fx'], first['fy']], 'cells': [list(c) for c in sorted(first['cells'])]},
                   walkable=walk and bool(first['cover']), levels=first['levels'], style=first['style'], surface='water', **ex)
        if cover:
            rec['top_cover'] = cover
        out.append(rec)
    return out


FOLDER_README = 'README.md'


def write_package(folder):
    recs = {a['id']: {'label': a['label'], 'file': f"{a['id']}.png", 'size': a['footprint']['size'], 'cells': a['footprint']['cells'], 'walkable': a['walkable'],
                      **({'levels': a['levels']} if 'levels' in a else {}), **({'top_cover': a['top_cover']} if 'top_cover' in a else {})} for a in build_assets()}
    write_json(folder, 'water-props.json', 'The water props in this folder. See README.md beside this file.', {'level': p3.LEVEL, 'walk_min': WALK_MIN, 'deck_levels': DECK, 'props': recs})


# --- preview ------------------------------------------------------------------------------------
def preview(path, scale=2):
    from PIL import Image, ImageDraw
    rgb = p3.role_rgb()
    water_c, water_hi = rgb['n'] + (255,), rgb['o'] + (255,)
    items = pieces()
    tiles = []
    for sid, label, kind, frames, extra in items:
        first = frames[0]
        tiles.append((sid, label, kind, frames, first))
    W = 1500
    pad = 16
    x, y, rowh = pad, pad, 0
    placed = []
    for sid, label, kind, frames, first in tiles:
        ims = []
        for d in frames:
            ims.append(p3.rows_to_image(d['rows'], rgb, scale))
        count = len(ims)
        w = max(sum(i.width for i in ims) + 6 * (count - 1), 7 * len(sid) + 40)
        h = max(i.height for i in ims) + 26
        if x + w > W - pad:
            x, y, rowh = pad, y + rowh + 12, 0
        placed.append((sid, label, kind, frames, first, ims, x, y))
        x += max(w, 7 * len(sid) + 40) + 22
        rowh = max(rowh, h)
    sheet = Image.new('RGBA', (W, y + rowh + pad), (30, 34, 56, 255))
    d = ImageDraw.Draw(sheet)
    for sid, label, kind, frames, first, ims, px, py in placed:
        cx = px
        for k, (im, fr) in enumerate(zip(ims, frames)):
            top = py + 14
            if fr.get('kind') not in ('decal', 'reeds') and 'cells' in fr:
                ax, ay = fr['anchor']
                fx, fy = fr['fx'], fr['fy']
                ox, oy = ax - 8 * (fx + fy), ay - 4 * (fx + fy)
                for i, j in fr['cells']:
                    pts = [(ox + 16 * (X - Y) + 8 * (fx + fy) * 0, 0) for X, Y in ()]
                    pts = [(ax + 16 * ((X - fx / 2) - (Y - fy / 2)), ay + 8 * ((X - fx / 2) + (Y - fy / 2))) for X, Y in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                    d.polygon([(cx + a * scale, top + b * scale) for a, b in pts], fill=water_c, outline=water_hi)
            elif fr.get('kind') == 'decal':
                pts = [(16, 0), (32, 8), (16, 16), (0, 8)]
                d.polygon([(cx + a * scale, top + b * scale) for a, b in pts], fill=water_c, outline=water_hi)
            sheet.alpha_composite(im, (cx, top))
            cx += im.width + 6
        cov = first.get('cover') or {}
        tag = ''
        if cov:
            tag = f"  flat top {min(cov.values()):.2f}" + (' WALK' if min(cov.values()) >= WALK_MIN else ' no')
        d.text((px, py), sid + tag, fill=(230, 220, 200, 255))
    sheet.save(path)
    for sid, label, kind, frames, first in tiles:
        cov = first.get('cover') or {}
        if cov:
            print(f"{sid:28s} min flat top {min(cov.values()):.2f}  {'WALKABLE' if min(cov.values()) >= WALK_MIN else 'not walkable'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the water props ->', args.preview)


if __name__ == '__main__':
    main()
