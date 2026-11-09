#!/usr/bin/env python3
"""A mushroom mantis: the mantis (see make_mantis.py) as a fungus-grown hunter, with the mushroom part of its anatomy.

The same body, legs, poses and animations as the mantis, so everything carries over. What changes is the colour (moss-green chitin, cream bands, glowing cyan eyes)
and two grown-in features, not growths stuck on its back:
    a crown      a wide orange-red cap sits on the head like a hood, with cream gills under its rim; the eyes stay clear below it
    blades       a shelf of bracket fungus runs down each scythe forearm in place of the spines, orange-red on top and cream beneath

    python3 tools/make_mushroom_mantis.py --model previews/mushroom-mantis-3d.png      look at the 3D model first
    python3 tools/make_mushroom_mantis.py sprites/mushroom-mantis [--preview sheet.png]
    python3 tools/extract_poses.py --merge mushroom-mantis=sprites/mushroom-mantis
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_mantis  # noqa: E402
from creature import deg, part, run, rz  # noqa: E402

ORIGINAL_ANATOMY, ORIGINAL_ARMS = make_mantis.anatomy, make_mantis.arms


def anatomy(p):
    body, head, decals = ORIGINAL_ANATOMY(p)
    tilt = rz(deg(-8))
    head += [
        part((3.1, 13.6, 0.0), (3.1, 0.75, 3.1), 'gill', 'crown', tilt),                # the gills, under the rim
        part((3.0, 14.1, 0.0), (3.0, 1.15, 3.0), 'cap', 'crown', tilt),                 # the cap, a hood over the head
        part((2.4, 15.0, 0.9), (0.7, 0.3, 0.7), 'spot', 'crown', tilt),
    ]
    return body, head, decals


def arms(on_body, p):
    """The mantis's arms, with the spines taken off and a bracket fungus growing along each forearm instead."""
    keep = [q for q in ORIGINAL_ARMS(on_body, p) if not q['part'].startswith('spine')]
    a1, a2, reach = p['arms']
    out = keep
    import math
    for side in (-1, 1):
        shoulder = (make_mantis.SHOULDER[0], make_mantis.SHOULDER[1], side * make_mantis.SHOULDER[2])
        d1 = (math.cos(deg(a1)), math.sin(deg(a1)))
        elbow = (shoulder[0] + make_mantis.FEMUR * d1[0] + reach * 0.3, shoulder[1] + make_mantis.FEMUR * d1[1], side * (make_mantis.SHOULDER[2] + 0.6))
        d2 = (math.cos(deg(a2)), math.sin(deg(a2)))
        wrist = (elbow[0] + make_mantis.TIBIA * d2[0] + reach * 0.4, elbow[1] + make_mantis.TIBIA * d2[1], side * (make_mantis.SHOULDER[2] + 0.5))
        for k, t in enumerate((0.3, 0.55, 0.8)):             # three shelves, smaller toward the wrist
            at = (elbow[0] + (wrist[0] - elbow[0]) * t, elbow[1] + (wrist[1] - elbow[1]) * t, elbow[2] - side * 0.45)
            size = 1.0 - 0.2 * k
            c = on_body((at[0] - 0.35 * d2[1], at[1] + 0.35 * d2[0], at[2]))
            out.append(part(c, (0.5 * size + 0.3, 0.3 * size + 0.15, 0.95 * size), 'cap', f'shelf{side}{k}'))
            out.append(part((c[0], c[1] - 0.25, c[2]), (0.45 * size + 0.3, 0.18, 0.8 * size), 'gill', f'shelf{side}{k}'))
    return out


def place(p):
    make_mantis.anatomy, make_mantis.arms = anatomy, arms          # the mantis's own place(), carrying the crown and shelves with it
    try:
        return make_mantis.place(p)
    finally:
        make_mantis.anatomy, make_mantis.arms = ORIGINAL_ANATOMY, ORIGINAL_ARMS


class MushroomMantis(make_mantis.Mantis):
    name = 'mushroom-mantis'
    ramps = {
        'body': ('z', 'A', 'B', 's'),        # moss green: lime, green, emerald, deep teal
        'stripe': ('t', 'C', 'b', 'a'),      # cream bands and the feet
        'eye': ('r', 'o', 'o', 'n'),         # glowing cyan eyes
        'limb': ('A', 'B', 's', 'D'),
        'cap': ('b', 'a', 'e', 'h'),         # orange-red caps: amber, orange, coral, dark magenta
        'gill': ('t', 'C', 'b', 'a'),        # cream gills
        'spot': ('t', 't', 'C', 'b'),
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = MushroomMantis()

if __name__ == '__main__':
    run(CREATURE)
