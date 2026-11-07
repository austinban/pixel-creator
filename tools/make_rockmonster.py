#!/usr/bin/env python3
"""A little rock monster: a jagged boulder on two long stumpy legs, with no arms and no mouth.

A creature, not a person (see creature.py and make_mushroom.py): a pile of angular stone slabs tilted every which way, spikes and tall plates sticking out of its back and sides, a heavy brow,
two glowing red eyes, a patch of moss, and two long legs. It squashes down and stretches as it moves. It attacks by jumping at its target and bouncing off it: crouch, leap, hit, and rebound
backwards. Walking is a heavy hop-waddle. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_rockmonster.py --model previews/rockmonster-3d.png      look at the 3D model first
    python3 tools/make_rockmonster.py sprites/rock-monster [--preview sheet.png]
    python3 tools/extract_poses.py --merge rock-monster=sprites/rock-monster
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import normalise  # noqa: E402
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

RAMPS = {
    'stone': ('q', 'p', 'l', 'k'),       # teal, steel, lavender, indigo: the rock asset's cool stone
    'slate': ('p', 'l', 'k', 'w'),       # a darker stone for the lower slabs, the legs and the brow
    'moss': ('z', 'A', 'B', 's'),        # lime, green, emerald, deep teal
    'eye': ('j', 'j', 'j', 'i'),         # glowing red eyes: flat bright hot pink
    'eyeshut': ('l', 'k', 'k', 'w'),     # an eye screwed shut: a dark slit
}

# Bones, in pixels. Two short legs under the boulder. z is the creature's right.
UPPER, LOWER = 2.7, 2.9
LIFT = 2.4                        # the boulder is held this far up, on long legs
HIPS = {'L': (0.4, 5.6, -2.6), 'R': (0.4, 5.6, 2.6)}
PIVOT = (0.0, 7.4 + LIFT, 0.0)     # the body turns about its middle
SQUASH_X, SQUASH_Y = 0.16, 0.2     # how much a full squash widens and flattens it


def squashed(q, s):
    """A part of the body with the whole boulder squashed (s > 0: wider and flatter) or stretched (s < 0: narrower and taller), from the ground up."""
    sx, sy = 1 + SQUASH_X * s, 1 - SQUASH_Y * s
    c, r = q['c'], q['r']
    return dict(q, c=(c[0] * sx, c[1] * sy, c[2] * sx), r=(r[0] * sx, r[1] * sy, r[2] * sx))


def along(direction):
    """An orientation whose x axis runs along `direction`, for a spike or a plate."""
    ex = normalise(direction)
    up = (0.0, 1.0, 0.0) if abs(ex[1]) < 0.95 else (1.0, 0.0, 0.0)
    ez = normalise((ex[1] * up[2] - ex[2] * up[1], ex[2] * up[0] - ex[0] * up[2], ex[0] * up[1] - ex[1] * up[0]))
    ey = (ez[1] * ex[2] - ez[2] * ex[1], ez[2] * ex[0] - ez[0] * ex[2], ez[0] * ex[1] - ez[1] * ex[0])
    return [[ex[i], ey[i], ez[i]] for i in range(3)]


def spike(centre, radii, direction, length, thick, mat, name, sink=0.35):
    """A shard of stone: a long thin ellipsoid whose root is sunk into the surface at `centre` and whose tip points along `direction`."""
    d = normalise(direction)
    c = tuple(centre[i] + d[i] * length * (0.5 - sink) for i in range(3))
    return part(c, (length / 2, thick, thick * 0.9), mat, name, along(d))


def anatomy(p):
    """The parts in the standing frame: the body, with its eyes."""
    body, decals = [], []
    main = ((0.0, 7.6, 0.0), (5.4, 4.6, 5.0))
    # a pile of angular slabs tilted every which way, each its own piece so the edges fall into shadow
    body += [
        part(main[0], main[1], 'stone', 'head', mm(rz(deg(6)), rx(deg(-5)))),
        part((-1.5, 9.5, 1.4), (4.3, 1.7, 3.6), 'stone', 'slab0', mm(rz(deg(-28)), rx(deg(10)))),
        part((1.7, 10.3, -1.6), (3.6, 1.5, 3.2), 'slate', 'slab1', mm(rz(deg(24)), rx(deg(-9)))),
        part((-3.0, 6.1, -2.5), (3.4, 1.6, 2.8), 'slate', 'slab2', mm(rz(deg(36)), rx(deg(-8)))),
        part((2.5, 5.0, 2.4), (3.5, 1.5, 3.0), 'stone', 'slab3', mm(rz(deg(-32)), rx(deg(8)))),
        part((-0.4, 4.4, 0.0), (4.6, 2.1, 4.4), 'slate', 'base'),                      # a darker underside, over the legs
        part((4.2, 10.2, 0.0), (1.9, 0.85, 3.9), 'slate', 'brow', rz(deg(-14))),      # a heavy brow over the eyes
    ]
    # spikes and shards out of its back, sides and top, in every direction but down
    for k, (direction, length, thick, mat) in enumerate((
            ((-0.5, 1.0, 0.2), 4.6, 1.1, 'stone'), ((0.4, 1.0, -0.6), 3.8, 1.0, 'slate'), ((-0.9, 0.8, 0.6), 4.0, 1.1, 'slate'), ((0.0, 0.9, 1.0), 3.3, 0.95, 'stone'),
            ((-1.0, 0.3, -0.5), 3.6, 1.0, 'stone'), ((-0.3, 0.2, 1.0), 3.2, 0.9, 'slate'), ((0.1, 0.1, -1.0), 3.4, 1.0, 'stone'), ((-0.8, -0.1, 0.9), 2.8, 0.9, 'stone'),
            ((0.7, 0.5, 0.9), 2.4, 0.8, 'slate'), ((0.8, 0.45, -0.9), 2.6, 0.85, 'stone'), ((-1.0, 0.6, 0.0), 3.0, 0.9, 'slate'))):
        d = normalise(direction)
        root = tuple(main[0][i] + d[i] * main[1][i] * 0.88 for i in range(3))
        body.append(spike(root, None, d, length, thick, mat, 'spike%d' % k))
    # tall flat plates standing up along its spine
    for k, (c, r, tilt) in enumerate((((-2.6, 11.7, 0.0), (0.5, 2.5, 1.6), -22), ((-0.8, 12.5, 0.3), (0.5, 2.9, 1.8), -8), ((1.0, 12.0, -0.2), (0.5, 2.3, 1.5), 12))):
        body.append(part(c, r, 'stone' if k % 2 else 'slate', 'plate%d' % k, rz(deg(tilt))))
    # moss in a crack on its shoulder
    body += [
        part((-1.2, 8.6, 4.4), (1.9, 0.8, 1.0), 'moss', 'moss0', rx(deg(-40))),
        part((2.4, 11.0, -1.0), (1.1, 0.6, 0.9), 'moss', 'moss1'),
    ]
    # two big glowing eyes under the brow (a dark slit when screwed shut); they are parts, not decals, so they can be a few pixels across
    for side in (-1, 1):
        if p['eyes'] == 'open':
            body.append(part((5.15, 8.9, side * 1.8), (1.25, 1.6, 1.3), 'eye', 'eye%d' % (side > 0)))
        else:
            body.append(part((5.1, 8.9, side * 1.8), (0.6, 0.3, 1.3), 'eyeshut', 'eye%d' % (side > 0)))
    return [dict(q, c=(q['c'][0], q['c'][1] + LIFT, q['c'][2])) for q in body], [((pt[0], pt[1] + LIFT, pt[2]), shape) for pt, shape in decals]


def place(p):
    """The rock monster in a pose: parts carried to where the pose puts them."""
    body, decals = anatomy(p)
    s = p['squash']
    sx, sy = 1 + SQUASH_X * s, 1 - SQUASH_Y * s
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)

    def carry(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    placed = [dict(q, c=carry(q['c']), R=mm(g, q['R'])) for q in (squashed(q, s) for q in body)]
    for name, hip in HIPS.items():
        hip_w = carry((hip[0] * sx, hip[1], hip[2] * sx))
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, True)
            toe = (foot[0] + 0.8, foot[1] + 0.6)
        else:
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.8, foot[1] + 0.6)
            knee, foot, toe = [carry((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.45, 'slate', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.2, 'slate', 'leg' + name, grow=0.4))
        placed.append(part((toe[0], toe[1], z), (2.2, 1.0, 1.7), 'stone', 'leg' + name))
    return placed, [(carry((pt[0] * sx, pt[1] * sy, pt[2] * sx)), shape) for pt, shape in decals]


# --- poses -------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, squash=0.0, eyes='open', feet={})


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def waddle(k, n=8):
    """A heavy hop-waddle: the legs take turns, the whole boulder drops and squashes onto each step and rocks from side to side."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('L', 0), ('R', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 1.6 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -1.6 + 3.2 * u, 1.5 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.5 * abs(math.sin(phase)) - 0.2, squash=0.35 * math.cos(2 * phase), body_pitch=3.0 * math.sin(phase))


