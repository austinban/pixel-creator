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
        for name in ('chests', 'traps', 'bazaar', 'crystal', 'rock', 'amulets', 'buildings', 'nodemap'):
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
