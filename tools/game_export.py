"""What the game (iso-fft-like) pulls from this repo, written as sprites/assets/game-export.json by make_assets.py.

pixel-creator decides what it ships: a family whose sheets the game should have is listed in EXPORT, and the game's sync
(tools/sync_sprites.py there) merges this file into its own manifest, so a new family reaches the game with no edit on its side.
`to` is the folder in the game, relative to the game's root. A folder of sheets that is not for the game is named in NOT_FOR_GAME
with the reason, and tools/test_handoff.py fails on any folder of sheets that is in neither list.

Not here: what the game reads in a way of its own (characters and weapons, the ground sheets, icons cut from sheets, assets rendered
from data.js, the piece table); its manifest keeps those.

    python3 tools/game_export.py            # write sprites/assets/game-export.json (make_assets.py does this too)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'sprites' / 'assets' / 'game-export.json'

EXPORT = {
    'png_folders': [
        {'from': 'sprites/assets/buildings', 'pattern': 'bld-*.png', 'to': 'assets/sprites/buildings'},
        {'from': 'sprites/assets/nodemap', 'pattern': 'nodemap-*.png', 'to': 'assets/sprites/nodemap'},
        {'from': 'sprites/assets/traps', 'pattern': 'trap-*.png', 'to': 'assets/sprites/traps'},
        {'from': 'sprites/assets/abilities', 'pattern': '*.png', 'to': 'assets/sprites/abilities'},
        {'from': 'sprites/assets/chests', 'pattern': 'chest-*.png', 'to': 'assets/sprites/chests'},
        {'from': 'sprites/assets/mushroom-trees', 'pattern': 'fungus-*.png', 'to': 'assets/sprites/props'},
        {'from': 'sprites/assets/trees', 'pattern': '*.png', 'to': 'assets/sprites/props'},
        {'from': 'sprites/assets/rocks', 'pattern': 'rock-*.png', 'to': 'assets/sprites/rocks'},
        {'from': 'sprites/assets/ruins', 'pattern': 'ruin-*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/low-structures', 'pattern': 'low-*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/stairs', 'pattern': 'stair-*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/scaffold-stairs', 'pattern': 'scaffold-*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/graveyard', 'pattern': '*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/corrupted-terrain', 'pattern': '*.png', 'to': 'assets/sprites/pieces'},
        {'from': 'sprites/assets/water', 'pattern': 'water-*.png', 'to': 'assets/sprites/water'},
        {'from': 'sprites/assets/buttons', 'pattern': 'ui-button-*.png', 'to': 'assets/sprites/ui/buttons'},
        {'from': 'sprites/assets/panel', 'pattern': 'ui-panel-*.png', 'to': 'assets/sprites/ui/panel'},
        {'from': 'sprites/assets/hud-icons', 'pattern': 'icon-*.png', 'to': 'assets/sprites/ui/icons'},
        {'from': 'sprites/assets/ui-controls', 'pattern': 'ui-*.png', 'to': 'assets/sprites/ui/controls'},
    ],
    'raw_files': [
        {'from': 'sprites/assets/all-tree/all-tree-wide.png', 'to': 'assets/sprites/victory/all-tree-wide.png'},
        {'from': 'sprites/assets/all-tree/all-tree.json', 'to': 'assets/sprites/victory/all-tree.json'},
        {'from': 'sprites/assets/all-tree-fall/all-tree-fall-wide.png', 'to': 'assets/sprites/victory/all-tree-fall-wide.png'},
        {'from': 'sprites/assets/blood-pool.png', 'to': 'assets/sprites/decals/blood-pool.png'},
        {'from': 'sprites/assets/trees/trees.json', 'to': 'assets/sprites/trees/trees.json'},
        {'from': 'sprites/assets/rocks/rocks.json', 'to': 'assets/sprites/rocks/rocks.json'},
        {'from': 'sprites/assets/water/water.json', 'to': 'assets/sprites/water/water.json'},
        {'from': 'sprites/assets/buttons/buttons.json', 'to': 'assets/sprites/ui/buttons/buttons.json'},
        {'from': 'sprites/assets/panel/panel.json', 'to': 'assets/sprites/ui/panel/panel.json'},
        {'from': 'sprites/assets/buildings/buildings.json', 'to': 'assets/sprites/buildings/buildings.json'},
        {'from': 'sprites/assets/traps/traps.json', 'to': 'assets/sprites/traps/traps.json'},
        {'from': 'sprites/assets/abilities/abilities.json', 'to': 'assets/sprites/abilities/abilities.json'},
        {'from': 'sprites/assets/manifest.json', 'to': 'assets/sprites/pixel-creator-manifest.json'},
        {'from': 'sprites/assets/buildings/example-street.json', 'to': 'tests/fixtures/buildings/example-street.json'},
        {'from': 'sprites/assets/buildings/example-street.png', 'to': 'tests/fixtures/buildings/example-street.png'},
    ],
}

# Folders of sheets the game does not take as a folder, and why. A folder of PNGs in neither list fails tools/test_handoff.py.
NOT_FOR_GAME = {
    'item-icons': 'the game cuts these itself (its manifest: item_icons)',
    'slot-icons': 'the game renders its slot icons from data.js (built_assets)',
    'bridges': 'the game draws bridges from data.js (built_assets: bridge)',
    'destructibles': 'not used by the game yet',
    'water-props': 'not used by the game yet',
    'weather': 'not used by the game yet',
    'sets': 'the terrain page\'s sets; the game reads no art from here',
    'all-tree': 'only the wide sheet and its JSON go, as raw files',
    'all-tree-fall': 'only the wide sheet goes, as a raw file',
}


def write(path=OUT):
    body = {'about': __doc__.split('\n\n')[0] + ' See tools/game_export.py.', 'format': 1, **EXPORT}
    text = json.dumps(body, indent=1) + '\n'
    if not path.exists() or path.read_text() != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return path


if __name__ == '__main__':
    print(f'wrote {write().relative_to(ROOT)}')
