#!/usr/bin/env python3
"""Melee weapons drawn along the swing the existing weapons share (see make_weapons.py and CONVENTIONS.md).

Every weapon strip is 4 frames of 48 x 48, NE and SE. The existing ones are hand-drawn, so the swing is read back from them: for each frame
the middle of the weapon (the mean of the existing weapons, which the checker holds new ones to), which way the iron sword points from hilt to
tip, and how much shorter it looks end-on (a weapon swung toward or away from the camera is foreshortened). A new weapon is a list of parts
along its own axis (a grip at t = 0, the butt behind it and the head ahead), drawn on that path: its grip sits near the hand and its middle
on the shared path.

    python3 tools/make_melee.py --preview previews/melee-new.png     the eight weapons, in the slim human's hand
    python3 tools/make_melee.py --out sprites/weapons                 write the strips (after they are approved)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions as cv  # noqa: E402
import extract_poses as ep  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CELL = cv.WEAPON_CELL
LIGHT = (-0.55, -0.83)         # light from the upper left, as everywhere
GRIP_BACK = 4.0                # the hand is this far from the weapon's middle, toward the body

RAMPS = {
    'steel': ('r', 'q', 'p', 'l'),
    'iron': ('q', 'p', 'l', 'k'),
    'wood': ('b', 'a', 'e', 'g'),
    'leather': ('e', 'f', 'h', 'g'),
    'gold': ('t', 'd', 'b', 'a'),
    'ruby': ('c', 'j', 'i', 'h'),
    'sapphire': ('r', 'o', 'n', 'm'),
    'bone': ('t', 'C', 'c', 'e'),
}


# --- the swing, read back from the existing weapons ------------------------------------------------
def swing():
    """{facing: [{'centre': (x, y), 'dir': (dx, dy) hilt to tip, 'scale': foreshortening 0..1} per frame]}"""
    from PIL import Image
    folder = ROOT / 'sprites' / 'weapons'
    paths = cv.weapon_paths(folder)
    pal = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): c for c, _, _, _, h in ep.ROLES}

    def role(rgb):
        return pal[min(pal, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, rgb)))]

    out = {}
    pad = (CELL - cv.CELL) / 2
    for facing in ('NE', 'SE'):
        sword = [n for n in paths if 'IronSword' in n][0]
        im = Image.open(paths[sword][facing][0]).convert('RGBA')
        px = im.load()
        frames = []
        lens = []
        for f in range(cv.WEAPON_FRAMES):
            hilt, blade, every = [], [], []
            for y in range(CELL):
                for x in range(CELL):
                    p = px[f * CELL + x, y]
                    if p[3] < 128:
                        continue
                    r = role(p[:3])
                    every.append((x, y))
                    if r in 'aeh':
                        hilt.append((x, y))
                    elif r in 'trqpl':
                        blade.append((x, y))
            hx = sum(p[0] for p in hilt) / len(hilt)
            hy = sum(p[1] for p in hilt) / len(hilt)
            bx = sum(p[0] for p in blade) / len(blade)
            by = sum(p[1] for p in blade) / len(blade)
            n = math.hypot(bx - hx, by - hy) or 1
            d = ((bx - hx) / n, (by - hy) / n)
            ts = [(x - hx) * d[0] + (y - hy) * d[1] for x, y in every]
            lens.append(max(ts) - min(ts))
            frames.append({'dir': d})
        mean_centres = [[], [], [], []]
        for name, f in paths.items():
            for k in range(cv.WEAPON_FRAMES):
                mean_centres[k].append(f[facing][2][k])
        for k, fr in enumerate(frames):
            fr['centre'] = (sum(c[0] for c in mean_centres[k]) / len(mean_centres[k]) + pad, sum(c[1] for c in mean_centres[k]) / len(mean_centres[k]) + pad)
            fr['scale'] = lens[k] / max(lens)
        for k, fr in enumerate(frames):
            a, b = frames[min(k + 1, 3)]['centre'], frames[max(k, 1) - (1 if k == 3 else 0)]['centre']
            nxt = frames[min(k + 1, 3)]['centre']
            cur = frames[k]['centre']
            if k == 3:
                nxt, cur = frames[3]['centre'], frames[2]['centre']
            fr['travel'] = (nxt[0] - cur[0], nxt[1] - cur[1])
        out[facing] = frames
    return out


# --- drawing a weapon -----------------------------------------------------------------------
def sym(w):
    return lambda t: (-w(t) / 2, w(t) / 2)


def part(t0, t1, shape, ramp):
    """A piece of a weapon: from t0 to t1 along the axis, `shape(t)` giving (low, high) across it, in `ramp`."""
    return (t0, t1, shape, ramp)


def rod(t0, t1, w, ramp):
    return part(t0, t1, lambda t: (-w / 2, w / 2), ramp)


def taper(t0, t1, w0, w1, ramp):
    return part(t0, t1, lambda t: (-(w0 + (w1 - w0) * (t - t0) / (t1 - t0)) / 4 * 2 / 2, (w0 + (w1 - w0) * (t - t0) / (t1 - t0)) / 2) if False else
                (-(w0 + (w1 - w0) * (t - t0) / (t1 - t0)) / 2, (w0 + (w1 - w0) * (t - t0) / (t1 - t0)) / 2), ramp)


def swell(t0, t1, w, ramp, power=0.7):
    """Narrow at both ends, widest in the middle (a leaf, a blade of a spear)."""
    return part(t0, t1, lambda t: (-w / 2 * math.sin(math.pi * (t - t0) / (t1 - t0)) ** power, w / 2 * math.sin(math.pi * (t - t0) / (t1 - t0)) ** power), ramp)


def tone_of(u):
    return 0 if u < 0.28 else 1 if u < 0.6 else 2 if u < 0.86 else 3


def render(parts, facing, f, ref, fwd_sign=1.0):
    """One frame (48 rows of roles) of a weapon in the swing's frame f. `parts` are given with fwd_sign 1 meaning the swing's cutting side."""
    fr = ref[facing][f]
    d = fr['dir']
    n = (-d[1], d[0])
    # which way the cutting edge leads: the side of the axis the weapon travels toward
    lead = 1.0 if (n[0] * fr['travel'][0] + n[1] * fr['travel'][1]) >= 0 else -1.0
    lit_positive = (n[0] * LIGHT[0] + n[1] * LIGHT[1]) > 0
    tmin = min(p[0] for p in parts)
    tmax = max(p[1] for p in parts)
    sc = fr['scale']
    c = (tmin + tmax) / 2
    # the grip (t = 0) goes where the hand is: the weapon's middle is GRIP_BACK ahead of it
    origin = (fr['centre'][0] - d[0] * c * sc, fr['centre'][1] - d[1] * c * sc)
    mask = {}
    for y in range(CELL):
        for x in range(CELL):
            rx, ry = x + 0.5 - origin[0], y + 0.5 - origin[1]
            t = (rx * d[0] + ry * d[1]) / sc
            s = (rx * n[0] + ry * n[1]) * lead * fwd_sign
            for t0, t1, shape, ramp in parts:
                if t0 <= t <= t1:
                    lo, hi = shape(t)
                    if lo - 0.15 <= s <= hi + 0.15:
                        u = (s - lo) / ((hi - lo) or 1)
                        u = min(1, max(0, u))
                        # the lit side is the one facing the light: with the cutting side flipped, flip it back
                        positive_lit = lit_positive if lead * fwd_sign > 0 else not lit_positive
                        if positive_lit:
                            u = 1 - u
                        mask[(x, y)] = RAMPS[ramp][tone_of(u)]
    rows = [['.'] * CELL for _ in range(CELL)]
    for (x, y), ch in mask.items():
        rows[y][x] = ch
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < CELL and 0 <= ny < CELL and rows[ny][nx] == '.' and (nx, ny) not in mask:
                rows[ny][nx] = 'O'
    return [''.join(r) for r in rows]


def recentre(rows, centre):
    """Shift a frame so the middle of what is drawn is on `centre`, which is what the checker measures."""
    pts = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    dx = int(round(centre[0] - (min(xs) + max(xs) + 1) / 2))
    dy = int(round(centre[1] - (min(ys) + max(ys) + 1) / 2))
    out = [['.'] * CELL for _ in range(CELL)]
    for x, y in pts:
        if 0 <= x + dx < CELL and 0 <= y + dy < CELL:
            out[y + dy][x + dx] = rows[y][x]
    return [''.join(r) for r in out]


# --- the weapons ------------------------------------------------------------------------------
def crescent(t0, t1, reach, ramp, both=True):
    """An axe's blade: curved out from the shaft, widest at the edge."""
    def shape(t):
        k = (t - t0) / (t1 - t0)
        h = 0.9 + reach * math.sin(math.pi * k) ** 0.8
        return (-h if both else -0.8, h)
    return part(t0, t1, shape, ramp)


