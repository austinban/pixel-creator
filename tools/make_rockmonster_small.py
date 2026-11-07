#!/usr/bin/env python3
"""The small rock monster: the same creature as make_rockmonster.py, drawn smaller, in warm sandstone with cyan eyes.

Where the first is cool teal-grey stone with red eyes, this one is a desert pebble: sand, amber and orange stone, a darker rust underside, green moss, and glowing cyan eyes.
The shape, the poses and the jump-and-bounce attack are shared.

    python3 tools/make_rockmonster_small.py sprites/rock-monster-small [--preview sheet.png]
    python3 tools/extract_poses.py --merge rock-monster-small=sprites/rock-monster-small
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import run  # noqa: E402
import make_rockmonster  # noqa: E402

CREATURE = make_rockmonster.RockMonster()
CREATURE.name = 'rock-monster-small'
CREATURE.scale = 0.85                                   # the first is 0.95
CREATURE.ramps = dict(make_rockmonster.RAMPS,
                      eye=('o', 'o', 'o', 'n'),       # cyan eyes
                      stone=('C', 'b', 'a', 'g'),       # sand, amber, orange, plum
                      slate=('b', 'a', 'g', 'w'))       # a darker rust

if __name__ == '__main__':
    run(CREATURE)
