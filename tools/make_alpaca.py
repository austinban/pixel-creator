#!/usr/bin/env python3
"""An alpaca: a four-legged creature built like the dog (see make_dog.py and creature.py).

A round woolly body on long thin legs, a tall slim neck, a small head with a topknot of wool and banana ears, and a short upturned tail.
Legs are solved with two-bone inverse kinematics; walking is a diagonal-pair walk. Its attack is a spit and headbutt. Colours are palette roles.

    python3 tools/make_alpaca.py --model previews/alpaca-3d.png      look at the 3D model first
    python3 tools/make_alpaca.py sprites/alpaca [--preview sheet.png]
    python3 tools/extract_poses.py --merge alpaca=sprites/alpaca
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

# Colour ramps by role: lit, base, shade, deep. Wool is cream and fawn; the face and legs are a darker fawn; hooves and nose are dark.
RAMPS = {
    'wool': ('t', 'C', 'b', 'a'),
    'face': ('C', 'b', 'a', 'g'),
    'hoof': ('l', 'k', 'w', 'x'),
    'nose': ('w', 'x', 'x', 'x'),
}

# Bones, in pixels. Hips are (x, y, z); z is the alpaca's right. Long thin legs under a round woolly body.
UPPER, LOWER = 4.7, 5.2
HIPS = {'FL': (4.4, 9.4, -2.3), 'FR': (4.4, 9.4, 2.3), 'HL': (-4.6, 9.2, -2.4), 'HR': (-4.6, 9.2, 2.4)}
KNEE_FORWARD = {'FL': False, 'FR': False, 'HL': True, 'HR': True}   # elbows point back, stifles forward
PIVOT = (0.0, 9.5, 0.0)      # the body turns about its middle
NECK = (9.6, 23.4, 0.0)      # the head turns about the top of the neck
TAIL_ROOT = (-8.4, 12.4, 0.0)
HINGE = (12.4, 24.4, 0.0)    # the jaw


def anatomy(p, extras=None):
    """The alpaca's parts in the standing frame, tagged by which group of parts moves together."""
    body, head, tail, decals = [], [], [], []

    # Body: a round woolly barrel, a fluffy back, and a long upright neck in wool.
    body += [
        part((1.2, 10.9, 0), (6.2, 4.7, 4.5), 'wool', 'body'),
        part((-3.8, 10.6, 0), (4.6, 4.3, 4.2), 'wool', 'body'),
        part((0.8, 14.6, 0), (4.6, 1.5, 3.1), 'wool', 'body'),            # the fluffy ridge of the back
        part((-3.6, 14.2, 0), (3.2, 1.3, 2.7), 'wool', 'body'),
        part((6.2, 13.0, 0), (3.1, 3.4, 3.1), 'wool', 'neck', rz(-0.3)),     # the base of the neck, thick with wool
        part((7.2, 17.0, 0), (2.9, 3.2, 2.8), 'wool', 'neck', rz(-0.2)),     # the neck rising in a fluffy column
        part((8.3, 21.0, 0), (2.6, 3.2, 2.5), 'wool', 'neck', rz(-0.15)),    # still fluffy above
        part((8.9, 22.6, 0), (3.0, 1.9, 2.9), 'wool', 'neck'),               # a big woolly collar under the head
        part((6.6, 15.2, 0), (1.6, 1.4, 3.2), 'wool', 'neck'),               # and tufts standing out at the sides
        part((7.8, 19.0, 0), (1.5, 1.3, 3.1), 'wool', 'neck'),
    ]
    # Head: small and narrow, with a topknot of wool, a short muzzle and a dark nose.
    head += [
        part((10.8, 26.0, 0), (2.9, 2.5, 2.3), 'face', 'head'),
        part((13.3, 25.0, 0), (2.0, 1.45, 1.55), 'face', 'head'),
        part((15.0, 25.2, 0), (0.7, 0.6, 0.95), 'nose', 'head'),
        part((10.0, 28.0, 0), (3.0, 1.9, 2.9), 'wool', 'head'),
    ]
    # The lower jaw drops a little about its hinge.
    jaw = rz(-deg(p['mouth']))
    head.append(part(add(HINGE, mv(jaw, sub((13.2, 23.9, 0), HINGE))), (2.0, 0.6, 1.2), 'face', 'jaw', jaw))
    # Small banana ears, tipped out and back.
    ear_roll, ear_back = p['ears']
    for side in (-1, 1):
        head.append(part((9.2, 29.4, side * 1.7), (0.8, 2.3, 0.7), 'face', 'ear', mm(rz(-deg(ear_back)), rx(side * deg(ear_roll)))))
    # Eyes are single pixels laid on the head after it is drawn.
    for side in (-1, 1):
        decals.append(((12.4, 26.6, side * 2.1), p['eyes']))

    # The tail: a short upturned tuft, turned about its root.
    a1, a2, _ = p['tail']
    seg1 = rz(-deg(a1))
    c1 = add(TAIL_ROOT, mv(seg1, (-1.4, 0.5, 0)))
    tail += [part(c1, (1.9, 1.4, 1.3), 'wool', 'tail', seg1)]
    if extras:                                  # a variant adds parts of its own: (body parts, head parts)
        more_body, more_head = extras(p)
        body += more_body
        head += more_head
    return body, head, tail, decals


