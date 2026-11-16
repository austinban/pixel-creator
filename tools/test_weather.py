"""The weather and fog overlays and the rain decals: sizes and frame counts as documented, loops that close, tiles that join, palette roles only, the same every time, and the
drawing advice (blend, opacity, scroll) in the records and in range."""
import unittest

from buildcache import assets_of

import extract_poses as ep

OVERLAYS = {
    # id: (tile w, tile h, frames, fps, blend)
    'weather-rain-light': (128, 128, 8, 12, 'normal'),
    'weather-rain-heavy': (128, 128, 8, 12, 'normal'),
    'weather-rain-ripples': (128, 128, 8, 8, 'normal'),
    'weather-fog-light': (128, 128, 12, 6, 'normal'),
    'weather-fog-dense': (128, 128, 12, 6, 'normal'),
    'weather-spore-haze': (128, 128, 12, 8, 'add'),
    'weather-embers': (128, 128, 12, 10, 'add'),
    'weather-petals': (128, 128, 12, 8, 'normal'),
    'weather-mist-low': (128, 64, 12, 6, 'normal'),
}
DECALS = {                       # id: (w, h, anchor x, anchor y)
    'weather-ripple-water': (32, 16, 16, 8),
    'weather-ripple-ground': (32, 16, 16, 8),
    'weather-splash': (32, 24, 16, 16),
}
FIELDS = ('weather-fog-light', 'weather-fog-dense', 'weather-spore-haze', 'weather-mist-low')       # smooth fields, made of waves
RAIN = {'weather-rain-light': (-16, 48), 'weather-rain-heavy': (-16, 48)}                          # how far a drop moves each frame (x, y)
ROLES = {c for c, *_ in ep.ROLES}


def assets():
    return {a['id']: a for a in assets_of('weather')}


