#!/usr/bin/env python3
"""A generic human: the worked example of a humanoid built with humanoid.py.

Nothing here draws anything. It only says what this person wears, and the process in
humanoid.py does the rest: a blue tunic, dark trousers, brown boots and hair.

    python3 tools/make_human.py sprites/human [--preview sheet.png]
    python3 tools/extract_poses.py --merge human=sprites/human

To make another person, copy this file and change the name, the colours, the hair, the
proportions or add accessories. See the notes at the top of humanoid.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humanoid import Humanoid, run  # noqa: E402

CREATURE = Humanoid('human')

if __name__ == '__main__':
    run(CREATURE)
