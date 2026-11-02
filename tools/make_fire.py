#!/usr/bin/env python3
"""A fire burst: an area spell on five plots (see make_aoe.py), eight frames.

It ignites on the middle plot, bursts, throws fire out onto the four plots around it, burns at full strength,
and dies back to embers and smoke. Flames are made of three tongues each, white-hot cream at the heart through
yellow and amber to orange and coral at the tips, over a scorched, glowing plot. Everything is palette roles.

    python3 tools/make_fire.py --preview previews/fire-burst.png     the eight frames, over five ground tiles
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_aoe as aoe  # noqa: E402

FRAMES = 8
HOT, CORE, MID, OUT, TIP, DEEP = 't', 'd', 'b', 'a', 'e', 'f'       # cream, yellow, amber, orange, coral, orchid
SMOKE, SMOKE_DARK = 'g', 'w'                                         # plum, grape

# Each frame: the height of the flame on each plot (0 = none), its glow on the ground (0-1), and the loose bits.
# The fire starts in the middle, bursts out onto the four plots around it, burns, and dies down.
SCHEDULE = [
    dict(C=4,  NW=0,  NE=0,  SW=0,  SE=0,  glow=0.2, sparks=0, smoke=0),    # a spark
    dict(C=14, NW=0,  NE=0,  SW=0,  SE=0,  glow=0.5, sparks=2, smoke=0),    # it bursts
    dict(C=24, NW=4,  NE=4,  SW=4,  SE=4,  glow=0.8, sparks=4, smoke=0),    # fire reaches out
    dict(C=29, NW=12, NE=12, SW=12, SE=12, glow=1.0, sparks=5, smoke=0),    # white-hot at the middle
    dict(C=26, NW=19, NE=19, SW=19, SE=19, glow=1.0, sparks=5, smoke=1),    # full strength on all five
    dict(C=22, NW=16, NE=16, SW=16, SE=16, glow=0.9, sparks=4, smoke=2),    # it flickers
    dict(C=12, NW=9,  NE=9,  SW=9,  SE=9,  glow=0.6, sparks=2, smoke=3),    # dying down
    dict(C=3,  NW=3,  NE=3,  SW=3,  SE=3,  glow=0.3, sparks=1, smoke=2),    # embers
]
PHASE = {'C': 0.0, 'NW': 2.1, 'NE': 4.0, 'SW': 1.2, 'SE': 5.1}      # so the flames on different plots do not move together


def ground_glow(grid, plot, strength, frame):
    """The plot scorched and glowing: a dither of orange and red over its diamond, hotter in the middle."""
    if strength <= 0.05:
        return
    cx, cy = aoe.centre(plot)
    for y in range(aoe.CELL_H):
        for x in range(aoe.CELL_W):
            if not aoe.inside(plot, x, y, 0.06):
                continue
            d = abs(x + 0.5 - cx) / 16 + abs(y + 0.5 - cy) / 8        # 0 in the middle, 1 at the edge
            heat = strength * (1.15 - d)
            if heat > 0.75 and (x // 2 + y) % 2 == 0:
                aoe.put(grid, x, y, OUT)
            elif heat > 0.45 and y % 2 == 0 and (x // 2 + y // 2) % 2 == 0:
                aoe.put(grid, x, y, TIP)
            elif heat > 0.15 and y % 2 == 0 and (x // 2 + y // 2) % 2 == 1 and (x // 4 + y // 4) % 2 == 0:
                aoe.put(grid, x, y, DEEP)


def tongue(grid, cx, base, height, width, phase, sway):
    """One flame: a tapering tongue that leans and wavers, painted hot at the heart and cool at the edge."""
    if height < 1:
        return
    for k in range(int(height) + 1):
        t = k / max(1.0, height)
        belly = min(1.0, 0.45 + 0.55 * math.sin(min(1.0, t / 0.22) * math.pi / 2))      # rounded at the foot, not a flat edge
        half = (width / 2) * belly * (1 - t ** 1.25) * (1 + 0.12 * math.sin(4 * t + phase))
        centre = cx + sway * t * t + 1.3 * math.sin(phase + 5 * t) * t
        y = base - k
        for x in range(int(math.floor(centre - half)), int(math.ceil(centre + half)) + 1):
            u = (x + 0.5 - centre) / max(half, 0.6)
            if abs(u) > 1.0:
                continue
            if t < 0.28 and abs(u) < 0.34:
                c = HOT
            elif t < 0.6 and abs(u) < 0.45:
                c = CORE
            elif t < 0.8 and abs(u) < 0.72:
                c = MID
            elif t < 0.93:
                c = OUT
            else:
                c = TIP
            if abs(u) > 0.86 and t > 0.35:
                c = OUT if t < 0.8 else TIP
            aoe.put(grid, x, y, c)


def pool(grid, cx, cy, width, frame):
    """The fire's foot: a low, wide, flickering bed of orange and coral that the flames rise out of."""
    for dy, (w, c) in enumerate(((0.55, OUT), (1.0, TIP), (0.8, OUT))):
        half = width * w / 2
        y = cy - 1 + dy
        for x in range(int(cx - half), int(cx + half) + 1):
            if (x + frame + dy) % 5 != 0:
                aoe.put(grid, x, y, c)


