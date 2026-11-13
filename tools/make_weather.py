#!/usr/bin/env python3
"""Weather and fog: screen-space overlays that loop in time and tile in both directions, and a few small splash and ripple decals to go with the rain.

THE FORM. The art is made of opaque palette pixels (the game's own notes say overlays cannot blend per pixel), so softness is made two ways: a pale, sparse, DITHERED
picture (an ordered 4 x 4 dither of a smooth field, in two or three roles from dim to bright), and the GAME drawing the whole layer at an opacity (and, for light, with an
additive blend). Every overlay is one animation of `frames` pictures, each `tile` pixels, empty (transparent) wherever there is nothing. Two kinds of motion are baked in:

    particles   (rain, embers, petals) fall or rise by a whole number of tiles over the loop, so the last frame runs straight into the first, and sway or flutter
                with a sine that comes back to where it started
    fields      (fog, haze, mist) are made of a few cosine waves with whole wave numbers, so they tile; the waves' phases swing back and forth rather than run, so a field
                billows and shifts in place and the loop has no seam; the DRIFT is the game's: scroll the tile at a few pixels a second (`scroll`, below)

Draw each one by REPEATING the tile over the whole view (texture repeat / a tiled sprite), in screen space (not the world), with the frames played at `fps`, at a whole
number of screen pixels per step, above the map and its props and below the UI. The pixels are opaque: the layer's opacity is the game's, per the range given.

    id                       tile         frames  fps   blend    opacity     scroll px/s   what it is
    weather-rain-light       128 x 128    8       12    normal   0.35-0.60   none          a few short streaks falling down and to the left (1 across per 3 down)
    weather-rain-heavy       128 x 128    8       12    normal   0.50-0.85   none          many longer streaks, the near ones two wide
    weather-rain-ripples     128 x 128    8       8     normal   0.45-0.90   none          tiny flat rings opening and fading on the ground: for the GROUND layer, under units and props
    weather-fog-light        128 x 128    12      6     normal   0.25-0.50   (6, 2)        thin drifting banks, a sixth of the tile covered
    weather-fog-dense        128 x 128    12      6     normal   0.40-0.70   (4, 1)        thick banks, a third covered
    weather-spore-haze       128 x 128    12      8     add      0.50-1.00   (-3, -2)      the corruption's spores: lime, mint and magenta motes looping in the air over a faint green haze
    weather-embers           128 x 128    12      10    add      0.60-1.00   none          embers and ash rising and swaying
    weather-petals           128 x 128    12      8     normal   0.80-1.00   (-8, 0)       petals and a few leaves falling and fluttering
    weather-mist-low         128 x 64     12      6     normal   0.30-0.60   (5, 0)        flat bands of mist for water and graves, thickest across the middle of the tile

Why those numbers: the rain's drop falls 48 pixels a frame down and 16 left (three tiles down for one across over the 8 frames), a streak of 6 to 13 pixels, so a drop is
drawn once a frame and the eye joins them; the ripples last 4 of the 8 frames, each starting at its own frame; fog moves at the pace of its scroll, not its frames; the
embers and petals go once through the tile (128 pixels) in 12 frames, about 85 pixels a second at 8 fps. `blend: add` is for light that should glow on a dark map (the
roles are bright and saturated for it); a game with no additive blend can use `normal` at the higher end of the range.

THE DECALS (category Decals, on a ground tile like the blood pool, 4 frames each, 8 fps, anchored at the middle of the tile's top face): `weather-ripple-water` (two rings
opening, for the water), `weather-ripple-ground` (a small ring, for dirt, stone and grass) and `weather-splash` (a ring and a crown of drops, 32 x 24, anchored where the ring is).
They play once, at the point a drop lands, on a tile the game picks at random; there is no outline, a splash has none.

Palette roles only. Deterministic: every random thing is seeded from the overlay's id. `check_loops()` proves each overlay's last frame runs into its first and that every
overlay tiles (it is drawn again shifted by half a tile and compared), and the same check runs on every preview.

    python3 tools/make_weather.py --check                                 the loop and tile checks, and how much of each is covered
    python3 tools/make_weather.py --preview previews/weather.png          each overlay tiled 2 x 2 over a night field, at its opacity; the decals in weather-decals.png; the GIF weather.gif
"""
import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

