#!/usr/bin/env python3
"""A slimmer person: a second build of the generic human, made the same way (see humanoid.py).

Same proportions of head, limbs and reach, so the poses, the swing and the weapon hand all carry
over, but a lighter body: no extra bulk through the torso and legs, narrower shoulders and hips. A green
tunic and ginger hair tell it from the standard Human. The slim build is a declared choice in
conventions.py (BUILDS), which allows a little less weight than the standard build.

    python3 tools/make_slim.py sprites/slim [--preview sheet.png]
    python3 tools/extract_poses.py --merge slim=sprites/slim

Its lean, weight shift and strike-hand numbers are its own (tools/data/slim_*.json), made with
`python3 tools/tune_lean.py slim` and `python3 tools/fit_hands.py slim`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humanoid import Humanoid, run  # noqa: E402

CREATURE = Humanoid(
    'slim',
    ramps={
        'shirt': ('z', 'A', 'B', 's'),      # lime, green, emerald, deep teal
        'pants': ('l', 'k', 'w', 'x'),
        'hair': ('b', 'a', 'e', 'f'),       # ginger
    },
    body={'bulk': 1.0, 'shoulder_z': 3.2, 'hip_z': 1.4},
    # With less body to fold, the slump seen from behind has to be folded further and turned a little
    # to be as low as the originals' while still leaning like them. Found by searching that one pose.
    tweaks={'weakNE': {'pitch': -70, 'lift': -6.6, 'sway': 4, 'twist': -15, 'head_pitch': -10}},
)

if __name__ == '__main__':
    run(CREATURE)
