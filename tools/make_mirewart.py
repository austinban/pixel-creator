#!/usr/bin/env python3
"""A mirewart: a squat, bloated bog toad with a mushroom growing from its back, the lowest of the drowned chain (see the siren, make_siren.py).

A creature, not a person (see creature.py and make_siren.py): a body as wide as it is tall, mud green with lime on the back and a pale mint belly, a broad head with a wide mouth line,
a pale throat sac that swells when it spits, a big bulging yellow eye on each side of the head, two folded hind legs with webbed feet and two short front arms. An orchid and plum mushroom cap
with hot-pink spots grows from its back on a short stem. It hops short distances; it attacks by rearing, swelling its throat and spitting a spore glob. Everything is palette roles.

    python3 tools/make_mirewart.py --model previews/mirewart-3d.png      look at the 3D model first
    python3 tools/make_mirewart.py sprites/mirewart [--preview sheet.png]
    python3 tools/extract_poses.py --merge mirewart=sprites/mirewart
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, rz, sub, two_bone  # noqa: E402

RAMPS = {
    'skin': ('z', 'A', 'B', 's'),            # lime, green, emerald, deep teal: the mud-green back and head
    'belly': ('r', 'q', 'p', 'l'),           # mint, teal, steel, lavender: the pale belly
    'sac': ('t', 'r', 'q', 'p'),             # cream and mint: the throat sac, paler than the belly
    'wart': ('C', 'z', 'A', 'B'),            # the warts, a paler tan-lime
    'eye': ('d', 'd', 'b', 'a'),             # a bright sick yellow
    'pupil': ('w', 'x', 'x', 'x'),
    'shut': ('s', 'D', 'x', 'x'),            # an eye screwed shut: a dark slit
    'mouth': ('w', 'x', 'x', 'x'),           # the mouth line
    'stem': ('t', 'C', 'p', 'l'),            # the mushroom's stem
    'cap': ('f', 'u', 'w', 'x'),             # the cap: orchid, purple, grape, eggplant
    'gill': ('c', 'e', 'g', 'w'),            # the gills under the cap rim
    'spot': ('j', 'i', 'h', 'w'),            # hot-pink spots
    'foot': ('A', 'B', 's', 'D'),
}

HIPS = {'L': (-2.4, 3.2, -3.6), 'R': (-2.4, 3.2, 3.6)}
SHOULDERS = {'L': (3.0, 3.4, -3.4), 'R': (3.0, 3.4, 3.4)}
LEG_UPPER, LEG_LOWER = 3.2, 3.4
ARM_UPPER, ARM_LOWER = 2.4, 2.5
PIVOT = (0.0, 2.0, 0.0)                     # the body turns about its belly


def anatomy(p):
    """The parts in the standing frame (x forward, y up, z across)."""
    eyes = p['eyes'] == 'open'
    cap_up = p['cap']                                                                # how far the cap rises, 0 squashed to 1 puffed
    sac = 0.75 + 0.9 * p['sac']
    body = [
        part((-1.0, 4.3, 0.0), (5.2, 3.6, 4.7), 'skin', 'body'),                                         # the bloated body
        part((1.6, 3.2, 0.0), (3.6, 2.6, 3.6), 'belly', 'belly'),                                        # the pale belly in front
        part((3.4, 5.0, 0.0), (3.5, 2.6, 4.0), 'skin', 'head'),                                          # a broad flat head, set low and forward
        part((5.9, 4.1, 0.0), (1.1, 0.35, 3.1), 'mouth', 'mouth'),                                       # the wide mouth line
        part((4.6, 3.2 - 0.3 * p['sac'], 0.0), (1.9 * sac, 1.35 * sac, 2.4 * sac), 'sac', 'sac'),       # the throat sac, swelling when it spits
    ]
    for k, (x, y, z) in enumerate(((-2.2, 7.0, 2.4), (0.6, 6.9, -2.9), (-3.3, 5.6, -3.2), (-0.8, 7.4, 0.8))):   # a few warts
        body.append(part((x, y, z), (0.55, 0.4, 0.55), 'wart', 'wart%d' % k))
    for side in (-1, 1):
        if eyes:
            body.append(part((3.0, 7.5, side * 2.8), (1.35, 1.4, 1.35), 'eye', 'eye%d' % (side > 0)))                # the bulging eyes
            body.append(part((3.9, 7.7, side * 3.2), (0.3, 0.95, 0.28), 'pupil', 'eye%d' % (side > 0)))             # a black slit pupil
        else:
            body.append(part((3.9, 7.1, side * 2.9), (0.5, 0.3, 1.2), 'shut', 'eye%d' % (side > 0)))
    # the mushroom: a stem from the back, gills under the rim, a tall dome cap with pink spots lying on its surface
    cx, cy, rr, rh = -2.3, 9.3 + 0.4 * cap_up, 3.4, 2.1 + 0.4 * cap_up

    def on_cap(dx, dz, size):
        y = cy + rh * math.sqrt(max(0.0, 1 - (dx / rr) ** 2 - (dz / rr) ** 2)) * 0.97
        return part((cx + dx, y, dz), (size, size * 0.55, size), 'spot', 'spot%d%d' % (int(dx * 10), int(dz * 10)))
    body += [
        part((cx, 7.2, 0.0), (1.0, 2.0, 1.0), 'stem', 'stem'),
        part((cx, cy - 0.2, 0.0), (rr + 0.1, 0.5, rr + 0.1), 'gill', 'gills'),
        part((cx, cy + 0.2, 0.0), (rr, rh, rr), 'cap', 'cap'),
        on_cap(1.1, -1.3, 0.75), on_cap(-1.6, 1.2, 0.8), on_cap(0.2, 0.8, 0.6), on_cap(-0.6, -1.9, 0.6), on_cap(1.5, 1.4, 0.55),
    ]
    return body


def foot(ankle, z, flat=1.0):
    """A webbed foot: a wide flat paddle with three toe pads."""
    out = [part((ankle[0] + 0.9, ankle[1] + 0.2, z), (2.0 * flat, 0.6, 1.6), 'foot', 'foot')]
    for k, dz in enumerate((-1.1, 0.0, 1.1)):
        out.append(part((ankle[0] + 2.4, ankle[1] + 0.1, z + dz), (0.8, 0.45, 0.5), 'foot', 'toe%d' % k))
    return out


def place(p):
    """The mirewart in a pose: parts carried to where the pose puts them, and the legs and arms fitted to their targets."""
    body = anatomy(p)
    s = p['squash']
    sx, sy = 1 + 0.14 * s, 1 - 0.16 * s
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
        hip_w = carry((hip[0] * sx, hip[1] * sy, hip[2] * sx))
        spec = p['feet'].get(name, (0.0, 0.0))
        knee, ank = two_bone(hip_w, (hip[0] + spec[0], spec[1] + 0.5), LEG_UPPER, LEG_LOWER, True)
        z = hip_w[2]
        placed.append(bone(hip_w[:2], knee, z, 1.7, 'skin', 'leg' + name))
        placed.append(bone(knee, ank, z, 1.2, 'skin', 'leg' + name, grow=0.4))
        placed += foot(ank, z)
    for name, sh in SHOULDERS.items():
        sh_w = carry((sh[0] * sx, sh[1] * sy, sh[2] * sx))
        dx, dy = p['arms'].get(name, (0.8, -3.0))
        elbow, wrist = two_bone(sh_w, (sh_w[0] + dx, sh_w[1] + dy), ARM_UPPER, ARM_LOWER, False)
        z = sh_w[2]
        placed.append(bone(sh_w[:2], elbow, z, 1.0, 'skin', 'arm' + name))
        placed.append(bone(elbow, wrist, z, 0.85, 'skin', 'arm' + name, grow=0.3))
        placed += foot(wrist, z, 0.7)
    return placed, []


# --- poses -------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, squash=0.0, sac=0.0, cap=0.0, eyes='open', feet={}, arms={})


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def hop(k, n=8):
    """A hop: crouch, spring (the legs straighten behind and the body lifts), a short flight and a landing that squashes, then rest. The sac pulses."""
    phase = k / n
    if phase < 0.25:                          # crouch: gather
        u = phase / 0.25
        lift, squash, pitch, feet = -0.4 * u, 0.5 * u, 4 * u, {'L': (0.0, 0.0), 'R': (0.0, 0.0)}
        arms = {'L': (0.8, -3.0), 'R': (0.8, -3.0)}
    elif phase < 0.75:                        # spring and flight
        u = (phase - 0.25) / 0.5
        rise = math.sin(math.pi * u)
        lift, squash, pitch = 3.2 * rise, -0.5 * rise, -10 * rise
        reach = -2.0 + 3.2 * rise
        feet = {'L': (reach, 3.0 * rise), 'R': (reach, 3.0 * rise)}
        arms = {'L': (2.2, -1.4), 'R': (2.2, -1.4)}
    else:                                     # landing, settling
        u = (phase - 0.75) / 0.25
        lift, squash, pitch, feet = -0.6 * (1 - u), 0.8 * (1 - u), 3 * (1 - u), {'L': (0.0, 0.0), 'R': (0.0, 0.0)}
        arms = {'L': (1.0, -3.0), 'R': (1.0, -3.0)}
    return pose(lift=lift, squash=squash, body_pitch=pitch, feet=feet, arms=arms, sac=0.35 + 0.35 * math.sin(2 * math.pi * phase), cap=0.5 + 0.5 * math.sin(2 * math.pi * phase + 1.0), fwd=0.0)


class Mirewart:
    name = 'mirewart'
    kind = 'creature'
    airborne = {('attack', 1), ('attack', 2), ('walking', 3), ('walking', 4), ('walking', 5)}       # the leap and the hop
    ramps = RAMPS
    scale = 1.15
    eye_colour = None
    stand = pose()

    poses = {
        # ready: crouched low, the throat swelling, weight forward on the arms
        'charging': [pose(body_pitch=-6, lift=-0.6, squash=0.5, sac=0.7, cap=0.3, arms={'L': (1.2, -3.0), 'R': (1.2, -3.0)}, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # rear back, swell the throat to its limit, spit forward, and settle
        'attack': [
            pose(body_pitch=14, lift=-0.4, squash=0.4, sac=0.5, fwd=-0.8, cap=0.2, arms={'L': (-0.4, -3.0), 'R': (-0.4, -3.0)}, feet={'L': (-0.4, 0), 'R': (-0.4, 0)}),
            pose(body_pitch=22, lift=1.0, squash=-0.3, sac=1.0, fwd=-1.2, cap=1.0, arms={'L': (0.8, -2.2), 'R': (0.8, -2.2)}, feet={'L': (-0.8, 0.4), 'R': (-0.8, 0.4)}),
            pose(body_pitch=-14, lift=0.6, squash=0.6, sac=0.2, fwd=1.4, cap=0.7, arms={'L': (2.2, -1.8), 'R': (2.2, -1.8)}, feet={'L': (0.8, 0.2), 'R': (0.8, 0.2)}),
            pose(body_pitch=-4, lift=-0.2, squash=0.3, sac=0.3, fwd=0.4, cap=0.4, arms={'L': (1.2, -3.0), 'R': (1.2, -3.0)}, feet={'L': (0.2, 0), 'R': (0.2, 0)}),
        ],
        # a spore burst: rises on its legs, the cap puffed right up, the sac emptied
        'release': [pose(body_pitch=10, lift=1.2, squash=-0.5, sac=0.0, cap=1.0, arms={'L': (0.6, -2.2), 'R': (0.6, -2.2)}, feet={'L': (-0.2, 0), 'R': (-0.2, 0)})],
        # a flinch: knocked back, eyes screwed shut, the cap squashed down
        'damage': [pose(body_pitch=12, lift=-0.4, squash=0.8, sac=0.1, fwd=-1.4, cap=0.0, eyes='shut', arms={'L': (-1.2, -2.6), 'R': (-0.8, -2.6)}, feet={'L': (0.6, 0), 'R': (-0.4, 0)})],
        # worn out: slumped flat, eyes shut, the throat slack
        'weak': [pose(body_pitch=-6, lift=-1.4, squash=0.9, sac=0.0, cap=0.0, eyes='shut', arms={'L': (0.8, -3.2), 'R': (0.6, -3.2)}, feet={'L': (0.8, 0), 'R': (0.8, 0)})],
        # flopped on its side, legs out, the cap crushed
        'dead': [pose(roll=-90, lift=-2.0, squash=0.4, sac=0.0, cap=0.0, eyes='shut', arms={'L': (1.6, -2.4), 'R': (-1.0, -2.8)}, feet={'L': (1.2, 0.0), 'R': (-0.6, 0.0)})],
        'walking': [hop(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Mirewart()

if __name__ == '__main__':
    run(CREATURE)
