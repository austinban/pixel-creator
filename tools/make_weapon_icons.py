#!/usr/bin/env python3
"""Display icons for the weapons: one 32 x 32 image each, in the amulets' style, for the shop and any weapon list.

Which icon belongs to which weapon is by NAME, and the name is the weapon's id without its prefix and facing:

    weapon asset ids        weapon-iron-sword-ne, weapon-iron-sword-se       the NAME is  iron-sword
    its display icon        icon-weapon-iron-sword                           (category "Weapon icons")

Both ends say so in the data: the icon asset has 'icon_for': 'iron-sword' and each weapon asset has 'icon': 'icon-weapon-iron-sword'.
ICONS below is the one list. It has an entry for every weapon, and make_assets.py stops with a message if a weapon has no icon or an icon
names a weapon that is not there, so they cannot drift apart.

The drawings are small 3D models, ray-cast with the creatures' renderer and finished with painted details (see make_weapon_icons3d.py, which also draws the amulets and has the model
of each weapon), all lying on the 45 degree diagonal rising to the upper right, bows too.

To add one: add the weapon (its strips, or a bow spec), draw it in make_weapon_icons3d.py, then one line in WEAPONS there. Preview all:

    python3 tools/make_weapon_icons.py --preview previews/weapon-icons.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
import make_weapon_icons3d as drawn  # noqa: E402

CELL = 32


def icon_prefix(stem):
    return f'icon-weapon-{stem}'


# --- the list: the one place a weapon and its icon are tied together ------------------------------
# (the weapon's NAME, shown as its label, how to draw it)
ICONS = list(drawn.WEAPONS)


def weapon_name(asset_id):
    """'weapon-iron-sword-ne' -> 'iron-sword' (None if it is not a weapon strip's id)."""
    if not asset_id.startswith('weapon-') or asset_id[-3:] not in ('-ne', '-se'):
        return None
    return asset_id[len('weapon-'):-3]


def build_icon_assets():
    assets = []
    for name, label, draw in ICONS:
        assets.append({
            'id': icon_prefix(name), 'label': f'{label} (display icon)', 'category': 'Weapon icons', 'kind': 'still', 'place': 'none',
            'icon_for': name,                                  # the weapon's NAME: its assets are weapon-NAME-ne and weapon-NAME-se
            'w': CELL, 'h': CELL, 'cols': 1, 'rows': 1, 'fps': 0,
            'anchor': {'x': CELL // 2, 'y': CELL // 2},
            'frames': [draw()],
        })
    return assets


def link_icons(assets):
    """Mark each weapon asset with its icon's id, and stop if a weapon has no icon or an icon has no weapon. Returns the problems."""
    problems = []
    icons = {a['icon_for']: a['id'] for a in assets if 'icon_for' in a}
    weapons = {}
    for a in assets:
        name = weapon_name(a['id']) if a.get('weapon') else None
        if name:
            weapons.setdefault(name, []).append(a)
    for name, group in weapons.items():
        if name not in icons:
            problems.append(f'weapon "{name}" has no display icon: add ({name!r}, label, drawing) to ICONS in tools/make_weapon_icons.py')
        for a in group:
            if name in icons:
                a['icon'] = icons[name]
    for name in icons:
        if name not in weapons:
            problems.append(f'display icon "{icons[name]}" is for a weapon called "{name}", and there is no such weapon')
    return problems


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    per_row = 6
    rows = -(-len(ICONS) // per_row)
    w = CELL * scale + 8
    sheet = Image.new('RGBA', (per_row * w, rows * (CELL * scale + 22)), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    for k, (name, label, draw) in enumerate(ICONS):
        x0, y0 = (k % per_row) * w, (k // per_row) * (CELL * scale + 22)
        cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        for y, line in enumerate(draw()):
            for x, ch in enumerate(line):
                if ch != '.':
                    cell.putpixel((x, y), rgb[ch] + (255,))
        sheet.alpha_composite(cell.resize((CELL * scale, CELL * scale), Image.NEAREST), (x0 + 4, y0 + 18))
        d.text((x0 + 6, y0 + 3), label, fill=(235, 238, 245, 255))
    sheet.save(path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
