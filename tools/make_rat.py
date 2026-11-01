#!/usr/bin/env python3
"""A rat, built the same way as the dog (see make_dog.py and creature.py).

Smaller and lower than the dog: a hunched body, a pointed snout, big round ears, short
legs and a long bare tail that follows the body in an S. Grey-violet fur with pink ears,
paws and tail, all palette roles, so it recolours like the other characters.

    python3 tools/make_rat.py sprites/rat [--preview sheet.png]
    python3 tools/extract_poses.py --merge rat=sprites/rat
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

RAMPS = {
    'fur': ('p', 'l', 'k', 'w'),         # steel, lavender, indigo, grape
    'cream': ('t', 'C', 'c', 'e'),
    'pink': ('c', 'e', 'f', 'g'),        # ears, paws and tail
    'nose': ('j', 'j', 'i', 'h'),
}

UPPER, LOWER = 2.2, 2.7
HIPS = {'FL': (3.0, 5.1, -1.9), 'FR': (3.0, 5.1, 1.9), 'HL': (-3.3, 5.0, -2.4), 'HR': (-3.3, 5.0, 2.4)}
KNEE_FORWARD = {'FL': False, 'FR': False, 'HL': True, 'HR': True}
PIVOT = (0.0, 5.0, 0.0)
NECK = (4.4, 6.3, 0.0)
TAIL_ROOT = (-6.4, 4.3, 0.0)
HINGE = (6.4, 5.5, 0.0)
TAIL_SEGMENTS = 6
TAIL_STEP = 1.8


def anatomy(p):
    body, head, decals = [], [], []

    # A hunched body: a small chest, a bigger rump, and a cream patch on the chest.
    body += [
        part((1.6, 5.3, 0), (4.0, 3.4, 2.9), 'fur', 'body'),
        part((-2.9, 5.0, 0), (4.3, 3.5, 3.1), 'fur', 'body'),
        part((4.6, 4.7, 0), (1.5, 2.3, 1.9), 'cream', 'body'),
        part((4.5, 6.2, 0), (2.3, 2.5, 2.2), 'fur', 'neck'),
    ]
    # A round head with a long pointed snout and a pink nose.
    head += [
        part((6.7, 6.9, 0), (3.0, 2.8, 2.7), 'fur', 'head'),
        part((9.6, 6.2, 0), (2.7, 1.5, 1.5), 'cream', 'head'),
        part((11.9, 6.3, 0), (0.9, 0.85, 0.95), 'nose', 'head'),
    ]
    jaw = rz(-deg(p['mouth']))
    for c, r, mat in (((9.2, 5.1, 0), (2.2, 0.65, 1.1), 'cream'), ((9.0, 5.6, 0), (1.6, 0.4, 0.7), 'nose')):
        if mat == 'nose' and not (p['tongue'] or p['mouth'] > 14):
            continue
        head.append(part(add(HINGE, mv(jaw, sub(c, HINGE))), r, mat, 'jaw', jaw))
    # Big round ears, set well back and out, thin like cards.
    ear_roll, ear_back = p['ears']
    for side in (-1, 1):
        head.append(part((5.6, 9.6, side * 2.5), (1.9, 2.1, 0.6), 'pink', 'ear', mm(rz(-deg(ear_back)), rx(side * deg(ear_roll)))))
    for side in (-1, 1):
        decals.append(((8.5, 8.0, side * 1.95), p['eyes']))
    return body, head, decals


def tail_parts(p):
    """A long thin tail: segments laid end to end, bending and swaying as they go."""
    a1, a2, wag = p['tail']
    out = []
    pos = TAIL_ROOT
    for i in range(TAIL_SEGMENTS):
        t = i / (TAIL_SEGMENTS - 1)
        pitch = a1 + (a2 - a1) * t
        yaw = wag * math.sin(math.pi * t) * (1 if i % 2 == 0 else 1)
        R = mm(ry(deg(yaw)), rz(-deg(pitch)))
        d = mv(R, (-1.0, 0.0, 0.0))
        centre = add(pos, tuple(x * TAIL_STEP / 2 for x in d))
        out.append(part(centre, (TAIL_STEP / 2 + 0.35, 0.62 - 0.05 * t, 0.62 - 0.05 * t), 'pink', 'tail', R))
        pos = add(pos, tuple(x * TAIL_STEP for x in d))
    return out


def place(p):
    body, head, decals = anatomy(p)
    tail = tail_parts(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    placed = []
    for q in body + tail:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))

    for name, hip in HIPS.items():
        hip_w = on_body(hip)
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, KNEE_FORWARD[name])
            toe = (foot[0] + 0.55, foot[1] + 0.5)
        else:
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.55, foot[1] + 0.5)
            knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        hind = name.startswith('H')
        placed.append(bone(hip_w[:2], knee, z, 1.5 if hind else 1.2, 'fur', 'leg' + name))
        placed.append(bone(knee, foot, z, 0.95, 'fur', 'leg' + name, grow=0.3))
        placed.append(part((toe[0], toe[1], z), (1.35, 0.7, 1.15), 'pink', 'leg' + name))

    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, mouth=0, tongue=False,
            ears=(18, 8), tail=(-4, 22, 0), feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def scurry(k, n=8):
    """A quick trot: short fast strides, the head bobbing and the tail whipping."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('FL', 0), ('HR', 0), ('FR', math.pi), ('HL', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 2.0 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -2.0 + 4.0 * u, 1.5 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.3 * math.cos(2 * phase) - 0.1, body_pitch=2.5 * math.sin(2 * phase),
                head_pitch=-2 * math.sin(2 * phase), tail=(-2, 18, 26 * math.sin(phase)), mouth=3)


