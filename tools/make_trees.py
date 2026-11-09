#!/usr/bin/env python3
"""More basic trees and bushes, to stand beside the ground sheet's round bush and pine: ten of them, tall ones among them, each on one ground tile.

Each is a small 3D model of round solids (ellipsoids for crowns, lumps and berries, tapering cylinders for trunks and the tiers of a fir), drawn in exactly the ground tiles' projection (16 across and 8 down a
cell, 16 pixels a level), in the shared colour roles, with the one-pixel outline. It reuses the mushrooms' ray-caster (make_fungi.py). A tree looks the same from every side, so there is one picture of each (NW and SW are it
flipped, which a game can do for variety). Foliage is built of many small lumps, so its edge is bumpy and a lit clump sits against a shaded one, with a little dither in each, like the bush and the pine.

     1  tall-pine    a very tall slim pine of four tapering tiers on a thin trunk
     2  spruce       a tall narrow fir in dark blue-green, with six drooping skirts
     3  poplar       a tall columnar poplar, bright green
     4  tall-oak     a tall tree with a long clean trunk and a big crown of five overlapping lobes
     5  broad-oak    a wide spreading crown on a thick short trunk
     6  birch        a slender white trunk with dark marks and a loose yellow-green crown
     7  small-pine   a sapling pine about the size of the bush
     8  dead-tree    bare gnarled branches, no leaves
     9  berry-bush   a round bush with red berries
    10  hedge        a long low trimmed hedge

    python3 tools/make_trees.py --preview previews/trees.png        the ten, enlarged, on grass, with the sheet's bush and pine at the left

As assets they are the **Trees** category (folder `trees`), ids `tree-NAME` and `bush-NAME`.
"""
import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from make_fungi import Ellipsoid, Frustum, LIGHT, PX, hashed, step_of  # noqa: E402,F401

CATEGORY = 'Trees'
FOLDER = 'trees'

# --- colours: a ramp is four roles, lit to dark --------------------------------------------------
PINE = ('A', 'B', 's', 'D')            # the sheet's own greens (green, emerald, deep teal), and an abyss for the darkest
FIR = ('B', 's', 'D', 'D')             # darker and bluer
BRIGHT = ('z', 'A', 'B', 's')          # lime down to emerald
LIME = ('z', 'z', 'A', 'B')            # the lightest, for the poplar
YELLOW = ('d', 'z', 'A', 'B')          # yellow-green, for the birch
BARK = ('a', 'e', 'g', 'w')            # orange-brown: the stump's and the pine's trunk
DEADWOOD = ('C', 'C', 'c', 'f')        # bleached grey-brown: mostly sand, shaded to salmon and orchid
BIRCHBARK = ('t', 'C', 'c', 'e')


# --- building blocks -----------------------------------------------------------------------------
def lump(c, r, mat, mark='leaf', squash=0.85, **extra):
    return Ellipsoid(mat, c, (r, r, r * squash), mark=mark, **extra)


def crown(c, radii, count, lobe, mats, seed, mark='leaf', shell=(0.7, 1.0)):
    """A solid crown: a core ellipsoid that fills it, and `count` small lumps scattered over its shell so the edge is bumpy and clumps read."""
    rng = random.Random(seed)
    cx, cy, ch = c
    rx, ry, rh = radii
    out = [Ellipsoid(mats[0], c, (rx * 0.82, ry * 0.82, rh * 0.82), mark=mark)]
    for i in range(count):
        a = rng.uniform(0, math.tau)
        v = rng.uniform(-0.95, 1.0)                                  # how high on the crown: -1 the bottom, 1 the top
        s = math.sqrt(max(0.0, 1 - v * v))
        k = rng.uniform(*shell)
        r = lobe * rng.uniform(0.8, 1.2)
        out.append(lump((cx + rx * k * s * math.cos(a), cy + ry * k * s * math.sin(a), ch + rh * k * v), r, mats[i % len(mats)], mark))
    return out


