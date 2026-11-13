"""The water props (docks, boats, stepping stones, waterfalls, pads, reeds) and the destructibles (barricades, barrels, walls, urns, a hay cart): sizes and anchors, the water's drawing level,
which pieces are walkable and why, corrupted twins, animations that loop, and the three states plus the destruction strip of every destructible."""
import json
import tempfile
import unittest
from pathlib import Path

from buildcache import assets_of

LEVEL = 16
WALK_MIN = 0.6                    # the rock kit's rule: every cell of a walkable piece has at least this much flat top
TOLERANCE = 0.01                  # top_cover is rounded to two places


def mask(rows):
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}


def differing(a, b):
    return sum(1 for ra, rb in zip(a, b) for ca, cb in zip(ra, rb) if ca != cb)


def lowest(rows):
    return max(y for y, r in enumerate(rows) if r.strip('.'))


class WaterProps(unittest.TestCase):
    """Things that live on and beside the water. z = 0 in a picture is the surface of a water tile (one game step, 8 pixels, under the land)."""

    @classmethod
    def setUpClass(cls):
        cls.list = assets_of('water-props')
        cls.assets = {a['id']: a for a in cls.list}

    def test_ids_are_unique_and_in_their_own_category_and_folder(self):
        self.assertEqual(len(self.list), len(self.assets))
        for a in self.list:
            self.assertEqual((a['category'], a['folder'], a['place']), ('Water props', 'water-props', 'ground'), a['id'])

    def test_every_piece_is_the_size_its_footprint_and_anchor_say(self):
        for a in self.list:
            fx, fy = a['footprint']['size']
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (a['w'], a['h']), a['id'])
            for f in a['frames']:
                self.assertEqual((len(f[0]), len(f)), (a['w'], a['h']), a['id'])      # every frame is the same size, so they swap in place
            self.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])                   # the middle of the footprint is the middle of the picture
            self.assertTrue(0 <= a['anchor']['y'] < a['h'], a['id'])
            self.assertGreaterEqual(a['w'], 16 * (fx + fy), a['id'])                   # it is at least as wide as the diamonds it covers
            self.assertLessEqual(a['w'], 16 * (fx + fy) + 32, a['id'])        # room for foam and a waterfall's spill
            cells = {tuple(c) for c in a['footprint']['cells']}
            self.assertEqual(cells, {(i, j) for i in range(fx) for j in range(fy)}, a['id'])    # every piece here is a plain rectangle

    def test_the_picture_stands_on_its_anchor(self):
        """The anchor is a point on the water's surface (z = 0): the picture reaches at least that far down, and no further than its own last row."""
        for a in self.list:
            for f in a['frames']:
                low = lowest(f)
                self.assertGreaterEqual(low, a['anchor']['y'] - 2, a['id'])
                self.assertLess(low, a['h'], a['id'])

    def test_decals_and_reeds_have_the_sizes_the_game_is_told(self):
        for pid in ('lily-pads', 'mushroom-pads'):
            a = self.assets[pid]
            self.assertEqual((a['w'], a['h'], a['anchor'], len(a['frames']), a['kind']), (32, 16, {'x': 16, 'y': 8}, 4, 'variants'), pid)
        for pid, frames, kind in (('reeds', 3, 'variants'), ('reeds-corrupted', 3, 'variants'), ('reeds-sway', 4, 'animation'), ('reeds-corrupted-sway', 4, 'animation')):
            a = self.assets[pid]
            self.assertEqual((a['w'], a['h'], a['anchor'], len(a['frames']), a['kind'], a['surface']), (32, 32, {'x': 16, 'y': 25}, frames, kind, 'shore'), pid)

    def test_a_walkable_piece_is_flush_with_the_land_and_flat_over_every_cell(self):
        walkable = [a for a in self.list if a['walkable']]
        self.assertEqual(sorted(a['id'] for a in walkable), sorted(i for i in self.assets if i.startswith(('dock-', 'stepping-'))))
        self.assertGreaterEqual(len(walkable), 13)
        for a in walkable:
            self.assertEqual(a['levels'], 0.5, a['id'])                                # the deck is the land's height: half a level (8 pixels, one game step) above the water's surface
            self.assertEqual(sorted(a['top_cover']), sorted(f'{i},{j}' for i, j in a['footprint']['cells']), a['id'])
            self.assertGreaterEqual(min(a['top_cover'].values()) + TOLERANCE, WALK_MIN, a['id'])
            self.assertTrue(all(0 <= v <= 1 for v in a['top_cover'].values()), a['id'])

    def test_a_piece_that_is_not_walkable_has_no_flat_top_claimed(self):
        for a in self.list:
            if not a['walkable']:
                self.assertNotIn('top_cover', a, a['id'])

    def test_the_flat_top_is_what_the_generator_measures(self):
        import make_water_props as m
        for fx, fy in ((1, 2), (3, 1)):
            built = m.build_dock(fx, fy, False)
            record = self.assets[f'dock-{fx}x{fy}']
            self.assertEqual({f'{i},{j}': round(v, 2) for (i, j), v in built['cover'].items()}, record['top_cover'])
        self.assertEqual(m.WALK_MIN, WALK_MIN)
        self.assertEqual(m.DECK, 0.5)

    def test_the_deck_and_stones_are_wider_than_a_unit_can_miss(self):
        """Walkable pieces are full-footprint: each cell of a dock has the same cover, so there are no gaps in the planks along its length."""
        for a in self.list:
            if a['id'].startswith('dock-'):
                self.assertEqual(len(set(a['top_cover'].values())), 1, a['id'])

    def test_a_corrupted_twin_has_the_footprint_and_numbers_of_its_base(self):
        pairs = [(i, i + '-corrupted') for i in ('dock-1x2', 'dock-2x1', 'dock-1x3', 'dock-3x1', 'waterfall-ne', 'waterfall-se', 'reeds')] + [('reeds-sway', 'reeds-corrupted-sway')]
        for base, twin in pairs:
            a, b = self.assets[base], self.assets[twin]
            for key in ('w', 'h', 'anchor', 'footprint', 'walkable', 'kind', 'fps', 'cols', 'rows', 'surface'):
                self.assertEqual(a[key], b[key], f'{base} / {twin}: {key}')
            self.assertEqual(a.get('top_cover'), b.get('top_cover'), twin)
            self.assertEqual(a.get('levels'), b.get('levels'), twin)
            self.assertEqual(len(a['frames']), len(b['frames']), twin)
            self.assertNotEqual(a['frames'], b['frames'], f'{twin} is the same picture as {base}')
            self.assertTrue(any(mask(f) for f in b['frames']), twin)

    def test_the_corrupted_water_is_in_the_corrupted_teal(self):
        """The waterfall's water roles are swapped for the corrupted water's teal (s, D, q): it uses none of the plain waterfall's blue roles for its water."""
        plain = ''.join(''.join(f) for f in self.assets['waterfall-ne']['frames'])
        cor = ''.join(''.join(f) for f in self.assets['waterfall-ne-corrupted']['frames'])
        self.assertGreater(plain.count('o') + plain.count('n'), 3 * (cor.count('o') + cor.count('n')))
        self.assertGreater(cor.count('s') + cor.count('D'), 3 * (plain.count('s') + plain.count('D')))

    def test_animations_have_their_frames_and_loop(self):
        expect = {'waterfall-ne': (6, 8), 'waterfall-se': (6, 8), 'waterfall-ne-corrupted': (6, 8), 'waterfall-se-corrupted': (6, 8),
                  'reeds-sway': (4, 4), 'reeds-corrupted-sway': (4, 4)}
        for pid, (frames, fps) in expect.items():
            a = self.assets[pid]
            self.assertEqual((a['kind'], len(a['frames']), a['fps']), ('animation', frames, fps), pid)
            self.assertEqual((a['cols'], a['rows']), (frames, 1), pid)
            steps = [differing(a['frames'][k], a['frames'][(k + 1) % frames]) for k in range(frames)]    # the last step is the loop point
            self.assertTrue(all(s > 0 for s in steps), f'{pid}: a frame repeats the next one')
            self.assertLessEqual(steps[-1], 1.25 * max(steps[:-1]), f'{pid}: the loop point jumps more than the frames do')

    def test_the_stills_are_not_animations_and_the_variants_differ(self):
        for a in self.list:
            if a['kind'] == 'still':
                self.assertEqual((len(a['frames']), a['fps']), (1, 0), a['id'])
            if a['kind'] == 'variants':
                self.assertEqual(len(a['names']), len(a['frames']), a['id'])
                self.assertEqual(len({tuple(f) for f in a['frames']}), len(a['frames']), a['id'])

    def test_the_boat_is_scenery_and_the_falls_and_pads_are_never_walkable(self):
        for pid in ('rowboat-2x1', 'rowboat-1x2', 'waterfall-ne', 'waterfall-se', 'lily-pads', 'mushroom-pads', 'reeds'):
            self.assertFalse(self.assets[pid]['walkable'], pid)
        self.assertEqual(self.assets['rowboat-2x1']['footprint']['size'], [2, 1])
        self.assertEqual(self.assets['rowboat-1x2']['footprint']['size'], [1, 2])

    def test_the_drawing_level_is_written_down(self):
        import make_water_props as m
        doc = m.__doc__
        self.assertIn('z = 0', doc)
        self.assertIn('surface', doc)
        folder = Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'water-props'
        self.assertIn('z = 0', (folder / 'README.md').read_text())

    def test_the_package_lists_every_file(self):
        import make_water_props as m
        with tempfile.TemporaryDirectory() as tmp:
            m.write_package(tmp)
            pkg = json.loads((Path(tmp) / 'water-props.json').read_text())
        self.assertEqual(sorted(pkg['props']), sorted(self.assets))
        self.assertEqual((pkg['level'], pkg['walk_min'], pkg['deck_levels']), (LEVEL, WALK_MIN, 0.5))
        for pid, rec in pkg['props'].items():
            self.assertEqual(rec['walkable'], self.assets[pid]['walkable'], pid)
            self.assertEqual(rec['file'], f'{pid}.png', pid)

    def test_it_is_the_same_every_time(self):
        import make_water_props as m
        self.assertEqual([a['frames'] for a in m.build_assets()], [a['frames'] for a in self.list])


