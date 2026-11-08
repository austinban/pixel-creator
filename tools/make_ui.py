#!/usr/bin/env python3
"""Small UI elements. First: the movement-point dot, filled and empty. Then the shell drawn behind a dot when a count has wrapped past ten.

A player's movement points are shown as a row of dots: a filled one for each point left, an empty one for each
spent. Seven pixels across, with the palette's outline round it like the other assets. The filled dot is the
move overlay's blue (sky, with a cyan highlight top left and blue in the shade bottom right) so it reads as "movement";
the empty one is the same shape as a dim socket, darker on the lit side and lighter on the shaded side so it looks pressed in.

    python3 tools/make_ui.py --preview previews/movement-dots.png     rows of them, some filled and some empty
"""
import sys
from pathlib import Path
from assetkit import sheet_layout  # noqa: E402

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


# --- the shell: a dot wrapped in a larger one ---------------------------------------------------------
# When there are more than ten of a point, a shell is drawn behind its dot to show the count has wrapped. It is a thick outlined ring in the dot's own colours
# (bright top left, dark bottom right) round a dark socket the dot sits in, so it reads as the dot nested inside a bigger gem. One wrap only.
SHELL_R = 5.4                   # the shell's radius; its cell is 2 r + 1 across (the dot is 7 across, so it adds one outline and one rim pixel all round)
SHELL = 11
SHELL_MIDDLE = (5, 5)
SHELL_BURST = 19                # room for the pieces to fly
SHELL_BURST_MIDDLE = (9, 9)
SHELL_BURST_FRAMES = 8
SHELL_PIECES = 8


def shell_grid(size, middle, r, tones=('o', 'n', 'm'), socket=('w', 'k', 'l')):
    """The shell as letters on a size x size grid: an outline, a rim shaded like the dot, and a dark socket inside, radius r."""
    grid = [['.'] * size for _ in range(size)]
    cx, cy = middle
    for y in range(size):
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > r + 0.3:
                continue
            t = ((x - cx) + (y - cy)) / (2 * max(r, 1))
            if d > r - 0.8:
                grid[y][x] = 'O'
            elif d > r - 1.9:
                grid[y][x] = tones[0] if t < -0.35 else tones[2] if t > 0.3 else tones[1]
            else:
                grid[y][x] = socket[0] if t < -0.35 else socket[2] if t > 0.4 else socket[1]
    return grid


def paint(colours, grid):
    return [''.join(colours.get(c, c) for c in row) for row in grid]


def render_shell(colours=BLUE):
    return paint(colours, shell_grid(SHELL, SHELL_MIDDLE, SHELL_R))


