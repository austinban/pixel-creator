#!/usr/bin/env python3
"""Ground loops: animated surfaces that stay on the ground for several rounds, in three kinds, as one-plot tiles that loop seamlessly.

    mire        brown-yellow mud with bubbles that swell and pop
    slick       blue wet ground with a sheen sliding over it and glints
    firewall    a row of flames, flickering, for a wall of fire (a line of three, one tile on each plot)

Each is `surface-NAME` (8 frames, loops, at 8 a second). The mire and the slick are drawn on a 32 x 16 diamond and join their neighbours: the pattern repeats from plot to plot, so five of them
side by side (radius 1) or any shape make one surface. The fire wall is flames standing on each plot, taller than the diamond, on a 32 x 56 cell with the anchor (16, 44); place it on each plot of the
line, and start each tile on a different frame so the flames do not all move together.

    python3 tools/make_ground_fx.py --preview previews/ground-loops.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
import make_fire as fire  # noqa: E402
from fx import Grid, dither, hashed  # noqa: E402

FRAMES = 8
FPS = 8
W, H = 32, 56
ANCHOR = (16, 44)


def uv(x, y):
    """The plot's own coordinates: whole numbers between neighbouring plots, so a pattern that repeats every 1 here joins up across plots."""
    return (x - ANCHOR[0] + 0.5) / 32 + (y - ANCHOR[1] + 0.5) / 16, (x - ANCHOR[0] + 0.5) / 32 - (y - ANCHOR[1] + 0.5) / 16


def mire(f):
    g = Grid(W, H)
    t = f / FRAMES
    for y in range(ANCHOR[1] - 9, ANCHOR[1] + 9):
        for x in range(0, W):
            if not fx.diamond_inside(ANCHOR[0], ANCHOR[1], x, y):
                continue
            u, v = uv(x, y)
            fu, fv = u % 1.0, v % 1.0
            n = hashed(int(fu * 14), int(fv * 14), 1)
            sw = 0.5 + 0.5 * math.sin((fu + fv) * 6.28 * 2 + t * 6.28)            # slow churn, repeating each plot
            g.put(x, y, 'a' if n < 0.18 else 'b' if sw > 0.45 else 'C' if n < 0.55 else 'b')
    for k in range(5):                                                            # bubbles: each swells, glints, and pops, on its own phase
        bu, bv = hashed(k, 1), hashed(k, 2)
        phase = (t + hashed(k, 3)) % 1.0
        x = ANCHOR[0] + ((bu + bv) - 1.0) * 16
        y = ANCHOR[1] + (bu - bv) * 8
        if phase < 0.7:
            r = 0.8 + 3.0 * phase / 0.7
            g.ellipse(x, y, r, r * 0.55, 'd', thick=1.0)
            g.put(x - r * 0.4, y - r * 0.2, 't')
        elif phase < 0.85:
            for a in range(5):
                g.put(x + math.cos(a * 1.26) * 3.8, y + math.sin(a * 1.26) * 2.0 - 1, 'd')
    return g.lines()


def slick(f):
    g = Grid(W, H)
    t = f / FRAMES
    for y in range(ANCHOR[1] - 9, ANCHOR[1] + 9):
        for x in range(0, W):
            if not fx.diamond_inside(ANCHOR[0], ANCHOR[1], x, y):
                continue
            u, v = uv(x, y)
            band = (u * 2 + v * 0.0 - t * 2) % 1.0                                # a sheen sliding across, repeating each plot
            n = hashed(int((u % 1.0) * 12), int((v % 1.0) * 12), 2)
            if band < 0.14:
                g.put(x, y, 'r' if band < 0.07 else 'o')
            elif band < 0.3 and dither(x, y, 0.5):
                g.put(x, y, 'o')
            else:
                g.put(x, y, 'n' if n < 0.55 else 'm' if n < 0.85 else 'q')
    for k in range(3):                                                            # glints that twinkle
        ph = (t * 2 + hashed(k, 7)) % 1.0
        if ph < 0.3:
            bu, bv = hashed(k, 8), hashed(k, 9)
            g.sparkle(round(ANCHOR[0] + (bu + bv - 1.0) * 14), round(ANCHOR[1] + (bu - bv) * 6), 1, 'r', 't')
    return g.lines()


