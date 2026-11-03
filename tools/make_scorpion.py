#!/usr/bin/env python3
"""A spirit scorpion, built the same way as the rat and the dog (see make_rat.py and creature.py).

A ghostly scorpion: a pale mint-and-teal shell like cold light through glass, six thin legs spread out
to the sides, two big pincers in front, and a long tail arched over its back that ends in a glowing violet
stinger with a few wisps of spirit-fire drifting off it. All palette roles, so it recolours like
the others.

    python3 tools/make_scorpion.py --model previews/scorpion-3d.png     look at the 3D model first
    python3 tools/make_scorpion.py sprites/scorpion [--preview sheet.png]
    python3 tools/extract_poses.py --merge scorpion=sprites/scorpion
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402

RAMPS = {
    'shell': ('r', 'q', 's', 'k'),       # mint, teal, deep teal, indigo: cold light through glass
    'plate': ('t', 'r', 'q', 'p'),       # paler plates down the back
    'claw': ('q', 'p', 'l', 'k'),        # steel to lavender for the pincers
    'glow': ('t', 'o', 'n', 'm'),        # the spirit-fire: cream to cyan to blue
    'sting': ('v', 'u', 'w', 'x'),       # the stinger: violet
}

PIVOT = (0.0, 2.3, 0.0)
LEG_X = (2.4, 0.3, -1.8)                  # where the three pairs of legs join the body
LEG_Y, LEG_Z = 2.2, 2.2
TAIL_ROOT = (-4.0, 2.55, 0.0)
TAIL_SEGMENTS = 7
TAIL_STEP = 1.65
HINGES = {'L': (4.0, 2.2, -1.9), 'R': (4.0, 2.2, 1.9)}


def bone3(a, b, radius, mat, name, grow=0.35):
    """An ellipsoid laid along the line from a to b, which may differ in all three directions."""
    d = sub(b, a)
    length = math.sqrt(sum(v * v for v in d)) or 1e-6
    y = [v / length for v in d]
    ref = (1.0, 0.0, 0.0) if abs(y[0]) < 0.9 else (0.0, 0.0, 1.0)
    dot = sum(r * v for r, v in zip(ref, y))
    x = [r - dot * v for r, v in zip(ref, y)]
    n = math.sqrt(sum(v * v for v in x))
    x = [v / n for v in x]
    z = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
    R = [[x[i], y[i], z[i]] for i in range(3)]
    mid = tuple((a[i] + b[i]) / 2 for i in range(3))
    return part(mid, (radius, length / 2 + grow, radius * 0.95), mat, name, R)


def anatomy(p):
    body, head, decals = [], [], []
    # The shell: a broad head-plate, then a tapering run of segments, each a little paler on top.
    head += [
        part((3.0, 2.5, 0), (3.5, 1.75, 2.8), 'shell', 'head'),
        part((3.0, 3.0, 0), (3.0, 1.0, 2.3), 'plate', 'head'),
    ]
    for i, (x, rx_, rz_) in enumerate(((-0.8, 2.5, 2.45), (-2.8, 2.0, 1.95))):
        body += [part((x, 2.35 - 0.1 * i, 0), (rx_, 1.55 - 0.1 * i, rz_), 'shell', 'body'),
                 part((x, 2.95 - 0.1 * i, 0), (rx_ * 0.85, 0.7, rz_ * 0.7), 'plate', 'body')]
    if p.get('crown'):
        # a crown on the back of the head-plate, clear of the eyes: a gold band round it, five points rising from it, a jewel at the front
        for k in range(8):
            t = 2 * math.pi * k / 8
            head.append(part((2.0 + 1.35 * math.cos(t), 4.3, 1.8 * math.sin(t)), (0.7, 0.5, 0.62), 'crown', 'crownband', ry(-t)))
        for k in range(5):
            t = 2 * math.pi * (k + 0.5) / 5 + math.pi
            head.append(part((2.0 + 1.35 * math.cos(t), 5.45, 1.8 * math.sin(t)), (0.42, 1.3, 0.42), 'crown', f'point{k}'))
        head.append(part((3.3, 4.3, 0.0), (0.5, 0.5, 0.5), 'jewel', 'jewel'))
    for side in (-1, 1):
        decals.append(((4.15, 3.85, side * 1.0), p['eyes']))
    return body, head, decals


def tail_parts(p):
    """The tail: segments end to end, curling up over the back and forward, ending in the stinger."""
    a1, a2, sway = p['tail']
    step = TAIL_STEP * p['stretch']       # stretched, the segments pull apart like a spring's coils
    out = []
    pos = TAIL_ROOT
    tip = pos
    for i in range(TAIL_SEGMENTS):
        t = i / (TAIL_SEGMENTS - 1)
        pitch = a1 + (a2 - a1) * t
        yaw = sway * math.sin(math.pi * t)
        R = mm(ry(deg(yaw)), rz(-deg(pitch)))
        d = mv(R, (-1.0, 0.0, 0.0))
        centre = add(pos, tuple(x * step / 2 for x in d))
        radius = 1.15 - 0.07 * i
        out.append(part(centre, (TAIL_STEP / 2 + 0.45, radius, radius), 'shell', 'tail', R))
        pos = add(pos, tuple(x * step for x in d))
        last = (R, d)
    R, d = last
    # the stinger: a glowing bulb, and a barb curving on from it
    bulb = add(pos, tuple(x * 0.7 for x in d))
    out.append(part(bulb, (1.0, 0.9, 0.9), 'sting', 'tail', R))
    barb = add(bulb, tuple(x * 1.3 for x in d))
    out.append(part(barb, (0.9, 0.35, 0.35), 'sting', 'barb', mm(R, rz(deg(-28)))))
    tip = barb
    return out, tip


def wisps(tip, p):
    """Spirit-fire drifting up off the stinger."""
    lift = p['wisp']
    return [
        part(add(tip, (0.2, 1.6 + lift, 0.0)), (0.75, 1.0, 0.75), 'glow', 'wisp0'),
        part(add(tip, (-1.0, 3.0 + lift, 0.9)), (0.55, 0.8, 0.55), 'glow', 'wisp1'),
        part(add(tip, (0.9, 3.6 + lift, -0.8)), (0.4, 0.6, 0.4), 'glow', 'wisp2'),
    ]


def pincers(on_body, p):
    """Two big pincers reaching out in front: an arm of two bones, and a claw that opens."""
    reach, spread, opening = p['claws']
    cs = p.get('claw_scale', 1.0)                      # a bigger-clawed scorpion sets this above 1
    out = []
    for side, z in (('L', -1), ('R', 1)):
        shoulder = (4.6, 2.2, z * 1.6)
        elbow = (6.0 + reach * 0.4, 2.4, z * (3.3 + spread))
        wrist = (7.6 + reach, 2.2, z * (2.4 + spread * 0.5))
        s, e, w = on_body(shoulder), on_body(elbow), on_body(wrist)
        out.append(bone3(s, e, 0.75 * cs, 'claw', 'arm' + side))
        out.append(bone3(e, w, 0.65 * cs, 'claw', 'arm' + side))
        out.append(part(add(w, (0.2, 0.0, 0.0)), (1.15 * cs, 0.8 * cs, 0.95 * cs), 'claw', 'arm' + side))
        # the pincer's two fingers, a V that opens
        for sign in (-1, 1):
            ang = deg(8 + opening) * sign * z
            R = ry(ang)
            tipv = mv(R, (1.55 * cs, 0.0, 0.0))
            out.append(part(add(w, (tipv[0] + 0.5 * cs, tipv[1] + 0.05, tipv[2])), (1.35 * cs, 0.42 * cs, 0.5 * cs), 'claw', 'pincer' + side + str(sign), R))
    return out


def stretched(q, e):
    """A part of the abdomen pulled back from the head by a factor e, and lengthened a little with it."""
    c = (3.0 + (q['c'][0] - 3.0) * e, q['c'][1], q['c'][2])
    r = (q['r'][0] * (1 + (e - 1) * 0.6), q['r'][1], q['r'][2])
    return dict(q, c=c, r=r)


def place(p):
    body, head, decals = anatomy(p)
    e = p['elongate']
    body = [stretched(q, e) for q in body]
    tail, tip = tail_parts(p)
    tail = [dict(q, c=(3.0 + (q['c'][0] - 3.0) * e, q['c'][1], q['c'][2])) for q in tail]
    tip = (3.0 + (tip[0] - 3.0) * e, tip[1], tip[2])
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))
    neck = (1.2, 2.4, 0.0)

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(neck, mv(h, sub(pt, neck))))

    placed = []
    for q in body + tail:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))
    # the pincers and the wisps follow the body
    placed += pincers(on_body, p)
    placed += wisps(on_body(tip), p)

    # Six legs: a hip on the side of the body, a knee up and out, a foot set wide on the ground.
    for k, x in enumerate(LEG_X):
        for side, z in (('L', -1), ('R', 1)):
            name = f'{side}{k + 1}'
            hip = on_body((3.0 + (x - 3.0) * e, LEG_Y, z * LEG_Z))
            dx, lift = p['feet'].get(name, (0.0, 0.0))
            curl = p['curl']
            if curl:
                foot = on_body((x + dx - 0.6 * curl, 0.5 + 3.2 * curl, z * (5.7 - 2.6 * curl)))
                knee = on_body((x + dx * 0.5 + 0.8, 4.4 + 0.5 * curl, z * (4.2 - 0.6 * curl)))
            else:
                foot = (hip[0] + dx - 0.2 + (0.5 - 0.4 * k) * 0.3, 0.5 + lift, hip[2] + z * 3.5)
                knee = ((hip[0] + foot[0]) / 2 + 0.5, 4.0 + lift * 0.4, hip[2] + z * 1.9)
            placed.append(bone3(hip, knee, 0.52, 'shell', 'leg' + name))
            placed.append(bone3(knee, foot, 0.4, 'shell', 'leg' + name, grow=0.25))
            placed.append(part((foot[0] + 0.15, foot[1] - 0.05, foot[2]), (0.65, 0.35, 0.55), 'plate', 'leg' + name))

    return placed, [(on_head(pt), shape) for pt, shape in decals]


# --- poses ---------------------------------------------------------------------------------
BASE = dict(elongate=1.0, stretch=1.0, body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, curl=0, wisp=0.0,
            claws=(0.0, 0.0, 14), tail=(32, 188, 0), feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def skitter(k, n=8):
    """The legs move in two sets of three, alternating, the body barely rising and falling."""
    phase = 2 * math.pi * k / n
    feet = {}
    for ki in range(3):
        for side, offset in (('L', 0 if ki % 2 == 0 else math.pi), ('R', math.pi if ki % 2 == 0 else 0)):
            s = (phase + offset) % (2 * math.pi)
            if s < math.pi:
                dx, lift = 1.6 * (1 - 2 * s / math.pi), 0.0
            else:
                u = (s - math.pi) / math.pi
                dx, lift = -1.6 + 3.2 * u, 1.2 * math.sin(math.pi * u)
            feet[f'{side}{ki + 1}'] = (dx, lift)
    return pose(feet=feet, lift=0.25 * math.cos(2 * phase), body_pitch=1.5 * math.sin(2 * phase),
                claws=(0.3 * math.sin(phase), 0.0, 16 + 6 * math.sin(phase)), tail=(32, 188 + 6 * math.sin(2 * phase), 6 * math.sin(phase)),
                wisp=0.3 * math.sin(phase))


class Scorpion:
    name = 'scorpion'
    kind = 'creature'
    airborne = set()
    ramps = RAMPS
    scale = 0.95
    stand = pose()

    poses = {
        # braced and ready: low, the claws held open in front, the tail arched high over the back
        'charging': [pose(body_pitch=-3, lift=-0.5, claws=(0.8, 0.4, 26), tail=(30, 176, 0), wisp=0.4,
                          feet={f'{s}{k}': (0.0, 0.0) for s in 'LR' for k in range(1, 4)})],
        # the wind-up, the lunge, the sting, and the recoil
        'attack': [
            # coiled back and cocked high, drawn in tight like a spring
            pose(body_pitch=-4, lift=-0.4, fwd=-2.2, claws=(-0.6, 1.0, 38), tail=(24, 128, 0), stretch=0.85, elongate=0.88, wisp=0.6),
            # the spring lets go: the body and tail lengthen and surge forward
            pose(body_pitch=5, lift=0.3, fwd=2.6, claws=(1.4, 0.2, 30), tail=(40, 172, 0), stretch=1.28, elongate=1.2, wisp=0.2),
            # the stab, stretched to full length and driven far forward and high
            pose(body_pitch=-9, lift=0.1, fwd=5.6, claws=(1.8, 0.0, 6), tail=(52, 168, 0), stretch=1.5, elongate=1.5, wisp=-0.4,
                 feet={'L3': (-0.6, 2.2), 'R3': (-0.6, 2.2), 'L2': (0.0, 0.7), 'R2': (0.0, 0.7)}),    # leaning into it, the back legs lift
            # it springs back
            pose(body_pitch=1, lift=0.0, fwd=1.6, claws=(0.4, 0.2, 18), tail=(30, 182, 0), stretch=1.1, elongate=1.12, wisp=0.2),
        ],
        # rearing up with the claws spread wide and the tail blazing
        'release': [pose(body_pitch=22, lift=0.6, claws=(1.0, 2.0, 46), tail=(20, 150, 0), wisp=1.6, eyes='shut',
                         feet={f'{s}{k}': (0.0, 0.0) for s in 'LR' for k in range(1, 4)})],
        # a flinch: thrown back, the claws up, the tail whipped
        'damage': [pose(body_pitch=8, fwd=-1.4, head_yaw=14, claws=(-0.2, 1.4, 34), tail=(18, 126, 10), wisp=0.8, eyes='shut')],
        # worn out: flat to the ground, the claws dropped, the tail drooping
        'weak': [pose(body_pitch=-2, lift=-1.0, claws=(-0.6, 0.3, 8), tail=(4, 62, 4), wisp=-0.9, eyes='shut')],
        # on its back, the legs curled up, the tail limp
        'dead': [pose(roll=180, lift=-0.4, claws=(-0.6, 0.6, 6), tail=(-6, 12, 5), curl=1.0, wisp=-0.4, eyes='shut')],
        'walking': [skitter(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Scorpion()

if __name__ == '__main__':
    run(CREATURE)