WEAPONS = {
    'dagger': dict(label='Dagger', parts=[
        rod(-1.4, 3.0, 1.6, 'leather'), rod(-2.0, -1.0, 2.4, 'gold'),
        rod(3.0, 3.9, 4.6, 'gold'), taper(3.9, 10.0, 2.8, 0.2, 'steel')]),
    'stiletto': dict(label='Stiletto', parts=[
        rod(-1.6, 2.6, 1.4, 'leather'), rod(-2.4, -1.5, 2.2, 'gold'),
        rod(2.6, 3.3, 3.6, 'gold'), taper(3.3, 12.2, 1.8, 0.2, 'steel')]),
    'kris': dict(label='Kris', parts=[
        rod(-1.8, 2.4, 1.5, 'leather'), rod(-2.6, -1.6, 2.4, 'gold'), rod(2.4, 3.2, 3.8, 'gold'),
        part(3.2, 11.6, lambda t: (0.95 * math.sin((t - 3.2) * 1.55) - (2.5 * (1 - (t - 3.2) / 8.4) + 0.2) / 2, 0.95 * math.sin((t - 3.2) * 1.55) + (2.5 * (1 - (t - 3.2) / 8.4) + 0.2) / 2), 'steel')]),
    'bone-dagger': dict(label='Bone dagger', parts=[
        rod(-1.6, 2.4, 1.8, 'leather'), rod(-2.4, -1.4, 2.8, 'bone'),
        rod(2.4, 3.0, 3.4, 'bone'),
        part(3.0, 11.0, lambda t: (-0.07 * (t - 3.0) ** 1.6 - 1.5 * (1 - ((t - 3.0) / 8.0) ** 1.4), -0.07 * (t - 3.0) ** 1.6 + 1.5 * (1 - ((t - 3.0) / 8.0) ** 1.4)), 'bone')]),
    'greatsword': dict(label='Greatsword', parts=[
        rod(-4.0, 2.0, 1.8, 'leather'), rod(-5.0, -3.6, 2.8, 'gold'),
        rod(2.0, 3.2, 7.0, 'gold'), taper(3.2, 12.6, 4.2, 3.4, 'steel'), taper(12.6, 14.6, 3.4, 0.2, 'steel')]),
    'scimitar': dict(label='Scimitar', parts=[
        rod(-2.0, 2.4, 1.6, 'leather'), rod(-2.8, -1.8, 2.6, 'gold'), rod(2.4, 3.2, 4.4, 'gold'),
        part(3.2, 12.5, lambda t: (-0.075 * (t - 3.2) ** 1.5 - 1.2 * (1 - ((t - 3.2) / 9.3) ** 3), -0.075 * (t - 3.2) ** 1.5 + 1.7 * (1 - ((t - 3.2) / 9.3) ** 3.4)), 'steel')]),
    'battle-axe': dict(label='Battle axe', parts=[
        rod(-5.5, 9.5, 1.6, 'wood'), rod(-5.5, -4.6, 2.4, 'iron'), rod(7.0, 8.4, 2.4, 'gold'),
        crescent(8.0, 12.5, 3.4, 'steel'), rod(9.2, 11.2, 2.0, 'gold')]),
    'war-hammer': dict(label='War hammer', parts=[
        rod(-5.0, 10.0, 1.6, 'wood'), rod(-5.0, -4.0, 2.4, 'iron'),
        rod(9.0, 13.0, 6.0, 'iron'), rod(8.6, 9.4, 3.0, 'gold'),
        part(10.2, 11.8, lambda t: (-(1.6 + 3.4 * max(0.0, 1 - abs(t - 11.0) / 0.8)), 0.0), 'iron')]),
    'spiked-mace': dict(label='Spiked mace', parts=[
        rod(-6.0, 9.0, 1.7, 'wood'), rod(-6.0, -5.0, 2.6, 'iron'), rod(5.0, 7.0, 2.2, 'leather'),
        part(8.8, 14.8, lambda t: (-math.sqrt(max(0, 3.0 ** 2 - (t - 11.8) ** 2)), math.sqrt(max(0, 3.0 ** 2 - (t - 11.8) ** 2))), 'iron'),
        part(10.9, 12.7, lambda t: (-5.2 + abs(t - 11.8) * 3, 5.2 - abs(t - 11.8) * 3), 'iron'),
        taper(14.8, 17.2, 1.8, 0.2, 'iron')]),
    'spear': dict(label='Spear', parts=[
        rod(-6.5, 10.5, 1.4, 'wood'), rod(-6.5, -5.6, 2.2, 'iron'), rod(8.6, 9.6, 3.4, 'gold'),
        swell(9.6, 15.6, 3.8, 'steel', 0.8)]),
    'crystal-staff': dict(label='Crystal staff', parts=[
        rod(-5.5, 11.0, 1.6, 'wood'), rod(-5.5, -4.5, 2.6, 'gold'), rod(10.2, 11.6, 3.6, 'gold'),
        swell(10.6, 17.6, 4.8, 'sapphire', 0.9), rod(11.4, 13.2, 0.9, 'sapphire')]),
}


