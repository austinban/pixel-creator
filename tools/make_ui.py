#!/usr/bin/env python3
"""Small UI elements. First: the movement-point dot, filled and empty.

A player's movement points are shown as a row of dots: a filled one for each point left, an empty one for each
spent. Seven pixels across, with the palette's outline round it like the other assets. The filled dot is the
move overlay's blue (sky, with a cyan highlight top left and blue in the shade bottom right) so it reads as "movement";
the empty one is the same shape as a dim socket, darker on the lit side and lighter on the shaded side so it looks pressed in.

    python3 tools/make_ui.py --preview previews/movement-dots.png     rows of them, some filled and some empty
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DOT = 7
FILLED = [
    '..OOO..',
    '.OooOO.',
    'OonnnmO',
    'OnnnnmO',
    'OnnnmmO',
    '.OmmmO.',
    '..OOO..',
]
EMPTY = [
    '..OOO..',
    '.OwwkO.',
    'OwkkkkO',
    'OwkkkkO',
    'OkkkklO',
    '.OkllO.',
    '..OOO..',
]
MIDDLE = (3, 3)


# Colourways: which palette role stands in for each letter of the shapes above. Blue is the movement dot;
# red is its twin in the palette's coral family (there is no pure red), with a plum socket for the empty one.
BLUE = {}
RED = {'o': 'c', 'n': 'e', 'm': 'f', 'w': 'w', 'k': 'g', 'l': 'f'}
YELLOW = {'o': 't', 'n': 'd', 'm': 'b', 'w': 'w', 'k': 'g', 'l': 'a'}       # spirit: cream highlight, yellow, amber in the shade
COLOURWAYS = [('ui-movement-dot', 'Movement point dot (filled and empty)', BLUE),
              ('ui-dot-red', 'Dot, red (filled and empty)', RED),
              ('ui-dot-yellow', 'Spirit point dot, yellow (filled and empty)', YELLOW)]


def render_pixels(kind, colours=BLUE):
    shape = FILLED if kind == 'filled' else EMPTY
    return [''.join(colours.get(c, c) for c in line) for line in shape]


# --- the burst: a point being spent ----------------------------------------------------------
BURST = 13                      # the cell is wider than the dot, so there is room for the bits to fly
BURST_MIDDLE = (6, 6)
BURST_FRAMES = 7


def disc(grid, cx, cy, r, tones=('o', 'n', 'm')):
    """A round, outlined, shaded dot of radius r centred on (cx, cy): the same look as the 7 x 7 one, any size."""
    for y in range(BURST):
        for x in range(BURST):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > r + 0.3:
                continue
            if d > r - 0.75:
                grid[y][x] = 'O'
            else:
                t = ((x - cx) + (y - cy)) / (2 * max(r, 1))
                grid[y][x] = tones[0] if t < -0.4 else tones[2] if t > 0.3 else tones[1]


def stamp(grid, shape, cx, cy):
    """Lay a small shape (like the 7 x 7 dot) on the grid with its middle at (cx, cy)."""
    h, w = len(shape), len(shape[0])
    for y, line in enumerate(shape):
        for x, c in enumerate(line):
            if c != '.':
                grid[cy - h // 2 + y][cx - w // 2 + x] = c


def bits(grid, radius, letters):
    """Eight bits flying out from the middle: four along the axes and four on the diagonals."""
    cx, cy = BURST_MIDDLE
    for i, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))):
        k = radius * (0.72 if dx and dy else 1.0)
        x, y = round(cx + dx * k), round(cy + dy * k)
        if 0 <= x < BURST and 0 <= y < BURST:
            grid[y][x] = letters[i % len(letters)]


def render_burst(frame, colours=BLUE):
    """Full to empty: it swells, bursts into bits that fly out and fade, and an empty socket is left behind."""
    grid = [['.'] * BURST for _ in range(BURST)]
    cx, cy = BURST_MIDDLE
    if frame == 0:
        stamp(grid, FILLED, cx, cy)                           # whole
    elif frame == 1:
        disc(grid, cx, cy, 4.2)                               # it swells
    elif frame == 2:
        for y in range(BURST):                                # the flash: a bright ring, and the core flung apart
            for x in range(BURST):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if 4.2 <= d < 5.4:
                    grid[y][x] = 't'
        disc(grid, cx, cy, 2.2)
        bits(grid, 4.0, 'ot')
    elif frame == 3:
        bits(grid, 4.8, 'on')
        stamp(grid, EMPTY, cx, cy)                            # the socket shows through where it was
        bits(grid, 3.2, 'tn')
    elif frame == 4:
        bits(grid, 5.6, 'nm')
        stamp(grid, EMPTY, cx, cy)
    elif frame == 5:
        bits(grid, 6.0, 'm')
        stamp(grid, EMPTY, cx, cy)
    else:
        stamp(grid, EMPTY, cx, cy)                            # spent
    return [''.join(colours.get(c, c) for c in row) for row in grid]


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--burst', type=Path, help='write the burst animation here, one row per colour')
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    scale = 14
    row = ['filled'] * 3 + ['empty'] * 2
    sheet = Image.new('RGBA', ((len(row) * 9 + 1) * scale, (len(COLOURWAYS) * 10 + 1) * scale), (36, 38, 56, 255))
    for r, (_, _, colours) in enumerate(COLOURWAYS):
        for i, kind in enumerate(row):
            for y, line in enumerate(render_pixels(kind, colours)):
                for x, c in enumerate(line):
                    if c != '.':
                        for dy in range(scale):
                            for dx in range(scale):
                                sheet.putpixel(((1 + i * 9 + x + 1) * scale + dx, (2 + r * 10 + y) * scale + dy), rgb[c] + (255,))
    if args.preview:
        sheet.save(args.preview)
        print('wrote', args.preview)
    if args.burst:
        scale = 10
        out = Image.new('RGBA', (BURST_FRAMES * (BURST + 1) * scale, len(COLOURWAYS) * (BURST + 1) * scale), (36, 38, 56, 255))
        for r, (_, _, colours) in enumerate(COLOURWAYS):
            for f in range(BURST_FRAMES):
                for y, line in enumerate(render_burst(f, colours)):
                    for x, c in enumerate(line):
                        if c != '.':
                            for dy in range(scale):
                                for dx in range(scale):
                                    out.putpixel((((f * (BURST + 1)) + x) * scale + dx, ((r * (BURST + 1)) + y) * scale + dy), rgb[c] + (255,))
        out.save(args.burst)
        print('wrote', args.burst)


if __name__ == '__main__':
    main()