def chain(points, r0, r1, mat, mark='bark'):
    """A limb: small ellipsoids along a polyline, thick at the first point and thin at the last."""
    segs = []
    for p, q in zip(points, points[1:]):
        segs.append((p, q, math.dist(p, q)))
    total = sum(s[2] for s in segs) or 1.0
    out, walked = [], 0.0
    for p, q, length in segs:
        n = max(1, int(length / 0.12))
        for i in range(n):
            t = i / n
            u = (walked + length * t) / total
            r = r0 + (r1 - r0) * u
            out.append(Ellipsoid(mat, tuple(p[k] + (q[k] - p[k]) * t for k in range(3)), (r, r, r), mark=mark))
        walked += length
    out.append(Ellipsoid(mat, points[-1], (r1, r1, r1), mark=mark))
    return out


def trunk(h, r_foot, r_top, bark=BARK, flare=1.4, cx=0.0, cy=0.0):
    """An upright trunk that flares at the root."""
    return [Frustum(bark, (cx, cy), 0.0, h, r_foot, r_top, mark='bark'),
            Ellipsoid(bark, (cx, cy, 0.04), (r_foot * flare, r_foot * flare, 0.2), lo=0.0, mark='bark')]


def tier(h0, h1, r0, r1, mat, seed, rim=8, drop=0.04):
    """One cone of needles with a ring of lumps round its foot, so the skirt has a ragged, drooping edge."""
    rng = random.Random(seed)
    out = [Frustum(mat, (0, 0), h0, h1, r0, r1, mark='leaf')]
    for i in range(rim):
        a = math.tau * (i + rng.uniform(-0.15, 0.15)) / rim
        out.append(Ellipsoid(mat, (r0 * 0.92 * math.cos(a), r0 * 0.92 * math.sin(a), h0 + 0.06 - drop), (r0 * 0.3, r0 * 0.3, 0.13), mark='leaf'))
    return out


# --- the ten --------------------------------------------------------------------------------------
def tall_pine():
    out = trunk(5.9, 0.12, 0.05)
    for n, (h0, h1, r0, r1) in enumerate(((0.9, 2.5, 0.66, 0.2), (1.9, 3.6, 0.56, 0.17), (3.0, 4.7, 0.45, 0.13), (4.0, 5.6, 0.33, 0.08))):
        out += tier(h0, h1, r0, r1, PINE, 10 + n, rim=9 - n)
    out.append(Frustum(PINE, (0, 0), 5.3, 6.4, 0.2, 0.0, mark='leaf'))
    return out


def spruce():
    out = trunk(5.2, 0.1, 0.05)
    for n, (h0, h1, r0, r1) in enumerate(((0.55, 1.45, 0.58, 0.25), (1.2, 2.2, 0.52, 0.22), (1.9, 2.95, 0.46, 0.2), (2.6, 3.7, 0.4, 0.17), (3.35, 4.4, 0.32, 0.13), (4.05, 5.1, 0.24, 0.08))):
        out += tier(h0, h1, r0, r1, FIR, 30 + n, rim=8, drop=0.1)
    out.append(Frustum(FIR, (0, 0), 4.9, 6.0, 0.14, 0.0, mark='leaf'))
    return out


def poplar():
    out = trunk(1.0, 0.09, 0.07)
    out += crown((0, 0, 3.55), (0.44, 0.44, 2.75), 34, 0.25, (LIME, BRIGHT, PINE), 50, shell=(0.75, 1.05))
    return out


def tall_oak():
    out = trunk(3.5, 0.17, 0.12, flare=1.45)
    out += chain([(0, 0, 3.0), (-0.28, 0.08, 3.8)], 0.1, 0.06, BARK)
    out += chain([(0, 0, 3.1), (0.3, -0.1, 3.9)], 0.1, 0.06, BARK)
    lobes = ((0.0, 0.0, 5.75, 0.72), (-0.5, 0.18, 4.95, 0.68), (0.5, -0.16, 4.9, 0.68), (-0.08, 0.5, 4.4, 0.58), (0.1, -0.5, 4.45, 0.58))
    for n, (x, y, h, r) in enumerate(lobes):
        out += crown((x, y, h), (r, r, r * 0.9), 11, r * 0.34, (BRIGHT, PINE) if n % 2 == 0 else (PINE, BRIGHT), 70 + n)
    return out