def pixels(rows):
    return {(x, y): c for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.'}


def shifted(px, dx, dy, w, h):
    return {((x + dx) % w, (y + dy) % h): c for (x, y), c in px.items()}


class Overlays(unittest.TestCase):
    """The nine looping screen-space overlays (category Weather)."""

    def test_the_set_is_the_nine_overlays_and_three_decals_and_ids_are_unique(self):
        records = assets_of('weather')
        ids = [a['id'] for a in records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sorted(ids), sorted([*OVERLAYS, *DECALS]))
        self.assertEqual({a['category'] for a in records if a['id'] in OVERLAYS}, {'Weather'})
        self.assertEqual({a['category'] for a in records if a['id'] in DECALS}, {'Decals'})

    def test_tile_sizes_frame_counts_and_speeds_are_as_documented(self):
        a = assets()
        for id, (w, h, frames, fps, blend) in OVERLAYS.items():
            r = a[id]
            self.assertEqual((r['w'], r['h'], len(r['frames']), r['fps'], r['kind'], r['place']), (w, h, frames, fps, 'animation', 'none'), id)
            self.assertEqual(r['weather']['tile'], [w, h], id)
            self.assertEqual(r['weather']['blend'], blend, id)
            for f in r['frames']:
                self.assertEqual((len(f), {len(row) for row in f}), (h, {w}), id)
            self.assertEqual((r['cols'], r['rows']), (min(frames, 8), -(-frames // 8)), id)

    def test_each_overlay_is_palette_roles_only_neither_empty_nor_full(self):
        for id in OVERLAYS:
            r = assets()[id]
            for t, f in enumerate(r['frames']):
                used = set(''.join(f)) - {'.'}
                self.assertTrue(used, f'{id} frame {t} is empty')
                self.assertLessEqual(used, ROLES, f'{id} frame {t}')
                share = sum(c != '.' for row in f for c in row) / (r['w'] * r['h'])
                self.assertGreater(share, 0.005, f'{id} frame {t}')
                self.assertLess(share, 0.5, f'{id} frame {t}')

    def test_the_drawing_advice_is_in_each_record_and_in_range(self):
        for id in OVERLAYS:
            w = assets()[id]['weather']
            lo, hi = w['opacity']
            self.assertTrue(0 < lo < hi <= 1.0, id)
            self.assertIn(w['blend'], ('normal', 'add'), id)
            self.assertEqual(len(w['scroll']), 2, id)
            self.assertTrue(all(abs(v) <= 12 for v in w['scroll']), id)            # a few pixels a second, never a rush
            self.assertTrue(w['note'], id)
        # light that should glow is additive and bright; a rain streak is not
        self.assertEqual(assets()['weather-embers']['weather']['blend'], 'add')
        self.assertEqual(assets()['weather-spore-haze']['weather']['blend'], 'add')
        self.assertEqual(assets()['weather-rain-light']['weather']['blend'], 'normal')
        # fields drift by the game's scroll; falling things move by their frames
        for id in FIELDS:
            self.assertNotEqual(assets()[id]['weather']['scroll'], [0, 0], id)
        for id in (*RAIN, 'weather-embers', 'weather-rain-ripples'):
            self.assertEqual(assets()[id]['weather']['scroll'], [0, 0], id)

    def test_every_overlay_loops_the_last_frame_runs_into_the_first(self):
        for id in OVERLAYS:
            frames = [pixels(f) for f in assets()[id]['frames']]
            n = len(frames)
            steps = [len(set(frames[k]) ^ set(frames[(k + 1) % n])) for k in range(n)]
            closing, others = steps[-1], steps[:-1]
            # the step that wraps is no bigger a jump than the steps inside the loop
            self.assertLessEqual(closing, max(others) * 1.1, f'{id}: steps {steps}')
            self.assertGreater(min(steps), 0, f'{id} stands still between two frames')

    def test_rain_streaks_move_by_the_same_step_every_frame_and_close_the_loop_exactly(self):
        for id, (dx, dy) in RAIN.items():
            r = assets()[id]
            frames = [pixels(f) for f in r['frames']]
            n = len(frames)
            for k in range(n):
                self.assertEqual(shifted(frames[k], dx, dy, r['w'], r['h']), frames[(k + 1) % n], f'{id} frame {k}')

    def test_the_generators_own_loop_and_tile_checks_pass(self):
        import make_weather as m
        cover = m.check_loops()
        self.assertEqual(sorted(cover), sorted(OVERLAYS))

    def test_a_field_has_no_seam_where_it_wraps(self):
        """The mismatch between the last column and the first (and the last row and the first) is no worse than between any other neighbours."""
        for id in FIELDS:
            r = assets()[id]
            w, h = r['w'], r['h']
            seam_c = seam_r = inner_c = inner_r = 0.0
            for f in r['frames']:
                o = [[c != '.' for c in row] for row in f]
                cols = [sum(o[y][x] != o[y][(x + 1) % w] for y in range(h)) / h for x in range(w)]
                rows = [sum(o[y][x] != o[(y + 1) % h][x] for x in range(w)) / w for y in range(h)]
                seam_c += cols[-1]
                seam_r += rows[-1]
                inner_c += sum(cols[:-1]) / (w - 1)
                inner_r += sum(rows[:-1]) / (h - 1)
            self.assertLessEqual(seam_c, inner_c * 1.35, f'{id}: columns')
            self.assertLessEqual(seam_r, inner_r * 1.35, f'{id}: rows')

    def test_every_overlay_is_even_across_the_tile_not_thinner_at_the_edges(self):
        """Summed over the loop, the strips at the tile's edges (which meet when it repeats) hold about as much as the strips in the middle."""
        for id in OVERLAYS:
            r = assets()[id]
            w, h = r['w'], r['h']
            across = [0] * 8
            down = [0] * 8
            for f in r['frames']:
                for y, row in enumerate(f):
                    for x, c in enumerate(row):
                        if c != '.':
                            across[x * 8 // w] += 1
                            down[y * 8 // h] += 1
            # the low mist is documented as flat bands, thickest across the middle of the tile, so it is only judged across
            for name, strips in (('across', across),) if id == 'weather-mist-low' else (('across', across), ('down', down)):
                mean = sum(strips) / 8
                edge = (strips[0] + strips[-1]) / 2
                self.assertGreater(edge, 0.45 * mean, f'{id} is thin at the {name} edges: {strips}')
                self.assertLess(edge, 1.8 * mean, f'{id} is heavy at the {name} edges: {strips}')

    def test_it_is_the_same_every_time(self):
        import make_weather as m
        first = [(a['id'], a['frames']) for a in m.build_assets()]
        second = [(a['id'], a['frames']) for a in m.build_assets()]
        self.assertEqual(first, second)


class Decals(unittest.TestCase):
    """The rain ripples and the splash: four frames each, on a ground tile, played once where a drop lands."""

    def test_sizes_anchors_and_frames(self):
        a = assets()
        for id, (w, h, ax, ay) in DECALS.items():
            r = a[id]
            self.assertEqual((r['category'], r['kind'], r['place'], r['w'], r['h'], len(r['frames']), r['fps']), ('Decals', 'animation', 'ground', w, h, 4, 8), id)
            self.assertEqual(r['anchor'], {'x': ax, 'y': ay}, id)
            self.assertEqual(r['weather']['play'], 'once, where a drop lands', id)
            for f in r['frames']:
                self.assertEqual((len(f), {len(row) for row in f}), (h, {w}), id)

    def test_every_frame_has_something_in_it_in_palette_roles_and_the_frames_differ(self):
        for id in DECALS:
            frames = assets()[id]['frames']
            for t, f in enumerate(frames):
                used = set(''.join(f)) - {'.'}
                self.assertTrue(used, f'{id} frame {t} is empty')
                self.assertLessEqual(used, ROLES, f'{id} frame {t}')
            self.assertEqual(len({tuple(f) for f in frames}), 4, id)

    def test_a_decal_is_one_shot_so_it_does_not_have_to_loop_but_it_must_stay_on_its_tile(self):
        # a ripple lies on the tile's top face (a 32 x 16 diamond): nothing outside the diamond's bounding rows or columns, and it grows or fades rather than jumps
        for id in ('weather-ripple-water', 'weather-ripple-ground'):
            frames = [pixels(f) for f in assets()[id]['frames']]
            for t, px in enumerate(frames):
                self.assertTrue(all(0 <= x < 32 and 0 <= y < 16 for x, y in px), f'{id} frame {t}')
            sizes = [len(p) for p in frames]
            self.assertLess(sizes[0], sizes[-1], f'{id}: a ripple opens, so it has more in it at the end than at the start: {sizes}')
        # the splash is anchored where its ring is: the ring's lowest row is at or near the anchor row, the crown rises above it
        splash = [pixels(f) for f in assets()['weather-splash']['frames']]
        ay = assets()['weather-splash']['anchor']['y']
        for t, px in enumerate(splash):
            self.assertLessEqual(max(y for _, y in px), ay + 8, f'splash frame {t} hangs below its anchor')
        self.assertLess(min(y for p in splash for _, y in p), ay, 'a splash has a crown above its ring')


if __name__ == '__main__':
    unittest.main()
