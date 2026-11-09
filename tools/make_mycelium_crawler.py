#!/usr/bin/env python3
"""A mycelium crawler: a low, many-legged creature of the corrupted lands whose whole carapace is a mushroom cap.

A creature (see creature.py, make_scorpion.py and make_mushroom.py): a pale bone body in three segments close to the ground under one big violet mushroom cap (cream gills show under its rim, a few cream spots on top), a blunt head with four glowing teal eyes and a
pair of mandibles, and six thin pale root-like legs that splay out and down in three joints.
It has no tail. It crawls in a tripod gait (three legs at a time), lunges and bites, and lies on its back with its legs curled. All palette roles, so it recolours like the rest.

    python3 tools/make_mycelium_crawler.py --model previews/mycelium-crawler-3d.png      look at the 3D model first
    python3 tools/make_mycelium_crawler.py sprites/mycelium-crawler [--preview sheet.png]
    python3 tools/extract_poses.py --merge mycelium-crawler=sprites/mycelium-crawler
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'body': ('t', 'C', 'c', 'e'),         # pale bone: cream, sand, salmon, coral
    'belly': ('C', 'c', 'e', 'f'),
    'limb': ('t', 'C', 'c', 'e'),         # the root legs, pale tendrils
    'tip': ('C', 'b', 'a', 'g'),          # the mandibles and feet, a little darker
    'cap': ('v', 'u', 'w', 'x'),          # the carapace: a violet cap
    'spot': ('t', 't', 'C', 'c'),
    'gill': ('t', 'C', 'c', 'e'),
    'glow': ('r', 'o', 'o', 'o'),         # the eyes: mint and cyan
}

PIVOT = (-1.0, 4.0, 0.0)
NECK = (5.0, 4.3, 0.0)
# hips: where each leg joins the body, (x, y, z), three a side
LEGS = {'FL': (3.2, 3.6, -2.0), 'FR': (3.2, 3.6, 2.0), 'ML': (-1.0, 3.6, -2.4), 'MR': (-1.0, 3.6, 2.4), 'HL': (-5.2, 3.6, -2.0), 'HR': (-5.2, 3.6, 2.0)}
CAP_C, CAP_R = (-1.6, 6.3, 0.0), (7.6, 2.7, 5.6)
SPOTS = ((-0.5, -1.6, 1.1), (-4.6, 1.8, 0.95), (2.2, 2.0, 0.85), (-2.0, 0.2, 0.7))      # (x, z, radius) on top of the cap


def anatomy(p):
    body, head = [], []
    # three segments, the rear one the largest, lying low
    body += [
        part((3.0, 3.9, 0), (3.6, 2.4, 3.0), 'body', 'seg1'),
        part((-1.4, 4.1, 0), (4.0, 2.9, 3.4), 'body', 'seg2'),
        part((-5.8, 3.9, 0), (3.8, 2.6, 3.0), 'body', 'seg3'),
        part((-1.4, 2.4, 0), (3.6, 1.0, 2.8), 'belly', 'belly'),
    ]
    # the carapace is one mushroom cap: gills under its rim, a few spots on top
    body.append(part((CAP_C[0], CAP_C[1] - 1.5, 0), (CAP_R[0] * 0.93, 0.7, CAP_R[2] * 0.93), 'gill', 'cap'))
    body.append(part(CAP_C, CAP_R, 'cap', 'cap'))
    for x, z, r in SPOTS:
        u = 1 - ((x - CAP_C[0]) / CAP_R[0]) ** 2 - (z / CAP_R[2]) ** 2
        body.append(part((x, CAP_C[1] + CAP_R[1] * math.sqrt(max(u, 0.0)) - 0.15, z), (r, r * 0.35, r), 'spot', 'cap'))
    # the head: blunt, with four eyes across the front and two mandibles that open
    o = p['mouth']
    head += [
        part((7.0, 3.9, 0), (2.6, 2.1, 2.5), 'body', 'head'),
        part((7.7, 5.0, -1.0), (0.55, 0.6, 0.6), 'glow', 'head'),
        part((7.7, 5.0, 1.0), (0.55, 0.6, 0.6), 'glow', 'head'),
        part((8.6, 4.2, -1.7), (0.45, 0.5, 0.45), 'glow', 'head'),
        part((8.6, 4.2, 1.7), (0.45, 0.5, 0.45), 'glow', 'head'),
    ]
    if p['eyes'] == 'shut':
        head = [q for q in head if q['mat'] != 'glow']
    for side in (-1, 1):
        head.append(part((9.0, 2.9 - 0.03 * o, side * (0.7 + 0.06 * o)), (1.3, 0.45, 0.4), 'tip', 'jaw', rz(deg(-20 - o * 0.5)) if False else rx(deg(side * (4 + o * 0.5)))))
    return body, head


def place(p):
    body, head = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    placed = [dict(q, c=on_body(q['c']), R=mm(g, q['R'])) for q in body]
    placed += [dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))) for q in head]

    for name, hip in LEGS.items():
        side = -1 if name.endswith('L') else 1
        row = name[0]
        hip_w = on_body(hip)
        dx, lift = p['feet'].get(name, (0.0, 0.0))
        # each pair splays a little differently: the front reaches forward, the hind trails back
        lean = {'F': 1.6, 'M': 0.0, 'H': -1.6}[row]
        wide = abs(hip[2])
        if p['curl']:
            c = p['curl']
            knee = on_body((hip[0] + lean * 0.3, 5.4 + 1.6 * c, side * (wide + 1.4)))
            ankle = on_body((hip[0] + lean * 0.4, 6.2 + 2.0 * c, side * (wide + 2.4 - 0.8 * c)))
            foot = on_body((hip[0] + lean * 0.5, 4.2 + 3.2 * c, side * (wide + 1.6 - 0.6 * c)))
        else:
            knee = (hip[0] + lean * 0.5 + dx * 0.3, 5.8 + lift * 0.5, side * (wide + 2.4))
            ankle = (hip[0] + lean * 0.9 + dx * 0.7, 3.2 + lift * 0.8, side * (wide + 4.6))
            foot = (hip[0] + lean * 1.1 + dx, 0.4 + lift, side * (wide + 5.6))
        placed.append(bone3(hip_w, knee, 0.55, 'limb', 'leg' + name, grow=0.3))
        placed.append(bone3(knee, ankle, 0.45, 'limb', 'leg' + name, grow=0.3))
        placed.append(bone3(ankle, foot, 0.36, 'limb', 'leg' + name, grow=0.25))
        placed.append(part((foot[0] + 0.1, foot[1], foot[2]), (0.55, 0.28, 0.5), 'tip', 'foot' + name))
    return placed, []


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, curl=0, mouth=0, feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def crawl(k, n=8):
    """A tripod gait: front-left, middle-right and hind-left step together, then the other three."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('FL', 0.0), ('MR', 0.0), ('HL', 0.0), ('FR', math.pi), ('ML', math.pi), ('HR', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 1.8 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -1.8 + 3.6 * u, 1.6 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.3 * math.cos(2 * phase) - 0.1, body_pitch=1.5 * math.sin(2 * phase), head_pitch=-2 * math.sin(2 * phase), mouth=4)


