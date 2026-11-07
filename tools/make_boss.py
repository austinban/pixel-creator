#!/usr/bin/env python3
"""The scorpion emperor, a final boss on a 2 x 2 footprint: 96 x 96 frames, one asset for each action and facing, read from sprites/scorpion-emperor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402


def build_assets():
    # The scorpion emperor, a final boss on a 2 x 2 footprint: 96 x 96 frames, one asset for each action and facing.
    boss_assets = []
    boss_dir = Path(__file__).resolve().parent.parent / 'sprites' / 'scorpion-emperor'
    if boss_dir.is_dir():
        found = conventions.load_boss_frames(boss_dir, 'scorpion-emperor')
        for action, count in conventions.BOSS_FRAMES.items():
            for facing in ('NE', 'SE'):
                frames = found.get(action + facing)
                if not frames:
                    continue
                cols = min(count, 8)
                boss_assets.append({
                    'id': f'emperor-{action}-{facing.lower()}', 'label': f'Scorpion emperor - {action} ({facing})', 'category': 'Bosses',
                    'kind': 'animation' if count > 1 else 'still', 'place': 'ground',
                    'w': conventions.BOSS_CELL, 'h': conventions.BOSS_CELL, 'cols': cols, 'rows': -(-count // cols),
                    'fps': {'attack': 6, 'walking': 8}.get(action, 0),
                    'anchor': {'x': conventions.BOSS_ANCHOR[0], 'y': conventions.BOSS_ANCHOR[1]},     # the middle of the 2 x 2 footprint
                    'frames': frames,
                })
    return boss_assets