def place(p, extras=None):
    """The alpaca in a pose: parts and decals carried to where the pose puts them."""
    body, head, tail, decals = anatomy(p, extras)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))     # the whole body
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))  # the head, about the top of the neck
    wag = ry(deg(p['tail'][2]))                               # the tail, about its root

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    def on_tail(pt):
        return on_body(add(TAIL_ROOT, mv(wag, sub(pt, TAIL_ROOT))))

    placed = []
    for q in body:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    for q in tail:
        placed.append(dict(q, c=on_tail(q['c']), R=mm(g, mm(wag, q['R']))))

    for name, hip in HIPS.items():
        hip_w = on_body(hip)
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, KNEE_FORWARD[name])
            toe = (foot[0] + 0.6, foot[1] + 0.7)       # a hoof sits a little ahead of the ankle
        else:
            # Raw angles from the hip, carried with the body (used lying down).
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.6, foot[1] + 0.7)
            knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.6, 'wool', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.25, 'face', 'leg' + name, grow=0.4))
        placed.append(part((toe[0], toe[1], z), (1.5, 0.85, 1.3), 'hoof', 'leg' + name))

    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, mouth=0, tongue=False,
            ears=(18, 12), tail=(30, 40, 0), feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def trot(k, n=8):
    """One frame of a trot: diagonal pairs swing together."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('FL', 0), ('HR', 0), ('FR', math.pi), ('HL', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:                      # on the ground, sliding back
            dx, lift = 3.0 * (1 - 2 * s / math.pi), 0.0
        else:                                # swinging forward through the air
            u = (s - math.pi) / math.pi
            dx, lift = -3.0 + 6.0 * u, 2.4 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.45 * math.cos(2 * phase) - 0.2, body_pitch=2 * math.sin(2 * phase),
                head_pitch=-1.5 * math.sin(2 * phase), tail=(40, 55, 14 * math.sin(phase)), mouth=5)


def walk(k, n=8):
    """One frame of a walk: diagonal pairs swing together, a little slower and higher than a trot."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('FL', 0), ('HR', 0), ('FR', math.pi), ('HL', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:                      # on the ground, sliding back
            dx, lift = 2.6 * (1 - 2 * s / math.pi), 0.0
        else:                                # swinging forward through the air
            u = (s - math.pi) / math.pi
            dx, lift = -2.6 + 5.2 * u, 2.2 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.4 * math.cos(2 * phase) - 0.2, body_pitch=1.5 * math.sin(2 * phase),
                head_pitch=-3 * math.sin(2 * phase) - 2, tail=(34, 40, 8 * math.sin(phase)))


