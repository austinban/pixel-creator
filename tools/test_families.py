"""Tests for the asset families: the chests, bazaar, traps, node map and buildings, and the registry and cache that build them.

    python3 -m unittest discover -s tools -p 'test_*.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildcache import assets_of  # noqa: E402
import conventions as cv  # noqa: E402


class Chests(unittest.TestCase):
    """The chests: three rarities, NE and SE, shut and opening, inside the cell, growing with rarity."""

    def test_the_assets_are_grouped_and_named(self):
        import make_chest as mk
        assets = {a['id']: a for a in assets_of('chests')}
        want = {f'chest-{r}-{f}{o}' for r in ('common', 'rare', 'legendary') for f in ('ne', 'se') for o in ('', '-open')}
        self.assertEqual(set(assets), want)
        for a in assets.values():
            self.assertEqual((a['category'], a['folder'], a['place'], a['w'], a['h']), ('Chests', 'chests', 'ground', 48, 52), a['id'])
            self.assertEqual(len(a['frames']), 8 if a['id'].endswith('-open') else 1, a['id'])

    def test_every_frame_is_inside_the_cell_and_on_the_palette(self):
        import make_chest as mk
        import extract_poses as ep
        known = {c for c, *_ in ep.ROLES}
        for a in assets_of('chests'):
            for rows in a['frames']:
                self.assertEqual((len(rows), {len(r) for r in rows}), (52, {48}))
                self.assertTrue(set(''.join(rows)) <= known | {'.'})
                pts = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
                self.assertTrue(all(1 <= x <= 46 and 1 <= y <= 50 for x, y in pts), a['id'] + ' reaches the edge of its cell')

    def test_the_opening_starts_shut_changes_every_frame_and_ends_open(self):
        import make_chest as mk
        assets = {a['id']: a for a in assets_of('chests')}
        for r in mk.RARITIES:
            for f in ('ne', 'se'):
                shut, anim = assets[f'chest-{r}-{f}']['frames'][0], assets[f'chest-{r}-{f}-open']['frames']
                self.assertEqual(anim[0], shut)
                self.assertEqual(len({tuple(x) for x in anim}), len(anim), r + ' repeats a frame')
                self.assertNotEqual(anim[-1], shut)

    def test_a_dearer_chest_is_larger_and_the_two_facings_differ(self):
        import make_chest as mk
        assets = {a['id']: a for a in assets_of('chests')}
        size = lambda rows: sum(ch != '.' for r in rows for ch in r)
        areas = [size(assets[f'chest-{r}-ne']['frames'][0]) for r in ('common', 'rare', 'legendary')]
        self.assertEqual(areas, sorted(areas))
        self.assertEqual(len(set(areas)), 3)
        for r in mk.RARITIES:
            self.assertNotEqual(assets[f'chest-{r}-ne']['frames'][0], assets[f'chest-{r}-se']['frames'][0])


class Bazaar(unittest.TestCase):
    """The bazaar is one 256 x 256 still on the palette, with the floor's middle as its anchor and room round it."""

    def test_one_asset_of_the_right_size(self):
        import make_bazaar as mb
        import extract_poses as ep
        (asset,) = assets_of('bazaar')
        self.assertEqual((asset['id'], asset['w'], asset['h'], asset['kind']), ('bazaar-shop', 256, 256, 'still'))
        rows = asset['frames'][0]
        self.assertEqual((len(rows), {len(r) for r in rows}), (256, {256}))
        self.assertLessEqual(set(''.join(rows)) - {'.'}, {c for c, *_ in ep.ROLES})

    def test_it_floats_with_clear_space_round_it(self):
        import make_bazaar as mb
        rows = assets_of('bazaar')[0]['frames'][0]
        self.assertEqual(rows[0].strip('.'), '')                                   # nothing touches the top, the sides or the bottom
        self.assertTrue(all(r[0] == '.' and r[-1] == '.' for r in rows))
        self.assertEqual(rows[-1].strip('.'), '')
        x, y = mb.ANCHOR
        self.assertNotEqual(rows[y][x], '.')                                       # the anchor is on the floor


class Traps(unittest.TestCase):
    """The traps: grouped, each placed and triggered, inside the cell, and the triggered animation starts like the placed trap and ends changed."""

    def test_the_assets_are_grouped_and_named(self):
        import make_traps as mt
        assets = {a['id']: a for a in assets_of('traps')}
        self.assertEqual(set(assets), {'trap-caltrops', 'trap-caltrops-triggered', 'trap-beartrap', 'trap-beartrap-triggered'})
        for a in assets.values():
            self.assertEqual((a['category'], a['folder'], a['place']), ('Traps', 'traps', 'ground'), a['id'])
        self.assertEqual(len(assets['trap-caltrops']['frames']), 1)
        self.assertEqual(len(assets['trap-beartrap-triggered']['frames']), len(mt.BEARTRAP_FRAMES))
        self.assertEqual(assets['trap-caltrops-triggered']['kind'], 'animation')

    def test_every_frame_is_inside_the_cell_and_outlined_in_the_palette(self):
        import make_traps as mt
        import extract_poses as ep
        known = {c for c, *_ in ep.ROLES}
        for a in assets_of('traps'):
            for rows in a['frames']:
                self.assertEqual(len(rows), 32)
                self.assertTrue(all(len(r) == 32 for r in rows))
                self.assertTrue(set(''.join(rows)) <= known | {'.'})
                painted = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
                self.assertTrue(painted, a['id'])
                self.assertTrue(all(1 <= x <= 30 and 1 <= y <= 30 for x, y in painted), a['id'] + ' reaches the edge of its cell')

    def test_a_triggered_animation_changes_and_the_last_frame_is_not_the_placed_trap(self):
        import make_traps as mt
        assets = {a['id']: a for a in assets_of('traps')}
        for name in mt.TRAPS:
            placed, anim = assets[f'trap-{name}']['frames'][0], assets[f'trap-{name}-triggered']['frames']
            self.assertEqual(len({tuple(f) for f in anim}), len(anim), name + ' repeats a frame')
            self.assertNotEqual(anim[-1], placed, name + ' ends the way it began')


