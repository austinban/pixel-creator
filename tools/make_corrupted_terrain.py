#!/usr/bin/env python3
"""Features of the corrupted ground: mycelium veins that run across it, shelf fungus you can climb, vents that breathe spores and walls of thorns that can be cut down.

    mycelium   FLAT DECALS, 32 x 16, one ground tile each, laid under everything else. Their veins leave a tile by the middle of an edge at the same width and place every time, so any two
               tiles that both have a vein on the shared edge join. Pieces: an end, a straight, a corner, a tee and a cross (each turned all the ways it can be), and a node, a fruiting
               body with no veins. Lay a network by choosing, for each tile, the piece whose open edges are the neighbours it should join.
    shelf      BRACKET FUNGUS with a flat top at a whole level that a unit can stand on, like the rock ledges: 1 x 1 at one and two levels, 1 x 2, 2 x 1 and 2 x 2 at one level, and two
               stepped ones (a 1 x 2 and a 2 x 2 at two levels with a one-level cell as the way up). `top_cover` is measured per cell.
    vent       a spore vent on one tile: a lipped hole in the ground with glowing nodules, and a puff of spores that rises and fades in a loop of six frames.
    thorns     a tangled wall of thorns that blocks a tile (1 x 1) or two (1 x 2, 2 x 1), each with an INTACT and a BROKEN picture: the broken one is cut stubs and litter.

Palette roles only. The mycelium has no outline (a stain has none); everything standing has the one-pixel outline.

    python3 tools/make_corrupted_terrain.py --preview previews/corrupted-terrain.png     every piece at 2x, the animation as a strip, the veins laid into a network
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
import propkit as pk  # noqa: E402
from propkit import Ellipsoid, Frustum, rnd, size_for  # noqa: E402

FOLDER = 'corrupted-terrain'
CATEGORY = 'Corrupted Terrain'
WALK_MIN = 0.6
FPS = 8

# --- mycelium -----------------------------------------------------------------------------------
# The tile's diamond is 32 x 16 with its middle at (16, 8). A vein leaves by the middle of an edge.
EDGES = {'se': (24, 12), 'nw': (8, 4), 'sw': (8, 12), 'ne': (24, 4)}      # the middles of the four edges, in pixels of the tile
ORDER = ('ne', 'se', 'sw', 'nw')                                         # clockwise on the screen
EDGE_HALF = 1.15                                                         # a vein's half width at an edge, in pixels: the same on both sides, so tiles join
CENTRE_HALF = 1.9
VEIN = {'rim': 'u', 'body': 'i', 'lit': 'e', 'glow': 'o'}


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)), t


def vein_path(edge, seed, steps=14):
    """Pixel points from the middle of the tile to an edge's middle with a wobble that is nothing at either end (and slope nothing, so tiles join without a kink)."""
    ex, ey = EDGES[edge]
    cx, cy = 16.0, 8.0
    dx, dy = ex - cx, ey - cy
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    amp = (rnd(seed, 1) - 0.5) * 5.0
    pts = []
    for k in range(steps + 1):
        s = k / steps
        w = amp * math.sin(math.pi * s) ** 2
        pts.append((cx + dx * s + nx * w, cy + dy * s + ny * w, s))
    return pts


