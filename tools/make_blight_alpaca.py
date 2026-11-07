#!/usr/bin/env python3
"""A blighted alpaca: the alpaca (see make_alpaca.py) gone purple and corrupted, with mushrooms growing out of it.

The same body, legs, poses and animations as the alpaca, so everything carries over. What changes is the colour (purple wool, a darker face, dark hooves, red eyes)
and what grows on it: seven tall mushrooms with big caps: three on the back and rump, two on the neck, and two on the head. None grow from the flanks.
Some caps are teal, some magenta, with cream stems and spots. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_blight_alpaca.py --model previews/blight-alpaca-3d.png      look at the 3D model first
    python3 tools/make_blight_alpaca.py sprites/blight-alpaca [--preview sheet.png]
    python3 tools/extract_poses.py --merge blight-alpaca=sprites/blight-alpaca
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_alpaca  # noqa: E402

from creature import part, rx, rz, run  # noqa: E402

# A mushroom: (where its stem starts in the standing frame, which way it leans: (roll about x, tilt about z), the cap's size, the cap's colour).
BODY_MUSHROOMS = [
    ((2.6, 15.2, 0.6), (0.1, -0.1), 3.0, 'capA'),          # the big one over the shoulders
    ((-2.4, 15.0, -1.0), (-0.2, 0.15), 2.4, 'capB'),
    ((-6.0, 13.8, 0.8), (0.2, 0.35), 2.0, 'capA'),         # on the rump
    ((6.6, 15.0, 2.2), (-0.5, -0.2), 1.8, 'capB'),         # the neck
    ((7.6, 19.4, -2.2), (0.6, -0.1), 1.6, 'capA'),
]
HEAD_MUSHROOMS = [
    ((10.0, 29.2, 0.6), (0.1, -0.15), 2.0, 'capA'),         # on the topknot
    ((11.6, 27.0, -2.4), (0.8, 0.1), 1.4, 'capB'),
]


def mushroom(at, lean, size, cap, n):
    """A stem and a flat cap with a cream spot, leaning by `lean`, in the standing frame."""
    roll, tilt = lean
    R = None
    from creature import mm
    R = mm(rx(roll), rz(tilt))
    stem_len = 1.6 + size * 1.1
    x, y, z = at
    parts = [
        part((x, y + stem_len * 0.5 * 0.9, z), (0.75, stem_len * 0.6, 0.75), 'stem', f'mush{n}', R),
        part((x, y + stem_len, z), (size, size * 0.5, size), cap, f'cap{n}', R),
        part((x - size * 0.25, y + stem_len + size * 0.42, z + size * 0.2), (size * 0.28, size * 0.2, size * 0.28), 'spot', f'cap{n}', R),
    ]
    return parts


def extras(p):
    body, head = [], []
    for n, (at, lean, size, cap) in enumerate(BODY_MUSHROOMS):
        body += mushroom(at, lean, size, cap, n)
    for n, (at, lean, size, cap) in enumerate(HEAD_MUSHROOMS):
        head += mushroom(at, lean, size, cap, 20 + n)
    return body, head


class BlightAlpaca(make_alpaca.Alpaca):
    name = 'blight-alpaca'
    ramps = {
        'wool': ('f', 'u', 'w', 'x'),            # purple wool: orchid, purple, grape, eggplant
        'face': ('u', 'w', 'x', 'x'),            # a darker, greyer face and legs
        'hoof': ('k', 'w', 'x', 'x'),
        'nose': ('w', 'x', 'x', 'x'),
        'stem': ('t', 'C', 'b', 'a'),            # cream stems
        'spot': ('t', 't', 'C', 'b'),
        'capA': ('r', 'q', 's', 'k'),            # teal caps
        'capB': ('y', 'i', 'h', 'u'),            # magenta caps
    }
    extras = staticmethod(extras)


CREATURE = BlightAlpaca()

if __name__ == '__main__':
    run(CREATURE)
