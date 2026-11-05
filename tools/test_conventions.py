"""Tests for the conventions checker: it must pass what is right and catch what is wrong.

    python3 -m unittest discover -s tools -p 'test_*.py'

A check that cannot fail protects nothing, so each rule is shown a good frame and a broken one.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions as cv  # noqa: E402


def bases():
    return {c['id']: c for c in cv.load_bases()['characters']}


class OriginalsFollowTheRules(unittest.TestCase):
    """The rules were measured from the six originals, so they must pass every one."""

    def test_each_original_passes(self):
        for name in ('cleric', 'fighter', 'mage', 'skeleton', 'zombie', 'knight'):
            self.assertEqual(cv.check_base(name, bases()[name]['frames']), [], name)

    def test_generated_bases_pass(self):
        for name in ('human', 'slim', 'ninja', 'dog', 'rat'):
            airborne = getattr(cv.creator_of(name), 'airborne', set())
            self.assertEqual(cv.check_base(name, bases()[name]['frames'], airborne=airborne), [], name)


class FloatersHaveTheirOwnGroundRules(unittest.TestCase):
    """A floater hangs below the ground line and bobs in a band; a person's feet-on-row-27 rule does not apply to it."""

    def frame(self, low, height=26):
        rows = ['.' * 32 for _ in range(32)]
        for y in range(low - height + 1, low + 1):
            rows[y] = '.' + 'O' * 10 + 'a' * 9 + 'O' * 10 + '..'
        return rows

    def ground_problems(self, low, kind):
        return [p for p in cv.check_frame(self.frame(low), 'charging', kind) if 'lowest row' in p or 'feet' in p]

    def test_a_floater_may_hang_below_the_ground_line(self):
        self.assertEqual(self.ground_problems(30, 'floater'), [])
        self.assertTrue(self.ground_problems(30, 'humanoid'))

    def test_a_floater_does_not_rest_on_the_ground_line(self):
        self.assertTrue(self.ground_problems(27, 'floater'))

    def test_the_hover_may_bob_only_so_far(self):
        ok = {'walkingSE': [self.frame(29), self.frame(31)]}
        self.assertEqual(cv.check_hover('x', ok), [])
        far = {'walkingSE': [self.frame(28, 20), self.frame(31, 20), self.frame(27, 20)]}
        self.assertTrue(cv.check_hover('x', far))

    @unittest.skipUnless('spirit' in bases(), 'the spirit base is not built here')
    def test_the_spirit_passes_as_a_floater(self):
        self.assertEqual(cv.kind_of('spirit'), 'floater')
        self.assertEqual(cv.check_base('spirit', bases()['spirit']['frames']), [])


class BreakingARuleIsCaught(unittest.TestCase):
    def setUp(self):
        self.frames = copy.deepcopy(bases()['knight']['frames'])

    def problems(self):
        return cv.check_base('knight', self.frames)

    def test_feet_off_the_ground(self):
        self.frames['chargingSE'][0] = ['.' * 32] * 3 + self.frames['chargingSE'][0][:-3]
        self.assertTrue(any('feet are on row' in p for p in self.problems()))

    def test_touching_the_edge(self):
        row = list(self.frames['chargingSE'][0][10])
        row[0] = 'O'
        self.frames['chargingSE'][0][10] = ''.join(row)
        self.assertTrue(any('keep inside columns' in p for p in self.problems()))

    def test_missing_outline(self):
        # swap every outline pixel of one frame for a body colour
        self.frames['chargingSE'][0] = [line.replace('O', 'a') for line in self.frames['chargingSE'][0]]
        self.assertTrue(any('not outlined' in p for p in self.problems()))

    def test_too_light(self):
        lines = self.frames['attackSE'][0]
        self.frames['attackSE'][0] = [l if y > 20 else '.' * 32 for y, l in enumerate(lines)]
        self.assertTrue(any('too light' in p or 'painted pixels' in p for p in self.problems()))

    def test_too_tall_for_the_pose(self):
        # a slump that stands as tall as a standing figure
        self.frames['weakSE'][0] = self.frames['chargingSE'][0]
        self.assertTrue(any('rows tall' in p and 'weakSE' in p for p in self.problems()))

    def test_not_leaning_into_the_attack(self):
        # the strike frame leaning back as far as the wind-up does
        self.frames['attackSE'][2] = self.frames['attackSE'][0]
        self.assertTrue(any('leans' in p and 'attackSE frame 3' in p for p in self.problems()))

    def test_lean_message_says_which_way(self):
        self.frames['attackSE'][2] = self.frames['attackSE'][0]
        message = next(p for p in self.problems() if 'attackSE frame 3' in p and 'leans' in p)
        self.assertIn('lean further into it', message)

    def test_off_centre(self):
        self.frames['chargingSE'][0] = [('.' * 6 + l)[:32] for l in self.frames['chargingSE'][0]]
        self.assertTrue(any('off centre' in p for p in self.problems()))