class MyceliumCrawler:
    name = 'mycelium-crawler'
    kind = 'creature'
    airborne = {('attack', 1)}
    ramps = RAMPS
    scale = 1.12
    stand = pose()

    poses = {
        # braced: head low and forward, mandibles a little open
        'charging': [pose(body_pitch=-6, lift=-0.4, head_pitch=-8, mouth=10)],
        # rear back, lunge, bite, recover
        'attack': [
            pose(body_pitch=10, lift=-0.6, fwd=-1.6, head_pitch=10, mouth=14),
            pose(body_pitch=-6, lift=1.4, fwd=1.6, head_pitch=-6, mouth=40, feet={'FL': (2.0, 2.0), 'FR': (2.0, 2.4), 'ML': (1.0, 0.6), 'MR': (1.0, 0.6)}),
            pose(body_pitch=-10, lift=0.4, fwd=4.0, head_pitch=-12, mouth=50, feet={'FL': (2.6, 0.8), 'FR': (2.6, 0.4)}),
            pose(body_pitch=0, fwd=1.0, head_pitch=0, mouth=12),
        ],
        # reared up, the front legs waving, cap thrown back: a roar
        'release': [pose(body_pitch=16, lift=0.8, head_pitch=14, mouth=44, feet={'FL': (2.4, 3.4), 'FR': (2.4, 3.8)})],
        # a flinch: knocked back, head wrenched round, eyes shut
        'damage': [pose(body_pitch=10, fwd=-1.8, head_pitch=14, head_yaw=18, mouth=26, eyes='shut')],
        # worn out: flat to the ground, head down
        'weak': [pose(body_pitch=-2, lift=-1.6, head_pitch=-22, eyes='shut')],
        # on its back, legs curled
        'dead': [pose(roll=160, lift=-0.4, head_pitch=-10, curl=1.0, eyes='shut')],
        'walking': [crawl(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = MyceliumCrawler()

if __name__ == '__main__':
    run(CREATURE)