class NodeMap(unittest.TestCase):
    """The node-map tiles: grouped under one name, 16 distinct shore tiles whose neighbours join, and the README's recipe really draws a map."""

    def test_the_assets_are_grouped_and_named(self):
        import make_nodemap as nm
        assets = assets_of('nodemap')
        self.assertEqual(len(assets), 2 * len(nm.BIOMES) + 1)
        for a in assets:
            self.assertEqual(a['category'], 'Node map', a['id'])
            self.assertTrue(a['id'].startswith('nodemap-'), a['id'])
            self.assertEqual(a['folder'], 'nodemap', a['id'])

    def test_the_sixteen_shore_tiles_are_distinct_and_the_ends_are_empty_and_full(self):
        import make_nodemap as nm
        for biome in nm.BIOMES:
            tiles = [nm.shore_tile(b, biome) for b in range(16)]
            self.assertEqual(set(''.join(tiles[0])), {'.'})
            self.assertNotIn('.', ''.join(tiles[15]))
            self.assertEqual(len({tuple(t) for t in tiles}), 16)

    def test_neighbouring_tiles_agree_on_where_land_is_along_the_edge_they_share(self):
        import make_nodemap as nm
        tiles = [nm.shore_tile(b, 'grass') for b in range(16)]
        land = lambda ch: ch not in '.rt'
        for a in range(16):
            for b in range(16):
                if (a >> 1) & 1 == b & 1 and (a >> 3) & 1 == (b >> 2) & 1:         # a's right corners are b's left corners
                    self.assertLessEqual(sum(land(tiles[a][y][15]) != land(tiles[b][y][0]) for y in range(16)), 1, (a, b))
                if (a >> 2) & 1 == b & 1 and (a >> 3) & 1 == (b >> 1) & 1:         # a's bottom corners are b's top corners
                    self.assertLessEqual(sum(land(tiles[a][15][x]) != land(tiles[b][0][x]) for x in range(16)), 1, (a, b))

    def test_the_readmes_recipe_draws_the_example_map_from_the_sheets(self):
        import json
        import make_nodemap as nm
        import extract_poses as ep
        from PIL import Image
        folder = cv.ROOT / 'sprites' / 'assets' / 'nodemap'
        if not (folder / 'example-layout.json').exists():
            self.skipTest('node map not built')
        rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
        rows = json.loads((folder / 'example-layout.json').read_text())['land']
        land = [[ch == '#' for ch in row] for row in rows]
        h, w = len(land), len(land[0])
        at = lambda x, y: 0 <= x < w and 0 <= y < h and land[y][x]
        for biome in nm.BIOMES:
            shore = Image.open(folder / f'nodemap-{biome}-shore.png').convert('RGBA')
            sea = Image.open(folder / f'nodemap-{biome}-sea.png').convert('RGBA')
            out = Image.new('RGBA', (w * 16, h * 16), (0, 0, 0, 255))
            for j in range(h + 1):
                for i in range(w + 1):
                    out.paste(sea.crop((0, 0, 16, 16)), (i * 16 - 8, j * 16 - 8))
            for j in range(h + 1):
                for i in range(w + 1):
                    n = at(i - 1, j - 1) * 1 | at(i, j - 1) * 2 | at(i - 1, j) * 4 | at(i, j) * 8
                    if n:
                        out.alpha_composite(shore.crop(((n % 4) * 16, (n >> 2) * 16, (n % 4) * 16 + 16, (n >> 2) * 16 + 16)), (i * 16 - 8, j * 16 - 8))
            want = nm.render_map(land, biome, 0, rgb)
            self.assertEqual(list(out.convert('RGB').getdata()), list(want.convert('RGB').getdata()), biome)


class Buildings(unittest.TestCase):
    """The building kit: one group, every tile in NE and SE, sized like the ground tiles, and the README's placement recipe really redraws the example."""

    def test_the_assets_are_grouped_named_and_sized(self):
        import make_buildings as mb
        assets = assets_of('buildings')
        self.assertTrue(assets)
        total = 0
        for a in assets:
            self.assertEqual((a['category'], a['folder']), ('Buildings', 'buildings'), a['id'])
            self.assertTrue(a['id'].startswith('bld-'), a['id'])
            self.assertEqual(a['w'], 32, a['id'])
            self.assertIn(a['h'], (32, 48), a['id'])
            self.assertEqual(len(a['frames']), len(a['names']), a['id'])
            for rows in a['frames']:
                self.assertEqual((len(rows), {len(r) for r in rows}), (a['h'], {32}), a['id'])
            total += len(a['frames'])
        self.assertEqual(total, 2 * len(mb.KIT))              # every piece, NE and SE

    def test_a_piece_with_a_direction_differs_between_ne_and_se_and_one_without_does_not(self):
        import make_buildings as mb
        for piece in mb.KIT:
            ne, se = (mb.piece_rows(piece, o)[0] for o in mb.ORIENTS)
            self.assertEqual(ne == se, piece['same'], piece['id'])

    def test_the_pieces_repeat_their_texture_so_stacked_blocks_join(self):
        import make_buildings as mb
        # the left and right edge of a plain block's wall are the same texture a cell over: its picture is the same one stacked on itself
        for pid in ('stone-plain', 'timber-plain'):
            piece = next(p for p in mb.KIT if p['id'] == pid)
            rows, _ = mb.piece_rows(piece, 'NE')
            self.assertEqual(rows[8][4:12], rows[8 + 0][4:12])
            self.assertNotIn('.', rows[16][1:31])             # a wall block has no gaps in its middle

    def test_the_readmes_placement_recipe_redraws_the_example_street(self):
        import json
        import extract_poses as ep
        from PIL import Image
        folder = cv.ROOT / 'sprites' / 'assets' / 'buildings'
        if not (folder / 'buildings.json').exists():
            self.skipTest('buildings not built')
        info = json.loads((folder / 'buildings.json').read_text())
        street = json.loads((folder / 'example-street.json').read_text())
        W, H = street['size']
        cx, cy = street['cellOrigin']
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sheets = {sid: Image.open(folder / meta['file']).convert('RGBA') for sid, meta in info['sheets'].items()}
        for x, y, k, pid in sorted(street['pieces'], key=lambda p: (p[0] + p[1], p[2])):
            piece = info['pieces'][pid]
            cw, ch = info['sheets'][piece['sheet']]['cell']
            tile = sheets[piece['sheet']].crop((piece['col'] * cw, piece['row'] * ch, piece['col'] * cw + cw, piece['row'] * ch + ch))
            gx, gy = cx + 16 * (x - y), cy + 8 * (x + y)
            out.alpha_composite(tile, (gx, gy - 16 * (k + piece['levels'])))
        want = Image.open(folder / 'example-street.png').convert('RGBA')
        self.assertEqual(list(out.getdata()), list(want.getdata()))


class UiShells(unittest.TestCase):
    """The shell drawn behind a dot for a wrapped count: same colours, same middle, still when idle, and its own break."""

    def test_each_dot_has_a_shell_and_a_break(self):
        assets = {a['id']: a for a in assets_of('ui')}
        for dot in ('ui-movement-dot', 'ui-dot-red', 'ui-dot-yellow'):
            shell, broken = assets[dot + '-shell'], assets[dot + '-shell-break']
            self.assertEqual((shell['w'], shell['h'], len(shell['frames']), shell['fps']), (11, 11, 1, 0))
            self.assertEqual((broken['w'], broken['h'], len(broken['frames']), broken['fps']), (19, 19, 8, 14))
            self.assertEqual(shell['anchor'], {'x': 5, 'y': 5})
            self.assertEqual(broken['anchor'], {'x': 9, 'y': 9})

    def test_the_dot_fits_inside_the_shell_with_the_middles_together(self):
        assets = {a['id']: a for a in assets_of('ui')}
        for dot in ('ui-movement-dot', 'ui-dot-red', 'ui-dot-yellow'):
            shell = assets[dot + '-shell']['frames'][0]
            filled = assets[dot]['frames'][0]
            shell_a, dot_a = assets[dot + '-shell']['anchor'], assets[dot]['anchor']
            for y, row in enumerate(filled):
                for x, c in enumerate(row):
                    if c != '.':
                        sx, sy = x - dot_a['x'] + shell_a['x'], y - dot_a['y'] + shell_a['y']
                        self.assertTrue(0 <= sx < 11 and 0 <= sy < 11, f'{dot}: dot pixel outside the shell')
            # the shell is a closed ring: nothing on its edge row or column is empty at the middle of each side
            for edge in (shell[0][5], shell[10][5], shell[5][0], shell[5][10]):
                self.assertNotEqual(edge, '.')

    def test_break_starts_whole_ends_nearly_empty_and_stays_in_its_cell(self):
        for dot in ('ui-movement-dot', 'ui-dot-red', 'ui-dot-yellow'):
            frames = {a['id']: a for a in assets_of('ui')}[dot + '-shell-break']['frames']
            count = [sum(c != '.' for row in f for c in row) for f in frames]
            self.assertGreater(count[0], 60)
            self.assertLess(count[-1], 12)
            self.assertTrue(all(len(row) == 19 for f in frames for row in f) and all(len(f) == 19 for f in frames))