class TheWalk(unittest.TestCase):
    def setUp(self):
        self.frames = copy.deepcopy(bases()['knight']['frames'])

    def problems(self):
        return [p for p in cv.check_walk('knight', self.frames)]

    def test_a_head_that_swings_forward_and_back_is_caught(self):
        # every other frame shoved three columns over, the way a rocking walk moves the head
        self.frames['walkingSE'] = [[('.' * 3 + l)[:32] for l in f] if i % 2 else f for i, f in enumerate(self.frames['walkingSE'])]
        self.assertTrue(any('the head moves' in p for p in self.problems()))

    def test_a_walk_with_no_bob_is_caught(self):
        self.frames['walkingSE'] = [self.frames['walkingSE'][0]] * 8
        found = self.problems()
        self.assertTrue(any('bobs' in p for p in found))
        self.assertTrue(any('feet slide only' in p for p in found))

    def test_feet_swinging_through_the_air_are_caught(self):
        raised = [f[2:] + ['.' * 32] * 2 for f in self.frames['walkingSE'][:4]]      # moved up two rows
        self.frames['walkingSE'] = raised + self.frames['walkingSE'][4:]
        self.assertTrue(any('leave the ground' in p for p in self.problems()))

    def test_feet_that_jump_back_and_forth_are_a_stutter(self):
        # every other frame, the bottom three rows (the feet) shoved three columns over
        def jitter(lines):
            low = max(y for y, l in enumerate(lines) if l.strip('.'))
            return [(('.' * 3 + l)[:32] if y > low - 3 else l) for y, l in enumerate(lines)]
        self.frames['walkingNE'] = [jitter(f) if i % 2 else f for i, f in enumerate(self.frames['walkingNE'])]
        self.assertTrue(any('the walk stutters' in p for p in cv.check_walk('knight', self.frames)))

    def test_the_originals_do_not_stutter(self):
        for name in ('cleric', 'fighter', 'mage', 'skeleton', 'zombie', 'knight'):
            self.assertEqual([p for p in cv.check_walk(name, bases()[name]['frames']) if 'stutters' in p], [], name)

    def test_a_bob_that_does_not_repeat_is_caught(self):
        frames = self.frames['walkingSE']
        self.frames['walkingSE'] = frames[:4] + [['.' * 32] * 4 + f[:-4] for f in frames[4:]]
        self.assertTrue(any('repeat every 4 frames' in p for p in self.problems()))


class Builds(unittest.TestCase):
    def test_slim_is_a_declared_choice_that_allows_less_weight_than_standard(self):
        self.assertLess(cv.BUILDS['slim'], cv.BUILDS['standard'])
        self.assertEqual(set(cv.BASE_BUILDS.values()) - set(cv.BUILDS), set())

    def test_only_the_slim_build_gets_the_allowance(self):
        frames = {'chargingSE': [bases()['knight']['frames']['chargingSE'][0]]}
        mass = len(cv.painted(frames['chargingSE'][0]))
        saved = cv.MASS['charging']
        try:
            # make this frame weigh 86% of the lightest original: under the standard 92%, over the slim 80%
            cv.MASS['charging'] = (mass / 0.86, mass / 0.86 * 1.4)
            standard = [p for p in cv.check_movement('knight', frames) if 'too light' in p]
            slim = [p for p in cv.check_movement('slim', frames) if 'too light' in p]
        finally:
            cv.MASS['charging'] = saved
        self.assertTrue(standard)
        self.assertEqual(slim, [])