def flame(grid, plot, height, frame):
    """A cluster of three tongues on a plot: a tall one in the middle and a shorter one either side."""
    if height < 1:
        return
    cx, cy = aoe.centre(plot)
    phase = PHASE[plot] + frame * 1.3
    wob = math.sin(phase)
    width = min(18, 6 + height * 0.55)
    pool(grid, cx, cy, width + 6, frame)
    tongue(grid, cx - width * 0.32, cy + 1, height * 0.62, width * 0.55, phase + 1.7, -2.0 + wob)
    tongue(grid, cx + width * 0.32, cy + 1, height * 0.7, width * 0.55, phase + 3.1, 2.0 - wob)
    tongue(grid, cx, cy + 2, height, width, phase, 1.5 * wob)


def bridges(grid, spec, frame):
    """Low licks of fire along the edges where two burning plots meet, so the five read as one blaze."""
    for plot in ('NW', 'NE', 'SW', 'SE'):
        reach = min(spec['C'], spec[plot])
        if reach < 3:
            continue
        a, b = aoe.centre('C'), aoe.centre(plot)
        for k, t in enumerate((0.3, 0.5, 0.7)):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            h = reach * (0.3 if k == 1 else 0.22) * (1 + 0.15 * math.sin(frame * 1.7 + k + t * 9))
            pool(grid, x, y, 8, frame + k)
            tongue(grid, x, y + 1, h, 6, frame * 1.1 + k * 2.3 + t * 7, 1.0 * math.sin(frame + k))


def sparks(grid, count, frame):
    """Sparks flung out from the middle, towards the four plots, and rising."""
    cx, cy = aoe.MIDDLE
    for i in range(count):
        ang = (i * 2.4 + frame * 0.7) % (2 * math.pi)
        run = 5 + 4 * ((frame + i) % 4)
        x = cx + math.cos(ang) * run * 1.6
        y = cy - 4 - abs(math.sin(ang)) * run * 0.5 - 3 * ((frame + i) % 3)
        aoe.put(grid, x, y, HOT if i % 2 == 0 else CORE)


def smoke(grid, count, frame):
    """A few wisps rising off the burning plots."""
    for i in range(count * 2):
        plot = aoe.DEPTH_ORDER[(i + frame) % 5]
        cx, cy = aoe.centre(plot)
        x = cx + 3 * math.sin(frame + i * 1.9)
        y = cy - 12 - 3 * ((frame + i) % 3) - frame
        aoe.put(grid, x, y, SMOKE if i % 2 == 0 else SMOKE_DARK)
        aoe.put(grid, x + 1, y - 1, SMOKE_DARK)


def render_pixels(frame):
    spec = SCHEDULE[frame]
    grid = aoe.blank()
    for plot in aoe.DEPTH_ORDER:
        ground_glow(grid, plot, spec['glow'] if spec[plot] or plot == 'C' else 0, frame)
    bridges(grid, spec, frame)
    for plot in aoe.DEPTH_ORDER:                          # far to near, so near flames overlap far ones
        flame(grid, plot, spec[plot], frame)
    sparks(grid, spec['sparks'], frame)
    smoke(grid, spec['smoke'], frame)
    return aoe.lines(grid)


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write the eight frames over five ground tiles here')
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
    scale = 4
    cols = 4
    rows = FRAMES // cols
    w, h = aoe.CELL_W, aoe.CELL_H + 20
    sheet = Image.new('RGBA', (cols * (w + 4) * scale, rows * (h + 4) * scale), (36, 38, 56, 255))
    for f in range(FRAMES):
        cell = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for plot in aoe.DEPTH_ORDER:                      # five ground tiles, far to near
            cx, cy = aoe.centre(plot)
            cell.alpha_composite(ground, (cx - 16, cy - 8))
        over = Image.new('RGBA', (aoe.CELL_W, aoe.CELL_H), (0, 0, 0, 0))
        for y, line in enumerate(render_pixels(f)):
            for x, c in enumerate(line):
                if c != '.':
                    over.putpixel((x, y), rgb[c] + (255,))
        cell.alpha_composite(over)
        sheet.alpha_composite(cell.resize((w * scale, h * scale), Image.NEAREST), (((f % cols) * (w + 4) + 2) * scale, ((f // cols) * (h + 4) + 2) * scale))
    if args.preview:
        sheet.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