FOLDER = 'weather'
CATEGORY = 'Weather'
DECAL_CATEGORY = 'Decals'
TAU = math.tau
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    return (BAYER4[y % 4][x % 4] + 0.5) / 16


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def plot(g, x, y, c):
    """One pixel, wrapped round the tile."""
    h, w = len(g), len(g[0])
    g[int(y) % h][int(x) % w] = c


def rows_of(g):
    return [''.join(r) for r in g]


# --- fields: waves that tile in space and loop in time --------------------------------------------------
class Field:
    """A smooth field in 0..1 made of cosine waves with whole wave numbers (so it tiles) whose phases swing with the frame (so it loops): value(x, y, t)."""

    def __init__(self, name, w, h, frames, waves):
        rng = random.Random(name)
        self.w, self.h, self.n = w, h, frames
        self.waves = [(a, kx, ky, rng.uniform(0, TAU), rng.uniform(0.7, 1.7) * rng.choice((-1, 1)), rng.uniform(0, TAU)) for kx, ky, a in waves]
        self.total = sum(a for a, *_ in self.waves)

    def value(self, x, y, t):
        s = 0.0
        for a, kx, ky, ph, swing, psi in self.waves:
            s += a * math.cos(TAU * (kx * x / self.w + ky * y / self.h) + ph + swing * math.sin(TAU * t / self.n + psi))
        return 0.5 + 0.5 * s / self.total


def dithered(field, t, ox, oy, lo, hi, roles, shape=None):
    """The field as dithered pixels: where its value is past `lo` a pixel appears, more of them (and brighter roles) up to `hi`. `shape(x, y)` can scale the value (a profile across the tile)."""
    w, h = field.w, field.h
    g = blank(w, h)
    for y in range(h):
        for x in range(w):
            gx, gy = x + ox, y + oy
            v = field.value(gx, gy, t)
            if shape:
                v *= shape(gx, gy)
            u = (v - lo) / (hi - lo)
            if u <= 0 or u <= bayer(gx, gy) * 0.98:
                continue
            u = min(u, 1.0)
            g[y][x] = roles[2] if u > 0.72 else roles[1] if u > 0.4 else roles[0]
    return g


# --- rain ---------------------------------------------------------------------------------------------
def rain(name, count, lengths, near):
    rng = random.Random(name)
    drops = []
    for _ in range(count):
        ln = rng.randint(*lengths)
        drops.append((rng.randrange(128), rng.randrange(128), ln, ln >= near))

    def frame(t, ox=0, oy=0):
        g = blank(128, 128)
        for x0, y0, ln, wide in drops:
            x, y = x0 - 16 * t, y0 + 48 * t            # 3 tiles down and 1 across to the left over the 8 frames
            for i in range(ln):
                px, py = x + (i + 1) // 3 - ox, y - i - oy
                c = 'r' if i < 2 else 'q' if i < ln * 0.62 else 'p'
                plot(g, px, py, c)
                if wide and i < ln - 3:
                    plot(g, px + 1, py, 'q' if i < 2 else 'p')
        return rows_of(g)
    return frame


def ripple_ring(g, cx, cy, a, c):
    """An ellipse on the ground (twice as wide as tall) of half-width a, drawn as an unbroken 1-pixel line."""
    seen = set()
    steps = max(24, int(a * 14))
    for k in range(steps):
        th = TAU * k / steps
        p = (int(round(cx + a * math.cos(th))), int(round(cy + a * 0.5 * math.sin(th))))
        if p not in seen:
            seen.add(p)
            plot(g, p[0], p[1], c)


