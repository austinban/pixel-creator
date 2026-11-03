#!/usr/bin/env python3
"""Work out the walkable top surface of each angled ground tile, so an overlay can be cut to fit it.

The ground tiles share a few shapes (grass, dirt and stone use the same silhouettes), so the shapes are read once, from the grass
row of sprites/assets/ground.png, where the colours make it clear: a flat top is lime, a slope is a mid green, and the dark green
fringe that drips down a cliff is not walkable. The result is kept as data (tools/data/overlay_shapes.json) so the overlays can be
rebuilt without the sheet.

    python3 tools/extract_overlay_shapes.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / 'sprites' / 'assets' / 'ground.png'
OUT = ROOT / 'tools' / 'data' / 'overlay_shapes.json'
TOP = {(0x55, 0xdc, 0x34), (0xa9, 0xe0, 0x30), (0x35, 0xcd, 0x62)}      # flat top, its highlight, slope
FRINGE = (0x00, 0xab, 0x56)

# The grass tiles of each angled shape: (column, row, grass number). The dirt and stone tiles with the same silhouette use the same shape.
ANGLED = [(2, 0, 3), (3, 0, 4), (4, 0, 5), (5, 0, 6), (6, 0, 7), (7, 0, 8),
          (2, 1, 15), (3, 1, 16), (4, 1, 17), (5, 1, 18), (6, 1, 19), (7, 1, 20)]


def surface(cell):
    px = cell.load()
    m = [[False] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            p = px[x, y]
            if p[3] >= 128 and p[:3] in TOP:
                m[y][x] = True
    for _ in range(2):                                   # texture inside the surface, in the fringe's dark green
        add = []
        for y in range(32):
            for x in range(32):
                p = px[x, y]
                if p[3] >= 128 and p[:3] == FRINGE and not m[y][x]:
                    near = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < 32 and 0 <= y + dy < 32 and m[y + dy][x + dx])
                    if near >= 3:
                        add.append((x, y))
        for x, y in add:
            m[y][x] = True
    return m


def smooth(m):
    """Smooth the ragged edge a little: a pixel stays on if most of the ones round it are."""
    out = [[False] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            n = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= x + dx < 32 and 0 <= y + dy < 32 and m[y + dy][x + dx])
            out[y][x] = n >= 6 or (m[y][x] and n >= 4)
    return out


def fill_holes(m):
    """Pixels of the surface that were painted another colour (a dark fleck in the grass) are still surface: fill what is enclosed."""
    outside = set()
    stack = [(x, y) for x in range(32) for y in (0, 31)] + [(x, y) for y in range(32) for x in (0, 31)]
    while stack:
        x, y = stack.pop()
        if (x, y) in outside or not (0 <= x < 32 and 0 <= y < 32) or m[y][x]:
            continue
        outside.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [[m[y][x] or (x, y) not in outside for x in range(32)] for y in range(32)]


def main():
    from PIL import Image
    sheet = Image.open(SHEET).convert('RGBA')
    shapes = []
    for c, r, number in ANGLED:
        m = fill_holes(smooth(surface(sheet.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32)))))
        shapes.append({'name': f'Grass {number}', 'tile': f'ground-{c}-{r}', 'rows': [''.join('#' if v else '.' for v in row) for row in m]})
    OUT.write_text(json.dumps(shapes, indent=1))
    print('wrote', OUT, len(shapes), 'shapes')


if __name__ == '__main__':
    main()
