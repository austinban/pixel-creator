#!/usr/bin/env python3
"""A smaller mantis in a slightly different palette: the same creature as make_mantis.py, drawn at about 70% of its size.

Where the large mantis is violet and purple with yellow, this one is a pinker magenta with amber and orange, so the two can stand
side by side. Everything else (the shape, the poses, the praying arms) is shared.

    python3 tools/make_mantis_small.py sprites/mantis-small [--preview sheet.png]
    python3 tools/extract_poses.py --merge mantis-small=sprites/mantis-small
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import run  # noqa: E402
import make_mantis  # noqa: E402

CREATURE = make_mantis.Mantis()
CREATURE.name = 'mantis-small'
CREATURE.scale = 0.92                                   # the large one is 1.3
CREATURE.ramps = dict(make_mantis.RAMPS,
                      body=('y', 'u', 'w', 'x'),        # fuchsia, purple, grape, eggplant: pinker than the large one
                      limb=('u', 'w', 'x', 'x'),
                      stripe=('t', 'b', 'a', 'e'),      # cream, amber, orange, coral
                      eye=('d', 'b', 'a', 'e'))

if __name__ == '__main__':
    run(CREATURE)
