#!/usr/bin/env python3
"""A ninja: the Slim build restyled (see make_slim.py and humanoid.py).

The same slim body, so every pose, the lean, the walk and the weapon hand come with it (its tuned
numbers started as copies of the Slim's, then were tuned for its own head). What changes is the clothing: a dark gi, a red sash at the waist, a hood,
a mask over the lower face leaving an eye slit, a headband with two tails, and dark gloves and neck
wrap in place of bare skin. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_ninja.py sprites/ninja [--preview sheet.png]
    python3 tools/extract_poses.py --merge ninja=sprites/ninja
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402
import math  # noqa: E402

from creature import deg, mm, part, ry, rz  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6        # the middle of the head, from BODY in humanoid.py
HOOD = (5.25, 5.55, 5.3)      # the hood's radii: it wraps the whole head, and is a little tall like the other builds' hair
BAND_Y = 2.2                  # how far above the middle of the head the headband sits
BAND_PIECES = 30


def band_ring(j, R):
    """The headband: a ring of small overlapping pieces lying on the hood's surface.

    One flat ellipsoid will not do. Its rim is all that shows past a round hood, and when the head
    tilts even that sinks into the hood and the band vanishes. Pieces laid along the surface cannot.
    """
    hx, hy, hz = HOOD
    dy = BAND_Y - 0.1                                     # height above the hood's middle
    shrink = math.sqrt(1 - (dy / hy) ** 2)                # the hood is narrower up here
    a, b = hx * shrink + 0.05, hz * shrink + 0.05         # where its surface is
    pieces = []
    for i in range(BAND_PIECES):
        t = 2 * math.pi * i / BAND_PIECES
        tangent = (-a * math.sin(t), b * math.cos(t))
        facing = math.atan2(-tangent[1], tangent[0])
        pieces.append(part(j['head'](a * math.cos(t), HEAD_Y + BAND_Y, b * math.sin(t)),
                           (1.0, 0.8, 0.55), 'sash', 'band', mm(R, ry(facing))))
    return pieces


def hanging_tail(j, x, y, z, length):
    """A tail of the headband: tied at (x, y, z) on the head and hanging straight down from the knot."""
    knot = j['head'](x, y, z)
    down = (-0.3, -0.95, 0.0)                                   # down, and a little back
    centre = tuple(knot[i] + down[i] * length for i in range(3))
    return part(centre, (length, 0.5, 0.5), 'sash', 'band', rz(math.atan2(down[1], down[0])))


def gear(j, pose):
    """The hood, the eye slit, the headband and its tails. All follow the head, and turn with it."""
    R = j['head_R']
    return [
        # a hood that wraps the whole head, face included
        part(j['head'](0.0, HEAD_Y + 0.35, 0), HOOD, 'cloth', 'mask', R),
        # the only skin showing: a narrow strip across the eyes, pushed out through the hood
        part(j['head'](3.9, HEAD_Y + 0.1, 0), (1.5, 0.9, 3.0), 'skin', 'head', R),
        # two tails trailing behind the headband
        hanging_tail(j, -5.0, HEAD_Y + 1.7, 1.0, 1.9),
        hanging_tail(j, -5.0, HEAD_Y + 1.7, -1.0, 1.6),
    ] + band_ring(j, R)


CREATURE = Humanoid(
    'ninja',
    ramps={
        'shirt': ('k', 'w', 'x', 'x'),           # the gi: deep indigo down to near black
        'pants': ('k', 'w', 'x', 'x'),
        'shoes': ('w', 'x', 'x', 'x'),
        'hair': ('k', 'w', 'x', 'x'),            # the hood
        'cloth': ('k', 'w', 'x', 'x'),           # the mask, gloves and neck wrap
        'belt': ('j', 'i', 'h', 'w'),            # the sash
        'sash': ('j', 'i', 'h', 'w'),            # and the headband
    },
    body=dict(make_slim.CREATURE.body, hand_mat='cloth', neck_mat='cloth'),
    hair='none',                                 # the hood replaces the hair
    accessories=gear,
    tuning='ninja',                              # its own tuned numbers, started from the Slim's (tools/data/ninja_*.json)
    tweaks=make_slim.CREATURE.tweaks,
    calibrate_like=make_slim.CREATURE,           # drawn on the Slim's grid, so the walk samples identically
)

if __name__ == '__main__':
    run(CREATURE)
