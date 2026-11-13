"""Every asset family, in the order the Assets page lists them.

A family is a module with `build_assets()` (and, if it ships a folder with a README, `write_package(folder)`). Adding one is a line in UNITS below.
For each unit, `inputs` are files or folders it reads besides its code, `depends` are modules it loads by name (the code scan cannot see those),
and `outputs` are files it must leave on disk. tools/buildcache.py uses all three to rebuild only the units that changed.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / 'sprites'
ASSETS = SPRITES / 'assets'

from make_bow import PEOPLE as BOW_PEOPLE  # noqa: E402


@dataclass(frozen=True)
class Unit:
    name: str
    module: str
    func: str = 'build_assets'
    inputs: tuple = ()
    depends: tuple = ()
    outputs: tuple = ()
    takes_weapons_dir: bool = False       # the one unit that reads a folder the command line can move


UNITS = [
    Unit('crystal', 'make_crystal'),
    Unit('facing', 'make_facing'),
    Unit('overlays', 'make_overlay', inputs=(ASSETS / 'ground.png',)),
    Unit('ropes', 'make_ropes', inputs=(ROOT / 'poses' / 'base.js',)),
    Unit('boss', 'make_boss', inputs=(SPRITES / 'scorpion-emperor', SPRITES / 'blood-mushroom')),
    Unit('elite', 'make_elite', inputs=(SPRITES / 'rat-king',)),
    Unit('ui', 'make_ui'),
    Unit('buttons', 'make_buttons'),
    Unit('panel', 'make_panel'),
    Unit('bridge', 'make_bridge'),
    Unit('vine', 'make_vine'),
    Unit('fire', 'make_fire'),
    Unit('heal', 'make_heal'),
    Unit('arrows', 'make_arrow'),
    Unit('bows', 'make_bow', depends=tuple('make_' + p.replace('-', '_') for p in BOW_PEOPLE)),
    Unit('bone', 'make_bone'),
    Unit('amulets', 'make_amulets', depends=('make_weapon_icons3d',)),
    Unit('rock', 'make_rock'),
    Unit('rocks', 'make_rocks'),
    Unit('nodemap', 'make_nodemap'),
    Unit('buildings', 'make_buildings'),
    Unit('traps', 'make_traps'),
    Unit('chests', 'make_chest'),
    Unit('fungi', 'make_fungi'),
    Unit('trees', 'make_trees'),
    Unit('slot-icons', 'make_slot_icons'),
    Unit('item-icons', 'make_item_icons3d', depends=('make_item_icons',)),
    Unit('hud-icons', 'make_hud_icons'),
    Unit('ui-controls', 'make_ui_controls'),
    Unit('blood-pool', 'make_blood_pool'),
    Unit('body-explosion', 'make_body_explosion'),
    Unit('all-tree', 'make_all_tree'),
    Unit('all-tree-fall', 'make_all_tree_fall'),
    Unit('all-tree-wide', 'make_all_tree', func='build_wide_assets'),
    Unit('all-tree-fall-wide', 'make_all_tree_fall', func='build_wide_assets'),
    # the shop is drawn from the game's own sheets, so it follows them
    Unit('bazaar', 'make_bazaar', inputs=(ASSETS / 'amulets.png', ASSETS / 'crystal.png', ASSETS / 'rock.png', *sorted(ASSETS.glob('icon-weapon-*.png')))),
    Unit('abilities', 'make_abilities'),
    Unit('ground', 'make_ground', inputs=(ASSETS / 'ground.png',), outputs=(ASSETS / 'ground-corrupted.png',), depends=('make_corrupted_ground',)),
    Unit('water', 'make_water', inputs=(ASSETS / 'ground.png',), depends=('make_ground', 'make_corrupted_ground')),
    Unit('weapons', 'make_weapons', func='build_weapon_assets', takes_weapons_dir=True),
    Unit('weapon-icons', 'make_weapon_icons', func='build_icon_assets'),
]