class The3DPreview(unittest.TestCase):
    def test_a_preview_is_drawn_from_every_view(self):
        import preview3d
        creature = cv.creator_of('human')
        parts, decals = creature.place(preview3d.pick_pose(creature))
        for view in preview3d.VIEWS:
            tile = preview3d.render_view(parts, decals, creature.ramps, preview3d.VIEWS[view], size=120)
            self.assertEqual(tile.size, (120, 120))
            alpha = tile.getchannel('A')
            filled = sum(1 for v in alpha.getdata() if v > 0)
            self.assertGreater(filled, 1500, view)             # something is there
            self.assertLess(filled, 120 * 120 * 0.8, view)      # and it is a figure, not a wall of colour

    def test_a_creator_can_make_a_preview_without_making_sprites(self):
        import preview3d
        for name in ('human', 'dog'):
            sheet = preview3d.render_sheet(cv.creator_of(name), preview3d.pick_pose(cv.creator_of(name)), ['face', 'SE'], size=100)
            self.assertEqual(sheet.size, (200, 118))


class RampsAndWeapons(unittest.TestCase):
    def test_ramp_must_go_light_to_dark(self):
        self.assertTrue(cv.check_ramps({'fur': ('f', 'e', 'a', 'b')}, 'x'))          # dark to light
        self.assertEqual(cv.check_ramps({'fur': ('b', 'a', 'e', 'f')}, 'x'), [])

    def test_ramp_needs_four_palette_roles(self):
        self.assertTrue(cv.check_ramps({'fur': ('b', 'a', 'e')}, 'x'))
        self.assertTrue(cv.check_ramps({'fur': ('b', 'a', 'e', '#')}, 'x'))

    def test_weapon_strips_are_the_right_size_and_share_a_swing(self):
        folder = cv.ROOT / 'sprites' / 'weapons'
        if folder.is_dir():
            self.assertEqual(cv.check_weapons(folder), [])

    def test_a_weapon_strip_of_the_wrong_size_is_caught(self):
        import tempfile

        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGBA', (128, 32), (255, 0, 0, 255)).save(Path(d) / 'axe-attackNE.png')
            Image.new('RGBA', (192, 48), (255, 0, 0, 255)).save(Path(d) / 'axe-attackSE.png')
            self.assertTrue(any('a strip is' in p for p in cv.check_weapons(d)))


class TheHeldWeapon(unittest.TestCase):
    def test_a_humans_hand_is_on_the_weapon(self):
        folder = cv.ROOT / 'sprites' / 'weapons'
        if folder.is_dir():
            self.assertEqual(cv.check_hand_path(cv.creator_of('human'), folder), [])

    def test_a_hand_in_the_wrong_place_is_caught(self):
        folder = cv.ROOT / 'sprites' / 'weapons'
        if not folder.is_dir():
            self.skipTest('no weapon strips')
        human = copy.deepcopy(cv.creator_of('human'))
        human.poses['attackSE'] = copy.deepcopy(human.poses['attackSE'])
        human.poses['attackSE'][2]['hands']['L'] = (-5.0, -5.0)      # behind the body instead of striking
        self.assertTrue(any('attackSE frame 3' in p for p in cv.check_hand_path(human, folder)))


class WeaponIcons(unittest.TestCase):
    """Every weapon has a 32 x 32 display icon, tied to it by name, and an icon is never left without its weapon."""

    def test_each_icon_is_a_painted_32_square_inside_the_cell(self):
        import make_weapon_icons as wi
        for a in wi.build_icon_assets():
            rows = a['frames'][0]
            self.assertEqual((len(rows), {len(r) for r in rows}), (32, {32}), a['id'])
            painted = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
            self.assertGreater(len(painted), 80, a['id'])
            self.assertTrue(all(0 <= x < 32 and 0 <= y < 32 for x, y in painted), a['id'])
            self.assertIn('O', ''.join(rows), f"{a['id']} has no outline")

    def test_a_weapon_without_an_icon_and_an_icon_without_a_weapon_are_both_caught(self):
        import make_weapon_icons as wi
        strips = [{'id': f'weapon-axe-{f}', 'weapon': 'Axe', 'category': 'Weapons'} for f in ('ne', 'se')]
        icon = {'id': 'icon-weapon-axe', 'icon_for': 'axe'}
        self.assertEqual(wi.link_icons(strips + [icon]), [])
        self.assertEqual({a['icon'] for a in strips}, {'icon-weapon-axe'})
        self.assertTrue(any('has no display icon' in p for p in wi.link_icons([dict(a) for a in strips])))
        self.assertTrue(any('no such weapon' in p for p in wi.link_icons([icon])))

    def test_every_weapon_in_the_built_assets_has_its_icon(self):
        import json
        path = cv.ROOT / 'assets' / 'data.js'
        if not path.exists():
            self.skipTest('assets are not built')
        text = path.read_text()
        data = json.loads(text[text.index('{'):text.rindex('}') + 1])
        by_id = {a['id']: a for a in data['assets']}
        weapons = [a for a in data['assets'] if a.get('weapon')]
        self.assertTrue(weapons)
        for a in weapons:
            self.assertIn(a.get('icon'), by_id, f"{a['id']} has no display icon")
            self.assertEqual(by_id[a['icon']]['icon_for'], a['id'][len('weapon-'):-3], a['id'])


