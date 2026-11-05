#!/usr/bin/env python3
"""Two traps for the ground: caltrops and a bear trap, each placed (as it waits) and triggered (an animation).

Built as small 3D models of ellipsoids, the way the vine spell is (see make_vine.py and creature.py), then rendered into 32 x 32 cells in the shared colour roles.
Both lie flat on a ground tile. The model's origin is the middle of the tile, on the ground, and lands on the anchor of each cell.

    python3 tools/make_traps.py --model previews/traps-3d.png            look at the 3D models first
    python3 tools/make_traps.py --preview previews/traps.png             the sprites, enlarged, as they will be drawn

Caltrops (`trap-caltrops`, one frame; `trap-caltrops-triggered`, 6 frames): five iron jacks, four spikes each, lying scattered. Triggered, they flash, jump,
tumble in a ring of dust and fall back spread wider.
Bear trap (`trap-beartrap`, one frame; `trap-beartrap-triggered`, 6 frames): a toothed pair of jaws lying open round a pressure pan, with a short chain.
Triggered, the pan drops, the jaws swing up and snap shut, and it rests closed.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, mm, part, rx, ry, rz  # noqa: E402

CELL = 32
ORIGIN = (16.0, 24.0)            # where the model's origin (the middle of the tile, on the ground) lands in the cell
ANCHOR = (16, 24)               # the same point, for the game
FPS = 10
SCALE = 1.3                      # the models are drawn this much larger, so the pieces are more than a pixel or two

RAMPS = {
    'iron': ('p', 'l', 'k', 'w'),         # steel, lavender, indigo, grape
    'tip': ('r', 'q', 'p', 'l'),          # a bright steel edge: mint, teal, steel, lavender
    'rust': ('a', 'g', 'w', 'x'),         # rust, plum, grape, eggplant (the palette has no true brown)
    'brass': ('b', 'a', 'g', 'w'),        # a dull gold spring: amber, orange, plum, grape
    'dust': ('t', 'C', 'b', 'a'),         # pale sand kicked up: cream, sand, amber, orange
    'spark': ('t', 'd', 'b', 'a'),        # cream, yellow, amber, orange
}


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def along(direction, up=(0.0, 1.0, 0.0)):
    """An orientation whose x axis runs along `direction` and whose y axis is as close to `up` as it can be."""
    ex = norm(direction)
    d = sum(a * b for a, b in zip(up, ex))
    ey = norm(tuple(u - d * e for u, e in zip(up, ex))) if abs(d) < 0.98 else norm(cross(ex, (0.0, 0.0, 1.0)))
    ez = cross(ex, ey)
    return [[ex[i], ey[i], ez[i]] for i in range(3)]


def spike(base, direction, length, radius, name, mat='iron', tip='tip'):
    """A tapering spike from `base` along `direction`: three ellipsoids, thick to fine, the last a bright steel point."""
    d = norm(direction)
    R = along(d)
    out = []
    for k, (t0, t1, rr, m) in enumerate(((0.0, 0.42, 1.0, mat), (0.38, 0.72, 0.68, mat), (0.68, 1.0, 0.38, tip))):
        a = tuple(base[i] + d[i] * length * t0 for i in range(3))
        b = tuple(base[i] + d[i] * length * t1 for i in range(3))
        mid = tuple((a[i] + b[i]) / 2 for i in range(3))
        out.append(part(mid, (length * (t1 - t0) / 2 + 0.25, radius * rr, radius * rr), m, name, R))
    return out


# --- caltrops -------------------------------------------------------------------
# five jacks: where each lies on the ground (x, z) and how it is turned
JACKS = [((0.0, 0.0), 0.3, 0.2), ((5.2, -3.4), 1.9, 0.5), ((-5.0, 2.6), 4.0, 0.3), ((2.8, 5.6), 2.6, 0.7), ((-3.0, -5.8), 5.4, 0.4)]
PRONG = 3.3


def jack(at, yaw, lean, lift=0.0, spin=0.0, flash=False):
    """One caltrop: four spikes from a hub, one up and three splayed down, so that it always rests on three points and points up with the fourth."""
    x, y, z = at
    parts = []
    hub_y = 0.95 * PRONG * 0.34 + y + lift
    centre = (x, hub_y, z)
    parts.append(part(centre, (0.9, 0.9, 0.9), 'iron', f'hub{x:.0f}{z:.0f}'))
    tip = 'spark' if flash else 'tip'
    dirs = [(0.0, 1.0, 0.0)] + [(math.cos(a) * 0.94, -0.34, math.sin(a) * 0.94) for a in (0.0, 2.094, 4.189)]
    tilt = mm(ry(yaw + spin), rz(lean + spin * 0.6))
    for n, d in enumerate(dirs):
        dd = tuple(sum(tilt[i][j] * d[j] for j in range(3)) for i in range(3))
        parts += spike(centre, dd, PRONG, 0.8, f'jack{x:.0f}{z:.0f}{n}', tip=tip)
    return parts


def caltrops(spread=1.0, lift=0.0, spin=0.0, flash=False, dust=0.0):
    parts = []
    for n, ((x, z), yaw, lean) in enumerate(JACKS):
        hop = lift * (0.7 + 0.3 * ((n * 3) % 5) / 4)
        parts += jack((x * spread, 0.0, z * spread), yaw + n * spin * 0.7, lean, hop, spin * (1 if n % 2 else -1), flash)
    if dust > 0:
        parts += dust_ring(dust)
    return parts


def dust_ring(amount):
    """Puffs of dust in a ring round the middle, spreading and rising as `amount` grows."""
    out = []
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.5
        d = 3.0 + 6.0 * amount
        size = 0.7 + 1.2 * amount * (0.8 + 0.4 * ((k * 5) % 3) / 2)
        out.append(part((math.cos(a) * d, 0.5 + 2.2 * amount, math.sin(a) * d), (size, size * 0.8, size), 'dust', f'puff{k}'))
    return out


CALTROP_FRAMES = [
    dict(name='stepped on', spread=1.0, lift=0.0, spin=0.0, flash=True, dust=0.0),
    dict(name='pop', spread=1.05, lift=3.2, spin=0.5, flash=True, dust=0.25),
    dict(name='tumble', spread=1.1, lift=6.0, spin=1.3, flash=False, dust=0.6),
    dict(name='fall', spread=1.15, lift=3.2, spin=2.0, flash=False, dust=0.9),
    dict(name='land', spread=1.2, lift=0.6, spin=2.6, flash=False, dust=0.7),
    dict(name='rest', spread=1.22, lift=0.0, spin=2.7, flash=False, dust=0.35),
]


# --- bear trap ------------------------------------------------------------------
JAW_R = 6.4                      # the radius of each jaw's half-ring
HINGE_Z = 0.9                    # the hinge line of each jaw, either side of the pan
TEETH = 6


def jaw(side, theta, pressed):
    """One jaw: a half-ring of iron with teeth, hinged beside the pan and swung up by `theta` degrees about its hinge (side is +1 or -1)."""
    parts = []
    swing = rx(-side * math.radians(theta))
    hinge = (0.0, 0.7, side * HINGE_Z)

    def carry(p, R):
        rel = (p[0] - hinge[0], p[1] - hinge[1], p[2] - hinge[2])
        w = tuple(sum(swing[i][j] * rel[j] for j in range(3)) for i in range(3))
        return add(hinge, w), mm(swing, R)

    ring = 11
    for k in range(ring):
        t0, t1 = math.pi * k / ring, math.pi * (k + 1) / ring
        a = (JAW_R * math.cos(t0), 0.7, side * (HINGE_Z + JAW_R * math.sin(t0)))
        b = (JAW_R * math.cos(t1), 0.7, side * (HINGE_Z + JAW_R * math.sin(t1)))
        mid = tuple((a[i] + b[i]) / 2 for i in range(3))
        c, R = carry(mid, along((b[0] - a[0], 0.0, b[2] - a[2])))
        parts.append(part(c, (math.dist(a, b) / 2 + 0.35, 0.85, 0.85), 'iron', f'jaw{side}', R))
    for k in range(TEETH):                                          # teeth on the ring, pointing up when flat and so across the gap when shut
        t = math.pi * (k + 0.5 + (0.5 if side > 0 else 0.0)) / (TEETH + 0.5)
        p = ((JAW_R - 0.2) * math.cos(t), 1.6, side * (HINGE_Z + (JAW_R - 0.2) * math.sin(t)))
        c, R = carry(p, I3)
        parts.append(part(c, (0.55, 1.2, 0.55), 'tip', f'jaw{side}', R))
    return parts


I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def beartrap(theta=0.0, pressed=False, shake=0.0, dust=0.0, spark=False):
    parts = []
    drop = 0.35 if pressed else 0.0
    parts.append(part((0.0, 0.3, 0.0), (3.2, 0.45, 1.9), 'rust', 'plate'))                    # the base plate
    parts.append(part((0.0, 0.75 - drop, 0.0), (1.3, 0.3, 1.3), 'brass', 'pan'))              # the pressure pan
    for sx in (-1, 1):                                                                         # the leaf springs at either end
        parts.append(part((sx * 4.2, 0.55, 0.0), (1.3, 0.35, 1.1), 'brass', f'spring{sx}'))
    for k in range(5):                                                                         # a short chain off the back, laid in a bend
        parts.append(part((-4.6 - k * 1.5, 0.45, math.sin(k * 0.9) * 1.1), (0.95, 0.4, 0.55), 'iron', f'link{k}', ry(0.5 * k) if k % 2 else I3))
    parts += jaw(1, theta, pressed) + jaw(-1, theta, pressed)
    if shake:                                                                                  # the snap jolts the whole trap a little
        parts = [dict(q, c=(q['c'][0] + shake, q['c'][1], q['c'][2])) for q in parts]
    if dust > 0:
        parts += dust_ring(dust)
    if spark:
        for k in range(5):
            a = k * 2 * math.pi / 5 + 0.3
            parts.append(part((math.cos(a) * 3.6, 6.0 + (k % 2) * 1.8, math.sin(a) * 3.6), (0.5, 0.5, 0.5), 'spark', f'spark{k}'))
    return parts


BEARTRAP_FRAMES = [
    dict(name='pressed', theta=0.0, pressed=True, dust=0.0),
    dict(name='jaws lift', theta=24.0, pressed=True, dust=0.15),
    dict(name='swing', theta=58.0, pressed=True, dust=0.3),
    dict(name='closing', theta=84.0, pressed=True, dust=0.55, spark=True),
    dict(name='snap', theta=92.0, pressed=True, dust=0.8, shake=0.7, spark=True),
    dict(name='shut', theta=88.0, pressed=True, dust=0.45),
]

TRAPS = {
    'caltrops': dict(label='Caltrops', frames=CALTROP_FRAMES, build=lambda f: caltrops(f['spread'], f['lift'], f['spin'], f['flash'], f['dust']),
                     placed=dict(spread=1.0, lift=0.0, spin=0.0, flash=False, dust=0.0)),
    'beartrap': dict(label='Bear trap', frames=BEARTRAP_FRAMES, build=lambda f: beartrap(f['theta'], f['pressed'], f.get('shake', 0.0), f['dust'], f.get('spark', False)),
                     placed=dict(theta=0.0, pressed=False, dust=0.0)),
}


# --- pixels -----------------------------------------------------------------------
def render_pixels(parts):
    """One frame as CELL rows of colour-role characters, outlined like the characters."""
    import creature as cr
    rows = cr.render_frame(parts, [], 'SE', ORIGIN, RAMPS, SCALE)
    return [''.join(row) for row in rows]


def frames_of(name):
    t = TRAPS[name]
    return render_pixels(t['build'](t['placed'])), [render_pixels(t['build'](f)) for f in t['frames']]


# --- previews ---------------------------------------------------------------------
def model_sheet(size=300):
    from PIL import Image, ImageDraw
    import preview3d as pv
    bounds = [(11, 0, 11), (-11, 0, -11), (11, 0, -11), (-11, 0, 11), (0, 10, 0)]
    cols = 7
    sheet = Image.new('RGBA', (size * cols, (size + 20) * 2), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(TRAPS):
        t = TRAPS[name]
        shown = [('placed', t['build'](t['placed']))] + [(f['name'], t['build'](f)) for f in t['frames']]
        for i, (label, parts) in enumerate(shown):
            tile = pv.render_view(parts, [], RAMPS, -45, size, fit_points=bounds)
            sheet.alpha_composite(tile, (i * size, row * (size + 20) + 20))
            draw.text((i * size + 6, row * (size + 20) + 4), f'{t["label"]}: {label}', fill=(235, 238, 245, 255))
    return sheet


def pixel_sheet(path, scale=6):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    cols = 7
    sheet = Image.new('RGB', (cols * CELL * scale, 2 * (CELL * scale + 16)), (50, 44, 84))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(TRAPS):
        placed, anim = frames_of(name)
        for i, rows in enumerate([placed] + anim):
            ox, oy = i * CELL * scale, row * (CELL * scale + 16) + 16
            draw.text((ox + 4, oy - 13), f'{TRAPS[name]["label"]}: ' + ('placed' if i == 0 else TRAPS[name]['frames'][i - 1]['name']), fill=(235, 238, 245))
            for y, line in enumerate(rows):
                for x, ch in enumerate(line):
                    if ch != '.':
                        draw.rectangle([ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1], fill=rgb[ch])
    sheet.save(path)


# --- the assets ---------------------------------------------------------------------
CATEGORY = 'Traps'
FOLDER = 'traps'


def build_assets():
    """Four assets, one folder: each trap placed (one frame) and triggered (an animation), by the ids trap-NAME and trap-NAME-triggered."""
    assets = []
    for name, t in TRAPS.items():
        placed, anim = frames_of(name)
        common = dict(category=CATEGORY, folder=FOLDER, place='ground', w=CELL, h=CELL, anchor={'x': ANCHOR[0], 'y': ANCHOR[1]})
        assets.append(dict(common, id=f'trap-{name}', label=f'{t["label"]} - placed (waiting on the ground)', kind='still', cols=1, rows=1, fps=0,
                           trap={'name': name, 'state': 'placed'}, frames=[placed]))
        assets.append(dict(common, id=f'trap-{name}-triggered', label=f'{t["label"]} - triggered (animation)', kind='animation', cols=len(anim), rows=1, fps=FPS,
                           trap={'name': name, 'state': 'triggered', 'plays': 'once, then holds the last frame'}, frames=anim))
    return assets


def write_package(folder):
    """Beside the sheets: traps.json, how a game uses them in numbers (README.md says it in words)."""
    import json
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'traps.json').write_text(json.dumps({
        'about': 'The trap sheets in this folder. See README.md beside this file for the whole story.',
        'cell': CELL, 'anchor': {'x': ANCHOR[0], 'y': ANCHOR[1]}, 'fps': FPS,
        'traps': {name: {'label': t['label'], 'placed': f'trap-{name}.png', 'triggered': f'trap-{name}-triggered.png',
                         'triggeredFrames': [f['name'] for f in t['frames']], 'triggeredPlays': 'once, then hold the last frame'}
                  for name, t in TRAPS.items()},
    }, indent=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, help='write the 3D preview of both traps here')
    parser.add_argument('--preview', type=Path, help='write the pixel sprites, enlarged, here')
    args = parser.parse_args()
    if args.model:
        args.model.parent.mkdir(parents=True, exist_ok=True)
        model_sheet().save(args.model)
        print(f'3D preview of the traps -> {args.model}; no sprites were made')
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        pixel_sheet(args.preview)
        print(f'the trap sprites, enlarged -> {args.preview}')


if __name__ == '__main__':
    main()
