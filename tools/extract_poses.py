#!/usr/bin/env python3
"""Turn a folder of sprite PNGs into role-indexed base poses.

Every pixel becomes a one-letter colour role instead of a colour, so a
character is just a role -> colour map applied to the same poses.

    python3 tools/extract_poses.py path/to/sprites

The folder holds one PNG per pose, named like 20240427cleric-attackNE.png: the
pose id (attackNE) is whatever follows the last hyphen.

Writes poses/base.js. Each frame is re-rendered from its roles and compared
with the source PNG, so a mismatch stops the run instead of shipping.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

CELL = 32
GROUND = 28  # last row of the feet in every upright frame

GROUPS = [
    ('skin', 'Head & skin'),
    ('cloth', 'Clothes'),
    ('accent', 'Accent'),
    ('mouth', 'Mouth'),
    ('outline', 'Outline'),
]

# char, id, label, group, original colour
ROLES = [
    ('O', 'outline', 'Outline', 'outline', '372971'),
    ('h', 'skin-light', 'Head highlight', 'skin', 'f27746'),
    ('b', 'skin', 'Head base', 'skin', 'd95572'),
    ('s', 'skin-shadow', 'Head shadow', 'skin', 'af417d'),
    ('6', 'skin-pale', 'Pale skin', 'skin', 'f29485'),
    ('4', 'skin-warm', 'Warm skin', 'skin', 'f5a13a'),
    ('p', 'cloth-shadow', 'Cloth shadow', 'cloth', '4e4883'),
    ('u', 'cloth-dark', 'Cloth dark', 'cloth', '455eb1'),
    ('t', 'cloth-mid', 'Cloth mid', 'cloth', '84bdc3'),
    ('m', 'cloth-light', 'Cloth light', 'cloth', 'a8e3d1'),
    ('c', 'cloth-highlight', 'Cloth highlight', 'cloth', 'faf1e3'),
    ('g', 'cloth-grey', 'Cloth grey', 'cloth', '7491ae'),
    ('k', 'cloth-bright', 'Cloth bright', 'cloth', '4394d6'),
    ('3', 'cloth-deep', 'Cloth deep', 'cloth', '007585'),
    ('y', 'accent', 'Accent', 'accent', 'fad52f'),
    ('1', 'mouth-dark', 'Mouth dark', 'mouth', 'a80d70'),
    ('2', 'mouth', 'Mouth', 'mouth', 'c9126e'),
    ('5', 'mouth-bright', 'Mouth bright', 'mouth', 'f2186c'),
]

# action, facing, columns, rows. Pose ids are action + facing, as in the
# source file names (attackNE). NE faces away from the camera, SE toward it.
POSES = [
    ('attack', 'NE', 4, 1),
    ('attack', 'SE', 4, 1),
    ('charging', 'NE', 1, 1),
    ('charging', 'SE', 1, 1),
    ('damage', 'NE', 1, 1),
    ('damage', 'SE', 1, 1),
    ('dead', 'NE', 1, 1),
    ('dead', 'SE', 1, 1),
    ('release', 'NE', 1, 1),
    ('release', 'SE', 1, 1),
    ('walking', 'NE', 4, 2),
    ('walking', 'SE', 4, 2),
    ('weak', 'NE', 1, 1),
    ('weak', 'SE', 1, 1),
]


def find_source(folder, pose_id):
    matches = sorted(folder.glob(f'*-{pose_id}.png'))
    if len(matches) != 1:
        sys.exit(f'{folder}: expected exactly one file ending -{pose_id}.png, found {len(matches)}')
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('src', type=Path, help='folder holding one PNG per pose, e.g. 20240427cleric-attackNE.png')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'poses' / 'base.js')
    args = parser.parse_args()

    by_colour = {tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4)): char for char, _, _, _, hex_ in ROLES}
    to_colour = {char: rgb for rgb, char in by_colour.items()}

    poses = []
    frames_checked = 0
    for action, facing, cols, rows in POSES:
        pose_id = action + facing
        path = find_source(args.src, pose_id)
        image = Image.open(path).convert('RGBA')
        if image.size != (cols * CELL, rows * CELL):
            sys.exit(f'{path}: expected {cols * CELL}x{rows * CELL}, got {image.size[0]}x{image.size[1]}')
        px = image.load()

        frames = []
        for index in range(cols * rows):
            ox, oy = (index % cols) * CELL, (index // cols) * CELL
            lines = []
            for y in range(CELL):
                line = ''
                for x in range(CELL):
                    r, g, b, a = px[ox + x, oy + y]
                    if a == 0:
                        line += '.'
                    elif a != 255:
                        sys.exit(f'{path}: semi-transparent pixel at ({ox + x}, {oy + y})')
                    elif (r, g, b) in by_colour:
                        line += by_colour[(r, g, b)]
                    else:
                        sys.exit(f'{path}: unknown colour #{r:02x}{g:02x}{b:02x} at ({ox + x}, {oy + y})')
                lines.append(line)
            frames.append(lines)

            # Re-render this frame from its roles and compare with the source.
            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    want = px[ox + x, oy + y]
                    got = (0, 0, 0, 0) if char == '.' else (*to_colour[char], 255)
                    if want != got:
                        sys.exit(f'{path}: round trip differs at ({ox + x}, {oy + y})')
            frames_checked += 1

        poses.append({
            'id': pose_id,
            'label': f'{action.capitalize()} {facing}',
            'action': action,
            'facing': facing,
            'cols': cols,
            'rows': rows,
            'frames': frames,
        })

    data = {
        'cell': CELL,
        'ground': GROUND,
        'groups': [{'id': i, 'label': l} for i, l in GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ROLES],
        'poses': poses,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.BASE_POSES = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(f'{frames_checked} frames across {len(poses)} poses, all re-rendered identical to the source -> {args.out}')


if __name__ == '__main__':
    main()
