#!/usr/bin/env python3
"""Pop-up icons for status abilities: a glyph pops in above a unit's head and fades, and the same glyph loops as the unit's status icon.

    mark      a crosshair                  silence   sealed lips
    stun      stars                        charm     a heart                  confuse   a spiral

Each glyph is drawn at 14 x 14 with a dark outline, in its own colours. `icon-NAME-pop` is the pop-up (8 frames, plays once: it pops in bigger than it settles, rises a little and
dissolves away) and `icon-NAME-loop` is the status icon (6 frames, loops: the stars orbit, the spiral turns, the heart beats, the crosshair closes in, the stitches on the lips
twitch). The cell is 24 x 32 and the anchor (12, 30) is the point just above the unit's head that the glyph sits over.

    python3 tools/make_icons.py --preview previews/icons.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
from fx import Grid, dither, hashed, smoothstep  # noqa: E402

W, H = 24, 32
ANCHOR = (12, 30)
GLYPH = 14
POP_FRAMES, LOOP_FRAMES = 8, 6
FPS_POP, FPS_LOOP = 10, 6
OUT = 'O'
CX, CY = 12.0, 18.0                                 # the middle of the glyph in the cell


def outline(g):
    """A one-pixel dark outline round whatever is drawn."""
    solid = {(x, y) for y in range(g.h) for x in range(g.w) if g.rows[y][x] != '.'}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in solid:
                g.put(x + dx, y + dy, OUT)


def crosshair(g, cx, cy, phase):
    r = 5.2 - 0.9 * math.sin(phase * 2 * math.pi)            # the ring closes in and opens
    g.ellipse(cx, cy, r, r, 'a', thick=1.6)
    for k in range(4):
        a = k * math.pi / 2
        for j in range(3, 8):
            g.put(cx + math.cos(a) * j, cy + math.sin(a) * j, 'b' if j > 5 else 'a')
    g.put(cx, cy, 't')
    g.put(cx - 1, cy, 'a'), g.put(cx + 1, cy, 'a'), g.put(cx, cy - 1, 'a'), g.put(cx, cy + 1, 'a')


LIPS = [
    "..............",
    "..............",
    "..eeeee.eeee..",
    ".ejjjjjejjjje.",
    "eijjjjjjjjjjie",
    ".eiiiiiiiiiie.",
    "..eeeeeeeeee..",
    "..............",
]


def lips(g, cx, cy, phase):
    x0, y0 = cx - 7, cy - 4
    for y, row in enumerate(LIPS):
        for x, ch in enumerate(row):
            if ch != '.':
                g.put(x0 + x, y0 + y, ch)
    for k in range(4):                                       # cream stitches across the mouth, twitching
        sx = x0 + 3 + k * 2.5
        jig = 1 if int(phase * 6 + k) % 2 else 0
        g.line(sx, y0 + 2 - jig, sx + 0.5, y0 + 6 + jig, 't')


def stars(g, cx, cy, phase):
    for k in range(3):
        a = phase * 2 * math.pi + k * 2 * math.pi / 3
        x = cx + math.cos(a) * 5.0
        y = cy + math.sin(a) * 2.2 - 1
        g.sparkle(round(x), round(y), 2, 'd', 't')
        g.put(round(x) + 1, round(y) + 1, 'b')
        g.put(round(x) - 1, round(y) - 1, 'b')


HEART = [
    "..............",
    "..jjj...jjj...",
    ".jtjjj.jjjjj..",
    "jtjjjjjjjjjjj.",
    "jjjjjjjjjjjjj.",
    ".jjjjjjjjjjj..",
    "..iijjjjjii...",
    "...iijjjii....",
    "....iijii.....",
    ".....ii.......",
]


def heart(g, cx, cy, phase):
    beat = 1.0 + 0.12 * math.sin(phase * 2 * math.pi * 2)
    rows, cols = len(HEART), len(HEART[0])
    for y in range(int(rows * beat) + 1):
        for x in range(int(cols * beat) + 1):
            sx, sy = int(x / beat), int(y / beat)
            if sy < rows and sx < cols and HEART[sy][sx] != '.':
                g.put(cx - cols * beat / 2 + x, cy - rows * beat / 2 + y - 1, HEART[sy][sx])


def spiral(g, cx, cy, phase):
    pts = []
    for i in range(0, 86):
        t = i / 85
        a = t * 3.6 * math.pi + phase * 2 * math.pi
        r = 0.7 + 5.6 * t
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    for i, (x, y) in enumerate(pts):
        c = 'v' if i < 30 else 'y' if i < 60 else 'f'
        g.put(x, y, c)
        if i > 20:
            g.put(x + 1, y, c)
    g.put(cx, cy, 't')


GLYPHS = {
    'mark': ('Mark (crosshair)', crosshair),
    'silence': ('Silence (sealed lips)', lips),
    'stun': ('Stun (stars)', stars),
    'charm': ('Charm (heart)', heart),
    'confuse': ('Confuse (spiral)', spiral),
}


def glyph_image(name, phase):
    """The glyph at its settled size, outlined, as a small grid."""
    g = Grid(GLYPH + 4, GLYPH + 4)
    GLYPHS[name][1](g, (GLYPH + 4) / 2, (GLYPH + 4) / 2, phase)
    outline(g)
    return g


def pop(name, f):
    """Pop in bigger than it settles (a little overshoot), rise a few pixels, hold, and dissolve away."""
    src = glyph_image(name, f / POP_FRAMES)
    scale = (0.4, 1.3, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0)[f]
    rise = (0, 0, 1, 2, 3, 4, 5, 6)[f]
    fade = (1, 1, 1, 1, 1, 0.75, 0.45, 0.2)[f]
    g = Grid(W, H)
    n = src.w
    size = int(round(n * scale))
    ox, oy = CX - size / 2, CY - size / 2 - rise
    for y in range(size):
        for x in range(size):
            c = src.rows[min(n - 1, int(y / scale))][min(n - 1, int(x / scale))]
            if c != '.' and dither(x + ox, y + oy, fade):
                g.put(ox + x, oy + y, c)
    return g.lines()


def loop(name, f):
    g = Grid(W, H)
    src = glyph_image(name, f / LOOP_FRAMES)
    for y in range(src.h):
        for x in range(src.w):
            if src.rows[y][x] != '.':
                g.put(CX - src.w / 2 + x, CY - src.h / 2 + y, src.rows[y][x])
    return g.lines()


def build_assets():
    assets = []
    for name, (label, _) in GLYPHS.items():
        common = dict(category='Abilities', folder='abilities', kind='animation', place='above', w=W, h=H, rows=1, anchor={'x': ANCHOR[0], 'y': ANCHOR[1]})
        assets.append(dict(common, id=f'icon-{name}-pop', label=f'{label} - pop-up above the head (once)', cols=POP_FRAMES, fps=FPS_POP,
                           fx={'family': 'icon', 'glyph': name, 'state': 'pop', 'loops': False}, frames=[pop(name, f) for f in range(POP_FRAMES)]))
        assets.append(dict(common, id=f'icon-{name}-loop', label=f'{label} - status icon (loops)', cols=LOOP_FRAMES, fps=FPS_LOOP,
                           fx={'family': 'icon', 'glyph': name, 'state': 'loop', 'loops': True}, frames=[loop(name, f) for f in range(LOOP_FRAMES)]))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    sheets = []
    for name in GLYPHS:
        sheets.append(fx.save_preview('/tmp/_i.png', [pop(name, f) for f in range(POP_FRAMES)] + [loop(name, f) for f in range(LOOP_FRAMES)], W, H, cols=14, scale=4))
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
