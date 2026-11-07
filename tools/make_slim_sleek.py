#!/usr/bin/env python3
"""A sleeker slim person: the Slim (make_slim.py) in a still narrower, less blocky build, and in the colours of the spirit realm.

Narrower through the body, shoulders and hips than the Slim (bulk 0.75 against 1.0, shoulders 2.6 against 3.2), with a slightly narrower head and a little larger overall. Ashen skin, teal
hair and a moss-green tunic. It is another base beside Human, Slim and Human (sleek); the others keep their looks. The sleek build is a declared choice in conventions.py (BUILDS).

    python3 tools/make_slim_sleek.py sprites/slim-sleek [--preview sheet.png]
    python3 tools/extract_poses.py --merge slim-sleek=sprites/slim-sleek

Its lean and strike-hand numbers are its own (tools/data/slim-sleek_*.json), made with `tune_lean.py slim-sleek` and `fit_hands.py slim-sleek`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humanoid import Humanoid, run  # noqa: E402

SLEEK = {'bulk': 0.75, 'shoulder_z': 2.6, 'hip_z': 1.15, 'head_rx': 4.4, 'head_ry': 4.6, 'head_rz': 4.15, 'scale': 1.1}

CREATURE = Humanoid(
    'slim-sleek',
    ramps={
        'skin': ('t', 'c', 'f', 'g'),
        'shirt': ('A', 'B', 's', 'k'),     # a moss-green tunic
        'pants': ('l', 'k', 'w', 'x'),
        'hair': ('r', 'q', 's', 'k'),      # teal hair
        'shoes': ('w', 'x', 'x', 'x'),
        'belt': ('o', 'q', 's', 'k'),
    },
    body=SLEEK,
    tweaks={'damageNE': {'lift': -4.2}, 'damageSE': {'lift': -4.2}},      # the flinch crouches a little less, so this narrower figure is still tall enough in it
)

if __name__ == '__main__':
    run(CREATURE)
