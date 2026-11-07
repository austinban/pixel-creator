#!/usr/bin/env python3
"""A verdant knight: the Slim build restyled (see make_slim.py and humanoid.py), in bark-gold plate and leaves.

The same slim body as the slim human and the ranger, so every pose, the lean, the walk and the weapon hand come with it.
What changes is what it wears, from a front and back drawing: a round bark-brown helm with a dark T visor, a green brow band and a crest of three leaves;
leaf pauldrons over indigo sleeves; a bark-plate chest with moss on it and a gold ridge; a leather belt with leaf tassets and a leather flap;
bark vambraces wrapped in vine; gold knee cops; green leaf boots with gold bands; and a long tattered green cape with a mantle of leaves across the back.
Everything is palette roles, so it recolours like the rest.

    python3 tools/make_verdant.py --model previews/verdant-3d.png      look at the 3D model first
    python3 tools/make_verdant.py sprites/verdant [--preview sheet.png]
    python3 tools/extract_poses.py --merge verdant=sprites/verdant
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import mm, part, rx, ry, rz  # noqa: E402
from humanoid import Humanoid, band, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
HELMET = (5.3, 5.5, 5.2)         # a round shell over the whole head
BAND_Y = 1.7                     # the green band's height above the head's middle
BAND_PIECES = 30
HALF_PI = math.pi / 2


def leaf(at, length, width, mat, name, R, thick=0.55):
    """A leaf: a flat ellipsoid long along its own x axis. `R` points it."""
    return part(at, (length / 2, thick / 2, width / 2), mat, name, R)


def band_ring(j, R, mat='leaf'):
    """A ring of small overlapping pieces lying on the helmet's surface: the green brow band."""
    hx, hy, hz = HELMET
    shrink = math.sqrt(1 - ((BAND_Y + 0.35) / hy) ** 2)
    a, b = hx * shrink + 0.05, hz * shrink + 0.05
    pieces = []
    for i in range(BAND_PIECES):
        t = 2 * math.pi * i / BAND_PIECES
        tangent = (-a * math.sin(t), b * math.cos(t))
        pieces.append(part(j['head'](a * math.cos(t), HEAD_Y + 0.35 + BAND_Y, b * math.sin(t)),
                           (1.3, 0.55, 0.6), mat, 'band', mm(R, ry(math.atan2(-tangent[1], tangent[0])))))
    return pieces


def helm(j):
    R = j['head_R']
    parts = [
        part(j['head'](0.0, HEAD_Y + 0.35, 0), HELMET, 'bark', 'helmet', R),
        part(j['head'](4.9, HEAD_Y - 0.15, 0), (0.9, 0.55, 2.7), 'visor', 'helmet', R),               # the dark visor slit
        part(j['head'](4.85, HEAD_Y - 1.9, 0), (0.9, 1.7, 0.55), 'visor', 'helmet', R),               # and the breath slit down from it: a T
        part(j['head'](4.7, HEAD_Y + 0.75, 0), (0.8, 0.35, 2.9), 'trim', 'helmet', R),                 # a gold rim above the visor
        part(j['head'](4.6, HEAD_Y - 0.9, 2.9), (0.8, 1.3, 0.35), 'trim', 'helmet', R),                # and down both sides of it
        part(j['head'](4.6, HEAD_Y - 0.9, -2.9), (0.8, 1.3, 0.35), 'trim', 'helmet', R),
    ]
    parts += band_ring(j, R)
    # the crest: three leaves fanned from the crown, each swooping back: it rises, then its tip trails behind the head
    top = HEAD_Y + 3.4
    for tilt, length in ((0.0, 3.4), (0.75, 2.8), (-0.75, 2.8)):
        x, y, z = -0.3, top, tilt * 1.5
        for seg, (angle, share) in enumerate(((HALF_PI + 0.05, 0.5), (HALF_PI + 0.95, 0.6))):
            run_ = length * share
            cx, cy = x + math.cos(angle) * run_ / 2, y + math.sin(angle) * run_ / 2
            roll = 0.7 if tilt == 0 else 1.1 * (1 if tilt > 0 else -1)         # turned on its length, so its face shows from the side as well as the front
            parts.append(leaf(j['head'](cx, cy, z + tilt * 0.5 * seg), run_ + 0.6, 3.0 - 0.8 * seg, 'leaf', 'crest',
                              mm(R, mm(ry(-tilt * 0.5), mm(rz(angle), rx(roll)))), thick=0.7))
            x, y = x + math.cos(angle) * run_ * 0.9, y + math.sin(angle) * run_ * 0.9
    return parts


def pauldrons(j):
    R = j['body_R']
    parts = []
    for side in (-1, 1):
        # a gold-edged cap over each shoulder and two big leaves fanned up and out from it (one part, so they read as one shape)
        parts.append(part(j['body'](0.0, 13.6, side * 4.6), (2.3, 1.5, 2.0), 'shirt', 'pauldron', R))
        for up, out, length, back in ((0.6, 5.2, 5.4, 0.0), (1.0, 4.2, 4.4, 1.3)):
            parts.append(leaf(j['body'](back, 14.6, side * out), length, 3.0, 'leaf', 'pauldron',
                              mm(R, mm(ry(back * 0.3), mm(rx(side * -up), ry(HALF_PI)))), thick=0.8))
    return parts