def mycelium_painter(edges, seed, node=False):
    # the shape at an edge must not depend on the tile, so a path's own noise is fixed by the edge's side, not by the seed
    paths = [vein_path(e, 100 + ORDER.index(e)) for e in edges]
    twigs = []
    for pi, pts in enumerate(paths):                                     # short side branches that end inside the tile
        for k in (4, 9):
            if rnd(seed, 20 + pi * 7 + k) > 0.5:
                x, y, s = pts[k]
                ang = (rnd(seed, 40 + pi * 7 + k) - 0.5) * 2.4 + math.atan2(8 - y, 16 - x) + math.pi / 2 * (1 if rnd(seed, 50 + k) > 0.5 else -1)
                ln = 3.0 + 4.0 * rnd(seed, 60 + pi * 7 + k)
                twig = (x, y, x + ln * math.cos(ang), y + ln * math.sin(ang) * 0.6)
                # a twig stays clear of every edge's middle, so the vein at a seam is the same in every tile
                if all(seg_dist(c[0], c[1], *twig)[0] > 4.5 for c in EDGES.values()):
                    twigs.append(twig)
    nodules = [(16 + 5.5 * math.cos(a), 8 + 2.6 * math.sin(a), 1.6 + 0.7 * rnd(seed, 80 + k)) for k, a in enumerate((0.4, 1.5, 2.6, 3.7, 4.9))] if node else []

    def paint(X, Y, px, py):
        x, y = px + 0.5, py + 0.5
        best = None
        for pts in paths:
            for (x0, y0, s0), (x1, y1, s1) in zip(pts, pts[1:]):
                d, t = seg_dist(x, y, x0, y0, x1, y1)
                s = s0 + (s1 - s0) * t
                half = EDGE_HALF + (CENTRE_HALF - EDGE_HALF) * (1 - s) ** 2
                if d <= half and (best is None or d / half < best[0]):
                    best = (d / half, s)
        for x0, y0, x1, y1 in twigs:
            d, t = seg_dist(x, y, x0, y0, x1, y1)
            half = 0.75 * (1 - t) + 0.25
            if d <= half and (best is None or d / half < best[0]):
                best = (d / half, 0.5)
        for nx_, ny_, r in nodules:
            d = math.hypot((x - nx_) / 1.0, (y - ny_) / 0.62)
            if d <= r:
                role = VEIN['glow'] if d < r * 0.38 else VEIN['lit'] if d < r * 0.7 else VEIN['body']
                return role
        if node and math.hypot((x - 16) / 1.0, (y - 8) / 0.55) < 2.6:
            return VEIN['glow'] if math.hypot((x - 16), (y - 8) / 0.55) < 1.0 else VEIN['lit']
        if best is None:
            return None
        r, s = best
        if r > 0.72:
            return VEIN['rim']
        if r < 0.28 and rnd(seed, int(x), int(y)) > 0.55:
            return VEIN['lit']
        return VEIN['body']
    return paint


def mycelium_pieces():
    kinds = []
    kinds.append(('end', [(e,) for e in ORDER]))
    kinds.append(('straight', [('ne', 'sw'), ('nw', 'se')]))
    kinds.append(('corner', [(ORDER[i], ORDER[(i + 1) % 4]) for i in range(4)]))
    kinds.append(('tee', [tuple(e for j, e in enumerate(ORDER) if j != i) for i in range(4)]))
    kinds.append(('cross', [ORDER]))
    out = []
    for kind, sets in kinds:
        for edges in sets:
            name = f"mycelium-{kind}" + ('' if len(sets) == 1 else '-' + '-'.join(edges if kind != 'tee' else [e for e in ORDER if e not in edges]))
            if kind == 'tee':
                name = f"mycelium-tee-no-{[e for e in ORDER if e not in edges][0]}"
            out.append((name, f"Mycelium, {kind} ({', '.join(edges)})", edges))
    out.append(('mycelium-node', 'Mycelium, fruiting node', ()))
    return out


def mycelium_rows(name, edges):
    painter = mycelium_painter(edges, sum(map(ord, name)), node=not edges)
    rows, anchor = pk.decal(1, 1, painter)
    return rows


# --- shelf fungus -------------------------------------------------------------------------------
CAP = ('c', 'e', 'f', 'g')                # the top of a bracket: salmon, coral, orchid, plum
UNDER = ('C', 'c', 'e', 'g')              # the pale pores and gills under it
STEM = ('t', 'C', 'c', 'f')


