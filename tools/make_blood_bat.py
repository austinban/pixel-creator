#!/usr/bin/env python3
"""A blood bat, built like the wasp (see make_wasp.py and creature.py): a flier that hovers instead of walking.

A big bat for the blood-themed enemies. A small furry body in dark plum, a round head with two tall pointed ears, glowing red eyes and a pair of bared cream fangs, and a pair of wide
leathery wings: a thick arm to the wrist, three finger bones fanning back from it, and dark crimson membrane stretched between them down to the hip. The wings are what you see (a wide,
low silhouette, the opposite of a mosquito). It hovers with slow beats; its attack rears back, swoops down and bites; it is worn out with its wings drooping; dead it lies on its back with
the wings crumpled in. All palette roles (no yellow), so it recolours like the others.

    python3 tools/make_blood_bat.py --model previews/blood-bat-3d.png      look at the 3D model first
    python3 tools/make_blood_bat.py sprites/blood-bat [--preview sheet.png]
    python3 tools/extract_poses.py --merge blood-bat=sprites/blood-bat
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'fur': ('f', 'g', 'w', 'x'),         # orchid, plum, grape, eggplant: the body
    'ear': ('e', 'g', 'w', 'x'),         # crimson inside the ears
    'membrane': ('e', 'g', 'w', 'x'),    # dark purple-crimson leather
    'bone': ('g', 'w', 'x', 'x'),        # the arm and finger bones, darker than the leather
    'fang': ('t', 't', 'C', 'c'),
    'eye': ('c', 'j', 'i', 'h'),         # glowing red-pink
}

PIVOT = (0.0, 10.0, 0.0)
NECK = (2.2, 10.8, 0.0)
JAW = (3.6, 10.4, 0.0)
SHOULDER = (0.2, 11.2, 1.3)
HIP = (-1.8, 9.2, 1.2)
# The wing flat out, in (x forward, d out along the wing): the wrist, three finger tips, and where the membrane meets the hip.
WRIST = (0.8, 5.8)
TIPS = ((-0.4, 11.0), (-3.4, 9.8), (-6.0, 6.8))
HIP_D = (-2.4, 1.6)


def wing_points(side, flap, span, droop):
    """The wing's skeleton in the body frame: a flap angle in degrees (0 flat, plus up), a span (1 open, 0.3 folded in) and how far the tips hang below the bones."""
    a = deg(flap)
    sn, cs = math.sin(a), math.cos(a)

    def at(x, d, hang=0.0):
        d = d * span
        return (SHOULDER[0] + x, SHOULDER[1] + d * sn - hang * d * 0.1 * droop, side * (SHOULDER[2] - 0.1 + d * cs))

    shoulder = (SHOULDER[0], SHOULDER[1], side * SHOULDER[2])
    wrist = at(*WRIST)
    tips = [at(x, d, 1.0) for x, d in TIPS]
    hip = (HIP[0], HIP[1], side * HIP[2])
    return shoulder, wrist, tips, hip, (0.0, sn, side * cs)


def panel(a, b, wide, normal, name):
    """A flat piece of membrane from a to b, `wide` across, lying in the plane of the wing."""
    d = sub(b, a)
    length = math.sqrt(sum(v * v for v in d)) or 1e-6
    u = tuple(v / length for v in d)
    dot = sum(n * v for n, v in zip(normal, u))
    n = tuple(nv - dot * uv for nv, uv in zip(normal, u))
    nl = math.sqrt(sum(v * v for v in n)) or 1e-6
    n = tuple(v / nl for v in n)
    w = (u[1] * n[2] - u[2] * n[1], u[2] * n[0] - u[0] * n[2], u[0] * n[1] - u[1] * n[0])
    R = [[u[i], n[i], w[i]] for i in range(3)]
    mid = tuple((a[i] + b[i]) / 2 for i in range(3))
    return part(mid, (length / 2 * 1.08, 0.2, wide), 'membrane', name, R)


def wings(p):
    out = []
    for side in (-1, 1):
        shoulder, wrist, tips, hip, along = wing_points(side, p['flap'] + side * 0.0, p['span'], p['droop'])
        normal = (0.0, math.cos(deg(p['flap'])), -side * math.sin(deg(p['flap'])))
        mids = [tuple((tips[i][k] + tips[i + 1][k]) / 2 for k in range(3)) for i in range(2)]
        gap = [math.dist(tips[i], tips[i + 1]) / 2 + 0.3 for i in range(2)]
        out.append(panel(wrist, mids[0], gap[0] * 0.62, normal, f'm0{side}'))
        out.append(panel(wrist, mids[1], gap[1] * 0.62, normal, f'm1{side}'))
        out.append(panel(wrist, tips[2], math.dist(tips[2], wrist) * 0.28, normal, f'm2{side}'))
        mid_back = tuple((tips[2][k] + hip[k]) / 2 for k in range(3))
        out.append(panel(wrist, hip, math.dist(wrist, hip) * 0.26, normal, f'm3{side}'))
        out.append(panel(hip, tips[2], math.dist(mid_back, hip) * 0.45, normal, f'm4{side}'))
        out.append(bone3(shoulder, wrist, 0.5, 'bone', f'arm{side}', grow=0.2))
        for i, tip in enumerate(tips):
            out.append(bone3(wrist, tip, 0.3, 'bone', f'finger{i}{side}', grow=0.15))
    return out


