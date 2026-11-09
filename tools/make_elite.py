#!/usr/bin/env python3
"""The elites: creatures bigger than an ordinary one that still stand on ONE ground tile, drawn in a 64 x 64 cell. The rat king is the first. Read from sprites/rat-king."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402
import extract_poses as ep  # noqa: E402

LAYOUT = {action + facing: (cols, rows) for action, facing, cols, rows in ep.POSES}      # the sheets lay frames out as the characters' do

ELITES = (('rat-king', 'Rat king'),)


def build_assets():
    """One asset for each action and facing, like the boss: `rat-king-attack-ne`, `rat-king-walking-se`..., 64 x 64, anchored at the middle of the tile."""
    assets = []
    root = Path(__file__).resolve().parent.parent / 'sprites'
    for elite_id, label in ELITES:
        folder = root / elite_id
        if not folder.is_dir():
            continue
        found = conventions.load_elite_frames(folder, elite_id)
        for action, count in conventions.BOSS_FRAMES.items():
            for facing in ('NE', 'SE'):
                frames = found.get(action + facing)
                if not frames:
                    continue
                cols, rows = LAYOUT[action + facing]
                assets.append({
                    'id': f'{elite_id}-{action}-{facing.lower()}', 'label': f'{label} - {action} ({facing})', 'category': 'Elites',
                    'kind': 'animation' if count > 1 else 'still', 'place': 'ground',
                    'w': conventions.ELITE_CELL, 'h': conventions.ELITE_CELL, 'cols': cols, 'rows': rows,
                    'fps': {'attack': 6, 'walking': 8}.get(action, 0),
                    'anchor': {'x': conventions.ELITE_ANCHOR[0], 'y': conventions.ELITE_ANCHOR[1]},
                    'frames': frames,
                })
    return assets