def rings_mark(level):
    def mark(body, p, n, step, px, py):
        if n[2] > 0.9 and step == 0:                       # growth rings on the flat top
            d = math.hypot(p[0] - body.c[0], p[1] - body.c[1])
            if int(d * 9) % 3 == 0:
                return CAP[1]
            if pk.hashed(px, py, 9) % 29 == 0:
                return CAP[2]
        elif step < 3 and pk.hashed(px, py, 4) % 17 == 0:
            return body.mat[min(3, step + 1)]
        return None
    return mark


def shelf_bodies(cells, levels, seed):
    """Lumps for every cell, every edge between two cells and every inside corner, each flat at its cell's level (the lower of two for an edge), over a stem or two."""
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    top = max(levels.values())
    pts = {}
    for i, j in cells:
        pts[(i + 0.5, j + 0.5)] = levels[(i, j)]
        for dx, dy in ((1, 0), (0, 1)):
            if (i + dx, j + dy) in cells:
                pts[(i + 0.5 + dx / 2, j + 0.5 + dy / 2)] = min(levels[(i, j)], levels[(i + dx, j + dy)])
        if all((i + a, j + b) in cells for a, b in ((1, 0), (0, 1), (1, 1))):
            pts[(i + 1.0, j + 1.0)] = min(levels[(i + a, j + b)] for a, b in ((0, 0), (1, 0), (0, 1), (1, 1)))
    bodies = []
    for k, ((x, y), lv) in enumerate(sorted(pts.items())):
        s = seed + k * 41
        r = 0.6 + 0.05 * rnd(s, 1)
        bx, by = x - fx / 2, y - fy / 2
        bodies.append(Ellipsoid(CAP, (bx, by, lv - 0.18), (r, r * (0.95 + 0.1 * rnd(s, 2)), 0.4), lo=lv - 0.5, hi=float(lv), mark=rings_mark(lv)))
        bodies.append(Frustum(UNDER, (bx, by), lv - 0.5, lv - 0.2, r * 0.7, r * 0.92, mark='gills'))
    # stems: one under each cell that is at least a level up
    for i, j in sorted(cells):
        lv = levels[(i, j)]
        if lv >= 1:
            bodies.append(Frustum(STEM, (i + 0.5 - fx / 2 + 0.03 * (rnd(seed, i, j) - 0.5), j + 0.5 - fy / 2), 0.0, lv - 0.3, 0.22, 0.15, mark='speckle'))
            bodies.append(Ellipsoid(STEM, (i + 0.5 - fx / 2, j + 0.5 - fy / 2, 0.15), (0.32, 0.32, 0.25), lo=0.0, mark='speckle'))
    return bodies, top


SHELVES = []
for lv in (1, 2):
    SHELVES.append((f'shelf-1x1-h{lv}', f'Shelf fungus 1 x 1, {lv} high', {(0, 0): lv}))
SHELVES += [('shelf-1x2-h1', 'Shelf fungus 1 x 2, 1 high', {(0, 0): 1, (0, 1): 1}), ('shelf-2x1-h1', 'Shelf fungus 2 x 1, 1 high', {(0, 0): 1, (1, 0): 1}),
            ('shelf-2x2-h1', 'Shelf fungus 2 x 2, 1 high', {(i, j): 1 for i in (0, 1) for j in (0, 1)}),
            ('shelf-1x2-h2-step', 'Shelf fungus 1 x 2, 2 high with a step', {(0, 0): 2, (0, 1): 1}),
            ('shelf-2x2-h2-step', 'Shelf fungus 2 x 2, 2 high with a step', {(0, 0): 2, (1, 0): 2, (0, 1): 2, (1, 1): 1})]


def shelf_render(levels, seed):
    cells = set(levels)
    bodies, top = shelf_bodies(cells, levels, seed)
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    w, h, anchor = size_for(fx, fy, top + 0.1, pad=12)
    return pk.render(bodies, w, h, anchor), anchor, (fx, fy), bodies, cells


