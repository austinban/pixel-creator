"""Tests for the ability animations: sizes, anchors, frame counts and the table that says which ability plays what.

    python3 -m unittest discover -s tools -p 'test_*.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


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
