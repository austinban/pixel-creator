#!/usr/bin/env python3
"""A fungal zombie: the Slim build (see make_slim.py and humanoid.py) rotted and overgrown, for the corrupted lands.

The same slim body as the slim human, the fey and the golden mushroom, so every pose, the lean, the walk and the weapon hand come with it. What changes is what it has become:
grey-green skin with plum patches of rot, ragged plum clothes, glowing teal eyes (spore light), and two fungal features that are part of it rather than stuck on: an orange-red
spotted cap that has grown over the skull in place of hair (cream gills under its rim, the face and eyes clear) and a shelf of bracket fungus at one shoulder. All palette roles.

    python3 tools/make_fungal_zombie.py --model previews/fungal-zombie-3d.png      look at the 3D model first
    python3 tools/make_fungal_zombie.py sprites/fungal-zombie [--preview sheet.png]
    python3 tools/extract_poses.py --merge fungal-zombie=sprites/fungal-zombie
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, run, rx, rz, deg  # noqa: E402
from humanoid import Humanoid, band  # noqa: E402

HEAD_Y = 18.6


CAP = {'centre': (0.2, HEAD_Y + 2.9, 0.5), 'radii': (5.3, 3.3, 5.5)}
# spots on the cap: a direction from its middle (x forward, y up, z right) and a size; few, so they read at 32 px
SPOTS = (((0.0, 1.0, 0.0), 1.2), ((0.6, 0.75, -0.55), 1.0), ((-0.6, 0.75, 0.5), 1.0), ((0.1, 0.3, 1.0), 0.95))
CAP_DROOP = 9                    # degrees the cap tips toward its right side, like a hat slipping


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def spot(j, droop, direction, size):
    """A flat round spot lying on the cap's surface where `direction` leaves its middle."""
    c, r = CAP['centre'], CAP['radii']
    d = unit(direction)
    at = tuple(c[i] + d[i] * r[i] * 1.005 for i in range(3))
    ey = unit(tuple(d[i] / r[i] for i in range(3)))
    ex = unit(cross((0.0, 1.0, 0.0) if abs(ey[1]) < 0.9 else (1.0, 0.0, 0.0), ey))
    ez = cross(ex, ey)
    R = [[ex[i], ey[i], ez[i]] for i in range(3)]
    return part(j['head'](*at), (size, 0.5, size * 0.9), 'spot', 'spot', mm(j['head_R'], R))


def fungus(j):
    """Two fungal features, both part of the body: the cap that has grown over the skull in place of hair, and a shelf of bracket fungus at one shoulder."""
    body = j['body']
    bR = j['body_R']
    R = j['head_R']
    c, r = CAP['centre'], CAP['radii']
    parts = [part(j['head'](*c), r, 'cap', 'cap', R),
             part(j['head'](c[0], c[1] - 1.1, c[2]), (r[0] - 0.4, 0.55, r[2] - 0.4), 'gill', 'gill', R)]      # gills under the rim
    parts += [spot(j, CAP_DROOP, d, s) for d, s in SPOTS]
    # the shoulder: two shelves, the lower smaller, growing out from the arm's top
    for y, w, d in ((13.4, 1.0, 0.0), (12.2, 0.75, 0.3)):
        parts.append(part(body(-0.2 - d, y, 4.6 + d), (1.7 * w + 0.4, 0.5, 2.3 * w + 0.4), 'bracket', 'bracket', mm(bR, rx(deg(-10)))))
    return parts


def rot(j, pose):
    """Plum patches of rot on the face and chest, thin flat discs."""
    return [part(j['head'](1.0, 21.2, 3.0), (1.3, 1.1, 0.7), 'rot', 'head', j['head_R']),
            part(j['body'](1.5, 11.0, 2.4), (1.4, 1.8, 0.8), 'rot', 'rot', j['body_R'])]


def eyes(j, pose):
    """Glowing teal spore-light eyes: real parts, a few pixels across (shut eyes keep the thin slit)."""
    if pose.get('eyes') != 'open':
        return []
    return [part(j['head'](4.2, HEAD_Y + 0.1, side * 1.95), (0.85, 1.6, 1.05), 'eye', 'eye', j['head_R']) for side in (-1, 1)]


def limbs(j):
    parts = []
    for side in ('L', 'R'):
        hip, knee, foot = j['leg_' + side]
        parts.append(band(knee, foot, 0.55, 0.85, 1.85, 'rags', 'rag' + side))               # torn trouser ends round the shin
    return parts


def gear(j, pose):
    return fungus(j) + rot(j, pose) + eyes(j, pose) + limbs(j)


CREATURE = Humanoid(
    'fungal-zombie',
    ramps={
        'skin': ('r', 'A', 'B', 's'),        # grey-green: mint, green, emerald, deep teal
        'rot': ('f', 'u', 'w', 'x'),         # plum patches of rot
        'rags': ('f', 'g', 'w', 'x'),
        'cap': ('b', 'a', 'e', 'h'),         # an orange-red cap: amber, orange, coral, dark magenta
        'gill': ('t', 'C', 'b', 'a'),        # cream gills
        'spot': ('t', 't', 'C', 'b'),        # cream spots
        'bracket': ('C', 'b', 'a', 'e'),     # the shoulder shelf: sand to coral
        'eye': ('r', 'o', 'o', 'o'),         # the teal glow
        'shirt': ('f', 'g', 'w', 'x'),       # a ragged plum shirt
        'pants': ('l', 'k', 'w', 'x'),
        'shoes': ('g', 'w', 'x', 'x'),
        'belt': ('g', 'w', 'x', 'x'),
    },
    hair='none',
    body={**make_slim.CREATURE.body, 'ears': False},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)
CREATURE.eye_colour = 'o'
CREATURE.eye_reach = 1.8

if __name__ == '__main__':
    run(CREATURE)
