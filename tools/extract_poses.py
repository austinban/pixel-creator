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

# char, id, label, group, colour (the moody spirit-realm palette)
ROLES = [
    ('O', 'outline', 'Outline', 'outline', '1a1233'),
    ('a', 'orange', 'Orange', 'warm', 'c9663f'),
    ('b', 'amber', 'Amber', 'warm', 'd69a4a'),
    ('c', 'salmon', 'Salmon', 'warm', 'c98480'),
    ('d', 'yellow', 'Yellow', 'warm', 'e3c868'),
    ('e', 'coral', 'Coral', 'rose', 'b8506a'),
    ('f', 'orchid', 'Orchid', 'rose', '8e4a86'),
    ('g', 'plum', 'Plum', 'rose', '5e3560'),
    ('h', 'magenta-dark', 'Magenta dark', 'magenta', '7a1d5c'),
    ('i', 'magenta', 'Magenta', 'magenta', '9c2a72'),
    ('j', 'hot-pink', 'Hot pink', 'magenta', 'd23d86'),
    ('k', 'indigo', 'Indigo', 'violet', '322e5e'),
    ('l', 'lavender', 'Lavender', 'violet', '524f85'),
    ('m', 'blue', 'Blue', 'blue', '34468a'),
    ('n', 'sky', 'Sky', 'blue', '3a78b8'),
    ('o', 'cyan', 'Cyan', 'blue', '3ad8e6'),
    ('p', 'steel', 'Steel', 'blue', '5a7390'),
    ('q', 'teal', 'Teal', 'teal', '5fa3a6'),
    ('r', 'mint', 'Mint', 'teal', '8fd4c0'),
    ('s', 'deep-teal', 'Deep teal', 'teal', '0e5a63'),
    ('t', 'cream', 'Cream', 'neutral', 'e6dcc8'),
    ('u', 'purple', 'Purple', 'violet', '66206a'),
    ('v', 'violet', 'Violet', 'violet', '8f4fe0'),
    ('w', 'grape', 'Grape', 'violet', '3a1a52'),
    ('x', 'eggplant', 'Eggplant', 'violet', '2f1a45'),
    ('y', 'fuchsia', 'Fuchsia', 'magenta', 'b0399c'),
    ('z', 'lime', 'Lime', 'green', '86b83e'),
    ('A', 'green', 'Green', 'green', '4a9e3c'),
    ('B', 'emerald', 'Emerald', 'green', '12804f'),
    ('C', 'sand', 'Sand', 'neutral', 'd9c598'),
]

# The colours the roles had before the moodier palette (the source PNGs that are not ours, such as the ground sheet and the weapon strips, still use them).
# Anything that reads a PNG accepts either set; everything we write uses the current hex above.
LEGACY_HEX = {'O': '372971', 'a': 'f27746', 'b': 'f5a13a', 'c': 'f29485', 'd': 'fad52f', 'e': 'd95572', 'f': 'af417d', 'g': '7d426e', 'h': 'a80d70', 'i': 'c9126e', 'j': 'f2186c', 'k': '4e4883', 'l': '6b6a9c', 'm': '455eb1', 'n': '4394d6', 'o': '08c3ee', 'p': '7491ae', 'q': '84bdc3', 'r': 'a8e3d1', 's': '007585', 't': 'faf1e3', 'u': '8a0c86', 'v': 'b13dff', 'w': '47255d', 'x': '4e1868', 'y': 'd92cbe', 'z': 'a9e030', 'A': '55dc34', 'B': '00ab56', 'C': 'fae1aa'}


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


COLOUR_TO_ROLE = {**{_rgb(h): c for c, h in LEGACY_HEX.items()}, **{_rgb(h): c for c, _, _, _, h in ROLES}}
"""colour (r, g, b) -> role letter, for reading a PNG made with the current palette or the legacy one"""

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

# Poses only some bases have (the humanoids built from the 3D model): taken from the folder when its PNGs
# are there, and listed with the others but marked optional, so a base without them is still complete.
OPTIONAL_POSES = [
    ('bow', 'NE', 4, 1),
    ('bow', 'SE', 4, 1),
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
                got = '.' if want[3] == 0 else by_colour.get(want[:3])
                if got != char:
                    sys.exit(f'{path}: round trip differs at ({ox + x}, {oy + y})')
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('bases', nargs='+', metavar='NAME=FOLDER', help='a base character and the folder of its pose PNGs, e.g. cleric=sprites/cleric')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'poses' / 'base.js')
    parser.add_argument('--merge', action='store_true', help='keep the bases already in the output and add or replace the ones named')
    args = parser.parse_args()

    by_colour = COLOUR_TO_ROLE
    to_colour = None

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
        for action, facing, cols, rows in OPTIONAL_POSES:
            matches = sorted(Path(folder).glob(f'*-{action}{facing}.png'))
            if matches:
                frames_by_pose[action + facing] = extract_frames(matches[0], cols, rows, by_colour, to_colour)
                frames_checked += len(frames_by_pose[action + facing])
        characters.append({'id': name.lower(), 'label': name.capitalize(), 'frames': frames_by_pose})

    kept = []
    if args.merge:
        if not args.out.exists():
            sys.exit(f'--merge needs an existing {args.out}')
        existing = json.loads(args.out.read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
        if existing.get('cell') != CELL or [p['id'] for p in existing.get('poses', [])] not in ([a + f for a, f, _, _ in POSES], [a + f for a, f, _, _ in POSES + OPTIONAL_POSES]):
            sys.exit(f'{args.out} was built from a different pose list; rebuild it from all the bases instead of merging')
        replaced = {c['id'] for c in characters}
        kept = [c for c in existing['characters'] if c['id'] not in replaced]

    def kind_of(base_id):
        import conventions            # imported here: conventions itself imports this module
        return conventions.kind_of(base_id)
    # Each base says whether it is a person or a creature, so a list of them can tell the two apart.
    for c in kept + characters:
        c['kind'] = kind_of(c['id'])

    data = {
        'cell': CELL,
        'ground': GROUND,
        'groups': [{'id': i, 'label': l, 'hue': i not in ('outline', 'neutral')} for i, l in GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ROLES],
        'poses': [
            {'id': a + f, 'label': f'{a.capitalize()} {f}', 'action': a, 'facing': f, 'cols': c, 'rows': r,
             **({'optional': True} if (a, f, c, r) in OPTIONAL_POSES else {})}
            for a, f, c, r in POSES + OPTIONAL_POSES
        ],
        'characters': kept + characters,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.BASE_POSES = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    total = len(kept) + len(characters)
    print(f'{frames_checked} frames across {len(characters)} bases ({total} in all), all re-rendered identical to the source -> {args.out}')


if __name__ == '__main__':
    main()
