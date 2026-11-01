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


if __name__ == '__main__':
    unittest.main()
