"""The ruins and the low structures: ruined walls, arches, heaps and floors, and the haybale stacks, stalls, sheds and carts a unit can climb.

Both kits follow the rock kit's model (footprint cells, flat tops, `walkable` only when every cell has at least WALK_MIN of flat top, one picture over the whole footprint
anchored at the middle of its bounding box on the ground), so the tests are the rock kit's, plus what is particular to them: a `cover` value on a sight blocker, floors that are
walkable at half a level, stepped stacks with the tall cell at the back, and an overgrown twin for many of the ruins.
"""
import json
import unittest
from pathlib import Path

from buildcache import assets_of
from make_rocks import MARGIN, WALK_MIN

ROOT = Path(__file__).resolve().parent.parent
COVER = ('low', 'high', 'full')
SOLID = ('wall', 'corner', 'tee', 'arch', 'heap')                  # ruins that are never walked on


def by_id(unit):
    return {a['id']: a for a in assets_of(unit)}


class Shared:
    """What both kits must satisfy; a subclass names its unit, category and folder."""
    unit = category = folder = None

    def assets(self):
        return by_id(self.unit)

    def test_ids_are_unique_and_every_picture_is_a_ground_still(self):
        assets = assets_of(self.unit)
        self.assertEqual(len({a['id'] for a in assets}), len(assets))
        for a in assets:
            self.assertEqual((a['category'], a['kind'], a['place'], len(a['frames']), a['folder']), (self.category, 'still', 'ground', 1, self.folder), a['id'])

    def test_every_picture_is_sized_to_its_footprint_and_anchored_in_the_middle(self):
        for a in self.assets().values():
            fx, fy = a['footprint']['size']
            self.assertEqual(a['w'], 16 * (fx + fy) + 2 * MARGIN, a['id'])
            self.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (a['w'], a['h']), a['id'])
            self.assertTrue(all(len(r) == a['w'] for r in rows), a['id'])
            low = max(y for y, r in enumerate(rows) if r.strip('.'))
            front = max(i + j + 2 for i, j in a['footprint']['cells'])
            self.assertGreaterEqual(low, a['anchor']['y'] + 8 * front - 4 * (fx + fy) - 7, a['id'])      # it stands on the ground diamond of its lowest cell
            self.assertLess(low, a['h'], a['id'])
            self.assertTrue(0 < a['anchor']['y'] < a['h'], a['id'])

    def test_the_footprint_fills_its_bounding_box_corner(self):
        for a in self.assets().values():
            fx, fy = a['footprint']['size']
            cells = {tuple(c) for c in a['footprint']['cells']}
            self.assertEqual(len(cells), len(a['footprint']['cells']), a['id'])
            self.assertTrue(any(c[0] == 0 for c in cells) and any(c[1] == 0 for c in cells), a['id'])
            self.assertTrue(any(c[0] == fx - 1 for c in cells) and any(c[1] == fy - 1 for c in cells), a['id'])
            self.assertTrue(all(0 <= i < fx and 0 <= j < fy for i, j in cells), a['id'])

    def test_a_walkable_piece_has_a_flat_top_over_every_cell(self):
        for a in self.assets().values():
            cells = sorted(f'{i},{j}' for i, j in a['footprint']['cells'])
            if a['walkable']:
                self.assertEqual(sorted(a['top_cover']), cells, a['id'])
                self.assertEqual(sorted(a['cell_levels']), cells, a['id'])
                self.assertGreaterEqual(min(a['top_cover'].values()), WALK_MIN, a['id'])
                self.assertLessEqual(max(a['top_cover'].values()), 1.0, a['id'])
                self.assertGreaterEqual(a['levels'] + 1e-9, max(a['cell_levels'].values()), a['id'])
            else:
                self.assertFalse(a['walkable'])

    def test_every_piece_is_outlined(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            h, w = len(rows), len(rows[0])
            for y in range(h):
                for x in range(w):
                    if rows[y][x] in '.OzA':                                       # moss and leaves may sit over the outline
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        self.assertTrue(0 <= nx < w and 0 <= ny < h and rows[ny][nx] != '.', f'{a["id"]}: a bare edge at {x},{y}')

    def test_the_pictures_differ(self):
        pics = {tuple(a['frames'][0]) for a in assets_of(self.unit)}
        self.assertEqual(len(pics), len(assets_of(self.unit)))

    def test_the_package_lists_every_picture_and_its_file_is_the_right_size(self):
        from PIL import Image
        package = json.loads((ROOT / 'sprites' / 'assets' / self.folder / f'{self.folder}.json').read_text())
        self.assertEqual(package['walk_min'], WALK_MIN)
        self.assertEqual(package['margin'], MARGIN)
        assets = self.assets()
        self.assertEqual(sorted(package['pieces']), sorted(assets))
        for id, rec in package['pieces'].items():
            a = assets[id]
            self.assertEqual(rec['walkable'], a['walkable'], id)
            self.assertEqual(rec['cells'], a['footprint']['cells'], id)
            self.assertEqual(rec.get('cover'), a.get('cover'), id)
            png = ROOT / 'sprites' / 'assets' / self.folder / rec['file']
            self.assertTrue(png.exists(), png)
            with Image.open(png) as im:
                self.assertEqual(im.size, (a['w'], a['h']), id)

    def test_it_is_the_same_every_time(self):
        import importlib
        module = importlib.import_module(self.module)
        again = module.build_assets()
        self.assertEqual([(a['id'], a['frames']) for a in again], [(a['id'], a['frames']) for a in assets_of(self.unit)])


class Ruins(Shared, unittest.TestCase):
    """Broken walls, corners, tees, arches and rubble heaps that block, and the foundation floors that can be walked on."""
    unit, category, folder, module = 'ruins', 'Ruins', 'ruins', 'make_ruins'

    def test_the_piece_kinds_are_the_ones_promised(self):
        kinds = {a['piece'] for a in self.assets().values()}
        self.assertEqual(kinds, {'wall', 'corner', 'tee', 'arch', 'heap', 'floor'})
        counts = {k: sum(a['piece'] == k for a in self.assets().values()) for k in kinds}
        self.assertGreaterEqual(counts['wall'] + counts['corner'] + counts['tee'], 30)
        self.assertGreaterEqual(counts['floor'], 8)
        self.assertGreaterEqual(counts['heap'], 8)

    def test_walls_arches_tees_corners_and_heaps_are_never_walkable_and_floors_always_are(self):
        for a in self.assets().values():
            if a['piece'] in SOLID:
                self.assertFalse(a['walkable'], a['id'])
                self.assertNotIn('top_cover', a)
            else:
                self.assertEqual(a['piece'], 'floor')
                self.assertTrue(a['walkable'], a['id'])

    def test_floors_are_walkable_at_half_a_level_and_one_cell_each(self):
        floors = [a for a in self.assets().values() if a['piece'] == 'floor']
        for a in floors:
            self.assertEqual(set(a['cell_levels'].values()), {0.5}, a['id'])            # a footing half a level high, not a whole step
            self.assertEqual(len(a['cell_levels']), len(a['footprint']['cells']), a['id'])
        self.assertTrue({(1, 1), (2, 2), (1, 2), (2, 1)} <= {tuple(a['footprint']['size']) for a in floors})

    def test_every_blocker_has_a_cover_value_and_nothing_else_does(self):
        for a in self.assets().values():
            if a['piece'] in SOLID:
                self.assertIn(a['cover'], COVER, a['id'])
            else:
                self.assertNotIn('cover', a, a['id'])

    def test_cover_follows_height(self):
        for a in self.assets().values():
            if a['piece'] not in SOLID:
                continue
            want = 'low' if a['levels'] < 1 else 'high' if a['levels'] < 1.75 else 'full'
            self.assertEqual(a['cover'], want, f"{a['id']} ({a['levels']} levels)")

    def test_heaps_are_low_and_arches_and_two_high_walls_are_full(self):
        for a in self.assets().values():
            if a['piece'] == 'heap':
                self.assertEqual(a['cover'], 'low', a['id'])
            if a['piece'] == 'arch' or (a['piece'] in ('wall', 'corner') and '-h2' in a['id']):
                self.assertEqual(a['cover'], 'full', a['id'])

    def test_a_wall_along_x_and_along_y_are_mirror_pairs(self):
        a = self.assets()
        for id in a:
            if '-x-' in id or id.endswith('-x') or id.endswith('-x-grown'):
                twin = id.replace('-x', '-y', 1)
                self.assertIn(twin, a, id)
                self.assertEqual((a[id]['cover'], a[id]['footprint']['size']), (a[twin]['cover'], a[twin]['footprint']['size']), id)

    def test_an_overgrown_twin_shares_its_base_footprint_and_kind_and_is_a_little_taller(self):
        a = self.assets()
        grown = [x for x in a.values() if x['overgrown']]
        self.assertGreaterEqual(len(grown), 15)
        for g in grown:
            self.assertTrue(g['id'].endswith('-grown'), g['id'])
            base = a[g['id'][:-len('-grown')]]
            self.assertFalse(base['overgrown'], base['id'])
            self.assertEqual(g['footprint'], base['footprint'], g['id'])
            self.assertEqual((g['piece'], g['walkable'], g.get('cover')), (base['piece'], base['walkable'], base.get('cover')), g['id'])
            self.assertGreaterEqual(g['levels'], base['levels'], g['id'])
            self.assertNotEqual(g['frames'], base['frames'], g['id'])
            self.assertTrue(set(''.join(g['frames'][0])) & set('zAB'), g['id'])         # it has moss or leaves on it

    def test_an_overgrown_walkable_floor_is_still_walkable(self):
        for a in self.assets().values():
            if a['overgrown'] and a['piece'] == 'floor':
                self.assertTrue(a['walkable'], a['id'])
                self.assertGreaterEqual(min(a['top_cover'].values()), WALK_MIN, a['id'])


class LowStructures(Shared, unittest.TestCase):
    """Haybale stacks, crate piles, stalls, sheds, carts and wagons: climbable steps one or two levels up, some with the cover of an awning or an alcove."""
    unit, category, folder, module = 'low-structures', 'Low structures', 'low-structures', 'make_lowstructures'

    def test_the_piece_kinds_are_the_ones_promised(self):
        self.assertEqual({a['piece'] for a in self.assets().values()}, {'hay', 'crates', 'stall', 'shed', 'cart', 'wagon'})

    def test_a_walkable_piece_stands_at_whole_levels(self):
        for a in self.assets().values():
            if a['walkable']:
                for cell, level in a['cell_levels'].items():
                    self.assertIn(level, (1, 2), f"{a['id']} {cell}")
                self.assertIn(a['levels'], (1, 2), a['id'])
                self.assertEqual(a['levels'], max(a['cell_levels'].values()), a['id'])

    def test_a_stepped_stack_is_tall_at_the_back_and_low_in_front(self):
        stepped = [a for a in self.assets().values() if a['id'].endswith('-stepped')]
        self.assertGreaterEqual(len(stepped), 8)
        for a in stepped:
            levels = {tuple(int(n) for n in k.split(',')): v for k, v in a['cell_levels'].items()}
            tallest = max(levels.values())
            self.assertEqual(tallest, 2, a['id'])
            self.assertIn(1, levels.values(), a['id'])
            back = min(levels, key=lambda c: (c[0] + c[1], c))
            self.assertEqual(levels[back], tallest, f'{a["id"]}: the tall cell must be at the back')
            for cell, level in levels.items():
                if level == tallest:
                    self.assertEqual(sum(cell), min(sum(c) for c in levels), f'{a["id"]}: a tall cell {cell} in front of a lower one hides it')

    def test_a_plain_stack_is_one_level_over_all_its_cells(self):
        for a in self.assets().values():
            if a['piece'] in ('hay', 'crates') and not a['id'].endswith('-stepped'):
                self.assertEqual(len(set(a['cell_levels'].values())), 1, a['id'])

    def test_a_sloping_awning_is_cover_and_not_walkable_and_everything_else_is_walkable(self):
        for a in self.assets().values():
            if 'slope' in a['id']:
                self.assertEqual((a['walkable'], a['cover']), (False, 'high'), a['id'])
                self.assertNotIn('top_cover', a)
            else:
                self.assertTrue(a['walkable'], a['id'])
                self.assertNotIn('cover', a, a['id'])

    def test_a_cart_or_wagon_has_a_load_flat_enough_to_stand_on(self):
        for a in self.assets().values():
            if a['piece'] in ('cart', 'wagon'):
                self.assertTrue(a['walkable'], a['id'])
                self.assertGreaterEqual(min(a['top_cover'].values()), WALK_MIN, a['id'])
                self.assertEqual(set(a['cell_levels'].values()), {1}, a['id'])

    def test_a_shed_opens_one_way_and_comes_in_both_openings(self):
        sheds = [a for a in self.assets().values() if a['piece'] == 'shed']
        self.assertEqual(len(sheds), 6)
        opens = {a['id'].rsplit('-', 1)[1] for a in sheds}
        self.assertEqual(opens, {'se', 'sw'})
        for a in sheds:
            self.assertEqual(a['id'].count('-'), 4, a['id'])
        pairs = {a['id'].rsplit('-', 1)[0] for a in sheds}
        self.assertIn('low-shed-1x1-h1', pairs)
        self.assertIn('low-shed-1x1-h2', pairs)

    def test_none_are_overgrown(self):
        self.assertFalse(any(a['overgrown'] for a in self.assets().values()))


if __name__ == '__main__':
    unittest.main()
