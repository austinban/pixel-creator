#!/usr/bin/env python3
"""Move every sprite PNG from one palette to another by swapping colours: no rebuilding from poses.

When the palette in extract_poses.ROLES changes, run this once:

    1. Before editing ROLES, copy the old hex values into LEGACY_HEX (extract_poses.py), or keep a JSON of {role letter: hex}.
    2. Edit the hex values in ROLES.
    3. python3 tools/recolor.py            # recolours sprites/**/*.png in place, and refreshes the role colours in poses/base.js
    4. python3 tools/make_assets.py --png-dir sprites/assets     # rebuilds assets/data.js and the generated sheets in the new colours

Every pixel's old colour is looked up and swapped for the new colour of the same role. A colour that is in neither palette (the ground sheet and the
weapon strips have a few) is snapped to the nearest old colour first, the way tools/make_ground.py and tools/make_weapons.py read them.
It is safe to run again: pixels already in the new palette are left alone. Roles are letters, so the pose data, the assets and the app's saved colours
all keep working; only the hex values change.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep

ROOT = Path(__file__).resolve().parent.parent


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def recolor_file(path, swap, old_colours, new_colours, snap):
    from PIL import Image
    im = Image.open(path).convert('RGBA')
    px = im.load()
    changed = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            c = (r, g, b)
            if c in new_colours and c not in swap:
                continue
            if c not in swap:
                if c not in snap:
                    snap[c] = swap[min(old_colours, key=lambda q: sum((u - v) ** 2 for u, v in zip(q, c)))]
                swap[c] = snap[c]
            px[x, y] = (*swap[c], a)
            changed += 1
    if changed:
        im.save(path)
    return changed


def refresh_base_roles(path):
    """poses/base.js stores the role colours next to the pose data; update them (the poses are role letters and do not change)."""
    if not path.exists():
        return False
    prefix = 'window.BASE_POSES = '
    data = json.loads(path.read_text()[len(prefix):].rstrip().rstrip(';'))
    data['roles'] = [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ep.ROLES]
    path.write_text(prefix + json.dumps(data, separators=(',', ':')) + ';\n')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('folders', nargs='*', type=Path, default=[ROOT / 'sprites'], help='folders of PNGs to recolour (default: sprites/)')
    parser.add_argument('--from', dest='source', type=Path, help='JSON of {role letter: hex} for the old palette (default: LEGACY_HEX in extract_poses.py)')
    args = parser.parse_args()

    legacy = json.loads(args.source.read_text()) if args.source else ep.LEGACY_HEX
    new = {c: rgb(h) for c, _, _, _, h in ep.ROLES}
    old = {rgb(h): c for c, h in legacy.items()}
    swap = {o: new[c] for o, c in old.items()}
    new_colours = set(new.values())
    snap = {}
    files = changed = pixels = 0
    for folder in args.folders:
        for path in sorted(folder.rglob('*.png')):
            files += 1
            n = recolor_file(path, swap, set(old), new_colours, snap)
            pixels += n
            changed += bool(n)
    print(f'{files} PNGs checked, {changed} recoloured ({pixels} pixels); {len(snap)} off-palette colours snapped to the nearest role')
    if refresh_base_roles(ROOT / 'poses' / 'base.js'):
        print('poses/base.js: role colours refreshed')


if __name__ == '__main__':
    main()
