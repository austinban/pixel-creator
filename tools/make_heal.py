#!/usr/bin/env python3
"""A healing spell on one character: pink rose petals appear above them and drift down over them, eight frames, and are gone by the last one.

The cell is 32 wide and 48 tall, the same as the vine spell's, with the character standing so their feet are at the anchor
(16, 41), so the petals start above the head and fall past the whole figure to the ground. Petals tumble as they fall, in coral
and salmon with an orchid shade and a plum edge, with a few cream sparkles, and nothing touches the ground. All
palette roles.

    python3 tools/make_heal.py --preview previews/heal.png      the eight frames, over a character
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CELL_W, CELL_H = 32, 48
ANCHOR = (16, 41)                 # the middle of the character's feet, on the ground
FRAMES = 8
LIGHT, MID, SHADE, EDGE, SPARK = 'c', 'e', 'f', 'g', 't'      # salmon, coral, orchid, plum, cream

# The petal shapes it tumbles through, in turn: each row is a row of pixels.
PETALS = [
    ['.cc.', 'ceef', '.eff', '..f.'],
    ['.c.', 'cee', 'eef', '.f.'],
    ['.ccc.', 'ceeef', '.fff.'],
    ['.cc.', 'feec', 'ffe.', '.f..'],
]
# Each petal: where it starts across the cell, the frame it appears on, how it sways, and where it is in its tumble.
DRIFT = [
    (6, 0, 0.0, 0), (13, 0, 1.7, 2), (20, 0, 3.2, 1), (26, 0, 4.6, 3), (10, 0, 5.8, 1),
    (3, 1, 2.1, 3), (16, 1, 0.6, 0), (23, 1, 3.8, 2), (9, 1, 5.1, 1),
    (12, 2, 1.1, 2), (25, 2, 2.8, 0), (5, 2, 4.2, 3),
    (18, 3, 0.4, 1), (8, 3, 3.3, 2),
    (15, 4, 2.4, 2),                              # the last one, still drifting on the final frame
]
START = 2             # the row a petal appears on
LIFE = 5              # frames a petal is in the air: it has left the bottom by then, so by the last frame almost none are left
SPARKS = [(10, 18), (22, 24), (14, 31), (24, 12), (7, 27)]


def draw(grid, x, y, shape):
    for dy, row in enumerate(shape):
        for dx, ch in enumerate(row):
            if ch != '.' and 0 <= x + dx < CELL_W and 0 <= y + dy < CELL_H:
                grid[y + dy][x + dx] = ch


def render_pixels(frame):
    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    # The petals: each appears at the top on its frame, then falls, swaying, tumbling as it goes, and is gone at the ground.
    for i, (x0, spawn, phase, tumble) in enumerate(DRIFT):
        age = frame - spawn
        if age < 0:
            continue
        y = START + 3.0 * age + 1.6 * age * age          # drifts at first, then falls faster, like a petal letting go
        if age >= LIFE or y > ANCHOR[1] - 7:             # gone by the knees: nothing reaches the floor
            continue
        x = x0 + 2.2 * math.sin(phase + age * 1.15)
        draw(grid, round(x), round(y), PETALS[(tumble + age) % len(PETALS)])
    # Sparkles: a few cream glints beside the petals.
    for k, (sx, sy) in enumerate(SPARKS):
        if frame < FRAMES - 1 and (frame + k) % 3 == 0:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if (frame + k) % 6 == 0 else ((0, 0),):
                x, y = sx + dx, sy + dy
                if 0 <= x < CELL_W and 0 <= y < CELL_H and grid[y][x] == '.':
                    grid[y][x] = SPARK
    return [''.join(row) for row in grid]


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write the eight frames over a character here')
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    root = Path(__file__).resolve().parent.parent
    figure = Image.open(root / 'sprites' / 'blossom' / 'blossom-chargingSE.png').convert('RGBA')
    scale = 6
    out = Image.new('RGBA', (FRAMES * (CELL_W + 2) * scale, (CELL_H + 2) * scale), (36, 38, 56, 255))
    for f in range(FRAMES):
        cell = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
        cell.alpha_composite(figure, (0, ANCHOR[1] - 27))            # the character's ground row sits on the anchor
        over = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
        for y, line in enumerate(render_pixels(f)):
            for x, c in enumerate(line):
                if c != '.':
                    over.putpixel((x, y), rgb[c] + (255,))
        cell.alpha_composite(over)
        out.alpha_composite(cell.resize((CELL_W * scale, CELL_H * scale), Image.NEAREST), ((f * (CELL_W + 2) + 1) * scale, scale))
    if args.preview:
        out.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
