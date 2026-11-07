#!/usr/bin/env python3
"""Vanish and appear: a shimmer that gathers a unit into a point, and (played backwards) grows it back out.

`vanish-COLOUR` is 8 frames: a column of shimmer rings round the unit, sparkles streaming in, the rings shrinking to a bright point that flashes and is gone. The game shrinks the unit's own
sprite to that point as it plays. `appear-COLOUR` is the same frames in the other order (a flash, then rings and sparkles spreading out), for the unit growing back, and for a summon expiring.
Four colours: violet (blink, swap), pale blue (call wolf), yellow (call decoy), stone grey (raise guardian). The cell is 48 x 56 with the unit's feet at the anchor (24, 44).

    python3 tools/make_vanish.py --preview previews/vanish.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
from fx import Grid, hashed, smoothstep  # noqa: E402

W, H = 48, 56
ANCHOR = (24, 44)
FRAMES = 8
FPS = 12
CENTRE = (24, 31)                                   # the middle of the unit, which the shimmer closes in on

COLOURS = {
    'violet': ('Violet (blink, swap)', dict(core='t', bright='y', mid='v', deep='u')),
    'blue': ('Pale blue (call wolf)', dict(core='t', bright='r', mid='o', deep='n')),
    'yellow': ('Yellow (call decoy)', dict(core='t', bright='d', mid='b', deep='a')),
    'stone': ('Stone grey (raise guardian)', dict(core='t', bright='q', mid='p', deep='l')),
}


def vanish_frame(f, pal):
    g = Grid(W, H)
    cx, cy = CENTRE
    t = f / (FRAMES - 1)
    close = 1 - smoothstep(0.0, 0.8, t)                  # 1 = fully open, 0 = a point
    if f < FRAMES - 1:
        for k in range(4):                               # rings stacked up the unit, each shrinking onto the middle
            y = cy + (k - 1.5) * 9 * close
            r = (13 - k * 1.2) * close + 1.5
            if r > 1.6:
                g.ellipse(cx, y, r, r * 0.5, pal['deep'] if k % 2 else pal['mid'], thick=2.0)
                g.ellipse(cx, y, r, r * 0.5, pal['bright'] if k % 2 else pal['core'], thick=1.0)
        for k in range(10):                              # sparkles streaming in from round the unit
            a = k * 2.4 + hashed(k, 3) * 1.5
            run = (1 - smoothstep(0.0, 0.85, (t + k * 0.07) % 1.0)) * 15
            x = cx + math.cos(a) * run
            y = cy - 3 + math.sin(a) * run * 1.2
            if run > 1.5:
                g.put(x, y, pal['core'] if k % 3 == 0 else pal['bright'])
                g.put(x + 1, y, pal['mid'])
        g.ellipse(cx, 43, 14 * close + 2, (14 * close + 2) * 0.5, pal['mid'], thick=1.4)       # a ring on the ground closing too
    if t > 0.55:                                          # the point it all gathers into: a growing glint, then a flash
        k = smoothstep(0.55, 1.0, t)
        size = int(1 + 4 * k)
        g.sparkle(cx, cy, size, pal['bright'], pal['core'])
        g.disc(cx, cy, 1 + 2.2 * (1 - abs(2 * k - 1)), pal['core'])
    if f == FRAMES - 1:                                   # the last frame: a faint glint where the unit was
        g.sparkle(cx, cy, 2, pal['mid'], pal['core'])
    return g.lines()


def build_assets():
    assets = []
    for name, (label, pal) in COLOURS.items():
        frames = [vanish_frame(f, pal) for f in range(FRAMES)]
        common = dict(category='Abilities', folder='abilities', kind='animation', place='ground', w=W, h=H, cols=FRAMES, rows=1, fps=FPS, anchor={'x': ANCHOR[0], 'y': ANCHOR[1]})
        assets.append(dict(common, id=f'vanish-{name}', label=f'Vanish - {label}', fx={'family': 'vanish', 'colour': name, 'direction': 'in'}, frames=frames))
        assets.append(dict(common, id=f'appear-{name}', label=f'Appear - {label}', fx={'family': 'vanish', 'colour': name, 'direction': 'out'}, frames=list(reversed(frames))))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = [fx.save_preview('/tmp/_v.png', [vanish_frame(f, pal) for f in range(FRAMES)], W, H, cols=8, scale=2, plots=[ANCHOR], ground_tile=ground) for name, (label, pal) in COLOURS.items()]
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
