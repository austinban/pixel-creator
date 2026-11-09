#!/usr/bin/env python3
"""A blight wasp, built the same way as the mantis and the scorpion (see make_mantis.py and creature.py).

A medium-small flying insect for the corrupted lands: a dark teal-black body with magenta bands round the abdomen, a pinched waist, a small head with two big glowing teal eyes and
a pair of antennae, six legs dangling under it, a stinger, and four small pale cyan wings that beat. It hovers instead of walking: the whole body bobs and the wings flap, and its feet
never reach the ground (its shadow is the game's job). Its attack rears back, dives, and drives the stinger forward and down. All palette roles, so it recolours like the others.

    python3 tools/make_wasp.py --model previews/wasp-3d.png      look at the 3D model first
    python3 tools/make_wasp.py sprites/wasp [--preview sheet.png]
    python3 tools/extract_poses.py --merge wasp=sprites/wasp
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'body': ('s', 'D', 'D', 'O'),        # dark teal-black: deep teal, abyss
    'stripe': ('j', 'i', 'h', 'u'),      # hot pink, magenta, dark magenta, purple: the bands
    'sting': ('c', 'j', 'i', 'h'),       # salmon to magenta
    'eye': ('r', 'o', 'n', 'm'),         # the teal glow, mint to blue
    'limb': ('s', 'D', 'D', 'O'),
    'wing': ('t', 'r', 'o', 'n'),        # pale cyan: cream, mint, cyan, sky
}

PIVOT = (-1.0, 10.0, 0.0)
WAIST = (-2.6, 9.7, 0.0)                 # the abdomen turns about here
NECK = (2.2, 10.4, 0.0)
WING_ROOT = (-0.4, 12.0, 0.0)
LEG_ROOTS = ((1.6, 8.6, 1.0), (0.0, 8.5, 1.1), (-1.5, 8.6, 1.0))


def anatomy(p):
    body, head, abd, decals = [], [], [], []
    # the thorax, a round hump, with a smaller one behind it
    body += [part((0.0, 10.4, 0), (2.5, 2.3, 2.2), 'body', 'thorax'),
             part((-1.9, 10.1, 0), (1.5, 1.5, 1.4), 'body', 'thorax2')]
    # the head: small, with two big glowing eyes at its sides and a pair of mandibles
    head += [part((3.9, 10.8, 0), (1.7, 1.6, 1.7), 'body', 'head'),
             part((4.2, 11.1, -1.7), (1.1, 1.4, 0.95), 'eye', 'head'),
             part((4.2, 11.1, 1.7), (1.1, 1.4, 0.95), 'eye', 'head')]
    opening = p['mouth']
    for side in (-1, 1):
        head.append(part((5.0, 9.5 - 0.02 * opening, side * 0.55), (0.5, 0.75 + 0.01 * opening, 0.3), 'sting', 'jaw', rx(deg(side * (8 + opening * 0.4)))))
        head.append(part((4.4, 13.2, side * 0.9), (0.16, 2.0, 0.16), 'limb', 'antenna', mm(rx(deg(-side * (22 + p['antennae'][1]))), rz(deg(-30 + p['antennae'][0])))))
    for side in (-1, 1):
        decals.append(((5.2, 11.2, side * 1.7), p['eyes']))
    # the abdomen: a narrow waist, then a fat teardrop with an orange band round it, ending in a stinger. All turned down about the waist by `abd`.
    abd += [part((-3.2, 9.7, 0), (1.0, 0.8, 0.8), 'body', 'waist')]
    for x, r, name in ((-6.0, (3.0, 2.1, 2.1), 'a1'), (-9.2, (2.6, 1.7, 1.7), 'a2')):
        abd.append(part((x, 9.2 - (6.0 + x) * 0.0, 0), r, 'body', name))
    for x, h in ((-5.0, 2.15), (-7.1, 2.0), (-9.1, 1.6)):
        abd.append(part((x, 9.2, 0), (0.62, h, h * 0.99), 'stripe', f'band{x}'))
    abd.append(part((-12.0, 9.0, 0), (1.5, 0.55, 0.55), 'sting', 'stinger', rz(deg(14))))
    return body, head, abd, decals


def wings(on_body, p):
    """Four wings: a long pair and a short pair behind it, thin flat ellipsoids that beat up and down about the back of the thorax."""
    out = []
    flap = p['wing']
    for k, (back, size, off) in enumerate(((0.0, (1.4, 0.16, 3.5), 0.0), (-2.2, (1.0, 0.16, 2.4), -6.0))):
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
            knee = on_body((root[0] + 0.9 + sway * 0.4 - curl * 0.6, root[1] - 1.6 + curl * 1.0, side * (root[2] + 1.5)))
            foot = on_body((root[0] + 0.4 + sway - curl * 1.0, root[1] - 4.2 + curl * 2.6, side * (root[2] + 1.8 - curl * 0.8)))
            placed.append(bone3(hip, knee, 0.34, 'limb', f'leg{i}{side}', grow=0.25))
            placed.append(bone3(knee, foot, 0.28, 'limb', f'leg{i}{side}', grow=0.25))
    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, abd=12, wing=40, curl=0, dangle=0, mouth=0, antennae=(0, 0), eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def hover(k, n=8):
    """A hover: the body bobs once over the cycle, the wings beat twice, the legs trail."""
    phase = 2 * math.pi * k / n
    return pose(lift=0.6 * math.sin(phase), body_pitch=6 + 2 * math.sin(phase), wing=35 + 38 * math.sin(2 * phase), abd=14 + 4 * math.sin(phase),
                head_pitch=-2 * math.sin(phase), dangle=0.8 * math.sin(phase), antennae=(4 * math.sin(phase), 0), mouth=4)


class Wasp:
    name = 'wasp'
    kind = 'creature'
    ramps = RAMPS
    scale = 1.35
    stand = pose()
    # it flies, so nothing is put on the ground row but the one lying dead
    airborne = {(a, i) for a, n in (('attack', 4), ('charging', 1), ('release', 1), ('damage', 1), ('weak', 1), ('walking', 8)) for i in range(n)}

    poses = {
        'charging': [pose(body_pitch=8, wing=55, abd=16, antennae=(6, 6))],
        # rear back with the stinger cocked, dive, drive the stinger forward and down, recover
        'attack': [
            pose(body_pitch=22, fwd=-1.8, lift=1.0, abd=-6, wing=78, head_pitch=8, mouth=14, antennae=(-6, 8)),
            pose(body_pitch=-14, fwd=0.4, lift=0.0, abd=40, wing=20, head_pitch=-8, mouth=26, antennae=(10, 6), curl=0.6),
            pose(body_pitch=-30, fwd=2.6, lift=-1.6, abd=74, wing=62, head_pitch=-16, mouth=34, antennae=(18, 4), curl=1.0),
            pose(body_pitch=0, fwd=0.6, lift=0.4, abd=30, wing=50, head_pitch=-2, mouth=10, curl=0.4),
        ],
        # a buzzing display: rising, wings flung up, head back, mouth open
        'release': [pose(body_pitch=26, lift=1.6, abd=-12, wing=85, head_pitch=-14, mouth=22, antennae=(14, 18), dangle=0.6, eyes='shut')],
        # a flinch: knocked back and tumbling, the wings crumpled
        'damage': [pose(body_pitch=34, fwd=-2.0, lift=0.4, abd=-14, wing=8, head_pitch=14, head_yaw=14, mouth=22, antennae=(-22, 24), dangle=-1.0, eyes='shut')],
        # worn out: sinking, the wings drooping, the abdomen hanging
        'weak': [pose(body_pitch=-8, lift=-2.4, abd=44, wing=-18, head_pitch=-26, antennae=(-30, -4), curl=0.6, eyes='shut')],
        # on its back, the legs curled, the wings splayed on the ground
        'dead': [pose(roll=180, lift=0.0, abd=26, wing=-6, head_pitch=-10, curl=1.0, antennae=(-30, -10), eyes='shut')],
        'walking': [hover(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Wasp()

if __name__ == '__main__':
    run(CREATURE)
