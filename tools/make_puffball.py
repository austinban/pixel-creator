#!/usr/bin/env python3
"""A puffball: a small, round, dusty blue-grey mushroom creature of the corrupted lands, on two stubby legs.

A creature (see creature.py and make_mushroom.py, whose waddle it shares): a blue-grey ball for a body with a few big orange-red warts, two glowing mint-and-cyan eyes, one open pore on top that spits spores, and two short legs. It does not bite: it swells and bumps into things (the attack), puffs itself up and out (the release), and when it dies it bursts, a flat ragged
husk with spore bits scattered around it. All palette roles, so it recolours like the rest.

    python3 tools/make_puffball.py --model previews/puffball-3d.png      look at the 3D model first
    python3 tools/make_puffball.py sprites/puffball [--preview sheet.png]
    python3 tools/extract_poses.py --merge puffball=sprites/puffball
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, rz, sub, two_bone  # noqa: E402
from make_mushroom import surface_disc  # noqa: E402

RAMPS = {
    'ball': ('t', 'p', 'l', 'k'),         # dusty blue-grey: cream light, steel, lavender, indigo
    'wart': ('b', 'a', 'e', 'h'),         # orange-red warts: amber, orange, coral, magenta-dark
    'glow': ('r', 'o', 'o', 'o'),         # the eyes: mint and cyan
    'rim': ('p', 'l', 'k', 'k'),
    'lip': ('t', 'p', 'l', 'k'),          # the raised lip of the pore
    'pore': ('u', 'w', 'x', 'x'),         # the dark opening
    'foot': ('p', 'l', 'k', 'k'),
    'spore': ('r', 'q', 's', 'k'),        # teal spore bits
    'husk': ('p', 'l', 'k', 'k'),
}

UPPER, LOWER = 1.6, 1.8
HIPS = {'L': (0.2, 3.0, -2.0), 'R': (0.2, 3.0, 2.0)}
PIVOT = (0.0, 7.0, 0.0)
CENTRE = (0.0, 8.2, 0.0)
RADIUS = 6.2

# a few big warts on the ball: (azimuth, elevation, size); azimuth 0 is the front, so the face is left clear around (0, 8) and (+-35, 12)
WARTS = [(110, 50, 2.3), (215, 35, 2.3), (300, 48, 2.1), (170, -8, 2.0), (260, -22, 2.0)]
EYES = [(-30, 14), (30, 14)]


def at(az, el, radii, centre):
    a, e = math.radians(az), math.radians(el)
    return (math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a))


def anatomy(p):
    body = []
    puff = p['puff']                       # 0 normal; above 0 swollen wide, below squashed
    sx, sy = 1.0 + 0.16 * puff, 1.0 - 0.1 * puff
    flat = p['flat']                       # 1 for the burst husk
    sy *= 1.0 - 0.72 * flat
    sx *= 1.0 + 0.3 * flat
    radii = (RADIUS * sx, RADIUS * sy, RADIUS * sx)
    centre = (0.0, 8.2 + flat * (radii[1] + 0.4 - 8.2), 0.0)
    body.append(part(centre, radii, 'ball', 'body'))
    body.append(part((centre[0], centre[1] - radii[1] * 0.8, 0), (radii[0] * 0.8, radii[1] * 0.35, radii[2] * 0.8), 'rim', 'body'))
    for k, (az, el, size) in enumerate(WARTS):
        d = at(az, el, radii, centre)
        body.append(surface_disc(0, 0, 0, radii, centre, d, size * (1 + 0.5 * flat), 'wart', f'wart{k}', height=0.55))
    if p['eyes'] == 'open':
        for k, (az, el) in enumerate(EYES):
            body.append(surface_disc(0, 0, 0, radii, centre, at(az, el, radii, centre), 1.5, 'glow', f'eye{k}', height=0.5))
    if not flat:                                   # one open pore on top: a raised lip round a dark opening
        top = (0.0, 1.0, 0.0)
        body.append(surface_disc(0, 0, 0, radii, centre, top, 3.0, 'lip', 'lip', height=0.7))
        body.append(surface_disc(0, 0, 0, radii, centre, top, 1.9, 'pore', 'pore', height=0.9))
    return body


def place(p):
    body = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    placed = [dict(q, c=on_body(q['c']), R=mm(g, q['R'])) for q in body]
    if not p['flat']:
        for name, hip in HIPS.items():
            hip_w = on_body(hip)
            spec = p['feet'].get(name, (0.0, 0.0))
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, True)
            toe = (foot[0] + 0.6, foot[1] + 0.55)
            z = hip_w[2]
            placed.append(bone(hip_w[:2], knee, z, 1.4, 'foot', 'leg' + name))
            placed.append(bone(knee, foot, z, 1.2, 'foot', 'leg' + name, grow=0.4))
            placed.append(part((toe[0], toe[1], z), (1.9, 0.9, 1.5), 'foot', 'leg' + name))
    for k, (x, y, z, r) in enumerate(p['spores']):
        placed.append(part((x, y, z), (r, r, r), 'spore', f'spore{k}'))
    return placed, []


BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, puff=0, flat=0, feet={}, eyes='open', spores=())


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def waddle(k, n=8):
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
    return pose(feet=feet, lift=0.45 * abs(math.sin(phase)) - 0.1, body_pitch=2.2 * math.sin(phase), puff=0.2 * math.sin(2 * phase))


BURST = ((8.5, 1.2, 5.5, 1.0), (-7.0, 3.5, 7.5, 0.8), (10.5, 3.0, -3.5, 0.9), (-9.5, 1.3, -5.5, 0.9), (2.5, 5.5, 9.0, 0.7), (1.0, 4.0, -9.5, 0.8), (-11.0, 4.5, 1.0, 0.6))


class Puffball:
    name = 'puffball'
    kind = 'creature'
    airborne = {('attack', 1)}
    ramps = RAMPS
    scale = 0.85
    stand = pose()

    poses = {
        'charging': [pose(puff=0.4, feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # squash, spring and bump with the whole body, recover
        'attack': [
            pose(lift=-1.8, puff=-1.0, fwd=-1.4, body_pitch=8, feet={'L': (-0.6, 0), 'R': (-0.6, 0)}),
            pose(lift=1.8, puff=0.8, fwd=1.8, body_pitch=-8, feet={'L': (1.4, 2.0), 'R': (1.0, 2.4)}),
            pose(lift=0.4, puff=1.2, fwd=4.0, body_pitch=-12, feet={'L': (1.8, 0.6), 'R': (1.6, 0)}),
            pose(fwd=1.0, puff=0.2, feet={'L': (0.6, 0), 'R': (0.6, 0)}),
        ],
        # swollen big, a ring of spores puffed out around it
        'release': [pose(lift=0.6, puff=1.8, body_pitch=6, spores=((6.5, 12.0, 3.0, 0.9), (-5.0, 13.5, -2.0, 0.8), (3.0, 15.0, -4.5, 0.7), (-6.5, 10.0, 4.0, 0.7)),
                         feet={'L': (-0.4, 0), 'R': (-0.4, 0)})],
        'damage': [pose(lift=-2.0, puff=-1.2, fwd=-1.4, body_pitch=9, eyes='shut', feet={'L': (0.6, 0), 'R': (-0.4, 0)})],
        'weak': [pose(lift=-2.4, puff=-0.8, body_pitch=-4, eyes='shut', feet={'L': (0.4, 0), 'R': (0.4, 0)})],
        # burst: a flat ragged husk with spore bits scattered around it
        'dead': [pose(flat=1, lift=-0.4, eyes='shut', spores=BURST)],
        'walking': [waddle(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Puffball()

if __name__ == '__main__':
    run(CREATURE)
