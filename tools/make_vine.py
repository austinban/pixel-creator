#!/usr/bin/env python3
"""A spell effect: a vine shoots up out of the ground, swells, and slams straight back down.

Eight frames, built as a small 3D model the way the characters are (see creature.py): a stem made of
ellipsoids along a gently curling line, leaves that open as it swells, and clumps of earth thrown up.
It is painted in the shared colour roles, in the leafy greens of the bush and tree, so it recolours.

    python3 tools/make_vine.py --model previews/vine-3d.png     look at the 3D model first

Model space: the ground is y = 0, the vine grows up +y from the origin, and the units are about one
game pixel.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, mm, part, rx, ry, rz  # noqa: E402
from assetkit import sheet_layout  # noqa: E402

RAMPS = {
    'stem': ('z', 'A', 'B', 's'),       # lime, green, emerald, deep teal: the bush and tree's greens
    'leaf': ('z', 'A', 'B', 's'),
    'bud': ('t', 'z', 'A', 'B'),        # a paler tip, so the head catches the eye
    'earth': ('a', 'e', 'f', 'g'),      # orange, coral, orchid, plum: the dirt tiles' colours
}

# What each frame does: height of the vine, thickness at the base, how far the leaves are open, how
# far the tip curls, how much earth is in the air, and a squash (the slam flattens it).
#            height  base  leaves  curl  earth
FRAMES = [
    dict(name='shoot',  height=8.0,  base=1.6, leaves=0.0, curl=0.0, earth=0.5, crater=0.4),
    dict(name='rise',   height=17.0, base=1.9, leaves=0.1, curl=0.3, earth=0.4, crater=0.5),
    dict(name='grow',   height=26.0, base=2.1, leaves=0.25, curl=0.7, earth=0.28, crater=0.5),
    dict(name='reach',  height=34.0, base=2.3, leaves=0.4, curl=1.0, earth=0.2, crater=0.5),
    dict(name='swell',  height=36.0, base=4.2, leaves=1.0, curl=0.7, earth=0.1, crater=0.5),
    dict(name='hold',   height=36.0, base=4.2, leaves=1.0, curl=0.7, earth=0.1, crater=0.5),   # hangs a frame longer
    dict(name='slam',   height=13.0, base=5.4, leaves=0.8, curl=0.0, earth=0.7, crater=0.7, squash=True),
    dict(name='impact', height=3.0,  base=4.6, leaves=0.45, curl=0.0, earth=1.0, crater=1.0, squash=True),
]
SEGMENTS = 20


def stem(f):
    """Ellipsoids along the vine's curling line, thick at the foot and fine at the tip."""
    parts = []
    h, base = f['height'], f['base']
    pts = []
    for i in range(SEGMENTS + 1):
        t = i / SEGMENTS
        sway = math.sin(t * math.pi * 1.5) * 2.2 * min(1.0, h / 30)       # a lazy S
        hook = (t ** 3) * 5.0 * f['curl']                                  # the tip curls over at the top
        pts.append((sway + hook, t * h, math.sin(t * 5.0) * 1.1 * min(1.0, h / 30)))
    for i in range(SEGMENTS):
        a, b = pts[i], pts[i + 1]
        t = (i + 0.5) / SEGMENTS
        radius = base * (1.0 - 0.72 * t) + 0.35
        mid = tuple((a[k] + b[k]) / 2 for k in range(3))
        length = math.dist(a, b)
        direction = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        tilt = math.atan2(direction[0], direction[1])                       # lean in x
        twist = math.atan2(direction[2], direction[1])                      # lean in z
        R = mm(rz(-tilt), rx(twist))
        half = length * 3.2 + 0.3
        if i < 4:
            half = min(half, mid[1] + 0.3)               # the foot must not go below the ground
        if i >= SEGMENTS - 2:
            half = length * 1.3 + 0.3                    # and the tip stays blunt, under the bud
        parts.append(part(mid, (radius, half, radius), 'stem', 'stem', R))
    return parts, pts


