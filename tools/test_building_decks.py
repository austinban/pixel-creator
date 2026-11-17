"""Tests for the flat roofs and balconies of the building kit (tools/make_building_decks.py)."""
import json
import unittest
from pathlib import Path

from buildcache import assets_of

ROOT = Path(__file__).resolve().parent.parent
ROOF = ('stone', 'timber', 'tile', 'slate', 'teal', 'plank')
BALCONY = ('stone', 'timber', 'plank')


def by_id():
    return {a['id']: a for a in assets_of('building-decks')}


class BuildingDecks(unittest.TestCase):
    def test_every_group_is_there_with_the_right_number_of_pieces(self):
        assets = by_id()
        for mat in ROOF:
            self.assertEqual(len(assets[f'bld-flat-roof-{mat}']['frames']), 10, mat)
        for mat in BALCONY:
            self.assertEqual(len(assets[f'bld-balcony-{mat}']['frames']), 7, mat)
        self.assertEqual(len(assets['bld-supports']['frames']), 3)
        self.assertEqual(len(assets), len(ROOF) + len(BALCONY) + 1)

    def test_every_piece_is_a_32_cell_in_the_buildings_category_anchored_like_the_kit(self):
        for a in by_id().values():
            self.assertEqual((a['category'], a['folder'], a['kind'], a['place'], a['w'], a['h']), ('Buildings', 'building-decks', 'variants', 'ground', 32, 32), a['id'])
            self.assertEqual(a['anchor'], {'x': 16, 'y': 24}, a['id'])
            self.assertEqual(len(a['names']), len(a['frames']), a['id'])
            for frame in a['frames']:
                self.assertEqual((len(frame), {len(r) for r in frame}), (32, {32}), a['id'])

    def test_every_piece_has_something_in_it_and_stays_inside_its_cell(self):
        for a in by_id().values():
            for name, frame in zip(a['names'], a['frames']):
                painted = [(x, y) for y, row in enumerate(frame) for x, c in enumerate(row) if c != '.']
                self.assertGreater(len(painted), 60, f"{a['id']} {name}")

    def test_the_decks_say_how_high_the_walkable_top_is(self):
        for a in by_id().values():
            b = a['buildings']
            self.assertEqual(b['role'], 'deck')
            self.assertEqual(b['deck_top'], 0.5)
            self.assertEqual(len(b['pieces']), len(a['frames']))
            self.assertEqual(a['walkable'], a['id'] != 'bld-supports')

    def test_the_two_wall_families_each_have_a_roof_and_a_balcony(self):
        assets = by_id()
        for mat in ('stone', 'timber'):
            self.assertIn(f'bld-flat-roof-{mat}', assets)
            self.assertIn(f'bld-balcony-{mat}', assets)

    def test_the_rails_are_named_for_the_sides_they_stand_on(self):
        a = by_id()['bld-balcony-stone']['buildings']
        sides = dict(zip(a['pieces'], a['sides']))
        self.assertEqual(sorted(sides['alcove-x']), ['+x', '+y', '-y'])
        self.assertEqual(sides['run-x'], ['+x'])
        self.assertEqual(sides['corner'], ['+x', '+y'])

    def test_the_kits_own_pieces_are_not_in_the_decks_and_the_other_way_round(self):
        kit = {a['id'] for a in assets_of('buildings')}
        self.assertFalse(kit & set(by_id()))

    def test_the_package_lists_every_piece(self):
        path = ROOT / 'sprites' / 'assets' / 'building-decks' / 'building-decks.json'
        if not path.exists():
            self.skipTest('the package is not built yet')
        pkg = json.load(open(path))
        self.assertEqual(sum(len(g['pieces']) for g in pkg['groups'].values()), 84)
        self.assertEqual(pkg['deck_top_levels'], 0.5)


if __name__ == '__main__':
    unittest.main()