def firewall(f):
    """Flames on one plot. Drawn with the fire burst's flame helpers on a wide scratch grid, then cut to the tile's width."""
    g = Grid(80, H)
    cx, cy = 40, ANCHOR[1]
    ph = 2 * math.pi * f / FRAMES
    for y in range(cy - 9, cy + 9):                                              # a glowing, scorched plot under the flames
        for x in range(cx - 17, cx + 17):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.05) and dither(x, y, 0.55) and hashed(x, y, 3) < 0.6:
                g.put(x, y, 'a' if hashed(x, y, 4) < 0.5 else 'e')
    for dy, (w, c) in enumerate(((0.55, 'a'), (1.0, 'e'), (0.8, 'a'))):             # the flames' foot: a flickering bed, drawn here so it repeats every 8 frames
        half = 24 * w / 2
        for x in range(int(cx - half), int(cx + half) + 1):
            if hashed(x, dy, f % FRAMES) > 0.2:
                g.put(x, cy - 1 + dy, c)
    wob = math.sin(ph)
    for i, (dx, hgt, w, off, sway) in enumerate(((-8, 15, 10, 1.7, -1.5), (8, 17, 10, 3.1, 1.5), (0, 24, 14, 0.0, 1.0), (-12, 9, 7, 4.3, -1.0), (12, 10, 7, 5.5, 1.0))):
        h = hgt * (1 + 0.14 * math.sin(ph + off))
        fire.tongue(g.rows, cx + dx, cy + 1 + (2 if i == 2 else 0), h, w, ph + off, sway * (1 + 0.4 * wob))
    for k in range(4):                                                            # sparks rising, one cycle every 8 frames
        a = k * 1.7
        yy = cy - 6 - ((f * 3 + k * 6) % 24)
        g.put(cx + math.sin(a + ph) * 8, yy, 't' if k % 2 else 'd')
    return [line[cx - ANCHOR[0]:cx - ANCHOR[0] + W] for line in g.lines()]


KINDS = {
    'mire': ('Mire (brown-yellow mud)', mire, 'ground'),
    'slick': ('Slick ground (blue, wet)', slick, 'ground'),
    'firewall': ('Fire wall (flames, for a line of three)', firewall, 'ground'),
}


def build_assets():
    assets = []
    for name, (label, draw, place) in KINDS.items():
        assets.append(dict(category='Abilities', folder='abilities', id=f'surface-{name}', label=f'Ground loop - {label}', kind='animation', place=place, w=W, h=H, cols=FRAMES, rows=1,
                           fps=FPS, anchor={'x': ANCHOR[0], 'y': ANCHOR[1]}, fx={'family': 'ground', 'kind': name, 'loops': True}, frames=[draw(f) for f in range(FRAMES)]))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = []
    for name, (label, draw, place) in KINDS.items():
        # five plots side by side (the middle and the four round it) as one wide frame, to show the join
        cell_w, cell_h = 80, 72
        frames = []
        for f in range(FRAMES):
            g = Grid(cell_w, cell_h)
            tile = draw(f)
            for plot, (dx, dy) in ((('NW'), (-16, -8)), ('NE', (16, -8)), ('C', (0, 0)), ('SW', (-16, 8)), ('SE', (16, 8))) if name != 'firewall' else (('a', (-32, -16)), ('b', (0, 0)), ('c', (32, 16))):
                for y, row in enumerate(tile):
                    for x, c in enumerate(row):
                        if c != '.':
                            g.put(40 + dx + x - ANCHOR[0], 44 + dy + y - ANCHOR[1] + 0, c)
            frames.append(g.lines())
        plots = [(40 + dx, 44 + dy) for dx, dy in ((-16, -8), (16, -8), (0, 0), (-16, 8), (16, 8))] if name != 'firewall' else [(40 + dx, 44 + dy) for dx, dy in ((-32, -16), (0, 0), (32, 16))]
        sheets.append(fx.save_preview('/tmp/_g.png', frames, cell_w, cell_h, cols=8, scale=2, plots=plots, ground_tile=ground))
    if args.preview:
        out = Image.new('RGBA', (max(s.width for s in sheets), sum(s.height for s in sheets)), (36, 38, 56, 255))
        y = 0
        for s in sheets:
            out.alpha_composite(s, (0, y))
            y += s.height
        out.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
