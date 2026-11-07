"""Tests for the corrupted ground: it follows the original sheet cell for cell, stays on the palette, and has its plain grass blocks.

    python3 -m unittest discover -s tools -p 'test_*.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


class CorruptedGround(unittest.TestCase):
    """The corrupted ground is the original sheet cell for cell: the same tiles in the same places, on the palette, with only a little drawn over the outlines."""

    @classmethod
    def setUpClass(cls):
        import make_ground as mg
        import make_corrupted_ground as mc
        mc.ensure_sheet()
        cls.mg, cls.mc = mg, mc
        cls.original = {a['id']: a for a in mg.build_ground_assets()}
        cls.corrupted = mg.build_corrupted_assets()
        cls.plain_ids = {f'ground-corrupted-{c}-{r}' for c, r in mc.CLEAN_GRASS}

    def test_every_corrupted_tile_has_an_original_in_the_same_cell(self):
        self.assertGreater(len(self.corrupted), 100)
        for a in self.corrupted:
            if a['id'] in self.plain_ids:
                continue
            o = self.original['ground-' + a['id'][len('ground-corrupted-'):]]
            self.assertEqual((a['w'], a['h']), (o['w'], o['h']), a['id'])
            self.assertEqual(a['category'], 'Corrupted ' + o['category'], a['id'])
        cats = {a['category'] for a in self.corrupted}
        self.assertLessEqual({'Corrupted Grass', 'Corrupted Water'}, cats)

    def test_a_block_keeps_its_shape(self):
        # Nothing of the original's outline is lost, and what is added past it (a mushroom cap, a spore) is small.
        for a in self.corrupted:
            if a['category'] == 'Corrupted Nature' or a['id'] in self.plain_ids:
                continue
            o = self.original['ground-' + a['id'][len('ground-corrupted-'):]]
            lost = extra = 0
            for ra, ro in zip(a['frames'][0], o['frames'][0]):
                for ca, co in zip(ra, ro):
                    lost += co != '.' and ca == '.'
                    extra += co == '.' and ca != '.'
            self.assertEqual(lost, 0, a['id'])
            self.assertLessEqual(extra, 45, a['id'])

    def test_it_is_teal_and_purple_not_green_and_orange(self):
        import collections
        count = collections.Counter(''.join(''.join(r) for a in self.corrupted if a['category'] in ('Corrupted Grass', 'Corrupted Dirt') for r in a['frames'][0]))
        total = sum(v for k, v in count.items() if k != '.')
        green_orange = sum(count[k] for k in 'zABabde')
        self.assertLess(green_orange / total, 0.03)

    def test_the_plain_grass_blocks_have_the_mushroom_blocks_shape_and_no_decoration(self):
        by_id = {a['id']: a for a in self.corrupted}
        accent = by_id['ground-corrupted-0-0']['frames'][0]
        sil = lambda rows: [''.join('#' if ch != '.' else '.' for ch in r) for r in rows]
        seen = set()
        for cell in self.mc.CLEAN_GRASS:
            a = by_id['ground-corrupted-%d-%d' % cell]
            self.assertEqual((a['category'], a['w'], a['h']), ('Corrupted Grass', 32, 32))
            self.assertEqual(sil(a['frames'][0]), sil(self.original['ground-0-0']['frames'][0]), a['id'] + ' has another shape than the plain (0, 0) block')
            # no mushroom, vine, thorn or eye: only the turf, earth and the two turf glints
            self.assertLessEqual(set(''.join(a['frames'][0])) - {'.'}, set('qsklpwxurDg'), a['id'])
            seen.add(tuple(a['frames'][0]))
        self.assertEqual(len(seen), len(self.mc.CLEAN_GRASS), 'the plain blocks should differ from each other')
        self.assertNotIn(tuple(accent), seen)
        for cell in self.mc.CLEAN_GRASS:      # the cells were empty in the original, and the accent block is still where it was
            self.assertNotIn('ground-%d-%d' % cell, self.original)
        self.assertIn('ground-corrupted-0-0', by_id)

    def test_there_are_mushrooms_and_vines(self):
        # caps and vine colours that the original tiles never used on their own: violet, pink, orchid-lit teal
        import collections
        count = collections.Counter(c for a in self.corrupted for r in a['frames'][0] for c in r)
        for role in 'vjr':
            self.assertGreater(count[role], 40, role)
