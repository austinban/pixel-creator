#!/usr/bin/env python3
"""A blood pool: a decal that lies on a ground tile, under a character that has died on it.

It is drawn on a tile's top face, the same 32 x 16 diamond the tile overlays use (see make_overlay.py), anchored at its middle (16, 8), so it goes where the tile is and the dead pose is drawn over it.
It is flat and irregular: a lumpy pool a little wider than a lying body, with a lobe or two running out, and a few separate drops. It stays inside the diamond, so it never spills off the tile.
Six pictures of it, so a battlefield does not repeat itself. Dark rim, a deep red body and a wetter, brighter middle with a glint or two; palette roles only, and no outline (a stain has none).

    python3 tools/make_blood_pool.py --preview previews/blood-pool.png     the six, over a grass tile, alone and under a dead character
"""
import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family  # noqa: E402

CELL_W, CELL_H = 32, 16
MIDDLE = (16, 8)
VARIANTS = 6
RIM, BODY, WET, GLINT = 'u', 'h', 'i', 'j'      # purple, dark magenta, magenta, hot pink: the darkest reds the palette has, then a wet shine

CATEGORY = 'Decals'


def inside(x, y, shrink=0.0):
    return abs(x + 0.5 - 16) / 16 + abs(y + 0.5 - 8) / 8 <= 1.0 - shrink + 1e-9


def pool_pixels(seed):
    """One pool as a CELL_H x CELL_W grid of rows. Its shape is a ring of radii on the ground plane (a circle on the ground is an ellipse twice as wide as tall on the screen)."""
    rng = random.Random(f'blood-pool-{seed}')
    base = 4.4 + rng.uniform(0.0, 0.7)                                       # radius on the ground, in pixels (about 18-20 wide on the screen)
    harmonics = [(k, rng.uniform(0.07, 0.2) / (k ** 0.35), rng.uniform(0, math.tau)) for k in (2, 3, 4, 5, 7)]
    lobes = [(rng.uniform(0, math.tau), rng.uniform(0.35, 0.75), rng.uniform(0.35, 0.6)) for _ in range(rng.choice((1, 2, 2)))]   # (direction, how far it runs out, how wide)

    def radius(theta):
        r = 1.0 + sum(a * math.sin(k * theta + ph) for k, a, ph in harmonics)
        for direction, reach, width in lobes:
            d = math.atan2(math.sin(theta - direction), math.cos(theta - direction))
            r += reach * math.exp(-(d / width) ** 2)
        return base * r

    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    depth = [[0.0] * CELL_W for _ in range(CELL_H)]
    for y in range(CELL_H):
        for x in range(CELL_W):
            if not inside(x, y, 0.1):
                continue
            gx, gy = (x + 0.5 - MIDDLE[0]) / 2.0, (y + 0.5 - MIDDLE[1])      # to the ground plane
            rho = math.hypot(gx, gy)
            edge = radius(math.atan2(gy, gx)) + rng.uniform(-0.35, 0.35)      # a ragged edge
            if rho <= edge:
                depth[y][x] = 1 - rho / max(edge, 0.01)
                grid[y][x] = BODY
    for y in range(CELL_H):                                                    # shade by how far in from the edge
        for x in range(CELL_W):
            if grid[y][x] == '.':
                continue
            d = depth[y][x]
            grid[y][x] = RIM if d < 0.17 else WET if d > 0.5 else BODY
    # a bit of the rim lost to the open air along the lit side, so the edge is not a ring
    # separate drops: a pixel or two near the edge, inside the tile
    for _ in range(rng.choice((2, 3, 4))):
        theta = rng.uniform(0, math.tau)
        rr = radius(theta) + rng.uniform(1.6, 3.2)
        x, y = int(MIDDLE[0] + 2 * rr * math.cos(theta)), int(MIDDLE[1] + rr * math.sin(theta))
        if inside(x, y, 0.12) and grid[y][x] == '.' and all(grid[y + dy][x + dx] == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < CELL_W and 0 <= y + dy < CELL_H):
            grid[y][x] = BODY
            if rng.random() < 0.4 and inside(x + 1, y, 0.12) and grid[y][x + 1] == '.':
                grid[y][x + 1] = RIM
    # a glint on the wet middle, towards the light (the upper left)
    wet = [(x, y) for y in range(CELL_H) for x in range(CELL_W) if grid[y][x] == WET]
    wet.sort(key=lambda p: p[0] + 2 * p[1])
    for x, y in wet[:1] + (wet[len(wet) // 5: len(wet) // 5 + 1] if len(wet) > 12 else []):
        grid[y][x] = GLINT
    return [''.join(row) for row in grid]


def build_assets():
    """One `blood-pool` asset with six variants, each a still on the 32 x 16 top face, anchored at its middle: it goes where a ground tile is."""
    make = family(CATEGORY, CELL_W, CELL_H, MIDDLE, place='ground')
    return [make('blood-pool', 'Blood pool', 'variants', [pool_pixels(i) for i in range(VARIANTS)], names=[f'Pool {i + 1}' for i in range(VARIANTS)])]


def preview(path, scale=6):
    from PIL import Image
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    root = Path(__file__).resolve().parent.parent
    ground = Image.open(root / 'sprites' / 'assets' / 'ground.png').convert('RGBA')
    grass = ground.crop((0, 0, 32, 32))
    dead = root / 'sprites' / 'slim' / 'slim-deadSE.png'
    sprite = Image.open(dead).convert('RGBA') if dead.exists() else None
    cols = VARIANTS
    cell_w, cell_h = 40, 44
    sheet = Image.new('RGBA', (cols * cell_w, cell_h * 2), (36, 38, 56, 255))
    for i in range(VARIANTS):
        pool = Image.new('RGBA', (32, 16), (0, 0, 0, 0))
        for y, row in enumerate(pool_pixels(i)):
            for x, c in enumerate(row):
                if c != '.':
                    pool.putpixel((x, y), rgb[c] + (255,))
        for row_i, with_dead in enumerate((False, True)):
            ox, oy = i * cell_w + 4, row_i * cell_h + 8
            sheet.alpha_composite(grass, (ox, oy))
            sheet.alpha_composite(pool, (ox, oy + 8 - 8))                    # the diamond is the top 16 rows of the tile, its middle at (16, 8) from the tile's top
            if with_dead and sprite:
                sheet.alpha_composite(sprite, (ox, oy + 8 - 26))              # a character's feet are on row 26 of its cell: the anchor is the tile's middle
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='the six pools over a grass tile, alone and under a dead character, enlarged')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the blood pools, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