class RockMonster:
    name = 'rock-monster'
    kind = 'creature'
    airborne = {('attack', 1), ('attack', 3)}       # the leap, and the rebound off its target
    ramps = RAMPS
    scale = 0.95
    stand = pose()

    poses = {
        # ready: sunk a little, weight on both feet
        'charging': [pose(lift=-0.7, squash=0.4, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # jump at it and bounce off, all exaggerated: a deep crouch that coils it flat, a high long leap stretched out at the target, a hard hit that squashes it against the target, and a big
        # backwards rebound, tumbling up and away
        'attack': [
            pose(lift=-2.9, squash=1.5, body_pitch=10, fwd=-2.2, feet={'L': (-1.0, 0), 'R': (-1.0, 0)}),
            pose(lift=5.8, squash=-1.4, body_pitch=-22, fwd=4.6, feet={'L': (1.8, 5.2), 'R': (1.0, 6.0)}),
            pose(lift=1.2, squash=1.3, body_pitch=-28, fwd=8.0, feet={'L': (2.4, 2.0), 'R': (2.0, 1.2)}),
            pose(lift=6.0, squash=-0.9, body_pitch=26, fwd=0.2, feet={'L': (-1.8, 4.6), 'R': (-2.4, 5.4)}),
        ],
        # a roar: reared back, stretched tall
        'release': [pose(lift=0.7, squash=-0.4, body_pitch=11, feet={'L': (-0.6, 0), 'R': (-0.6, 0)})],
        # a flinch: squashed flat and knocked back, eyes screwed shut
        'damage': [pose(lift=-1.9, squash=0.9, body_pitch=9, fwd=-1.6, eyes='shut', feet={'L': (0.6, 0), 'R': (-0.5, 0)})],
        # worn out: sagging low
        'weak': [pose(lift=-2.7, squash=0.8, body_pitch=-4, eyes='shut', feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # toppled on its side, legs sticking out
        'dead': [pose(roll=-90, lift=-3.8, squash=0.3, eyes='shut', feet={'L': (0, 0, 22, -6), 'R': (0, 0, 14, -4)})],
        'walking': [waddle(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = RockMonster()

if __name__ == '__main__':
    run(CREATURE)
