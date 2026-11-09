#!/usr/bin/env python3
"""A blighted dog: the dog (see make_dog.py) with the fungus as part of its body, three features and no more.

The same body, legs, poses and animations as the dog. The fur is a sickly teal-grey (not purple, so it stands apart from the blight-alpaca), the eyes red, and:

    the ears are rose mushroom caps on cream stems, with gills under the rim; they flop and prick with the dog's own ears
    a bracket fungus (two teal shelves) is fused to the side of the near shoulder
    the tail ends in a small teal cap

Everything is palette roles, so it recolours like the rest.

    python3 tools/make_blight_dog.py --model previews/blight-dog-3d.png      look at the 3D model first
    python3 tools/make_blight_dog.py sprites/blight-dog [--preview sheet.png]
    python3 tools/extract_poses.py --merge blight-dog=sprites/blight-dog
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_dog  # noqa: E402
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402

EAR_AT = (9.2, 18.2, 3.0)       # where the dog's ears sit (make_dog.anatomy), either side of the head


def ear_caps(p):
    """Each ear is a mushroom: a short stem, gills, a wide flat cap and a cream spot, tipped by the dog's own ear angles."""
    ear_roll, ear_back = p['ears']
    out = []
    for side in (-1, 1):
        R = mm(rz(-deg(ear_back)), rx(side * deg(ear_roll)))
        c = (EAR_AT[0], EAR_AT[1], side * EAR_AT[2])

        def at(v):
            return add(c, mv(R, v))
        out += [part(at((0, 0.2, 0)), (0.8, 1.6, 0.8), 'stem', 'ear', R),
                part(at((0, 1.4, 0)), (2.1, 0.45, 2.1), 'gill', 'ear', R),
                part(at((0, 1.9, 0)), (2.3, 1.1, 2.3), 'capB', 'ear', R),
                part(at((-0.7, 2.7, 0.5 * side)), (0.55, 0.3, 0.55), 'spot', 'ear', R)]
    return out


def bracket():
    """Two shelves of bracket fungus fused to the side of the near shoulder, in the standing frame."""
    out = []
    for n, (c, r) in enumerate((((2.8, 10.7, 3.9), (2.5, 0.6, 2.0)), ((2.2, 8.9, 4.3), (2.9, 0.65, 2.3)))):
        R = rx(0.18)
        out += [part((c[0], c[1] - 0.5, c[2]), (r[0] * 0.9, 0.3, r[2] * 0.9), 'gill', 'bracket', R),
                part(c, r, 'capA', 'bracket', R)]
    return out


def tail_cap(p):
    """A small cap on the very end of the tail, carried with the tail's two segments."""
    a1, a2, _ = p['tail']
    seg1 = rz(-deg(a1))
    seg2 = mm(seg1, rz(-deg(a2 - a1)))
    end = add(add(make_dog.TAIL_ROOT, mv(seg1, (-3.2, 0.6, 0))), mv(seg2, (-3.1, 0.6, 0)))
    return [part(end, (1.5, 1.4, 1.4), 'capA', 'tailcap', seg2),
            part(add(end, mv(seg2, (-0.3, 1.1, 0.4))), (0.45, 0.3, 0.45), 'spot', 'tailcap', seg2)]


def place(p):
    """The dog without its ears, plus the fungus carried with the head, body and tail like the parts it replaces."""
    parts, decals = make_dog.place(p)
    parts = [q for q in parts if q['part'] != 'ear']
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))
    wag = ry(deg(p['tail'][2]))
    pivot, neck, root = make_dog.PIVOT, make_dog.NECK, make_dog.TAIL_ROOT

    def on_body(pt):
        return add(add(pivot, mv(g, sub(pt, pivot))), shift)

    def on_head(pt):
        return on_body(add(neck, mv(h, sub(pt, neck))))

    def on_tail(pt):
        return on_body(add(root, mv(wag, sub(pt, root))))

    for q in bracket():
        parts.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in ear_caps(p):
        parts.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    for q in tail_cap(p):
        parts.append(dict(q, c=on_tail(q['c']), R=mm(g, mm(wag, q['R']))))
    return parts, decals


class BlightDog(make_dog.Dog):
    name = 'blight-dog'
    eye_colour = 'j'      # red eyes (the palette's hot pink: there is no pure red)
    ramps = {
        'fur': ('q', 'p', 's', 'D'),             # sickly teal-grey: teal, steel, deep teal, abyss
        'dark': ('s', 'D', 'D', 'D'),
        'cream': ('t', 'q', 'p', 's'),           # a pale muzzle, chest and paws
        'nose': ('w', 'x', 'x', 'x'),
        'tongue': ('j', 'j', 'i', 'h'),
        'stem': ('t', 'C', 'b', 'a'),            # cream stems
        'gill': ('C', 'b', 'a', 'e'),            # the gills, tan
        'spot': ('t', 't', 'C', 'b'),
        'capA': ('r', 'q', 's', 'D'),            # teal fungus
        'capB': ('c', 'e', 'h', 'w'),            # rose caps
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = BlightDog()

if __name__ == '__main__':
    run(CREATURE)
