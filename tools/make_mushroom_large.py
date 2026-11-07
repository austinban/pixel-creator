#!/usr/bin/env python3
"""The large mushroom: the same creature as make_mushroom.py, drawn about a third bigger, and corrupted.

Where the small one is the red of a fly agaric with white dots and a cream stem, this one is blighted: a violet cap with glowing teal dots, a grey-lavender stem, teal gills, and
dark feet. The shape, the poses and the black mouth are shared.

    python3 tools/make_mushroom_large.py sprites/mushroom-large [--preview sheet.png]
    python3 tools/extract_poses.py --merge mushroom-large=sprites/mushroom-large
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import run  # noqa: E402
import make_mushroom  # noqa: E402

CREATURE = make_mushroom.Mushroom()
CREATURE.name = 'mushroom-large'
CREATURE.scale = 0.9                                    # the small one is 0.66
CREATURE.ramps = dict(make_mushroom.RAMPS,
                      cap=('v', 'u', 'w', 'x'),         # violet, purple, grape, eggplant: a sick purple cap
                      spot=('r', 'o', 'q', 's'),        # glowing teal dots: mint, cyan, teal, deep teal
                      gill=('o', 'q', 's', 'k'),        # teal gills
                      stem=('l', 'u', 'w', 'x'),        # a grey-lavender stem
                      volva=('u', 'w', 'x', 'x'),
                      tooth=('t', 'C', 'b', 'a'),
                      foot=('k', 'w', 'x', 'x'))

if __name__ == '__main__':
    run(CREATURE)
