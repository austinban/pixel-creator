#!/usr/bin/env python3
"""Small icons for the game's text: gold, experience points and the skulls that say how hard a fight is. Each is 16 x 16, the size of a line of text, drawn in the shared palette with a one-pixel outline and lit from the upper left.

    gold       a little golden mushroom, a friendlier thing than a coin, and the game's own kind of thing
    xp         a four-point star of cyan light, brightest at the middle
    skulls     one skull in three colours for how hard a fight is: green (easy), yellow (even) and red (hard)

A skull is 13 x 14 inside the 16 x 16 cell, so a row of them for a difficulty of one to three sits closely (14 pixels apart). The palette has no pure red, so the red skull is its coral, salmon and magenta.

    python3 tools/make_hud_icons.py --preview previews/hud-icons.png     every icon enlarged, then at the size of text beside a number and a row of skulls
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

CELL = 16
FOLDER = 'hud-icons'
CATEGORY = 'UI'
LIGHT = (-0.45, -0.89)


def canvas():
    return [['.'] * CELL for _ in range(CELL)]


def inside_poly(pts, x, y):
    c = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def fill_where(g, test, role_at):
    """Every pixel for which test(x, y, dx, dy) holds, with the role role_at(x, y, dx, dy) gives."""
    for y in range(CELL):
        for x in range(CELL):
            if test(x, y):
                g[y][x] = role_at(x, y)


def outline(g):
    """A one-pixel `O` round everything painted, on the empty pixels that touch it."""
    out = [row[:] for row in g]
    for y in range(CELL):
        for x in range(CELL):
            if g[y][x] != '.':
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < CELL and 0 <= ny < CELL and g[ny][nx] != '.':
                    out[y][x] = 'O'
                    break
    return out


def rows(g):
    return [''.join(r) for r in g]


def lit(dx, dy, r):
    """0 where the surface faces the light (upper left), 1 where it faces away."""
    return 0.5 + 0.5 * ((dx * -LIGHT[0] + dy * -LIGHT[1]) / (r or 1))


def pick(ramp, t):
    return ramp[max(0, min(len(ramp) - 1, int(t * len(ramp))))]


def mushroom():
    """A little golden mushroom: an amber cap with cream spots over a cream stem, a gill line under the cap."""
    g = canvas()

    def cap(x, y):
        dx, dy = (x + 0.5 - 8) / 6.3, (y + 0.5 - 7.2) / 4.9
        return dx * dx + dy * dy <= 1.0 and y + 0.5 <= 8.6

    def cap_role(x, y):
        dx, dy = x + 0.5 - 8, y + 0.5 - 7.2
        t = lit(dx / 1.3, dy, math.hypot(dx / 1.3, dy))
        return pick('dbba', t)
    fill_where(g, cap, cap_role)
    for y in range(8, 14):                                           # the stem
        for x in range(6, 10):
            g[y][x] = 't' if x == 6 else ('c' if x == 9 else 'C')
    for x in range(2, 14):                                           # the gill line under the cap
        if g[8][x] != '.':
            g[8][x] = 'a'
    for x, y in ((6, 4), (9, 3), (11, 6), (4, 6)):                   # spots
        g[y][x] = 't'
        if x < 11 and g[y + 1][x + 1] not in '.t':
            pass
    g[13][5] = g[13][10] = 'c'                                       # the foot
    return rows(outline(g))


# --- gold and experience ----------------------------------------------------------------------------
def star():
    """A four-point star of cyan light, brightest at the middle, with two tiny sparkles."""
    g = canvas()
    pts = [(8, 1.5), (9.7, 6.3), (14.5, 8), (9.7, 9.7), (8, 14.5), (6.3, 9.7), (1.5, 8), (6.3, 6.3)]
    pts = [(8 + (x - 8) * 0.92, 8 + (y - 8) * 0.92) for x, y in pts]

    def role(x, y):
        dx, dy = x + 0.5 - 8, y + 0.5 - 8
        d = math.hypot(dx, dy)
        if d < 1.6:
            return 't'
        t = lit(dx, dy, d) * 0.55 + min(1.0, d / 7.0) * 0.45
        return pick('roon', t)
    fill_where(g, lambda x, y: inside_poly(pts, x + 0.5, y + 0.5), role)
    return rows(outline(g))


# --- skulls --------------------------------------------------------------------------------
SKULL = [
    '....OOOOO....',
    '..OOLLLLLOO..',
    '.OLLLLLLLMMO.',
    '.OLLLLLLMMMO.',
    'OLLLLLLLMMMMO',
    'OLLXXXLLXXXMO',
    'OLLXXXMMXXXMO',
    'OLLXXXMMXXXMO',
    '.OLLLMXXMMMO.',
    '.OOMMMXXMMOO.',
    '..OOMMMMMMO..',
    '...OLOMOMLO..',
    '...OLOMOMMO..',
    '....OOOOOOO..'[:13],
]
SKULL_COLOURS = {                      # light, middle, dark, and the eyes
    'green': dict(L='z', M='A', D='B'),
    'yellow': dict(L='d', M='b', D='a'),
    'red': dict(L='c', M='e', D='h'),
}


def skull(colour):
    """The skull in a colour: 13 x 14, its eye sockets and nose black, a row of teeth, centred in the 16 x 16 cell."""
    c = SKULL_COLOURS[colour]
    g = canvas()
    for y, line in enumerate(SKULL):
        assert len(line) == 13, (y, line)
        for x, ch in enumerate(line):
            if ch == '.':
                continue
            g[y + 1][x + 1] = {'L': c['L'], 'M': c['M'], 'D': c['D'], 'X': 'x', 'O': 'O'}[ch]
    return rows(g)


ICONS = [
    ('icon-gold', 'Gold (a golden mushroom)', mushroom),
    ('icon-xp', 'Experience points (a star of light)', star),
    ('icon-skull-green', 'Fight difficulty: easy (green skull)', lambda: skull('green')),
    ('icon-skull-yellow', 'Fight difficulty: even (yellow skull)', lambda: skull('yellow')),
    ('icon-skull-red', 'Fight difficulty: hard (red skull)', lambda: skull('red')),
]


def build_assets():
    """Five 16 x 16 stills in category UI (`icon-gold`, `icon-xp`, `icon-skull-green`, `-yellow`, `-red`), anchored at the middle; nothing is placed on the map."""
    make = family(CATEGORY, CELL, CELL, (CELL // 2, CELL // 2), place='none', folder=FOLDER)
    return [make(id, label, 'still', [icon()]) for id, label, icon in ICONS]


def write_package(folder):
    """Beside the sheets: hud-icons.json, which file is which icon."""
    write_json(folder, 'hud-icons.json', 'The small text icons in this folder. See README.md beside this file.',
               {'cell': [CELL, CELL], 'icons': {id.replace('icon-', ''): {'label': label, 'file': f'{id}.png'} for id, label, _ in ICONS},
                'skull': {'size': [13, 14], 'advance': 14, 'about': 'a skull fills 13 x 14 of its 16 x 16 cell, from (1, 1); put them 14 pixels apart in a row'}})


def _image(rows_, rgb):
    from PIL import Image
    im = Image.new('RGBA', (len(rows_[0]), len(rows_)), (0, 0, 0, 0))
    for y, row in enumerate(rows_):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    return im


def preview(path, scale=10):
    """Every icon enlarged in a row, and below that at 1x and 2x beside a line of text-sized marks."""
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i, _ in ((0, 0), (2, 0), (4, 0))) for c, _, _, _, h in ep.ROLES}
    images = [_image(icon(), rgb) for _, _, icon in ICONS]
    pad = 2
    w = (len(images) * (CELL + pad) + pad) * scale
    sheet = Image.new('RGBA', (w, (CELL + 2 * pad) * scale + 120), (36, 38, 56, 255))
    for i, im in enumerate(images):
        sheet.alpha_composite(im.resize((CELL * scale, CELL * scale), Image.NEAREST), ((pad + i * (CELL + pad)) * scale, pad * scale))
    # in use: at 2x, with a line of text and a row of skulls
    d = ImageDraw.Draw(sheet)
    y0 = (CELL + 2 * pad) * scale + 12
    x = 16
    for k, label in ((0, '120 g'), (1, '45 xp')):
        sheet.alpha_composite(images[k].resize((CELL * 2, CELL * 2), Image.NEAREST), (x, y0))
        d.text((x + CELL * 2 + 4, y0 + 10), label, fill=(230, 220, 200, 255))
        x += CELL * 2 + 84
    x += 30
    for k, n in ((2, 1), (3, 2), (4, 3)):
        for j in range(n):
            sheet.alpha_composite(images[k].resize((CELL * 2, CELL * 2), Image.NEAREST), (x, y0))
            x += CELL * 2 - 4
        x += 24
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='every icon enlarged, and at the size of text')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the icons, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
