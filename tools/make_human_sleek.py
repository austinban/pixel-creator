#!/usr/bin/env python3
"""A sleeker human: the generic human (make_human.py) in a narrower, less blocky build, and in the colours of the spirit realm.

Narrower through the body, shoulders and hips than the first Human (bulk 1.1 against 1.5, shoulders 3.0 against 3.7), with a slightly narrower head and a little larger overall, so it
reads as slender and not chunky. Ashen skin, violet hair, a dark teal tunic and a glowing teal belt. It is another base beside Human, Slim and Slim (sleek); the others keep their looks.
The sleek build is a declared choice in conventions.py (BUILDS), which allows it a little less weight.

    python3 tools/make_human_sleek.py sprites/human-sleek [--preview sheet.png]
    python3 tools/extract_poses.py --merge human-sleek=sprites/human-sleek

Its lean and strike-hand numbers are its own (tools/data/human-sleek_*.json), made with `tune_lean.py human-sleek` and `fit_hands.py human-sleek`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humanoid import Humanoid, run  # noqa: E402

SLEEK_HUMAN = {'bulk': 1.1, 'shoulder_z': 3.0, 'hip_z': 1.35, 'head_rx': 4.4, 'head_ry': 4.6, 'head_rz': 4.15, 'scale': 1.1}

CREATURE = Humanoid(
    'human-sleek',
    ramps={
        'skin': ('t', 'c', 'f', 'g'),      # pale, ashen skin with a little mauve
        'hair': ('v', 'u', 'w', 'x'),      # violet hair
        'shirt': ('s', 'k', 'w', 'x'),     # a dark teal tunic
        'pants': ('l', 'k', 'w', 'x'),
        'shoes': ('w', 'x', 'x', 'x'),
        'belt': ('o', 'q', 's', 'k'),      # a glowing teal belt
    },
    body=SLEEK_HUMAN,
)

if __name__ == '__main__':
    run(CREATURE)
