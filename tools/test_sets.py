"""The terrain sets: every piece a set names exists and fits its ground, the generated files are up to date, and the terrain builder's script is sound."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

import make_sets as M
import sets as S

ROOT = Path(__file__).resolve().parent.parent


class Sets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = M.load_data()
        cls.doc = M.document(cls.data)

    def test_the_definitions_have_no_problems(self):
        self.assertEqual(M.problems(self.data), [])

    def test_every_set_has_something_to_scatter_and_something_to_stand_on(self):
        for sid, s in self.doc['sets'].items():
            scatter = [i for g in s['scatter']['groups'] for i in self.doc['groups'][g['group']]['ids']]
            self.assertTrue(scatter, sid)
            feats = [i for g in s['features']['groups'] for i in self.doc['groups'][g['group']]['ids']]
            self.assertTrue(feats, sid)
            self.assertGreater(len(s['grass']), 0, sid)
            for g in s['grass']:
                self.assertIn(g['id'], self.data, sid)

    def test_every_feature_has_a_footprint_the_builder_can_place(self):
        for sid, s in self.doc['sets'].items():
            for g in s['features']['groups']:
                for i in self.doc['groups'][g['group']]['ids']:
                    a = self.data[i]
                    self.assertIn('footprint', a, f'{sid}: {i}')
                    cells = {tuple(c) for c in a['footprint']['cells']}
                    self.assertTrue(cells, i)

    def test_scatter_pieces_are_one_cell_and_water_pieces_stand_in_water(self):
        for sid, s in self.doc['sets'].items():
            for g in s['scatter']['groups']:
                for i in self.doc['groups'][g['group']]['ids']:
                    cells = self.data[i].get('footprint', {'cells': [[0, 0]]})['cells']
                    self.assertEqual(len(cells), 1, f'{sid}: {i} is in the scatter layer but covers {len(cells)} cells')
            for g in (s['water'] or {'groups': []})['groups']:
                for i in self.doc['groups'][g['group']]['ids']:
                    self.assertEqual(self.data[i].get('surface'), 'water', f'{sid}: {i}')
            for d in s['decals']:
                for i in self.doc['groups'][d['group']]['ids']:
                    a = self.data[i]
                    want = {'water': 'water', 'shore': 'shore'}.get(d['on'])
                    if want:
                        self.assertEqual(a.get('surface'), want, f'{sid}: {i}')

    def test_a_bridge_group_has_whole_walkable_spans_the_builder_can_lay(self):
        for sid, s in self.doc['sets'].items():
            if s['bridge'] and s['bridge'] != 'bridge-plank':
                for i in self.doc['groups'][s['bridge']]['ids']:
                    a = self.data[i]
                    self.assertTrue(a['walkable'] and a['run'] in ('x', 'y'), f'{sid}: {i}')
                    self.assertIn(max(a['footprint']['size']), (3, 5), i)

    def test_every_overlay_names_its_blend_and_opacity(self):
        for gid, g in self.doc['groups'].items():
            if g['role'] == 'overlay':
                for i in g['ids']:
                    w = self.data[i]['weather']
                    self.assertIn(w['blend'], ('normal', 'add'), i)
                    self.assertLess(w['opacity'][0], w['opacity'][1] + 1e-9, i)

    def test_a_set_keeps_to_its_ground(self):
        for sid, s in self.doc['sets'].items():
            sheet = S.GROUNDS[s['ground']]['sheet']
            for g in s['grass']:
                self.assertTrue(g['id'].startswith(sheet + '-'), sid)
            for layer in ('scatter', 'features'):
                for g in s[layer]['groups']:
                    self.assertIn(self.doc['groups'][g['group']]['fits'], ('any', s['ground']), f'{sid}: {g["group"]}')

    def test_the_corrupted_sets_use_clean_turf_not_the_mushroom_block_as_the_floor(self):
        for sid, s in self.doc['sets'].items():
            if s['ground'] == 'corrupted':
                weights = {tuple(g['cell']): g['weight'] for g in s['grass']}
                clean = sum(w for c, w in weights.items() if c in S.CLEAN_GRASS)
                self.assertGreater(clean, 3 * weights.get((0, 0), 0), sid)

    def test_twins_have_the_same_footprints_where_both_are_rocks(self):
        for a, b in S.TWINS:
            if a.startswith('rocks-') and b.startswith('rocks-'):
                fa = {tuple(self.data[i]['footprint']['size']) for i in S.resolve(a, self.data)}
                fb = {tuple(self.data[i]['footprint']['size']) for i in S.resolve(b, self.data)}
                self.assertTrue(fa & fb, (a, b))

    def test_the_generated_files_are_up_to_date(self):
        for path, make in M.OUTPUTS.items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_text(), make(self.doc), f'{path.relative_to(ROOT)} is out of date: run python3 tools/make_sets.py')

    def test_the_page_reads_what_the_file_has(self):
        text = (ROOT / 'assets' / 'sets.js').read_text()
        self.assertEqual(json.loads(text[text.index('{'):text.rindex('}') + 1]), self.doc)
        html = (ROOT / 'terrain.html').read_text()
        self.assertIn('assets/sets.js', html)
        self.assertIn('id="set"', html)

    @unittest.skipUnless(shutil.which('node'), 'node is not installed')
    def test_the_terrain_script_parses(self):
        subprocess.run(['node', '--check', str(ROOT / 'terrain.js')], check=True)


if __name__ == '__main__':
    unittest.main()
