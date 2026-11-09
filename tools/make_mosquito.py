#!/usr/bin/env python3
"""A blood mosquito, built the same way as the wasp (see make_wasp.py and creature.py).

Thinner and more upright than the wasp: a slim grey-black body held tilted up, a small head with two glowing red eyes and a long pale needle for a proboscis, very long thin legs dangling under it,
small pale wings that beat so fast they blur, and an abdomen that ends in a swollen deep red belly. The belly is what it has drunk: it fills out in the attack and release frames.
It hovers instead of walking and its feet never reach the ground. Its attack rears back, dives, and drives the needle forward and down. All palette roles, so it recolours like the others.

    python3 tools/make_mosquito.py --model previews/mosquito-3d.png      look at the 3D model first
    python3 tools/make_mosquito.py sprites/mosquito [--preview sheet.png]
    python3 tools/extract_poses.py --merge mosquito=sprites/mosquito
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'body': ('p', 'l', 'k', 'k'),        # grey-black: steel, lavender, indigo
    'belly': ('c', 'e', 'i', 'h'),       # deep red: salmon, coral, magenta, dark magenta
    'needle': ('t', 'C', 'p', 'l'),      # a pale needle
    'eye': ('c', 'j', 'i', 'h'),         # the red glow
    'limb': ('l', 'k', 'k', 'k'),
    'wing': ('t', 'r', 'o', 'n'),        # pale cyan: cream, mint, cyan, sky
}

PIVOT = (-0.5, 10.0, 0.0)
WAIST = (-2.0, 9.9, 0.0)                 # the abdomen turns about here
NECK = (1.6, 10.6, 0.0)
WING_ROOT = (-0.4, 12.2, 0.0)
LEG_ROOTS = ((1.0, 8.6, 0.7), (-0.2, 8.5, 0.8), (-1.3, 8.6, 0.7))


def anatomy(p):
    body, head, abd, decals = [], [], [], []
    # a slim thorax, taller than it is long
    body += [part((0.0, 10.6, 0), (1.7, 2.3, 1.6), 'body', 'thorax')]
    # the head: small, two big red eyes at its sides, and the needle out in front
    head += [part((2.9, 11.0, 0), (1.3, 1.3, 1.3), 'body', 'head'),
             part((3.2, 11.3, -1.3), (0.9, 1.2, 0.8), 'eye', 'head'),
             part((3.2, 11.3, 1.3), (0.9, 1.2, 0.8), 'eye', 'head')]
    # the proboscis: a long thin needle forward and down; it drops further as the mouth opens
    drop = 28 + p['mouth'] * 0.7
    head.append(part((5.9, 10.3 - 0.0, 0), (3.6, 0.28, 0.28), 'needle', 'needle', rz(deg(-drop))))
    for side in (-1, 1):
        head.append(part((3.6, 13.0, side * 0.7), (0.14, 1.7, 0.14), 'limb', 'antenna', mm(rx(deg(-side * (18 + p['antennae'][1]))), rz(deg(-28 + p['antennae'][0])))))
        decals.append(((4.0, 11.4, side * 1.4), p['eyes']))
    # the abdomen: a narrow waist, a long thin segment, then the belly, which swells by `fill`
    abd += [part((-2.3, 9.9, 0), (1.0, 0.7, 0.7), 'body', 'waist'),
            part((-5.0, 9.6, 0), (2.6, 0.95, 0.95), 'body', 'a1')]
    k = p['fill']
    abd.append(part((-8.6 - 0.8 * k, 9.4, 0), (2.4 + 1.6 * k, 1.2 + 1.5 * k, 1.2 + 1.5 * k), 'belly', 'belly'))
    return body, head, abd, decals


def wings(on_body, p):
    """Four wings: a long pair and a short pair behind it, thin flat ellipsoids that beat up and down about the back of the thorax."""
    out = []
    flap = p['wing']
    for k, (back, size, off) in enumerate(((0.0, (1.0, 0.14, 3.0), 0.0), (-1.6, (0.8, 0.14, 2.0), -6.0))):
        for side in (-1, 1):
            a = deg(flap + off * 0.2)
            root = (WING_ROOT[0] + back, WING_ROOT[1], side * 0.8)
            reach = size[2] * 0.9
            centre = (root[0] - 0.9 + back * 0.2, root[1] + reach * math.sin(a), root[2] + side * reach * math.cos(a))
            R = mm(ry(side * deg(-14)), rx(-side * a))
            out.append(dict(part(on_body(centre), size, 'wing', f'wing{k}{side}', None), R=mm(p['_g'], R)))
    return out


def place(p):
    body, head, abd, decals = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    p = dict(p, _g=g)
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))
    a = rz(deg(p['abd']))

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    def on_abd(pt):
        return on_body(add(WAIST, mv(a, sub(pt, WAIST))))

    placed = []
    for q in body:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    for q in abd:
        placed.append(dict(q, c=on_abd(q['c']), R=mm(g, mm(a, q['R']))))
    placed += wings(on_body, p)

    # six legs hanging under the thorax: a short thigh down and out, a shin hooked back under
    curl = p['curl']
    for i, root in enumerate(LEG_ROOTS):
        for side in (-1, 1):
            hip = on_body((root[0], root[1], side * root[2]))
            sway = p['dangle'] * (1 if (i + (side > 0)) % 2 else -1)
            knee = on_body((root[0] + 1.3 + sway * 0.5 - curl * 0.8, root[1] - 2.8 + curl * 1.4, side * (root[2] + 1.5)))
            foot = on_body((root[0] + 0.4 + sway - curl * 1.0, root[1] - 7.4 + curl * 3.6, side * (root[2] + 1.8 - curl * 0.8)))
            placed.append(bone3(hip, knee, 0.24, 'limb', f'leg{i}{side}', grow=0.25))
            placed.append(bone3(knee, foot, 0.2, 'limb', f'leg{i}{side}', grow=0.25))
    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, abd=22, wing=40, fill=0.0, curl=0, dangle=0, mouth=0, antennae=(0, 0), eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def hover(k, n=8):
    """A hover: the body bobs once over the cycle, the wings beat twice, the legs trail."""
    phase = 2 * math.pi * k / n
    return pose(lift=0.6 * math.sin(phase), body_pitch=22 + 2 * math.sin(phase), wing=35 + 38 * math.sin(2 * phase), abd=24 + 4 * math.sin(phase),
                head_pitch=-2 * math.sin(phase), dangle=0.8 * math.sin(phase), antennae=(4 * math.sin(phase), 0), mouth=4)


class Mosquito:
    name = 'mosquito'
    kind = 'creature'
    ramps = RAMPS
    scale = 1.1
    stand = pose()
    # it flies, so nothing is put on the ground row but the one lying dead
    airborne = {(a, i) for a, n in (('attack', 4), ('charging', 1), ('release', 1), ('damage', 1), ('weak', 1), ('walking', 8)) for i in range(n)}

    poses = {
        'charging': [pose(body_pitch=26, wing=55, abd=26, fill=0.2, antennae=(6, 6))],
        # rear back with the needle cocked, dive, drive the needle forward and down while the belly fills, recover
        'attack': [
            pose(body_pitch=42, fwd=-1.6, lift=1.0, abd=0, wing=78, head_pitch=8, mouth=14, antennae=(-6, 8), fill=0.0),
            pose(body_pitch=-6, fwd=0.4, lift=0.0, abd=44, wing=20, head_pitch=-10, mouth=26, antennae=(10, 6), curl=0.6, fill=0.3),
            pose(body_pitch=-26, fwd=2.4, lift=-1.6, abd=66, wing=62, head_pitch=-14, mouth=34, antennae=(18, 4), curl=1.0, fill=0.8),
            pose(body_pitch=14, fwd=0.6, lift=0.4, abd=34, wing=50, head_pitch=-2, mouth=10, curl=0.4, fill=1.0),
        ],
        # drinking and swollen: rising, the belly full, wings flung up, head back
        'release': [pose(body_pitch=38, lift=1.6, abd=8, wing=85, head_pitch=-12, mouth=22, antennae=(14, 18), dangle=0.6, fill=1.0, eyes='shut')],
        # a flinch: knocked back and tumbling
        'damage': [pose(body_pitch=48, fwd=-2.0, lift=0.4, abd=-6, wing=8, head_pitch=14, head_yaw=14, mouth=22, antennae=(-22, 24), dangle=-1.0, eyes='shut')],
        # worn out: sinking, the belly hanging full
        'weak': [pose(body_pitch=4, lift=-2.4, abd=60, wing=-18, head_pitch=-26, antennae=(-30, -4), curl=0.6, fill=0.6, eyes='shut')],
        # on its back, the legs curled, the belly flat
        'dead': [pose(roll=180, lift=0.0, abd=26, wing=-6, head_pitch=-10, curl=1.0, antennae=(-30, -10), eyes='shut')],
        'walking': [hover(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Mosquito()

if __name__ == '__main__':
    run(CREATURE)
