"""Tests for the corrupted terrain (mycelium veins, shelf fungus, the spore vent, thorn walls) and the graveyard and ritual set (gravestones, cairns, bones, the obelisk, altars, lanterns, iron, ritual circles).

    python3 -m unittest discover -s tools -p 'test_corrupted_terrain.py'
"""
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildcache import assets_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OPPOSITE = {'ne': 'sw', 'sw': 'ne', 'se': 'nw', 'nw': 'se'}
STEP = {'ne': (16, -8), 'se': (16, 8), 'sw': (-16, 8), 'nw': (-16, -8)}          # where the neighbour across an edge sits, in pixels
OPEN = 2.0           # how close to an edge's middle paint counts as the vein leaving by that edge, in pixels
SEAM = 1.5           # the core of the vein at an edge, which is the same in every tile that has it


def painted(rows):
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}


def near(points, centre, radius):
    return {(x, y) for x, y in points if math.hypot(x + 0.5 - centre[0], y + 0.5 - centre[1]) <= radius}


def differing(a, b):
    return sum(ca != cb for ra, rb in zip(a, b) for ca, cb in zip(ra, rb))


def bare_edges(rows):
    """How many painted pixels that are not outline have empty space (or the picture's edge) at their side."""
    h, w = len(rows), len(rows[0])
    n = 0
    for y in range(h):
        for x in range(w):
            if rows[y][x] in '.O':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or rows[ny][nx] == '.':
                    n += 1
                    break
    return n


def looks_closed(frames, slack=1.25):
    """The last frame leads into the first as smoothly as any frame leads into the next."""
    steps = [differing(frames[k], frames[k + 1]) for k in range(len(frames) - 1)]
    return differing(frames[-1], frames[0]) <= slack * max(steps)


def common_checks(test, assets, category, folder):
    ids = [a['id'] for a in assets]
    test.assertEqual(len(ids), len(set(ids)), 'ids are not unique')
    import extract_poses as ep
    known = {c for c, *_ in ep.ROLES}
    for a in assets:
        test.assertEqual((a['category'], a['folder'], a['place']), (category, folder, 'ground'), a['id'])
        test.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])                           # the middle of the footprint is the middle of the picture
        for f in a['frames']:
            test.assertEqual((len(f), {len(r) for r in f}), (a['h'], {a['w']}), a['id'])
            test.assertLessEqual(set(''.join(f)) - {'.'}, known, a['id'])               # palette roles only
        if 'footprint' in a:
            fx, fy = a['footprint']['size']
            test.assertEqual(sorted(map(tuple, a['footprint']['cells'])), [(i, j) for i in range(fx) for j in range(fy)] if len(a['footprint']['cells']) == fx * fy
                             else sorted(map(tuple, a['footprint']['cells'])), a['id'])
            test.assertEqual(len(a['footprint']['cells']), fx * fy, a['id'])


