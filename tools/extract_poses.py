#!/usr/bin/env python3
"""Turn folders of sprite PNGs into role-indexed base poses.

Every pixel becomes a one-letter colour role instead of a colour, so a
character is just a role -> colour map applied to the same poses. All the
bases share one master palette, so the same roles work across them.

    python3 tools/extract_poses.py cleric=path/to/cleric fighter=path/to/fighter

To add or replace one base without the others' folders to hand, merge it into the
existing poses/base.js:

    python3 tools/extract_poses.py --merge dog=sprites/dog

Each folder holds one PNG per pose, named like 20240427cleric-attackNE.png: the
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

# Roles are the master palette's colours, grouped into ramps. Names say what
# the colour is, not what it is used for: the cleric's dome and the fighter's
# hair are painted from the same slots.
GROUPS = [
    ('warm', 'Orange & gold'),
    ('rose', 'Coral & plum'),
    ('magenta', 'Magenta'),
    ('violet', 'Violet'),
    ('blue', 'Blue'),
    ('teal', 'Teal & mint'),
    ('green', 'Green'),
    ('neutral', 'Cream'),
    ('outline', 'Outline'),
]

# char, id, label, group, original colour
ROLES = [
    ('O', 'outline', 'Outline', 'outline', '372971'),
    ('a', 'orange', 'Orange', 'warm', 'f27746'),
    ('b', 'amber', 'Amber', 'warm', 'f5a13a'),
    ('c', 'salmon', 'Salmon', 'warm', 'f29485'),
    ('d', 'yellow', 'Yellow', 'warm', 'fad52f'),
    ('e', 'coral', 'Coral', 'rose', 'd95572'),
    ('f', 'orchid', 'Orchid', 'rose', 'af417d'),
    ('g', 'plum', 'Plum', 'rose', '7d426e'),
    ('h', 'magenta-dark', 'Magenta dark', 'magenta', 'a80d70'),
    ('i', 'magenta', 'Magenta', 'magenta', 'c9126e'),
    ('j', 'hot-pink', 'Hot pink', 'magenta', 'f2186c'),
    ('k', 'indigo', 'Indigo', 'violet', '4e4883'),
    ('l', 'lavender', 'Lavender', 'violet', '6b6a9c'),
    ('m', 'blue', 'Blue', 'blue', '455eb1'),
    ('n', 'sky', 'Sky', 'blue', '4394d6'),
    ('o', 'cyan', 'Cyan', 'blue', '08c3ee'),
    ('p', 'steel', 'Steel', 'blue', '7491ae'),
    ('q', 'teal', 'Teal', 'teal', '84bdc3'),
    ('r', 'mint', 'Mint', 'teal', 'a8e3d1'),
    ('s', 'deep-teal', 'Deep teal', 'teal', '007585'),
    ('t', 'cream', 'Cream', 'neutral', 'faf1e3'),
    ('u', 'purple', 'Purple', 'violet', '8a0c86'),
    ('v', 'violet', 'Violet', 'violet', 'b13dff'),
    ('w', 'grape', 'Grape', 'violet', '47255d'),
    ('x', 'eggplant', 'Eggplant', 'violet', '4e1868'),
    ('y', 'fuchsia', 'Fuchsia', 'magenta', 'd92cbe'),
    ('z', 'lime', 'Lime', 'green', 'a9e030'),
    ('A', 'green', 'Green', 'green', '55dc34'),
    ('B', 'emerald', 'Emerald', 'green', '00ab56'),
    ('C', 'sand', 'Sand', 'neutral', 'fae1aa'),
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


def extract_frames(path, cols, rows, by_colour, to_colour):
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
                    sys.exit(f'{path}: colour #{r:02x}{g:02x}{b:02x} at ({ox + x}, {oy + y}) has no role; add it to ROLES')
            lines.append(line)
        frames.append(lines)

        # Re-render this frame from its roles and compare with the source.
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                want = px[ox + x, oy + y]
                got = (0, 0, 0, 0) if char == '.' else (*to_colour[char], 255)
                if want != got:
                    sys.exit(f'{path}: round trip differs at ({ox + x}, {oy + y})')
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('bases', nargs='+', metavar='NAME=FOLDER', help='a base character and the folder of its pose PNGs, e.g. cleric=sprites/cleric')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'poses' / 'base.js')
    parser.add_argument('--merge', action='store_true', help='keep the bases already in the output and add or replace the ones named')
    args = parser.parse_args()

    by_colour = {tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4)): char for char, _, _, _, hex_ in ROLES}
    to_colour = {char: rgb for rgb, char in by_colour.items()}

    characters = []
    frames_checked = 0
    for spec in args.bases:
        name, sep, folder = spec.partition('=')
        if not sep or not name or not folder:
            sys.exit(f'{spec}: expected NAME=FOLDER')
        frames_by_pose = {}
        for action, facing, cols, rows in POSES:
            pose_id = action + facing
            frames = extract_frames(find_source(Path(folder), pose_id), cols, rows, by_colour, to_colour)
            frames_by_pose[pose_id] = frames
            frames_checked += len(frames)
        characters.append({'id': name.lower(), 'label': name.capitalize(), 'frames': frames_by_pose})

    kept = []
    if args.merge:
        if not args.out.exists():
            sys.exit(f'--merge needs an existing {args.out}')
        existing = json.loads(args.out.read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
        if existing.get('cell') != CELL or [p['id'] for p in existing.get('poses', [])] != [a + f for a, f, _, _ in POSES]:
            sys.exit(f'{args.out} was built from a different pose list; rebuild it from all the bases instead of merging')
        replaced = {c['id'] for c in characters}
        kept = [c for c in existing['characters'] if c['id'] not in replaced]

    data = {
        'cell': CELL,
        'ground': GROUND,
        'groups': [{'id': i, 'label': l, 'hue': i not in ('outline', 'neutral')} for i, l in GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ROLES],
        'poses': [
            {'id': a + f, 'label': f'{a.capitalize()} {f}', 'action': a, 'facing': f, 'cols': c, 'rows': r}
            for a, f, c, r in POSES
        ],
        'characters': kept + characters,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.BASE_POSES = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    total = len(kept) + len(characters)
    print(f'{frames_checked} frames across {len(characters)} bases ({total} in all), all re-rendered identical to the source -> {args.out}')


if __name__ == '__main__':
    main()