def shelf_cover(levels, seed):
    rows, anchor, fp, bodies, cells = shelf_render(levels, seed)
    return pk.top_cover(bodies, cells, lambda i, j: levels[(i, j)])


# --- spore vent -----------------------------------------------------------------------------------
VENT_FRAMES = 6
VENT_W, VENT_H = 32, 48
VENT_ANCHOR = (16, 40)
LIP = ('c', 'e', 'f', 'g')
NODULE = ('r', 'o', 'o', 'q')


def vent_base(frame):
    glow = [('r', 'o'), ('t', 'r'), ('r', 'o'), ('o', 'q'), ('q', 'q'), ('o', 'q')][frame % 6]
    bodies = [Ellipsoid(LIP, (0, 0, 0.0), (0.5, 0.5, 0.2), lo=0.0, mark=pk_mark_speckle()),
              Frustum(LIP, (0, 0), 0.0, 0.17, 0.4, 0.3, mark='speckle'),
              Frustum(('x', 'w', 'x', 'x'), (0, 0), 0.1, 0.2, 0.27, 0.25)]
    for k in range(5):
        a = 0.3 + k * 2 * math.pi / 5
        bodies.append(Ellipsoid(glow + glow, (0.37 * math.cos(a), 0.37 * math.sin(a), 0.16), (0.08, 0.08, 0.09), glow=True))
    return bodies


def pk_mark_speckle():
    def mark(body, p, n, step, px, py):
        if step < 3 and pk.hashed(px, py, 6) % 13 == 0:
            return body.mat[min(3, step + 1)]
        return None
    return mark


def puff(rows, frame):
    """Spores drawn over the vent: seven puffs that rise from the hole in turn, swell, change from bright to dim and thin out, a loop of VENT_FRAMES frames."""
    grid = [list(r) for r in rows]
    h, w = len(grid), len(grid[0])
    ox, oy = 16.0, 37.0
    for k in range(9):
        phase = (k / 9.0 + frame / VENT_FRAMES) % 1.0
        age = phase
        sway = math.sin((k * 1.7) + age * 3.0) * (1.0 + 3.0 * age)
        cx, cy = ox + sway + (rnd(31, k) - 0.5) * 2, oy - 4 - 24.0 * age ** 0.9
        r = 1.8 + 4.2 * age ** 0.7
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                d = math.hypot((x + 0.5 - cx), (y + 0.5 - cy) * 1.1)
                if d > r:
                    continue
                if age > 0.45 and pk.hashed(x, y, k + frame * 3) % 100 < (age - 0.45) * 160:       # thinning out with age
                    continue
                lit = d < r * 0.5 and age < 0.8
                role = ('t' if lit and age < 0.3 else 'r' if lit else 'q' if age < 0.55 else 'p' if age < 0.8 else 's')
                if d > r - 1.0 and age < 0.8:
                    role = 'q' if age < 0.55 else 'p'
                grid[y][x] = role
    return pk.add_outline([''.join(r) for r in grid])


def vent_frame(frame):
    w, h, anchor = VENT_W, VENT_H, VENT_ANCHOR
    rows = pk.render(vent_base(frame), w, h, anchor, outline=False)
    return puff(rows, frame)


# --- thorn walls ---------------------------------------------------------------------------------
VINE = ('A', 'B', 's', 'D')
VINE_DARK = ('B', 's', 'D', 'x')
THORN = ('c', 'e', 'h', 'u')


