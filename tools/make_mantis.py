#!/usr/bin/env python3
"""A giant praying mantis, built the same way as the scorpion, rat and dog (see make_scorpion.py and creature.py).

A big, long creature in purple and yellow: a slim purple body with yellow bands down the abdomen, a small triangular head with
two big yellow eyes (each with a dark slit) and a pair of antennae, four long thin legs with an extra joint, and the two raptorial front arms
held up as if praying: a long upper arm raised forward and a spiked forearm folded back down. Its attack
snaps those arms out. All palette roles, so it recolours like the others.

    python3 tools/make_mantis.py --model previews/mantis-3d.png      look at the 3D model first
    python3 tools/make_mantis.py sprites/mantis [--preview sheet.png]
    python3 tools/extract_poses.py --merge mantis=sprites/mantis
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'body': ('v', 'u', 'w', 'x'),        # violet, purple, grape, eggplant
    'stripe': ('t', 'd', 'b', 'a'),      # cream, yellow, amber, orange: the bands and the arms' spines
    'eye': ('t', 'd', 'b', 'a'),         # big yellow eyes
    'limb': ('u', 'w', 'x', 'x'),        # the legs, a deeper purple
}

PIVOT = (-2.0, 6.0, 0.0)
SHOULDER = (2.4, 6.9, 1.45)              # where each raptorial arm joins, x and y, and its z
LEGS = {'ML': (-0.8, 5.2, -1.3), 'MR': (-0.8, 5.2, 1.3), 'HL': (-4.4, 5.0, -1.5), 'HR': (-4.4, 5.0, 1.5)}
FEMUR, TIBIA = 4.2, 3.9


def anatomy(p):
    body, head, decals = [], [], []
    # the abdomen: long, tapering back, with a yellow band at each joint
    for x, y, r, name in ((-9.0, 5.2, (2.7, 1.35, 1.3), 'a1'), (-6.2, 5.6, (2.9, 1.8, 1.75), 'a2'), (-3.0, 6.0, (2.9, 2.0, 1.95), 'a3')):
        body.append(part((x, y, 0), r, 'body', name))
    for x, h in ((-7.6, 1.45), (-4.6, 1.9), (-1.6, 2.05)):
        body.append(part((x, 5.7 + (h - 1.8) * 0.2, 0), (0.45, h, h * 0.98), 'stripe', f'band{x}'))
    # the thorax, and the long neck of the prothorax that rises to the head
    body.append(part((0.2, 7.0, 0), (2.1, 2.2, 1.7), 'body', 'thorax'))
    body.append(part((1.8, 9.0, 0), (1.25, 3.0, 1.15), 'body', 'neck', rz(deg(-14))))
    # the head, triangular, with two big yellow eyes and a pair of mandibles
    head += [
        part((3.5, 11.4, 0), (2.0, 1.75, 2.25), 'body', 'head'),
        part((4.0, 11.8, -2.0), (1.2, 1.7, 1.05), 'eye', 'head'),
        part((4.0, 11.8, 2.0), (1.2, 1.7, 1.05), 'eye', 'head'),
    ]
    opening = p['mouth']
    for side in (-1, 1):
        head.append(part((4.3, 10.0 - 0.02 * opening, side * 0.5), (0.45, 0.9 + 0.01 * opening, 0.35), 'stripe', 'jaw', rx(deg(side * (6 + opening * 0.4)))))
        # antennae, long and thin, sweeping up and back
        head.append(part((3.0, 13.9, side * 0.9), (0.18, 2.3, 0.18), 'limb', 'antenna', mm(rx(deg(-side * (16 + p['antennae'][1]))), rz(deg(-18 + p['antennae'][0])))))
    for side in (-1, 1):
        decals.append(((5.1, 11.8, side * 2.0), p['eyes']))
    return body, head, decals


def arms(on_body, p):
    """The two raptorial arms: an upper arm raised, a forearm folded, and a row of spines along it."""
    a1, a2, reach = p['arms']
    out = []
    for pair, (shoulder_xy, spread, a1_off, a2_off, scale_) in enumerate((((SHOULDER[0], SHOULDER[1]), SHOULDER[2], 0, 0, 1.0),)):
        for side in (-1, 1):
            shoulder = (shoulder_xy[0], shoulder_xy[1], side * spread)
            d1 = (math.cos(deg(a1 + a1_off)), math.sin(deg(a1 + a1_off)))
            elbow = (shoulder[0] + FEMUR * scale_ * d1[0] + reach * 0.3, shoulder[1] + FEMUR * scale_ * d1[1], side * (spread + 0.6))
            d2 = (math.cos(deg(a2 + a2_off)), math.sin(deg(a2 + a2_off)))
            wrist = (elbow[0] + TIBIA * scale_ * d2[0] + reach * 0.4, elbow[1] + TIBIA * scale_ * d2[1], side * (spread + 0.5))
            s, e, w = on_body(shoulder), on_body(elbow), on_body(wrist)
            out.append(bone3(s, e, 0.95 * scale_, 'body', f'femur{pair}{side}', grow=0.5))
            out.append(bone3(e, w, 0.72 * scale_, 'body', f'tibia{pair}{side}', grow=0.4))
            out.append(part(on_body((wrist[0] + 0.5 * d2[0], wrist[1] + 0.5 * d2[1], wrist[2])), (0.8, 0.5, 0.45), 'stripe', f'claw{pair}{side}'))
            for k in range(1, 5):                                  # spines along the forearm's inner edge
                t = k / 5
                at = (elbow[0] + (wrist[0] - elbow[0]) * t, elbow[1] + (wrist[1] - elbow[1]) * t, elbow[2] - side * 0.5)
                out.append(part(on_body((at[0] - 0.25 * d2[1], at[1] + 0.25 * d2[0] + 0.1, at[2])), (0.22, 0.6 * scale_, 0.22), 'stripe', f'spine{pair}{side}{k}'))
    return out


def place(p):
    body, head, decals = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))
    neck = (2.4, 10.0, 0.0)

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(neck, mv(h, sub(pt, neck))))

    placed = []
    for q in body:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    placed += arms(on_body, p)

    # four long legs, each with three bones and two joints: the thigh up and out to a high knee, the shin down and further out
    # to a second joint, and a foot-bone down to the ground
    for name, hip in LEGS.items():
        side = -1 if name.endswith('L') else 1
        hip_w = on_body(hip)
        dx, lift = p['feet'].get(name, (0.0, 0.0))
        wide = abs(hip[2])
        knee = (hip[0] + dx * 0.3 + 0.2, 8.8 + lift * 0.4, side * (wide + 1.5))
        ankle = (hip[0] + dx * 0.7 + 0.3, 3.6 + lift * 0.8, side * (wide + 3.4))
        foot = (hip[0] + 0.4 + dx, 0.45 + lift, side * (wide + 4.3))
        if p['curl']:
            c = p['curl']
            knee = on_body((hip[0] + 0.8, 7.6 + 1.2 * c, side * (wide + 1.6)))
            ankle = on_body((hip[0] + 0.2, 5.8 + 1.8 * c, side * (wide + 2.8)))
            foot = on_body((hip[0] - 0.6 * c, 4.2 + 3.0 * c, side * (wide + 2.4 - 1.0 * c)))
        placed.append(bone3(hip_w, knee, 0.5, 'limb', 'leg' + name, grow=0.3))
        placed.append(bone3(knee, ankle, 0.42, 'limb', 'leg' + name, grow=0.3))
        placed.append(bone3(ankle, foot, 0.34, 'limb', 'leg' + name, grow=0.25))
        placed.append(part((foot[0] + 0.15, foot[1], foot[2]), (0.6, 0.3, 0.5), 'stripe', 'foot' + name))
    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
PRAY = (20, -100, 0.0)       # the arms: upper arm out and a little up in front of the chest, forearm folded back down, all below the eyes
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, curl=0, mouth=0, arms=PRAY, antennae=(0, 0), feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def stalk(k, n=8):
    """A slow stalk: the legs move in two pairs, the body swaying, the arms held up and the head bobbing."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('ML', 0.0), ('HR', 0.0), ('MR', math.pi), ('HL', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 1.7 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -1.7 + 3.4 * u, 1.3 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.3 * math.cos(2 * phase), body_pitch=1.8 * math.sin(2 * phase), head_pitch=-2.5 * math.sin(2 * phase),
                arms=(20 + 3 * math.sin(phase), -100, 0.0), antennae=(3 * math.sin(phase), 0))