def leaves(f, pts):
    """Pairs of paddle leaves, alternating round the stem, opening upward as the vine swells."""
    out = []
    amount = f['leaves']
    if amount <= 0:
        return out
    for i in range(4, SEGMENTS - 2, 4):
        t = i / SEGMENTS
        x, y, z = pts[i]
        size = (4.0 + 6.0 * (1 - abs(t - 0.45))) * amount
        side = 1 if (i // 4) % 2 == 0 else -1
        droop = 0.5 + 0.9 * (1 - amount) if f.get('squash') else 0.0
        angle = math.radians(35 + 25 * amount) if not f.get('squash') else math.radians(110)
        for k, turn in enumerate((0.0, math.pi)):
            heading = turn + side * 0.6 + i * 0.7
            reach = size * 0.9
            cx = x + math.cos(heading) * reach * math.sin(angle)
            cz = z + math.sin(heading) * reach * math.sin(angle)
            cy = y + reach * math.cos(angle) * 0.6 - droop
            R = rz(-math.cos(heading) * (math.pi / 2 - angle * 0.8))
            R = mm_(R, rx(math.sin(heading) * (math.pi / 2 - angle * 0.8)))
            out.append(part((cx, max(cy, 0.6), cz), (size * 0.62, size * 0.13 + 0.15, size * 0.30), 'leaf', f'leaf{i}{k}', R))
    return out


def mm_(a, b):
    return mm(a, b)


def bud(f, pts):
    """A pale bud at the very tip while the vine is reaching."""
    if f['curl'] <= 0 or f['height'] < 20:
        return []
    x, y, z = pts[-1]
    r = 1.4 + 0.8 * f['leaves']
    return [part((x, y + 0.8, z), (r, r * 1.3, r), 'bud', 'bud')]


def earth(f):
    """The ground bursting: a rim of earth round the foot, and clumps thrown up that fall as the frames go."""
    out = []
    amount, crater = f['earth'], f['crater']
    # the rim: low mounds round the base
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.4
        dist = (2.4 + 2.0 * crater) * (0.9 + 0.2 * ((k * 7) % 3) / 2)
        out.append(part((math.cos(a) * dist, 0.5 + 0.35 * crater, math.sin(a) * dist), (1.0 + 0.7 * crater, 0.6 + 0.5 * crater, 1.0 + 0.7 * crater), 'earth', f'rim{k}'))
    # clumps in the air
    clumps = 6
    for k in range(clumps):
        a = k * 2 * math.pi / clumps + 1.1
        out_dist = 3.0 + 7.0 * amount * (0.6 + 0.4 * ((k * 5) % 3) / 2)
        height = 2.0 + 9.0 * amount * (0.5 + 0.5 * ((k * 3) % 4) / 3)
        size = 0.7 + 0.6 * amount
        if amount < 0.25:
            continue
        out.append(part((math.cos(a) * out_dist, height, math.sin(a) * out_dist), (size, size, size), 'earth', f'clump{k}'))
    return out


def place(f):
    stem_parts, pts = stem(f)
    parts = stem_parts + leaves(f, pts) + bud(f, pts) + earth(f)
    if f.get('squash'):
        # the slam squashes the stem down; everything is already at its short height
        pass
    return parts, []


# --- the pixel sprites ----------------------------------------------------------
CELL_W, CELL_H = 32, 48
ORIGIN = (24, 41)                       # where the vine's foot lands, in a square 48 cell that is then cut to 32 wide
ANCHOR = (16, 41)                       # the same point in the cut cell: the middle of the foot, on the ground
EDGE_RAMP_DEEP = 3                      # the edge takes its neighbour's deepest tone on the lit side...
EDGE_SHADE = 'k'                        # ...and indigo on the side turned from the light, as under the bush


def render_pixels(f):
    """One frame as rows of colour-role characters, CELL_W x CELL_H, outlined in two tones."""
    import creature as cr
    parts, decals = place(f)
    old = cr.CELL
    cr.CELL = CELL_H                    # the renderer draws square cells; draw a tall one and cut it down
    try:
        rows = cr.render_frame(parts, decals, 'SE', ORIGIN, RAMPS, 1.0)
    finally:
        cr.CELL = old
    grid = [[('.' if ch == cr.OUTLINE else ch) for ch in row[8:8 + CELL_W]] for row in rows]
    deep = {}
    for ramp in RAMPS.values():                     # the first ramp to use a colour decides its edge
        for c in ramp:
            deep.setdefault(c, ramp[EDGE_RAMP_DEEP])
    painted = [(y, x) for y in range(CELL_H) for x in range(CELL_W) if grid[y][x] != '.']
    edge = {}
    for y, x in painted:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < CELL_H and 0 <= nx < CELL_W and grid[ny][nx] == '.':
                    edge.setdefault((ny, nx), []).append((dy, dx, grid[y][x]))
    for (ny, nx), near in edge.items():
        dy = sum(n[0] for n in near)
        dx = sum(n[1] for n in near)
        lit = dy < 0 or (dy == 0 and dx < 0)
        grid[ny][nx] = deep[near[0][2]] if lit else EDGE_SHADE
    return [''.join(row) for row in grid]


def render_sheet(size=330):
    from PIL import Image, ImageDraw
    import preview3d as pv
    bounds = [(0, 0, 0), (0, 38, 0), (12, 0, 12), (-12, 0, -12), (12, 0, -12), (-12, 0, 12), (0, 20, 0), (9, 14, 9), (-9, 14, -9)]
    sheet = Image.new('RGBA', (size * len(FRAMES), size + 20), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for i, f in enumerate(FRAMES):
        parts, decals = place(f)
        tile = pv.render_view(parts, decals, RAMPS, -45, size, fit_points=bounds)
        sheet.alpha_composite(tile, (i * size, 20))
        draw.text((i * size + 6, 4), f'{i + 1}  {f["name"]}', fill=(235, 238, 245, 255))
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, required=True, help='write the 3D preview of all the frames here')
    args = parser.parse_args()
    args.model.parent.mkdir(parents=True, exist_ok=True)
    render_sheet().save(args.model)
    print(f'3D preview of the vine -> {args.model}; no sprites were made')

def build_assets():
    # The vine spell: shoots up out of the ground, swells, hangs a frame, and slams back down.
    vine_frames = [render_pixels(f) for f in FRAMES]
    cols, rows = sheet_layout(len(vine_frames))
    vine_asset = {
        'id': 'vine', 'label': 'Vine spell', 'category': 'Animations', 'kind': 'animation', 'place': 'ground',
        'w': CELL_W, 'h': CELL_H, 'cols': cols, 'rows': rows, 'fps': 8,
        # The middle of the vine's foot, on the ground.
        'anchor': {'x': ANCHOR[0], 'y': ANCHOR[1]},
        'frames': vine_frames,
    }
    return [vine_asset]


if __name__ == '__main__':
    main()
