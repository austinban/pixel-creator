"""The wood scaffold stairs: the same 24 pieces as the stone stairs in footprint, height, direction and walkability, with no rail on the stepped ones."""
import unittest

from buildcache import assets_of


class ScaffoldStairs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scaffold = {a['id']: a for a in assets_of('scaffold-stairs')}
        cls.stone = {a['id']: a for a in assets_of('stairs')}

    def twin(self, a):
        return self.stone[a['twin']]

    def test_there_is_one_scaffold_for_every_stone_stair_ramp_and_ledge_ramp(self):
        self.assertEqual(len(self.scaffold), 24)
        self.assertEqual(sorted(a['twin'] for a in self.scaffold.values()), sorted(self.stone))
        for sid, a in self.scaffold.items():
            self.assertTrue(sid.startswith('scaffold-'), sid)
            self.assertEqual((a['category'], a['kind'], a['place'], a['folder'], a['style']), ('Stairs', 'still', 'ground', 'scaffold-stairs', 'timber'), sid)

    def test_each_matches_its_stone_twin_in_footprint_height_direction_and_run(self):
        for a in self.scaffold.values():
            t = self.twin(a)
            self.assertEqual(a['footprint'], t['footprint'], a['id'])
            self.assertEqual(a['levels'], t['levels'], a['id'])
            self.assertEqual(a['connector'], t['connector'], a['id'])
            self.assertEqual(a['w'], t['w'], a['id'])
            self.assertEqual(a['anchor']['x'], t['anchor']['x'], a['id'])

    def test_every_piece_is_walkable_over_its_whole_footprint(self):
        for a in self.scaffold.values():
            cells = {f'{i},{j}' for i, j in a['footprint']['cells']}
            self.assertEqual(set(a['top_cover']), cells, a['id'])
            self.assertTrue(a['walkable'], a['id'])
            self.assertGreaterEqual(min(a['top_cover'].values()), 0.6, a['id'])

    def test_the_stepped_stairs_have_no_rail_and_the_ramps_do(self):
        for a in self.scaffold.values():
            t = self.twin(a)
            if a['connector']['kind'] == 'stair':
                self.assertEqual(a['h'], t['h'], f'{a["id"]}: nothing stands higher than the top step')
                self.assertEqual(min(a['top_cover'].values()), 1.0, a['id'])        # no post stands on a tread
            else:
                self.assertGreater(a['h'], t['h'], f'{a["id"]}: a ramp has its back rail')

    def test_they_are_open_underneath_so_the_ground_shows_through(self):
        for a in self.scaffold.values():
            if a['connector']['kind'] != 'stair':
                continue                                                               # the ramps have a rail, which a solid ramp lacks
            rows = a['frames'][0]
            filled = sum(c != '.' for r in rows for c in r)
            t = self.twin(a)
            stone = sum(c != '.' for r in t['frames'][0] for c in r)
            self.assertLess(filled, stone, f'{a["id"]}: a scaffold stair has fewer pixels than the solid stone one')

    def test_the_variants_differ_and_it_is_the_same_every_time(self):
        self.assertEqual(len({tuple(a['frames'][0]) for a in self.scaffold.values()}), 24)
        import make_scaffold_stairs as m
        self.assertEqual([x['frames'] for x in m.build_assets()], [x['frames'] for x in m.build_assets()])

    def test_the_package_lists_every_piece_with_its_stone_twin(self):
        import json
        import tempfile
        import make_scaffold_stairs as m
        with tempfile.TemporaryDirectory() as d:
            m.write_package(d)
            pkg = json.load(open(f'{d}/scaffold-stairs.json'))
        self.assertEqual(sorted(pkg['pieces']), sorted(self.scaffold))
        for sid, p in pkg['pieces'].items():
            self.assertEqual(p['stone_twin'], self.scaffold[sid]['twin'])


if __name__ == '__main__':
    unittest.main()