class Alpaca:
    eye_colour = 'j'      # red eyes (the palette's hot pink: there is no pure red)
    name = 'alpaca'
    kind = 'creature'
    airborne = set()
    ramps = RAMPS
    scale = 0.7       # keeps the tall neck inside the cell
    stand = pose()

    poses = {
        # alert: the head up and forward, ears pricked, weight on all four feet
        'charging': [pose(head_pitch=-8, ears=(8, -6), feet={'FL': (1.6, 0), 'FR': (1.6, 0), 'HL': (-1.2, 0), 'HR': (-1.2, 0)}, tail=(44, 50, 0))],
        # a spit and headbutt: the head pulls back, thrusts forward and down, then returns
        'attack': [
            pose(body_pitch=6, lift=-0.6, fwd=-1.6, head_pitch=22, mouth=2, ears=(36, 46),
                 feet={'FL': (-1.0, 0), 'FR': (-1.0, 0), 'HL': (1.0, 0), 'HR': (1.0, 0)}),
            pose(body_pitch=-5, lift=-0.2, fwd=1.0, head_pitch=-26, mouth=20, ears=(40, 58),
                 feet={'FL': (1.4, 0), 'FR': (1.4, 0), 'HL': (-1.0, 0), 'HR': (-1.0, 0)}),
            pose(body_pitch=-8, lift=-0.2, fwd=2.6, head_pitch=-40, mouth=26, ears=(40, 62),
                 feet={'FL': (2.2, 0), 'FR': (2.2, 0), 'HL': (-1.6, 0), 'HR': (-1.6, 0)}),
            pose(body_pitch=0, fwd=0.8, head_pitch=-6, mouth=6, ears=(24, 24),
                 feet={'FL': (0.8, 0), 'FR': (0.8, 0), 'HL': (-0.8, 0), 'HR': (-0.8, 0)}),
        ],
        # a hum of alarm: head thrown up, mouth open
        'release': [pose(body_pitch=7, lift=0.3, head_pitch=34, mouth=22, ears=(14, 34), eyes='shut',
                         feet={'FL': (0.4, 0), 'FR': (0.4, 0), 'HL': (-1.6, 0), 'HR': (-1.6, 0)}, tail=(46, 60, 0))],
        # a flinch: knocked back, head wrenched round, ears flat
        'damage': [pose(body_pitch=5, fwd=-1.6, head_pitch=14, head_yaw=18, mouth=10, ears=(60, 56), eyes='shut',
                        feet={'FL': (2.0, 0), 'FR': (1.8, 0), 'HL': (-2.0, 0), 'HR': (-1.8, 0)}, tail=(-10, 0, 0))],
        # worn out: sagging, head hanging low
        'weak': [pose(body_pitch=-3, lift=-3.0, head_pitch=-46, mouth=4, ears=(70, 8), eyes='shut',
                      feet={'FL': (0.6, 0), 'FR': (0.6, 0), 'HL': (-0.4, 0), 'HR': (-0.4, 0)}, tail=(-12, 0, 0))],
        # lying on its side, legs out stiff
        'dead': [pose(roll=-90, lift=-3.8, head_pitch=-14, mouth=10, ears=(60, 20), eyes='shut',
                      tail=(-6, 0, 0),
                      feet={'FL': (0, 0, 24, -6), 'FR': (0, 0, 14, -4), 'HL': (0, 0, -22, 8), 'HR': (0, 0, -14, 5)})],
        'walking': [walk(k) for k in range(8)],
    }

    extras = None     # a variant sets this to add parts (see make_blight_alpaca.py)

    def place(self, p):
        return place(p, self.extras)


CREATURE = Alpaca()

if __name__ == '__main__':
    run(CREATURE)
