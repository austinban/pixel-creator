#!/usr/bin/env python3
"""A blood cultist: the Slim build (see make_slim.py and humanoid.py) in a crimson robe and a deep hood, for the blood-themed enemies.

The same slim body as the slim human, the ranger and the golden mushroom, so every pose, the lean, the walk and the weapon hand come with it. What changes is what it wears:
a dark crimson robe that flares into a skirt above the boots, a hood pulled forward so the brow throws the upper face into shadow, a pale face with glowing red eyes, a black sash,
a ritual dagger hung at the hip and a small vial of blood on the belt. A few big features, all palette roles.

    python3 tools/make_blood_cultist.py --model previews/blood-cultist-3d.png      look at the 3D model first
    python3 tools/make_blood_cultist.py sprites/blood-cultist [--preview sheet.png]
    python3 tools/extract_poses.py --merge blood-cultist=sprites/blood-cultist
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, run, rx, rz, deg  # noqa: E402
from humanoid import Humanoid  # noqa: E402

HEAD_Y = 18.6
HOOD = (4.9, 5.1, 4.8)               # the hood's radii: a shell over the skull
HOOD_BACK = 1.2                      # how far back from the head's middle it sits
RIM_X = 3.2                          # the brim ring stands this far forward, so it overhangs the face
RIM_RADIUS = 3.9
RIM_PIECES = 22


def hood(j):
    R = j['head_R']
    parts = [
        part(j['head'](-HOOD_BACK, HEAD_Y + 1.0, 0), HOOD, 'hood', 'hood', R),
        part(j['head'](-HOOD_BACK - 4.4, HEAD_Y + 0.2, 0), (2.8, 2.6, 2.4), 'hood', 'hood', mm(R, rz(0.5))),           # the soft point behind
        part(j['head'](2.2, HEAD_Y + 3.3, 0), (2.8, 1.0, 3.8), 'hood', 'hood', R),                                       # the brow, jutting over the eyes
        part(j['head'](3.6, HEAD_Y + 1.7, 0), (1.6, 1.6, 3.2), 'shadow', 'shadow', R),                                   # the shadow it throws over the upper face
    ]
    for i in range(RIM_PIECES):
        angle = math.radians(-100 + 380 * i / (RIM_PIECES - 1))
        yc = HEAD_Y + 0.4 + RIM_RADIUS * math.cos(angle)
        zc = RIM_RADIUS * math.sin(angle)
        if yc < HEAD_Y - 2.4:
            continue
        parts.append(part(j['head'](RIM_X, yc, zc), (1.4, 2.0, 1.0), 'rim', 'rim', mm(R, rx(angle + math.pi / 2))))
    return parts


def eyes(j, pose):
    """Glowing red eyes, real parts, set under the brow (shut eyes keep the thin slit)."""
    if pose.get('eyes') != 'open':
        return []
    return [part(j['head'](4.3, HEAD_Y - 0.3, side * 1.95), (0.6, 1.2, 0.8), 'eye', 'eye', j['head_R']) for side in (-1, 1)]


def robe(j, pose):
    """A skirt that flares from the waist to just above the boots, and a sash with a vial and a dagger."""
    R = j['body_R']
    parts = []
    if pose['pitch'] < 80:                                    # lying on its back, the skirt is under it
        for i, (y, rx_, rz_) in enumerate(((8.4, 3.2, 4.0), (6.2, 3.5, 4.6))):
            parts.append(part(j['body'](-0.1, y, 0), (rx_, 2.6, rz_), 'robe', 'robe', R))
    parts.append(part(j['body'](0.3, 10.6, 0), (3.1, 0.8, 3.7), 'sash', 'sash', R))                      # the sash
    parts.append(part(j['body'](2.7, 10.0, 2.7), (0.8, 1.5, 0.8), 'vial', 'vial', R))                    # a vial of blood at the belt
    parts.append(part(j['body'](2.7, 11.5, 2.7), (0.45, 0.4, 0.45), 'cork', 'vial', R))
    parts.append(part(j['body'](-0.4, 9.2, -3.9), (0.55, 2.7, 0.55), 'blade', 'dagger', mm(R, rz(deg(-14)))))   # the dagger: a blade hung point down
    parts.append(part(j['body'](-0.4, 11.8, -3.9), (0.9, 0.5, 0.9), 'hilt', 'dagger', R))
    return parts


def gear(j, pose):
    return hood(j) + eyes(j, pose) + robe(j, pose)


CREATURE = Humanoid(
    'blood-cultist',
    ramps={
        'skin': ('t', 'C', 'c', 'e'),        # pale, a little salmon in the shade
        'hood': ('e', 'h', 'w', 'x'),        # deep crimson
        'rim': ('h', 'w', 'x', 'x'),         # the brim, darker still
        'robe': ('j', 'i', 'h', 'w'),        # bright crimson
        'shadow': ('w', 'x', 'x', 'x'),
        'sash': ('l', 'k', 'x', 'x'),        # black-violet
        'vial': ('j', 'i', 'h', 'w'),        # blood in glass
        'blade': ('t', 'p', 'l', 'k'),       # steel
        'hilt': ('c', 'e', 'h', 'x'),
        'cork': ('C', 'b', 'a', 'e'),
        'eye': ('j', 'i', 'h', 'w'),         # the red glow
        'shirt': ('j', 'i', 'h', 'w'),       # the robe's body and sleeves
        'pants': ('h', 'w', 'x', 'x'),
        'shoes': ('w', 'x', 'x', 'x'),
        'belt': ('l', 'k', 'x', 'x'),
    },
    hair='none',
    body={**make_slim.CREATURE.body, 'ears': False},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)
CREATURE.eye_colour = 'j'
CREATURE.eye_reach = 2.2             # the brow hangs over the face, so the eyes are painted on from further in

if __name__ == '__main__':
    run(CREATURE)
