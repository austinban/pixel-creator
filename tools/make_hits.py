#!/usr/bin/env python3
"""Hit flashes: a short, punchy flash played on the unit that was struck, for the shots that need their own hit (the ranger's).

They share make_burst.py's one-plot tile (a 32 x 56 cell, anchor (16, 44), 8 frames at 8 fps), but they are hits, not bursts: everything happens in the first four frames
and is gone by frame 6, with only a speck or two left after that. A unit's chest is about ten pixels above the anchor, so that is where a flash centres.

    crit     a sharp white-gold star with four long rays and sparks thrown out (Headshot)
    impact   a heavy blow: a white flash, a ring slammed into the ground, a shockwave and dust (Called Shot)
    streak   a fast cyan-white streak passing straight through, left to right, with speed lines (Piercing Shot)
    nick     a small red slash low on the legs and a few drops of blood falling (Hamstring)

    python3 tools/make_hits.py --preview previews/hits.png      all of them, over ground tiles
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
from fx import Grid, dither, hashed, smoothstep  # noqa: E402
from make_burst import FPS, FRAMES, TILE_ANCHOR, TILE_H, TILE_W  # noqa: E402

CHEST = 10                                          # how far above the anchor a struck unit's chest is
DUST = ('t', 'C', 'C', 'b')


def punch(f):
    """How strong a hit is at frame f: full at once, holding for two frames, gone by frame 6."""
    return 1.0 - smoothstep(2.0, 5.6, f)


# --- crit -----------------------------------------------------------------------------
def ray(g, x, y, dx, dy, length, core, edge):
    """A ray tapering from three pixels wide at the root to one at the tip: a white core, gold sides."""
    n = int(round(length))
    for k in range(n + 1):
        px, py = x + dx * k, y + dy * k
        g.put(px, py, core if k < n * 0.7 else edge)
        if k < n * 0.45:
            g.put(px + dy, py + dx, edge)
            g.put(px - dy, py - dx, edge)


def crit(g, cx, cy, f, key):
    amp = punch(f)
    sy = cy - CHEST - 2
    reach = (5, 14, 11, 6, 3, 0, 0, 0)[f]                                      # the four long rays shoot out, then pull back in
    if reach:
        for dx, dy in ((1, 0), (-1, 0)):
            ray(g, cx, sy, dx, dy, reach, 't', 'd')
        for dx, dy in ((0, 1), (0, -1)):
            ray(g, cx, sy, dx, dy, reach * 0.8, 't', 'd')
        short = reach * 0.4                                                     # short diagonals between them
        for sx_, sy_ in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            for k in range(1, int(short) + 1):
                g.put(cx + sx_ * k, sy + sy_ * k, 'b' if k > short * 0.6 else 'd')
    core = (2.0, 3.2, 2.4, 1.4, 0.0, 0, 0, 0)[f]
    if core:
        g.disc(cx + 0.5, sy + 0.5, core, 't')
    if f == 1:
        g.ellipse(cx + 0.5, sy + 0.5, 6.5, 6.5, 'd', thick=1.0)                  # a thin gold ring at the peak
    for k in range(8):                                                          # sparks thrown out, slowing, falling a little
        a = k * math.pi / 4 + math.pi / 8 + (hashed(k, key) - 0.5) * 0.5
        t = f + 0.5
        if t < 1.0 or amp <= 0.02:
            continue
        d = 3 + 10 * smoothstep(0, 4.5, t) * (0.7 + 0.5 * hashed(k, key, 2))
        x = cx + math.cos(a) * d
        y = sy + math.sin(a) * d * 0.8 + 0.35 * t * t
        if f <= 2:
            g.sparkle(round(x), round(y), 1, 'd', 't')
        elif hashed(k, f, key) < amp + 0.3:
            g.put(x, y, 'd' if f < 4 else 'b')
    if f >= 5:                                                                  # one last glint
        g.put(cx + 7 - f, sy - 9 + f, 'b' if f < 7 else 'a')


# --- impact ---------------------------------------------------------------------------
def impact(g, cx, cy, f, key):
    amp = punch(f)
    sy = cy - CHEST
    if f <= 2:                                                                  # the white flash on the body
        r = (2.5, 4.0, 2.2)[f]
        for k in range(8):                                                      # a jagged white star, not a ball
            a = k * math.pi / 4 + 0.2
            ln = r * (1.9 if k % 2 == 0 else 1.3)
            g.line(cx, sy, cx + math.cos(a) * ln, sy + math.sin(a) * ln * 0.9, 'd' if f == 2 else 't')
        g.disc(cx + 0.5, sy + 0.5, r, 't')
        if f == 1:
            for k in range(6):
                a = k * math.pi / 3 + 0.3
                g.line(cx + math.cos(a) * 6, sy + math.sin(a) * 6, cx + math.cos(a) * 10, sy + math.sin(a) * 9, 't')
    ring = (4.0, 9.0, 12.5, 14.5, 15.5, 0, 0, 0)[f]                             # the ring slammed into the ground, spreading flat
    if ring:
        thick = (2.4, 2.4, 1.8, 1.2, 1.0)[f]
        c = ('t', 't', 't', 'C', 'b')[f]
        g.ellipse(cx, cy, ring, ring * 0.5, c, thick=thick)
        if f >= 1:                                                              # a second, fainter shockwave inside it
            inner = ring * 0.6
            g.ellipse(cx, cy, inner, inner * 0.5, 'C' if f < 3 else 'b', thick=1.0)
    if 1 <= f <= 2:                                                             # the ground under it darkens for a moment
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 10, cx + 11):
                if fx.diamond_inside(cx, cy, x, y, half_w=10, half_h=5) and dither(x, y, 0.35) and g.get(x, y) == '.':
                    g.put(x, y, 'g')
    puffs = []
    for k in range(6):                                                          # dust thrown out low, round the ring
        if f < 1 or amp <= 0.05:
            continue
        a = k * math.pi / 3 + hashed(k, key) * 0.6
        prog = smoothstep(0, 4.0, f)
        r = 6 + 8 * prog
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * 0.5 - 1 - 2 * prog
        puffs.append((y, x, (1.0 + 1.2 * prog) * (0.5 + 0.5 * amp)))
    for y, x, r in sorted(puffs):
        g.blob(x, y, r, DUST, edge=0.4, seed=key + int(x))
    for k in range(5):                                                          # grit flung up
        t = f - 0.5
        if t <= 0:
            continue
        x = cx + (hashed(k, key, 3) - 0.5) * 22
        y = cy - (3.4 * t - 0.8 * t * t) * 1.6
        if y < cy + 2:
            g.put(x, y, 'g')
    if f >= 5:                                                                  # a few specks settling
        for k in range(3):
            g.put(cx - 8 + k * 8 + (k == 1) * 1, cy + 2 - (k % 2), 'C' if f == 5 else 'b')


# --- streak ---------------------------------------------------------------------------
def streak(g, cx, cy, f, key):
    sy = cy - CHEST - 1
    head = (6, 20, 34, 46, 0, 0, 0, 0)[f]                                       # the tip of the shot, left to right, gone off the edge by frame 3
    tail = (0, 0, 8, 22, 0, 0, 0, 0)[f]                                        # where its tail has got to
    if head:
        h = head
        for x in range(int(tail), min(int(h), TILE_W)):
            age = (h - x) / 20.0                                                # 0 at the tip, 1 twenty pixels behind
            if age > 1.0 and not dither(x, sy, 1.6 - age):
                continue
            g.put(x, sy, 't' if age < 0.45 else 'o')
            if age < 0.7:
                g.put(x, sy - 1, 'o' if age < 0.35 else 'n')
                g.put(x, sy + 1, 'o')
            if age < 0.25:
                g.put(x, sy - 2, 'n')
                g.put(x, sy + 2, 'n')
        if head and head < TILE_W:
            g.put(head, sy, 't')
            g.put(head + 1, sy, 't')
    if 1 <= f <= 3:                                                             # the burst where it passes through the body
        r = (0, 3.0, 2.2, 1.2)[f]
        g.disc(cx + 0.5, sy + 0.5, r, 't')
        g.put(cx, sy - r - 2, 'o'), g.put(cx, sy + r + 2, 'o')
        if f == 1:
            for dy in (-1, 1):
                g.line(cx + 1, sy + dy * 2, cx + 6, sy + dy * 6, 'o')
    for k in range(5):                                                          # speed lines above and below, trailing it
        if f > 4:
            break
        y = sy + (-6, -4, 3, 5, 7)[k]
        length = 4 + int(6 * hashed(k, key))
        x0 = -4 + f * 10 + int(hashed(k, key, 2) * 10) - 6
        if f >= 3:
            length = max(1, length - (f - 2) * 3)
            x0 += 6
        for x in range(x0, x0 + length):
            g.put(x, y, 'n' if x < x0 + length // 2 else 'o')
    if f >= 4:                                                                  # a fleck of light where it went through
        g.put(cx + 2 + f, sy, 'o' if f < 6 else 'n')
        if f == 4:
            g.put(cx + 5, sy - 1, 'n'), g.put(cx + 5, sy + 1, 'n')


# --- nick -----------------------------------------------------------------------------
def nick(g, cx, cy, f, key):
    sx, sy = cx + 1, cy - 5                                                     # low, on the legs
    drawn = (0.6, 1.0, 1.0, 1.0, 0.6, 0.0, 0.0, 0.0)[f]
    n = 10
    for i in range(int(n * drawn) + 1):                                         # a short slash, upper right to lower left
        x, y = sx + 5 - i, sy - 5 + i
        mid = 1 <= i <= n - 2
        if f <= 1:
            g.put(x, y, 't')                                                    # a white edge the moment it cuts
            g.put(x + 1, y, 'e')
            if mid:
                g.put(x + 1, y + 1, 'i')
        else:
            g.put(x, y, 'e' if f <= 3 else 'i')
            g.put(x + 1, y, 'i' if f <= 3 else 'h')
            if mid and f <= 3:
                g.put(x + 1, y + 1, 'h')
    if f == 0:
        g.put(sx + 7, sy - 7, 't')
        g.put(sx - 6, sy + 6, 't')
    for k in range(5):                                                          # drops of blood, falling and landing
        start = 0.4 + k * 0.45
        t = f - start
        if t < 0:
            continue
        x0 = sx + 2 - k * 1.4 + (hashed(k, key) - 0.5) * 2
        x = x0 + (k - 2) * 0.6 * t
        y = sy - 2 + k + (0.6 + 0.9 * t) * t * 1.4
        floor = cy + 1 + (k % 3) - 1
        if y >= floor:                                                          # a small dark splat where it lands
            if f <= 6 or k < 2:
                g.put(x, floor, 'h')
                if f <= 5:
                    g.put(x + 1, floor, 'i')
        else:
            g.put(x, y, 'e' if t < 1.5 else 'i')
            g.put(x + 1, y, 'i')
            g.put(x, y - 1, 'e')


STYLES = {
    # id: (label, draw)
    'crit': ('Critical hit', crit),
    'impact': ('Heavy impact', impact),
    'streak': ('Piercing streak', streak),
    'nick': ('Nick', nick),
}


def render_tile(style, f):
    label, draw = STYLES[style]
    g = Grid(TILE_W, TILE_H)
    draw(g, TILE_ANCHOR[0], TILE_ANCHOR[1], f, 5)
    return g.lines()


def build_assets():
    assets = []
    for style, (label, draw) in STYLES.items():
        assets.append(dict(category='Abilities', folder='abilities', kind='animation', place='ground', rows=1, fps=FPS,
                           id=f'burst-{style}-tile', label=f'{label} - one plot', w=TILE_W, h=TILE_H, cols=FRAMES,
                           anchor={'x': TILE_ANCHOR[0], 'y': TILE_ANCHOR[1]}, fx={'family': 'burst', 'style': style, 'shape': 'tile'},
                           frames=[render_tile(style, f) for f in range(FRAMES)]))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write every hit here, over ground tiles')
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = [fx.save_preview('/tmp/_h.png', [render_tile(style, f) for f in range(FRAMES)], TILE_W, TILE_H, cols=FRAMES, scale=3, plots=[TILE_ANCHOR], ground_tile=ground)
              for style in STYLES]
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
