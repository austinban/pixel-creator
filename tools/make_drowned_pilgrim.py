#!/usr/bin/env python3
"""A Drowned Pilgrim: a drowned fisherman, a mid-level water enemy.

Someone who worked these waters, then was sacrificed at a rune altar and sunk in the marsh, risen with the spirit lantern they were given. The same slim body as the ranger (make_slim.py, humanoid.py),
so every pose, the lean, the walk and the weapon hand come with it, but nothing like the ranger: a bare head with lank wet hair and pale mint skin, a faded oilskin slicker that hangs to the knee,
a rope at the waist, a fishing net slung over one shoulder, waders and boots, pond weed in the hair and on one shoulder, and a spirit lantern hung from the off hand, glowing cyan: the one bright thing on it.
Everything is palette roles, so it recolours like the rest.

    python3 tools/make_drowned_pilgrim.py --model previews/pilgrim-3d.png      look at the 3D model first
    python3 tools/make_drowned_pilgrim.py sprites/drowned-pilgrim [--preview previews/drowned-pilgrim.png]
    python3 tools/extract_poses.py --merge drowned-pilgrim=sprites/drowned-pilgrim

The weak pose is a kneel, so 'drowned-pilgrim' belongs in KNEELERS in tools/conventions.py.
"""
import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_ranger as mr  # noqa: E402
import make_slim  # noqa: E402

from creature import mm, part, rx, rz  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = mr.HEAD_Y
HEM_Y = 3.4                           # where the robe ends, above the ground


def collar(j):
    R = j['body_R']
    return [part(j['body'](-0.4, 13.5, 0), (2.8, 1.6, 5.1), 'coat', 'coat', R)]                    # the slicker's collar, turned up


def coat(j, pose):
    """A slicker that hangs to the knee and flares a little, with a rope round the waist: a few long overlapping pieces, so it falls in one sheet."""
    R = j['body_R']
    parts = []
    if pose['pitch'] > 80:
        return parts                                           # lying on its back, the coat is under it
    for i, (y, h, rx_, rz_) in enumerate(((9.8, 3.2, 3.2, 4.7), (7.9, 2.7, 3.5, 5.0), (6.4, 2.0, 3.6, 5.2))):
        parts.append(part(j['body'](-0.2, y, 0), (rx_, h, rz_), 'coat', 'coat', R))
    parts.append(part(j['body'](0.2, 10.6, 0), (2.5, 0.55, 4.2), 'rope', 'rope', R))                # the rope at the waist
    return parts


def cap(j):
    """A knit fisherman's cap pulled down over the hair, with a rolled brim."""
    R = j['head_R']
    return [part(j['head'](-0.8, HEAD_Y + 3.4, 0), (4.6, 2.5, 4.9), 'cap', 'cap', R), part(j['head'](-0.6, HEAD_Y + 2.1, 0), (4.8, 0.8, 5.0), 'brim', 'brim', R)]


def net(j, pose):
    """A fishing net slung from one shoulder across the chest: pale cords, with a knot or two hanging."""
    R = j['body_R']
    if pose['pitch'] > 80:
        return []
    parts = []
    for n, (y, z) in enumerate(((12.4, 3.6), (11.2, 2.0), (10.0, 0.4), (8.8, -1.2))):
        parts.append(part(j['body'](2.7, y, z), (0.8, 0.8, 1.7), 'net', 'net' + str(n), mm(R, rx(0.7))))
    for n, (y, z) in enumerate(((8.4, 3.6), (7.6, 2.4))):
        parts.append(part(j['body'](1.9, y, z), (0.8, 1.2, 0.8), 'net', 'netk' + str(n), R))
    return parts


def weed(j, pose):
    """Pond weed: a strand in the hair, a hank over one shoulder."""
    R = j['head_R']
    parts = [part(j['head'](-2.6, HEAD_Y + 4.6, -2.2), (1.3, 0.6, 0.8), 'weed', 'weedH0', R), part(j['head'](-4.2, HEAD_Y + 1.4, 1.8), (0.7, 2.0, 0.7), 'weed', 'weedH1', R)]
    B = j['body_R']
    parts.append(part(j['body'](-0.6, 12.0, -4.6), (0.9, 1.8, 0.8), 'weed', 'weedS', B))
    return parts


def lantern(j, pose):
    """A spirit lantern hung from the strike hand: a ring, a dark frame and a big glowing cyan flame, so it reads at 1x."""
    if pose['pitch'] > 80:
        return []                                              # fallen: the lantern has gone out
    x, y, z = j['hand_R']
    x += 0.6
    z += 1.0 if z >= 0 else -1.0                       # held out from the side, so it clears the robe
    return [
        part((x, y - 0.1, z), (0.5, 0.7, 0.5), 'frame', 'ring'),
        part((x, y - 0.9, z), (1.7, 0.45, 1.7), 'frame', 'cap'),
        part((x, y - 2.4, z), (1.8, 1.7, 1.8), 'glow', 'glow'),
        part((x, y - 3.4, z), (1.2, 0.4, 1.2), 'frame', 'base'),
    ]


def gear(j, pose):
    return cap(j) + collar(j) + coat(j, pose) + net(j, pose) + weed(j, pose) + lantern(j, pose)


CREATURE = Humanoid(
    'drowned-pilgrim',
    ramps={
        'coat': ('C', 'b', 'a', 'e'),         # a faded oilskin slicker: sand, amber, orange, coral, gone grey-yellow with the water
        'cap': ('l', 'k', 'w', 'x'),          # a knit cap, navy gone grey
        'brim': ('p', 'l', 'k', 'w'),
        'rope': ('t', 'C', 'b', 'a'),         # a pale rope at the waist
        'net': ('t', 'C', 'p', 'l'),          # the fishing net, bleached
        'hair': ('p', 'l', 'k', 'w'),         # lank, wet, grey-lavender hair
        'shirt': ('b', 'a', 'e', 'g'),        # the sleeves, the same slicker
        'pants': ('s', 'D', 'x', 'x'),        # waders, dark deep teal
        'shoes': ('k', 'w', 'x', 'x'),
        'skin': ('r', 'q', 'p', 'l'),         # mint, teal, steel, lavender: drowned grey-teal
        'weed': ('A', 'B', 's', 'D'),
        'frame': ('p', 'l', 'k', 'w'),
        'glow': ('o', 'o', 'q', 's'),         # the one bright accent
    },
    hair='long',
    body=make_slim.CREATURE.body,
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
    tuning='ranger',
)
CREATURE.eye_colour = None
# the robe and lantern put its head a little too far forward on two frames of the SE walk, so hold those two back
_walk = copy.deepcopy(CREATURE.poses.get('walkingSE', CREATURE.poses['walking']))
for _i, _back in ((2, 1.1), (6, 0.8)):
    _walk[_i]['sway'] = _walk[_i].get('sway', 0) - _back
CREATURE.poses['walkingSE'] = _walk
_walkne = copy.deepcopy(CREATURE.poses.get('walkingNE', CREATURE.poses['walking']))
_walkne[6]['sway'] = _walkne[6].get('sway', 0) + 0.7
CREATURE.poses['walkingNE'] = _walkne

if __name__ == '__main__':
    run(CREATURE)
