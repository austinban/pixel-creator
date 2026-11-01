#!/usr/bin/env python3
"""Turn weapon sprite strips into assets.

Each weapon is two PNG strips, one per facing, named for the weapon and the pose they go with:

    sprites/weapons/20240429weapons-IronAxeattackNE.png     4 frames of 48 x 48, side by side (192 x 48)
    sprites/weapons/20240429weapons-IronAxeattackSE.png

A weapon cell is bigger than a character's: 48 x 48 against 32 x 32, so a swing can reach past the
character's edge. The character sits in the middle of it, 8 pixels in from each side, so laying a
weapon frame over the matching attack frame of a character puts the weapon in the hand. Each
becomes an asset in the Weapons category ('Axe NE' and 'Axe SE'), painted in palette roles so it
recolours like everything else: an exact palette match where there is one, otherwise the nearest
colour. Semi-transparent pixels count as painted only if they are at least half opaque.

Used by make_assets.py, which writes assets/data.js; run that to rebuild.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

DEFAULT_DIR = Path(__file__).resolve().parent.parent / 'sprites' / 'weapons'
CELL = ep.CELL                # a character's cell
FRAMES = 4                  # an attack has four frames
SOLID = 128
# 'iron-axe-attackNE.png' and '20240429weapons-IronAxeattackNE.png' both work.
FILE = re.compile(r'^(?P<name>.+?)-?attack(?P<facing>NE|SE)\.png$')


def clean(name):
    """The weapon's own name: without a leading date or the folder's 'weapons-'."""
    name = re.sub(r'^\d+', '', name)
    name = re.sub(r'^weapons?[-_ ]*', '', name, flags=re.I)
    return name or 'weapon'


def label_of(name):
    """'IronAxe', 'iron-axe' or '20240429weapons-IronAxe' -> 'Iron axe'."""
    spaced = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', clean(name)).replace('_', ' ').replace('-', ' ')
    return ' '.join(spaced.split()).capitalize() or name


def build_weapon_assets(folder=DEFAULT_DIR):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    from PIL import Image

    palette = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): c for c, _, _, _, h in ep.ROLES}
    nearest = {}

    def role(rgb):
        if rgb in palette:
            return palette[rgb]
        if rgb not in nearest:
            nearest[rgb] = palette[min(palette, key=lambda p: sum((a - b) ** 2 for a, b in zip(p, rgb)))]
        return nearest[rgb]

    found = {}
    for path in sorted(folder.glob('*.png')):
        m = FILE.match(path.name)
        if not m:
            print(f'weapons: skipping {path.name} (expected NAME-attackNE.png or NAME-attackSE.png)', file=sys.stderr)
            continue
        found.setdefault(clean(m['name']), {})[m['facing']] = path

    assets = []
    for name in sorted(found):
        for facing in ('NE', 'SE'):
            path = found[name].get(facing)
            if not path:
                print(f'weapons: {name} has no {facing} strip, so it will only show for the other facing', file=sys.stderr)
                continue
            im = Image.open(path).convert('RGBA')
            cell = im.height
            if im.width != FRAMES * cell or cell < CELL:
                sys.exit(f'{path}: expected {FRAMES} square frames side by side (like 192x48), got {im.width}x{im.height}')
            px = im.load()
            frames = []
            for f in range(FRAMES):
                rows = []
                for y in range(cell):
                    row = ''
                    for x in range(cell):
                        r, g, b, a = px[f * cell + x, y]
                        row += role((r, g, b)) if a >= SOLID else '.'
                    rows.append(row)
                frames.append(rows)
            label = f'{label_of(name)} {facing}'
            assets.append({
                'id': f'weapon-{re.sub(r"[^a-z0-9]+", "-", label_of(name).lower()).strip("-")}-{facing.lower()}',
                'label': label, 'category': 'Weapons', 'kind': 'animation', 'place': 'none',
                'weapon': name, 'facing': facing,
                'w': cell, 'h': cell, 'cols': FRAMES, 'rows': 1, 'fps': 8,
                'anchor': {'x': cell // 2, 'y': cell},
                'frames': frames,
            })
    return assets


if __name__ == '__main__':
    found = build_weapon_assets(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
    print(f'{len(found)} weapon strips: ' + ', '.join(a['label'] for a in found))
