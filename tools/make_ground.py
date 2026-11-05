#!/usr/bin/env python3
"""Slice the ground tileset into assets.

sprites/assets/ground.png is a sheet of 32 x 32 cells, one tile or prop per cell. A few
props are taller than a cell and are listed in TALL so they come out whole. Every pixel
is mapped to the shared master palette, so the tiles recolour like everything else:
an exact match where there is one, otherwise the nearest colour. Faint, see-through
shadow sprites are skipped, because assets are painted in solid colour only.

Used by make_assets.py; run that to rebuild assets/data.js.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

SHEET = Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png'
CELL = 32
SOLID = 128  # alpha at or above this counts as painted

# Props taller than one cell: (column, first row, rows, name). The cells below the first
# are folded in, not listed on their own.
TALL = [
    (1, 3, 2, 'Pine tree'),
    (3, 6, 2, 'Fence post tall'),
    (3, 8, 2, 'Fence post tall'),
]

# Props by cell, named by hand. Everything else is a tile, named from what it is made of.
NAMED = {
    (0, 3): ('Nature', 'Bush'),
    (0, 4): ('Nature', 'Rock'), (0, 5): ('Nature', 'Rock'),
    (1, 5): ('Nature', 'Tree stump'),
    (0, 6): ('Nature', 'Log'), (1, 6): ('Nature', 'Log'), (0, 7): ('Nature', 'Log'),
    (0, 8): ('Nature', 'Log'), (1, 8): ('Nature', 'Log'), (1, 9): ('Nature', 'Log'),
    (2, 6): ('Fences', 'Fence end left'), (4, 6): ('Fences', 'Fence end right'),
    (2, 7): ('Fences', 'Fence end left'), (4, 7): ('Fences', 'Fence end right'),
    (2, 8): ('Nature', 'Red flowers'), (4, 8): ('Nature', 'White flowers'),
    (0, 1): ('Stairs', 'Stone stairs'), (1, 1): ('Stairs', 'Stone stairs'),
}

# Where water, crates and plain dirt sit on the sheet, by cell ranges (c0, c1, r0, r1).
WATER = [(0, 7, 2, 2), (2, 7, 3, 4)]
CRATES = [(2, 7, 5, 8)]
DIRT_ONLY = [(8, 15, 3, 4)]


def inside(cell, ranges):
    c, r = cell
    return any(c0 <= c <= c1 and r0 <= r <= r1 for c0, c1, r0, r1 in ranges)


def classify(cell, counts):
    """A category for a tile: by place for water and crates, otherwise by what tops it."""
    if inside(cell, WATER):
        return 'Water'
    if inside(cell, CRATES):
        return 'Crates'
    total = sum(counts.values()) or 1
    if counts['green'] / total > 0.06:
        return 'Grass'
    if inside(cell, DIRT_ONLY):
        return 'Dirt'
    if (counts['teal'] + counts['violet'] + counts['neutral']) / total > 0.18:
        return 'Stone'
    return 'Dirt'


def build_ground_assets():
    if not SHEET.exists():
        return []
    from PIL import Image
    im = Image.open(SHEET).convert('RGBA')
    px = im.load()
    cols, rows = im.width // CELL, im.height // CELL

    group_of = {c: g for c, _, _, g, _ in ep.ROLES}
    palette = {rgb: (c, group_of[c]) for rgb, c in ep.COLOUR_TO_ROLE.items()}
    nearest_cache = {}

    def role(rgb):
        if rgb in palette:
            return palette[rgb]
        if rgb not in nearest_cache:
            nearest_cache[rgb] = palette[min(palette, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, rgb)))]
        return nearest_cache[rgb]

    def painted(x, y):
        return px[x, y][3] >= SOLID

    def lines_of(x0, y0, w, h):
        out, groups = [], Counter()
        for y in range(y0, y0 + h):
            row = ''
            for x in range(x0, x0 + w):
                if painted(x, y):
                    ch, group = role(px[x, y][:3])
                    row += ch
                    groups[group] += 1
                else:
                    row += '.'
            out.append(row)
        return out, groups

    taken = set()
    items = []   # (reading order, w, h, lines, groups, cell, tall name)
    for c, r, n, name in TALL:
        for k in range(n):
            taken.add((c, r + k))
        lines, groups = lines_of(c * CELL, r * CELL, CELL, n * CELL)
        items.append(((r, c), CELL, n * CELL, lines, groups, (c, r), name))
    for r in range(rows):
        for c in range(cols):
            if (c, r) in taken:
                continue
            lines, groups = lines_of(c * CELL, r * CELL, CELL, CELL)
            if not groups:
                continue   # empty, or only a see-through shadow
            items.append(((r, c), CELL, CELL, lines, groups, (c, r), None))
    items.sort(key=lambda i: i[0])

    assets, seen = [], Counter()
    for _, w, h, lines, groups, cell, tall in items:
        if tall:
            category, label = 'Nature' if 'tree' in tall.lower() else 'Fences', tall
        elif cell in NAMED:
            category, label = NAMED[cell]
        else:
            category = classify(cell, groups)
            label = category
        seen[label] += 1
        # Same-named pieces are told apart by a number, in reading order.
        assets.append({'_label': label, 'category': category, 'w': w, 'h': h, 'frames': [lines], 'cell': cell})
    totals = Counter(a['_label'] for a in assets)
    counter = Counter()
    out = []
    for a in assets:
        counter[a['_label']] += 1
        label = f"{a['_label']} {counter[a['_label']]}" if totals[a['_label']] > 1 else a['_label']
        out.append({
            'id': f"ground-{a['cell'][0]}-{a['cell'][1]}", 'label': label, 'category': a['category'],
            'kind': 'still', 'place': 'none', 'names': [label],
            'w': a['w'], 'h': a['h'], 'cols': 1, 'rows': 1, 'fps': 0,
            'anchor': {'x': a['w'] // 2, 'y': a['h']},
            'frames': a['frames'],
        })
    return out


if __name__ == '__main__':
    found = build_ground_assets()
    print(f'{len(found)} ground assets')
    print(Counter(a['category'] for a in found))
