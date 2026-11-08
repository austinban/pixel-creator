#!/usr/bin/env python3
"""A golden mushroom person: the Slim build restyled (see make_slim.py and humanoid.py), wearing a big golden mushroom cap, with glowing teal eyes.

The same slim body as the slim human, the fey and the ranger, so every pose, the lean, the walk and the weapon hand come with it. What changes is what it wears:
a wide domed golden cap for a hat, pale cream spots on it and cream gills under its rim; a cream collar like a mushroom's ring; a rust-brown tunic, dark plum trousers and amber boots;
pale sandy skin; and glowing teal eyes. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_golden_mushroom.py --model previews/golden-mushroom-3d.png      look at the 3D model first
    python3 tools/make_golden_mushroom.py sprites/golden-mushroom [--preview sheet.png]
    python3 tools/extract_poses.py --merge golden-mushroom=sprites/golden-mushroom
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, run  # noqa: E402
from humanoid import Humanoid, band  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
CAP = {'centre': (-1.0, HEAD_Y + 2.5, 0.0), 'radii': (6.6, 3.1, 6.6)}
# where the cream spots sit on the cap: a direction from its middle (x forward, y up, z right) and a size
SPOTS = (((0.0, 1.0, 0.0), 1.15), ((0.55, 0.8, 0.5), 0.9), ((0.55, 0.8, -0.5), 0.9), ((-0.6, 0.78, 0.45), 0.95), ((-0.6, 0.78, -0.45), 0.95),
         ((0.1, 0.35, 1.0), 0.9), ((0.1, 0.35, -1.0), 0.9), ((-0.95, 0.35, 0.1), 0.85))


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def spot(j, direction, size):
    """A flat round spot lying on the cap's surface where `direction` leaves its middle, turned to lie flat and to move with the head."""
    c, r = CAP['centre'], CAP['radii']
    d = unit(direction)
    at = tuple(c[i] + d[i] * r[i] * 1.005 for i in range(3))
    ey = unit(tuple(d[i] / r[i] for i in range(3)))                  # the surface normal of an ellipsoid
    ex = unit(cross((0.0, 1.0, 0.0) if abs(ey[1]) < 0.9 else (1.0, 0.0, 0.0), ey))
    ez = cross(ex, ey)
    R = [[ex[i], ey[i], ez[i]] for i in range(3)]
    return part(j['head'](*at), (size, 0.5, size * 0.9), 'spot', 'spot', mm(j['head_R'], R))


def hat(j):
    R = j['head_R']
    c, r = CAP['centre'], CAP['radii']
    parts = [part(j['head'](*c), r, 'cap', 'cap', R)]
    # the gills: a thin pale disc just under the rim, so the underside shows at the edge
    parts.append(part(j['head'](c[0], c[1] - 1.15, c[2]), (r[0] - 0.4, 0.55, r[2] - 0.4), 'gill', 'gill', R))
    parts += [spot(j, d, s) for d, s in SPOTS]
    return parts


def eyes(j, pose):
    """Big glowing teal eyes: real parts, not the one-pixel decals, so they are a few pixels across (shut eyes keep the thin slit)."""
    if pose.get('eyes') != 'open':
        return []
    return [part(j['head'](4.2, HEAD_Y + 0.1, side * 1.95), (0.9, 1.7, 1.1), 'eye', 'eye', j['head_R']) for side in (-1, 1)]


def collar(j, pose):
    """The cream ring round the neck, like the ring on a mushroom's stem."""
    return [part(j['body'](0.7, 14.5, 0), (2.9, 1.0, 3.6), 'collar', 'collar', j['body_R'])]


def limbs(j):
    parts = []
    for side in ('L', 'R'):
        hip, knee, foot = j['leg_' + side]
        parts.append(band(knee, foot, 0.55, 0.85, 1.9, 'cuff', 'cuff' + side))                  # a cream cuff round the boot
    return parts


def gear(j, pose):
    return hat(j) + eyes(j, pose) + collar(j, pose) + limbs(j)


CREATURE = Humanoid(
    'golden-mushroom',
    ramps={
        'skin': ('t', 'C', 'b', 'a'),        # pale sand
        'cap': ('d', 'b', 'a', 'g'),         # gold: yellow, amber, orange, plum
        'spot': ('t', 't', 'C', 'd'),        # cream spots
        'gill': ('t', 'C', 'b', 'a'),        # cream gills under the rim
        'collar': ('t', 'C', 'b', 'a'),
        'cuff': ('t', 'C', 'b', 'a'),
        'eye': ('r', 'o', 'o', 'o'),         # the teal glow
        'shirt': ('a', 'g', 'w', 'x'),       # a rust-brown tunic, dark against the gold cap and the pale skin
        'pants': ('g', 'w', 'x', 'x'),       # dark plum trousers
        'shoes': ('b', 'a', 'g', 'w'),       # amber boots
        'belt': ('d', 'b', 'a', 'g'),
    },
    hair='none',
    body={**make_slim.CREATURE.body, 'ears': False},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)
CREATURE.eye_colour = 'o'                      # glowing teal eyes
CREATURE.eye_reach = 1.8                       # the cap's rim hangs over the face, so the eyes are painted on from further in

if __name__ == '__main__':
    run(CREATURE)