def armour(j):
    R = j['body_R']
    parts = [
        part(j['body'](0.4, 11.9, 0), (3.95, 3.45, 3.2), 'bark', 'plate', R),                         # the breastplate, over the whole chest
        part(j['body'](0.3, 15.1, 0), (2.5, 0.9, 2.5), 'bark', 'plate', R),                           # a gorget round the neck
        part(j['body'](3.7, 12.6, 0), (0.7, 1.3, 1.9), 'moss', 'plate', R),                           # one patch of moss on the chest
        part(j['body'](0.0, 9.5, 0), (3.75, 0.85, 3.25), 'belt', 'torso', R),                         # the leather belt
        part(j['body'](3.2, 7.6, 0), (0.9, 2.5, 1.5), 'belt', 'torso', R),                            # and a leather flap hanging from it
    ]
    for side in (-1, 1):                                                                              # a leaf tasset over each hip
        parts.append(leaf(j['body'](2.5, 7.3, side * 2.7), 4.6, 2.4, 'leaf', 'tasset', mm(R, mm(rx(side * 0.25), rz(-HALF_PI + 0.15))), thick=0.9))
    return parts


def limbs(j):
    parts = []
    for side in ('L', 'R'):
        hip, knee, foot = j['leg_' + side]
        parts.append(part((knee[0] + 0.9, knee[1] + 0.7, knee[2]), (1.3, 1.25, 1.4), 'bark', 'knee' + side))          # a knee cop
        parts.append(band(knee, foot, 0.22, 0.42, 1.8, 'trim', 'boot' + side))                                         # a gold band round the boot
    return parts


def cape(j, pose):
    R = j['body_R']
    parts = [
        # a mantle of leaves across the shoulders and upper back
        part(j['body'](-1.0, 13.8, 0), (2.4, 1.5, 5.1), 'cape', 'cape', R),
    ]
    if pose['pitch'] >= 80:
        return parts                       # lying on its back, the cape is under it
    for k, (z, y, length, ang) in enumerate(((0.0, 12.6, 5.0, -0.05), (-2.0, 12.2, 4.4, 0.25), (2.0, 12.2, 4.4, -0.25),
                                              (-3.6, 12.7, 3.6, 0.5), (3.6, 12.7, 3.6, -0.5), (0.0, 14.2, 3.4, 0.0))):
        parts.append(leaf(j['body'](-3.6, y, z), length, 2.6, 'mantle', 'mantle', mm(R, mm(rx(ang), rz(-HALF_PI + 0.1))), thick=0.9))
    # the cape: long sheets hanging from the shoulders, wider as they fall, ending in a ragged hem
    crouched = pose['lift'] < -2                 # crouching or slumped, the cape bunches up instead of hanging
    pieces = 3 if crouched or pose['pitch'] <= -30 else 4
    for i in range(pieces):
        y = 11.4 - i * 1.0
        parts.append(part(j['body'](-3.9 - 0.14 * i, y, 0), (1.15, 2.6, 4.6 + 0.45 * i), 'cape', 'cape', R))
    if pose['pitch'] > -30 and not crouched:
        hem = [(-6.2, 6.6), (-4.4, 5.2), (-2.5, 7.0), (-0.8, 5.6), (0.9, 7.2), (2.5, 5.4), (4.3, 6.8), (6.1, 5.2)]
        for z, bottom in hem:
            top = 8.0
            parts.append(part(j['body'](-4.5 - 0.1 * abs(z), (top + bottom) / 2, z), (1.0, (top - bottom) / 2 + 0.5, 1.05), 'cape', 'cape', R))
    return parts


def gear(j, pose):
    return helm(j) + pauldrons(j) + armour(j) + limbs(j) + cape(j, pose)


CREATURE = Humanoid(
    'verdant',
    ramps={
        'bark': ('a', 'g', 'w', 'x'),        # bark-brown plate: rust, plum, grape, eggplant (the palette has no true brown)
        'trim': ('b', 'a', 'g', 'w'),        # the muted gold edges
        'visor': ('w', 'x', 'x', 'x'),       # the dark visor
        'leaf': ('A', 'B', 's', 'k'),        # green, emerald, deep teal, indigo: a quieter green
        'moss': ('A', 'B', 's', 'k'),
        'cape': ('A', 'B', 's', 'k'),
        'mantle': ('A', 'B', 's', 'k'),
        'shirt': ('l', 'k', 'w', 'x'),       # indigo sleeves
        'pants': ('l', 'k', 'w', 'x'),
        'boot': ('A', 'B', 's', 'k'),        # leaf-green boots
        'shoes': ('A', 'B', 's', 'k'),
        'belt': ('a', 'g', 'w', 'x'),        # leather
    },
    hair='none',                              # a closed helm
    body={**make_slim.CREATURE.body, 'hand_mat': 'bark', 'neck_mat': 'bark', 'ears': False, 'shin_mat': 'boot', 'bangles': 'leaf'},
    calibrate_like=make_slim.CREATURE,
    accessories=gear,
)
CREATURE.eye_reach = 2.5

if __name__ == '__main__':
    run(CREATURE)