def rain_ripples(name, count=34):
    rng = random.Random(name)
    spots = []
    while len(spots) < count:
        x, y, s = rng.randrange(128), rng.randrange(128), rng.randrange(8)
        if all(min(abs(x - a), 128 - abs(x - a)) + 2 * min(abs(y - b), 128 - abs(y - b)) > 22 for a, b, _ in spots):
            spots.append((x, y, s))

    def frame(t, ox=0, oy=0):
        g = blank(128, 128)
        for x, y, s in spots:
            age = (t - s) % 8
            if age < 4:
                ripple_ring(g, x - ox, y - oy, (1.2, 2.6, 4.0, 5.2)[age], ('r', 'r', 'q', 'p')[age])
        return rows_of(g)
    return frame


# --- fog, haze, mist -------------------------------------------------------------------------------------
def fog(name, lo, hi, roles, waves):
    f = Field(name, 128, 128, 12, waves)
    return lambda t, ox=0, oy=0: rows_of(dithered(f, t, ox, oy, lo, hi, roles))


def mist(name):
    f = Field(name, 128, 64, 12, [(1, 1, 0.9), (2, 1, 0.8), (3, 2, 0.6), (4, 1, 0.5), (5, 3, 0.35), (7, 2, 0.25)])
    band = lambda x, y: 0.35 + 0.65 * (0.5 + 0.5 * math.cos(TAU * (y - 30) / 64)) ** 1.3       # thickest across the middle of the tile, and it tiles upwards too
    return lambda t, ox=0, oy=0: rows_of(dithered(f, t, ox, oy, 0.34, 0.8, ('p', 'q', 'r'), shape=band))


MOTE_PAIR = {'z': 'A', 'r': 'q', 'y': 'f'}


def spore_haze(name):
    rng = random.Random(name)
    haze = Field(name + '-haze', 128, 128, 12, [(1, 2, 0.8), (2, -1, 0.7), (3, 1, 0.55), (2, -4, 0.45), (4, 3, 0.35)])
    motes = [(rng.randrange(128), rng.randrange(128), rng.uniform(2.5, 7.0), rng.uniform(0, TAU), rng.uniform(0, TAU), rng.choice(('z', 'z', 'r', 'y')), rng.choice((-1, 1))) for _ in range(46)]

    def frame(t, ox=0, oy=0):
        g = dithered(haze, t, ox, oy, 0.6, 0.98, ('s', 'B', 'A'))
        for x0, y0, rad, ph, tw, c, sgn in motes:
            ang = sgn * TAU * t / 12 + ph
            x = int(round(x0 + rad * math.cos(ang))) - ox
            y = int(round(y0 + rad * 0.5 * math.sin(ang))) - oy
            glow = math.sin(TAU * t / 12 + tw)
            if glow > 0.45:                                        # at its brightest a little plus of light
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    plot(g, x + dx, y + dy, MOTE_PAIR[c])
                plot(g, x, y, 'j' if c == 'y' else 't' if c == 'r' else 'r')
            elif glow > -0.4:
                plot(g, x, y, c)
            else:
                plot(g, x, y, MOTE_PAIR[c])
        return rows_of(g)
    return frame


# --- embers and ash ----------------------------------------------------------------------------------------
def embers(name):
    rng = random.Random(name)
    sparks = [(rng.randrange(128), rng.randrange(128), rng.choice((1, 1, 2)), rng.uniform(0, TAU), rng.uniform(1.5, 4.5), rng.random() < 0.4) for _ in range(84)]
    ash = [(rng.randrange(128), rng.randrange(128), rng.uniform(0, TAU), rng.uniform(3, 7), rng.choice(('p', 'l', 'p'))) for _ in range(40)]

    def frame(t, ox=0, oy=0):
        g = blank(128, 128)
        for x0, y0, ph, sway, c in ash:
            x = x0 + round(sway * math.sin(TAU * t / 12 + ph)) - ox
            y = y0 - round(128 * t / 12) - oy
            plot(g, x, y, c)
        for x0, y0, k, ph, sway, big in sparks:
            x = x0 + round(sway * math.sin(TAU * t / 12 * k + ph)) - ox
            y = y0 - round(k * 128 * t / 12) - oy
            heat = 0.5 + 0.5 * math.cos(TAU * t / 12 + ph)
            c = 'd' if heat > 0.66 else 'b' if heat > 0.33 else 'a'
            plot(g, x, y, c)
            plot(g, x, y + 1, 'a' if heat > 0.33 else 'g')            # a dim trail below it
            if big and heat > 0.4:
                plot(g, x + 1, y, 'd' if heat > 0.66 else 'b')
                plot(g, x + 1, y + 1, 'a')
        return rows_of(g)
    return frame


