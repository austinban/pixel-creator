#!/usr/bin/env python3
"""The bone a skeleton throws: a spinning projectile, and the bone shattering where it hits.

    projectile-bone-spin      8 frames, loops: a long bone tumbling end over end (the frames cover half a turn, which is a full one for a bone, so the loop is seamless)
    projectile-bone-shatter   6 frames, plays once: it cracks, breaks into three pieces that fly apart and fall, and a puff of bone dust

Both are drawn on a 24 x 24 cell with the middle of the bone at the anchor (12, 12). The game moves the spin along the throw (from the thrower's hand to the target's) and plays the shatter where it lands.
The throw animation itself, with the bone in the hand, is make_throw.py.

    python3 tools/make_bone.py --preview previews/bone.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
from fx import Grid, dither, hashed  # noqa: E402

CELL = 24
ANCHOR = (12, 12)
SPIN_FRAMES, SHATTER_FRAMES = 8, 6
LIGHT = (-0.55, -0.83)
BONE = ('t', 'C', 'p', 'k')            # the skeleton's own bone: pale, sand, steel shade, indigo
LENGTH = 15.0


def draw_bone(g, cx, cy, angle, length=LENGTH, thick=1.1, knob=2.0, fade=1.0, seed=0):
    """A long bone: a thin shaft and a double knob at each end, shaded from the upper left, with an outline."""
    ax, ay = math.cos(angle), math.sin(angle)
    px, py = -ay, ax                                       # across the shaft
    mask = {}
    half = length / 2
    steps = int(length * 3)
    for i in range(steps + 1):
        t = -half + length * i / steps
        x, y = cx + ax * t, cy + ay * t
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                X, Y = int(x) + dx, int(y) + dy
                off = (X + 0.5 - x) * px + (Y + 0.5 - y) * py
                along = (X + 0.5 - x) * ax + (Y + 0.5 - y) * ay
                if abs(off) <= thick / 2 + 0.35 and abs(along) <= 0.7:
                    lit = off * (px * LIGHT[0] + py * LIGHT[1])
                    mask[(X, Y)] = BONE[0 if lit > 0.35 else 1 if lit > -0.35 else 2]
    for end in (-1, 1):                                     # a knob of two lobes at each end
        for lobe in (-1, 1):
            kx = cx + ax * end * (half - 0.4) + px * lobe * knob * 0.62
            ky = cy + ay * end * (half - 0.4) + py * lobe * knob * 0.62
            for Y in range(int(ky - knob - 1), int(ky + knob + 2)):
                for X in range(int(kx - knob - 1), int(kx + knob + 2)):
                    d = math.hypot(X + 0.5 - kx, Y + 0.5 - ky)
                    if d <= knob * 0.82:
                        lit = -((X + 0.5 - kx) * LIGHT[0] * -1 + (Y + 0.5 - ky) * LIGHT[1] * -1) / (knob * 0.82)
                        lit = ((kx - X - 0.5) * 0.55 + (ky - Y - 0.5) * 0.83) / (knob * 0.82)
                        mask[(X, Y)] = BONE[0 if lit > 0.35 else 1 if lit > -0.3 else 2]
    solid = set(mask)
    for (X, Y), c in mask.items():
        if fade >= 1.0 or dither(X + seed, Y, fade):
            g.put(X, Y, c)
    for (X, Y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (X + dx, Y + dy) not in solid and (fade >= 1.0 or dither(X + seed, Y, fade)):
                g.put(X + dx, Y + dy, 'O')


def spin(f):
    g = Grid(CELL, CELL)
    draw_bone(g, *ANCHOR, angle=math.pi * f / SPIN_FRAMES - math.pi / 5)
    return g.lines()


def shatter(f):
    g = Grid(CELL, CELL)
    cx, cy = ANCHOR
    if f == 0:
        draw_bone(g, cx, cy, -0.5)
        g.line(cx - 1, cy - 2, cx + 1, cy + 2, 'k')                 # a crack across it
        return g.lines()
    t = f - 1
    pieces = ((-1.0, -0.2, 0.2, 5.0), (0.2, -1.0, 0.8, 4.2), (1.0, 0.1, -0.4, 5.4))      # (flight x, flight y, spin, length): three pieces
    for k, (vx, vy, sp, ln) in enumerate(pieces):
        x = cx + vx * t * 3.0
        y = cy + vy * t * 3.0 + 0.55 * t * t * 1.3
        fade = 1.0 if f < 4 else 0.7 if f == 4 else 0.4
        draw_bone(g, x, y, -0.5 + sp * t * 1.4 + k, length=ln, thick=1.0, knob=1.3, fade=fade, seed=k)
    for k in range(7):                                              # bone dust
        a = k * 2 * math.pi / 7 + 0.4
        r = 1.5 + t * 2.6
        if t < 4:
            g.put(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7 - 1, 't' if k % 2 else 'C')
    return g.lines()


def build_assets():
    common = dict(category='Weapons', kind='animation', place='none', w=CELL, h=CELL, rows=1, anchor={'x': ANCHOR[0], 'y': ANCHOR[1]})
    return [
        dict(common, id='projectile-bone-spin', label='Thrown bone - spinning (loops)', cols=SPIN_FRAMES, fps=16, projectile={'name': 'bone', 'state': 'flying', 'loops': True},
             frames=[spin(f) for f in range(SPIN_FRAMES)]),
        dict(common, id='projectile-bone-shatter', label='Thrown bone - shattering where it lands (once)', cols=SHATTER_FRAMES, fps=12, projectile={'name': 'bone', 'state': 'shatter', 'loops': False},
             frames=[shatter(f) for f in range(SHATTER_FRAMES)]),
    ]


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        frames = [spin(f) for f in range(SPIN_FRAMES)] + [shatter(f) for f in range(SHATTER_FRAMES)]
        fx.save_preview(args.preview, frames, CELL, CELL, cols=8, scale=6)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
