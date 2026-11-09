#!/usr/bin/env python3
"""A crystal rock monster: the rock monster (see make_rockmonster.py) as a slate-blue boulder with four big rose crystals growing out of it as its shoulders and spine.

The same body, legs, poses and animations, so everything carries over. The rock monster's own spikes, plates and moss come off so the crystals are what you read:
one shard on each shoulder, a tall one up the spine and a low one on the rump, in rose and hot pink, and they squash and tilt with the boulder. The eyes glow cyan.

    python3 tools/make_rockmonster_crystal.py --model previews/rock-monster-crystal-3d.png      look at the 3D model first
    python3 tools/make_rockmonster_crystal.py sprites/rock-monster-crystal [--preview sheet.png]
    python3 tools/extract_poses.py --merge rock-monster-crystal=sprites/rock-monster-crystal
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_rockmonster as rm  # noqa: E402
from creature import add, deg, mm, mv, run, rx, rz, sub  # noqa: E402

ROCK_ANATOMY = rm.anatomy
MAIN = ((0.0, 7.6, 0.0), (5.4, 4.6, 5.0))
# (direction out of the boulder, length, thickness, material): four big shards that grow out of it as its shoulders and spine
CRYSTALS = [
    ((-0.15, 0.85, -0.85), 7.4, 1.9, 'crystal'),       # a shoulder on each side, leaning outward
    ((-0.15, 0.85, 0.85), 7.0, 1.8, 'crystalB'),
    ((-0.6, 1.0, 0.05), 8.6, 2.1, 'crystalB'),          # the tall one up its spine
    ((-1.0, 0.45, -0.3), 6.4, 1.5, 'crystal'),          # a low one out of its rump
]
GROWTHS = ('spike', 'plate', 'moss')                    # the rock monster's own spikes, plates and moss come off, so the shards are what you see


def anatomy(p):
    body, decals = ROCK_ANATOMY(p)
    body = [q for q in body if not q['part'].startswith(GROWTHS)]
    for k, (direction, length, thick, mat) in enumerate(CRYSTALS):
        d = rm.normalise(direction)
        root = tuple(MAIN[0][i] + d[i] * MAIN[1][i] * 0.88 for i in range(3))
        q = rm.spike(root, None, d, length, thick, mat, 'crystal%d' % k, sink=0.3)
        q['c'] = (q['c'][0], q['c'][1] + rm.LIFT, q['c'][2])
        body.append(q)
    return body, decals


def place(p):
    rm.anatomy = anatomy                      # the rock monster's own place(), carrying the crystals with the rest of the boulder
    try:
        return rm.place(p)
    finally:
        rm.anatomy = ROCK_ANATOMY


class CrystalRockMonster(rm.RockMonster):
    name = 'rock-monster-crystal'
    ramps = dict(rm.RAMPS,
                 stone=('p', 'p', 'l', 'k'),            # slate-blue stone: steel, steel, lavender, indigo
                 slate=('p', 'l', 'k', 'w'),
                 eye=('r', 'o', 'o', 'n'),              # glowing cyan eyes, against the rose crystals
                 crystal=('c', 'e', 'i', 'h'),          # rose crystal: salmon, coral, magenta, dark magenta
                 crystalB=('t', 'c', 'j', 'i'))         # a paler, hotter one: cream, salmon, hot pink, magenta

    @staticmethod
    def place(p):
        return place(p)


CREATURE = CrystalRockMonster()

if __name__ == '__main__':
    run(CREATURE)