# --- petals and leaves -----------------------------------------------------------------------------------
PETAL_SHAPES = ((0, 0), (1, 0), (2, 1)), ((0, 0), (0, 1), (1, 2)), ((0, 0), (1, 1), (2, 1)), ((0, 0), (1, 0), (1, 1))


def petals(name):
    rng = random.Random(name)
    flakes = []
    for _ in range(56):
        leaf = rng.random() < 0.3
        flakes.append((rng.randrange(128), rng.randrange(128), rng.uniform(0, TAU), rng.uniform(3, 9), rng.randrange(4), ('z', 'A') if leaf else rng.choice((('c', 'e'), ('C', 'c'), ('e', 'f')))))

    def frame(t, ox=0, oy=0):
        g = blank(128, 128)
        for x0, y0, ph, sway, spin, (c1, c2) in flakes:
            x = x0 + round(sway * math.sin(TAU * t / 12 + ph)) - ox
            y = y0 + round(128 * t / 12) - oy
            shape = PETAL_SHAPES[(spin + t // 3) % 4]                    # it turns as it falls: four positions over the loop
            for k, (dx, dy) in enumerate(shape):
                plot(g, x + dx, y + dy, c1 if k == 0 else c2)
        return rows_of(g)
    return frame


# --- the overlays ------------------------------------------------------------------------------------------
FOG_LIGHT_WAVES = [(1, 2, 1.0), (2, -1, 0.9), (2, 3, 0.65), (3, -2, 0.55), (1, -4, 0.45), (4, 1, 0.35), (5, -3, 0.25)]
FOG_DENSE_WAVES = [(1, 1, 1.0), (1, -2, 0.9), (2, 2, 0.7), (3, -1, 0.55), (2, -3, 0.45), (4, 3, 0.35), (1, 4, 0.3)]

OVERLAYS = [
    dict(id='weather-rain-light', label='Rain, light', w=128, h=128, frames=8, fps=12, blend='normal', opacity=(0.35, 0.60), scroll=(0, 0), frame=rain('rain-light', 30, (6, 10), 99),
         note='a few short streaks, down and to the left'),
    dict(id='weather-rain-heavy', label='Rain, heavy', w=128, h=128, frames=8, fps=12, blend='normal', opacity=(0.50, 0.85), scroll=(0, 0), frame=rain('rain-heavy', 58, (8, 13), 11),
         note='many longer streaks, the near ones two wide'),
    dict(id='weather-rain-ripples', label='Rain on the ground', w=128, h=128, frames=8, fps=8, blend='normal', opacity=(0.45, 0.90), scroll=(0, 0), frame=rain_ripples('rain-ripples'),
         note='flat rings opening and fading: draw it on the ground layer'),
    dict(id='weather-fog-light', label='Fog, light', w=128, h=128, frames=12, fps=6, blend='normal', opacity=(0.25, 0.50), scroll=(6, 2), frame=fog('fog-light', 0.52, 0.86, ('p', 'q', 'r'), FOG_LIGHT_WAVES),
         note='thin drifting banks'),
    dict(id='weather-fog-dense', label='Fog, dense', w=128, h=128, frames=12, fps=6, blend='normal', opacity=(0.40, 0.70), scroll=(4, 1), frame=fog('fog-dense', 0.40, 0.78, ('p', 'q', 'r'), FOG_DENSE_WAVES),
         note='thick banks'),
    dict(id='weather-spore-haze', label='Spore haze', w=128, h=128, frames=12, fps=8, blend='add', opacity=(0.50, 1.00), scroll=(-3, -2), frame=spore_haze('spore-haze'),
         note="the corruption's motes: lime, mint and magenta"),
    dict(id='weather-embers', label='Embers and ash', w=128, h=128, frames=12, fps=10, blend='add', opacity=(0.60, 1.00), scroll=(0, 0), frame=embers('embers'),
         note='embers and ash rising'),
    dict(id='weather-petals', label='Falling petals', w=128, h=128, frames=12, fps=8, blend='normal', opacity=(0.80, 1.00), scroll=(-8, 0), frame=petals('petals'),
         note='petals and a few leaves falling'),
    dict(id='weather-mist-low', label='Low mist', w=128, h=64, frames=12, fps=6, blend='normal', opacity=(0.30, 0.60), scroll=(5, 0), frame=mist('mist-low'),
         note='flat bands of mist for water and graves'),
]


# --- the decals ------------------------------------------------------------------------------------------------
DW, DH = 32, 16


def diamond_ok(x, y, shrink=0.05, cy=8):
    return abs(x + 0.5 - 16) / 16 + abs(y + 0.5 - cy) / 8 <= 1.0 - shrink + 1e-9


def ring_in_tile(g, a, c, cy=8):
    seen = set()
    for k in range(max(24, int(a * 14))):
        th = TAU * k / max(24, int(a * 14))
        p = (int(round(16 + a * math.cos(th))), int(round(cy + a * 0.5 * math.sin(th))))
        if p not in seen and diamond_ok(*p, cy=cy):
            seen.add(p)
            g[p[1]][p[0]] = c


def ripple_water():
    out = []
    for k in range(4):
        g = blank(DW, DH)
        ring_in_tile(g, 2.0 + 2.9 * k, ('r', 'r', 'q', 'p')[k])
        if k >= 1:
            ring_in_tile(g, 2.0 + 2.9 * (k - 1) - 0.4, ('q', 'q', 'p', 'p')[k])
        out.append(rows_of(g))
    return out


def ripple_ground():
    out = []
    for k in range(4):
        g = blank(DW, DH)
        ring_in_tile(g, 1.4 + 1.6 * k, ('r', 'r', 'q', 'p')[k])
        out.append(rows_of(g))
    return out


SPLASH_DROPS = [((-2, -2), (0, -3), (2, -2)), ((-4, -4), (-2, -5), (0, -6), (2, -5), (4, -4)), ((-5, -4), (-3, -3), (3, -3), (5, -4)), ((-6, -1), (6, -1))]


def splash():
    out = []
    for k in range(4):
        g = blank(DW, 24)
        ring_in_tile(g, (1.5, 3.5, 5.5, 7.5)[k], ('r', 'r', 'q', 'p')[k], cy=16)
        for dx, dy in SPLASH_DROPS[k]:
            g[16 + dy][16 + dx] = ('r', 'r', 'q', 'p')[k]
        out.append(rows_of(g))
    return out


DECALS = [('weather-ripple-water', 'Rain ripple, water', ripple_water, (16, 8), DH), ('weather-ripple-ground', 'Rain ripple, ground', ripple_ground, (16, 8), DH),
          ('weather-splash', 'Rain splash', splash, (16, 16), 24)]


# --- the checks ------------------------------------------------------------------------------------------------------
def roll(rows, dx, dy):
    """The picture moved (dx, dy) with wrap-round, as rows."""
    h, w = len(rows), len(rows[0])
    return [''.join(rows[(y - dy) % h][(x - dx) % w] for x in range(w)) for y in range(h)]


def check_loops(verbose=False):
    """Each overlay: its picture one loop later is the first again, it tiles (drawn again shifted by half a tile it is the first rolled by half a tile), it is the size it says,
    uses palette roles only and is neither empty nor full. Returns {id: share of the tile covered}."""
    roles = set('OabcdefghijklmnopqrstuvwxyzABCD')
    cover = {}
    for o in OVERLAYS:
        w, h, n = o['w'], o['h'], o['frames']
        shares = []
        for t in range(n):
            f = o['frame'](t)
            assert len(f) == h and all(len(r) == w for r in f), (o['id'], t, 'size')
            assert set(''.join(f)) - {'.'} <= roles, (o['id'], t, 'roles')
            assert o['frame'](t + n) == f, (o['id'], t, 'the loop does not close')
            assert o['frame'](t, w // 2, h // 2) == roll(f, -(w // 2), -(h // 2)), (o['id'], t, 'it does not tile')
            shares.append(sum(c != '.' for r in f for c in r) / (w * h))
        assert 0.002 < min(shares) and max(shares) < 0.6, (o['id'], min(shares), max(shares))
        cover[o['id']] = (min(shares), max(shares))
    for id, label, fn, anchor, h in DECALS:
        fr = fn()
        assert len(fr) == 4 and all(len(f) == h and len(f[0]) == DW for f in fr), id
        assert all(any(c != '.' for r in f for c in r) for f in fr), id
    if verbose:
        for k, (lo, hi) in cover.items():
            print(f'{k:22s} covers {lo * 100:4.1f}% to {hi * 100:4.1f}% of its tile')
    return cover


# --- the family contract -----------------------------------------------------------------------------------------------
def build_assets():
    """Nine looping overlays (category Weather, 128 x 128 or 128 x 64, 8 or 12 frames, `place` none) and three splash decals (category Decals, 4 frames, on a ground tile)."""
    out = []
    for o in OVERLAYS:
        make = family(CATEGORY, o['w'], o['h'], (0, 0), place='none', folder=FOLDER)
        out.append(make(o['id'], o['label'], 'animation', [o['frame'](t) for t in range(o['frames'])], fps=o['fps'],
                        weather={'tile': [o['w'], o['h']], 'blend': o['blend'], 'opacity': list(o['opacity']), 'scroll': list(o['scroll']), 'note': o['note']}))
    for id, label, fn, anchor, h in DECALS:
        make = family(DECAL_CATEGORY, DW, h, anchor, place='ground', folder=FOLDER)
        out.append(make(id, label, 'animation', fn(), fps=8, weather={'play': 'once, where a drop lands'}))
    return out


def write_package(folder):
    """Beside the sheets: weather.json, how each overlay is meant to be drawn."""
    write_json(folder, 'weather.json', 'The weather overlays and splash decals in this folder. How to draw each is in tools/make_weather.py.',
               {'overlays': {o['id']: {'label': o['label'], 'file': f"{o['id']}.png", 'tile': [o['w'], o['h']], 'frames': o['frames'], 'fps': o['fps'], 'blend': o['blend'],
                                       'opacity': list(o['opacity']), 'scroll_px_per_second': list(o['scroll']), 'note': o['note']} for o in OVERLAYS},
                'decals': {id: {'label': label, 'file': f'{id}.png', 'cell': [DW, h], 'anchor': list(anchor), 'frames': 4, 'fps': 8} for id, label, fn, anchor, h in DECALS},
                'draw': 'repeat the tile over the view in screen space, above the map and below the UI, at a whole number of screen pixels per scroll step; the pixels are opaque, the layer opacity is the game\'s'})


# --- preview --------------------------------------------------------------------------------------------------------------
def _rgb():
    import extract_poses as ep
    return {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}


def _image(rows, rgb):
    from PIL import Image
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                px[x, y] = rgb[c] + (255,)
    return im


def backdrop(w, h, rgb):
    """A night field of ground diamonds, 32 x 16 each, in the darkest cool roles, for the overlays to sit over."""
    from PIL import Image, ImageDraw
    im = Image.new('RGBA', (w, h), rgb['x'] + (255,))
    d = ImageDraw.Draw(im)
    tones = [rgb['D'], rgb['s'], rgb['k'], rgb['D'], rgb['w'], rgb['s']]
    for i in range(-4, 40):
        for j in range(-4, 40):
            cx, cy = 16 * (i - j) + w // 2, 8 * (i + j) - 8
            t = tones[(i * 7 + j * 13 + (i * j) % 5) % len(tones)]
            if -16 <= cx <= w + 16 and -8 <= cy <= h + 8:
                d.polygon([(cx, cy - 8), (cx + 16, cy), (cx, cy + 8), (cx - 16, cy)], fill=t + (255,))
    return im


def apply_layer(base, layer, opacity, blend):
    """Draw a tiled layer of opaque pixels over a picture at an opacity, normally or additively."""
    from PIL import Image, ImageChops
    if blend == 'add':
        rgb = Image.new('RGB', layer.size, (0, 0, 0))
        rgb.paste(layer.convert('RGB'), mask=layer.split()[3])
        rgb = rgb.point(lambda v: int(v * opacity))
        out = ImageChops.add(base.convert('RGB'), rgb).convert('RGBA')
        return out
    a = layer.split()[3].point(lambda v: int(v * opacity))
    lay = layer.copy()
    lay.putalpha(a)
    out = base.copy()
    out.alpha_composite(lay)
    return out


def panel(o, t, rgb, bg):
    from PIL import Image
    tile = _image(o['frame'](t % o['frames']), rgb)
    big = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    for yy in range(0, 256, o['h']):
        for xx in range(0, 256, o['w']):
            big.alpha_composite(tile, (xx, yy))
    op = sum(o['opacity']) / 2
    return apply_layer(bg, big, op, o['blend'])


def preview(path, scale=2):
    from PIL import Image, ImageDraw
    rgb = _rgb()
    check_loops()
    cols = 3
    bg = backdrop(256, 256, rgb)
    rows_n = -(-len(OVERLAYS) // cols)

    def sheet_at(t):
        sheet = Image.new('RGBA', (cols * 264 + 8, rows_n * 280 + 8), (20, 22, 36, 255))
        d = ImageDraw.Draw(sheet)
        for i, o in enumerate(OVERLAYS):
            x, y = 8 + (i % cols) * 264, 8 + (i // cols) * 280
            sheet.alpha_composite(panel(o, t, rgb, bg), (x, y + 14))
            d.text((x, y), f"{o['id'].replace('weather-', '')}  {o['blend']} {sum(o['opacity']) / 2:.2f}", fill=(230, 220, 200, 255))
        return sheet
    still = sheet_at(3)
    still.resize((still.width * scale // 2 * 1, still.height * scale // 2 * 1), Image.NEAREST).save(path) if scale == 2 else still.save(path)
    gif_path = path.with_suffix('.gif')
    frames = [sheet_at(t).convert('RGB') for t in range(24)]
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    # the decals: four frames each, enlarged, on a ground diamond
    sc = 8
    dec = Image.new('RGBA', (4 * (DW * sc + 12) + 12, len(DECALS) * (24 * sc + 28) + 8), (20, 22, 36, 255))
    d = ImageDraw.Draw(dec)
    for r, (id, label, fn, anchor, h) in enumerate(DECALS):
        d.text((12, 6 + r * (24 * sc + 28)), id, fill=(230, 220, 200, 255))
        for k, rows_ in enumerate(fn()):
            cell = Image.new('RGBA', (DW, 24), rgb['D'] + (255,))
            ground = Image.new('RGBA', (DW, 24), (0, 0, 0, 0))
            from PIL import ImageDraw as ID
            ID.Draw(ground).polygon([(16, anchor[1] - 8 - 0), (32, anchor[1]), (16, anchor[1] + 8), (0, anchor[1])], fill=rgb['s'] + (255,))
            cell.alpha_composite(ground)
            cell.alpha_composite(_image(rows_, rgb), (0, 0))
            dec.alpha_composite(cell.resize((DW * sc, 24 * sc), Image.NEAREST), (12 + k * (DW * sc + 12), 20 + r * (24 * sc + 28)))
    dec.save(path.with_name(path.stem + '-decals.png'))
    return gif_path


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='each overlay tiled 2 x 2 over a night field at its opacity; also a GIF and the decals')
    parser.add_argument('--check', action='store_true', help='the loop and tile checks, and the share of each tile covered')
    args = parser.parse_args()
    if args.check or not args.preview:
        check_loops(verbose=True)
        print('every overlay loops and tiles')
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        gif = preview(args.preview)
        print('weather ->', args.preview, gif, args.preview.with_name(args.preview.stem + '-decals.png'))


if __name__ == '__main__':
    main()
