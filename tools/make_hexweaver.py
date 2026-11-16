#!/usr/bin/env python3
"""A hexweaver: the Slim build restyled (see make_slim.py and humanoid.py), a witch whose craft is paid in blood.

The same slim body as the slim human, the ranger and the fey, so every pose, the lean, the walk and the weapon hand come with it. What changes is what she
wears: a tall pointed hat, black, its crown bent back at a crooked tip, with a wide brim and a crimson band with a drop of blood at the front; long dark red
hair falling from under the back of the brim to below the shoulders; a pale face with red eyes; a black dress that flares into a skirt above the boots, with
a crimson sash, a vial of blood at the hip, and a red thread wound round one forearm. No wings. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_hexweaver.py --model previews/hexweaver-3d.png      look at the 3D model first
    python3 tools/make_hexweaver.py sprites/hexweaver [--preview sheet.png]
    python3 tools/extract_poses.py --merge hexweaver=sprites/hexweaver
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, rz  # noqa: E402
from humanoid import Humanoid, band, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
BRIM_Y = HEAD_Y + 3.0            # the brim sits on the brow
BRIM = (6.4, 0.5, 6.4)           # a wide brim
# The crown: overlapping rings that rise, then fold over and droop down behind the head, the tip hanging at the back of the brim. It reads big
# without standing above the cell. The lowest ring is as wide as the skull, so the head never shows above the brim.
CROWN = [  # (back, up from the brim, radius)
    (-0.9, 0.5, 4.7),
    (-1.1, 1.2, 3.9),
    (-1.5, 1.9, 3.2),
    (-2.2, 2.4, 2.6),
    (-3.1, 2.8, 2.1),
    (-4.2, 2.9, 1.7),
    (-5.3, 2.7, 1.4),
    (-6.2, 2.1, 1.15),
    (-6.9, 1.4, 0.95),
    (-7.3, 0.7, 0.75),          # the tip, hanging down behind
]


def hat(j):
    R = j['head_R']
    parts = [part(j['head'](0.2, BRIM_Y, 0), BRIM, 'hat', 'brim', R)]
    for back, up, r in CROWN:
        parts.append(part(j['head'](back, BRIM_Y + up, 0), (r, 1.1, r), 'hat', 'crown', R))
    parts.append(part(j['head'](-0.9, BRIM_Y + 0.75, 0), (4.6, 0.4, 4.6), 'band', 'band', R))          # the crimson band round the crown
    parts.append(part(j['head'](3.7, BRIM_Y + 0.8, 0), (0.5, 0.65, 0.55), 'drop', 'band', R))              # a drop of blood at its front
    return parts


def hair(j, pose):
    """Long hair out from under the back of the brim, down past the shoulders; lying down, it fans out under the head."""
    R = j['head_R']
    parts = [part(j['head'](-1.6, HEAD_Y + 0.8, 0), (4.0, 3.9, 4.75), 'hair', 'hair', R),                  # under the hat, round the back and sides
             part(j['head'](-3.6, HEAD_Y - 1.4, 0), (1.8, 3.4, 4.1), 'hair', 'hair', R)]                   # the fall at the back of the head                  # the fall at the back of the head
    if pose['pitch'] < 80:
        # below the head it hangs from the shoulders, not the skull, so a bowed head does not throw it up into the air
        B = j['body_R']
        parts.append(part(j['body'](-3.4, 12.6, 0), (1.5, 2.4, 3.5), 'hair', 'hair', B))                    # on down the back
        parts.append(part(j['body'](-3.6, 10.2, 0), (1.2, 1.6, 2.8), 'hair', 'hair', B))                    # the ends
    for side in (-1, 1):
        parts.append(part(j['head'](-0.4, HEAD_Y - 1.6, side * 4.0), (1.3, 2.9, 0.9), 'hair', 'hair', R))   # a lock down each side of the face
    return parts


def eyes(j, pose):
    if pose.get('eyes') != 'open':
        return []
    return [part(j['head'](4.2, HEAD_Y + 0.0, side * 1.9), (0.55, 1.0, 0.7), 'eye', 'eye', j['head_R']) for side in (-1, 1)]


def dress(j, pose):
    R = j['body_R']
    parts = []
    if pose['pitch'] < 80:                                    # lying on her back, the skirt is under her
        for y, rx_, rz_ in ((8.4, 3.1, 3.9), (6.0, 3.5, 4.5)):
            parts.append(part(j['body'](-0.1, y, 0), (rx_, 2.6, rz_), 'dress', 'skirt', R))
        parts.append(part(j['body'](-0.1, 3.7, 0), (3.6, 0.45, 4.6), 'trim', 'skirt', R))                # a crimson hem
    parts.append(part(j['body'](0.3, 10.6, 0), (3.0, 0.75, 3.6), 'sash', 'sash', R))                     # the sash
    parts.append(part(j['body'](2.5, 9.7, 2.8), (0.75, 1.3, 0.75), 'vial', 'vial', R))                   # a vial of blood at the hip
    parts.append(part(j['body'](2.5, 11.1, 2.8), (0.4, 0.35, 0.4), 'cork', 'vial', R))
    parts.append(part(j['body'](0.6, 14.3, 0), (2.6, 0.9, 3.4), 'trim', 'collar', R))                    # a red collar
    return parts


def thread(j):
    """A red thread wound round the right forearm: three turns."""
    arm = j.get('arm_R')
    if not arm:
        return []
    return [band(arm[1], arm[2], t, t + 0.12, 1.45, 'thread', 'thread') for t in (0.3, 0.5, 0.7)]


def gear(j, pose):
    return hat(j) + hair(j, pose) + eyes(j, pose) + dress(j, pose) + thread(j)


CREATURE = Humanoid(
    'hexweaver',
    ramps={
        'skin': ('C', 'b', 'a', 'e'),        # a warm brown
        'hair': ('E', 'F', 'G', 'w'),        # blood red
        'hat': ('l', 'k', 'w', 'x'),         # black-violet, light enough to show its shape
        'band': ('E', 'F', 'G', 'w'),        # crimson
        'drop': ('E', 'F', 'G', 'G'),
        'eye': ('E', 'F', 'G', 'w'),
        'dress': ('g', 'w', 'x', 'x'),       # a plum-black dress, warmer than the hat so the two do not run together
        'shirt': ('g', 'w', 'x', 'x'),       # its bodice and sleeves
        'trim': ('E', 'F', 'G', 'w'),
        'sash': ('F', 'G', 'w', 'x'),
        'vial': ('E', 'F', 'G', 'w'),
        'cork': ('C', 'b', 'a', 'e'),
        'thread': ('E', 'F', 'G', 'G'),
        'pants': ('k', 'w', 'x', 'x'),
        'shoes': ('w', 'x', 'x', 'x'),
        'belt': ('F', 'G', 'w', 'x'),
    },
    hair='none',
    body={**make_slim.CREATURE.body, 'ears': False},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
    tuning='slim',                               # the slim build's lean and hand numbers
)
# With the hat, the SE wind-up crouches a row lower to stay in the cell,
CREATURE.poses['attackSE'][0]['lift'] -= 1.0
for i in range(8):                               # and the brim's front tips the SE walk forward of the slim's lean, so it sways a little less
    CREATURE.poses['walkingSE'][i]['sway'] = 0.6
CREATURE.poses['walkingSE'][2]['sway'] = 0.0       # the stride where the crown swings forward most
CREATURE.eye_colour = 'E'
CREATURE.eye_reach = 1.4

if __name__ == '__main__':
    run(CREATURE)
