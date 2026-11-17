"""The Overgrowth map: ground tiles that join, floors that follow their rules, pieces that stay on the land, flowers and routes in every state, and the README's recipe redrawing a floor."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions as cv  # noqa: E402
import extract_poses as ep  # noqa: E402
import make_overgrowth as og  # noqa: E402
from buildcache import assets_of  # noqa: E402

FOLDER = cv.ROOT / 'sprites' / 'assets' / 'overgrowth'
EMPTY = '.' * 16


class Assets(unittest.TestCase):
    def test_the_assets_are_grouped_named_and_sized(self):
        assets = assets_of('overgrowth')
        self.assertTrue(assets)
        for a in assets:
            self.assertEqual((a['category'], a['folder']), ('Overgrowth map', 'overgrowth'), a['id'])
            self.assertTrue(a['id'].startswith('overgrowth-'), a['id'])
            self.assertEqual(a['place'], 'none', a['id'])
            self.assertLessEqual(len(a['frames']), a['cols'] * a['rows'], a['id'])
            for rows in a['frames']:
                self.assertEqual((len(rows), {len(r) for r in rows}), (a['h'], {a['w']}), a['id'])
        ids = {a['id'] for a in assets}
        for kind, _ in og.FLOWER_KINDS:
            for state in og.STATES:
                self.assertIn(f'overgrowth-node-{kind}-{state}', ids)
        for need in ('overgrowth-ground', 'overgrowth-full', 'overgrowth-spill', 'overgrowth-void', 'overgrowth-path-default', 'overgrowth-path-off', 'overgrowth-path-used', 'overgrowth-tone-patch'):
            self.assertIn(need, ids)

    def test_no_asset_leaves_the_palette(self):
        known = {r[0] for r in ep.ROLES} | {'.'}
        for a in assets_of('overgrowth'):
            for rows in a['frames']:
                self.assertLessEqual(set(''.join(rows)), known, a['id'])


class Ground(unittest.TestCase):
    def test_the_ends_are_empty_and_full_and_every_shape_is_different(self):
        tiles = [og.ground_tile(b) for b in range(1, 15)]
        self.assertEqual(len({tuple(t) for t in tiles}), 14)
        self.assertNotIn('.', ''.join(og.ground_tile(15)))

    def test_tiles_side_by_side_agree_on_where_there_is_ground_along_the_edge_they_share(self):
        mask = lambda t, y, x: t[y][x] != '.'
        for a in range(16):
            for b in range(16):
                for sa in range(og.STYLES):
                    for sb in range(og.STYLES):
                        ta = og.ground_tile(a, 0, sa) if a else [EMPTY] * 16
                        tb = og.ground_tile(b, 0, sb) if b else [EMPTY] * 16
                        if (a >> 1) & 1 == b & 1 and (a >> 3) & 1 == (b >> 2) & 1:                 # a's right corners are b's left corners
                            self.assertEqual([mask(ta, y, 15) for y in range(16)], [mask(tb, y, 0) for y in range(16)], (a, b, sa, sb))

    def test_tiles_above_and_below_agree_on_the_land_along_their_edge(self):
        for a in range(16):
            for b in range(16):
                if (a >> 2) & 1 == b & 1 and (a >> 3) & 1 == (b >> 1) & 1:                         # a's bottom corners are b's top corners
                    self.assertEqual(og.land_grid(a)[15], og.land_grid(b)[0], (a, b))

    def test_every_cliff_style_ends_the_same_at_the_tile_sides(self):
        for x in (0, og.TILE - 1):
            self.assertEqual(len({og.column_depth(x, st) for st in range(og.STYLES)}), 1, x)
        self.assertGreater(len({tuple(og.column_depth(x, st) for x in range(16)) for st in range(og.STYLES)}), 3)

    def test_a_cliff_that_runs_past_the_bottom_of_its_tile_goes_on_in_the_spill_tile(self):
        self.assertNotEqual(set(''.join(og.spill_tile(12))), {'.'})                                 # land along the bottom: the whole cliff is below it
        painted = lambda b: sum(ch != '.' for ch in ''.join(og.spill_tile(b)))
        self.assertLess(painted(3), painted(12) / 2)                                                # land along the top: only the roots reach past the tile
        sheet = next(a for a in assets_of('overgrowth') if a['id'] == 'overgrowth-spill')['frames']
        for st in range(og.STYLES):
            for b in (0, 15):                                                                       # nothing below an empty tile, and a full one has land under it
                self.assertEqual(set(''.join(sheet[st * 16 + b])), {'.'})

    def test_the_full_variants_differ_only_in_the_middle(self):
        tiles = [og.ground_tile(15, v) for v in range(len(og.FULL_VARIANTS))]
        self.assertGreater(len({tuple(t) for t in tiles}), 3)
        ring = lambda t: [t[y][x] for y in range(16) for x in range(16) if min(x, y, 15 - x, 15 - y) < 3]
        for t in tiles[1:]:
            self.assertEqual(ring(t), ring(tiles[0]))


class Floors(unittest.TestCase):
    def setUp(self):
        self.floors = [og.generate(seed, preset) for preset in og.PRESETS for seed in (3, 7, 21)]

    def test_the_same_seed_makes_the_same_floor_and_another_makes_another(self):
        a, b = og.generate(7, 'climb'), og.generate(7, 'climb')
        self.assertEqual((a['kinds'], a['edges'], a['land']), (b['kinds'], b['edges'], b['land']))
        self.assertEqual(og.layout_json(a), og.layout_json(b))
        self.assertNotEqual(og.generate(8, 'climb')['land'], a['land'])

    def test_the_kinds_follow_the_rules(self):
        for f in self.floors:
            top = f['params']['floors'] - 1
            kinds = f['kinds']
            self.assertEqual([n for n, k in kinds.items() if k == 'boss'], [(top, f['params']['lanes'] // 2)])
            for (floor, lane), k in kinds.items():
                if floor == 0:
                    self.assertEqual(k, 'battle')
                if floor == top - 1:
                    self.assertEqual(k, 'rest')
                if floor < 2:
                    self.assertNotIn(k, ('elite', 'shop'))
                self.assertIn(k, [kk for kk, _ in og.FLOWER_KINDS])

    def test_every_node_leads_up_to_the_boss_and_stands_on_land_joined_to_the_rest(self):
        for f in self.floors:
            edges = f['edges']
            top = f['params']['floors'] - 1
            for node in f['centre']:
                at = {node}
                while at and not any(n[0] == top for n in at):
                    at = {b for a, b in edges if a in at}
                self.assertTrue(at, node)
            land = f['land']
            h, w = len(land), len(land[0])
            nodes = set(f['centre'].values())
            for (x, y) in nodes:
                self.assertTrue(land[y][x])
            seen, todo = set(), [next(iter(nodes))]
            while todo:
                x, y = todo.pop()
                if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not land[y][x]:
                    continue
                seen.add((x, y))
                todo += [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            self.assertLessEqual(nodes, seen)

    def test_the_water_is_kept_off_the_edge_of_the_map(self):
        for f in self.floors:
            land = f['land']
            self.assertFalse(any(land[0]) or any(land[-1]) or any(r[0] or r[-1] for r in land))

    def test_loose_pieces_never_hang_over_the_edge_of_an_island(self):
        for preset, seed in og.EXAMPLES:
            lay = og.generate(seed, preset)
            plan = og.build_plan(lay)
            spec = {s[0]: s for s in og.decor_assets_spec()}
            for pc in plan['placements']:
                if pc['layer'] not in ('tone', 'patch', 'decor'):
                    continue
                rows = spec[pc['id']][5][pc['frame']]
                ax, ay = spec[pc['id']][4]
                for y, row in enumerate(rows):
                    for x, ch in enumerate(row):
                        if ch != '.':
                            cx, cy = (pc['x'] - ax + x) // 16, (pc['y'] - ay + y) // 16
                            self.assertTrue(og.cell_at(lay['land'], cx, cy), (preset, pc))


class Flowers(unittest.TestCase):
    def test_every_kind_has_every_state_with_its_frames_and_the_click_plays_once(self):
        for kind, _ in og.FLOWER_KINDS:
            for state, info in og.STATES.items():
                frames = [og.flower(kind, f, state) for f in range(info['frames'])]
                size = 64 if kind == 'boss' else 48
                for w, h, (ax, ay), rows in frames:
                    self.assertEqual((w, h, len(rows), {len(r) for r in rows}), (size, size, size, {size}), (kind, state))
                    self.assertEqual((ax, ay), (size // 2, 50 if kind == 'boss' else 34))
                    painted = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
                    self.assertGreater(len(painted), 150, (kind, state))
                    self.assertTrue(all(1 <= x < size - 1 and 1 <= y < size - 1 for x, y in painted), (kind, state))
        self.assertFalse(og.STATES['click']['loop'])
        self.assertTrue(og.STATES['idle']['loop'] and og.STATES['hover']['loop'])

    def test_the_states_look_different_and_the_animations_move(self):
        for kind, _ in og.FLOWER_KINDS:
            idle = [tuple(og.flower(kind, f, 'idle')[3]) for f in range(4)]
            hover = [tuple(og.flower(kind, f, 'hover')[3]) for f in range(4)]
            click = [tuple(og.flower(kind, f, 'click')[3]) for f in range(6)]
            used = tuple(og.flower(kind, 0, 'used')[3])
            self.assertGreater(len(set(idle)), 1, kind)
            self.assertEqual(len(set(hover)), 4, kind)
            self.assertEqual(len(set(click)), 6, kind)
            self.assertFalse(set(idle) & set(hover), kind)
            self.assertNotIn(used, idle + hover + click, kind)

    def test_a_used_flower_is_faded_and_not_bright(self):
        bright = set('oEdbtjvr')
        for kind, _ in og.FLOWER_KINDS:
            if kind == 'event':
                continue
            idle = ''.join(og.flower(kind, 0, 'idle')[3])
            used = ''.join(og.flower(kind, 0, 'used')[3])
            self.assertLess(sum(ch in bright for ch in used), sum(ch in bright for ch in idle) / 2, kind)

    def test_each_flower_has_its_own_colour_ring(self):
        self.assertEqual(len(set(og.ACCENT.values())), len(og.FLOWER_KINDS))


class Paths(unittest.TestCase):
    def test_the_three_states_and_their_frames(self):
        run = [(5 + k, 5) for k in range(60)]
        default = [tuple(og.path_pixels(run, 'default', f)) for f in range(4)]
        used = [tuple(og.path_pixels(run, 'used', f)) for f in range(4)]
        off = tuple(og.path_pixels(run, 'off', 0))
        self.assertEqual((len(set(default)), len(set(used))), (4, 4))
        self.assertEqual(og.path_pixels(run, 'off', 3), list(off))
        self.assertEqual(len({tuple(sorted({(x, y) for x, y, _ in d})) for d in default}), 1)            # the dots do not move, the pulse does
        self.assertNotEqual({r for _, _, r in default[0]}, {r for _, _, r in off})
        for pixels in default + used + [off]:
            self.assertTrue(all(r in {c for c, *_ in ep.ROLES} for _, _, r in pixels))

    def test_the_route_sheets_are_made_from_the_same_shapes(self):
        sheets = {a['id']: a for a in assets_of('overgrowth')}
        self.assertEqual(len(sheets['overgrowth-path-default']['frames']), 4)
        self.assertEqual(len(sheets['overgrowth-path-off']['frames']), 1)
        self.assertEqual(len(sheets['overgrowth-path-used']['frames']), 3)


class Package(unittest.TestCase):
    def setUp(self):
        if not (FOLDER / 'example-climb.json').exists():
            self.skipTest('the Overgrowth map is not built')

    def test_the_folder_has_what_the_readme_lists(self):
        for name in ('README.md', 'overgrowth.json', 'overgrowth-ground.png', 'overgrowth-full.png', 'overgrowth-spill.png', 'overgrowth-void.png', 'example-climb.png', 'example-tall.png'):
            self.assertTrue((FOLDER / name).exists(), name)
        for preset, _ in og.EXAMPLES:
            data = json.loads((FOLDER / f'example-{preset}.json').read_text())
            self.assertEqual(data['format'], og.FORMAT)
            self.assertEqual(len(data['nodes']), len(og.generate(dict(og.EXAMPLES)[preset], preset)['centre']))
        spec = json.loads((FOLDER / 'overgrowth.json').read_text())
        self.assertEqual(set(spec['nodes']), {k for k, _ in og.FLOWER_KINDS})
        for kind, node in spec['nodes'].items():
            self.assertEqual(set(node['states']), set(og.STATES))
            self.assertFalse(node['states']['click']['loops'])
        self.assertEqual(set(spec['paths']['states']), {'default', 'off', 'used'})

    def test_the_readmes_recipe_redraws_the_example_floor_from_the_sheets_and_the_layout_file(self):
        from PIL import Image
        rgb = og.rgb_of()
        for preset, seed in og.EXAMPLES[:2]:
            data = json.loads((FOLDER / f'example-{preset}.json').read_text())
            sheet = lambda name: Image.open(FOLDER / f'overgrowth-{name}.png').convert('RGBA')
            ground, full, spill, void = sheet('ground'), sheet('full'), sheet('spill'), sheet('void')
            W, H = data['cells']
            out = Image.new('RGBA', (W * 16, H * 16), (0, 0, 0, 255))
            for y in range(0, out.height, og.VOID):
                for x in range(0, out.width, og.VOID):
                    out.paste(void, (x, y))
            crop = lambda im, col, row: im.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16))
            bits, style, fullv = data['tiles']['bits'], data['tiles']['style'], data['tiles']['full']
            for j in range(H + 1):
                for i in range(W + 1):
                    b = int(bits[j][i], 16)
                    if 0 < b < 15:
                        out.alpha_composite(crop(spill, b, int(style[j][i])), (i * 16 - 8, (j + 1) * 16 - 8))
            for j in range(H + 1):
                for i in range(W + 1):
                    b = int(bits[j][i], 16)
                    if b == 15:
                        out.alpha_composite(crop(full, int(fullv[j][i]), 0), (i * 16 - 8, j * 16 - 8))
                    elif b:
                        out.alpha_composite(crop(ground, b, int(style[j][i])), (i * 16 - 8, j * 16 - 8))
            want = og.render(og.generate(seed, preset), layers=('void', 'spill', 'ground'))
            self.assertEqual(list(out.convert('RGB').getdata()), list(want.convert('RGB').getdata()), preset)

    def test_the_layout_file_holds_the_routes_the_pieces_and_the_node_anchors(self):
        data = json.loads((FOLDER / 'example-climb.json').read_text())
        self.assertEqual(len(data['tiles']['bits']), data['cells'][1] + 1)
        self.assertEqual({len(r) for r in data['tiles']['bits']}, {data['cells'][0] + 1})
        for e in data['edges']:
            self.assertGreater(e['n'], 10)
        for n in data['nodes']:
            self.assertIn(n['kind'], {k for k, _ in og.FLOWER_KINDS})
            self.assertEqual((n['px'], n['py']), (int((n['x'] + 0.5) * 16), int((n['y'] + 0.5) * 16) + 4))
        order = [p['layer'] for p in data['pieces']]
        self.assertEqual(order, sorted(order, key=['tone', 'patch', 'decor', 'hang'].index))


if __name__ == '__main__':
    unittest.main()
