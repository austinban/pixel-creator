#!/usr/bin/env python3
"""A blighted fey: the Slim build restyled (see make_slim.py and humanoid.py), with four veined wings and twig antlers.

The same slim body as the slim human, the ranger and the verdant, so every pose, the lean, the walk and the weapon hand come with it.
What changes is what it wears and grows, from a front and back drawing: messy magenta hair with two twig antlers and long pointed ears; glowing teal eyes;
bare arms with dark wristbands; a dark ruff, a dark teal tunic and a ragged skirt of long purple tatters with teal leaf tabs; blue trousers and dark boots
with teal cuffs; and four wings (two large upper, two smaller lower) in violet and magenta with teal veins, folded out from the upper back.
Everything is palette roles, so it recolours like the rest.

    python3 tools/make_fey.py --model previews/fey-3d.png      look at the 3D model first
    python3 tools/make_fey.py sprites/fey [--preview sheet.png]
    python3 tools/extract_poses.py --merge fey=sprites/fey
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, rx, rz  # noqa: E402
from humanoid import Humanoid, band, bone3, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
HALF_PI = math.pi / 2


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def facing(direction, face=(-1.0, 0.0, 0.0)):
    """An orientation whose x axis runs along `direction` and whose thin y axis points toward `face` as far as it can: a flat blade lying that way."""
    ex = norm(direction)
    d = sum(a * b for a, b in zip(face, ex))
    ey = norm(tuple(f - d * e for f, e in zip(face, ex)))
    ez = cross(ex, ey)
    return [[ex[i], ey[i], ez[i]] for i in range(3)]


def blade(j, base, direction, length, width, mat, name, thick=0.5, face=(-1.0, 0.0, 0.0)):
    """A flat leaf-shaped piece from `base` along `direction`, in the body's own space."""
    ex = norm(direction)
    centre = tuple(base[i] + ex[i] * length / 2 for i in range(3))
    R = mm(j['body_R'], facing(direction, face))
    return part(j['body'](*centre), (length / 2, thick / 2, width / 2), mat, name, R), centre, ex, R


def wings(j, pose):
    parts = []
    if pose['pitch'] >= 80:
        return parts                                    # lying on its back, the wings are under it
    fold = max(0.6, 1 - 0.012 * abs(pose.get('twist', 0)) - 0.07 * abs(pose.get('sway', 0)))    # swung or thrown into a strike, the wings fold in so they stay inside the cell
    for side in (-1, 1):
        for base, direction, length, width in (((-3.0, 13.6, side * 1.2), (-0.35, 0.42, side * 0.85), 9.6, 5.0),
                                               ((-3.0, 11.6, side * 1.2), (-0.35, -0.28, side * 0.9), 7.6, 3.8)):
            length, width = length * fold, width * fold
            wing, centre, ex, R = blade(j, base, direction, length, width, 'wing', 'wing' + str(side), thick=0.7)
            parts.append(wing)
            # the teal vein down the middle of the wing, on both faces so it shows from either side
            for face in (-1, 1):
                at = tuple(centre[i] + (-0.45 * face if i == 0 else 0.0) for i in range(3))
                parts.append(part(j['body'](*at), (length * 0.42, 0.3, 0.45), 'vein', 'wing' + str(side), R))
    return parts


def head(j):
    R = j['head_R']
    parts = []
    # messy hair: tufts sticking up and out round the crown
    for dx, dy, dz, rr in ((-1.0, 3.2, 0.0, (1.6, 1.6, 1.4)), (0.2, 3.2, 1.8, (1.3, 1.5, 1.1)), (0.2, 3.2, -1.8, (1.3, 1.5, 1.1)),
                           (-2.5, 4.4, 3.0, (1.3, 1.6, 1.0)), (-2.5, 4.4, -3.0, (1.3, 1.6, 1.0)), (1.6, 3.4, 3.6, (1.4, 1.5, 0.9)), (1.6, 3.4, -3.6, (1.4, 1.5, 0.9))):
        parts.append(part(j['head'](dx, HEAD_Y + dy, dz), rr, 'hair', 'hair', R))
    # pointed ears, swept back and up
    for side in (-1, 1):
        parts.append(part(j['head'](-0.4, HEAD_Y + 0.8, side * 4.6), (1.0, 3.3, 0.7), 'skin', 'ear', mm(R, mm(rx(side * 0.45), rz(-0.5)))))
    # twig antlers: a stem rising from each side of the crown, forked
    for side in (-1, 1):
        stem = [(-0.6, HEAD_Y + 3.6, side * 2.4), (-1.0, HEAD_Y + 4.4, side * 3.2), (-1.4, HEAD_Y + 4.6, side * 3.8)]
        for a, b in zip(stem, stem[1:]):
            parts.append(bone3(j['head'](*a), j['head'](*b), 0.75, 'twig', 'antler' + str(side), grow=0.3))
        for tip in ((-0.4, HEAD_Y + 4.8, side * 5.4), (-2.4, HEAD_Y + 5.0, side * 3.0)):
            parts.append(bone3(j['head'](*stem[1]), j['head'](*tip), 0.65, 'twig', 'antler' + str(side), grow=0.2))
    return parts


