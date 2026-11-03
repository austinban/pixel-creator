#!/usr/bin/env python3
"""Blossom: a flower fairy, a delicate humanoid (see humanoid.py and fairy.py).

Slim and light, with butterfly wings of pale mint, a skirt of coral petals and a rose-pink bodice, long
white hair, and pointed ears. Built like the other people, so it uses their poses, the lean, the walk and the bow.

    python3 tools/make_blossom.py --model previews/blossom-3d.png    look at the 3D model first
    python3 tools/make_blossom.py sprites/blossom [--preview sheet.png]
    python3 tools/extract_poses.py --merge blossom=sprites/blossom
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fairy  # noqa: E402
import make_slim  # noqa: E402

from creature import deg, mm, part  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402


def gear(j, pose):
    parts = fairy.wings(j) + fairy.petal_skirt(j) + fairy.pointed_ears(j)
    # a blossom in her hair, over one ear
    parts.append(part(j['head'](-0.2, fairy.HEAD_Y + 3.4, 3.0), (1.0, 1.0, 1.0), 'bloom', 'bloom', j['head_R']))
    parts.append(part(j['head'](-0.2, fairy.HEAD_Y + 3.4, 3.0), (0.55, 0.55, 0.55), 'heart', 'bloom2', j['head_R']))
    return parts


CREATURE = Humanoid(
    'blossom',
    ramps={
        'skin': ('t', 'C', 'b', 'e'),
        'hair': ('t', 't', 'r', 'p'),            # white: cream, with a cool mint and steel shade
        'shirt': ('c', 'e', 'f', 'g'),           # the bodice
        'pants': ('t', 'C', 'c', 'e'),           # pale stockings
        'shoes': ('c', 'e', 'f', 'g'),
        'belt': ('d', 'b', 'a', 'e'),            # a gold sash
        'wing': ('t', 'r', 'q', 'p'),            # cream to mint: pale, like light through petals
        'petal': ('c', 'e', 'f', 'g'),           # coral petals
        'bloom': ('c', 'e', 'f', 'g'),           # a coral blossom, so it shows against the white hair
        'heart': ('d', 'b', 'a', 'e'),
    },
    body=dict(make_slim.CREATURE.body, bulk=0.82, shoulder_z=3.0, hip_z=1.25, ears=False),
    hair='long',
    # a flinch crouches less, or this slight figure ends up shorter than the damage pose should be
    tweaks={'damageSE': {'lift': -3.4, 'sway': 3.5}, 'damageNE': {'lift': -3.4}},
    accessories=gear,
    calibrate_like=make_slim.CREATURE,
)

if __name__ == '__main__':
    run(CREATURE)