class Mantis:
    name = 'mantis'
    kind = 'creature'
    airborne = set()
    ramps = RAMPS
    scale = 1.3
    stand = pose()

    poses = {
        # praying: the arms folded up in front, the head raised, the antennae forward
        'charging': [pose(body_pitch=14, lift=0.6, arms=PRAY, antennae=(6, 6))],
        # the arms cock back, snap out, hold, and fold in again
        'attack': [
            pose(body_pitch=6, fwd=-1.2, head_pitch=6, mouth=12, arms=(82, -118, -1.0), antennae=(-8, 8)),
            pose(body_pitch=-4, fwd=-0.4, head_pitch=-4, mouth=26, arms=(36, -60, 0.6), antennae=(10, 6)),
            pose(body_pitch=-10, fwd=-1.6, head_pitch=-8, mouth=34, arms=(8, 14, 0.6), antennae=(18, 4)),
            pose(body_pitch=-2, fwd=0.5, head_pitch=-2, mouth=10, arms=(42, -104, 0.3), antennae=(8, 6)),
        ],
        # the arms are thrown up wide: a display
        'release': [pose(body_pitch=10, lift=0.6, head_pitch=-10, mouth=16, arms=(96, -170, 0.0), antennae=(14, 18), eyes='shut')],
        # a flinch: thrown back, the arms flung out
        'damage': [pose(body_pitch=14, fwd=-1.8, head_pitch=14, head_yaw=14, mouth=22, arms=(20, 30, -1.0), antennae=(-22, 24), eyes='shut')],
        # worn out: low, the arms hanging, the head down
        'weak': [pose(body_pitch=-3, lift=-1.6, head_pitch=-28, arms=(-30, -80, -1.0), antennae=(-30, -4), eyes='shut',
                      feet={'ML': (0, 0), 'MR': (0, 0), 'HL': (0, 0), 'HR': (0, 0)})],
        # on its back, the legs curled
        'dead': [pose(roll=150, lift=-0.5, head_pitch=-10, curl=1.0, arms=(110, 160, 0.0), antennae=(-30, -10), eyes='shut')],
        'walking': [stalk(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Mantis()

if __name__ == '__main__':
    run(CREATURE)
