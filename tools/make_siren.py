#!/usr/bin/env python3
"""A siren: a horrible, upright fish with a mouth too big for its head, and arms.

A creature, not a person (see creature.py and make_rockmonster.py): a bloated fish body standing on two short webbed legs, a dark teal back and a pale, sick belly, a head that is nearly all mouth
(a short, broad jaw with thick fleshy lips that hinges wide open on a black throat, and no teeth, just the gape), two bulging yellow eyes with black pupils, gill slits down each cheek, a ridge of fin
along its back and a ragged tail fin behind, and two long arms with webbed clawed hands. It lurches when it walks, with the jaw working. It attacks by rearing back with the jaw gaping,
lunging with both arms out and snapping shut. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_siren.py --model previews/siren-3d.png      look at the 3D model first
    python3 tools/make_siren.py sprites/siren [--preview sheet.png]
    python3 tools/extract_poses.py --merge siren=sprites/siren
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402

RAMPS = {
    'scale': ('q', 's', 'D', 'x'),           # teal, deep teal, abyss, eggplant: the back and head
    'belly': ('r', 'q', 'p', 'l'),           # mint, teal, steel, lavender: the pale belly
    'fin': ('y', 'u', 'w', 'x'),             # fuchsia, purple, grape: the fins, a sickly contrast
    'maw': ('w', 'x', 'x', 'x'),             # the throat: as dark as the palette goes
    'tongue': ('h', 'w', 'x', 'x'),          # a dark, wet tongue
    'lip': ('c', 'e', 'g', 'w'),             # heavy fleshy lips: salmon, coral, plum, grape
        'eye': ('d', 'd', 'b', 'a'),             # a sick bright yellow
    'pupil': ('w', 'x', 'x', 'x'),
    'shut': ('s', 'D', 'x', 'x'),            # an eye screwed shut: a dark slit
    'gill': ('D', 'x', 'x', 'x'),
    'claw': ('l', 'k', 'w', 'x'),            # dark bony claws, so they do not read as teeth
}

HIPS = {'L': (0.0, 4.6, -2.2), 'R': (0.0, 4.6, 2.2)}
SHOULDERS = {'L': (0.2, 12.0, -3.8), 'R': (0.2, 12.0, 3.8)}
LEG_UPPER, LEG_LOWER = 2.4, 2.5
ARM_UPPER, ARM_LOWER = 4.4, 4.8                   # long, gangly arms
HINGE = (0.4, 13.4, 0.0)                    # where the jaw turns, in the head
PIVOT = (0.0, 5.0, 0.0)                     # the body turns about its hips


def jaw_parts(jaw):
    """The mouth: a short upper jaw, the lower jaw hinged open by `jaw` (0 shut, 1 gaping), a black throat and tongue, and thick lips round the rim. It is wide and round, not a snout."""
    a = deg(62 * jaw)
    R = rz(-a)
    parts = [
        part(add(HINGE, (2.5, 1.0, 0.0)), (3.4, 1.5, 4.3), 'scale', 'head'),                                  # the upper jaw: short and broad
        part(add(HINGE, mv(rz(-a / 2), (2.6, 0.0, 0.0))), (3.6, 0.7 + 3.7 * jaw, 3.7), 'maw', 'maw', rz(-a / 2)),   # the throat: a big black gape, taller as it opens
    ]

    def lower(pt):
        return add(HINGE, mv(R, pt))

    parts += [
        part(lower((2.5, -1.1, 0.0)), (3.4, 1.4, 4.1), 'scale', 'jaw', R),                                    # the lower jaw
        part(lower((1.6, -0.1, 0.0)), (2.1, 0.5, 1.6), 'tongue', 'tongue', R),
        # the lips: a fat pad along the front of each jaw, and a swollen corner at each side
        part(add(HINGE, (5.2, 0.7, 0.0)), (1.5, 1.05, 3.9), 'lip', 'lipU'),
        part(lower((5.1, -0.8, 0.0)), (1.6, 1.15, 3.8), 'lip', 'lipL', R),
    ]
    for side in (-1, 1):
        parts.append(part(add(HINGE, mv(rz(-a / 2), (3.6, 0.0, side * 3.9))), (1.3, 1.1 + 0.9 * jaw, 1.0), 'lip', 'corner%d' % (side > 0), rz(-a / 2)))
        parts.append(part(add(HINGE, (3.9, 0.9, side * 3.8)), (1.9, 0.8, 0.8), 'lip', 'lipU%d' % (side > 0)))
    return parts


def anatomy(p):
    """The parts in the standing frame: the body, head and mouth, eyes and fins."""
    eyes = p['eyes'] == 'open'
    body = [
        part((-0.8, 8.4, 0.0), (3.3, 6.3, 3.1), 'scale', 'body'),                                              # a gaunt, tall body
        part((1.3, 7.6, 0.0), (2.4, 4.8, 2.3), 'belly', 'belly'),                                              # the pale belly in front
        part((-0.2, 14.4, 0.0), (4.7, 3.5, 4.5), 'scale', 'head'),                                             # the head, mostly jaw
    ]
    for k, y in enumerate((10.2, 8.9, 7.6, 6.3)):                                                              # ribs showing through the belly
        body.append(part((2.35, y, 0.0), (0.45, 0.38, 2.0 - 0.15 * k), 'gill', 'rib%d' % k))
    body += jaw_parts(p['jaw'])
    for side in (-1, 1):
        if eyes:
            body.append(part((2.2, 16.0, side * 3.9), (1.1, 1.3, 1.0), 'eye', 'eye%d' % (side > 0)))           # small, sunken, to the sides like a fish's
            body.append(part((3.2, 16.0, side * 4.2), (0.3, 1.1, 0.28), 'pupil', 'eye%d' % (side > 0)))        # a thin black slit
        else:
            body.append(part((2.8, 15.8, side * 3.9), (0.5, 0.3, 1.1), 'shut', 'eye%d' % (side > 0)))
        for k in range(4):                                                                                     # gill slits down each cheek
            body.append(part((-0.9 - k * 0.1, 13.9 - k * 0.8, side * 4.5), (0.25, 0.75, 0.2), 'gill', 'gill%d' % (k * 2 + (side > 0))))
    # a ridge of fin down the back, tall at the neck and dwindling, and a ragged tail fin behind
    for k, (y, h) in enumerate(((16.2, 2.4), (13.4, 2.8), (10.4, 2.6), (7.6, 2.0))):
        body.append(part((-3.9 - 0.15 * k, y, 0.0), (1.6, h, 0.28), 'fin', 'dorsal%d' % k, rz(deg(24 + 4 * k))))
    for k, (x, y, rr, tilt) in enumerate(((-5.6, 3.6, (2.8, 1.0, 0.28), -26), (-5.8, 5.2, (2.4, 1.0, 0.28), 14), (-5.2, 2.2, (2.2, 0.8, 0.28), -50))):
        body.append(part((x, y, 0.0), rr, 'fin', 'tail%d' % k, rz(deg(tilt))))
    return body


def hand(wrist, z, spread=1.0):
    """A webbed clawed hand at the wrist: a flat paddle of a palm and three claws."""
    out = [part((wrist[0] + 0.6, wrist[1] - 0.2, z), (1.9, 0.9, 1.7), 'scale', 'hand')]
    for k, dz in enumerate((-1.1, 0.0, 1.1)):
        out.append(part((wrist[0] + 2.9, wrist[1] - 0.9, z + dz * spread * 1.2), (1.9, 0.36, 0.36), 'claw', 'claw%d' % k, rz(deg(-20))))
    return out


def place(p):
    """The siren in a pose: parts carried to where the pose puts them, and the arms and legs fitted to their targets."""
    body = anatomy(p)
    s = p['squash']
    sx, sy = 1 + 0.12 * s, 1 - 0.14 * s
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)

    def carry(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    placed = []
    for q in body:
        c, r = q['c'], q['r']
        c, r = (c[0] * sx, c[1] * sy, c[2] * sx), (r[0] * sx, r[1] * sy, r[2] * sx)
        placed.append(dict(q, c=carry(c), R=mm(g, q['R']), r=r))
    for name, hip in HIPS.items():
        hip_w = carry((hip[0] * sx, hip[1], hip[2] * sx))
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), LEG_UPPER, LEG_LOWER, True)
        else:
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + LEG_UPPER * math.sin(a1), hip[1] - LEG_UPPER * math.cos(a1))
            foot = (knee[0] + LEG_LOWER * math.sin(a1 + a2), knee[1] - LEG_LOWER * math.cos(a1 + a2))
            knee, foot = [carry((k[0], k[1], hip[2]))[:2] for k in (knee, foot)]
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.4, 'scale', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.15, 'scale', 'leg' + name, grow=0.4))
        placed.append(part((foot[0] + 0.9, foot[1] + 0.4, z), (2.6, 0.7, 1.7), 'fin', 'leg' + name))             # a webbed foot, wide and flat
    for name, sh in SHOULDERS.items():
        sh_w = carry((sh[0] * sx, sh[1] * sy, sh[2] * sx))
        dx, dy = p['arms'].get(name, (1.0, -5.0))
        elbow, wrist = two_bone(sh_w, (sh_w[0] + dx, sh_w[1] + dy), ARM_UPPER, ARM_LOWER, False)
        z = sh_w[2]
        placed.append(bone(sh_w[:2], elbow, z, 1.25, 'scale', 'arm' + name))
        placed.append(bone(elbow, wrist, z, 1.05, 'scale', 'arm' + name, grow=0.4))
        placed += hand(wrist, z)
    return placed, []


# --- poses -------------------------------------------------------------------------------
BASE = dict(body_pitch=-6, roll=0, fwd=0, lift=0, squash=0.0, jaw=0.25, eyes='open', feet={}, arms={})


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def lurch(k, n=8):
    """A lurching walk: the legs take turns, the body rocks side to side and dips on each step, the arms swing slackly and the jaw works."""
    phase = 2 * math.pi * k / n
    feet, arms = {}, {}
    for name, offset in (('L', 0), ('R', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 1.3 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -1.3 + 2.6 * u, 1.3 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
        arms[name] = (1.2 + 1.4 * math.sin(phase + offset + math.pi), -5.0 + 0.6 * math.cos(phase + offset))
    return pose(feet=feet, arms=arms, lift=0.4 * abs(math.sin(phase)) - 0.2, squash=0.2 * math.cos(2 * phase), body_pitch=-6 + 2.5 * math.sin(phase), jaw=0.38 + 0.22 * math.sin(2 * phase))


class Siren:
    name = 'siren'
    kind = 'creature'
    airborne = {('attack', 1), ('attack', 2)}       # the lunge
    ramps = RAMPS
    scale = 0.95
    stand = pose()

    poses = {
        # ready: weight forward, jaw hanging open, arms hooked out in front
        'charging': [pose(jaw=0.6, body_pitch=-8, lift=-0.5, squash=0.3, arms={'L': (3.0, -3.0), 'R': (3.4, -2.4)}, feet={'L': (0.5, 0), 'R': (0.5, 0)})],
        # rear back with the jaw gaping, lunge with both arms out, snap shut on it, and fall back
        'attack': [
            pose(jaw=1.0, body_pitch=14, lift=-0.6, squash=0.5, fwd=-1.6, arms={'L': (-1.0, 2.5), 'R': (-1.4, 3.0)}, feet={'L': (-0.8, 0), 'R': (-0.8, 0)}),
            pose(jaw=1.0, body_pitch=-14, lift=2.6, squash=-0.6, fwd=2.8, arms={'L': (5.0, 1.2), 'R': (5.4, 0.4)}, feet={'L': (1.2, 2.6), 'R': (0.6, 3.2)}),
            pose(jaw=0.0, body_pitch=-24, lift=1.0, squash=0.9, fwd=4.4, arms={'L': (5.4, -1.4), 'R': (5.0, -2.0)}, feet={'L': (2.0, 1.2), 'R': (1.6, 0.6)}),
            pose(jaw=0.4, body_pitch=8, lift=0.0, squash=0.3, fwd=1.0, arms={'L': (1.8, -4.0), 'R': (2.0, -4.2)}, feet={'L': (0.6, 0), 'R': (0.2, 0)}),
        ],
        # a shriek: reared right back, the jaw as wide as it goes, arms flung up and out
        'release': [pose(jaw=1.0, body_pitch=18, lift=0.6, squash=-0.4, arms={'L': (1.4, 4.5), 'R': (1.0, 4.8)}, feet={'L': (-0.6, 0), 'R': (-0.6, 0)})],
        # a flinch: knocked back, the jaw snapped half shut, eyes screwed up, arms thrown wide
        'damage': [pose(jaw=0.2, body_pitch=10, lift=-1.2, squash=0.7, fwd=-1.6, eyes='shut', arms={'L': (-2.4, -1.0), 'R': (-2.0, -0.4)}, feet={'L': (0.6, 0), 'R': (-0.6, 0)})],
        # worn out: slumped over, the jaw hanging slack and the arms trailing
        'weak': [pose(jaw=0.7, body_pitch=-14, lift=-2.2, squash=0.8, eyes='shut', arms={'L': (0.6, -6.2), 'R': (0.2, -6.4)}, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # flopped on its side like a landed fish, the mouth open, the legs and arms out
        'dead': [pose(roll=-90, jaw=0.8, lift=-3.2, squash=0.3, eyes='shut', arms={'L': (3.0, -3.0), 'R': (-2.0, -4.0)}, feet={'L': (0, 0, 22, -6), 'R': (0, 0, 14, -4)})],
        'walking': [lurch(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Siren()

if __name__ == '__main__':
    run(CREATURE)