def vine_mark(body, p, n, step, px, py):
    if step < 3 and pk.hashed(px, py, 8) % 11 == 0:
        return body.mat[min(3, step + 1)]
    if step == 0 and pk.hashed(px // 2, py, 12) % 9 == 0:
        return 'z'
    return None


def thorn_bodies(fx, fy, broken, seed):
    """A tangle: upright stalks and cross vines along the wall's long axis (x, or y for a 1 x 2), thick at the foot. Broken: the stalks cut low, the middle gone, litter on the ground."""
    along_x = fx >= fy
    n = max(fx, fy)
    bodies = []
    length = n * 0.9
    count = 8 * n
    for k in range(count):
        t = (k + 0.5) / count - 0.5
        pos = t * length * 1.08 + (rnd(seed, 1, k) - 0.5) * 0.12
        off = (rnd(seed, 2, k) - 0.5) * 0.34
        x, y = (pos, off) if along_x else (off, pos)
        hgt = 0.7 + 0.65 * rnd(seed, 3, k)
        if broken:
            gap = abs(t) < 0.18 * (n if n == 1 else 1.0) * (0.7 if n == 1 else 0.55)
            if gap:
                continue
            hgt = 0.12 + 0.3 * rnd(seed, 3, k)
        bodies.append(Frustum(VINE if k % 3 else VINE_DARK, (x, y), 0.0, hgt, 0.1 + 0.03 * rnd(seed, 4, k), 0.04, mark=vine_mark))
    bodies.append(Ellipsoid(VINE_DARK, (0, 0, 0.0), ((length / 2 + 0.1) if along_x else 0.3, 0.3 if along_x else (length / 2 + 0.1), 0.45 if not broken else 0.12), lo=0.0, mark=vine_mark))
    if not broken:
        for k in range(9 * n):                                 # the cross vines: long thin lumps along the wall's axis, at different heights
            hh = 0.35 + 0.95 * rnd(seed, 5, k)
            pos = (rnd(seed, 6, k) - 0.5) * length * 0.6
            off = (rnd(seed, 7, k) - 0.5) * 0.3
            ln = 0.3 + 0.3 * rnd(seed, 8, k)
            if along_x:
                bodies.append(Ellipsoid(VINE, (pos, off, hh), (ln, 0.09, 0.09), lo=0.0, mark=vine_mark))
            else:
                bodies.append(Ellipsoid(VINE, (off, pos, hh), (0.09, ln, 0.09), lo=0.0, mark=vine_mark))
    else:
        for k in range(4 * n):                                 # litter
            pos = (rnd(seed, 9, k) - 0.5) * length * 0.9
            off = (rnd(seed, 10, k) - 0.5) * 0.5
            x, y = (pos, off) if along_x else (off, pos)
            bodies.append(Ellipsoid(VINE_DARK if k % 2 else VINE, (x, y, 0.04), ((0.2, 0.06, 0.05) if (k + int(rnd(seed, 11, k) * 3)) % 2 == 0 else (0.06, 0.2, 0.05)), lo=0.0, mark=vine_mark))
        for k in range(3 * n):                                 # the cut ends are pale
            pos = (rnd(seed, 12, k) - 0.5) * length * 0.9
            off = (rnd(seed, 13, k) - 0.5) * 0.3
            x, y = (pos, off) if along_x else (off, pos)
            bodies.append(Frustum(('C', 'c', 'e', 'f'), (x, y), 0.0, 0.1 + 0.2 * rnd(seed, 14, k), 0.07, 0.05))
    return bodies


def add_thorns(rows, seed, broken):
    """Spikes: wherever the silhouette has an edge facing up or sideways, now and then a two-pixel thorn in coral and plum."""
    grid = [list(r) for r in rows]
    h, w = len(grid), len(grid[0])
    for y in range(2, h - 1):
        for x in range(1, w - 1):
            if rows[y][x] in '.O' or rows[y - 1][x] != '.':
                continue
            if pk.hashed(x, y, seed) % (7 if not broken else 14) == 0:
                grid[y - 1][x] = THORN[0]
                if rows[y - 2][x] == '.':
                    grid[y - 2][x + (1 if pk.hashed(x, y, 3) % 2 else -1)] = THORN[1]
    for y in range(h):
        for x in range(1, w - 1):
            if rows[y][x] in '.O':
                continue
            for dx in (-1, 1):
                if rows[y][x + dx] == '.' and pk.hashed(x, y, seed + 9) % (9 if not broken else 18) == 0:
                    grid[y][x + dx] = THORN[0] if dx > 0 else THORN[1]
    return pk.add_outline([''.join(r) for r in grid])


THORN_WALLS = [('thorn-wall-1x1', 'Thorn wall 1 x 1', 1, 1), ('thorn-wall-1x2', 'Thorn wall 1 x 2', 1, 2), ('thorn-wall-2x1', 'Thorn wall 2 x 1', 2, 1)]


def thorn_render(fx, fy, broken, seed):
    w, h, anchor = size_for(fx, fy, 1.5 if not broken else 0.8, pad=8)
    rows = pk.render(thorn_bodies(fx, fy, broken, seed), w, h, anchor, outline=False)
    return add_thorns(rows, seed, broken), anchor


# --- the assets ------------------------------------------------------------------------------------
def seed_of(name):
    return sum(ord(c) * (i + 1) for i, c in enumerate(name))


def build_assets():
    out = []
    mk = family(CATEGORY, 32, 16, (16, 8), place='ground', folder=FOLDER)
    for name, label, edges in mycelium_pieces():
        out.append(mk(name, label, 'still', [mycelium_rows(name, edges)], decal={'edges': list(edges), 'join': 'at the middle of an edge'}))
    for name, label, levels in SHELVES:
        rows, anchor, (fx, fy), bodies, cells = shelf_render(levels, seed_of(name))
        cover = pk.top_cover(bodies, cells, lambda i, j: levels[(i, j)])
        walk = min(cover.values()) >= WALK_MIN
        out.append(family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)(
            name, label, 'still', [rows], footprint={'size': [fx, fy], 'cells': [list(c) for c in sorted(cells)]}, walkable=walk, levels=max(levels.values()),
            cell_levels={f'{i},{j}': v for (i, j), v in sorted(levels.items())}, top_cover={f'{i},{j}': round(v, 2) for (i, j), v in sorted(cover.items())}))
    out.append(family(CATEGORY, VENT_W, VENT_H, VENT_ANCHOR, place='ground', folder=FOLDER)(
        'spore-vent', 'Spore vent (animation)', 'animation', [vent_frame(f) for f in range(VENT_FRAMES)], fps=FPS, vent={'loops': True, 'blocks': False}))
    for name, label, fx, fy in THORN_WALLS:
        for broken in (False, True):
            rows, anchor = thorn_render(fx, fy, broken, seed_of(name))
            out.append(family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)(
                name + ('-broken' if broken else ''), label + (', broken' if broken else ''), 'still', [rows],
                footprint={'size': [fx, fy], 'cells': [[i, j] for i in range(fx) for j in range(fy)]}, blocks=not broken, destroyable=True))
    return out


