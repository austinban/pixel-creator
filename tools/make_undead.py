#!/usr/bin/env python3
"""A zombie: the Slim build, rotted (see make_slim.py and humanoid.py).

The same style and palette as the original zombie (make_zombie.py): sickly green skin with an emerald shade,
a bald dome with a patch of skull showing through a bloody wound, hollow eyes, a chest torn open
to the ribs, plum and indigo rags, and the right arm gone, ending in a bleeding stump. Built like the other
people so it uses their poses, lean and walk. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_undead.py --model previews/undead-3d.png      look at the 3D model first
    python3 tools/make_undead.py sprites/undead [--preview sheet.png]
    python3 tools/extract_poses.py --merge undead=sprites/undead
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
HEAD_RADII = (4.8, 4.6, 4.5)     # the head, from BODY in humanoid.py
SKULL_AT = (-0.15, 0.40, 0.90)   # where the skull shows: low on the head, at the character's right side, a little back
RIBS = 2


def patch(j, direction, radius, thick, push, mat, name):
    """A flat disc lying on the head's surface in a direction, `push` out from it, carried with the head."""
    n = sum(v * v for v in direction) ** 0.5
    p = [HEAD_RADII[i] * direction[i] / n for i in range(3)]                    # the point on the head's surface
    p[1] += 0.0
    normal = [p[0] / HEAD_RADII[0] ** 2, p[1] / HEAD_RADII[1] ** 2, p[2] / HEAD_RADII[2] ** 2]
    length = sum(v * v for v in normal) ** 0.5
    normal = [v / length for v in normal]
    t1 = (normal[2], 0.0, -normal[0])                                           # across the surface, level
    t1 = [v / (sum(w * w for w in t1) ** 0.5) for v in t1]
    t2 = [normal[1] * t1[2] - normal[2] * t1[1], normal[2] * t1[0] - normal[0] * t1[2], normal[0] * t1[1] - normal[1] * t1[0]]
    R = [[normal[i], t1[i], t2[i]] for i in range(3)]
    at = tuple(p[i] + normal[i] * push for i in range(3))
    return part(j['head'](at[0], HEAD_Y + at[1], at[2]), (thick, radius, radius * 0.9), mat, name, mm(j['head_R'], R))


def gear(j, pose):
    """The skull patch, the torn chest with its ribs. All follow the head or the body."""
    HR, R = j['head_R'], j['body_R']
    parts = [
        # a ragged wound on the scalp, and the bone showing in it
        patch(j, SKULL_AT, 2.3, 0.6, -0.1, 'blood', 'wound'),
        patch(j, SKULL_AT, 1.5, 0.6, 0.18, 'bone', 'skull'),
        # the chest torn open: a dark red hollow on the front and the ribs across it
        part(j['body'](3.0, 11.0, -1.0), (1.2, 2.4, 1.7), 'blood', 'chest', R),
    ]
    for side in (-1, 1):                                  # sickly yellow round each eye
        parts.append(part(j['head'](3.95, HEAD_Y + 0.1, side * 1.95), (0.8, 1.9, 1.35), 'sickly', 'head', HR))
    for i in range(RIBS):
        parts.append(part(j['body'](3.7, 10.2 + 1.5 * i, -1.0), (0.5, 0.5, 1.9), 'bone', f'rib{i}', R))   # thicker and wider, but no further out
    return parts


CREATURE = Humanoid(
    'undead',
    ramps={
        'skin': ('z', 'A', 'B', 's'),            # sickly green, emerald in the shade (as the original zombie)
        'shirt': ('g', 'w', 'x', 'x'),           # plum rags
        'pants': ('l', 'k', 'w', 'x'),           # dull indigo
        'shoes': ('w', 'x', 'x', 'x'),
        'belt': ('f', 'g', 'w', 'x'),
        'blood': ('j', 'h', 'h', 'x'),           # the wound and the torn chest
        'stump': ('j', 'i', 'h', 'w'),           # the end of the missing arm, bleeding
        'bone': ('t', 'C', 'p', 'k'),            # exposed skull and ribs
        'sickly': ('d', 'b', 'a', 'e'),          # the yellowed skin round the eyes
    },
    body=dict(make_slim.CREATURE.body, armless=('R',), torn_leg='L'),     # the right arm gone, the left trouser ripped away below the knee
    scale=1.12,                                  # a little taller than the Slim: a bald dome has no hair to add height
    hair='none',                                 # a bald dome
    accessories=gear,
    calibrate_like=make_slim.CREATURE,           # drawn on the Slim's grid, so the walk samples identically
)

CREATURE.eye_reach = 1.4                          # the yellow stands a little out of the face, so the eyes are painted on it from further in

if __name__ == '__main__':
    run(CREATURE)
