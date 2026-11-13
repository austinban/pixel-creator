#!/usr/bin/env python3
"""A stone shaper: the Slim build (see make_slim.py and humanoid.py) in a deep teal robe and armour carved from square blocks of stone.

A person who works stone with their hands, so the gear is made of the box shape (`part(..., box=True)`, see creature.py) and not the usual rounded ellipsoids: an open stone cowl (a back, a top, two sides, a crest of stepped blocks, swept horns,
cheek guards, a nose bar and a split brow with a gold mark; the face left bare), stacked pauldrons, a chest slab with a gold rune inlaid, a stone belt, and brown leather gloves. The robe and the skin stay soft,
so the hard stone stands out. Palette roles only. It has the slim body's poses, lean, walk and weapon hand.

    python3 tools/make_stone_shaper.py --model previews/stoneshaper-3d.png      look at the 3D model first
    python3 tools/make_stone_shaper.py sprites/stone-shaper [--preview sheet.png]
    python3 tools/extract_poses.py --merge stone-shaper=sprites/stone-shaper
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

from creature import deg, mm, part, run, rx, ry, rz  # noqa: E402
from humanoid import Humanoid  # noqa: E402

HEAD_Y = 18.6


def block(c, r, mat, name, R=None):
    return part(c, r, mat, name, R, box=True)


def cowl(j):
    """A stone hood, open at the front: the back, the top, two sides and a brow that overhangs the eyes."""
    HR = j['head_R']
    head = lambda x, y, z: j['head'](x - 0.5, y, z)      # the whole helmet sits a little further back, which keeps the figure's lean right
    parts = [
        block(head(-3.4, HEAD_Y + 0.2, 0), (1.0, 4.0, 3.5), 'stone', 'cowl', HR),                            # the back
        block(head(-0.4, HEAD_Y + 3.6, 0), (3.8, 0.7, 3.8), 'stone', 'cowl', mm(HR, ry(deg(6)))),            # the top
        block(head(-0.8, HEAD_Y + 0.4, 3.9), (2.6, 3.6, 0.6), 'dark', 'cowl', HR),                          # the sides
        block(head(-0.8, HEAD_Y + 0.4, -3.9), (2.6, 3.6, 0.6), 'dark', 'cowl', HR),
        block(head(3.3, HEAD_Y + 2.2, 1.7), (0.9, 0.5, 1.4), 'dark', 'brow', HR),                           # a brow split over the nose, each half set a little differently
        block(head(3.4, HEAD_Y + 2.0, -1.7), (0.9, 0.5, 1.4), 'dark', 'brow', mm(HR, rx(deg(-6)))),
        block(head(3.6, HEAD_Y - 0.6, 0), (0.45, 1.7, 0.35), 'dark', 'guard', HR),                          # a bar down the nose
        block(head(4.0, HEAD_Y + 2.7, 0), (0.15, 0.4, 0.4), 'rune', 'mark', mm(HR, rx(deg(45)))),           # a gold mark over it
    ]
    # a crest of stepped blocks along the top, front to back, each a different height and turned a little
    for k, (x, h, turn) in enumerate(((1.4, 0.7, 5), (-0.4, 1.3, -4), (-2.2, 1.0, 7), (-3.6, 0.6, -3))):
        parts.append(block(head(x, HEAD_Y + 4.0 + h, 0), (0.85, h, 0.9), 'pale' if k % 2 else 'stone', 'crest', mm(HR, ry(deg(turn)))))
    for side in (-1, 1):
        # a slab swept out and up from each side like a horn, one longer than the other; and a cheek guard
        length = 1.4 if side == 1 else 1.9
        parts.append(block(head(-0.9, HEAD_Y + 3.4, side * 5.0), (0.7, length, 0.45), 'dark', 'horn' + str(side), mm(HR, rx(deg(-30 * side)))))
        parts.append(block(head(2.0, HEAD_Y - 2.3, side * 3.6), (1.5, 1.0, 0.45), 'stone', 'cheek' + str(side), HR))
    return parts


def armour(j):
    R = j['body_R']
    parts = []
    for side in (-1, 1):
        parts.append(block(j['body'](0.2, 14.6, side * 5.0), (2.3, 1.2, 2.0), 'stone', 'pauldron' + str(side), mm(R, ry(deg(8 * side)))))      # stacked, each turned a little
        parts.append(block(j['body'](0.1, 15.8, side * 4.9), (1.6, 0.55, 1.4), 'pale', 'pauldron' + str(side), mm(R, ry(deg(-12 * side)))))
    parts += [
        block(j['body'](3.5, 12.2, 0), (0.8, 2.3, 2.7), 'stone', 'chest', R),                          # a slab over the chest
        block(j['body'](4.35, 12.2, 0), (0.15, 0.95, 0.95), 'rune', 'rune', mm(R, rx(deg(45)))),         # a gold diamond rune inlaid in it
        block(j['body'](0.3, 9.6, 0), (3.3, 0.9, 3.9), 'dark', 'belt', R),
        block(j['body'](0.0, 7.4, 0), (3.6, 0.5, 4.2), 'stone', 'hem', R),                                 # a stone hem on the robe
        block(j['body'](3.2, 9.6, 0), (0.7, 1.0, 1.0), 'stone', 'belt', R),                              # the buckle: a block
    ]
    for side in ('L', 'R'):
        parts.append(block(j['hand_' + side], (1.3, 1.3, 1.3), 'glove', 'fist' + side, mm(R, ry(deg(20)))))      # chunky leather gloves
    return parts


def robe(j, pose):
    R = j['body_R']
    parts = []
    if pose['pitch'] < 80:                                       # lying on its back, the skirt is under it
        for y, rx_, rz_ in ((8.4, 3.3, 4.2), (6.2, 3.6, 4.8)):
            parts.append(part(j['body'](-0.1, y, 0), (rx_, 2.6, rz_), 'robe', 'robe', R))
    return parts


def gear(j, pose):
    return cowl(j) + armour(j) + robe(j, pose)


CREATURE = Humanoid(
    'stone-shaper',
    ramps={
        'skin': ('t', 'C', 'c', 'e'),
        'stone': ('q', 'p', 'l', 'k'),           # the stone tiles' colours
        'pale': ('r', 'q', 'p', 'l'),
        'dark': ('p', 'l', 'k', 'w'),
        'rune': ('t', 'd', 'b', 'a'),            # gold, glowing
        'robe': ('B', 's', 'D', 'w'),            # deep teal cloth
        'shirt': ('B', 's', 'D', 'w'),
        'pants': ('B', 'D', 'w', 'x'),
        'glove': ('a', 'g', 'w', 'x'),            # brown leather: rust, plum, grape, eggplant (the palette has no true brown)
        'shoes': ('p', 'l', 'k', 'w'),
        'belt': ('p', 'l', 'k', 'w'),
    },
    hair='none',
    body={**make_slim.CREATURE.body, 'ears': False, 'head_rx': 3.6, 'head_ry': 3.5, 'head_rz': 3.3, 'hand_mat': 'glove'},      # a smaller head, so it sits inside the cowl and does not poke through it
    calibrate_like=make_slim.CREATURE,
    tuning='slim',                               # the slim build's lean and hand numbers
    accessories=gear,
)
CREATURE.eye_colour = 't'                        # white eyes: a tall cream slit,
CREATURE.eye_white = 't'                         # with a pixel of white either side, so the whites are wider,
CREATURE.eye_pupil = 'x'                         # and a dot of black in the middle of each

if __name__ == '__main__':
    run(CREATURE)
