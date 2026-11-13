"""Tests for the bridges (stone arch, broken, plank and corrupted) and the stairs and ramps that carry a unit up to a ledge.

    python3 -m unittest discover -s tools -p 'test_bridges.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildcache import assets_of  # noqa: E402
import extract_poses as ep  # noqa: E402
import make_rocks as mr  # noqa: E402
import voxelkit as vk  # noqa: E402

PALETTE = {c for c, *_ in ep.ROLES}


def bare_edges(a, allowed='.OzA'):
    """The painted pixels with an empty pixel beside them that are not an outline (or moss, which may sit over it)."""
    rows = a['frames'][0]
    h, w = len(rows), len(rows[0])
    out = []
    for y in range(h):
        for x in range(w):
            if rows[y][x] in allowed:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and rows[ny][nx] == '.':
                    out.append((x, y))
                    break
    return out


def lowest_row(a):
    return max(y for y, r in enumerate(a['frames'][0]) if r.strip('.'))


def contiguous_run(cells, axis):
    """Whether the cells are one unbroken line along the axis (0 for x, 1 for y), starting at 0."""
    along = sorted(c[axis] for c in cells)
    other = {c[1 - axis] for c in cells}
    return along == list(range(len(along))) and other == {0}


class Bridges(unittest.TestCase):
    """The bridges: 3 or 5 cells long, along x or y, deck exactly one level up, walkable when every cell has enough deck."""

    NAMES = ('arch', 'plank', 'corrupt')

    def assets(self):
        return {a['id']: a for a in assets_of('bridges')}

    def test_the_pieces_are_the_ones_promised(self):
        want = {f'bridge-{k}-{n}x1' for k in self.NAMES for n in (3, 5)} | {f'bridge-{k}-1x{n}' for k in self.NAMES for n in (3, 5)}
        want |= {'bridge-broken-5x1', 'bridge-broken-1x5'}
        self.assertEqual(set(self.assets()), want)
        self.assertEqual(len(assets_of('bridges')), len(want))              # no id twice

    def test_each_is_a_ground_still_in_the_bridges_category(self):
        for a in self.assets().values():
            self.assertEqual((a['category'], a['kind'], a['place'], a['folder'], len(a['frames'])), ('Bridges', 'still', 'ground', 'bridges', 1), a['id'])
            self.assertNotEqual(a['id'], 'bridge')                         # the older bridge is not touched

    def test_the_footprint_is_a_straight_run_along_the_axis_the_name_says(self):
        for a in self.assets().values():
            fx, fy = a['footprint']['size']
            cells = [tuple(c) for c in a['footprint']['cells']]
            n = max(fx, fy)
            self.assertIn(n, (3, 5), a['id'])
            self.assertEqual(len(cells), n, a['id'])
            if a['id'].endswith(f'-{n}x1'):
                self.assertEqual((a['run'], (fx, fy)), ('x', (n, 1)), a['id'])
                self.assertTrue(contiguous_run(cells, 0), a['id'])
            else:
                self.assertTrue(a['id'].endswith(f'-1x{n}'), a['id'])
                self.assertEqual((a['run'], (fx, fy)), ('y', (1, n)), a['id'])
                self.assertTrue(contiguous_run(cells, 1), a['id'])

    def test_the_picture_is_sized_to_its_footprint_and_anchored_in_the_middle(self):
        for a in self.assets().values():
            fx, fy = a['footprint']['size']
            self.assertEqual(a['w'], 16 * (fx + fy) + 2 * vk.MARGIN, a['id'])
            self.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (a['w'], a['h']), a['id'])
            front = max(i + j + 2 for i, j in a['footprint']['cells'])
            self.assertGreaterEqual(lowest_row(a), a['anchor']['y'] + 8 * front - 4 * (fx + fy) - 7, a['id'])      # it stands on the ground diamond of its lowest cell
            self.assertLess(lowest_row(a), a['h'], a['id'])

    def test_the_deck_is_exactly_one_level_up(self):
        import make_bridges as mb
        self.assertEqual(mb.DK, 16)
        for a in self.assets().values():
            self.assertEqual(a['levels'], 1, a['id'])
            self.assertEqual(mb.DK, 16 * a['levels'], a['id'])
        # a taller picture is not a taller deck: the deck's own level is the same in every bridge, and the tallest part is the parapet and posts
        self.assertEqual(self.assets()['bridge-arch-3x1']['h'] - self.assets()['bridge-arch-3x1']['anchor']['y'],
                         self.assets()['bridge-arch-1x3']['h'] - self.assets()['bridge-arch-1x3']['anchor']['y'])

    def test_a_bridge_is_walkable_when_every_cell_has_enough_deck(self):
        for a in self.assets().values():
            cells = {tuple(c) for c in a['footprint']['cells']}
            self.assertEqual({tuple(int(v) for v in k.split(',')) for k in a['top_cover']}, cells, a['id'])
            for v in a['top_cover'].values():
                self.assertTrue(0.0 <= v <= 1.0, a['id'])
            solid = {tuple(int(v) for v in k.split(',')) for k, v in a['top_cover'].items() if v >= mr.WALK_MIN}
            self.assertEqual({tuple(c) for c in a['walkable_cells']}, solid, a['id'])           # walkable_cells is exactly the cells at or over the threshold
            self.assertEqual(a['walkable'], solid == cells, a['id'])

    def test_every_whole_bridge_is_walkable_but_the_broken_ones(self):
        for a in self.assets().values():
            if 'broken' in a['id']:
                self.assertFalse(a['walkable'], a['id'])
            else:
                self.assertTrue(a['walkable'], a['id'])
                self.assertGreaterEqual(min(a['top_cover'].values()), mr.WALK_MIN, a['id'])
                self.assertEqual(len(a['walkable_cells']), len(a['footprint']['cells']), a['id'])

    def test_a_broken_bridge_has_two_walkable_ends_and_an_open_gap(self):
        for id in ('bridge-broken-5x1', 'bridge-broken-1x5'):
            a = self.assets()[id]
            axis = 0 if a['run'] == 'x' else 1
            walk = sorted(c[axis] for c in a['walkable_cells'])
            self.assertEqual(walk, [0, 1, 3, 4], id)                                          # the middle cell is the gap
            self.assertLess(a['top_cover']['2,0' if axis == 0 else '0,2'], 0.3, id)
            self.assertGreaterEqual(min(v for k, v in a['top_cover'].items() if k not in ('2,0', '0,2')), mr.WALK_MIN, id)
            self.assertNotEqual(a['frames'][0], self.assets()[id.replace('broken', 'arch')]['frames'][0], id)

    def test_the_bridge_along_x_and_along_y_are_one_bridge_turned(self):
        for kind in ('arch', 'plank', 'corrupt'):
            for n in (3, 5):
                ax, ay = self.assets()[f'bridge-{kind}-{n}x1'], self.assets()[f'bridge-{kind}-1x{n}']
                self.assertEqual((ax['w'], ax['h'], ax['anchor']), (ay['w'], ay['h'], ay['anchor']), (kind, n))
                self.assertEqual(list(ax['top_cover'].values()), list(ay['top_cover'].values()), (kind, n))
                self.assertNotEqual(ax['frames'][0], ay['frames'][0], (kind, n))                # drawn, not just copied
        for n in (5,):
            ax, ay = self.assets()['bridge-broken-5x1'], self.assets()['bridge-broken-1x5']
            self.assertEqual(list(ax['top_cover'].values()), list(ay['top_cover'].values()))

    def test_every_bridge_is_outlined_and_on_the_palette(self):
        for a in self.assets().values():
            self.assertEqual(bare_edges(a), [], a['id'])
            self.assertLessEqual({c for r in a['frames'][0] for c in r} - {'.'}, PALETTE, a['id'])

    def test_the_kinds_look_different_and_the_corrupted_one_has_its_own_colours(self):
        a = self.assets()
        pics = {tuple(x['frames'][0]) for x in a.values()}
        self.assertEqual(len(pics), len(a))
        palette = lambda id: {c for r in a[id]['frames'][0] for c in r} - {'.', 'O'}
        self.assertTrue(palette('bridge-corrupt-3x1') - palette('bridge-arch-3x1'))             # colours the stone one does not use (the plum, the mushrooms)
        self.assertTrue(palette('bridge-plank-3x1') - palette('bridge-arch-3x1'))               # and the timber

    def test_it_is_the_same_every_time(self):
        import make_bridges as mb
        self.assertEqual([x['frames'] for x in mb.build_assets()], [x['frames'] for x in mb.build_assets()])

    def test_the_package_lists_every_bridge(self):
        import json
        import tempfile
        import make_bridges as mb
        with tempfile.TemporaryDirectory() as d:
            mb.write_package(d)
            pack = json.loads((Path(d) / 'bridges.json').read_text())
        self.assertEqual(set(pack['bridges']), set(self.assets()))
        self.assertEqual((pack['deck_levels'], pack['walk_min']), (1, mr.WALK_MIN))
        for id, p in pack['bridges'].items():
            self.assertEqual(p['walkable'], self.assets()[id]['walkable'], id)
            self.assertEqual(p['walkable_cells'], self.assets()[id]['walkable_cells'], id)
            self.assertEqual(p['file'], f'{id}.png', id)


class StairsAndRamps(unittest.TestCase):
    """The stairs and ramps: one or two levels up, rising toward each of four sides, ending flush with a ledge of that height, all of it walkable."""

    KINDS = ('stair', 'ramp', 'ledge-ramp')
    DIRS = ('se', 'nw', 'sw', 'ne')

    def assets(self):
        return {a['id']: a for a in assets_of('stairs')}

    @staticmethod
    def name(kind, lv, d):
        return f'stair-h{lv}-{d}' if kind == 'stair' else f'stair-{kind}-h{lv}-{d}'

    def test_the_pieces_are_the_ones_promised(self):
        want = {self.name(k, lv, d) for k in self.KINDS for lv in (1, 2) for d in self.DIRS}
        self.assertEqual(set(self.assets()), want)
        self.assertEqual(len(assets_of('stairs')), len(want))              # no id twice, and none of the two old stair cubes' ids

    def test_each_is_a_ground_still_in_the_stairs_category(self):
        for a in self.assets().values():
            self.assertEqual((a['category'], a['kind'], a['place'], a['folder'], len(a['frames'])), ('Stairs', 'still', 'ground', 'stairs', 1), a['id'])
            self.assertFalse(a['id'].startswith('ground-'), a['id'])       # the ground sheet's own stairs are not touched

    def test_the_connector_says_what_the_name_says(self):
        for kind in self.KINDS:
            for lv in (1, 2):
                for d in self.DIRS:
                    a = self.assets()[self.name(kind, lv, d)]
                    c = a['connector']
                    self.assertEqual((c['kind'], c['up'], c['rise_levels'], a['levels']), (kind, d, lv, lv), a['id'])
                    if kind == 'ledge-ramp':
                        self.assertEqual((c['run_cells'], c['flat_cells']), (lv, 1), a['id'])      # a ramp one cell per level, then a ledge cell
                    else:
                        self.assertEqual((c['run_cells'], c['flat_cells']), (2 if lv == 1 else 3, 0), a['id'])

    def test_the_footprint_is_the_run_plus_the_flat_cell_along_the_way_up(self):
        for a in self.assets().values():
            c = a['connector']
            total = c['run_cells'] + c['flat_cells']
            fx, fy = a['footprint']['size']
            cells = [tuple(x) for x in a['footprint']['cells']]
            self.assertEqual(len(cells), total, a['id'])
            if c['up'] in ('se', 'nw'):                                     # up along x
                self.assertEqual((fx, fy), (total, 1), a['id'])
                self.assertTrue(contiguous_run(cells, 0), a['id'])
            else:                                                           # up along y
                self.assertEqual((fx, fy), (1, total), a['id'])
                self.assertTrue(contiguous_run(cells, 1), a['id'])

    def test_the_picture_is_sized_to_its_footprint_and_anchored_in_the_middle(self):
        for a in self.assets().values():
            fx, fy = a['footprint']['size']
            self.assertEqual(a['w'], 16 * (fx + fy) + 2 * vk.MARGIN, a['id'])
            self.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (a['w'], a['h']), a['id'])
            front = max(i + j + 2 for i, j in a['footprint']['cells'])
            self.assertGreaterEqual(lowest_row(a), a['anchor']['y'] + 8 * front - 4 * (fx + fy) - 7, a['id'])

    def test_every_stair_and_ramp_is_walkable_over_the_whole_footprint(self):
        for a in self.assets().values():
            cells = {tuple(c) for c in a['footprint']['cells']}
            self.assertTrue(a['walkable'], a['id'])
            self.assertEqual({tuple(int(v) for v in k.split(',')) for k in a['top_cover']}, cells, a['id'])
            self.assertGreaterEqual(min(a['top_cover'].values()), mr.WALK_MIN, a['id'])
            self.assertIn(a['levels'], (1, 2), a['id'])                      # whole levels, so it lines up with the ledges

    def test_the_high_end_is_the_height_of_a_ledge_the_rocks_have(self):
        ledges = {a['id']: a for a in assets_of('rocks')}
        for a in self.assets().values():
            lv = a['connector']['rise_levels']
            ledge = ledges.get(f'rock-ledge-1x1-h{lv}')
            self.assertIsNotNone(ledge, a['id'])
            self.assertTrue(ledge['walkable'], a['id'])
            self.assertEqual(ledge['levels'], lv, a['id'])                   # the stairs end flush with a ledge of that many levels

    def test_the_picture_rises_the_right_height_toward_the_right_side(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            top = min(y for y, r in enumerate(rows) if r.strip('.'))
            c = a['connector']
            fx, fy = a['footprint']['size']
            total = fx + fy - 1
            sign = 1 if c['up'] in ('se', 'sw') else -1
            # the top of the high cell sits a level's worth of pixels above where the ground would be at that end (within half a level, since a slope's top is not a flat diamond)
            expected = a['anchor']['y'] + sign * 4 * (total - 1) - 16 * a['levels'] - 8
            self.assertLessEqual(abs(top - expected), 8, a['id'])
            xs = [x for y in range(top, top + 3) for x, ch in enumerate(rows[y]) if ch != '.']
            mean = sum(xs) / len(xs) - a['anchor']['x']
            # up toward se or ne is up to the right of the picture, toward nw or sw up to the left
            self.assertTrue(mean > 0 if c['up'] in ('se', 'ne') else mean < 0, (a['id'], mean))

    def test_two_levels_rise_higher_than_one(self):
        for kind in self.KINDS:
            for d in self.DIRS:
                one, two = self.assets()[self.name(kind, 1, d)], self.assets()[self.name(kind, 2, d)]
                self.assertGreater(two['h'] - two['anchor']['y'], one['h'] - one['anchor']['y'] - 1, (kind, d))
                self.assertGreater(two['h'], one['h'], (kind, d))

    def test_a_step_is_four_pixels_and_a_ramp_has_no_steps(self):
        import make_stairs as ms
        self.assertEqual(ms.STEP, 4)
        for lv in (1, 2):
            total = 2 if lv == 1 else 3
            stairs = ms.heights('stair', lv, total)
            self.assertEqual(sorted(set(stairs)), [4 * i for i in range(1, 4 * lv + 1)])          # 4 steps a level, each 4 pixels high
            self.assertEqual(stairs[-1], 16 * lv)                                                 # the last step is the full height
            ramp = ms.heights('ramp', lv, total)
            self.assertEqual(ramp[-1], 16 * lv)
            self.assertEqual(ramp, sorted(ramp))
            self.assertGreater(len(set(ramp)), len(set(stairs)))                                  # a slope has finer heights than the steps
            ledge = ms.heights('ledge-ramp', lv, lv + 1)
            self.assertEqual(ledge[-vk.PX:], [16 * lv] * vk.PX)                                   # the ledge cell is flat at the full height

    def test_every_picture_is_outlined_and_on_the_palette(self):
        for a in self.assets().values():
            self.assertEqual(bare_edges(a), [], a['id'])
            self.assertLessEqual({c for r in a['frames'][0] for c in r} - {'.'}, PALETTE, a['id'])

    def test_the_four_ways_up_and_the_three_kinds_all_differ(self):
        pics = {tuple(a['frames'][0]) for a in self.assets().values()}
        self.assertEqual(len(pics), len(self.assets()))

    def test_it_is_the_same_every_time(self):
        import make_stairs as ms
        self.assertEqual([x['frames'] for x in ms.build_assets()], [x['frames'] for x in ms.build_assets()])

    def test_the_package_lists_every_piece(self):
        import json
        import tempfile
        import make_stairs as ms
        with tempfile.TemporaryDirectory() as d:
            ms.write_package(d)
            pack = json.loads((Path(d) / 'stairs.json').read_text())
        self.assertEqual(set(pack['pieces']), set(self.assets()))
        self.assertEqual((pack['step'], pack['walk_min']), (4, mr.WALK_MIN))
        for id, p in pack['pieces'].items():
            c = self.assets()[id]['connector']
            self.assertEqual((p['up'], p['rise_levels'], p['run_cells'], p['flat_cells']), (c['up'], c['rise_levels'], c['run_cells'], c['flat_cells']), id)
            self.assertEqual(p['file'], f'{id}.png', id)


if __name__ == '__main__':
    unittest.main()
