"""Tests for what the game reads: the editor's Save to sprites/ guard and the shape of assets/data.js.

    python3 -m unittest discover -s tools -p 'test_*.py'
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


class SpritesSave(unittest.TestCase):
    """The editor's Save to sprites/ never overwrites a generated set (the guard is tested in node with in-memory folders)."""

    def test_the_guard_refuses_generated_sets_and_allows_its_own(self):
        import shutil
        import subprocess
        if not shutil.which('node'):
            self.skipTest('node is not installed')
        done = subprocess.run(['node', str(Path(__file__).resolve().parent / 'test_save.js')], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


class DataFile(unittest.TestCase):
    """assets/data.js is read by the game as data: its shape is a contract."""

    @classmethod
    def setUpClass(cls):
        import json
        text = (Path(__file__).resolve().parent.parent / 'assets' / 'data.js').read_text()
        assert text.startswith('window.ASSETS = ')
        cls.data = json.loads(text[len('window.ASSETS = '):].rstrip().rstrip(';'))

    def test_it_says_which_format_it_is(self):
        import make_assets
        self.assertEqual(self.data['format'], make_assets.DATA_FORMAT)
        self.assertEqual(list(self.data)[0], 'format')

    def test_the_ids_the_game_reads_are_there_and_every_id_is_unique(self):
        ids = [a['id'] for a in self.data['assets']]
        self.assertEqual(len(ids), len(set(ids)))
        for want in ('crystal', 'rock', 'facing', 'facing-pale', 'weapon-bow-ne', 'weapon-bow-se', 'arrow-iso', 'arrow'):
            self.assertIn(want, ids)
        by = {a['id']: a for a in self.data['assets']}
        self.assertEqual((by['weapon-bow-ne']['w'], by['weapon-bow-ne']['h'], len(by['weapon-bow-ne']['frames'])), (48, 48, 4))
        self.assertEqual((by['arrow-iso']['w'], by['arrow-iso']['h'], len(by['arrow-iso']['frames'])), (28, 16, 2))
        self.assertEqual((by['arrow']['w'], by['arrow']['h']), (28, 12))
        self.assertEqual((by['facing']['w'], by['facing']['h'], by['facing']['anchor']), (20, 14, {'x': 10, 'y': 8}))

    def test_the_roles_are_the_palette(self):
        import extract_poses as ep
        self.assertEqual([r['char'] for r in self.data['roles']], [c for c, *_ in ep.ROLES])