def broad_oak():
    out = trunk(1.5, 0.26, 0.2, flare=1.45)
    out += chain([(0, 0, 1.2), (-0.55, 0.1, 1.95)], 0.15, 0.09, BARK)
    out += chain([(0, 0, 1.3), (0.55, -0.1, 2.0)], 0.15, 0.09, BARK)
    ring = [(0.0, 0.0, 2.7, 0.62)]
    for i in range(6):
        a = math.tau * i / 6 + 0.3
        ring.append((0.62 * math.cos(a), 0.62 * math.sin(a), 2.2 + 0.16 * math.sin(i * 2.1), 0.5))
    for n, (x, y, h, r) in enumerate(ring):
        out += crown((x, y, h), (r, r, r * 0.8), 10, r * 0.34, (PINE, BRIGHT) if n % 2 == 0 else (BRIGHT, PINE), 90 + n)
    return out


def birch():
    out = trunk(3.4, 0.1, 0.06, bark=BIRCHBARK, flare=1.35)
    out[0].mark = out[1].mark = 'birch'
    out += chain([(0, 0, 2.5), (0.42, 0.08, 3.4)], 0.06, 0.05, BIRCHBARK, mark='birch')
    out += chain([(0, 0, 2.9), (-0.38, -0.1, 3.8)], 0.06, 0.05, BIRCHBARK, mark='birch')
    for n, (x, y, h, r) in enumerate(((0.0, 0.0, 4.2, 0.55), (0.42, 0.1, 3.45, 0.38), (-0.38, -0.1, 3.7, 0.4), (0.06, -0.3, 3.4, 0.34), (-0.1, 0.3, 4.9, 0.36))):
        out += crown((x, y, h), (r, r, r * 1.05), 8, r * 0.36, (YELLOW, BRIGHT), 110 + n)
    return out


def small_pine():
    out = trunk(1.5, 0.07, 0.03, flare=1.35)
    for n, (h0, h1, r0, r1) in enumerate(((0.35, 1.0, 0.38, 0.12), (0.8, 1.45, 0.29, 0.08))):
        out += tier(h0, h1, r0, r1, PINE, 130 + n, rim=7 - n, drop=0.03)
    out.append(Frustum(PINE, (0, 0), 1.3, 1.9, 0.12, 0.0, mark='leaf'))
    return out


def dead_tree():
    out = chain([(0, 0, 0), (-0.05, 0.03, 0.7), (0.05, -0.03, 1.5), (0.1, 0.0, 2.3), (0.04, 0.04, 3.0)], 0.2, 0.08, DEADWOOD)
    out.append(Ellipsoid(DEADWOOD, (0, 0, 0.05), (0.3, 0.3, 0.2), lo=0.0, mark='bark'))
    out += chain([(0.0, 0.0, 1.4), (-0.35, 0.1, 1.9), (-0.7, 0.18, 2.7)], 0.1, 0.06, DEADWOOD)
    out += chain([(-0.5, 0.14, 2.2), (-0.8, 0.0, 2.35)], 0.07, 0.06, DEADWOOD)
    out += chain([(0.06, 0.0, 1.9), (0.42, -0.1, 2.5), (0.62, -0.2, 3.4)], 0.1, 0.06, DEADWOOD)
    out += chain([(0.5, -0.14, 2.7), (0.85, -0.02, 2.95)], 0.07, 0.06, DEADWOOD)
    out += chain([(0.1, 0.0, 2.5), (-0.1, 0.12, 3.3), (-0.3, 0.15, 3.9)], 0.09, 0.06, DEADWOOD)
    out += chain([(0.04, 0.04, 3.0), (0.2, 0.0, 3.7)], 0.07, 0.06, DEADWOOD)
    return out


