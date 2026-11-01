#!/usr/bin/env python3
"""A generic dog: the worked example of a creature built with creature.py.

The other bases are painted over the humanoid fighter; a dog has a different body, so it is
modelled from scratch. Body, neck, head, snout, jaw, ears, tail and four legs are ellipsoids.
Legs are solved with two-bone inverse kinematics, so a paw stays where the pose puts it on the
ground and the knees bend the way a dog's do. Walking is a trot: diagonal pairs of legs swing
together. Colours are palette roles, so the dog recolours like the other characters.

    python3 tools/make_dog.py sprites/dog [--preview sheet.png]
    python3 tools/extract_poses.py --merge dog=sprites/dog

To make another four-legged creature, copy this file and change the proportions, the colour
ramps and the poses; for something with a different body, build its own `place`.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

# Colour ramps by role: lit, base, shade, deep. Fur is warm and rose; the muzzle and paws
# are cream.
RAMPS = {
    'fur': ('b', 'a', 'e', 'f'),
    'dark': ('a', 'e', 'f', 'g'),
    'cream': ('t', 'C', 'c', 'e'),
    'nose': ('l', 'k', 'w', 'w'),
    'tongue': ('j', 'j', 'i', 'h'),
}

# Bones, in pixels. Hips are (x, y, z); z is the dog's right.
UPPER, LOWER = 4.0, 4.5
HIPS = {'FL': (5.0, 8.8, -2.8), 'FR': (5.0, 8.8, 2.8), 'HL': (-5.2, 8.6, -2.9), 'HR': (-5.2, 8.6, 2.9)}
KNEE_FORWARD = {'FL': False, 'FR': False, 'HL': True, 'HR': True}   # elbows point back, stifles forward
PIVOT = (0.0, 8.0, 0.0)      # the body turns about its middle
NECK = (7.8, 11.5, 0.0)      # the head turns about the base of the neck
TAIL_ROOT = (-8.2, 10.0, 0.0)
HINGE = (11.5, 11.4, 0.0)    # the jaw


def anatomy(p):
    """The dog's parts in the standing frame, tagged by which group of parts moves together."""
    body, head, tail, decals = [], [], [], []

    # Body: a deep chest, a slimmer rump, a cream patch on the chest, and the neck.
    body += [
        part((3.0, 8.6, 0), (5.4, 5.0, 4.1), 'fur', 'body'),
        part((-3.4, 8.4, 0), (5.0, 4.6, 3.9), 'fur', 'body'),
        part((7.4, 8.2, 0), (2.0, 3.4, 2.7), 'cream', 'body'),
        part((7.6, 11.8, 0), (3.2, 3.7, 3.1), 'fur', 'neck'),
    ]
    # Head, snout and nose.
    head += [
        part((10.8, 14.2, 0), (4.8, 4.4, 4.2), 'fur', 'head'),
        part((14.9, 12.9, 0), (3.3, 2.2, 2.3), 'cream', 'head'),
        part((17.7, 13.4, 0), (1.15, 1.05, 1.35), 'nose', 'head'),
    ]
    # The lower jaw drops about its hinge, with a tongue when the mouth is open.
    jaw = rz(-deg(p['mouth']))
    for c, r, mat in (((14.0, 10.9, 0), (3.0, 1.0, 1.8), 'cream'), ((13.6, 11.5, 0), (2.4, 0.55, 1.1), 'tongue')):
        if mat == 'tongue' and not (p['tongue'] or p['mouth'] > 14):
            continue
        head.append(part(add(HINGE, mv(jaw, sub(c, HINGE))), r, mat, 'jaw', jaw))
    # Ears, tipped out and back; flopped ears are tipped further.
    ear_roll, ear_back = p['ears']
    for side in (-1, 1):
        head.append(part((9.2, 18.2, side * 3.0), (1.5, 2.6, 1.1), 'dark', 'ear', mm(rz(-deg(ear_back)), rx(side * deg(ear_roll)))))
    # Eyes are single pixels laid on the head after it is drawn.
    for side in (-1, 1):
        decals.append(((14.0, 15.2, side * 2.8), p['eyes']))

    # The tail: two short segments, turned about its root. Positive angles lift it.
    a1, a2, _ = p['tail']
    seg1 = rz(-deg(a1))
    seg2 = mm(seg1, rz(-deg(a2 - a1)))
    c1 = add(TAIL_ROOT, mv(seg1, (-1.7, 0.4, 0)))
    c2 = add(add(TAIL_ROOT, mv(seg1, (-3.2, 0.6, 0))), mv(seg2, (-1.6, 0.3, 0)))
    tail += [part(c1, (2.3, 1.15, 1.15), 'fur', 'tail', seg1), part(c2, (2.0, 1.0, 1.0), 'dark', 'tail', seg2)]
    return body, head, tail, decals