class Rat:
    name = 'rat'
    kind = 'creature'
    airborne = {('attack', 1)}     # the leap
    ramps = RAMPS
    scale = 0.98      # small model: big enough for the features to be a pixel or more, small enough for the tail
    stand = pose()

    poses = {
        # crouched and ready, sniffing the air
        'charging': [pose(body_pitch=-6, lift=-0.9, head_pitch=18, mouth=4, ears=(22, 4),
                          feet={'FL': (1.4, 0), 'FR': (1.4, 0), 'HL': (-0.6, 0), 'HR': (-0.6, 0)}, tail=(10, 40, 12))],
        # crouch, leap, bite, recover
        'attack': [
            pose(body_pitch=-8, lift=-1.1, fwd=-1.3, head_pitch=12, mouth=8, ears=(26, 18),
                 feet={'FL': (-1.0, 0), 'FR': (-1.0, 0), 'HL': (1.0, 0), 'HR': (1.0, 0)}, tail=(20, 45, 0)),
            pose(body_pitch=8, lift=1.6, fwd=1.4, head_pitch=-4, mouth=30, ears=(30, 26),
                 feet={'FL': (2.2, 2.6), 'FR': (1.8, 2.9), 'HL': (-2.0, 1.4), 'HR': (-2.4, 1.8)}, tail=(-6, 18, 18)),
            pose(body_pitch=-6, lift=0.9, fwd=3.4, head_pitch=-14, mouth=38, ears=(30, 30),
                 feet={'FL': (2.0, 0.8), 'FR': (2.4, 0.4), 'HL': (-1.4, 0), 'HR': (-1.0, 0)}, tail=(0, 24, -16)),
            pose(body_pitch=2, lift=0.2, fwd=0.9, head_pitch=2, mouth=6, tail=(-2, 20, 16),
                 feet={'FL': (0.7, 0), 'FR': (1.1, 0), 'HL': (-0.7, 0), 'HR': (-1.0, 0)}),
        ],
        # rearing up on its hind legs to squeal
        'release': [pose(body_pitch=34, lift=0.8, head_pitch=18, mouth=30, ears=(14, 26), eyes='shut',
                         feet={'FL': (2.0, 5.0), 'FR': (2.4, 5.6), 'HL': (-1.2, 0), 'HR': (-1.2, 0)}, tail=(54, 72, 24))],
        # a flinch: knocked back, head thrown up and round, eyes screwed shut
        'damage': [pose(body_pitch=6, fwd=-1.2, head_pitch=22, head_yaw=18, mouth=16, ears=(48, 40), eyes='shut',
                        feet={'FL': (1.6, 0), 'FR': (1.4, 0), 'HL': (-1.6, 0), 'HR': (-1.4, 0)}, tail=(-8, 0, 0))],
        # worn out: pressed low to the floor, head hanging, tail limp
        'weak': [pose(body_pitch=-3, lift=-2.2, head_pitch=-24, mouth=3, ears=(58, 4), eyes='shut',
                      feet={'FL': (0.5, 0), 'FR': (0.5, 0), 'HL': (-0.3, 0), 'HR': (-0.3, 0)}, tail=(-6, 2, 6))],
        # on its back with its legs in the air, tail trailing
        'dead': [pose(roll=-90, lift=-2.6, head_pitch=-10, mouth=14, tongue=True, ears=(50, 14), eyes='shut',
                      tail=(-4, 0, 6),
                      feet={'FL': (0, 0, 24, -6), 'FR': (0, 0, 14, -4), 'HL': (0, 0, -22, 8), 'HR': (0, 0, -14, 5)})],
        'walking': [scurry(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Rat()

if __name__ == '__main__':
    run(CREATURE)