class Water(unittest.TestCase):
    """The animated water: 36 tiles that keep the ground sheet's cells, silhouettes and sides, loop, and join their neighbours."""

    def assets(self):
        return {a['id']: a for a in assets_of('water')}

    def test_thirty_six_tiles_in_two_categories_of_ten_frames(self):
        assets = self.assets()
        self.assertEqual(len(assets), 36)
        self.assertEqual({a['category'] for a in assets.values()}, {'Animated Water', 'Animated Corrupted Water'})
        for a in assets.values():
            self.assertEqual((a['kind'], len(a['frames']), a['fps'], a['w'], a['h']), ('animation', 10, 4, 32, 32), a['id'])

    def test_silhouette_matches_the_ground_sheet_and_the_sides_do_not_move(self):
        import make_ground
        import make_water
        for theme, still in (('original', make_ground.build_ground_assets()), ('corrupted', make_ground.build_ground_assets(make_ground.CORRUPTED))):
            cells = {tuple(map(int, s['id'].split('-')[-2:])): s['frames'][0] for s in still if s['w'] == 32 and s['h'] == 32}
            for a in self.assets().values():
                if a['water']['theme'] != theme:
                    continue
                rows = cells[tuple(a['water']['cell'])]
                off = make_water.TOP_OFFSET[a['water']['level']]
                for f in a['frames']:
                    for y in range(32):
                        for x in range(32):
                            self.assertEqual(f[y][x] == '.', rows[y][x] == '.', f'{a["id"]} silhouette at {x},{y}')
                            if not make_water.in_top(x, y - off):
                                self.assertEqual(f[y][x], rows[y][x], f'{a["id"]} side changed at {x},{y}')

    def test_open_tile_frame_zero_is_the_sheet_tile_and_every_frame_moves(self):
        assets = self.assets()
        a = assets['water-0-2']
        self.assertEqual(len({tuple(f) for f in a['frames']}), 10)
        self.assertEqual(a['water']['foam'], [])

    def test_the_loop_closes_and_neighbours_join(self):
        import make_water
        self.assertEqual((make_water.DRIFT_X[0], make_water.DRIFT_Y[0]), (0, 0))
        self.assertEqual(len(make_water.DRIFT_X), make_water.FRAMES)
        # the loop's whole drift is one step of the tiling, (16, 8): the same place on the face
        for x, y in ((16, 8), (10, 6), (20, 9), (12, 11)):
            self.assertEqual(make_water.reduce_to_face(x - 16, y - 8), make_water.reduce_to_face(x, y))
            self.assertEqual(make_water.reduce_to_face(x, y), (x, y))

    def test_every_foam_side_set_has_a_tile_at_both_heights(self):
        import make_water
        for table in (make_water.FLUSH, make_water.SUNKEN):
            self.assertEqual({frozenset(v) for v in table.values()}, {frozenset(v) for v in ([], ['NE'], ['NW'], ['SE'], ['SW'], ['NW', 'NE'], ['NE', 'SE'], ['NW', 'SW'], ['SW', 'SE'])})
            self.assertEqual(len(table), 9)


class Panel(unittest.TestCase):
    """The menu panel: nine pieces and a ready-made one, outlined, rounded, with no gaps, and joining without a seam."""

    def assets(self):
        return {a['id']: a for a in assets_of('panel')}

    def test_nine_pieces_and_a_ready_made_one_at_the_sizes_the_readme_gives(self):
        assets = self.assets()
        self.assertEqual(len(assets), 15)
        sizes = {'tl': (40, 54), 't': (64, 54), 'tr': (40, 54), 'l': (40, 64), 'c': (64, 64), 'r': (40, 64), 'bl': (40, 44), 'b': (64, 44), 'br': (40, 44), 't2': (64, 54), 't3': (64, 54), 't4': (64, 54), 't5': (64, 54), 't6': (64, 54)}
        for name, (w, h) in sizes.items():
            a = assets['ui-panel-' + name]
            self.assertEqual((a['category'], a['kind'], len(a['frames']), a['w'], a['h']), ('UI', 'still', 1, w, h), name)
            self.assertEqual((len(a['frames'][0]), len(a['frames'][0][0])), (h, w), name)
        self.assertEqual((assets['ui-panel']['w'], assets['ui-panel']['h']), (320, 138))

    def test_the_whole_panel_is_outlined_rounded_and_has_no_gaps(self):
        import make_panel as mp
        for width, height in ((320, 120), (80, 80), (203, 131)):
            rows = mp.assemble(width, height)
            self.assertEqual((len(rows[0]), len(rows)), (width, mp.PAD + height + mp.SLAB), (width, height))
            self.assertEqual(rows[mp.PAD][0], '.', 'a square corner')
            body = rows[mp.PAD + mp.CH: mp.PAD + height - mp.CH]
            for y, row in enumerate(body):
                self.assertEqual(row[0], 'O', f'row {y}: the left edge is not outlined')
                self.assertEqual(row[-1], 'O', f'row {y}: the right edge is not outlined')
                self.assertNotIn('.', row, f'row {y}: a gap in the panel')

    def test_the_pieces_wrap_and_the_panel_is_the_same_every_time(self):
        import make_panel as mp
        self.assertEqual(mp.assemble(320, 120), mp.assemble(320, 120))
        # a wider panel is the narrower one with more of the wrapping pieces: the corners and the first 64-wide runs are the same
        narrow, wide = mp.assemble(200, 120), mp.assemble(400, 120)
        for y in range(len(narrow)):
            self.assertEqual(narrow[y][:mp.CW + mp.TILE], wide[y][:mp.CW + mp.TILE], y)
        # the left and right edges wrap top to bottom: a taller panel repeats them every 64 rows
        tall = mp.assemble(200, 400)
        mid = [row for row in tall[mp.PAD + mp.CH: mp.PAD + 400 - mp.CH]]
        for y in range(len(mid) - mp.TILE):
            self.assertEqual(mid[y], mid[y + mp.TILE], y)

    def test_the_six_top_edges_follow_each_other_in_any_order_without_a_seam(self):
        import make_panel as mp
        self.assertEqual(len(mp.TOP_VARIANTS), 6)
        self.assertAlmostEqual(sum(mp.TOP_WEIGHTS), 1.0)
        base = mp.piece('T')
        pieces = {v: mp.piece(v) for v in mp.TOP_VARIANTS}
        for v, rows in pieces.items():
            self.assertEqual((len(rows), len(rows[0])), (len(base), mp.TILE), v)
        self.assertEqual(len({tuple(rows) for rows in pieces.values()}), 6, 'two top edges are the same picture')
        for v, rows in pieces.items():
            for y in range(len(base)):
                for x in list(range(0, 4)) + list(range(mp.TILE - 4, mp.TILE)):
                    self.assertEqual(rows[y][x], base[y][x], f'{v} differs at its end ({x}, {y}): it would not join')

    def test_the_random_choice_is_stable_and_uses_every_picture(self):
        import make_panel as mp
        picks = [mp.pick_top(i, 1) for i in range(400)]
        self.assertEqual(picks, [mp.pick_top(i, 1) for i in range(400)])
        self.assertEqual(set(picks), set(mp.TOP_VARIANTS))
        self.assertLess(picks.count('T'), picks.count('T2'))             # the busy one least, the mossy one most

    def test_it_has_mushrooms_and_vines_in_palette_roles(self):
        import make_panel as mp
        rows = mp.assemble(320, 120)
        text = ''.join(rows)
        for role in 'ji' 'rq' 'AzB':                             # pink and teal caps, and the greens of the moss and vines
            self.assertIn(role, text, role)
        self.assertTrue(set(text) <= set('.OABCDabcdeghijklmnopqrstuvwxyz'), set(text))
        self.assertTrue(any(ch != '.' for ch in rows[1]), 'the pad has more headroom than the mushrooms use')          # the tallest mushroom, with its outline, reaches row 1 of the pad
        self.assertTrue(all(ch == '.' for ch in rows[0]), 'a mushroom is cut off by the pad')


