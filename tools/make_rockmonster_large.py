#!/usr/bin/env python3
"""The large rock monster: the same creature as make_rockmonster.py, drawn bigger, in black volcanic stone with glowing ember cracks and yellow eyes.

Where the first is cool teal-grey stone with moss, this one is obsidian: lavender, purple and grape stone over an eggplant underside, glowing yellow-orange patches where the moss was, and
yellow eyes. The shape, the poses and the jump-and-bounce attack are shared.

    python3 tools/make_rockmonster_large.py sprites/rock-monster-large [--preview sheet.png]
    python3 tools/extract_poses.py --merge rock-monster-large=sprites/rock-monster-large
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import run  # noqa: E402
import make_rockmonster  # noqa: E402

CREATURE = make_rockmonster.RockMonster()
CREATURE.name = 'rock-monster-large'
CREATURE.scale = 1.05                                    # the first is 0.95
CREATURE.ramps = dict(make_rockmonster.RAMPS,
                      eye=('d', 'd', 'd', 'b'),       # yellow eyes
                      stone=('l', 'u', 'w', 'x'),       # lavender, purple, grape, eggplant
                      slate=('u', 'w', 'x', 'x'),
                      moss=('d', 'b', 'a', 'g'))        # glowing ember: yellow, amber, orange, plum

# At this size the full jump and lunge would leave the 32 x 32 cell, so the attack travels a little less far and high; the crouch, the squash and the rebound are the same.
TRAVEL = 0.4
CREATURE.poses = dict(CREATURE.poses, attack=[dict(f, lift=f['lift'] * TRAVEL if f['lift'] > 0 else f['lift'], fwd=f['fwd'] * TRAVEL) for f in CREATURE.poses['attack']])

if __name__ == '__main__':
    run(CREATURE)
