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
SCALE = 1.25
CREATURE.scale = SCALE                                   # the spirit scorpion is 0.95; any larger and the big claws run off the cell
CREATURE.ramps = dict(make_scorpion.RAMPS,
                      shell=('a', 'e', 'f', 'g'),        # a red-orange shell: orange lit, coral, orchid, plum in the shade
                      plate=('b', 'a', 'e', 'f'),        # lighter plates down the back: amber over the red
                      claw=('t', 'd', 'b', 'a'),         # the pincers are the stinger's yellow
                      glow=('t', 'd', 'b', 'a'),         # embers: cream, yellow, amber, orange
                      sting=('t', 'd', 'b', 'a'),        # a bright yellow stinger
                      crown=('d', 'b', 'a', 'e'),        # a gold crown
                      jewel=('j', 'i', 'h', 'w'))        # with a red-pink jewel

# big claws and a crown: every pose carries them, and the scorpion model reads them
CLAW_SCALE = 1.6
LUNGE = 0.5
DEAD_ROLL = 150
DEAD_LIFT = 0.0         # the dead pose is raised in the model so its legs are not cut off at the bottom of the cell while it is drawn              # how much of the spirit scorpion's attack travel it keeps: a bigger body has less room to lunge
CREATURE.stand = dict(CREATURE.stand, claw_scale=CLAW_SCALE, crown=True)
def _pose(frame):
    f = dict(frame, claw_scale=CLAW_SCALE, crown=True)
    f['fwd'] = frame['fwd'] * LUNGE
    f['elongate'] = 1 + (frame['elongate'] - 1) * LUNGE
    f['claws'] = (frame['claws'][0] * LUNGE, frame['claws'][1], frame['claws'][2])
    return f


CREATURE.poses = {name: [_pose(frame) for frame in frames] for name, frames in make_scorpion.Scorpion.poses.items()}
# lying down, the big claws and the long tail would run off the cell, so the tail is curled in closer and the claws are tucked
CREATURE.poses['weak'] = [dict(f, tail=(10, 70, 4), claws=(-1.2, -0.6, 4)) for f in CREATURE.poses['weak']]
CREATURE.poses['dead'] = [dict(f, tail=(60, 112, 5), claws=(-1.2, -0.6, 4), roll=DEAD_ROLL, curl=0.6, lift=f['lift'] + DEAD_LIFT) for f in CREATURE.poses['dead']]

if __name__ == '__main__':
    run(CREATURE)