def write_package(folder):
    write_json(folder, 'corrupted-terrain.json', 'The corrupted terrain pieces in this folder. See README.md beside this file.',
               {'mycelium': {'cell': [32, 16], 'edge_half_width': EDGE_HALF, 'edges': {k: list(v) for k, v in EDGES.items()}},
                'shelf': {'walk_min': WALK_MIN}, 'vent': {'cell': [VENT_W, VENT_H], 'anchor': list(VENT_ANCHOR), 'frames': VENT_FRAMES, 'fps': FPS}})


# --- preview -------------------------------------------------------------------------------------
def network_preview(path):
    """A little network of mycelium laid over teal ground, to show that the tiles join: a ring and a branch."""
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}
    # the grid: (i, j) -> the set of edges that have a vein; chosen so that every shared edge agrees
    layout = {(1, 1): ('se', 'sw'), (2, 1): ('nw', 'se', 'sw'), (3, 1): ('nw', 'sw'), (1, 2): ('ne', 'se'), (2, 2): ('ne', 'se', 'nw', 'sw'), (3, 2): ('ne', 'sw'),
              (1, 3): ('ne', 'nw'), (2, 3): ('ne', 'nw'), (3, 3): ('ne',), (2, 4): ()}
    # fix up: a tile has an edge only if its neighbour has the opposite edge
    opp = {'se': 'nw', 'nw': 'se', 'sw': 'ne', 'ne': 'sw'}
    step = {'se': (1, 0), 'nw': (-1, 0), 'sw': (0, 1), 'ne': (0, -1)}
    clean = {}
    for (i, j), es in layout.items():
        keep = [e for e in es if (i + step[e][0], j + step[e][1]) in layout and opp[e] in layout[(i + step[e][0], j + step[e][1])]]
        clean[(i, j)] = tuple(keep)
    size = 6
    W, H = 16 * size * 2 + 40, 8 * size * 2 + 40
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ground = Image.new('RGBA', (W, H), (30, 34, 56, 255))
    d = ImageDraw.Draw(ground)
    for (i, j), edges in sorted(clean.items(), key=lambda kv: kv[0][0] + kv[0][1]):
        ox, oy = W // 2 + 16 * (i - j) - 16, 14 + 8 * (i + j)
        d.polygon([(ox, oy + 8), (ox + 16, oy), (ox + 32, oy + 8), (ox + 16, oy + 16)], fill=rgb['D'])
    for (i, j), edges in sorted(clean.items(), key=lambda kv: kv[0][0] + kv[0][1]):
        ox, oy = W // 2 + 16 * (i - j) - 16, 14 + 8 * (i + j)
        rows = mycelium_rows('network', edges) if edges else None
        if rows is None:
            continue
        # the painter's noise depends on the name (twigs), but the edges do not
        tile = Image.new('RGBA', (32, 16), (0, 0, 0, 0))
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    tile.putpixel((x, y), rgb[ch] + (255,))
        ground.alpha_composite(tile, (ox, oy))
    ground.resize((W * 3, H * 3), Image.NEAREST).save(path)


