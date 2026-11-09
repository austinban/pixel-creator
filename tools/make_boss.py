#!/usr/bin/env python3
"""The bosses, on a 2 x 2 footprint: 96 x 96 frames, one asset for each action and facing, read from sprites/NAME. The scorpion emperor and the blood mushroom."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402

# (the sprite folder and file prefix, the prefix of the asset ids, the name in the labels)
BOSSES = (
    ('scorpion-emperor', 'emperor', 'Scorpion emperor'),
    ('blood-mushroom', 'blood-mushroom', 'Blood mushroom'),
)


def build_assets():
    # A final boss on a 2 x 2 footprint: 96 x 96 frames, one asset for each action and facing.
    boss_assets = []
    for folder_name, prefix, label in BOSSES:
        boss_dir = Path(__file__).resolve().parent.parent / 'sprites' / folder_name
        if not boss_dir.is_dir():
            continue
        found = conventions.load_boss_frames(boss_dir, folder_name)
        for action, count in conventions.BOSS_FRAMES.items():
            for facing in ('NE', 'SE'):
                frames = found.get(action + facing)
                if not frames:
                    continue
                cols = min(count, 8)
                boss_assets.append({
                    'id': f'{prefix}-{action}-{facing.lower()}', 'label': f'{label} - {action} ({facing})', 'category': 'Bosses',
                    'kind': 'animation' if count > 1 else 'still', 'place': 'ground',
                    'w': conventions.BOSS_CELL, 'h': conventions.BOSS_CELL, 'cols': cols, 'rows': -(-count // cols),
                    'fps': {'attack': 6, 'walking': 8}.get(action, 0),
                    'anchor': {'x': conventions.BOSS_ANCHOR[0], 'y': conventions.BOSS_ANCHOR[1]},     # the middle of the 2 x 2 footprint
                    'frames': frames,
                })
    return boss_assets
