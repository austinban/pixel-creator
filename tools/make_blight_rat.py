#!/usr/bin/env python3
"""A blighted rat: the rat (see make_rat.py) with the fungus as part of its body, two features and no more.

The same body, legs, tail, poses and animations as the rat. The fur is a dusty rose-mauve (so it stands apart from the grey rat, the grey-teal blight-dog and the purple blight-alpaca), the nose a dark plum, the eyes red, and:

    one big teal mushroom cap grows out of the skull like a hat, on a short stem, with the tan gills showing under its rim (it takes the place of the ears)
    the tail ends in a small rose cap

Everything is palette roles, so it recolours like the rest.

    python3 tools/make_blight_rat.py --model previews/blight-rat-3d.png      look at the 3D model first
    python3 tools/make_blight_rat.py sprites/blight-rat [--preview sheet.png]
    python3 tools/extract_poses.py --merge blight-rat=sprites/blight-rat
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_rat  # noqa: E402
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402


def hat():
    """The cap on the skull, in the head's standing frame: a stem, gills and a wide cap with two cream spots."""
    return [part((6.4, 9.3, 0), (0.95, 1.5, 0.95), 'stem', 'hat'),
            part((6.4, 10.8, 0), (2.9, 0.5, 2.9), 'gill', 'hat'),
            part((6.4, 11.5, 0), (3.1, 1.6, 3.1), 'capA', 'hat'),
            part((5.4, 12.9, -0.9), (0.7, 0.35, 0.7), 'spot', 'hat'),
            part((7.3, 12.7, 1.2), (0.55, 0.3, 0.55), 'spot', 'hat')]


def place(p):
    """The rat without its ears, plus the cap carried with the head, and a small cap on the end of the tail."""
    parts, decals = make_rat.place(p)
    parts = [q for q in parts if q['part'] != 'ear']
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))
    pivot, neck = make_rat.PIVOT, make_rat.NECK

    def on_body(pt):
        return add(add(pivot, mv(g, sub(pt, pivot))), shift)

    def on_head(pt):
        return on_body(add(neck, mv(h, sub(pt, neck))))

    tip = [q for q in parts if q['part'] == 'tail'][-1]          # the last tail segment, already in place
    end = add(tip['c'], mv(tip['R'], (-make_rat.TAIL_STEP / 2 - 0.4, 0, 0)))
    parts += [part(end, (1.1, 1.0, 1.0), 'capB', 'tailcap', tip['R']),
              part(add(end, mv(tip['R'], (-0.2, 0.8, 0.3))), (0.35, 0.25, 0.35), 'spot', 'tailcap', tip['R'])]
    for q in hat():
        parts.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    return parts, decals


class BlightRat(make_rat.Rat):
    name = 'blight-rat'
    eye_colour = 'j'      # red eyes (the palette's hot pink: there is no pure red)
    ramps = {
        'fur': ('c', 'e', 'f', 'g'),             # dusty rose-mauve: salmon, coral, orchid, plum
        'cream': ('t', 'C', 'c', 'e'),           # a pale muzzle and chest
        'pink': ('f', 'g', 'w', 'x'),            # paws and tail, a dark plum
        'nose': ('g', 'w', 'x', 'x'),            # a dark plum nose
        'stem': ('t', 'C', 'b', 'a'),            # cream stem
        'gill': ('C', 'b', 'a', 'e'),            # the gills, tan
        'spot': ('t', 't', 'C', 'b'),
        'capA': ('r', 'q', 's', 'D'),            # the hat: teal
        'capB': ('y', 'i', 'h', 'w'),            # the tail cap: magenta
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = BlightRat()

if __name__ == '__main__':
    run(CREATURE)