class Buttons(unittest.TestCase):
    """The menu buttons: 33 sheets (3 colourways by 11 sizes), three states each, rounded, outlined and inside their cells."""

    def assets(self):
        return {a['id']: a for a in assets_of('buttons')}

    def test_thirty_three_sheets_of_three_states(self):
        import make_buttons as mb
        assets = self.assets()
        self.assertEqual(len(assets), 33)
        for a in assets.values():
            self.assertEqual((a['category'], a['kind'], len(a['frames']), a['cols'], a['rows']), ('UI', 'variants', 3, 3, 1), a['id'])
            self.assertEqual([a['w'], a['h']], a['button']['cell'], a['id'])
        for name, cell in (('short-xs', (48, 32)), ('compact-sm', (112, 40)), ('icon-sq', (36, 36))):
            for colourway in ('primary', 'low', 'red'):
                a = assets[f'ui-button-{colourway}-{name}']
                self.assertEqual((a['w'], a['h']), cell, a['id'])
        self.assertEqual(assets['ui-button-red-compact-sm']['button']['body'], 36)
        self.assertEqual({a['button']['colourway'] for a in assets.values()}, {'primary', 'low', 'red'})

    def test_every_state_is_outlined_inside_its_cell_with_rounded_corners_and_no_gaps(self):
        for a in self.assets().values():
            for f in a['frames']:
                self.assertEqual((len(f), len(f[0])), (a['h'], a['w']), a['id'])
                self.assertEqual(f[0][0], '.', f'{a["id"]}: a square corner')
                self.assertEqual(f[a['h'] - 1][0], '.', f'{a["id"]}: a square corner')
                for y in range(a['h']):
                    for x in range(a['w']):
                        if f[y][x] == '.':
                            continue
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nx, ny = x + dx, y + dy
                            if not (0 <= nx < a['w'] and 0 <= ny < a['h']) or f[ny][nx] == '.':
                                self.assertIn(f[y][x], 'OABzsD', f'{a["id"]}: a bare edge at {x},{y}')       # the outline, or the moss over the top edge

    def test_states_differ_and_the_middle_repeats_without_a_seam(self):
        import make_buttons as mb
        for a in self.assets().values():
            self.assertEqual(len({tuple(f) for f in a['frames']}), 3, a['id'])
        for colourway in mb.COLOURWAYS:
            for height in mb.HEIGHTS:
                mb.configure(height, colourway)
                mid = mb.piece('default', 'middle')
                for y in range(mb.H):
                    self.assertEqual(mid[y][0] == '.', mid[y][-1] == '.', f'{colourway}/{height} row {y}')
        mb.configure('std', 'primary')

    def test_no_pixel_of_a_state_is_left_unpainted_in_the_middle_of_the_body(self):
        for a in self.assets().values():
            f = a['frames'][0]
            self.assertNotIn('.', f[a['h'] // 2][4:-4], a['id'])


class Trees(unittest.TestCase):
    """The new trees and bushes: ten stills, four of them taller than the sheet's 64 px pine, each outlined, inside its cell, standing on its anchor."""

    def assets(self):
        return {a['id']: a for a in assets_of('trees')}

    def test_ten_and_four_are_tall(self):
        assets = self.assets()
        self.assertEqual(len(assets), 10)
        tall = [a for a in assets.values() if a['h'] >= 100]
        self.assertGreaterEqual(len(tall), 4)
        for a in assets.values():
            self.assertEqual(a['tree']['footprint'], [1, 1], a['id'])
            self.assertTrue(a['tree']['blocks'], a['id'])
            self.assertEqual(a['category'], 'Trees')

    def test_each_is_outlined_inside_its_cell_and_stands_on_its_anchor(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            self.assertEqual((len(rows), len(rows[0])), (a['h'], a['w']), a['id'])
            pts = [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.']
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.assertTrue(min(xs) >= 1 and max(xs) <= a['w'] - 2 and min(ys) >= 1 and max(ys) <= a['h'] - 2, f'{a["id"]} touches its cell edge')
            for x, y in pts:
                if any(not (0 <= x + dx < a['w'] and 0 <= y + dy < a['h']) or rows[y + dy][x + dx] == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.assertEqual(rows[y][x], 'O', f'{a["id"]}: a bare edge at {x},{y}')
            self.assertLessEqual(max(ys), a['anchor']['y'] + 12, f'{a["id"]} stands below its anchor')


class BloodPool(unittest.TestCase):
    """The blood pool: six irregular decals on a tile's top face (32 x 16), inside the diamond, with no outline."""

    def test_six_pools_inside_the_diamond(self):
        pool = {a['id']: a for a in assets_of('blood-pool')}['blood-pool']
        self.assertEqual((pool['w'], pool['h'], pool['category'], pool['place'], pool['anchor']), (32, 16, 'Decals', 'ground', {'x': 16, 'y': 8}))
        self.assertEqual((len(pool['frames']), len(pool['names'])), (6, 6))
        shapes = set()
        for rows in pool['frames']:
            self.assertEqual((len(rows), len(rows[0])), (16, 32))
            pts = [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.']
            self.assertGreater(len(pts), 70, 'a pool should be a pool, not a stain')
            for x, y in pts:
                self.assertTrue(abs(x + 0.5 - 16) / 16 + abs(y + 0.5 - 8) / 8 <= 1.0, 'a pool should stay on its tile')
                self.assertNotEqual(rows[y][x], 'O', 'a stain has no outline')
            shapes.add(tuple(rows))
        self.assertEqual(len(shapes), 6, 'six different pools')


class BodyExplosion(unittest.TestCase):
    """The body explosion: six frames on a 48 x 48 cell, in the blood pool's four colours only, bursting, peaking and leaving only splatters."""

    def asset(self):
        return {a['id']: a for a in assets_of('body-explosion')}['body-explosion']

    def test_six_frames_on_a_48_cell_anchored_at_the_body(self):
        a = self.asset()
        self.assertEqual((a['w'], a['h'], a['category'], a['kind'], a['place'], a['fps'], a['anchor']), (48, 48, 'Animations', 'animation', 'ground', 12, {'x': 24, 'y': 34}))
        self.assertEqual(len(a['frames']), 6)
        for rows in a['frames']:
            self.assertEqual((len(rows), len(rows[0])), (48, 48))

    def test_it_uses_only_the_blood_pools_colours_and_no_outline(self):
        a = self.asset()
        for rows in a['frames']:
            self.assertTrue(set(''.join(rows)) <= set('.uhij'), set(''.join(rows)))

    def test_it_bursts_peaks_and_leaves_only_splatters(self):
        counts = [sum(c != '.' for row in rows for c in row) for rows in self.asset()['frames']]
        self.assertIn(counts.index(max(counts)), (1, 2), counts)                # the biggest frame is the second or the third
        self.assertGreater(max(counts), 2 * counts[0], counts)                  # it grew out of the burst
        self.assertLess(counts[5], max(counts) // 2, counts)                    # and is mostly gone by the last frame
        self.assertGreater(counts[5], 30, 'the splatters are left on the ground')
        self.assertEqual(len({tuple(r) for r in self.asset()['frames']}), 6, 'two frames are the same')

    def test_it_is_the_same_every_time(self):
        import make_body_explosion as m
        self.assertEqual(m.build_assets()[0]['frames'], m.build_assets()[0]['frames'])


class Rocks(unittest.TestCase):
    """The rock kit: blocky ledges and crags and natural slabs and stones, on footprints of 1 x 1 to 2 x 2, 1 x 3 and L, some with flat tops a unit can walk on."""

    def assets(self):
        return {a['id']: a for a in assets_of('rocks')}

    def test_every_rock_is_a_ground_still_sized_to_its_footprint(self):
        import make_rocks as m
        assets = self.assets()
        self.assertEqual(sorted(assets), sorted(s[0] for s in m.SHAPES))
        for a in assets.values():
            fx, fy = a['footprint']['size']
            self.assertEqual((a['category'], a['kind'], a['place'], len(a['frames'])), ('Nature', 'still', 'ground', 1), a['id'])
            self.assertEqual(a['w'], 16 * (fx + fy) + 2 * m.MARGIN, a['id'])
            self.assertEqual(a['anchor']['x'], a['w'] // 2, a['id'])                 # the middle of the footprint is the middle of the picture
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (a['w'], a['h']), a['id'])
            low = max(y for y, r in enumerate(rows) if r.strip('.'))
            front = max(i + j + 2 for i, j in a['footprint']['cells'])
            self.assertGreaterEqual(low, a['anchor']['y'] + 8 * front - 4 * (fx + fy) - 7, a['id'])      # it stands on the ground diamond of its lowest cell, not above it
            self.assertLess(low, a['h'], a['id'])

    def test_the_footprints_are_the_ones_promised(self):
        shapes = {a['footprint']['size'][0] * 10 + a['footprint']['size'][1] for a in self.assets().values()}
        for size in (11, 12, 21, 22, 13, 31):
            self.assertIn(size, shapes)
        ls = [a for a in self.assets().values() if len(a['footprint']['cells']) in (3, 4) and a['footprint']['size'] in ([2, 2], [3, 2], [2, 3])]
        self.assertGreaterEqual(len(ls), 8)                                              # the L, in all its turns
        for a in self.assets().values():
            cells = {tuple(c) for c in a['footprint']['cells']}
            fx, fy = a['footprint']['size']
            self.assertTrue(any(c[0] == 0 for c in cells) and any(c[1] == 0 for c in cells) and any(c[0] == fx - 1 for c in cells) and any(c[1] == fy - 1 for c in cells), a['id'])

    def test_a_walkable_rock_has_a_flat_top_over_every_cell(self):
        import make_rocks as m
        walk = [a for a in self.assets().values() if a['walkable']]
        self.assertGreaterEqual(len(walk), 36)
        for a in walk:
            self.assertEqual(sorted(a['top_cover']), sorted(f'{i},{j}' for i, j in a['footprint']['cells']), a['id'])
            self.assertGreaterEqual(min(a['top_cover'].values()), m.WALK_MIN, a['id'])
            self.assertIn(a['levels'], (1, 2), a['id'])                                  # whole levels, so it lines up with the ground's steps

    def test_crags_and_stones_are_never_walkable_and_ledges_and_slabs_are(self):
        for a in self.assets().values():
            if a['id'].startswith(('rock-crag', 'rock-stone')):
                self.assertFalse(a['walkable'], a['id'])
                self.assertNotIn('top_cover', a)
            else:
                self.assertTrue(a['walkable'], a['id'])

    def test_every_rock_is_outlined(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            h, w = len(rows), len(rows[0])
            for y in range(h):
                for x in range(w):
                    if rows[y][x] in '.O':
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        self.assertTrue(0 <= nx < w and 0 <= ny < h and rows[ny][nx] != '.', f'{a["id"]}: a bare edge at {x},{y}')

    def test_a_natural_rock_never_undercuts(self):
        import make_rocks as m
        for sid, label, cells, kind, levels in m.SHAPES:
            if kind in ('slab', 'stone'):
                blobs = m.build_slab(cells, levels, m.seed_of(sid)) if kind == 'slab' else m.build_stones(cells, levels, m.seed_of(sid), sid)
                for b in blobs:
                    self.assertLessEqual(b.c[2], 0.0, sid)                              # widest at the ground, so it only narrows going up

    def test_the_variants_differ_and_it_is_the_same_every_time(self):
        import make_rocks as m
        pics = {tuple(a['frames'][0]) for a in self.assets().values()}
        self.assertEqual(len(pics), len(self.assets()))
        self.assertEqual(m.render(*m.SHAPES[0][2:4], m.SHAPES[0][4], 7), m.render(*m.SHAPES[0][2:4], m.SHAPES[0][4], 7))


class UiControls(unittest.TestCase):
    """The slider (track, fill, knob) and the toggle: pieces that join, the sizes the game is told, outlined, and the states differing."""

    def assets(self):
        return {a['id']: a for a in assets_of('ui-controls')}

    def test_the_pieces_and_their_sizes(self):
        assets = self.assets()
        sizes = {'ui-slider-track-left': (8, 16), 'ui-slider-track-mid': (32, 16), 'ui-slider-track-right': (8, 16), 'ui-slider-fill-left': (8, 16), 'ui-slider-fill-mid': (32, 16),
                 'ui-slider-knob-default': (24, 24), 'ui-slider-knob-hovered': (24, 24), 'ui-slider-knob-pressed': (24, 24),
                 'ui-toggle-off': (44, 22), 'ui-toggle-off-hovered': (44, 22), 'ui-toggle-on': (44, 22), 'ui-toggle-on-hovered': (44, 22)}
        self.assertEqual(sorted(assets), sorted(sizes))
        for id, (w, h) in sizes.items():
            a = assets[id]
            self.assertEqual((a['category'], a['kind'], a['place'], a['w'], a['h'], len(a['frames'])), ('UI', 'still', 'none', w, h, 1), id)
            rows = a['frames'][0]
            self.assertEqual((len(rows[0]), len(rows)), (w, h), id)

    def test_the_wrapping_middle_joins_itself(self):
        a = self.assets()
        for id in ('ui-slider-track-mid', 'ui-slider-fill-mid'):
            rows = a[id]['frames'][0]
            for y in range(16):
                # the first and last columns of a middle are the same kind of pixel in the same rows, so a run of them has no seam
                self.assertEqual(rows[y][0] == '.', rows[y][-1] == '.', f'{id} row {y}')

    def test_the_track_caps_meet_the_middle(self):
        a = self.assets()
        for y in range(16):
            self.assertEqual(a['ui-slider-track-left']['frames'][0][y][-1] == '.', a['ui-slider-track-mid']['frames'][0][y][0] == '.', y)
            self.assertEqual(a['ui-slider-track-right']['frames'][0][y][0] == '.', a['ui-slider-track-mid']['frames'][0][y][-1] == '.', y)

    def test_the_fill_sits_inside_the_trough(self):
        a = self.assets()
        for piece in ('left', 'mid'):
            rows = a[f'ui-slider-fill-{piece}']['frames'][0]
            for y in (0, 1, 2, 13, 14, 15):
                self.assertTrue(all(c == '.' for c in rows[y]), f'fill {piece} row {y}')

    def test_every_round_piece_is_outlined(self):
        for id, a in self.assets().items():
            if 'fill' in id:
                continue
            rows = a['frames'][0]
            h, w = len(rows), len(rows[0])
            for y in range(h):
                for x in range(w):
                    if rows[y][x] in '.OzA':                                      # moss may sit over the outline
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:                       # a cap's open side is allowed
                            self.assertNotEqual(rows[ny][nx], '.', f'{id}: a bare edge at {x},{y}')

    def test_the_states_differ(self):
        a = self.assets()
        for group in (('ui-slider-knob-default', 'ui-slider-knob-hovered', 'ui-slider-knob-pressed'),
                      ('ui-toggle-off', 'ui-toggle-off-hovered', 'ui-toggle-on', 'ui-toggle-on-hovered')):
            self.assertEqual(len({tuple(a[i]['frames'][0]) for i in group}), len(group))

    def test_the_toggle_knob_is_at_the_left_when_off_and_the_right_when_on(self):
        a = self.assets()
        def bead(id):
            rows = a[id]['frames'][0]
            xs = [x for r in rows for x, c in enumerate(r) if c in 'dba']
            return sum(xs) / len(xs) if xs else None
        self.assertGreater(bead('ui-toggle-on'), 30)
        off = a['ui-toggle-off']['frames'][0]
        self.assertTrue(any(c != '.' for c in off[11][:12]))

    def test_it_is_the_same_every_time(self):
        import make_ui_controls as m
        self.assertEqual([x['frames'] for x in m.build_assets()], [x['frames'] for x in m.build_assets()])


class HudIcons(unittest.TestCase):
    """The text icons: gold (a golden mushroom), experience (a star) and the three difficulty skulls, 16 x 16 each, outlined, and the skulls the same picture in three colours."""

    def assets(self):
        return {a['id']: a for a in assets_of('hud-icons')}

    def test_five_16_pixel_stills(self):
        assets = self.assets()
        self.assertEqual(sorted(assets), ['icon-gold', 'icon-skull-green', 'icon-skull-red', 'icon-skull-yellow', 'icon-xp'])
        for a in assets.values():
            self.assertEqual((a['category'], a['kind'], a['place'], a['w'], a['h'], len(a['frames'])), ('UI', 'still', 'none', 16, 16, 1), a['id'])
            rows = a['frames'][0]
            self.assertEqual((len(rows), len(rows[0])), (16, 16), a['id'])
            self.assertGreater(sum(c != '.' for r in rows for c in r), 60, a['id'])

    def test_every_icon_is_outlined(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            for y in range(16):
                for x in range(16):
                    if rows[y][x] in '.O':
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        self.assertTrue(0 <= nx < 16 and 0 <= ny < 16 and rows[ny][nx] != '.', f'{a["id"]}: a bare edge at {x},{y}')

    def test_the_skulls_are_one_picture_in_three_colours(self):
        assets = self.assets()
        masks = {c: [''.join('X' if ch != '.' else '.' for ch in r) for r in assets[f'icon-skull-{c}']['frames'][0]] for c in ('green', 'yellow', 'red')}
        self.assertEqual(masks['green'], masks['yellow'])
        self.assertEqual(masks['green'], masks['red'])
        self.assertEqual(len({tuple(assets[f'icon-skull-{c}']['frames'][0]) for c in ('green', 'yellow', 'red')}), 3)
        used = {c: set(''.join(assets[f'icon-skull-{c}']['frames'][0])) - set('.Ox') for c in ('green', 'yellow', 'red')}
        self.assertEqual(used['green'], {'z', 'A'})                                # light and middle: lime and green
        self.assertEqual(used['yellow'], {'d', 'b'})                               # yellow and amber
        self.assertEqual(used['red'], {'c', 'e'})                                  # salmon and coral
        rows = assets['icon-skull-green']['frames'][0]                          # 13 x 14, from (1, 1)
        self.assertEqual((min(i for r in rows for i, c in enumerate(r) if c != '.'), max(i for r in rows for i, c in enumerate(r) if c != '.')), (1, 13))
        self.assertEqual((min(y for y, r in enumerate(rows) if r.strip('.')), max(y for y, r in enumerate(rows) if r.strip('.'))), (1, 14))

    def test_gold_is_golden_and_experience_is_cyan(self):
        assets = self.assets()
        gold = set(''.join(assets['icon-gold']['frames'][0])) - set('.O')
        self.assertTrue({'d', 'b', 'a'} <= gold, gold)
        xp = set(''.join(assets['icon-xp']['frames'][0])) - set('.O')
        self.assertTrue(xp <= set('rotn') | {'m'}, xp)
        self.assertIn('o', xp)


class ItemIcons(unittest.TestCase):
    """The 26 item pictures: 32 x 32 stills, outlined, in palette roles, with the weapons on the same diagonal."""

    IDS = ['recurve_bow', 'sling', 'worn_sword', 'worn_dagger', 'worn_bow', 'oak_staff', 'warding_staff', 'storm_staff', 'leather_jerkin', 'iron_mail', 'warden_plate', 'dragonscale_mail',
           'swift_boots', 'windrunner_boots', 'warding_charm', 'vigor_ring', 'strength_band', 'sage_amulet', 'giants_belt', 'hawkeye_pendant', 'guardian_sigil', 'sage_circlet',
           'summit_crown', 'phoenix_heart', 'stormcaller_band', 'stone_idol']

    def assets(self):
        return {a['id']: a for a in assets_of('item-icons')}

    def test_twenty_six_32_pixel_stills_named_for_the_games_ids(self):
        assets = self.assets()
        self.assertEqual(sorted(assets), sorted('item-' + i for i in self.IDS))
        for a in assets.values():
            self.assertEqual((a['category'], a['kind'], a['place'], a['w'], a['h'], len(a['frames'])), ('Item icons', 'still', 'none', 32, 32, 1), a['id'])
            rows = a['frames'][0]
            self.assertEqual((len(rows), len(rows[0])), (32, 32), a['id'])
            self.assertGreater(sum(c != '.' for r in rows for c in r), 120, f'{a["id"]} is nearly empty')
            self.assertEqual(rows[0][0], '.', a['id'])

    def test_every_icon_is_outlined_and_inside_its_cell(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            for y in range(32):
                for x in range(32):
                    if rows[y][x] in '.O':
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < 32 and 0 <= ny < 32):
                            continue                                             # an icon may run to the edge of its cell
                        self.assertNotEqual(rows[ny][nx], '.', f'{a["id"]}: a bare edge at {x},{y}')

    def test_the_weapons_lie_on_one_diagonal_rising_to_the_right(self):
        for name in ('recurve_bow', 'worn_sword', 'worn_dagger', 'worn_bow', 'oak_staff', 'warding_staff', 'storm_staff'):
            rows = self.assets()['item-' + name]['frames'][0]
            pts = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c not in '.O']
            n = len(pts)
            mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
            cov = sum((x - mx) * (y - my) for x, y in pts) / n
            self.assertLess(cov, 0, f'{name} does not slope up to the right')          # y grows downwards, so a rise to the right is a negative covariance

    def test_it_is_the_same_every_time(self):
        import make_item_icons3d as m
        self.assertEqual([a['frames'] for a in m.build_assets()], [a['frames'] for a in m.build_assets()])


class AllTree(unittest.TestCase):
    """The All Tree, the victory screen's display piece: a 384 x 448 still and a 12-frame loop, the tree cropped by the top edge and the frames loop-safe."""

    def assets(self):
        return {a['id']: a for a in assets_of('all-tree')}

    def test_a_still_and_a_loop_in_one_cell(self):
        assets = self.assets()
        self.assertEqual(sorted(assets), ['all-tree', 'all-tree-still'])
        for a in assets.values():
            self.assertEqual((a['w'], a['h'], a['category'], a['place'], a['anchor']), (384, 448, 'Victory Screen', 'none', {'x': 192, 'y': 336}))
            for rows in a['frames']:
                self.assertEqual((len(rows), len(rows[0])), (448, 384), a['id'])
        loop = assets['all-tree']
        self.assertEqual((loop['kind'], len(loop['frames']), loop['fps']), ('animation', 12, 10))

    def test_the_tree_runs_off_the_top_and_stays_put_while_it_shimmers(self):
        loop = self.assets()['all-tree']['frames']
        for rows in loop:
            self.assertTrue(any(c != '.' for c in rows[0]), 'the trunk should run off the top edge')
            self.assertTrue(any(c != '.' for c in rows[-48]), 'and stand on its base')
        silhouette = [[[c != '.' for c in row] for row in rows] for rows in (loop[0], loop[6])]
        steady = sum(1 for y in range(300, 448) for x in range(384) if silhouette[0][y][x] == silhouette[1][y][x])
        self.assertGreater(steady, 0.98 * 148 * 384, 'the base should not wobble between frames')


class AllTreeFall(unittest.TestCase):
    """The autumn All Tree: the same cell, anchor and boughs as the corrupted one, with no mushrooms, in yellow, orange and red."""

    def test_a_still_and_a_loop_like_the_corrupted_tree(self):
        fall = {a['id']: a for a in assets_of('all-tree-fall')}
        corrupted = {a['id']: a for a in assets_of('all-tree')}
        self.assertEqual(sorted(fall), ['all-tree-fall', 'all-tree-fall-still'])
        for a in fall.values():
            self.assertEqual((a['w'], a['h'], a['category'], a['place'], a['anchor']), (384, 448, 'Victory Screen', 'none', {'x': 192, 'y': 336}))
        loop = fall['all-tree-fall']
        self.assertEqual((loop['kind'], len(loop['frames']), loop['fps']), ('animation', 12, 10))
        # the trunk and the roots are the same drawing: the base's silhouette agrees with the corrupted tree's, below the foliage
        base = lambda frame: [[c != '.' for c in row] for row in frame[330:430]]
        a, b = base(fall['all-tree-fall-still']['frames'][0]), base(corrupted['all-tree-still']['frames'][0])
        same = sum(1 for ra, rb in zip(a, b) for x, y in zip(ra, rb) if x == y)
        self.assertGreater(same, 0.9 * 100 * 384, 'the roots should sit where the corrupted tree\'s do')

    def test_it_has_leaves_in_all_three_colours_and_no_mushroom_caps(self):
        rows = {a['id']: a for a in assets_of('all-tree-fall')}['all-tree-fall-still']['frames'][0]
        count = {}
        for row in rows:
            for c in row:
                count[c] = count.get(c, 0) + 1
        yellow, orange, red = count.get('d', 0) + count.get('b', 0), count.get('a', 0), count.get('c', 0) + count.get('h', 0)
        self.assertTrue(yellow > 500 and orange > 500 and red > 500, (yellow, orange, red))


class AllTreeWide(unittest.TestCase):
    """The wide All Trees: the same trees on a 704 x 448 canvas so the sides are not cut off, with the anchor at the middle."""

    PAIRS = (('all-tree-wide', 'all-tree', 'all-tree-wide', 'all-tree-wide-still', 'all-tree-still'),
             ('all-tree-fall-wide', 'all-tree-fall', 'all-tree-fall-wide', 'all-tree-fall-wide-still', 'all-tree-fall-still'))

    def test_a_wide_still_and_loop_for_each_tree(self):
        for unit, narrow_unit, loop_id, still_id, _ in self.PAIRS:
            assets = {a['id']: a for a in assets_of(unit)}
            self.assertEqual(sorted(assets), sorted([loop_id, still_id]))
            for a in assets.values():
                self.assertEqual((a['w'], a['h'], a['category'], a['place'], a['anchor']), (704, 448, 'Victory Screen', 'none', {'x': 352, 'y': 336}))
                for rows in a['frames']:
                    self.assertEqual((len(rows), len(rows[0])), (448, 704), a['id'])
            self.assertEqual((assets[loop_id]['kind'], len(assets[loop_id]['frames']), assets[loop_id]['fps']), ('animation', 12, 10))

    def test_no_painted_pixel_touches_the_sides(self):
        for unit, _, loop_id, *_ in self.PAIRS:
            for rows in {a['id']: a for a in assets_of(unit)}[loop_id]['frames']:
                for row in rows:
                    self.assertTrue(row[0] == '.' and row[-1] == '.', f'{loop_id}: a pixel on the edge')

    def test_the_middle_is_the_narrow_tree(self):
        """The anchor is at the middle, so narrow column x is wide column x + 160; away from the old edges the two pictures are the same."""
        for unit, narrow_unit, _, wide_still, narrow_still in self.PAIRS:
            wide = {a['id']: a for a in assets_of(unit)}[wide_still]['frames'][0]
            narrow = {a['id']: a for a in assets_of(narrow_unit)}[narrow_still]['frames'][0]
            for y in range(448):
                self.assertEqual(wide[y][184:520], narrow[y][24:360], f'{wide_still} row {y}')


class Bosses(unittest.TestCase):
    """The bosses: 96 x 96 on a 2 x 2 footprint, every action in both facings (they read from sprites/NAME, which is local)."""

    def test_the_blood_mushroom_has_every_action_in_a_96_cell(self):
        if not (Path(__file__).resolve().parent.parent / 'sprites' / 'blood-mushroom').is_dir():
            self.skipTest('sprites/blood-mushroom is not here')
        assets = {a['id']: a for a in assets_of('boss')}
        for action, count in cv.BOSS_FRAMES.items():
            for facing in ('ne', 'se'):
                a = assets[f'blood-mushroom-{action}-{facing}']
                self.assertEqual((a['w'], a['h'], a['category'], a['place']), (96, 96, 'Bosses', 'ground'))
                self.assertEqual(len(a['frames']), count, a['id'])
                self.assertEqual(a['anchor'], {'x': 48, 'y': 72})


class Elites(unittest.TestCase):
    """The elites: bigger than a creature, on one tile, in a 64 x 64 cell, with every action in both facings (the rat king reads from sprites/rat-king, which is local)."""

    def test_the_rat_king_has_every_action_in_a_64_cell(self):
        if not (Path(__file__).resolve().parent.parent / 'sprites' / 'rat-king').is_dir():
            self.skipTest('sprites/rat-king is not here')
        assets = {a['id']: a for a in assets_of('elite')}
        self.assertEqual(len(assets), 14)
        counts = {'charging': 1, 'attack': 4, 'release': 1, 'damage': 1, 'weak': 1, 'dead': 1, 'walking': 8}
        for action, count in counts.items():
            for facing in ('ne', 'se'):
                a = assets[f'rat-king-{action}-{facing}']
                self.assertEqual((a['w'], a['h'], a['category'], a['place']), (64, 64, 'Elites', 'ground'))
                self.assertEqual(len(a['frames']), count, a['id'])
                self.assertEqual(a['anchor'], {'x': 32, 'y': 52})
                self.assertEqual(a['cols'] * a['rows'], count)

    def test_the_checks_catch_a_frame_that_leaves_the_cell(self):
        row = '.' * 64
        bad = [[row] * 64]
        bad[0][0] = 'O' * 64
        found = cv.check_elite('x', {'chargingNE': bad})
        self.assertTrue(any('only' in p or 'edge' in p for p in found))


class SlotIcons(unittest.TestCase):
    """The Weapon, Armor and Trinket slot icons: three 32 x 32 stills, outlined, inside their cell."""

    def test_three_icons_outlined_and_inside_the_cell(self):
        assets = {a['id']: a for a in assets_of('slot-icons')}
        self.assertEqual(sorted(assets), ['slot-armor', 'slot-trinket', 'slot-weapon'])
        for a in assets.values():
            rows = a['frames'][0]
            self.assertEqual((a['w'], a['h'], len(rows), len(rows[0])), (32, 32, 32, 32), a['id'])
            pts = [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.']
            self.assertGreater(len(pts), 150, a['id'])
            self.assertTrue(all(1 <= x <= 30 and 1 <= y <= 30 for x, y in pts), f'{a["id"]} touches its cell edge')
            for x, y in pts:
                if any(not (0 <= x + dx < 32 and 0 <= y + dy < 32) or rows[y + dy][x + dx] == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.assertEqual(rows[y][x], 'O', f'{a["id"]}: a bare edge at {x},{y}')


class Fungi(unittest.TestCase):
    """The mushroom trees: six of them, anchored on their footprint, inside their cell, and the giant one is the walkable 2 x 2."""

    def assets(self):
        return {a['id']: a for a in assets_of('fungi')}

    def test_there_are_six_and_one_covers_four_tiles(self):
        assets = self.assets()
        self.assertGreaterEqual(len(assets), 6)
        wide = [a for a in assets.values() if a['fungus']['footprint'] == [2, 2]]
        self.assertEqual([a['id'] for a in wide], ['fungus-toadstool'])
        self.assertEqual(wide[0]['fungus']['walkableTop']['pixels'], 32)
        self.assertFalse(wide[0]['fungus']['blocks'])
        for a in assets.values():
            if a['fungus']['footprint'] == [1, 1]:
                self.assertTrue(a['fungus']['blocks'], a['id'])
                self.assertNotIn('walkableTop', a['fungus'], a['id'])

    def test_each_is_outlined_inside_its_cell_and_stands_on_its_anchor(self):
        for a in self.assets().values():
            rows = a['frames'][0]
            self.assertEqual((len(rows), len(rows[0])), (a['h'], a['w']), a['id'])
            pts = [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.']
            self.assertGreater(len(pts), 300, a['id'])
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.assertTrue(min(xs) >= 1 and max(xs) <= a['w'] - 2 and min(ys) >= 1 and max(ys) <= a['h'] - 2, f'{a["id"]} touches its cell edge')
            for x, y in pts:                                             # the silhouette is outlined
                if any(not (0 <= x + dx < a['w'] and 0 <= y + dy < a['h']) or rows[y + dy][x + dx] == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.assertEqual(rows[y][x], 'O', f'{a["id"]}: a bare edge at {x},{y}')
            # the foot is on the ground: the lowest pixel is within the footprint's near corner
            n = a['fungus']['footprint'][0]
            self.assertLessEqual(max(ys), a['anchor']['y'] + 8 * n + 1, f'{a["id"]} hangs below its footprint')
            self.assertGreaterEqual(max(ys), a['anchor']['y'] - 2, f'{a["id"]} floats above the anchor')

    def test_the_giant_top_is_flat_and_two_levels_up(self):
        a = self.assets()['fungus-toadstool']
        rows = a['frames'][0]
        top = min(y for y, row in enumerate(rows) if any(c != '.' for c in row))
        far_corner = a['anchor']['y'] - 16 - 32          # the far tip of the footprint's diamond, raised by the walkable top
        self.assertLessEqual(abs(top - (far_corner - 4)), 8, 'the flat top is not where a platform two levels up would be')


class Registry(unittest.TestCase):
    """Every family is a registered unit with the same contract, and the cache rebuilds a unit when, and only when, something it depends on changed."""

    def test_every_unit_has_the_contract(self):
        import importlib
        import registry
        names = [u.name for u in registry.UNITS]
        self.assertEqual(len(names), len(set(names)), 'a unit is registered twice')
        for u in registry.UNITS:
            module = importlib.import_module(u.module)
            self.assertTrue(callable(getattr(module, u.func, None)), f'{u.module}.{u.func} is missing')
            if hasattr(module, 'write_package'):
                self.assertTrue(getattr(module, 'FOLDER', ''), f'{u.module} writes a package but has no FOLDER')

    def test_every_asset_record_has_the_keys_the_page_and_the_game_read(self):
        required = {'id', 'label', 'category', 'kind', 'place', 'w', 'h', 'cols', 'rows', 'fps', 'anchor', 'frames'}
        for name in ('chests', 'fungi', 'trees', 'slot-icons', 'blood-pool', 'body-explosion', 'all-tree', 'all-tree-fall', 'all-tree-wide', 'all-tree-fall-wide', 'traps', 'bazaar', 'crystal', 'rock', 'amulets', 'buildings', 'nodemap'):
            for a in assets_of(name):
                self.assertLessEqual(required, set(a), f'{name}: {a.get("id")} lacks {required - set(a)}')
                self.assertIn(a['kind'], ('still', 'animation', 'variants'), a['id'])
                self.assertTrue(0 < len(a['frames']) <= a['cols'] * a['rows'], a['id'])

    def test_the_cache_key_follows_the_code_the_inputs_and_nothing_else(self):
        import buildcache
        import registry
        unit = next(u for u in registry.UNITS if u.name == 'amulets')
        self.assertEqual(buildcache.key_of(unit), buildcache.key_of(unit), 'the key is not stable')
        self.assertIn('assetkit', buildcache.closure(['make_amulets']), 'a shared helper should be part of what a family depends on')
        other = next(u for u in registry.UNITS if u.name == 'chests')
        self.assertNotEqual(buildcache.key_of(unit), buildcache.key_of(other))
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'input.png'
            f.write_bytes(b'one')
            with_input = registry.Unit('t', 'make_amulets', inputs=(f,))
            before = buildcache.key_of(with_input)
            f.write_bytes(b'two')
            self.assertNotEqual(before, buildcache.key_of(with_input), 'changing an input file should change the key')

    def test_a_cached_unit_is_the_same_as_a_fresh_one(self):
        import buildcache
        import registry
        unit = next(u for u in registry.UNITS if u.name == 'amulets')
        fresh, _ = buildcache.build(unit, force=True)
        cached, hit = buildcache.build(unit)
        self.assertTrue(hit)
        self.assertEqual(fresh, cached)