def piece_of(x, y, middle):
    """Which of the eight pieces (wedges round the middle) a pixel belongs to, and the direction that piece flies."""
    import math
    angle = math.atan2(y - middle[1], x - middle[0]) % (2 * math.pi)
    k = int(angle // (2 * math.pi / SHELL_PIECES)) % SHELL_PIECES
    mid = (k + 0.5) * 2 * math.pi / SHELL_PIECES
    return k, (math.cos(mid), math.sin(mid))


def render_shell_burst(frame, colours=BLUE):
    """The shell breaking: it swells and cracks, flashes, splits into eight pieces that fly out and fade, and nothing is left (the dot has its own animation)."""
    import math
    size, middle = SHELL_BURST, SHELL_BURST_MIDDLE
    cx, cy = middle
    k = SHELL_R / 6.4                                                  # everything below was drawn for a radius of 6.4
    out = [['.'] * size for _ in range(size)]
    if frame == 0:
        out = shell_grid(size, middle, SHELL_R)
    elif frame == 1:
        out = shell_grid(size, middle, SHELL_R + 0.8)               # it swells
        for n in range(SHELL_PIECES):                             # light leaks through the cracks between pieces
            a = n * 2 * math.pi / SHELL_PIECES
            for step in (2.5 * k, 3.5 * k, 4.5 * k, 5.5 * k, 6.3 * k):
                x, y = round(cx + math.cos(a) * step), round(cy + math.sin(a) * step)
                if out[y][x] != '.':
                    out[y][x] = 't'
    elif frame == 7:
        for dx, dy in ((7, 0), (-7, 1), (1, 7), (0, -7), (5, 5), (-5, -5)):      # a last few sparks
            dx, dy = round(dx * k), round(dy * k)
            out[cy + dy][cx + dx] = 't' if (dx + dy) % 2 else 'o'
    else:
        reach = {2: 0.9, 3: 1.9, 4: 2.9, 5: 3.7, 6: 4.2}[frame] * k
        base = shell_grid(size, middle, SHELL_R)
        for y in range(size):
            for x in range(size):
                c = base[y][x]
                if c == '.':
                    continue
                _, (ux, uy) = piece_of(x, y, middle)
                nx, ny = round(x + ux * reach), round(y + uy * reach)
                if frame >= 5 and (x + y + frame) % (2 if frame == 5 else 3) == 0:
                    continue                                       # the pieces crumble away
                if 0 <= nx < size and 0 <= ny < size:
                    if frame >= 4 and c in 'ow':
                        c = 'n' if c == 'o' else 'k'                # and dim as they go
                    out[ny][nx] = c
        if frame == 2:
            for y in range(size):
                for x in range(size):
                    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if SHELL_R + 1.8 <= d < SHELL_R + 3.0 and out[y][x] == '.':
                        out[y][x] = 't'                            # the flash
    return paint(colours, out)


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--shell', type=Path, help='write the shell and its breaking animation here, one row per colour')
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
    if args.shell:
        scale = 12
        cols = SHELL_BURST_FRAMES
        out = Image.new('RGBA', ((cols + 4) * (SHELL_BURST + 1) * scale, len(COLOURWAYS) * (SHELL_BURST + 1) * scale), (36, 38, 56, 255))

        def put(pixels, ox, oy):
            for y, line in enumerate(pixels):
                for x, c in enumerate(line):
                    if c != '.':
                        for dy in range(scale):
                            for dx in range(scale):
                                out.putpixel(((ox + x) * scale + dx, (oy + y) * scale + dy), rgb[c] + (255,))
        for r, (_, _, colours) in enumerate(COLOURWAYS):
            oy = r * (SHELL_BURST + 1)
            put(render_shell(colours), 1, oy + 4)
            behind = [list(row) for row in render_shell(colours)]            # a dot over its shell, as the game stacks them
            for y, line in enumerate(render_pixels('filled', colours)):
                for x, c in enumerate(line):
                    if c != '.':
                        behind[(SHELL - 7) // 2 + y][(SHELL - 7) // 2 + x] = c
            put([''.join(row) for row in behind], 15, oy + 4)
            for f in range(cols):
                put(render_shell_burst(f, colours), 30 + f * (SHELL_BURST + 1) - 0, oy)
        out.save(args.shell)
        print('wrote', args.shell)
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

def build_assets():
    # The dots for the UI: filled for a point left, empty for a point spent. Blue is the movement point; red is its twin.
    dot_assets = [{
        'id': id_, 'label': label, 'category': 'UI', 'kind': 'variants', 'place': 'none',
        'names': ['Filled', 'Empty'],
        'w': DOT, 'h': DOT, 'cols': 2, 'rows': 1, 'fps': 0,
        'anchor': {'x': MIDDLE[0], 'y': MIDDLE[1]},
        'frames': [render_pixels('filled', colours), render_pixels('empty', colours)],
    } for id_, label, colours in COLOURWAYS]
    # The dots bursting as a point is spent: full to empty, played once.
    for id_, label, colours in COLOURWAYS:
        burst_frames = [render_burst(f, colours) for f in range(BURST_FRAMES)]
        cols, rows = sheet_layout(len(burst_frames))
        dot_assets.append({
            'id': id_ + '-burst', 'label': label.replace(' (filled and empty)', '') + ' - burst (full to empty)', 'category': 'UI',
            'kind': 'animation', 'place': 'none',
            'w': BURST, 'h': BURST, 'cols': cols, 'rows': rows, 'fps': 14,
            'anchor': {'x': BURST_MIDDLE[0], 'y': BURST_MIDDLE[1]},
            'frames': burst_frames,
        })
    # The shell drawn behind a dot when there are more than ten of a point: one still image, and its break (the shell shattering), played once. Its middle is the dot's middle.
    for id_, label, colours in COLOURWAYS:
        short = label.replace(' (filled and empty)', '')
        dot_assets.append({
            'id': id_ + '-shell', 'label': short + ' - shell (behind the dot, for a wrapped count)', 'category': 'UI', 'kind': 'variants', 'place': 'none',
            'names': ['Shell'], 'w': SHELL, 'h': SHELL, 'cols': 1, 'rows': 1, 'fps': 0,
            'anchor': {'x': SHELL_MIDDLE[0], 'y': SHELL_MIDDLE[1]},
            'frames': [render_shell(colours)],
        })
    for id_, label, colours in COLOURWAYS:
        break_frames = [render_shell_burst(f, colours) for f in range(SHELL_BURST_FRAMES)]
        cols, rows = sheet_layout(len(break_frames))
        dot_assets.append({
            'id': id_ + '-shell-break', 'label': label.replace(' (filled and empty)', '') + ' - shell breaking', 'category': 'UI',
            'kind': 'animation', 'place': 'none',
            'w': SHELL_BURST, 'h': SHELL_BURST, 'cols': cols, 'rows': rows, 'fps': 14,
            'anchor': {'x': SHELL_BURST_MIDDLE[0], 'y': SHELL_BURST_MIDDLE[1]},
            'frames': break_frames,
        })
    return dot_assets


if __name__ == '__main__':
    main()
