"""The one preview tool draws any family's sheets, labelled, at game scale and 2x.

    python3 -m unittest discover -s tools -p 'test_*.py'
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preview  # noqa: E402


class Preview(unittest.TestCase):
    def test_it_draws_a_ground_sheet_and_an_icon(self):
        with tempfile.TemporaryDirectory() as scratch:
            out = Path(scratch) / 'p.png'
            self.assertEqual(preview.main(["trap-snare-triggered", "item-recurve_bow", "--out", str(out)]), 0)
            from PIL import Image
            image = Image.open(out)
            # Six frames of 32 + padding, at 1x and 2x, is wider than three times one cell.
            self.assertGreater(image.width, 6 * 32 * 3)
            self.assertGreater(image.height, 32 * 2 * 2)

    def test_an_unknown_id_draws_nothing(self):
        self.assertEqual(preview.main(['no-such-asset', '--out', '/tmp/never.png']), 1)


if __name__ == '__main__':
    unittest.main()