def berry_bush():
    return crown((0, 0, 0.58), (0.66, 0.66, 0.56), 16, 0.27, (PINE, BRIGHT, PINE), 150, mark='berry', shell=(0.75, 1.0))


def hedge():
    out = []
    for n, x in enumerate((-0.78, -0.52, -0.26, 0.0, 0.26, 0.52, 0.78)):
        out.append(Ellipsoid((PINE, BRIGHT)[n % 2], (x, -x * 0.12, 0.34), (0.42, 0.38, 0.74), lo=0.0, hi=0.98, mark='leaf'))
    return out


# name, label, builder, cell width, height in levels, what it is called as an asset id
SHAPES = [
    ('tall-pine', 'Tall pine', tall_pine, 48, 6.4, 'tree'),
    ('spruce', 'Spruce', spruce, 48, 6.0, 'tree'),
    ('poplar', 'Poplar', poplar, 48, 6.3, 'tree'),
    ('tall-oak', 'Tall oak', tall_oak, 64, 6.6, 'tree'),
    ('broad-oak', 'Broad oak', broad_oak, 64, 3.5, 'tree'),
    ('birch', 'Birch', birch, 48, 5.3, 'tree'),
    ('small-pine', 'Small pine', small_pine, 48, 1.9, 'tree'),
    ('dead-tree', 'Dead tree', dead_tree, 64, 4.1, 'tree'),
    ('berry-bush', 'Berry bush', berry_bush, 48, 1.3, 'bush'),
    ('hedge', 'Hedge', hedge, 64, 1.0, 'bush'),
]


