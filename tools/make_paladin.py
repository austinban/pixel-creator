#!/usr/bin/env python3
"""A paladin: a knight in full armour, on the standard heavy build (see humanoid.py).

Modelled on the look of the original knight (steel-blue plate, gold trim, a red plume, a dark slit to see
through) but built like the other people, so it uses their poses, the lean, the walk and the weapon hand.
Armour all over: a closed helmet with a dark visor slit, a gold brow band and a red plume, a gorget, a
breastplate and broad pauldrons, steel gauntlets and greaves, and a gold belt. Everything is palette
roles, so it recolours like the rest.

    python3 tools/make_paladin.py --model previews/paladin-3d.png    look at the 3D model first
    python3 tools/make_paladin.py sprites/paladin [--preview sheet.png]
    python3 tools/extract_poses.py --merge paladin=sprites/paladin
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from creature import deg, mm, part, ry, rz  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
HELMET = (5.35, 5.6, 5.3)        # the helmet's radii: a shell over the whole head
BAND_Y = 1.6                     # how far above the middle of the head the gold band sits
BAND_PIECES = 30
PLUME = [(1.2, 4.4), (-0.8, 4.9), (-3.0, 4.7), (-5.0, 4.0), (-6.3, 2.8)]      # the plume's spine over the helmet: (forward, height above the head's middle)


def band_ring(j, R):
    """A ring of small overlapping pieces lying on the helmet's surface (as the ninja's headband is)."""
    hx, hy, hz = HELMET
    dy = BAND_Y
    shrink = math.sqrt(1 - ((dy + 0.35) / hy) ** 2)
    a, b = hx * shrink + 0.05, hz * shrink + 0.05
    pieces = []
    for i in range(BAND_PIECES):
        t = 2 * math.pi * i / BAND_PIECES
        tangent = (-a * math.sin(t), b * math.cos(t))
        facing = math.atan2(-tangent[1], tangent[0])
        pieces.append(part(j['head'](a * math.cos(t), HEAD_Y + 0.35 + BAND_Y, b * math.sin(t)),
                           (1.25, 0.7, 0.55), 'gold', 'band', mm(R, ry(facing))))
    return pieces


def plume(j, R):
    """A red plume swept back from the crown of the helmet and drooping behind."""
    pieces = []
    for k, (x, y) in enumerate(PLUME):
        nxt = PLUME[min(k + 1, len(PLUME) - 1)]
        prev = PLUME[max(k - 1, 0)]
        dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
        slope = math.atan2(dy, dx)
        if slope > math.pi / 2:
            slope -= math.pi
        elif slope < -math.pi / 2:
            slope += math.pi
        size = 1.9 - 0.12 * k
        pieces.append(part(j['head'](x, HEAD_Y + y, 0.0), (size, 1.45, 1.05), 'plume', 'plume', mm(R, rz(slope))))
    return pieces


def gear(j, pose):
    """The helmet, its visor slit, band and plume; the gorget, pauldrons and trim. All follow the head or body."""
    HR, R = j['head_R'], j['body_R']
    parts = [
        part(j['head'](0.0, HEAD_Y + 0.35, 0), HELMET, 'steel', 'helmet', HR),                    # the helmet, over the whole head
        part(j['head'](4.95, HEAD_Y - 0.1, 0), (0.9, 0.62, 3.1), 'slit', 'helmet', HR),             # the dark visor slit to see through
        part(j['head'](4.9, HEAD_Y + 0.95, 0), (0.8, 0.38, 3.1), 'gold', 'helmet', HR),             # a gold bar right above the slit
        part(j['head'](4.95, HEAD_Y - 1.7, 0), (0.9, 1.5, 0.5), 'slit', 'helmet', HR),             # and a breathing slit down from the middle: a T
        part(j['body'](0.3, 15.1, 0.0), (2.4, 0.75, 2.4), 'gold', 'torso', R),                    # a gold gorget round the neck
        part(j['body'](0.0, 9.5, 0.0), (5.7, 0.8, 4.65), 'gold', 'torso', R),                    # the gold belt, wide and bold
    ]
    for side in (-1, 1):                                       # broad pauldrons, rimmed in gold
        at = j['body'](0.0, 14.0, side * 5.0)
        parts.append(part(at, (2.7, 1.7, 2.6), 'steel', 'pauldron', R))
        parts.append(part(j['body'](0.0, 12.9, side * 5.1), (2.5, 0.4, 2.45), 'gold', 'pauldron', R))
    parts += plume(j, HR)
    return parts


CREATURE = Humanoid(
    'paladin',
    ramps={
        'skin': ('q', 'p', 'l', 'k'),
        'steel': ('q', 'p', 'l', 'k'),           # polished steel, blue-grey like the original knight's
        'shirt': ('q', 'p', 'l', 'k'),           # the breastplate and sleeves
        'pants': ('p', 'l', 'k', 'w'),           # greaves, a shade darker
        'shoes': ('l', 'k', 'w', 'x'),
        'belt': ('d', 'b', 'a', 'e'),
        'gold': ('d', 'b', 'a', 'e'),            # the trim
        'plume': ('j', 'i', 'h', 'w'),           # the red plume
        'slit': ('w', 'x', 'x', 'x'),            # the visor slit
    },
    body=dict(hand_mat='steel', neck_mat='steel', ears=False),
    hair='none',                                 # a closed helmet
    accessories=gear,
)
CREATURE.eye_reach = 2.5

if __name__ == '__main__':
    run(CREATURE)