class AbilityAnimations(unittest.TestCase):
    """The ability animations: grouped, every ability tied to sheets that exist, every sheet inside its cell, and the pieces that must line up do."""

    WANTED = ['crimson-bolt', 'sanguine-burst', 'spore-cloud', 'static-surge', 'downpour', 'quake', 'tremor', 'raise', 'lower', 'stone-wall', 'shove',
              'rally', 'inspire', 'cleanse', 'sever', 'ward', 'climb', 'dash', 'mark', 'silence', 'stun', 'charm', 'confuse',
              'blink', 'swap', 'call-wolf', 'call-decoy', 'raise-guardian', 'mire', 'slick-ground', 'fire-wall']

    def assets(self):
        import make_abilities as ma
        return {a['id']: a for a in ma.build_assets()}

    def test_every_ability_in_the_kit_is_covered_and_names_sheets_that_exist(self):
        import make_abilities as ma
        have = self.assets()
        for name in self.WANTED:
            self.assertIn(name, ma.ABILITIES, name)
            for e in ma.ABILITIES[name]['effects']:
                self.assertIn(e['sheet'], have, f'{name} plays {e["sheet"]}, which is not there')
        for name, e in list(ma.STATUSES.items()) + [(k, r['effects'][0]) for k, r in ma.REUSED.items()]:
            self.assertTrue(e['sheet'] in have or e['sheet'] == 'vine', f'{name} plays {e["sheet"]}')
        self.assertEqual(set(ma.REUSED), {'root', 'hook'})

    def test_the_sheets_are_grouped_named_and_unique(self):
        import make_abilities as ma
        assets = ma.build_assets()
        self.assertEqual(len({a['id'] for a in assets}), len(assets))
        for a in assets:
            self.assertEqual((a['category'], a['folder']), ('Abilities', 'abilities'), a['id'])
            self.assertEqual(a['kind'], 'animation', a['id'])
            self.assertEqual(len(a['frames']), a['cols'] * a['rows'], a['id'])

    def test_every_frame_is_the_size_of_its_cell_and_in_the_palette(self):
        import extract_poses as ep
        known = {c for c, *_ in ep.ROLES}
        for a in self.assets().values():
            for rows in a['frames']:
                self.assertEqual(len(rows), a['h'], a['id'])
                self.assertTrue(all(len(r) == a['w'] for r in rows), a['id'])
                self.assertTrue(set(''.join(rows)) <= known | {'.'}, a['id'])
            self.assertTrue(0 <= a['anchor']['x'] < a['w'] and 0 <= a['anchor']['y'] < a['h'], a['id'] + ' anchor')

    def test_every_frame_has_something_in_it_and_a_burst_dies_away(self):
        for a in self.assets().values():
            counts = [sum(ch != '.' for r in rows for ch in r) for rows in a['frames']]
            self.assertTrue(all(c > 0 for c in counts), f'{a["id"]} has an empty frame: {counts}')
            if a['id'].startswith('burst-'):
                self.assertLess(counts[-1], 0.6 * max(counts), f'{a["id"]} does not fade out')
                self.assertGreater(counts[1], counts[0] * 0.8, a['id'] + ' does not start small and grow')

    def test_appear_is_vanish_backwards(self):
        have = self.assets()
        for colour in ('violet', 'blue', 'yellow', 'stone'):
            self.assertEqual(have['appear-' + colour]['frames'], list(reversed(have['vanish-' + colour]['frames'])), colour)

    def test_the_mire_and_the_slick_join_the_next_plot(self):
        """Two ground tiles side by side agree wherever their diamonds overlap, so five of them are one surface."""
        import make_ground_fx as gf
        have = self.assets()
        for name in ('surface-mire', 'surface-slick'):
            for frame in have[name]['frames']:
                for dx, dy in ((16, 8), (16, -8)):
                    for y in range(gf.H):
                        for x in range(gf.W):
                            nx, ny = x + dx, y + dy
                            ax, ay = gf.ANCHOR
                            if 0 <= nx < gf.W and 0 <= ny < gf.H and abs(x + 0.5 - ax) / 16 + abs(y + 0.5 - ay) / 8 < 0.97 and abs(nx + 0.5 - ax) / 16 + abs(ny + 0.5 - ay) / 8 < 0.97:
                                self.assertEqual(frame[y][x], frame[ny][nx], f'{name} does not join at ({x}, {y})')

    def test_a_looping_sheet_comes_back_to_where_it_started(self):
        """The ground loops are periodic in their frame count: the frame after the last one is the first."""
        import make_ground_fx as gf
        for kind in ('mire', 'slick', 'firewall'):
            draw = gf.KINDS[kind][1]
            self.assertEqual(draw(0), draw(gf.FRAMES), kind)

    def test_the_package_matches_the_table(self):
        import json
        import tempfile
        import make_abilities as ma
        with tempfile.TemporaryDirectory() as d:
            ma.write_package(d)
            data = json.loads((Path(d) / 'abilities.json').read_text())
            readme = (Path(d) / 'README.md').read_text()
        self.assertEqual(set(data['abilities']), set(ma.ABILITIES))
        self.assertEqual(set(data['sheets']), set(self.assets()))
        self.assertEqual(len(data['offsets']['radius1']), 5)
        self.assertEqual(len(data['offsets']['radius2']), 13)
        for name in data['sheets']:
            self.assertIn(f'`{name}.png`', readme, name + ' is not in the README')


