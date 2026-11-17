#!/usr/bin/env python3
"""A spark eel: a long, slick eel risen out of the sunken water, crackling with the spirit realm's stolen energy. A low-to-mid water enemy beside the siren (make_siren.py).

Lore: it drank from the drowned spirit lanterns and the rune altars until the light would not leave, and now it hunts by shocking. A creature (see creature.py and make_leech.py, which also
builds a long body from a chain of ellipsoids): a chain of seventeen overlapping segments that lies coiled and low at the tail and rises in an S to a raised head, a dark abyss-teal back with a pale mint
belly, a fuchsia dorsal fin ridge, a narrow pointed head with a small jaw (no ring mouth, no gape: that is the Lamprey Mother and the siren) and two small yellow eyes, a row of glowing cyan electric organs
along each flank, and forking arcs of cyan with a pale core that jump off the body when it charges and strikes. It slithers in place (its body undulates), and when it strikes it rears back, lunges the
head forward and down and throws a bolt. Everything is palette roles, so it recolours like the rest.

    python3 tools/make_spark_eel.py --model previews/spark-eel-3d.png      look at the 3D model first
    python3 tools/make_spark_eel.py sprites/spark-eel [--preview previews/spark-eel.png]
    python3 tools/extract_poses.py --merge spark-eel=sprites/spark-eel
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import I3, add, deg, mm, mv, part, run, ry, rz  # noqa: E402

RAMPS = {
    'back': ('q', 's', 'D', 'x'),              # teal, deep teal, abyss, eggplant: the dark slick back
    'belly': ('t', 'r', 'q', 'p'),             # cream, mint, teal, steel: the pale belly
    'fin': ('y', 'u', 'w', 'x'),               # fuchsia, purple, grape, eggplant: the dorsal ridge
    'jaw': ('r', 'q', 'p', 'l'),               # a pale small jaw
    'mouth': ('w', 'x', 'x', 'x'),             # the dark line of the mouth
    'eye': ('d', 'd', 'b', 'a'),               # a small sick yellow
    'shut': ('s', 'D', 'x', 'x'),              # an eye screwed shut
    'organ': ('t', 't', 'o', 'q'),             # the glowing electric organs along each flank: cream core, cyan
    'arc': ('t', 'o', 'o', 'q'),               # the arcs: a cream core, vivid cyan
    'spark': ('t', 't', 'o', 'o'),             # the brightest points
}

N = 17                                          # segments in the body
LENGTH = 13.0                                   # the body's length lying down, tail to head
R_MAX = 2.55                                    # the fattest segment's radius
RISE = 15.5                                     # how far the head can lift


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def spine(p):
    """Points along the body, tail (t = 0) to head (t = 1): (x, y, z)."""
    pts = []
    L = LENGTH * p['reach']
    for i in range(N):
        t = i / (N - 1)
        lift = RISE * p['rise'] * smooth((t - 0.18) / 0.82) ** 1.15
        x = -5.5 + L * t - 8.5 * p['rise'] * smooth((t - 0.15) / 0.85) * (0.6 + p['coil'])      # the neck gathers back as it rears
        x += p['fwd'] * smooth((t - 0.5) / 0.5) + p['shift']
        bow = p['bow'] * 4.5 * smooth((t - 0.78) / 0.22)                                      # the head dips on the strike
        y = R_MAX * 0.8 + lift - bow
        x += p['bow'] * 3.2 * smooth((t - 0.78) / 0.22)
        amp = p['amp'] * 1.35 * (1.0 - 0.72 * t)
        z = amp * math.sin(2 * math.pi * (1.35 * t) - p['phase'])
        y += p['sag'] * 1.6 * math.sin(math.pi * t) * (1 - t) if p['sag'] else 0.0
        pts.append([x, y, z])
    return pts


def frame_of(pts, i):
    """Where segment i points: pitch (about z) and yaw (about y), from its neighbours."""
    a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    pitch = math.atan2(dy, math.hypot(dx, dz))
    yaw = math.atan2(-dz, dx)
    return mm(ry(yaw), rz(pitch)), (dx, dy, dz)


def radius(t):
    """The fatness at t along the body: slim at the tail fin, full through the middle, narrower to the head."""
    if t < 0.5:
        return 0.38 + 0.62 * smooth(t / 0.5)
    return 1.0 - 0.34 * smooth((t - 0.5) / 0.5)


# hand-placed bolts: each is a zig-zag path in (along, up, across) steps, a main stroke and a fork that leaves it part-way, so it reads as lightning at 1x
BOLT_UP = ((0.0, 0.0, 0.0), (1.4, 1.5, 1.2), (-0.1, 3.0, -0.9), (1.7, 4.5, 0.8), (0.3, 6.0, -0.5), (1.5, 7.3, 0.4))
BOLT_FORK = ((0.0, 0.0, 0.0), (1.7, 0.6, 1.5), (2.4, 1.9, 1.2), (3.6, 2.6, 2.2))
BOLT_FWD = ((0.0, 0.0, 0.0), (1.8, -0.9, 1.2), (2.9, 0.9, -1.1), (4.6, -0.6, 0.9), (6.0, 0.7, -0.5))
BOLT_FORK_FWD = ((0.0, 0.0, 0.0), (1.2, 1.4, 1.0), (2.2, 2.5, 1.7))


def lay(shape, origin, M, size=1.0, flip=(1.0, 1.0)):
    """The points of `shape` carried to `origin`, turned by M, scaled, with the along and across axes flipped as `flip` says."""
    return [add(origin, mv(M, (a * size * flip[0], b * size, c * size * flip[1]))) for a, b, c in shape]


def stroke(pts, width, name):
    """A path as small ellipsoids laid end to end in cyan, with a pale core ball at every joint."""
    out = []
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        ln = math.sqrt(sum(c * c for c in d)) or 1.0
        out.append(part(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), (ln / 2 + 0.3, width, width), 'arc', name,
                        mm(ry(math.atan2(-d[2], d[0])), rz(math.atan2(d[1], math.hypot(d[0], d[2]))))))
    for k in range(1, len(pts) - 1):
        out.append(part(pts[k], (width * 0.8, width * 0.8, width * 0.8), 'spark', name))
    return out


def bolt(origin, M, size, flip, fork_flip, name, main=BOLT_UP, fork=BOLT_FORK, at=2):
    """A hand-placed forked bolt: the main stroke and a fork leaving it at point `at`."""
    pts = lay(main, origin, M, size, flip)
    return stroke(pts, 0.62, name) + stroke(lay(fork, pts[at], M, size, fork_flip), 0.5, name)


def anatomy(p):
    pts = spine(p)
    parts = []
    step = LENGTH * p['reach'] / (N - 1)
    open_ = p['open']
    for i, (x, y, z) in enumerate(pts):
        t = i / (N - 1)
        R, _ = frame_of(pts, i)
        r = R_MAX * radius(t)
        along = max(1.5, step * 0.95)
        parts.append(part((x, y, z), (along, r * 0.98, r * 0.88), 'back', 'seg%d' % i, R))
        parts.append(part(add((x, y, z), mv(R, (0.0, -r * 0.5, 0.0))), (along * 0.97, r * 0.64, r * 0.8), 'belly', 'belly%d' % i, R))
        if 0.06 < t < 0.96 and i % 1 == 0:                                       # the dorsal fin ridge: a thin sail along the back
            parts.append(part(add((x, y, z), mv(R, (0.0, r * 0.92, 0.0))), (along * 1.05, r * 0.52 * (1.0 - 0.45 * t), 0.3), 'fin', 'fin', R))
        if 0.12 < t < 0.88 and i % 3 == 1:                                       # the electric organs: glowing dashes along each flank
            grow = 0.8 + 1.1 * p['glow']
            for side in (-1, 1):
                parts.append(part(add((x, y, z), mv(R, (0.0, -r * 0.12, side * r * 0.9))), (along * 0.75 * grow, 0.4 * grow, 0.4 * grow), 'organ', 'organ%d%d' % (i, side), R))
    # the tail: a thin flattened fin ending the body
    x, y, z = pts[0]
    R, _ = frame_of(pts, 0)
    parts.append(part(add((x, y, z), mv(R, (-2.0, 0.0, 0.0))), (2.4, 0.9, 0.35), 'fin', 'tailfin', R))
    # the head: a narrow, pointed wedge of a head and a small lower jaw that drops a little when it opens
    x, y, z = pts[-1]
    R, d = frame_of(pts, N - 1)
    hr = R_MAX * radius(1.0)
    parts.append(part(add((x, y, z), mv(R, (1.9, 0.1, 0.0))), (2.9, hr * 0.78, hr * 0.7), 'back', 'head', R))
    parts.append(part(add((x, y, z), mv(R, (4.3, -0.05, 0.0))), (1.7, hr * 0.5, hr * 0.46), 'back', 'snout', R))
    jaw = mm(R, rz(-0.55 * open_))
    parts.append(part(add((x, y, z), mv(R, (2.9 + 0.3 * open_, -hr * 0.62 - 0.9 * open_, 0.0))), (2.1, hr * 0.28, hr * 0.46), 'jaw', 'jaw', jaw))
    parts.append(part(add((x, y, z), mv(R, (4.6, -hr * 0.18 - 0.1 * open_, 0.0))), (1.5 + 0.5 * open_, 0.2, hr * 0.36), 'mouth', 'mouth', R))
    for side in (-1, 1):
        if p['eyes'] == 'open':
            parts.append(part(add((x, y, z), mv(R, (2.6, hr * 0.3, side * hr * 0.64))), (0.55, 0.55, 0.45), 'eye', 'eye%d' % (side > 0), R))
        else:
            parts.append(part(add((x, y, z), mv(R, (2.6, hr * 0.28, side * hr * 0.68))), (0.7, 0.18, 0.35), 'shut', 'eye%d' % (side > 0), R))
    # electricity: hand-placed bolts jumping off the body at the points the pose names, and a bolt from the head
    for k, (t, fx, fz, size) in enumerate(p['arcs']):
        i = min(N - 1, max(0, int(round(t * (N - 1)))))
        px, py, pz = pts[i]
        parts += bolt((px, py + 1.0, pz), I3, size, (fx, fz), (-fx, fz), 'bolt%d' % k)
    if p['head_bolt']:
        hx, hy, hz = add((x, y, z), mv(R, (5.8, 0.0, 0.0)))
        parts += bolt((hx, hy, hz), R, p['head_bolt'], (1.0, 1.0), (1.0, -1.0), 'headbolt', BOLT_FWD, BOLT_FORK_FWD, 2)
    return parts


def place(p):
    g = mm(rz(deg(p['roll'])), ry(deg(p['yaw'])))
    placed = []
    for q in anatomy(p):
        c = tuple(q['c'][i] + (p['lift'] if i == 1 else 0.0) for i in range(3))
        placed.append(dict(q, c=mv(g, c), R=mm(g, q['R'])))
    return placed, []


BASE = dict(shift=0.0, reach=1.0, rise=0.55, coil=0.0, fwd=0.0, bow=0.0, amp=1.5, phase=0.0, sag=0.0, open=0.0, glow=0.35, arcs=(), head_bolt=0.0, spin=0.0, roll=0, yaw=-15, lift=0.0, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def slither(k, n=8):
    """One frame of the slither: the body undulates in place, the electric organs pulse and a spark flickers on the back."""
    a = 2 * math.pi * k / n
    flick = ((0.5 + 0.06 * (k % 3), 1.0 if k % 4 == 0 else -1.0, 1.0, 0.45),) if k % 2 == 0 else ()
    return pose(phase=a, rise=0.5 + 0.05 * math.sin(a), glow=0.35 + 0.3 * (0.5 + 0.5 * math.sin(2 * a)), arcs=flick, spin=float(k))


# arcs: (where along the body 0..1, along flip, across flip, size)
CHARGE_ARCS = ((0.42, 1.0, 1.0, 0.8), (0.6, -1.0, -1.0, 0.8), (0.78, 1.0, -1.0, 0.7), (0.3, -1.0, 1.0, 0.7))


class SparkEel:
    name = 'spark-eel'
    kind = 'creature'
    airborne = set()
    ramps = RAMPS
    scale = 1.2
    eye_colour = None
    stand = pose()

    poses = {
        # ready: reared up, head swaying, the organs blazing and arcs crawling over the back
        'charging': [pose(rise=0.8, amp=1.6, phase=0.9, glow=1.0, arcs=CHARGE_ARCS, spin=2.0)],
        # coil back, lunge head forward and down throwing a bolt, hold, recover
        'attack': [
            pose(rise=0.76, coil=0.5, amp=1.2, phase=1.6, glow=0.8, bow=-0.4, shift=0.0, arcs=(), spin=1.0),
            pose(rise=0.7, reach=0.75, bow=0.6, fwd=0.2, shift=-1.1, amp=0.8, phase=2.4, glow=1.0, open=0.9, head_bolt=0.9, spin=3.0),
            pose(rise=0.6, reach=0.75, bow=0.55, fwd=0.3, shift=-1.6, amp=0.8, phase=2.8, glow=1.0, open=0.6, head_bolt=0.8, arcs=CHARGE_ARCS[1:3], spin=5.0),
            pose(rise=0.6, bow=0.2, fwd=1.0, amp=1.5, phase=3.4, glow=0.55, arcs=(), spin=2.0),
        ],
        # a discharge: reared up high, every organ blazing, arcs flung out all round
        'release': [pose(rise=0.88, coil=0.4, amp=1.0, phase=0.4, glow=1.0, open=0.5,
                         arcs=((0.45, 1.0, 1.0, 0.85), (0.6, -1.0, -1.0, 0.85), (0.74, 1.0, -1.0, 0.8), (0.88, -1.0, 1.0, 0.7)), spin=4.0)],
        # a flinch: whipped back, eyes shut, the glow stuttering
        'damage': [pose(rise=0.65, bow=-0.6, fwd=-3.0, amp=2.6, phase=3.0, glow=0.9, eyes='shut', open=0.7, arcs=((0.6, 1.0, 1.0, 0.7),), spin=6.0)],
        # worn out: slumped low, head down, the organs dark
        'weak': [pose(rise=0.15, bow=0.5, amp=2.4, phase=0.7, glow=0.0, eyes='shut', sag=0.6)],
        # limp on its side, belly flopped over, no light left
        'dead': [pose(rise=0.0, reach=1.05, roll=165, amp=2.6, phase=0.6, glow=0.0, eyes='shut', lift=0.0, shift=-0.5)],
        'walking': [slither(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = SparkEel()


def _facing_se(q, low):
    """The SE view: the head points down and to the right with the body side-on (not at the camera): yaw 0, and the neck sags so the head drops below the coil."""
    q = dict(q, yaw=0)
    if low:
        q.update(rise=q['rise'] * 0.75, bow=q['bow'] + 0.6, head_bolt=q['head_bolt'] * 0.35, shift=q['shift'] - (2.5 if q['head_bolt'] else 0.0))
    return q


for _action in ('walking', 'charging', 'attack', 'release', 'damage', 'weak', 'dead'):
    CREATURE.poses[_action + 'SE'] = [_facing_se(q, _action not in ('weak', 'dead')) for q in CREATURE.poses[_action]]

if __name__ == '__main__':
    run(CREATURE)
