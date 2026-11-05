#!/usr/bin/env python3
"""A mushroom creature: a fly agaric on two little legs, with no arms, and a wide jack-o'-lantern mouth. This is the small one, in the red of a fly agaric.

A creature, not a person (see creature.py and make_dog.py): a cream stem for a body, a big red cap with white dots sitting on top, a mouth that takes up nearly the whole front of
the stem, and two short legs. The mouth is a black hollow with a dark rim and jagged teeth above and below, and it opens and closes with the pose. Walking is a waddle.
Everything is palette roles, so it recolours like the rest.

    python3 tools/make_mushroom.py --model previews/mushroom-3d.png      look at the 3D model first
    python3 tools/make_mushroom.py sprites/mushroom-small [--preview sheet.png]
    python3 tools/extract_poses.py --merge mushroom-small=sprites/mushroom-small

The large one is the same creature, bigger, in a corrupted colour scheme: make_mushroom_large.py.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

RAMPS = {
    'stem': ('t', 'C', 'b', 'a'),        # cream, sand, amber, orange: a pale stem
    'volva': ('C', 'b', 'a', 'g'),       # the swollen base, a shade darker
    'cap': ('j', 'i', 'h', 'u'),         # hot pink, magenta, dark magenta, purple: the palette's nearest to a fly agaric's red
    'gill': ('t', 'C', 'c', 'e'),        # pale gills under the cap
    'spot': ('t', 't', 'C', 'b'),        # white dots
    'maw': ('w', 'x', 'x', 'x'),         # the dark inside of the mouth
    'glow': ('x', 'O', 'O', 'O'),        # the inside of the mouth: black (the palette's outline colour, its darkest)
    'tooth': ('t', 't', 'C', 'b'),
    'foot': ('a', 'g', 'w', 'x'),        # rust feet
}

# Bones, in pixels. Two short legs under a round stem. z is the creature's right.
UPPER, LOWER = 1.9, 2.1
HIPS = {'L': (0.3, 2.9, -2.3), 'R': (0.3, 2.9, 2.3)}
PIVOT = (0.0, 7.0, 0.0)          # the body turns about its middle
CAP_PIVOT = (0.0, 14.8, 0.0)     # the cap tilts about the top of the stem
FACE_X = 4.35                    # how far the front of the stem is from the middle, at the height of the mouth
MOUTH_Y = 8.2


def surface_disc(cx, cy, cz, radii, centre, direction, size, mat, name, height=0.5):
    """A flat round dot lying on an ellipsoid's surface, at the point the unit `direction` leaves `centre` in, turned to lie flat on it."""
    d = direction
    n = math.sqrt(sum(c * c for c in d))
    d = tuple(c / n for c in d)
    pt = tuple(centre[i] + d[i] * radii[i] * 1.005 for i in range(3))
    # the surface normal of an ellipsoid at that point
    nx = tuple(d[i] / radii[i] for i in range(3))
    m = math.sqrt(sum(c * c for c in nx))
    ey = tuple(c / m for c in nx)
    ref = (0.0, 1.0, 0.0) if abs(ey[1]) < 0.9 else (1.0, 0.0, 0.0)
    ex = (ref[1] * ey[2] - ref[2] * ey[1], ref[2] * ey[0] - ref[0] * ey[2], ref[0] * ey[1] - ref[1] * ey[0])
    mx = math.sqrt(sum(c * c for c in ex))
    ex = tuple(c / mx for c in ex)
    ez = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
    R = [[ex[i], ey[i], ez[i]] for i in range(3)]
    return part(pt, (size, height, size * 0.9), mat, name, R)


def anatomy(p):
    """The creature's parts in the standing frame, by what moves together: the body, the cap (it tilts) and nothing else."""
    body, cap = [], []
    # the stem, its swollen base, and a frill under the cap
    body += [
        part((0.0, 8.0, 0.0), (4.7, 6.9, 4.5), 'stem', 'body'),
        part((0.0, 4.2, 0.0), (5.4, 3.4, 5.2), 'volva', 'body'),
        part((0.1, 14.4, 0.0), (5.4, 0.8, 5.2), 'stem', 'body'),
    ]
    # the mouth: a dark rim, a black hollow in it, and jagged teeth above and below; it opens by `mouth` (0 shut to 1 wide open)
    o = p['mouth']
    half = 1.5 + 2.7 * o
    wide = 3.0 + 1.0 * o
    body += [
        part((FACE_X - 0.2, MOUTH_Y, 0.0), (0.9, half + 0.5, wide + 0.4), 'maw', 'mouth'),
        part((FACE_X + 0.15, MOUTH_Y - 0.1, 0.0), (0.9, half - 0.2, wide - 0.5), 'glow', 'mouth'),
    ]
    for k, z in enumerate((-2.8, -1.4, 0.0, 1.4, 2.8)):
        body.append(part((FACE_X + 0.55, MOUTH_Y + half - 0.25 - (0.35 if k % 2 else 0.0), z * wide / 3.4), (0.4, 0.85, 0.5), 'tooth', 'mouth', rz(math.pi)))
    for k, z in enumerate((-2.1, -0.7, 0.7, 2.1)):
        body.append(part((FACE_X + 0.55, MOUTH_Y - half + 0.25 + (0.3 if k % 2 == 0 else 0.0), z * wide / 3.4), (0.4, 0.8, 0.5), 'tooth', 'mouth'))
    # the cap: wide and tall, with a lip, gills under it and white dots on it
    dome = ((0.0, 17.0, 0.0), (10.4, 6.8, 10.4))
    cap += [
        part(dome[0], dome[1], 'cap', 'cap'),
        part((0.0, 15.7, 0.0), (11.0, 1.4, 11.0), 'cap', 'cap'),
        part((0.0, 15.0, 0.0), (9.8, 0.7, 9.8), 'gill', 'gill'),
    ]
    for k, (az, el, size) in enumerate(((0, 88, 2.4), (45, 62, 2.0), (160, 64, 2.2), (250, 60, 2.1), (330, 68, 1.9),
                                        (100, 38, 1.9), (215, 34, 2.0), (300, 32, 1.9), (10, 30, 1.7), (65, 22, 1.5), (160, 24, 1.6), (355, 16, 1.4))):
        a, e = math.radians(az), math.radians(el)
        direction = (math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a))
        cap.append(surface_disc(0, 0, 0, dome[1], dome[0], direction, size, 'spot', 'spot%d' % k))
    return body, cap


