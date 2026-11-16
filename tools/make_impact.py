#!/usr/bin/env python3
"""Impact animations: the abilities and supplies that had to borrow another's effect (the vine, the fire burst, the heal petals), each with its own motion.

They follow make_burst.py exactly: an effect starts on its plot, swells for two frames and fades over the last three, 8 frames at 8 fps; a five-plot sheet on the 80 x 56 cell of
make_aoe.py (anchor (40, 38)) and a one-plot tile on a 32 x 56 cell (anchor (16, 44)), so any area is the tile on each of its cells.

    explosion  a bomb going off: a white flash, a fireball that swells and rolls upward into smoke, chips thrown out, the ground scorched (Fire Bomb, Blast Charge)
    grasp      cracked earth and grey-green hands clawing up out of it, closing and sinking again (the Zombie's Grasp)
    mindspore  violet spores spiralling up round the plot, an eye opening in them for a moment (Mind Spore, Dominion, Sap)
    potion     a drink taking: rose bubbles rising from the feet, popping into small sparkles (Healing and Greater Draught)
    elixir     the same in gold, fuller (Grand Elixir)
    sweep      a scythe's one stroke across the whole cone in front of the attacker (Scythe Sweep): `sweep-scythe-ne` and `-se` on a 96 x 96 cell anchored at
               the attacker's feet, mirrored for NW and SW, as Dash is
    wave       a shout or a howl: arcs of force rising and spreading over the plot (Bark; played the same way, so it fans out)

    python3 tools/make_impact.py --preview previews/impacts.png      all of them, over ground tiles
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx  # noqa: E402
import make_aoe as aoe  # noqa: E402
from fx import Grid, dither, hashed, smoothstep  # noqa: E402
from make_burst import DELAY, FPS, FRAMES, TILE_ANCHOR, TILE_H, TILE_W, envelope  # noqa: E402

FIRE = ('t', 'd', 'b', 'a')
SMOKE = ('p', 'l', 'k', 'x')
SKIN = ('r', 'q', 's', 'D')


def scorch(g, cx, cy, amp, level, key, tones=('k', 'x')):
    for y in range(int(cy - 9), int(cy + 10)):
        for x in range(int(cx - 17), int(cx + 18)):
            if fx.diamond_inside(cx, cy, x, y, shrink=0.06) and dither(x, y, level * amp) and hashed(x, y, key) < 0.65:
                g.put(x, y, tones[0] if hashed(x, y, key + 1) < 0.6 else tones[1])


# --- explosion ------------------------------------------------------------------------
def explosion(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    scorch(g, cx, cy, amp, 0.55, key)
    if age < 1.2:                                                               # the flash: a white star on the ground
        r = (3 + 5 * age) * size
        g.ellipse(cx, cy, r * 1.6, r * 0.8, 'd', thick=1.6)
        g.blob(cx, cy - 3, 2.5 + 3 * age, ('t', 't', 'd', 'b'))
    rise = smoothstep(0, 5.0, age)
    fire = 1.0 - smoothstep(1.5, 4.0, age)
    r = (3.5 + 4.5 * smoothstep(0, 2.0, age)) * size
    for k in range(5):                                                          # the fireball, rolling up into smoke
        a = k * 2 * math.pi / 5 + hashed(k, key) * 0.8
        x = cx + math.cos(a) * r * 0.9
        y = cy - 4 - r * 0.6 - rise * 12 * size + math.sin(a) * r * 0.45
        rr = r * (0.55 + 0.25 * hashed(k, key, 3)) * (0.35 + 0.65 * amp)       # the smoke thins and shrinks as it fades
        if amp > 0.22:
            g.blob(x, y, rr, FIRE if hashed(k, key, 7) < fire else SMOKE, edge=0.4, seed=key + k)
    if fire > 0.2:
        g.blob(cx, cy - 5 - rise * 10 * size, r * 0.75, FIRE, edge=0.3, seed=key)
    for k in range(8):                                                          # chips thrown out in arcs
        a = k * 0.79 + hashed(k, key, 9) * 0.4
        t = age
        x = cx + math.cos(a) * (2 + t * 4.2) * 1.4
        y = cy - (3.0 * t - 0.45 * t * t) * 2.2 + math.sin(a) * t * 1.6
        if y < cy + 4:
            g.put(x, y, 'g')
            g.put(x + 1, y, 'a' if k % 2 else 'O')


# --- grasp ----------------------------------------------------------------------------
def hand(g, x, y, up, open_, flip):
    """A hand and forearm reaching up and out `up` pixels from (x, y), leaning away from the middle: a two-wide forearm with an outline on its shaded side, a palm,
    three fingers with gaps between them and a thumb, spread wide (`open_` 1) or hooked into a claw (0). `flip` leans and mirrors it the other way."""
    if up <= 1:
        return
    s = -1 if flip else 1
    lean = 0.35
    top_y = y - up
    for k in range(int(up)):                                                    # the forearm, leaning out as it rises
        xx = x + s * lean * k
        g.put(xx, y - k, SKIN[0] if s > 0 else SKIN[1])
        g.put(xx + 1, y - k, SKIN[1] if s > 0 else SKIN[0])
        g.put(xx + 2, y - k, 'O')
    hx = x + s * lean * up
    for dy in range(3):                                                         # the palm, three wide
        for dx in range(-1, 3):
            g.put(hx + dx, top_y - dy, 'O' if dx == 2 else SKIN[0] if dx == -1 else SKIN[1])
    tip = top_y - 3
    for dx in (-1, 1, 3):                                                       # three fingers, a gap between each
        if open_ > 0.5:
            for j in range(3):
                g.put(hx + dx + (dx - 1) * 0.3 * j, tip - j, SKIN[0] if j == 2 else SKIN[1])
        else:
            g.put(hx + dx, tip, SKIN[1])
            g.put(hx + dx + (1 if dx < 1 else -1), tip + 1, SKIN[0])
    g.put(hx - 2 if s > 0 else hx + 4, top_y - 1, SKIN[0])                       # the thumb
    g.put(hx - 3 if s > 0 else hx + 5, top_y - 2 if open_ > 0.5 else top_y - 1, SKIN[0])


def grasp(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    for k in range(5):                                                          # the earth cracking open
        a = k * 1.26 + hashed(k, key) * 0.5
        length = 3 + 6 * smoothstep(0, 2.0, age)
        g.line(cx, cy, cx + math.cos(a) * length * 1.5, cy + math.sin(a) * length * 0.7, 'g' if k % 2 else 'O')
    scorch(g, cx, cy, amp, 0.3, key, tones=('g', 'a'))
    reach = 11 * smoothstep(0.3, 2.2, age) * (1 - smoothstep(5.0, 7.4, f))
    grip = smoothstep(2.2, 3.4, age)
    for i, (dx, dy, scale) in enumerate(((-6, 1, 0.85), (4, -1, 1.0))):
        hand(g, cx + dx, cy + dy, reach * scale, 1.0 - grip, i == 0)
    for k in range(4):                                                          # clods thrown up as they break out
        t = max(0.0, age - 0.2)
        x = cx + (hashed(k, key, 4) - 0.5) * 18
        y = cy - (4.0 * t - 0.9 * t * t)
        if t > 0 and y < cy:
            g.put(x, y, 'g')
            g.put(x + 1, y, 'a')


# --- mind spores ----------------------------------------------------------------------
def mindspore(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    scorch(g, cx, cy, amp, 0.12, key, tones=('u', 'v'))
    for k in range(14):                                                         # a spiral of spores rising round the plot
        t = age * 0.9 + k * 0.42
        a = t * 1.9 + hashed(k, key) * 6.3
        r = 4 + 8 * ((k * 0.37 + age * 0.15) % 1.0)
        x = cx + math.cos(a) * r * 1.3
        y = cy - 2 - ((k * 3 + age * 4.2) % 22) + math.sin(a) * r * 0.4
        c = ('v', 'y', 'u')[k % 3]
        g.put(x, y, c)
        if k % 4 == 0:
            g.put(x + 1, y, 'v')
            g.put(x, y - 1, 't' if amp > 0.6 else 'v')
    open_ = smoothstep(1.8, 2.8, age) * (1 - smoothstep(4.2, 5.4, age))
    if open_ > 0.05:                                                            # the eye
        ey = cy - 15
        half = 5 * open_ + 1
        for x in range(int(cx - 6), int(cx + 7)):
            h = half * (1 - ((x + 0.5 - cx) / 6.5) ** 2)
            if h > 0.3:
                g.put(x, ey - h, 'u')
                g.put(x, ey + h, 'u')
                for y in range(int(ey - h + 1), int(ey + h)):
                    g.put(x, y, 't')
        if open_ > 0.4:
            g.disc(cx, ey, 1.6, 'w')
            g.put(cx, ey, 'y')


# --- potion and elixir ----------------------------------------------------------------
def drink(g, cx, cy, age, amp, f, key, tones, many=1.0):
    if amp <= 0.02:
        return
    g.ellipse(cx, cy, 6 + 5 * smoothstep(0, 3.0, age), 3 + 2.5 * smoothstep(0, 3.0, age), tones[1] if age < 3 else tones[2], thick=1.2)
    for k in range(int(10 * many)):                                             # bubbles rising from the feet, wobbling, then popping
        t = age - hashed(k, key) * 2.5
        if t < 0:
            continue
        x = cx + (hashed(k, key, 3) - 0.5) * 16 + math.sin(t * 2.4 + k) * 1.2
        y = cy - t * 4.2
        if t < 3.2:
            if hashed(k, key, 5) < 0.4:
                g.put(x, y, tones[0])
                g.put(x + 1, y, tones[1])
                g.put(x, y + 1, tones[1])
                g.put(x + 1, y + 1, tones[2])
            else:
                g.put(x, y, tones[1])
        elif t < 4.0:
            g.sparkle(x, y, 1, tones[0], 't')


def potion(g, cx, cy, age, amp, f, key, size=1.0):
    drink(g, cx, cy, age, amp, f, key, ('c', 'j', 'e'))


def elixir(g, cx, cy, age, amp, f, key, size=1.0):
    drink(g, cx, cy, age, amp, f, key, ('t', 'd', 'b'), many=1.6)
    if 1.0 < age < 4.0:
        g.sparkle(cx, cy - 16, 3, 'd', 't')


# --- scythe slash ---------------------------------------------------------------------
# --- scythe sweep (one stroke over the whole cone) -------------------------------------
SWEEP_W, SWEEP_H = 96, 96
SWEEP_ANCHOR = (24, 56)                                                         # the attacker's feet
SWEEP_FPS = 10
# The cone, in the attacker's own terms: `along` the way it faces, `across` to its right. Moving one cell along x is (16, 8) on the screen, along y (-16, 8).
SWEEP_DIRECTIONS = {'se': ((1, 0), (0, 1)), 'ne': ((0, -1), (1, 0))}


def sweep_point(direction, u, v):
    """Where a point `u` cells ahead and `v` cells to the side of the attacker sits in the sheet, on the ground."""
    (ax, ay), (bx, by) = SWEEP_DIRECTIONS[direction]
    i, j = ax * u + bx * v, ay * u + by * v
    return SWEEP_ANCHOR[0] + 16 * (i - j), SWEEP_ANCHOR[1] + 8 * (i + j)


def render_sweep(direction, f):
    """A scythe's one stroke across the whole cone (the cell in front and the three beyond it): a crescent two cells out from the attacker, swung from its
    left to its right over three frames, a white edge and a cyan trail lifted a little off the ground, then fading back along itself, with cut grass thrown."""
    g = Grid(SWEEP_W, SWEEP_H)
    age = float(f)
    drawn = smoothstep(0.0, 2.6, age)
    gone = smoothstep(3.0, 6.0, age)
    for i in range(140):
        t = i / 139.0
        if t > drawn or t < gone:
            continue
        theta = (-0.95 + 1.9 * t)                                               # from the attacker's left to its right
        radius = 1.75 + 0.25 * math.sin(math.pi * t)
        x, y = sweep_point(direction, radius * math.cos(theta), radius * math.sin(theta))
        lift = 7 + 3 * math.sin(math.pi * t)
        width = max(1, int(round(5 * math.sin(math.pi * t) * (1 - gone))))
        fresh = drawn - t
        for k in range(width):
            c = 't' if k == 0 or fresh < 0.12 else 'o' if k < width - 1 else 'n'
            g.put(x, y - lift + k, c)
        g.put(x, y - lift + width, 'O')
    for k in range(10):                                                         # grass and dust thrown up behind the blade
        t = age - 1.0 - (k % 5) * 0.25
        if t <= 0 or t > 4:
            continue
        theta = -0.9 + 1.8 * (k / 9.0)
        x, y = sweep_point(direction, 1.6 * math.cos(theta), 1.6 * math.sin(theta))
        y -= (3.0 * t - 0.6 * t * t) * 2.0
        g.put(x, y, 'z' if k % 2 else 'A')
        g.put(x + 1, y - 1, 'A' if k % 3 else 'C')
    return g.lines()


# --- wave -----------------------------------------------------------------------------
def wave(g, cx, cy, age, amp, f, key, size=1.0):
    if amp <= 0.02:
        return
    for ring in range(3):                                                       # arcs of force, each a little later, rising and spreading
        t = age - ring * 0.7
        if t <= 0 or t > 3.6:
            continue
        r = 3 + t * 4.0
        lift = t * 2.0
        c = 't' if t < 1.2 else 'd' if t < 2.4 else 'b'
        for i in range(-60, 61):
            a = i / 60.0 * 1.15
            x = cx + math.sin(a) * r * 1.5
            y = cy - 3 - lift - math.cos(a) * r * 0.5
            g.put(x, y, c)
            if t < 2.4:
                g.put(x, y + 1, 'b' if t > 1.2 else 'd')
    for k in range(4):                                                          # dust kicked up on the plot
        x = cx + (hashed(k, key) - 0.5) * 20
        if dither(x, cy, 0.5 * amp):
            g.put(x, cy + (hashed(k, key, 2) - 0.5) * 6, 'C')


STYLES = {
    # id: (label, draw, five-plot too?)
    'explosion': ('Explosion', explosion, True),
    'grasp': ('Grasping hands', grasp, False),
    'mindspore': ('Mind spores', mindspore, True),
    'potion': ('Potion', potion, False),
    'elixir': ('Elixir', elixir, False),
    'wave': ('Force wave', wave, False),
}


def render_five(style, f):
    label, draw, five = STYLES[style]
    g = Grid(aoe.CELL_W, aoe.CELL_H)
    for plot in aoe.DEPTH_ORDER:
        cx, cy = aoe.centre(plot)
        age, amp = envelope(DELAY[plot], f)
        draw(g, cx, cy, age, amp, f, 3 + len(plot) * 11 + ord(plot[0]))
    return g.lines()


def render_tile(style, f):
    label, draw, five = STYLES[style]
    g = Grid(TILE_W, TILE_H)
    age, amp = envelope(0.0, f)
    draw(g, TILE_ANCHOR[0], TILE_ANCHOR[1], age, amp, f, 5)
    return g.lines()


def build_assets():
    assets = []
    for direction in SWEEP_DIRECTIONS:
        assets.append(dict(category='Abilities', folder='abilities', kind='animation', place='ground', rows=1, fps=SWEEP_FPS,
                           id=f'sweep-scythe-{direction}', label=f'Scythe sweep ({direction.upper()}; mirrored for the other side)', w=SWEEP_W, h=SWEEP_H, cols=FRAMES,
                           anchor={'x': SWEEP_ANCHOR[0], 'y': SWEEP_ANCHOR[1]}, fx={'family': 'sweep', 'style': 'scythe', 'shape': 'cone'},
                           frames=[render_sweep(direction, f) for f in range(FRAMES)]))
    for style, (label, draw, five) in STYLES.items():
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
    parser.add_argument('--preview', type=Path, help='write every impact here, over ground tiles')
    args = parser.parse_args()
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    sheets = []
    for style, (label, draw, five) in STYLES.items():
        if five:
            frames = [render_five(style, f) for f in range(FRAMES)]
            sheets.append(fx.save_preview('/tmp/_i.png', frames, aoe.CELL_W, aoe.CELL_H, cols=FRAMES, scale=3, plots=[aoe.centre(p) for p in aoe.DEPTH_ORDER], ground_tile=ground))
        frames = [render_tile(style, f) for f in range(FRAMES)]
        sheets.append(fx.save_preview('/tmp/_i.png', frames, TILE_W, TILE_H, cols=FRAMES, scale=3, plots=[TILE_ANCHOR], ground_tile=ground))
    for direction in SWEEP_DIRECTIONS:
        frames = [render_sweep(direction, f) for f in range(FRAMES)]
        plots = [sweep_point(direction, 0, 0)] + [sweep_point(direction, u, v) for u, v in ((1, 0), (2, -1), (2, 0), (2, 1))]
        sheets.append(fx.save_preview('/tmp/_i.png', frames, SWEEP_W, SWEEP_H, cols=FRAMES, scale=2, plots=[(int(x), int(y)) for x, y in plots], ground_tile=ground))
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