def place(p):
    """The dog in a pose: parts and decals carried to where the pose puts them."""
    body, head, tail, decals = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))     # the whole body
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))  # the head, about the neck
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
            # Where the paw goes: ahead of the hip by dx, and this high off the ground.
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, KNEE_FORWARD[name])
            toe = (foot[0] + 0.9, foot[1] + 0.8)       # a paw sits a little ahead of the ankle
        else:
            # Raw angles from the hip, carried with the body (used lying down).
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.9, foot[1] + 0.8)
            knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.9, 'fur', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.7, 'fur', 'leg' + name, grow=0.4))
        placed.append(part((toe[0], toe[1], z), (2.1, 1.05, 1.8), 'cream', 'leg' + name))

    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, mouth=0, tongue=False,
            ears=(24, 14), tail=(35, 60, 0), feet={}, eyes='open')


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


class Dog:
    name = 'dog'
    kind = 'creature'
    airborne = {('attack', 1)}     # the leap
    ramps = RAMPS
    scale = 0.86      # keeps the back views, which stretch tall, inside the cell
    stand = pose()

    poses = {
        # a play bow, chest down and rump up, looking up at whatever it is about to chase
        'charging': [pose(body_pitch=-13, lift=-1.0, head_pitch=22, mouth=7, ears=(28, 8),
                          feet={'FL': (2.6, 0), 'FR': (2.6, 0), 'HL': (-0.6, 0), 'HR': (-0.6, 0)}, tail=(62, 72, 10))],
        # crouch, leap, bite, recover
        'attack': [
            pose(body_pitch=-9, lift=-1.6, fwd=-2.0, head_pitch=14, mouth=10, ears=(30, 22),
                 feet={'FL': (-1.5, 0), 'FR': (-1.5, 0), 'HL': (1.6, 0), 'HR': (1.6, 0)}, tail=(48, 66, 0)),
            pose(body_pitch=9, lift=2.2, fwd=2.0, head_pitch=-6, mouth=34, ears=(34, 30),
                 feet={'FL': (3.4, 3.4), 'FR': (3.0, 3.8), 'HL': (-3.2, 2.2), 'HR': (-3.6, 2.8)}, tail=(20, 40, 0)),
            pose(body_pitch=-7, lift=1.4, fwd=5.2, head_pitch=-16, mouth=42, ears=(34, 34),
                 feet={'FL': (3.2, 1.2), 'FR': (3.6, 0.6), 'HL': (-2.0, 0), 'HR': (-1.4, 0)}, tail=(28, 44, 0)),
            pose(body_pitch=2, lift=0.4, fwd=1.4, head_pitch=2, mouth=8, tail=(36, 60, 12),
                 feet={'FL': (1.0, 0), 'FR': (1.6, 0), 'HL': (-1.0, 0), 'HR': (-1.4, 0)}),
        ],
        # a howl: chest up, head thrown back, mouth open
        'release': [pose(body_pitch=9, lift=0.4, head_pitch=44, mouth=30, ears=(20, 38), eyes='shut',
                         feet={'FL': (0.4, 0), 'FR': (0.4, 0), 'HL': (-1.6, 0), 'HR': (-1.6, 0)}, tail=(24, 46, 0))],
        # a flinch: knocked back, head wrenched up and round, eyes screwed shut, tail clamped
        'damage': [pose(body_pitch=5, fwd=-1.6, head_pitch=24, head_yaw=18, mouth=18, ears=(55, 50), eyes='shut',
                        feet={'FL': (2.2, 0), 'FR': (2.0, 0), 'HL': (-2.2, 0), 'HR': (-2.0, 0)}, tail=(-30, -14, 0))],
        # worn out: sagging low, head hanging, ears down, tongue out
        'weak': [pose(body_pitch=-4, lift=-3.4, head_pitch=-26, mouth=7, tongue=True, ears=(72, 6), eyes='shut',
                      feet={'FL': (0.6, 0), 'FR': (0.6, 0), 'HL': (-0.4, 0), 'HR': (-0.4, 0)}, tail=(-28, -12, 0))],
        # lying on its side, legs out stiff
        'dead': [pose(roll=-90, lift=-3.8, head_pitch=-10, mouth=14, tongue=True, ears=(60, 20), eyes='shut',
                      tail=(-6, 0, 0),
                      feet={'FL': (0, 0, 24, -6), 'FR': (0, 0, 14, -4), 'HL': (0, 0, -22, 8), 'HR': (0, 0, -14, 5)})],
        'walking': [trot(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Dog()

if __name__ == '__main__':
    run(CREATURE)
