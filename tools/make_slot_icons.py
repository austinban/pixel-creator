#!/usr/bin/env python3
"""Equipment slot icons: one 32 x 32 picture each for the Weapon, Armor and Trinket slots, in the amulets' style (the shared palette, lit from the upper left, one-pixel outline).

    weapon    a sword on the diagonal: silver blade, gold crossguard, cord grip, gold pommel
    armor     a breastplate with pauldrons: steel plates trimmed in gold, a ridge down the middle, rivets
    trinket   a ring with a cyan gem on gold prongs

Each is a stack of shapes shaded from the light, built with the same `Icon` as the amulets, so a change is a few lines.

    python3 tools/make_slot_icons.py --preview previews/slot-icons.png
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from make_amulets import Icon, RAMPS, disc, diamond, ellipse, minus, poly, ring  # noqa: E402,F401

RAMPS['gem'] = ('r', 'o', 'n', 'm')           # a cyan gem: mint, cyan, sky, blue
RAMPS['plate'] = ('r', 'q', 'p', 'l')


def bar(p0, p1, w0, w1):
    """A straight piece from p0 to p1, w0 wide at p0 and w1 at p1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    return poly([(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
                 (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)])


def scaled(points, about, k):
    return [(about[0] + (x - about[0]) * k, about[1] + (y - about[1]) * k) for x, y in points]


def weapon():
    i = Icon()
    i.layer(bar((9.5, 22.5), (24.6, 7.4), 4.6, 1.2), 'silver')                  # the blade, tapering to the point
    i.layer(bar((11.0, 21.0), (23.2, 8.8), 1.3, 0.6), 'silver', flat=0)           # the bright edge
    i.layer(bar((6.0, 19.0), (13.0, 26.0), 2.6, 2.6), 'gold')                   # the crossguard
    i.layer(bar((8.6, 23.4), (4.6, 27.4), 2.4, 2.4), 'cord')                    # the grip
    i.layer(disc(3.8, 28.2, 2.1), 'gold')                                        # the pommel
    i.dot(5, 20, 't')
    return i.outline()


def armor():
    i = Icon()
    body = [(5, 9), (11, 5), (14, 7.5), (16, 8.5), (18, 7.5), (21, 5), (27, 9), (25.5, 15), (23, 21), (20, 27), (16, 28.5), (12, 27), (9, 21), (6.5, 15)]
    i.layer(poly(body), 'gold')                                                  # the trim
    i.layer(poly(scaled(body, (16, 17), 0.82)), 'plate')                         # the plates
    i.layer(disc(7.4, 10.4, 3.6), 'gold')                                        # the pauldrons, trimmed too
    i.layer(disc(7.2, 10.2, 2.4), 'plate')
    i.layer(disc(24.6, 10.4, 3.6), 'gold')
    i.layer(disc(24.8, 10.2, 2.4), 'plate')
    i.layer(bar((16, 11), (16, 25), 1.6, 1.6), 'plate', flat=0)                  # the ridge down the middle
    i.layer(bar((11, 17.5), (21, 17.5), 1.3, 1.3), 'gold', flat=1)               # a belt of trim across it
    for x, y in ((11, 14), (21, 14), (12, 22), (20, 22)):
        i.dot(x, y, 'd')                                                         # rivets
    i.dot(10, 8, 't')
    return i.outline()


def trinket():
    i = Icon()
    i.layer(minus(ellipse(16, 21, 9.6, 8.4), ellipse(16, 21.6, 5.6, 4.8)), 'gold', centre=(16, 21), radius=10)    # the band
    i.layer(poly([(10.5, 14.6), (21.5, 14.6), (19.6, 18.4), (12.4, 18.4)]), 'gold')                                  # the setting
    i.layer(diamond(16, 10.2, 5.8, 5.6), 'gem')                                                                      # the gem
    i.layer(poly([(16, 6.2), (19.6, 10.2), (16, 14.2), (12.4, 10.2)]), 'gem', flat=None)
    i.layer(poly([(16, 8.4), (18, 10.2), (16, 12.2), (14, 10.2)]), 'gem', flat=0)
    i.dot(13, 8, 't')
    i.dot(25, 5, 't')
    i.dot(24, 6, 'r')
    i.dot(26, 6, 'r')
    i.dot(25, 7, 'r')
    return i.outline()


ICONS = [('slot-weapon', 'Weapon slot', weapon), ('slot-armor', 'Armor slot', armor), ('slot-trinket', 'Trinket slot', trinket)]


CATEGORY = 'UI'
FOLDER = 'slot-icons'
CELL = 32


def build_assets():
    """One still asset per slot (`slot-weapon`, `slot-armor`, `slot-trinket`), 32 x 32, anchored at the middle; nothing is placed on the map."""
    make = family(CATEGORY, CELL, CELL, (CELL // 2, CELL // 2), place='none', folder=FOLDER)
    return [make(id, label, 'still', [icon()]) for id, label, icon in ICONS]


def write_package(folder):
    """Beside the sheets: slot-icons.json, which file is which slot."""
    body = {id.replace('slot-', ''): {'label': label, 'file': f'{id}.png', 'cell': [CELL, CELL]} for id, label, _ in ICONS}
    write_json(folder, 'slot-icons.json', 'The equipment slot icons in this folder. See README.md beside this file.', {'slots': body})


def preview(path, scale=10):
    from PIL import Image
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    sheet = Image.new('RGB', ((len(ICONS) * 34 + 2) * scale + 40 * 3, 34 * scale + 10 * scale), (44, 40, 76))
    for n, (_, _, make) in enumerate(ICONS):
        rows = make()
        ox = (1 + n * 34) * scale
        for y, line in enumerate(rows):
            for x, c in enumerate(line):
                if c != '.':
                    for dy in range(scale):
                        for dx in range(scale):
                            sheet.putpixel((ox + x * scale + dx, scale + y * scale + dy), rgb[c])
        for y, line in enumerate(rows):                                   # and at true size, beside it, below
            for x, c in enumerate(line):
                if c != '.':
                    sheet.putpixel((ox + x, 34 * scale + 3 + y), rgb[c])
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the slot icons, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