def cell_of(width, tall):
    h = int(math.ceil(tall * PX)) + 22
    return width, h, (width // 2, h - 12)


# --- drawing -------------------------------------------------------------------------------------
def colour(body, p, n, step, px, py):
    r = body.mat
    mark = body.mark
    if mark in ('leaf', 'berry'):
        h = hashed(px, py, 7)
        if mark == 'berry' and h % 7 == 0 and n[2] > -0.2:
            return 'j' if step < 2 else 'h'
        if step < 3 and h % 5 == 0:
            return r[step + 1]
        if step > 0 and h % 11 == 0:
            return r[step - 1]
        return r[step]
    if mark == 'bark' and step < 3 and (px + hashed(0, py // 3, 2) % 3) % 4 == 0:
        return r[step + 1]
    if mark == 'birch':
        if hashed(0, py, 4) % 5 == 0 and (px + hashed(py, 0, 5)) % 7 < 3:
            return 'g' if step < 2 else 'w'
        return r[step]
    return r[step]


def render(builder, width, tall):
    w, h, (ax, ay) = cell_of(width, tall)
    bodies = builder()
    grid = [[None] * w for _ in range(h)]
    depth = [[0.0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            a, b = (px + 0.5 - ax) / 16.0, (py + 0.5 - ay) / 8.0
            ox, oy = (a + b) / 2, (b - a) / 2
            best = None
            for body in bodies:
                got = body.hit(ox, oy)
                if got and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], body)
            if best is None:
                continue
            t, n, body = best
            p = (ox + t, oy + t, t)
            grid[py][px] = (colour(body, p, n, step_of(n), px, py), id(body), body)
            depth[py][px] = t
    out = [[(c[0] if c else '.') for c in row] for row in grid]
    # where a nearer body overlaps another, the edge falls a step into shadow (one step darker on its own ramp)
    for y in range(h):
        for x in range(w):
            cell = grid[y][x]
            if not cell:
                continue
            for nx, ny in ((x - 1, y), (x, y - 1)):
                other = grid[ny][nx] if 0 <= nx < w and 0 <= ny < h else None
                if other and other[1] != cell[1] and depth[ny][nx] - depth[y][x] > 0.18:
                    ramp = cell[2].mat
                    if out[y][x] in ramp:
                        out[y][x] = ramp[min(3, ramp.index(out[y][x]) + 1)]
    final = [row[:] for row in out]
    for y in range(h):
        for x in range(w):
            if grid[y][x] is None and any(0 <= x + dx < w and 0 <= y + dy < h and grid[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                final[y][x] = 'O'
    return [''.join(r) for r in final], (w, h), (ax, ay)


def preview(path, scale=4):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}
    root = Path(__file__).resolve().parent.parent
    ground = Image.open(root / 'sprites' / 'assets' / 'ground.png').convert('RGBA')
    drawn = [(f'{i + 1} {name}', render(builder, width, tall)) for i, (name, _, builder, width, tall, _) in enumerate(SHAPES)]
    existing = [('bush', ground.crop((0, 96, 32, 128)), 24, 32), ('pine', ground.crop((32, 96, 64, 160)), 52, 64)]
    slot = lambda w: max(w, 62)
    total_w = sum(slot(32) for _ in existing) + sum(slot(d[1][1][0]) for d in drawn) + 6
    height = max(d[1][1][1] for d in drawn) + 22
    sheet = Image.new('RGBA', (total_w, height), (48, 70, 84, 255))
    draw = ImageDraw.Draw(sheet)
    x0 = 6
    for label, img, bottom, h in existing:           # the sheet's own, standing as a prop does: its lowest row 4 below the middle of the tile's top face
        cy = height - 16
        ox = x0 + (slot(32) - 32) // 2
        draw.polygon([(ox, cy), (ox + 16, cy - 8), (ox + 32, cy), (ox + 16, cy + 8)], fill=(74, 150, 70, 255))
        sheet.alpha_composite(img, (ox, cy + 4 - bottom - 1))
        draw.text((x0, 2), label, fill=(235, 238, 245, 255))
        x0 += slot(32)
    for label, (rows, (w, h), (ax, ay)) in drawn:
        cy = height - 16
        ox = x0 + (slot(w) - w) // 2
        draw.polygon([(ox + ax - 16, cy), (ox + ax, cy - 8), (ox + ax + 16, cy), (ox + ax, cy + 8)], fill=(74, 150, 70, 255))
        oy = cy - ay
        for y, line in enumerate(rows):
            for x, ch in enumerate(line):
                if ch != '.':
                    sheet.putpixel((ox + x, oy + y), rgb[ch] + (255,))
        draw.text((x0, 2), label, fill=(235, 238, 245, 255))
        x0 += slot(w)
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.save(path)


# --- the assets ----------------------------------------------------------------------------------
def build_assets():
    """One still asset per tree (`tree-NAME`, `bush-NAME`), each in its own cell with the anchor at the middle of its footprint on the ground."""
    assets = []
    for name, label, builder, width, tall, kind in SHAPES:
        rows, (w, h), anchor = render(builder, width, tall)
        extra = {'tree': {'footprint': [1, 1], 'blocks': True, 'height': tall}}
        assets.append(family(CATEGORY, w, h, anchor, folder=FOLDER)(f'{kind}-{name}', label, 'still', [rows], **extra))
    return assets


def write_package(folder):
    """Beside the sheets: trees.json, each tree's file, cell, anchor and height in numbers (README.md says how to place them)."""
    body = {}
    for name, label, builder, width, tall, kind in SHAPES:
        rows, (w, h), (ax, ay) = render(builder, width, tall)
        body[f'{kind}-{name}'] = {'label': label, 'file': f'{kind}-{name}.png', 'cell': [w, h], 'anchor': {'x': ax, 'y': ay}, 'footprint': [1, 1], 'blocks': True, 'height': tall}
    write_json(folder, 'trees.json', 'The tree sheets in this folder. See README.md beside this file for the whole story.', {'trees': body})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write every tree, enlarged, here')
    parser.add_argument('--scale', type=int, default=4)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, args.scale)
        print(f'the trees, enlarged -> {args.preview}')


if __name__ == '__main__':
    main()
