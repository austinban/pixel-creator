#!/usr/bin/env python3
"""Tile overlays: a flat tone laid over a ground tile's top face.

A tile's top face is a diamond 32 wide and 16 tall (see terrain.js). An overlay is that diamond, covering all of
it in one even tone, and painted see-through (the asset's `opacity`, applied when it is drawn), so it tones the
whole tile, grass and all, without covering it. The edge is two-tone like the facing marker's (lit along the top,
shaded along the bottom). The see-through ones are a single still frame for now. The solid ones, for hovering, are
opaque and animate, eight frames looping.

The first is the blue one, for choosing where to move.

    python3 tools/make_overlay.py --preview previews/overlay-blue.png     the overlays, over a grass tile
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CELL_W, CELL_H = 32, 16
MIDDLE = (16, 8)                   # the middle of the diamond, on the ground
FRAMES = 8                          # eight frames, so each step is small and the loop is slow

# base tone, and the edge's lit and shaded tones: palette roles. The overlay is
# painted see-through (OPACITY), so it tones the whole tile, grass and all, and the tones sit close together.
OPACITY = 0.4
BLUE = dict(base='n', lit='o', shade='m')
YELLOW = dict(base='d', lit='t', shade='b')
RED = dict(base='e', lit='c', shade='f')
# id, label, colours. Blue is for choosing where to move.
COLOURWAYS = [('overlay-move', 'Tile overlay - blue (move)', BLUE),
              ('overlay-yellow', 'Tile overlay - yellow', YELLOW),
              ('overlay-red', 'Tile overlay - red', RED)]


def inside(x, y, shrink=0.0):
    """Is a pixel inside the diamond (the top face of a tile)? `shrink` pulls the edge in, as a fraction."""
    dx, dy = abs(x + 0.5 - 16), abs(y + 0.5 - 8)
    return dx / 16 + dy / 8 <= 1.0 - shrink + 1e-9


def edge_pixels():
    """The diamond's outline, in order round it starting from the top and going clockwise."""
    out = []
    for y in range(CELL_H):
        for x in range(CELL_W):
            if inside(x, y) and any(not inside(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.append((x, y))
    out.sort(key=lambda p: math.atan2(p[0] + 0.5 - 16, -(p[1] + 0.5 - 8) * 2))
    return out


def render_pixels(colours=BLUE):
    """The see-through wash: one even tone over the whole top face, and a soft two-tone edge. A single frame."""
    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    for y in range(CELL_H):
        for x in range(CELL_W):
            if inside(x, y):
                grid[y][x] = colours['base']
    for x, y in edge_pixels():
        grid[y][x] = colours['lit'] if y < 8 else colours['shade']
    return [''.join(row) for row in grid]


# The solid ones, for hovering: full coverage, so the tile under the pointer is clearly picked out. Same
# three colours as the dithered ones: the veil's colour fills it, the lit edge's colour is the bright middle.
SOLID_BLUE = dict(fill='n', glow='p', lit='q', shade='m')
SOLID_YELLOW = dict(fill='b', glow='a', lit='d', shade='a')
SOLID_RED = dict(fill='e', glow='f', lit='c', shade='f')
SOLID_COLOURWAYS = [('overlay-move-solid', 'Tile overlay - solid blue (hover)', SOLID_BLUE),
                    ('overlay-yellow-solid', 'Tile overlay - solid yellow', SOLID_YELLOW),
                    ('overlay-red-solid', 'Tile overlay - solid red', SOLID_RED)]
BREATH = (0.30, 0.37, 0.47, 0.55, 0.60, 0.55, 0.47, 0.37)         # how big the bright middle is, frame by frame: it breathes in and out


def render_solid(frame, colours=SOLID_BLUE):
    """Every pixel of the diamond painted: a pale fill, a bright middle that breathes, and a two-tone edge."""
    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    for y in range(CELL_H):
        for x in range(CELL_W):
            if inside(x, y):
                dx, dy = abs(x + 0.5 - 16), abs(y + 0.5 - 8)
                grid[y][x] = colours['glow'] if dx / 16 + dy / 8 <= BREATH[frame] else colours['fill']
    for x, y in edge_pixels():
        grid[y][x] = colours['lit'] if y < 8 else colours['shade']
    return [''.join(row) for row in grid]


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write the four frames over a grass tile here')
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    scale = 5
    rows = len(COLOURWAYS) + len(SOLID_COLOURWAYS)
    sheet = Image.new('RGBA', (FRAMES * 34 * scale, rows * 34 * scale), (36, 38, 56, 255))
    for row, (id_, _, colours) in enumerate(COLOURWAYS + SOLID_COLOURWAYS):
        for f in range(FRAMES):
            lines = render_solid(f, colours) if id_.endswith('-solid') else render_pixels(colours)
            over = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            opacity = 255 if id_.endswith('-solid') else round(255 * OPACITY)
            for y, line in enumerate(lines):
                for x, c in enumerate(line):
                    if c != '.':
                        over.putpixel((x, y), rgb[c] + (opacity,))
            cell = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            cell.alpha_composite(ground)
            cell.alpha_composite(over)
            sheet.alpha_composite(cell.resize((32 * scale, 32 * scale), Image.NEAREST), ((f * 34 + 1) * scale, (row * 34 + 1) * scale))
    if args.preview:
        sheet.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