def place(p):
    """The mushroom in a pose: parts carried to where the pose puts them."""
    body, cap = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    c = mm(rx(deg(p['cap_roll'])), rz(deg(p['cap_tilt'])))      # the cap, about the top of the stem

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_cap(pt):
        return on_body(add(CAP_PIVOT, mv(c, sub(pt, CAP_PIVOT))))

    placed = [dict(q, c=on_body(q['c']), R=mm(g, q['R'])) for q in body]
    placed += [dict(q, c=on_cap(q['c']), R=mm(g, mm(c, q['R']))) for q in cap]
    for name, hip in HIPS.items():
        hip_w = on_body(hip)
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, True)
            toe = (foot[0] + 0.7, foot[1] + 0.6)
        else:
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.7, foot[1] + 0.6)
            knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.5, 'stem', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.3, 'stem', 'leg' + name, grow=0.4))
        placed.append(part((toe[0], toe[1], z), (2.0, 0.95, 1.6), 'foot', 'leg' + name))
    return placed, []


# --- poses -------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, mouth=0.3, cap_tilt=0, cap_roll=0, feet={})


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def waddle(k, n=8):
    """One frame of a waddle: the legs take turns, the whole body rocks from side to side and bobs, the cap lags behind."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('L', 0), ('R', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 1.8 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -1.8 + 3.6 * u, 1.6 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.45 * abs(math.sin(phase)) - 0.1, body_pitch=2.0 * math.sin(phase), cap_tilt=-4 * math.sin(phase), cap_roll=5 * math.cos(phase),
                mouth=0.3 + 0.1 * math.sin(2 * phase))


class Mushroom:
    name = 'mushroom-small'
    kind = 'creature'
    airborne = {('attack', 1)}       # the lunge
    ramps = RAMPS
    scale = 0.66                     # the small one; the large one (make_mushroom_large.py) is 0.9
    stand = pose()

    poses = {
        # ready: the mouth a little open, weight on both feet
        'charging': [pose(mouth=0.4, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # a lunge: crouch, spring at the target jaws wide, bite, recover
        'attack': [
            pose(lift=-1.8, body_pitch=8, fwd=-1.4, mouth=0.15, cap_tilt=10, feet={'L': (-0.6, 0), 'R': (-0.6, 0)}),
            pose(lift=1.8, body_pitch=-8, fwd=1.8, mouth=1.0, cap_tilt=-10, feet={'L': (1.4, 2.0), 'R': (1.0, 2.4)}),
            pose(lift=0.4, body_pitch=-14, fwd=4.0, mouth=0.85, cap_tilt=-14, feet={'L': (1.8, 0.6), 'R': (1.6, 0)}),
            pose(lift=0.0, body_pitch=0, fwd=1.0, mouth=0.35, cap_tilt=3, feet={'L': (0.6, 0), 'R': (0.6, 0)}),
        ],
        # a roar: leaning back, mouth wide open, the cap thrown back
        'release': [pose(lift=0.6, body_pitch=12, mouth=1.0, cap_tilt=14, feet={'L': (-0.6, 0), 'R': (-0.6, 0)})],
        # a flinch: squashed down and knocked back, the cap pushed over
        'damage': [pose(lift=-2.2, body_pitch=9, fwd=-1.4, mouth=0.7, cap_tilt=10, cap_roll=12, feet={'L': (0.6, 0), 'R': (-0.4, 0)})],
        # worn out: sagging, the cap drooping, the mouth shut
        'weak': [pose(lift=-2.8, body_pitch=-4, mouth=0.05, cap_tilt=-16, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # on its side, legs out
        'dead': [pose(roll=-90, lift=-3.4, mouth=0.6, cap_tilt=6,
                      feet={'L': (0, 0, 22, -6), 'R': (0, 0, 14, -4)})],
        'walking': [waddle(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Mushroom()

if __name__ == '__main__':
    run(CREATURE)
