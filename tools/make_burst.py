#!/usr/bin/env python3
"""Burst animations: the area effects that hit a spot, in five styles, each as a five-plot burst and as a single-plot tile.

The fire burst (make_fire.py) is the template: an effect starts on the middle plot, spreads to the four plots beside it, peaks on all five, and dies away, 8 frames. These
are the other bursts, each with its own motion and not just its own colour:

    blood    a fountain of blood: droplets thrown up and out in arcs, falling into a spreading dark pool
    spore    a green cloud: soft puffs that swell and drift up and sideways, with bright spores floating in them
    static   yellow-white lightning: jagged bolts strike down, crackle along the ground and arc between the plots
    rain     a downpour: blue streaks fall, splash on the ground in rings, and leave the plots wet
    dust     brown dust, low: a ring of puffs thrown out, flying chips, and cracks in the ground (small = a little puff for a shove)
    crimson  a deep red bolt that strikes a single plot (tile only)

Each style makes `burst-NAME` (five plots on the 80 x 56 cell of make_aoe.py, anchor (40, 38)) and `burst-NAME-tile` (one plot, a 32 x 56 cell, anchor (16, 44)), so a radius-2 burst,
a line of three for a wall, or any other shape is the tile placed on each plot.

    python3 tools/make_burst.py --preview previews/bursts.png      all of them, over ground tiles
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
import make_aoe as aoe  # noqa: E402
from fx import Grid, dither, hashed, smoothstep  # noqa: E402

FRAMES = 8
FPS = 8
TILE_W, TILE_H = 32, 56
TILE_ANCHOR = (16, 44)

DELAY = {'C': 0.0, 'NW': 1.2, 'NE': 1.2, 'SW': 1.2, 'SE': 1.2}
LIGHT_RAMP = ('t', 'C', 'b', 'a')


def envelope(delay, f):
    """How strong an effect is on a plot at frame f: it rises two frames after it starts, and everything fades over the last three frames."""
    age = f - delay
    if age < 0:
        return age, 0.0
    return age, (0.3 + 0.7 * smoothstep(0, 2.0, age)) * (1 - smoothstep(4.8, 7.6, f))


# --- dust ---------------------------------------------------------------------------
DUST = ('t', 'C', 'b', 'a')


def dust(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    prog = smoothstep(0, 5.0, age)
    for y in range(int(cy - 9), int(cy + 10)):                                  # a film of dust on the ground, and cracks
        for x in range(int(cx - 17), int(cx + 18)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.05) and dither(x, y, 0.3 * amp * size) and hashed(x, y, key) < 0.5:
                g.put(x, y, 'C' if hashed(x, y, 3) < 0.6 else 'b')
    for k in range(int(round(5 * amp))):                                        # cracks, fewer as the burst dies
        a = k * 1.26 + 0.4 + hashed(k, key) * 0.5
        length = (3 + 6 * prog) * size
        g.line(cx, cy, cx + math.cos(a) * length * 1.5, cy + math.sin(a) * length * 0.7, 'w' if k % 2 else 'g')
    puffs = []
    for k in range(7):                                                          # a ring of puffs thrown out and up, slowly
        a = k * 2 * math.pi / 7 + hashed(k, key) * 0.6
        r = (2 + 9 * prog) * size
        x = cx + math.cos(a) * r * 1.6
        y = cy + math.sin(a) * r * 0.8 - (1.5 + 5 * prog) * size
        puffs.append((y, x, (1.5 + 1.7 * prog) * size * (0.6 + 0.4 * amp) * (0.8 + 0.4 * hashed(k, key, 5))))
    for y, x, r in sorted(puffs):
        g.blob(x, y, r, DUST, ry=r * 0.9, edge=0.35, seed=key + int(x))
    for k in range(6):                                                          # chips flying, then lying where they land
        a = k * 1.05 + hashed(k, key, 9) * 0.5
        vx, vy = math.cos(a) * 1.8 * size, (2.4 + hashed(k, key, 2)) * size
        t = max(0.0, age - 0.4)
        x = cx + vx * t * 1.5
        y = cy - (vy * t - 0.55 * t * t * size)
        if y >= cy + math.sin(a) * 3:
            y = cy + math.sin(a) * 3 * 0.8
            if amp > 0.35:
                g.put(x, y, 'g')
        elif t > 0:
            g.put(x, y, 'a')
            g.put(x + 1, y, 'a')
            g.put(x + 1, y + 1, 'g')


# --- rain ---------------------------------------------------------------------------
RAIN = ('r', 'o', 'n', 'm')


def rain(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    for y in range(int(cy - 9), int(cy + 10)):                                  # the plot wet: a sheen of teal and light blue
        for x in range(int(cx - 17), int(cx + 18)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.04) and dither(x, y, 0.42 * amp) and hashed(x, y, 7 + key) < 0.55:
                g.put(x, y, 'q' if hashed(x, y, 1) < 0.7 else 'r')
    for k in range(3 if amp > 0.3 else 0):                                      # rings where the drops hit
        ox, oy = (hashed(k, key, 4) - 0.5) * 18, (hashed(k, key, 6) - 0.5) * 7
        t = (age * 0.9 + k * 1.7) % 4.0
        if t < 3.2:
            r = 1.0 + t * 2.3
            g.ellipse(cx + ox, cy + oy, r, r * 0.5, 'r' if t < 1.4 else 'o', thick=1.2)
    for k in range(int(round(9 * amp))):                                        # streaks falling, slanted a little, fewer as it stops
        x0 = cx + (hashed(k, key, 1) - 0.5) * 30
        speed = 7.0 + hashed(k, key, 8) * 2.0
        y = (cy - 34) + ((f * speed + hashed(k, key, 2) * 36) % 40)
        for j in range(4):
            g.put(x0 + (y - cy) * 0.12 - j * 0.12, y - j, ('r', 'o', 'n', 'm')[min(3, j)])
        if y > cy - 1 and y < cy + 6:
            g.put(x0, cy + 2, 'r')
            g.put(x0 + 2, cy + 1, 'r')
            g.put(x0 - 2, cy + 1, 'o')


# --- spore --------------------------------------------------------------------------
SPORE = ('z', 'A', 'B', 's')


def spore(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    for y in range(int(cy - 8), int(cy + 9)):                                   # a green stain on the ground
        for x in range(int(cx - 16), int(cx + 17)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.12) and dither(x, y, 0.4 * amp) and hashed(x, y, 3 + key) < 0.6:
                g.put(x, y, 'B' if hashed(x, y, 5) < 0.6 else 's')
    puffs = []
    for k in range(6):                                                          # soft puffs that swell and drift up and to the right
        ph = hashed(k, key, 1)
        x = cx + (ph - 0.5) * 16 + age * (0.9 + 0.5 * hashed(k, key, 2)) * 1.4
        y = cy - 3 - age * (1.5 + hashed(k, key, 3)) - ph * 6
        r = (2.2 + 2.6 * smoothstep(0, 4, age)) * (0.7 + 0.3 * amp) * (0.8 + 0.4 * hashed(k, key, 4))
        puffs.append((y, x, r))
    for y, x, r in sorted(puffs):
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                d = math.hypot((xx + 0.5 - x) / r, (yy + 0.5 - y) / (r * 0.9))
                d += (hashed(xx, yy, key) - 0.5) * 0.5
                if d <= 1.0 and dither(xx, yy, 0.25 + 0.85 * amp):
                    lit = -((xx + 0.5 - x) * 0.55 + (yy + 0.5 - y) * 0.83) / r
                    g.put(xx, yy, SPORE[0 if lit > 0.45 else 1 if lit > -0.2 else 2 if lit > -0.65 else 3])
    for k in range(9):                                                          # bright spores floating up through it
        a = hashed(k, key, 6) * 6.28
        t = age * 0.8 + hashed(k, key, 7) * 3
        x = cx + math.cos(a) * 11 + math.sin(t * 1.4 + k) * 2.5
        y = cy - 4 - (t * 2.4) % 16
        g.put(x, y, 't' if k % 3 == 0 else 'z')


# --- static -------------------------------------------------------------------------
def zig(g, x0, y0, x1, y1, f, key, core='t', halo='d', jag=3.0, steps=6):
    pts = [(x0, y0)]
    for i in range(1, steps):
        t = i / steps
        pts.append((x0 + (x1 - x0) * t + (hashed(i, f, key) - 0.5) * 2 * jag, y0 + (y1 - y0) * t + (hashed(i, f, key + 5) - 0.5) * jag * 0.4))
    pts.append((x1, y1))
    for a, b in zip(pts, pts[1:]):
        g.line(a[0] + 1, a[1], b[0] + 1, b[1], halo)
        g.line(a[0], a[1], b[0], b[1], core)


def static(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    for y in range(int(cy - 9), int(cy + 10)):                                  # a flash on the ground, flickering
        for x in range(int(cx - 17), int(cx + 18)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.05) and dither(x + f, y, 0.35 * amp * (0.6 + 0.8 * hashed(f, key))) and hashed(x, y, 2 + f) < 0.7:
                g.put(x, y, 'd' if hashed(x, y, 4) < 0.6 else 't')
    strikes = 2 if amp > 0.7 else 1
    for k in range(strikes):                                                    # a bolt down onto the plot, a different one every frame
        gx = cx + (hashed(f, key, k) - 0.5) * 14
        gy = cy + (hashed(f, key, k + 3) - 0.5) * 5
        if hashed(f, key, 9 + k) < 0.85 * min(1.0, amp * 1.8):
            zig(g, gx + (hashed(f, key, 11) - 0.5) * 8, cy - 30 - 4 * k, gx, gy, f, key + k)
            g.disc(gx, gy, 1.6, 't')
    for k in range(int(round(4 * amp))):                                        # crackle along the ground: short arcs between points on the plot, fewer as it dies
        a, b = hashed(f, key, 20 + k) * 6.28, hashed(f, key, 30 + k) * 6.28
        zig(g, cx + math.cos(a) * 12, cy + math.sin(a) * 5, cx + math.cos(b) * 12, cy + math.sin(b) * 5, f, key + 40 + k, core='d', halo='b', jag=1.6, steps=4)
    for k in range(int(round(6 * amp))):
        g.put(cx + (hashed(f, key, 50 + k) - 0.5) * 30, cy - hashed(f, key, 60 + k) * 18, 't' if k % 2 else 'd')


def static_link(g, a, b, amp, f):
    if amp > 0.5:
        zig(g, a[0], a[1], b[0], b[1], f, 77, core='t', halo='d', jag=1.8, steps=5)


# --- blood --------------------------------------------------------------------------
BLOOD = ('e', 'i', 'h', 'u')


def blood(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    pool = 4 + 9 * smoothstep(0, 5, age) * (0.6 + 0.4 * amp)
    for y in range(int(cy - 8), int(cy + 9)):                                   # a dark pool spreading over the plot
        for x in range(int(cx - 17), int(cx + 18)):
            d = math.hypot((x + 0.5 - cx) / pool, (y + 0.5 - cy) / (pool * 0.5))
            d += (hashed(x, y, key) - 0.5) * 0.35
            if d < 1.0 and fx.diamond_inside(cx, cy, x, y, shrink=0.0) and dither(x, y, 0.2 + 0.8 * amp):      # the pool thins out as the burst dies
                g.put(x, y, 'h' if d > 0.55 else 'i')
                if hashed(x, y, 8) < 0.07:
                    g.put(x, y, 'e')
    if age < 3.0:                                                               # a spurt from the middle
        h = (3 + 9 * math.sin(math.pi * min(1.0, age / 3.0))) * size
        for yy in range(int(h)):
            half = max(0.6, 2.2 - yy * 0.16)
            for xx in range(int(cx - half), int(cx + half) + 1):
                g.put(xx, cy - 1 - yy, BLOOD[0 if xx < cx - half * 0.3 else 1 if xx < cx + half * 0.4 else 2])
    for k in range(11):                                                         # droplets thrown out and up, in arcs
        a = k * 2.4 + hashed(k, key) * 0.8
        vx, vy = math.cos(a) * (1.4 + hashed(k, key, 3)), 3.2 + hashed(k, key, 5) * 2.2
        t = max(0.0, age - 0.3)
        x = cx + vx * t * 1.8
        y = cy - 2 - (vy * t - 0.62 * t * t)
        ground = cy + math.sin(a) * 4
        if t <= 0:
            continue
        if y < ground:
            g.put(x, y, 'e')
            g.put(x, y + 1, 'i')
            if hashed(k, key, 1) < 0.4:
                g.put(x, y - 1, 'c')
        elif amp > 0.3:
            g.put(x, ground, 'e')
            g.put(x + 1, ground, 'i')


# --- the crimson bolt (tile only) ----------------------------------------------------------
CRIMSON = ('j', 'e', 'i', 'h')


def crimson(g, cx, cy, age, amp, f, key, size=1.0):
    if age < 0:
        return
    if age < 1.0:                                                               # a red glow gathers above
        g.blob(cx, cy - 30, 2 + 3 * age, ('t', 'j', 'e', 'i'))
    elif age < 4.0:                                                             # the bolt strikes, thick and jagged, and flickers
        w = 2.6 - 0.35 * (age - 1)
        x = cx
        for yy in range(int(cy - 32), int(cy)):
            x += (hashed(yy, f, 3) - 0.5) * 2.2
            x = max(cx - 4, min(cx + 4, x))
            for xx in range(int(x - w), int(x + w) + 1):
                d = abs(xx + 0.5 - x) / max(w, 0.1)
                g.put(xx, yy, 't' if d < 0.35 else 'j' if d < 0.7 else 'e')
    for y in range(int(cy - 9), int(cy + 10)):                                  # the ground scorched red under it
        for x in range(int(cx - 17), int(cx + 18)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.1) and dither(x, y, 0.5 * amp) and hashed(x, y, 3) < 0.7:
                g.put(x, y, 'i' if hashed(x, y, 5) < 0.5 else 'h')
    if age >= 1.0:
        r = 2 + (age - 1) * 3.2
        g.ellipse(cx, cy, r, r * 0.5, 'j' if age < 3.5 else 'e', thick=1.6)    # a ring of force spreading over the plot
        for k in range(8):
            a = k * 0.8 + 0.3
            t = age - 1
            g.put(cx + math.cos(a) * (3 + t * 3.4), cy - 2 - t * 2.2 + t * t * 0.55 + math.sin(a) * 1.5, 'j' if k % 2 else 't')


# --- the styles -----------------------------------------------------------------------
STYLES = {
    # id: (label, draw, five-plot too?, link)
    'blood': ('Blood burst', blood, True, None),
    'spore': ('Spore cloud', spore, True, None),
    'static': ('Static surge', static, True, static_link),
    'rain': ('Downpour', rain, True, None),
    'dust': ('Dust burst', dust, True, None),
    'dust-small': ('Dust puff (small)', lambda *a: dust(*a, size=0.55), False, None),
    'crimson': ('Crimson bolt', crimson, False, None),
}


def render_five(style, f):
    label, draw, five, link = STYLES[style]
    g = Grid(aoe.CELL_W, aoe.CELL_H)
    for plot in aoe.DEPTH_ORDER:
        cx, cy = aoe.centre(plot)
        age, amp = envelope(DELAY[plot], f)
        draw(g, cx, cy, age, amp, f, 3 + len(plot) * 11 + ord(plot[0]))
    if link:
        age, amp = envelope(1.5, f)
        for plot in ('NW', 'NE', 'SW', 'SE'):
            link(g, aoe.centre('C'), aoe.centre(plot), amp, f)
    return g.lines()


def render_tile(style, f):
    label, draw, five, link = STYLES[style]
    g = Grid(TILE_W, TILE_H)
    age, amp = envelope(0.0, f)
    draw(g, TILE_ANCHOR[0], TILE_ANCHOR[1], age, amp, f, 5)
    return g.lines()


def build_assets():
    assets = []
    for style, (label, draw, five, link) in STYLES.items():
        common = dict(category='Abilities', folder='abilities', kind='animation', place='ground', rows=1, fps=FPS)
        if five:
            assets.append(dict(common, id=f'burst-{style}', label=f'{label} - five plots', w=aoe.CELL_W, h=aoe.CELL_H, cols=FRAMES,
                               anchor={'x': aoe.MIDDLE[0], 'y': aoe.MIDDLE[1]}, fx={'family': 'burst', 'style': style, 'shape': 'five-plot'},
                               frames=[render_five(style, f) for f in range(FRAMES)]))
        assets.append(dict(common, id=f'burst-{style}-tile', label=f'{label} - one plot', w=TILE_W, h=TILE_H, cols=FRAMES,
                           anchor={'x': TILE_ANCHOR[0], 'y': TILE_ANCHOR[1]}, fx={'family': 'burst', 'style': style, 'shape': 'tile'},
                           frames=[render_tile(style, f) for f in range(FRAMES)]))
    return assets


def main():
    import argparse
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write every burst here, over ground tiles')
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = []
    for style, (label, draw, five, link) in STYLES.items():
        if five:
            frames = [render_five(style, f) for f in range(FRAMES)]
            sheets.append(fx.save_preview('/tmp/_b.png', frames, aoe.CELL_W, aoe.CELL_H, cols=FRAMES, scale=2, plots=[aoe.centre(p) for p in aoe.DEPTH_ORDER], ground_tile=ground))
        else:
            frames = [render_tile(style, f) for f in range(FRAMES)]
            sheets.append(fx.save_preview('/tmp/_b.png', frames, TILE_W, TILE_H, cols=FRAMES, scale=2, plots=[TILE_ANCHOR], ground_tile=ground))
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