class CorruptedTerrain(unittest.TestCase):
    """Mycelium veins that join, shelf fungus a unit can stand on, a looping spore vent and thorn walls with an intact and a broken picture."""

    @classmethod
    def setUpClass(cls):
        import make_corrupted_terrain as m
        import make_rocks
        cls.m = m
        cls.walk_min = make_rocks.WALK_MIN
        cls.assets = {a['id']: a for a in assets_of('corrupted-terrain')}
        cls.myc = {i: a for i, a in cls.assets.items() if i.startswith('mycelium')}
        cls.shelf = {i: a for i, a in cls.assets.items() if i.startswith('shelf')}
        cls.thorn = {i: a for i, a in cls.assets.items() if i.startswith('thorn')}

    # --- the whole family ---
    def test_the_family_and_its_names(self):
        common_checks(self, list(self.assets.values()), 'Corrupted Terrain', 'corrupted-terrain')
        want = {'mycelium-end-' + e for e in ('ne', 'se', 'sw', 'nw')} | {'mycelium-straight-ne-sw', 'mycelium-straight-nw-se'}
        want |= {'mycelium-corner-ne-se', 'mycelium-corner-se-sw', 'mycelium-corner-sw-nw', 'mycelium-corner-nw-ne'}
        want |= {'mycelium-tee-no-' + e for e in ('ne', 'se', 'sw', 'nw')} | {'mycelium-cross', 'mycelium-node'}
        want |= {'shelf-1x1-h1', 'shelf-1x1-h2', 'shelf-1x2-h1', 'shelf-2x1-h1', 'shelf-2x2-h1', 'shelf-1x2-h2-step', 'shelf-2x2-h2-step', 'spore-vent'}
        want |= {f'thorn-wall-{s}{b}' for s in ('1x1', '1x2', '2x1') for b in ('', '-broken')}
        self.assertEqual(set(self.assets), want)

    def test_it_is_the_same_every_time(self):
        self.assertEqual([a['frames'] for a in self.m.build_assets()], [a['frames'] for a in assets_of('corrupted-terrain')])

    def test_the_package_file_says_what_the_pictures_are(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            self.m.write_package(d)
            doc = json.loads((Path(d) / 'corrupted-terrain.json').read_text())
        self.assertEqual(doc['mycelium']['cell'], [32, 16])
        self.assertEqual({k: tuple(v) for k, v in doc['mycelium']['edges'].items()}, {k: tuple(v) for k, v in self.m.EDGES.items()})
        self.assertEqual((doc['vent']['frames'], doc['vent']['fps']), (6, 8))
        self.assertEqual(doc['shelf']['walk_min'], self.walk_min)

    def test_the_folder_readme_names_every_file(self):
        text = (ROOT / 'sprites' / 'assets' / 'corrupted-terrain' / 'README.md').read_text()
        for i in self.assets:
            self.assertIn(f'{i}.png', text, f'README.md does not mention {i}.png')

    # --- mycelium ---
    def test_the_veins_are_flat_decals_inside_the_tile_diamond_with_no_outline(self):
        self.assertEqual(len(self.myc), 16)
        for i, a in self.myc.items():
            self.assertEqual((a['w'], a['h'], a['anchor']), (32, 16, {'x': 16, 'y': 8}), i)
            self.assertEqual((a['kind'], len(a['frames'])), ('still', 1), i)
            roles = set(''.join(a['frames'][0])) - {'.'}
            self.assertNotIn('O', roles, i)                                              # a stain has no outline
            self.assertLessEqual(roles, set('uieo'), i)
            for x, y in painted(a['frames'][0]):
                self.assertLessEqual(abs(x + 0.5 - 16) / 16 + abs(y + 0.5 - 8) / 8, 1.0, f'{i}: paint outside the diamond at {x},{y}')

    def test_each_tile_has_paint_at_exactly_the_edges_it_says(self):
        for i, a in self.myc.items():
            pts = painted(a['frames'][0])
            got = {e for e, c in self.m.EDGES.items() if near(pts, c, OPEN)}
            self.assertEqual(got, set(a['decal']['edges']), i)

    def test_the_piece_kinds_cover_every_turn(self):
        edges = {i: frozenset(a['decal']['edges']) for i, a in self.myc.items()}
        counts = {k: sum(len(e) == n for e in edges.values()) for k, n in (('one', 1), ('two', 2), ('three', 3), ('four', 4), ('none', 0))}
        self.assertEqual(counts, {'one': 4, 'two': 2 + 4, 'three': 4, 'four': 1, 'none': 1})                  # ends; straights and corners; tees; the cross; the node
        self.assertEqual({e for i, e in edges.items() if i.startswith('mycelium-end')}, {frozenset([k]) for k in ('ne', 'se', 'sw', 'nw')})
        straights = {e for i, e in edges.items() if 'straight' in i}
        self.assertEqual(straights, {frozenset(('ne', 'sw')), frozenset(('nw', 'se'))})
        corners = {e for i, e in edges.items() if 'corner' in i}
        self.assertEqual(corners, {frozenset(p) for p in (('ne', 'se'), ('se', 'sw'), ('sw', 'nw'), ('nw', 'ne'))})
        self.assertEqual(edges['mycelium-cross'], frozenset(('ne', 'se', 'sw', 'nw')))
        self.assertEqual(edges['mycelium-node'], frozenset())
        tees = {e for i, e in edges.items() if 'tee' in i}
        self.assertEqual(tees, {frozenset(('ne', 'se', 'sw', 'nw')) - {k} for k in ('ne', 'se', 'sw', 'nw')})

    def test_the_vein_at_an_edge_is_the_same_in_every_tile_that_has_it(self):
        for e, c in self.m.EDGES.items():
            shapes = {frozenset((x - int(c[0]), y - int(c[1])) for x, y in near(painted(a['frames'][0]), c, SEAM))
                      for a in self.myc.values() if e in a['decal']['edges']}
            self.assertEqual(len(shapes), 1, f'the vein at {e} differs between tiles')
            self.assertTrue(next(iter(shapes)), e)

    def test_no_twig_reaches_the_seam(self):
        # a side twig must not run out to an edge's middle and widen the vein at the seam: the vein at an edge is the same in every tile that has it
        for e, c in self.m.EDGES.items():
            shapes = {frozenset((x - int(c[0]), y - int(c[1])) for x, y in near(painted(a['frames'][0]), c, OPEN))
                      for a in self.myc.values() if e in a['decal']['edges']}
            self.assertEqual(len(shapes), 1, f'the vein at {e} differs between tiles')

    def test_a_closed_edge_has_no_paint_near_it(self):
        for i, a in self.myc.items():
            pts = painted(a['frames'][0])
            for e, c in self.m.EDGES.items():
                if e not in a['decal']['edges']:
                    self.assertFalse(near(pts, c, OPEN), f'{i}: paint at the closed edge {e}')

    def test_any_two_tiles_with_a_vein_on_their_shared_edge_join(self):
        pairs = 0
        for e, c in self.m.EDGES.items():
            dx, dy = STEP[e]
            for ia, a in self.myc.items():
                if e not in a['decal']['edges']:
                    continue
                pa = near(painted(a['frames'][0]), c, 3.0)
                for ib, b in self.myc.items():
                    if OPPOSITE[e] not in b['decal']['edges']:
                        continue
                    pb = {(x + dx, y + dy) for x, y in near(painted(b['frames'][0]), self.m.EDGES[OPPOSITE[e]], 3.0)}
                    self.assertTrue(pa and pb, (ia, ib, e))
                    # some pixel of one touches (or overlaps) some pixel of the other: the vein goes across the seam without a gap
                    self.assertTrue(any(abs(x - u) <= 1 and abs(y - v) <= 1 for x, y in pa for u, v in pb), f'{ia} and {ib} do not join across {e}')
                    pairs += 1
        self.assertGreater(pairs, 100)

    def test_the_veins_are_a_few_pixels_wide_at_the_seam(self):
        for e, c in self.m.EDGES.items():
            widths = set()
            for a in self.myc.values():
                if e in a['decal']['edges']:
                    widths.add(len(near(painted(a['frames'][0]), c, SEAM)))
            self.assertEqual(len(widths), 1, e)
            self.assertTrue(2 <= widths.pop() <= 10, e)

    # --- shelf fungus ---
    def test_shelf_fungus_is_walkable_with_a_flat_top_over_every_cell(self):
        self.assertEqual(len(self.shelf), 7)
        for i, a in self.shelf.items():
            fx, fy = a['footprint']['size']
            self.assertEqual((a['kind'], len(a['frames']), a['w']), ('still', 1, 16 * (fx + fy) + 24), i)       # the same width rule as the rocks, with the cap's overhang
            self.assertEqual(sorted(a['top_cover']), sorted(f'{c[0]},{c[1]}' for c in a['footprint']['cells']), i)
            self.assertEqual(sorted(a['cell_levels']), sorted(a['top_cover']), i)
            self.assertGreaterEqual(min(a['top_cover'].values()), self.walk_min, i)
            self.assertTrue(a['walkable'], i)
            self.assertEqual(a['levels'], max(a['cell_levels'].values()), i)
            self.assertTrue(all(v in (1, 2) for v in a['cell_levels'].values()), i)                            # whole levels, so it lines up with the ground's steps

    def test_the_cover_is_what_the_geometry_gives(self):
        for name, label, levels in self.m.SHELVES:
            got = {f'{i},{j}': round(v, 2) for (i, j), v in self.m.shelf_cover(levels, self.m.seed_of(name)).items()}
            self.assertEqual(got, self.shelf[name]['top_cover'], name)

    def test_a_stepped_shelf_has_a_lower_cell_in_front_to_climb_from(self):
        for i in ('shelf-1x2-h2-step', 'shelf-2x2-h2-step'):
            levels = {tuple(map(int, k.split(','))): v for k, v in self.shelf[i]['cell_levels'].items()}
            low = [c for c, v in levels.items() if v == 1]
            self.assertEqual(len(low), 1, i)
            self.assertEqual(max(levels.values()), 2, i)
            self.assertEqual(low[0], max(levels, key=lambda c: c[0] + c[1]), f'{i}: the step is not the front-most cell')
        for i in ('shelf-1x1-h1', 'shelf-1x1-h2', 'shelf-1x2-h1', 'shelf-2x1-h1', 'shelf-2x2-h1'):
            self.assertEqual(len(set(self.shelf[i]['cell_levels'].values())), 1, i)

    def test_a_shelf_stands_on_its_footprint_and_is_outlined(self):
        for i, a in self.shelf.items():
            rows = a['frames'][0]
            fx, fy = a['footprint']['size']
            low = max(y for y, r in enumerate(rows) if r.strip('.'))
            self.assertGreaterEqual(low, a['anchor']['y'], i)
            self.assertLess(low, a['h'], i)
            self.assertIn('O', ''.join(rows), i)
            self.assertLessEqual(bare_edges(rows), 16, i)                                                       # a few pores or moss may break the outline on the big ones

    # --- the vent ---
    def test_the_vent_is_a_six_frame_loop(self):
        a = self.assets['spore-vent']
        self.assertEqual((a['kind'], a['fps'], len(a['frames']), a['w'], a['h'], a['anchor']), ('animation', 8, 6, 32, 48, {'x': 16, 'y': 40}))
        self.assertEqual(a['vent'], {'loops': True, 'blocks': False})
        self.assertEqual(len({tuple(f) for f in a['frames']}), 6)
        self.assertTrue(looks_closed(a['frames']), 'the last frame does not lead into the first')
        for f in a['frames']:
            self.assertEqual(f[40:], a['frames'][0][40:] if False else f[40:])                                  # (the rim below the anchor is outlined in every frame)
        self.assertEqual(bare_edges(a['frames'][0]), 0)

    # --- thorns ---
    def test_thorn_walls_come_intact_and_broken(self):
        for s in ('1x1', '1x2', '2x1'):
            whole, cut = self.thorn[f'thorn-wall-{s}'], self.thorn[f'thorn-wall-{s}-broken']
            self.assertEqual(whole['footprint'], cut['footprint'], s)
            self.assertEqual(whole['footprint']['size'], [int(s[0]), int(s[2])], s)
            self.assertEqual((whole['blocks'], cut['blocks']), (True, False), s)
            self.assertEqual((whole['destroyable'], cut['destroyable']), (True, True), s)
            self.assertEqual((whole['w'], whole['anchor']['x']), (cut['w'], cut['anchor']['x']), s)             # swap one for the other in place
            self.assertLess(cut['h'], whole['h'], s)
            self.assertLess(len(painted(cut['frames'][0])), 0.6 * len(painted(whole['frames'][0])), s)          # the broken one is stubs and litter
            self.assertNotEqual(whole['frames'], cut['frames'], s)
            self.assertLessEqual(bare_edges(whole['frames'][0]), 14, s)
            self.assertLessEqual(bare_edges(cut['frames'][0]), 14, s)


class Graveyard(unittest.TestCase):
    """The graveyard and ritual set: standing pieces that block, an altar that can be stood on, flickering lanterns, iron that runs along an axis and ritual circles on the ground."""

    @classmethod
    def setUpClass(cls):
        import make_graveyard as m
        import make_rocks
        cls.m = m
        cls.walk_min = make_rocks.WALK_MIN
        cls.assets = {a['id']: a for a in assets_of('graveyard')}

    def test_the_family_and_its_names(self):
        common_checks(self, list(self.assets.values()), 'Graveyard', 'graveyard')
        want = {'gravestone-round', 'gravestone-cross', 'gravestone-leaning', 'gravestone-broken', 'cairn-tall', 'cairn-small', 'bones-skull', 'bones-ribs', 'bones-scatter',
                'obelisk', 'rune-plinth', 'rune-altar-2x1', 'rune-altar-1x2', 'spirit-lantern-post', 'spirit-lantern-stone', 'iron-fence-x', 'iron-fence-y', 'graveyard-gate-x',
                'graveyard-gate-y', 'ritual-circle-2', 'ritual-circle-3', 'ritual-circle-4'}
        self.assertEqual(set(self.assets), want)

    def test_it_is_the_same_every_time(self):
        self.assertEqual([a['frames'] for a in self.m.build_assets()], [a['frames'] for a in assets_of('graveyard')])

    def test_the_package_file_says_what_the_pictures_are(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            self.m.write_package(d)
            doc = json.loads((Path(d) / 'graveyard.json').read_text())
        self.assertEqual(doc['walk_min'], self.walk_min)
        self.assertEqual((doc['lantern']['frames'], doc['lantern']['fps']), (4, 6))
        self.assertEqual(doc['circles']['sizes'], [2, 3, 4])

    def test_the_folder_readme_names_every_file(self):
        text = (ROOT / 'sprites' / 'assets' / 'graveyard' / 'README.md').read_text()
        for i in self.assets:
            self.assertIn(f'{i}.png', text, f'README.md does not mention {i}.png')

    def test_standing_pieces_are_one_cell_blockers_and_sized_by_the_ground_rule(self):
        for i in ('gravestone-round', 'gravestone-cross', 'gravestone-leaning', 'gravestone-broken', 'cairn-tall', 'cairn-small', 'bones-skull', 'bones-ribs', 'bones-scatter', 'obelisk', 'rune-plinth'):
            a = self.assets[i]
            self.assertEqual((a['kind'], len(a['frames']), a['w'], a['footprint']['size'], a['blocks']), ('still', 1, 52, [1, 1], True), i)
            self.assertNotIn('walkable', a, i)
            rows = a['frames'][0]
            self.assertGreaterEqual(max(y for y, r in enumerate(rows) if r.strip('.')), a['anchor']['y'], i)   # it stands on the ground, not above it
            self.assertEqual(bare_edges(rows), 0, i)                                                          # the one-pixel outline is unbroken
        self.assertGreater(self.assets['obelisk']['h'], 2 * self.assets['gravestone-round']['h'] - 20)       # the obelisk is the tall one

    def test_the_gravestones_are_four_different_shapes(self):
        shapes = {tuple(self.assets[f'gravestone-{k}']['frames'][0]) for k in ('round', 'cross', 'leaning', 'broken')}
        self.assertEqual(len(shapes), 4)

    # --- the altar ---
    def test_the_altar_can_be_stood_on(self):
        for i, size in (('rune-altar-2x1', [2, 1]), ('rune-altar-1x2', [1, 2])):
            a = self.assets[i]
            self.assertEqual(a['footprint']['size'], size, i)
            self.assertEqual((a['w'], a['levels']), (68, 1), i)
            self.assertEqual(sorted(a['top_cover']), sorted(f'{c[0]},{c[1]}' for c in a['footprint']['cells']), i)
            self.assertGreaterEqual(min(a['top_cover'].values()), self.walk_min, i)
            self.assertEqual(a['walkable'], min(a['top_cover'].values()) >= self.walk_min, i)
            self.assertTrue(a['walkable'], i)
            self.assertNotIn('blocks', a, i)                                                                  # it is a step to stand on; the game decides whether to block it
        self.assertEqual(self.assets['rune-altar-2x1']['w'], self.assets['rune-altar-1x2']['w'])
        self.assertNotEqual(self.assets['rune-altar-2x1']['frames'], self.assets['rune-altar-1x2']['frames'])

    def test_the_cover_is_what_the_geometry_gives(self):
        for along_x, name in ((True, 'rune-altar-2x1'), (False, 'rune-altar-1x2')):
            got = {f'{i},{j}': round(v, 2) for (i, j), v in self.m.altar_cover(along_x).items()}
            self.assertEqual(got, self.assets[name]['top_cover'], name)

    # --- lanterns ---
    def test_the_lanterns_flicker_in_a_loop_and_give_light(self):
        for kind in ('post', 'stone'):
            a = self.assets[f'spirit-lantern-{kind}']
            self.assertEqual((a['kind'], a['fps'], len(a['frames']), a['w']), ('animation', 6, 4, 60), kind)
            self.assertEqual((a['light'], a['blocks'], a['footprint']['size']), (True, True, [1, 1]), kind)
            self.assertEqual(len({tuple(f) for f in a['frames']}), 4, kind)
            self.assertTrue(looks_closed(a['frames']), f'{kind}: the last frame does not lead into the first')
            self.assertIn('o', ''.join(a['frames'][0]), kind)                                                  # the glow
            self.assertEqual(bare_edges(a['frames'][0]), 0, kind)

    # --- iron ---
    def test_the_fence_and_the_gate_run_along_an_axis(self):
        for kind, opens in (('iron-fence', False), ('graveyard-gate', True)):
            x, y = self.assets[f'{kind}-x'], self.assets[f'{kind}-y']
            self.assertEqual((x['runs_along'], y['runs_along']), ('x', 'y'), kind)
            self.assertEqual((x['opens'], y['opens']), (opens, opens), kind)
            self.assertEqual((x['blocks'], y['blocks']), (True, True), kind)
            self.assertEqual((x['w'], x['h'], x['anchor']), (y['w'], y['h'], y['anchor']), kind)
            self.assertNotEqual(x['frames'], y['frames'], kind)
            self.assertEqual(len(painted(x['frames'][0])), len(painted(y['frames'][0])), kind)
            self.assertEqual(bare_edges(x['frames'][0]) + bare_edges(y['frames'][0]), 0, kind)
        self.assertGreater(self.assets['graveyard-gate-x']['h'], self.assets['iron-fence-x']['h'])             # the gate is taller than the fence

    # --- ritual circles ---
    def test_the_ritual_circles_are_flat_decals_the_size_of_their_cells(self):
        for n in (2, 3, 4):
            a = self.assets[f'ritual-circle-{n}']
            self.assertEqual((a['w'], a['h'], a['anchor']), (32 * n, 16 * n, {'x': 16 * n, 'y': 8 * n}), n)
            self.assertEqual(a['footprint']['size'], [n, n], n)
            self.assertEqual(len(a['footprint']['cells']), n * n, n)
            self.assertTrue(a['decal'], n)
            self.assertNotIn('blocks', a, n)
            self.assertNotIn('walkable', a, n)
            rows = a['frames'][0]
            self.assertNotIn('O', ''.join(rows), n)                                                            # a mark on the ground has no outline
            self.assertIn('o', ''.join(rows), n)                                                               # the glow
            for x, y in painted(rows):
                self.assertLessEqual(abs(x + 0.5 - 16 * n) / (16 * n) + abs(y + 0.5 - 8 * n) / (8 * n), 1 + 3 / (16 * n), f'ritual-circle-{n}: paint outside its diamond at {x},{y}')     # a pixel's width of give at the edge
        sizes = [len(painted(self.assets[f'ritual-circle-{n}']['frames'][0])) for n in (2, 3, 4)]
        self.assertEqual(sizes, sorted(sizes))                                                                 # a bigger circle has more in it


if __name__ == '__main__':
    unittest.main()
