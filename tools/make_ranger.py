#!/usr/bin/env python3
"""A ranger: the Slim build restyled (see make_slim.py and humanoid.py), in a hood and a cloak.

The same slim body, so every pose, the lean, the walk and the weapon hand come with it. What changes is
what he wears: a forest-green hood pulled up over the head with the face left open, a cloak that hangs
from the shoulders down the back, a clasp at the throat, a burgundy tunic, dark trousers and
boots. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_ranger.py --model previews/ranger-3d.png      look at the 3D model first
    python3 tools/make_ranger.py sprites/ranger [--preview sheet.png]
    python3 tools/extract_poses.py --merge ranger=sprites/ranger
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, rx, ry, rz  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6                         # the middle of the head, from BODY in humanoid.py
HOOD = (5.5, 5.7, 5.5)                # the hood's radii: a shell set back over the skull, so the face is left bare
HOOD_BACK = 1.7                       # how far back from the head's middle the shell sits
RIM_X = 2.6                           # how far forward the ring sits
RIM_RADIUS = 4.1                      # and how wide it is there
RIM_PIECES = 26                       # the hood's edge round the face is a ring of small pieces
CAPE_PIECES = 5


def hood(j):
    R = j['head_R']
    parts = [
        part(j['head'](-HOOD_BACK, HEAD_Y + 0.9, 0), HOOD, 'hood', 'hood', R),
        # the peak: the hood bunches to a soft point at the back
        part(j['head'](-HOOD_BACK - 4.6, HEAD_Y + 0.4, 0), (2.6, 2.2, 2.2), 'hood', 'hood', mm(R, rz(0.5))),
    ]
    # the edge: a ring round the face opening, over the brow and down the sides, lying on the head's surface
    for i in range(RIM_PIECES):
        angle = math.radians(-100 + 380 * i / (RIM_PIECES - 1))        # from one jaw, over the brow, to the other
        yc = HEAD_Y + 0.2 + RIM_RADIUS * math.cos(angle)
        zc = RIM_RADIUS * math.sin(angle)
        if yc < HEAD_Y - 2.6:
            continue                                                   # open under the chin
        parts.append(part(j['head'](RIM_X, yc, zc), (1.5, 2.1, 1.0), 'rim', 'rim', mm(R, rx(angle + math.pi / 2))))   # long along the edge, so they run together
    return parts


def cloak(j, pose):
    R = j['body_R']
    parts = [
        # a collar round the neck and shoulders
        part(j['body'](-0.4, 13.5, 0), (2.4, 1.4, 4.9), 'cloak', 'cloak', R),
        # a clasp at the throat
        part(j['body'](3.0, 13.6, 0), (0.9, 0.9, 0.9), 'clasp', 'clasp', R),
    ]
    # the cloak itself: hangs down the back from the shoulders, a little wider as it falls. Long pieces that
    # overlap, so it drapes in one sheet instead of a stack of discs.
    if pose['pitch'] >= 80:
        return parts[:2]                  # lying on his back, the cloak is under him
    pieces = CAPE_PIECES if pose['pitch'] > -30 else 3        # slumped forward, it bunches up on the shoulders
    for i in range(pieces):
        y = 11.8 - i * 1.0
        spread = 4.0 + 0.3 * i
        parts.append(part(j['body'](-3.6 - 0.12 * i, y, 0), (1.15, 2.5, spread), 'cloak', 'cloak', R))
    return parts


def gear(j, pose):
    return hood(j) + cloak(j, pose)


CREATURE = Humanoid(
    'ranger',
    ramps={
        'hood': ('A', 'B', 's', 'k'),       # green, emerald, deep teal, indigo: a forest green
        'cloak': ('A', 'B', 's', 'k'),
        'rim': ('B', 's', 'k', 'w'),        # the hood's edge, a shade deeper
        'clasp': ('d', 'b', 'a', 'e'),      # gold
        'shirt': ('e', 'f', 'g', 'w'),      # a burgundy tunic: coral, orchid, plum, grape, to set off the green
        'pants': ('l', 'k', 'w', 'x'),
        'shoes': ('f', 'g', 'w', 'x'),
    },
    hair='none',
    body=make_slim.CREATURE.body,
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)

if __name__ == '__main__':
    run(CREATURE)