def build(name, ref):
    out = {}
    parts = WEAPONS[name]['parts']
    for facing in ('NE', 'SE'):
        out[facing] = [recentre(render(parts, facing, f, ref), ref[facing][f]['centre']) for f in range(cv.WEAPON_FRAMES)]
    return out


def write_strips(folder, built):
    from PIL import Image
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    for name, by_facing in built.items():
        for facing, frames in by_facing.items():
            img = Image.new('RGBA', (CELL * len(frames), CELL), (0, 0, 0, 0))
            px = img.load()
            for f, rows in enumerate(frames):
                for y, line in enumerate(rows):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            px[f * CELL + x, y] = (*rgb[ch], 255)
            img.save(folder / f'{name}-attack{facing}.png')


def preview(built, path, who='slim'):
    """Each weapon behind the person's own attack frames, as it will be held, and enlarged."""
    import json
    from PIL import Image, ImageDraw
    data = json.loads((ROOT / 'poses' / 'base.js').read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
    person = {c['id']: c['frames'] for c in data['characters']}[who]
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    scale = 5
    names = list(built)
    sheet = Image.new('RGBA', (2 * 4 * CELL * scale // 2 + 40, len(names) * 2 * 0 + len(names) * CELL * scale // 1), (70, 74, 84, 255))
    cols = 2
    cw = 4 * CELL * scale // 2
    sheet = Image.new('RGBA', (cols * (4 * CELL * scale // 2 + 12), len(names) * (CELL * scale // 2 + 4)), (70, 74, 84, 255))
    half = scale * CELL // 2
    for r, name in enumerate(names):
        for c, facing in enumerate(('NE', 'SE')):
            for f in range(4):
                cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
                for y, line in enumerate(built[name][facing][f]):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            cell.putpixel((x, y), rgb[ch] + (255,))
                for y, line in enumerate(person['attack' + facing][f]):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            cell.putpixel((x + 8, y + 8), rgb[ch] + (255,))
                tile = cell.resize((half, half), Image.NEAREST)
                sheet.alpha_composite(tile, (c * (4 * half + 12) + f * half, r * (half + 4)))
    d = ImageDraw.Draw(sheet)
    for r, name in enumerate(names):
        d.text((4, r * (half + 4) + 2), WEAPONS[name]['label'], fill=(235, 238, 245, 255))
    sheet.save(path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    ref = swing()
    built = {name: build(name, ref) for name in WEAPONS}
    if args.preview:
        preview(built, args.preview)
        print('wrote', args.preview)
    if args.out:
        write_strips(args.out, built)
        print(f'wrote {len(built)} weapons -> {args.out}')


if __name__ == '__main__':
    main()