class Destructibles(unittest.TestCase):
    """Things that can be broken: each has three states (one asset of kind `variants`) and a six frame destruction strip, `<id>-destroy`, all the same size and anchor."""

    PIECES = ('barricade-1x1', 'barricade-1x2', 'barrel-explosive', 'barrel-stack', 'wall-1x1', 'wall-1x2', 'urns', 'haycart')
    FLAGS = ('blocks', 'blocks_when_destroyed', 'explosive', 'cover_levels', 'footprint', 'states')

    @classmethod
    def setUpClass(cls):
        cls.list = assets_of('destructibles')
        cls.assets = {a['id']: a for a in cls.list}

    def test_ids_are_unique_and_each_piece_has_its_states_and_its_strip(self):
        self.assertEqual(len(self.list), len(self.assets))
        self.assertEqual(sorted(self.assets), sorted(list(self.PIECES) + [p + '-destroy' for p in self.PIECES]))
        for a in self.list:
            self.assertEqual((a['category'], a['folder'], a['place']), ('Destructibles', 'destructibles', 'ground'), a['id'])

    def test_the_three_states_are_intact_damaged_and_destroyed(self):
        for pid in self.PIECES:
            a = self.assets[pid]
            self.assertEqual((a['kind'], a['names'], a['states'], len(a['frames'])), ('variants', ['Intact', 'Damaged', 'Destroyed'], ['intact', 'damaged', 'destroyed'], 3), pid)
            self.assertEqual(len({tuple(f) for f in a['frames']}), 3, f'{pid}: two states are the same picture')

    def test_the_destruction_strip_is_six_frames_at_twelve_a_second(self):
        for pid in self.PIECES:
            a = self.assets[pid + '-destroy']
            self.assertEqual((a['kind'], len(a['frames']), a['fps'], a['cols'], a['rows']), ('animation', 6, 12, 6, 1), pid)
            self.assertEqual(len({tuple(f) for f in a['frames']}), 6, f'{pid}: a frame repeats')

    def test_a_piece_its_states_and_its_strip_swap_in_place(self):
        for pid in self.PIECES:
            a, s = self.assets[pid], self.assets[pid + '-destroy']
            for key in ('w', 'h', 'anchor', 'footprint'):
                self.assertEqual(a[key], s[key], f'{pid}: {key}')
            for f in a['frames'] + s['frames']:
                self.assertEqual((len(f[0]), len(f)), (a['w'], a['h']), pid)
            fx, fy = a['footprint']['size']
            self.assertEqual(a['anchor']['x'], a['w'] // 2, pid)
            self.assertGreaterEqual(a['w'], 16 * (fx + fy), pid)
            for f in a['frames']:
                self.assertGreaterEqual(lowest(f), a['anchor']['y'] - 2, pid)
                self.assertLess(lowest(f), a['h'], pid)

    def test_the_strip_starts_on_the_intact_piece_and_ends_on_the_wreck(self):
        for pid in self.PIECES:
            states, strip = self.assets[pid]['frames'], self.assets[pid + '-destroy']['frames']
            intact, destroyed = mask(states[0]), mask(states[2])
            self.assertLessEqual(len(intact - mask(strip[0])), 0.02 * len(intact), f'{pid}: the first frame does not cover the intact piece')
            self.assertLessEqual(len(mask(strip[0]) ^ intact), 0.4 * len(intact), f'{pid}: the first frame is not the intact piece lit up')
            self.assertLessEqual(len(mask(strip[-1]) ^ destroyed), 0.2 * len(destroyed), f'{pid}: the last frame is not the wreck')
            self.assertLessEqual(differing(strip[-1], states[2]), 0.3 * len(destroyed), f'{pid}: the last frame does not match the destroyed state')
            peak = max(len(mask(f)) for f in strip[1:5])
            self.assertGreater(peak, len(destroyed), f'{pid}: the middle of the strip shows nothing breaking')

    def test_the_wreck_is_lower_than_the_piece(self):
        for pid in self.PIECES:
            states = self.assets[pid]['frames']
            top = lambda rows: min(y for y, r in enumerate(rows) if r.strip('.'))
            self.assertGreater(top(states[2]), top(states[0]), pid)
            self.assertLess(len(mask(states[2])), len(mask(states[0])), pid)

    def test_every_piece_says_what_it_is_for_the_game(self):
        for a in self.list:
            for key in self.FLAGS:
                self.assertIn(key, a, f'{a["id"]}: {key}')
            self.assertIsInstance(a['blocks'], bool, a['id'])
            self.assertIsInstance(a['blocks_when_destroyed'], bool, a['id'])
            self.assertIsInstance(a['explosive'], bool, a['id'])
            self.assertGreater(a['cover_levels'], 0, a['id'])
            self.assertFalse(a['walkable'], a['id'])
            self.assertTrue(a['blocks'], f'{a["id"]}: a piece blocks while it stands')
            self.assertFalse(a['blocks_when_destroyed'], f'{a["id"]}: the wreck is walked over')

    def test_only_the_explosive_barrel_is_explosive(self):
        for a in self.list:
            self.assertEqual(a['explosive'], a['id'].startswith('barrel-explosive'), a['id'])

    def test_the_strip_has_the_flags_of_its_piece(self):
        for pid in self.PIECES:
            a, s = self.assets[pid], self.assets[pid + '-destroy']
            for key in self.FLAGS:
                self.assertEqual(a[key], s[key], f'{pid}: {key}')

    def test_cover_is_in_levels_and_sensible(self):
        cover = {pid: self.assets[pid]['cover_levels'] for pid in self.PIECES}
        for pid, c in cover.items():
            self.assertTrue(0.3 <= c <= 2.0, pid)
        self.assertGreater(cover['barrel-stack'], cover['barrel-explosive'])             # a stack is higher than a barrel
        self.assertLess(cover['urns'], 0.5)                                              # a cluster of urns is no cover
        self.assertGreaterEqual(cover['wall-1x1'], 1.0)                                  # a wall is a full level

    def test_the_footprints_are_the_ones_promised(self):
        sizes = {pid: self.assets[pid]['footprint']['size'] for pid in self.PIECES}
        self.assertEqual(sizes, {'barricade-1x1': [1, 1], 'barricade-1x2': [1, 2], 'barrel-explosive': [1, 1], 'barrel-stack': [1, 1], 'wall-1x1': [1, 1], 'wall-1x2': [1, 2],
                                 'urns': [1, 1], 'haycart': [2, 1]})
        for pid in self.PIECES:
            fx, fy = sizes[pid]
            self.assertEqual({tuple(c) for c in self.assets[pid]['footprint']['cells']}, {(i, j) for i in range(fx) for j in range(fy)}, pid)

    def test_the_explosion_is_fire_and_the_rest_is_dust(self):
        def count(pid, roles):
            return sum(ch in roles for f in self.assets[pid + '-destroy']['frames'][1:4] for row in f for ch in row)
        self.assertGreater(count('barrel-explosive', 'dbtac'), 2 * count('wall-1x1', 'dbtac'))

    def test_the_package_lists_every_piece(self):
        import make_destructibles as m
        with tempfile.TemporaryDirectory() as tmp:
            m.write_package(tmp)
            names = [p.name for p in Path(tmp).iterdir()]
            self.assertEqual(names, ['destructibles.json'])
            pkg = json.loads((Path(tmp) / 'destructibles.json').read_text())
        text = json.dumps(pkg)
        for pid in self.PIECES:
            self.assertIn(pid, text)

    def test_it_is_the_same_every_time(self):
        import make_destructibles as m
        self.assertEqual([a['frames'] for a in m.build_assets()], [a['frames'] for a in self.list])


if __name__ == '__main__':
    unittest.main()
