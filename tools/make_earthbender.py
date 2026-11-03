#!/usr/bin/env python3
"""An earth bender: a bald man of living stone, on the standard heavy build (see humanoid.py).

His skin is stone, in the stone tiles' own colours (steel and teal, lavender in the shade, indigo in the cracks), with slabs of
rock on the shoulders and chest, a dark brow, cracks across the scalp, and white slit eyes. He wears bronze bangles on his upper arms,
wrists and ankles, and orange shorts, and nothing else. Built like the other people, so it uses their poses, the lean, the walk
and the bow. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_earthbender.py --model previews/earthbender-3d.png    look at the 3D model first
    python3 tools/make_earthbender.py sprites/earthbender [--preview sheet.png]
    python3 tools/extract_poses.py --merge earthbender=sprites/earthbender
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_undead  # noqa: E402

from creature import part  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6        # the middle of the head, from BODY in humanoid.py
STONE = ('q', 'p', 'l', 'k')          # the stone tiles' top, face, shade and crack
ROCK = ('r', 'q', 'p', 'l')           # slabs of paler rock set into him


def gear(j, pose):
    """Rock on the shoulders, chest and brow, cracks across the scalp, and stone knuckles. All follow the body, head or hands."""
    R, HR = j['body_R'], j['head_R']
    parts = []
    for side in (-1, 1):
        # a boulder of a shoulder, and a slab on the chest over each side
        parts.append(part(j['body'](0.2, 14.4, side * 5.5), (2.1, 1.7, 2.0), 'rock', 'shoulder' + str(side), R))
        parts.append(part(j['body'](5.1, 12.7, side * 1.9), (0.7, 1.7, 1.7), 'rock', 'chest' + str(side), R))
    # a heavy brow, and a few cracks lying flat across the bald head
    parts.append(part(j['head'](4.0, HEAD_Y + 2.0, 0.0), (1.0, 0.6, 3.3), 'brow', 'brow', HR))
    for k, (direction, size) in enumerate((((0.25, 0.9, 0.45), 1.5), ((-0.45, 0.8, -0.4), 1.2), ((0.55, 0.55, -0.62), 1.0))):
        parts.append(make_undead.patch(j, direction, size, 0.3, -0.05, 'crack', f'crack{k}'))
    # stone knuckles
    for side in ('L', 'R'):
        parts.append(part(j['hand_' + side], (1.9, 1.9, 1.9), 'rock', 'fist' + side, R))
    return parts


CREATURE = Humanoid(
    'earthbender',
    ramps={
        'skin': STONE,
        'shirt': STONE,                          # a bare stone chest
        'shoes': STONE,                          # bare stone feet
        'pants': ('b', 'a', 'e', 'f'),           # orange shorts: amber, orange, coral, orchid
        'belt': ('b', 'e', 'g', 'x'),            # a bronze waistband
        'bronze': ('b', 'e', 'g', 'x'),          # the bangles: an amber glint on a dark, reddish bronze
        'rock': ROCK,
        'brow': ('p', 'l', 'k', 'w'),            # a darker grey stone for the brow
        'crack': ('l', 'k', 'w', 'x'),
    },
    body=dict(bulk=1.6, hand_mat='skin', neck_mat='skin', sleeve_mat='skin', shin_mat='skin', bangles='bronze'),
    hair='none',                                 # bald
    # lying down, his bulk makes him a couple of rows too tall seen from the SE, so he is turned a little on the ground
    tweaks={'deadSE': {'twist': 15}},
    accessories=gear,
)
CREATURE.eye_colour = 't'                        # white slit eyes
CREATURE.eye_pupil = 'j'                         # with a red pupil in the middle of each (the palette's hot pink: there is no pure red)

if __name__ == '__main__':
    run(CREATURE)