def anatomy(p):
    body, head, decals = [], [], []
    body += [part((0.0, 10.0, 0), (2.7, 2.8, 2.2), 'fur', 'body'),
             part((-1.6, 9.6, 0), (2.0, 2.1, 1.7), 'fur', 'rump')]
    head += [part((3.5, 11.4, 0), (1.9, 1.8, 1.7), 'fur', 'head'),
             part((5.0, 10.9, 0), (1.1, 0.9, 1.0), 'fur', 'snout')]
    ear = p['ears']
    for side in (-1, 1):
        head.append(part((3.0, 13.9, side * 1.3), (0.6, 2.3, 0.4), 'ear', f'ear{side}', mm(rx(deg(-side * (14 + ear))), rz(deg(8)))))
        head.append(part((5.5, 10.1, side * 0.55), (0.24, 0.8, 0.22), 'fang', f'fang{side}'))     # the upper fangs
    # the lower jaw drops about its hinge, with two fangs pointing up
    jaw = rz(-deg(p['mouth']))
    for c, r, mat in (((4.6, 9.6, 0), (1.3, 0.55, 1.0), 'fur'), ((5.4, 10.4, 0.5), (0.2, 0.6, 0.2), 'fang'), ((5.4, 10.4, -0.5), (0.2, 0.6, 0.2), 'fang')):
        head.append(part(add(JAW, mv(jaw, sub(c, JAW))), r, mat, 'jaw', jaw))
    for side in (-1, 1):
        decals.append(((4.9, 11.9, side * 1.15), p['eyes']))
    return body, head, decals


def place(p):
    body, head, decals = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = rz(deg(p['head_pitch']))

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    placed = []
    for q in body:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    for q in wings(p):
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    # two small feet tucked under the rump
    for side in (-1, 1):
        a = on_body((-2.2, 8.4, side * 0.9))
        b = on_body((-2.9 + 0.4 * p['curl'], 6.9 + 0.8 * p['curl'], side * 1.0))
        placed.append(bone3(a, b, 0.4, 'bone', f'foot{side}', grow=0.2))
    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, flap=20, span=1.0, droop=1.0, mouth=0, ears=0, curl=0, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def hover(k, n=8):
    """A slow hover: the wings beat once over the cycle, the body rises on the downstroke and sinks on the upstroke."""
    phase = 2 * math.pi * k / n
    return pose(flap=22 + 40 * math.cos(phase), span=0.95 - 0.1 * (1 - math.cos(phase)) / 2, lift=-0.7 * math.cos(phase), body_pitch=4 + 2 * math.sin(phase),
                head_pitch=-2 * math.sin(phase), mouth=4, curl=0.3)


class BloodBat:
    name = 'blood-bat'
    kind = 'creature'
    ramps = RAMPS
    scale = 1.2
    stand = pose()
    eye_colour = 'j'
    eye_reach = 1.8
    # it flies, so nothing is put on the ground row but the one lying dead
    airborne = {(a, i) for a, n in (('attack', 4), ('charging', 1), ('release', 1), ('damage', 1), ('weak', 1), ('walking', 8)) for i in range(n)}

    poses = {
        'charging': [pose(body_pitch=10, flap=22, span=1.0, mouth=8)],
        # rear back with the wings raised, swoop down with the wings swept back, bite, recover
        'attack': [
            pose(body_pitch=22, fwd=-1.6, lift=1.2, flap=62, span=1.0, head_pitch=8, mouth=14, ears=10),
            pose(body_pitch=-18, fwd=0.8, lift=-0.6, flap=-6, span=0.8, head_pitch=-10, mouth=28, ears=20, curl=0.8),
            pose(body_pitch=-26, fwd=1.4, lift=-1.4, flap=-20, span=0.75, head_pitch=-18, mouth=40, ears=26, curl=1.0),
            pose(body_pitch=0, fwd=0.8, lift=0.2, flap=24, span=0.9, mouth=10, ears=6),
        ],
        # a shriek: rising, head back, wings flung up and wide, mouth open
        'release': [pose(body_pitch=24, lift=1.4, flap=70, span=1.0, head_pitch=-16, mouth=34, ears=16, eyes='shut')],
        # a flinch: knocked back, wings snapped half shut
        'damage': [pose(body_pitch=32, fwd=-2.0, lift=0.4, flap=48, span=0.5, head_pitch=14, mouth=22, ears=30, curl=0.6, eyes='shut')],
        # worn out: sinking, the wings drooping, the head hanging
        'weak': [pose(body_pitch=-10, lift=-2.2, flap=-30, span=0.8, droop=2.0, head_pitch=-24, ears=22, curl=0.6, eyes='shut')],
        # on its back, the wings crumpled in beside it
        'dead': [pose(roll=180, lift=0.0, flap=-34, span=0.4, droop=2.5, head_pitch=-8, mouth=14, ears=24, curl=1.0, eyes='shut')],
        'walking': [hover(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = BloodBat()

if __name__ == '__main__':
    run(CREATURE)
