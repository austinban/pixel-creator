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


# --- the shaped overlays: one 32 x 32 cell per ground tile, lined up with the tile -----------------------------------------
# Ground tiles come in a few shapes (flat tops at two heights, ramps, stepped ramps, half blocks), and an overlay has to
# follow the walkable surface of the tile it covers. These are cut to the same 32 x 32 cell as the tiles, so an overlay is
# drawn at the same place as the tile it lies on, whatever the tile's height. The angled shapes are read from the ground sheet
# (tools/extract_overlay_shapes.py); the grass, dirt and stone tiles with the same silhouette share a shape.
SHAPES_PATH = Path(__file__).resolve().parent / 'data' / 'overlay_shapes.json'


def diamond_mask(top):
    """The flat top face as a 32 x 32 mask, its upper corner `top` rows down from the top of the cell."""
    return [[abs(x + 0.5 - 16) / 16 + abs(y - top + 0.5 - 8) / 8 <= 1.0 + 1e-9 for x in range(32)] for y in range(32)]


def shapes():
    """All the overlay shapes: (name, mask) pairs. The two flat ones first, then the angled ones, by grass tile number."""
    import json
    out = [('Flat (a full block)', diamond_mask(0)), ('Flat, low (8 rows down)', diamond_mask(8))]
    for entry in json.loads(SHAPES_PATH.read_text()):
        out.append((entry['name'], [[ch == '#' for ch in row] for row in entry['rows']]))
    return out


def _edge(mask):
    """Each outline pixel of a mask, and whether it is lit (a top edge) or shaded (a bottom edge)."""
    h, w = len(mask), len(mask[0])
    on = lambda x, y: 0 <= x < w and 0 <= y < h and mask[y][x]
    out = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            up, down, left, right = (not on(x, y - 1), not on(x, y + 1), not on(x - 1, y), not on(x + 1, y))
            if up or down or left or right:
                out.append((x, y, up or (left and not down)))
    return out


def _depth(mask):
    """How far each pixel is from the edge, in steps (a flood in from the outline)."""
    h, w = len(mask), len(mask[0])
    depth = [[None] * w for _ in range(h)]
    frontier = [(x, y) for x, y, _ in _edge(mask)]
    for x, y in frontier:
        depth[y][x] = 0
    while frontier:
        nxt = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = x + dx, y + dy
                if 0 <= a < w and 0 <= b < h and mask[b][a] and depth[b][a] is None:
                    depth[b][a] = depth[y][x] + 1
                    nxt.append((a, b))
        frontier = nxt
    return depth


def render_shape(mask, colours=BLUE):
    """The see-through wash cut to a shape: one even tone and a soft two-tone edge."""
    grid = [['.'] * len(mask[0]) for _ in mask]
    for y in range(len(mask)):
        for x in range(len(mask[0])):
            if mask[y][x]:
                grid[y][x] = colours['base']
    for x, y, lit in _edge(mask):
        grid[y][x] = colours['lit'] if lit else colours['shade']
    return [''.join(row) for row in grid]


def render_shape_solid(mask, colours=SOLID_BLUE, glow=3, depth=None):
    """The solid hover version cut to a shape: a fill, a brighter middle (every pixel at least `glow` steps in), and a two-tone edge."""
    grid = [['.'] * len(mask[0]) for _ in mask]
    depth = depth or _depth(mask)
    for y in range(len(mask)):
        for x in range(len(mask[0])):
            if mask[y][x]:
                grid[y][x] = colours['glow'] if depth[y][x] >= glow else colours['fill']
    for x, y, lit in _edge(mask):
        grid[y][x] = colours['lit'] if lit else colours['shade']
    return [''.join(row) for row in grid]


def render_shape_breath(mask, frame, colours=SOLID_BLUE):
    """One frame of the solid overlay breathing: the bright middle swells and shrinks, as a share of how deep the shape is."""
    depth = _depth(mask)
    deepest = max(v for row in depth for v in row if v is not None)
    glow = max(1, round(deepest * (1 - BREATH[frame])))
    return render_shape_solid(mask, colours, glow, depth)


def bridge_shapes():
    """The four bridge decks as masks in the bridge's own cell (32 x 40): flat NE-SW, flat NW-SE, slope down NE, slope down SE."""
    import make_bridge
    return [(name, make_bridge.deck_mask(axis, kind)) for _, name, axis, kind in make_bridge.SPRITES]


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write the four frames over a grass tile here')
    parser.add_argument('--shapes', type=Path, help='write the shaped overlays, over the ground tiles they fit, here')
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
    if args.shapes:
        sheet_full = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA')
        tiles = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
        washes = (BLUE, YELLOW, RED)
        solids = (SOLID_BLUE, SOLID_YELLOW, SOLID_RED)
        scale = 4
        count = len(tiles)
        out = Image.new('RGBA', (count * 34 * scale, 6 * 34 * scale), (36, 38, 56, 255))
        for i, ((name, mask), (c, r)) in enumerate(zip(shapes(), tiles)):
            tile = sheet_full.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
            for k in range(6):
                lines = render_shape(mask, washes[k]) if k < 3 else render_shape_solid(mask, solids[k - 3])
                opacity = round(255 * OPACITY) if k < 3 else 255
                over = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
                for y, line in enumerate(lines):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            over.putpixel((x, y), rgb[ch] + (opacity,))
                cell = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
                cell.alpha_composite(tile)
                cell.alpha_composite(over)
                out.alpha_composite(cell.resize((32 * scale, 32 * scale), Image.NEAREST), ((i * 34 + 1) * scale, (k * 34 + 1) * scale))
        out.save(args.shapes)
        print('wrote', args.shapes)

if __name__ == '__main__':
    main()
