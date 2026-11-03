#!/usr/bin/env python3
"""The king scorpion: the spirit scorpion's shape, drawn large and in red (see make_scorpion.py).

Where the spirit scorpion is pale mint and teal with a violet stinger, this one is a deep, hot red: a red-orange shell with amber
plates, big yellow pincers (the stinger's colour), and a yellow stinger with embers drifting off it in place of spirit-fire. Everything else (the shape, the
poses, the stretching tail-stab) is shared.

    python3 tools/make_scorpion_king.py --model previews/scorpion-king-3d.png   look at the 3D model first
    python3 tools/make_scorpion_king.py sprites/scorpion-king [--preview sheet.png]
    python3 tools/extract_poses.py --merge scorpion-king=sprites/scorpion-king
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import run  # noqa: E402
import make_scorpion  # noqa: E402

CREATURE = make_scorpion.Scorpion()
CREATURE.name = 'scorpion-king'
CREATURE.scale = 1.05                                    # the spirit scorpion is 0.95; any larger and the big claws run off the cell
CREATURE.ramps = dict(make_scorpion.RAMPS,
                      shell=('a', 'e', 'f', 'g'),        # a red-orange shell: orange lit, coral, orchid, plum in the shade
                      plate=('b', 'a', 'e', 'f'),        # lighter plates down the back: amber over the red
                      claw=('t', 'd', 'b', 'a'),         # the pincers are the stinger's yellow
                      glow=('t', 'd', 'b', 'a'),         # embers: cream, yellow, amber, orange
                      sting=('t', 'd', 'b', 'a'),        # a bright yellow stinger
                      crown=('d', 'b', 'a', 'e'),        # a gold crown
                      jewel=('j', 'i', 'h', 'w'))        # with a red-pink jewel

# big claws and a crown: every pose carries them, and the scorpion model reads them
CLAW_SCALE = 1.7
CREATURE.stand = dict(CREATURE.stand, claw_scale=CLAW_SCALE, crown=True)
CREATURE.poses = {name: [dict(frame, claw_scale=CLAW_SCALE, crown=True) for frame in frames] for name, frames in make_scorpion.Scorpion.poses.items()}

if __name__ == '__main__':
    run(CREATURE)