class Traps(unittest.TestCase):
    """The traps: grouped, each placed and triggered, inside the cell, and the triggered animation starts like the placed trap and ends changed."""

    def test_the_assets_are_grouped_and_named(self):
        import make_traps as mt
        assets = {a['id']: a for a in mt.build_assets()}
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
        for a in mt.build_assets():
            for rows in a['frames']:
                self.assertEqual(len(rows), 32)
                self.assertTrue(all(len(r) == 32 for r in rows))
                self.assertTrue(set(''.join(rows)) <= known | {'.'})
                painted = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != '.']
                self.assertTrue(painted, a['id'])
                self.assertTrue(all(1 <= x <= 30 and 1 <= y <= 30 for x, y in painted), a['id'] + ' reaches the edge of its cell')

    def test_a_triggered_animation_changes_and_the_last_frame_is_not_the_placed_trap(self):
        import make_traps as mt
        for name in mt.TRAPS:
            placed, anim = mt.frames_of(name)
            self.assertEqual(len({tuple(f) for f in anim}), len(anim), name + ' repeats a frame')
            self.assertNotEqual(anim[-1], placed, name + ' ends the way it began')


class NodeMap(unittest.TestCase):
    """The node-map tiles: grouped under one name, 16 distinct shore tiles whose neighbours join, and the README's recipe really draws a map."""

    def test_the_assets_are_grouped_and_named(self):
        import make_nodemap as nm
        assets = nm.build_assets()
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
        assets = mb.build_assets()
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


if __name__ == '__main__':
    unittest.main()


class EyesAreTallSlits(unittest.TestCase):
    """Every person's open eyes are tall vertical slits, not dots."""

    def test_every_person_has_tall_eyes(self):
        for name in cv.CREATORS:
            creator = cv.creator_of(name)
            if getattr(creator, 'kind', 'humanoid') == 'humanoid':
                self.assertEqual(cv.check_eyes(creator, name), [], name)

    def test_dot_eyes_are_caught(self):
        class Dotty:
            kind = 'humanoid'
            tall_eyes = False
        self.assertTrue(cv.check_eyes(Dotty(), 'dotty'))

    def test_other_creatures_are_not_asked(self):
        class Beast:
            kind = 'creature'
        self.assertEqual(cv.check_eyes(Beast(), 'beast'), [])


class EveryPersonHasTheBow(unittest.TestCase):
    """The bow animation is standard: a generated person without it is caught."""

    def test_generated_people_have_it(self):
        for name, ch in ((c['id'], c) for c in cv.load_bases()['characters']):
            self.assertEqual(cv.check_bow(name, ch['frames']), [], name)

    def test_missing_bow_is_caught(self):
        frames = {k: v for k, v in bases()['slim']['frames'].items() if not k.startswith('bow')}
        self.assertTrue(cv.check_bow('slim', frames))

    def test_exempt_and_original_characters_are_not_asked(self):
        self.assertEqual(cv.check_bow('undead', {}), [])
        self.assertEqual(cv.check_bow('knight', {}), [])
        self.assertEqual(cv.check_bow('rat', {}), [])
