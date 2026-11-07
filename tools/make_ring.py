#!/usr/bin/env python3
"""Ring pulses: rings of light that spread out from a unit on the ground, for the support abilities, in a few colours, and the ward bubble and the break.

    pulse     a ring that spreads out over the ground with a few sparkles and fades (rally, inspire, cleanse); rally is the large one for radius 2
    sever     a white ring that cracks and breaks into pieces that fly out and fall
    ward      a blue bubble: it forms round the unit (ward-form), holds with a shimmer (ward-hold, loops), and breaks when it takes a hit (ward-break, the same break as sever)
    climb     light blue rings that rise up the unit from the ground
    dash      white speed lines streaking behind the unit, for NE and SE (NW and SW are those flipped)

Small effects are drawn on a 64 x 56 cell with the unit's feet at the anchor (32, 40); the rally on a 112 x 72 cell with the anchor (56, 52). 8 frames each (the ward-hold loop is 6).

    python3 tools/make_ring.py --preview previews/rings.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
from fx import Grid, dither, hashed, smoothstep  # noqa: E402

SMALL = (64, 56, (32, 40))
LARGE = (112, 72, (56, 52))
FRAMES = 8
FPS = 10

PALETTES = {
    'gold': dict(core='t', ring='d', edge='b', glow='a', spark='t'),
    'yellow': dict(core='t', ring='d', edge='d', glow='b', spark='t'),
    'cleanse': dict(core='t', ring='r', edge='z', glow='A', spark='t'),
    'white': dict(core='t', ring='t', edge='r', glow='q', spark='t'),
    'ward': dict(core='r', ring='o', edge='n', glow='m', spark='t'),
    'climb': dict(core='t', ring='r', edge='o', glow='n', spark='r'),
    'blue': dict(core='r', ring='o', edge='n', glow='m', spark='t'),
    'storm': dict(core='t', ring='d', edge='b', glow='a', spark='t'),
    'green': dict(core='t', ring='z', edge='A', glow='B', spark='z'),
}


def pulse(g, cx, cy, rmax, f, pal, sparks=5, seed=1, t=None):
    """A ring on the ground spreading out from (cx, cy): bright at first, then thinner and fainter, with sparkles rising."""
    t = f / (FRAMES - 1) * 0.94 if t is None else t              # (a hair short of 1, so the last frame still shows the ring's last trace)
    r = 4 + (rmax - 4) * smoothstep(0, 1, t ** 0.8)
    fade = 1 - smoothstep(0.55, 1.0, t)
    thick = 1.0 + 2.6 * (1 - t)
    for y in range(int(cy - rmax * 0.5 - 4), int(cy + rmax * 0.5 + 5)):          # a faint glow filling the ring, thinning out
        for x in range(int(cx - rmax - 4), int(cx + rmax + 5)):
            d = math.hypot((x + 0.5 - cx) / r, (y + 0.5 - cy) / (r * 0.5))
            if d < 1.0 and dither(x, y, 0.2 * fade * (1 - d)) and hashed(x, y, seed) < 0.6:
                g.put(x, y, pal['glow'])
    if fade > 0.04:
        g.ellipse(cx, cy, r, r * 0.5, pal['edge'], thick=thick + 1.4)
        g.ellipse(cx, cy, r, r * 0.5, pal['ring'] if t < 0.7 else pal['edge'], thick=thick)
        if t < 0.45:
            g.ellipse(cx, cy, r, r * 0.5, pal['core'], thick=max(0.8, thick - 1.6))
    for k in range(sparks):                                                    # sparkles rising off the ring
        a = k * 2 * math.pi / sparks + seed + hashed(k, seed) * 0.8
        x = cx + math.cos(a) * r * 0.96
        y = cy + math.sin(a) * r * 0.48 - 2 - (t * 8 + k * 2) % 9
        if fade > 0.1 and hashed(f, k, seed) < 0.9:
            g.sparkle(x, y, 1 if (f + k) % 3 else 2, pal['spark'] if k % 2 else pal['ring'], pal['core'])


def shards(g, cx, cy, rmax, f, pal, start=2, seed=3):
    """A ring (or bubble) breaking: the ring forms, cracks, then 12 pieces of it fly out and fall away, fading."""
    t = f - start
    n = 12
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        if t < 0:
            continue                                                            # (before `start` the intact ring is drawn by the caller)
        vx, vy = math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)
        out = 1.0 + 1.6 * t
        lift = (2.5 * t - 0.5 * t * t)
        drop = 0.5 * max(0, t - 1) ** 2
        a_mid = (a0 + a1) / 2
        alive = 1 - smoothstep(2.5, 5.2, t) * (0.6 + 0.6 * hashed(k, seed))
        for j in range(4):
            a = a0 + (a1 - a0) * j / 3
            x = cx + math.cos(a) * rmax * out
            y = cy + math.sin(a) * rmax * 0.5 * out - lift * (0.7 + 0.5 * hashed(k, seed, 1)) + drop * 1.5
            if dither(x + k, y, alive + 0.15):
                g.put(x, y, pal['ring'] if j % 2 == 0 else pal['edge'])
                g.put(x + 1, y, pal['ring'])
                g.put(x, y - 1, pal['core'] if j == 1 else pal['edge'])
                g.put(x + 1, y + 1, pal['edge'])
    for k in range(6):
        if t >= 0:
            a = hashed(k, seed, 2) * 6.28
            g.put(cx + math.cos(a) * rmax * (0.6 + t * 0.35), cy + math.sin(a) * rmax * 0.3 - t * 2 - 3, pal['spark'])


def bubble(g, cx, cy, rx, h, f, pal, form=1.0, shimmer=0.0, seed=4):
    """A dome over the unit: a ring on the ground, a thin shell above it with a bright highlight, and sparkles that run round it."""
    top = cy - h * form
    ry = rx * 0.5
    g.ellipse(cx, cy, rx * form, ry * form, pal['edge'], thick=2.0)
    g.ellipse(cx, cy, rx * form, ry * form, pal['ring'], thick=1.0)
    for y in range(int(top - 2), int(cy + 2)):                                  # the shell: the dome's outline and a faint fill
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            dx = (x + 0.5 - cx) / max(0.5, rx * form)
            dy = (cy - y - 0.5) / max(0.5, h * form)
            d = math.hypot(dx, dy)
            if dy < 0 or d > 1.04:
                continue
            if d > 0.93:
                g.put(x, y, pal['ring'] if (x + y + int(shimmer * 3)) % 4 else pal['core'])
            elif d < 0.9 and dither(x, y, 0.1 + 0.05 * math.sin(shimmer * 6.28 + dx * 3)) and hashed(x, y, seed) < 0.5:
                g.put(x, y, pal['glow'])
    hx, hy = cx - rx * 0.45 * form, cy - h * 0.7 * form                         # the highlight, upper left
    for k in range(4):
        g.put(hx + k * 0.8, hy + k * 0.9, pal['core'])
    g.put(hx - 1, hy - 1, pal['core'])
    a = shimmer * 2 * math.pi                                                   # a glint running round the shell
    g.sparkle(cx + math.cos(a) * rx * form, cy - abs(math.sin(a)) * h * form, 1, pal['core'])


def climb(g, cx, cy, f, pal):
    """Rings rising up the unit from the ground, shrinking as they go, with sparkles."""
    for k in range(3):
        t = ((f / FRAMES) * 1.0 + k / 3.0) % 1.0
        y = cy - t * 26
        r = 12 * (1 - 0.35 * t)
        fade = 1 - smoothstep(0.65, 1.0, t)
        if fade > 0.05 and t >= 0.0:
            g.ellipse(cx, y, r, r * 0.5, pal['edge'], thick=2.2)
            g.ellipse(cx, y, r, r * 0.5, pal['ring'] if dither(k, f, fade) else pal['core'], thick=1.0)
    for k in range(5):
        a = k * 1.7 + 0.4
        yy = cy - ((f * 3 + k * 5) % 26)
        g.put(cx + math.cos(a) * 9, yy, pal['spark'])
        if (f + k) % 2 == 0:
            g.put(cx + math.cos(a) * 9, yy - 1, pal['ring'])


def dash(g, cx, cy, f, pal, direction):
    """Speed lines streaking back from where the unit is going, for NE (up and right) and SE (down and right); they stretch, then thin out."""
    sx = -1.0                                                                  # behind the unit is to the left, and up for SE, down for NE
    sy = 0.5 if direction == 'NE' else -0.5
    t = f / (FRAMES - 1)
    length = 4 + 22 * smoothstep(0, 0.5, t)
    fade = 1 - smoothstep(0.5, 1.0, t)
    for k in range(7):
        off = (k - 3) * 2.4
        y0 = cy - 12 + off * 0.7
        x0 = cx - 3 + (hashed(k, 1) - 0.5) * 6
        ln = length * (0.5 + 0.5 * hashed(k, 2))
        for j in range(int(ln)):
            u = j / max(1.0, ln)
            if dither(j + k, k, fade * (1 - 0.7 * u) + 0.1):
                c = pal['core'] if u < 0.3 else pal['ring'] if u < 0.65 else pal['edge']
                g.put(x0 + sx * j * 1.0, y0 + sy * j * 0.5, c)
                g.put(x0 + sx * j * 1.0, y0 + sy * j * 0.5 + 1, pal['edge'] if u < 0.5 else c)
    if f < 4:                                                                  # a puff of dust where it pushed off
        for k in range(5):
            a = k * 1.3
            g.put(cx - 4 + math.cos(a) * (2 + f * 1.4), cy + 1 + math.sin(a) * (1 + f * 0.5), 'r' if k % 2 else 't')


def make(kind, f):
    w, h, (ax, ay) = (LARGE if kind == 'rally' else SMALL)
    g = Grid(w, h)
    if kind == 'rally':
        pulse(g, ax, ay, 46, f, PALETTES['gold'], sparks=9, seed=2)
    elif kind == 'inspire':
        pulse(g, ax, ay, 22, f, PALETTES['yellow'], sparks=5, seed=5)
    elif kind == 'cleanse':
        pulse(g, ax, ay, 22, f, PALETTES['cleanse'], sparks=6, seed=6)
    elif kind.startswith('status-'):                                          # a status ring: two rings a half-cycle apart, so it loops with no gap
        pal = PALETTES[{'status-soaked': 'blue', 'status-shocked': 'storm', 'status-spored': 'green'}[kind]]
        for k, off in enumerate((0.0, 0.5)):
            pulse(g, ax, ay, 18, f, pal, sparks=3, seed=3 + k, t=((f / FRAMES) + off) % 1.0 * 0.92)
    elif kind == 'sever':
        pal = PALETTES['white']
        if f < 2:
            r = 8 + 6 * f
            g.ellipse(ax, ay, r, r * 0.5, pal['edge'], thick=2.6)
            g.ellipse(ax, ay, r, r * 0.5, pal['core'], thick=1.2)
            if f == 1:
                for k in range(5):
                    g.line(ax + math.cos(k * 1.26) * 12, ay + math.sin(k * 1.26) * 6, ax + math.cos(k * 1.26 + 0.3) * 15, ay + math.sin(k * 1.26 + 0.3) * 7.5, pal['glow'])
        else:
            shards(g, ax, ay, 14, f, pal, start=2)
    elif kind == 'ward-form':
        bubble(g, ax, ay, 17, 26, f, PALETTES['ward'], form=smoothstep(0, 3.5, f), shimmer=f / 8)
        if f < 3:
            r = 24 - 6 * f
            g.ellipse(ax, ay, r, r * 0.5, PALETTES['ward']['ring'], thick=1.4)
    elif kind == 'ward-hold':
        bubble(g, ax, ay, 17, 26, f, PALETTES['ward'], form=1.0, shimmer=f / 6)
    elif kind == 'ward-break':
        pal = PALETTES['ward']
        if f < 2:
            bubble(g, ax, ay, 17, 26, f, pal, form=1.0 + 0.04 * f, shimmer=f / 3)
            if f == 1:
                for k in range(6):
                    g.line(ax + (k - 2.5) * 5, ay - 20 + hashed(k, 1) * 6, ax + (k - 2.5) * 5 + 3, ay - 9, pal['core'])
        else:
            shards(g, ax, ay - 6, 17, f, pal, start=2, seed=8)
            shards(g, ax, ay - 16, 12, f, pal, start=2, seed=9)
    elif kind == 'climb':
        climb(g, ax, ay, f, PALETTES['climb'])
    elif kind in ('dash-ne', 'dash-se'):
        dash(g, ax, ay, f, PALETTES['white'], kind[-2:].upper())
    return g.lines()


KINDS = [
    # id, label, frames, fps, loops?
    ('rally', 'Rally ring (gold, radius 2)', FRAMES, FPS, False),
    ('inspire', 'Inspire ring (bright yellow)', FRAMES, FPS, False),
    ('cleanse', 'Cleanse ring (white-green)', FRAMES, FPS, False),
    ('sever', 'Sever (a white ring breaking)', FRAMES, FPS, False),
    ('ward-form', 'Ward - the bubble forming', 6, FPS, False),
    ('ward-hold', 'Ward - the bubble holding (loops)', 6, 8, True),
    ('ward-break', 'Ward - the bubble breaking', FRAMES, FPS, False),
    ('climb', 'Climb (light blue rings rising)', FRAMES, FPS, False),
    ('status-soaked', 'Soaked status (blue ring, loops)', FRAMES, 8, True),
    ('status-shocked', 'Shocked status (yellow ring, loops)', FRAMES, 8, True),
    ('status-spored', 'Spored status (green ring, loops)', FRAMES, 8, True),
    ('dash-ne', 'Dash NE (speed lines; NW is this flipped)', 6, 12, False),
    ('dash-se', 'Dash SE (speed lines; SW is this flipped)', 6, 12, False),
]


def build_assets():
    assets = []
    for kind, label, n, fps, loops in KINDS:
        w, h, (ax, ay) = (LARGE if kind == 'rally' else SMALL)
        assets.append(dict(category='Abilities', folder='abilities', id=f'ring-{kind}', label=label, kind='animation', place='ground', w=w, h=h, cols=n, rows=1, fps=fps,
                           anchor={'x': ax, 'y': ay}, fx={'family': 'ring', 'kind': kind, 'loops': loops}, frames=[make(kind, f) for f in range(n)]))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = []
    for kind, label, n, fps, loops in KINDS:
        w, h, (ax, ay) = (LARGE if kind == 'rally' else SMALL)
        plots = [(ax, ay)] if kind != 'rally' else [(ax + dx * 16, ay + dy * 8) for dx in range(-2, 3) for dy in range(-2, 3) if abs(dx) + abs(dy) <= 2 and (dx + dy) % 2 == 0] 
        if kind == 'rally':
            plots = [(ax + (i - j) * 16, ay + (i + j) * 8) for i in range(-2, 3) for j in range(-2, 3) if abs(i) + abs(j) <= 2]
        sheets.append(fx.save_preview('/tmp/_r.png', [make(kind, f) for f in range(n)], w, h, cols=8, scale=2, plots=plots, ground_tile=ground))
    if args.preview:
        W = max(s.width for s in sheets)
        out = Image.new('RGBA', (W, sum(s.height for s in sheets)), (36, 38, 56, 255))
        y = 0
        for s in sheets:
            out.alpha_composite(s, (0, y))
            y += s.height
        out.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