def clothes(j, pose):
    R = j['body_R']
    parts = [part(j['body'](0.7, 14.4, 0), (2.9, 1.3, 3.6), 'rag', 'ruff', R)]                       # the dark ruff round the neck and shoulders
    # the skirt: long ragged strips hung round the hips, longer behind, purple with teal leaf tabs between
    hips = 8.6
    ring = [(3.6, 0.0, 4.2, 'rag'), (2.9, 2.2, 3.6, 'tab'), (2.9, -2.2, 3.6, 'tab'), (0.0, 3.5, 4.6, 'rag'), (0.0, -3.5, 4.6, 'rag'),
            (-2.8, 2.6, 4.8, 'rag'), (-2.8, -2.6, 4.8, 'rag'), (-3.7, 0.0, 5.0, 'rag'), (-3.3, 1.3, 4.2, 'tab'), (-3.3, -1.3, 4.2, 'tab')]
    if pose['pitch'] >= 80:
        ring = ring[:5]
    for x, z, length, mat in ring:
        length = max(2.0, min(length, hips + 0.4 + pose['lift'] - 1.2))      # crouching or leaping, the tatters stop above the ground
        parts.append(part(j['body'](x, hips - length / 2 + 0.4, z), (0.95, length / 2, 1.25), mat, 'skirt', R))
    return parts


def limbs(j):
    parts = []
    for side in ('L', 'R'):
        hip, knee, foot = j['leg_' + side]
        parts.append(band(knee, foot, 0.55, 0.85, 1.9, 'tab', 'cuff' + side))                  # a teal cuff round the boot
        arm = j.get('arm_' + side)
        if arm:
            parts.append(band(arm[1], arm[2], 0.45, 0.85, 1.6, 'wrist', 'wristband' + side))   # a dark wristband
    return parts


def gear(j, pose):
    return wings(j, pose) + head(j) + clothes(j, pose) + limbs(j)


CREATURE = Humanoid(
    'fey',
    ramps={
        'skin': ('c', 'e', 'f', 'g'),        # a muted mauve
        'hair': ('y', 'i', 'h', 'u'),        # magenta
        'twig': ('f', 'g', 'w', 'x'),
        'wing': ('v', 'y', 'i', 'h'),        # violet, fuchsia, magenta, dark magenta
        'vein': ('r', 'o', 'q', 's'),        # the teal glow in the veins
        'shirt': ('s', 'k', 'w', 'x'),       # a dark teal tunic
        'rag': ('l', 'k', 'w', 'x'),         # the ruff and the skirt's tatters
        'tab': ('q', 's', 'k', 'w'),         # teal leaf tabs and cuffs
        'wrist': ('s', 'k', 'w', 'x'),
        'pants': ('p', 'l', 'k', 'w'),       # blue trousers
        'shoes': ('l', 'k', 'w', 'x'),
        'belt': ('f', 'g', 'w', 'x'),
    },
    hair='short',
    body={**make_slim.CREATURE.body, 'ears': False, 'sleeve_mat': 'skin'},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)
CREATURE.poses['attackSE'][0]['lift'] -= 1.0      # the SE wind-up crouches a little more: with the antlers and wings the figure is a row taller than the cell otherwise
CREATURE.eye_colour = 'o'                      # glowing teal eyes
CREATURE.eye_reach = 1.4

if __name__ == '__main__':
    run(CREATURE)