def preview(path):
    items = []
    for name, label, edges in mycelium_pieces():
        rows = mycelium_rows(name, edges)
        items.append(dict(label=name.replace('mycelium-', 'myc '), frames=[rows], anchor=(16, 8), fp=(1, 1), ground=(8, 58, 69, 255)))
    for name, label, levels in SHELVES:
        rows, anchor, fp, bodies, cells = shelf_render(levels, seed_of(name))
        cover = pk.top_cover(bodies, cells, lambda i, j: levels[(i, j)])
        print(f"{name:22s} top_cover " + ' '.join(f'{k[0]},{k[1]}:{v:.2f}' for k, v in sorted(cover.items())) + (' WALK' if min(cover.values()) >= WALK_MIN else ' no'))
        items.append(dict(label=name.replace('shelf-', 'shelf '), frames=[rows], anchor=anchor, fp=fp, walk=cover, cells=cells))
    items.append(dict(label='spore-vent (6 frames)', frames=[vent_frame(f) for f in range(VENT_FRAMES)], anchor=VENT_ANCHOR, fp=(1, 1), ground=(8, 58, 69, 255)))
    for name, label, fx, fy in THORN_WALLS:
        for broken in (False, True):
            rows, anchor = thorn_render(fx, fy, broken, seed_of(name))
            items.append(dict(label=name.replace('thorn-wall-', 'thorns ') + (' broken' if broken else ''), frames=[rows], anchor=anchor, fp=(fx, fy), ground=(8, 58, 69, 255)))
    pk.contact_sheet(path, items)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--network', type=Path, help='a small network of mycelium laid over the ground, to show the tiles join')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the corrupted terrain ->', args.preview)
    if args.network:
        network_preview(args.network)
        print('the network ->', args.network)


if __name__ == '__main__':
    main()
