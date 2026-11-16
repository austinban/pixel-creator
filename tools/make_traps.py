#!/usr/bin/env python3
"""Traps for the ground: caltrops, a bear trap, a snare, a spike pit, a tripwire and a mine, each placed (as it waits) and triggered (an animation).

Built as small 3D models of ellipsoids, the way the vine spell is (see make_vine.py and creature.py), then rendered into 32 x 32 cells in the shared colour roles.
Both lie flat on a ground tile. The model's origin is the middle of the tile, on the ground, and lands on the anchor of each cell.

    python3 tools/make_traps.py --model previews/traps-3d.png            look at the 3D models first
    python3 tools/make_traps.py --preview previews/traps.png             the sprites, enlarged, as they will be drawn

Caltrops (`trap-caltrops`, one frame; `trap-caltrops-triggered`, 6 frames): five iron jacks, four spikes each, lying scattered. Triggered, they flash, jump,
tumble in a ring of dust and fall back spread wider.
Bear trap (`trap-beartrap`, one frame; `trap-beartrap-triggered`, 6 frames): a toothed pair of jaws lying open round a pressure pan, with a short chain.
Triggered, the pan drops, the jaws swing up and snap shut, and it rests closed.
Snare (`trap-snare`, `trap-snare-triggered`, 6 frames): a rope noose lying open, its line tied off to a peg. Triggered, it draws tight and leaps up on its taut line.
Spike pit (`trap-spikepit`, `trap-spikepit-triggered`, 6 frames): a dark square hole framed in boards, sharpened stakes standing in it. Triggered, they thrust up in a burst of dust.
Tripwire (`trap-tripwire`, `trap-tripwire-triggered`, 6 frames): a thin pale cord taut between two little stakes. Triggered, it bows, snaps and the ends whip back.
Mine (`trap-mine`, `trap-mine-triggered`, 6 frames): a small iron disc with a fuse nub, half buried. Triggered, the fuse fizzes, it bursts in fire and smoke and leaves a scorched crater.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from creature import add, mm, part, rx, ry, rz  # noqa: E402
from fx import hashed  # noqa: E402

CELL = 32
ORIGIN = (16.0, 24.0)            # where the model's origin (the middle of the tile, on the ground) lands in the cell
ANCHOR = (16, 24)               # the same point, for the game
FPS = 10
SCALE = 1.3                      # the models are drawn this much larger, so the pieces are more than a pixel or two

RAMPS = {
    'iron': ('p', 'l', 'k', 'w'),         # steel, lavender, indigo, grape
    'tip': ('r', 'q', 'p', 'l'),          # a bright steel edge: mint, teal, steel, lavender
    'rust': ('a', 'g', 'w', 'x'),         # rust, plum, grape, eggplant (the palette has no true brown)
    'brass': ('b', 'a', 'g', 'w'),        # a dull gold spring: amber, orange, plum, grape
    'dust': ('t', 'C', 'b', 'a'),         # pale sand kicked up: cream, sand, amber, orange
    'spark': ('t', 'd', 'b', 'a'),        # cream, yellow, amber, orange
    'rope': ('C', 'b', 'a', 'g'),         # hemp: sand, amber, orange, plum
    'cord': ('t', 't', 'C', 'b'),         # a thin pale cord, kept light so a one-pixel line still shows
    'wood': ('b', 'a', 'g', 'w'),         # stakes and boards: amber, orange, plum, grape
    'bone': ('t', 'C', 'C', 'b'),         # the pale cut points of sharpened stakes
    'pit': ('w', 'x', 'O', 'O'),          # the dark inside of a hole
    'earth': ('a', 'g', 'w', 'x'),        # turned earth: orange, plum, grape, eggplant
    'char': ('w', 'x', 'O', 'O'),         # a scorched crater
    'fire': ('t', 'd', 'd', 'b'),         # the white-hot heart of a blast
    'flame': ('d', 'b', 'a', 'e'),        # yellow, amber, orange, coral (the billows' edges fall to coral)
    'ember': ('b', 'a', 'e', 'h'),        # the darker, redder billows of a blast: amber, orange, coral, dark magenta
    'smoke': ('C', 'p', 'l', 'k'),        # sand-lit grey smoke: sand, steel, lavender, indigo
}


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def along(direction, up=(0.0, 1.0, 0.0)):
    """An orientation whose x axis runs along `direction` and whose y axis is as close to `up` as it can be."""
    ex = norm(direction)
    d = sum(a * b for a, b in zip(up, ex))
    ey = norm(tuple(u - d * e for u, e in zip(up, ex))) if abs(d) < 0.98 else norm(cross(ex, (0.0, 0.0, 1.0)))
    ez = cross(ex, ey)
    return [[ex[i], ey[i], ez[i]] for i in range(3)]


def spike(base, direction, length, radius, name, mat='iron', tip='tip'):
    """A tapering spike from `base` along `direction`: three ellipsoids, thick to fine, the last a bright steel point."""
    d = norm(direction)
    R = along(d)
    out = []
    for k, (t0, t1, rr, m) in enumerate(((0.0, 0.42, 1.0, mat), (0.38, 0.72, 0.68, mat), (0.68, 1.0, 0.38, tip))):
        a = tuple(base[i] + d[i] * length * t0 for i in range(3))
        b = tuple(base[i] + d[i] * length * t1 for i in range(3))
        mid = tuple((a[i] + b[i]) / 2 for i in range(3))
        out.append(part(mid, (length * (t1 - t0) / 2 + 0.25, radius * rr, radius * rr), m, name, R))
    return out


# --- caltrops -------------------------------------------------------------------
# five jacks: where each lies on the ground (x, z) and how it is turned
JACKS = [((0.0, 0.0), 0.3, 0.2), ((5.2, -3.4), 1.9, 0.5), ((-5.0, 2.6), 4.0, 0.3), ((2.8, 5.6), 2.6, 0.7), ((-3.0, -5.8), 5.4, 0.4)]
PRONG = 3.3


def jack(at, yaw, lean, lift=0.0, spin=0.0, flash=False):
    """One caltrop: four spikes from a hub, one up and three splayed down, so that it always rests on three points and points up with the fourth."""
    x, y, z = at
    parts = []
    hub_y = 0.95 * PRONG * 0.34 + y + lift
    centre = (x, hub_y, z)
    parts.append(part(centre, (0.9, 0.9, 0.9), 'iron', f'hub{x:.0f}{z:.0f}'))
    tip = 'spark' if flash else 'tip'
    dirs = [(0.0, 1.0, 0.0)] + [(math.cos(a) * 0.94, -0.34, math.sin(a) * 0.94) for a in (0.0, 2.094, 4.189)]
    tilt = mm(ry(yaw + spin), rz(lean + spin * 0.6))
    for n, d in enumerate(dirs):
        dd = tuple(sum(tilt[i][j] * d[j] for j in range(3)) for i in range(3))
        parts += spike(centre, dd, PRONG, 0.8, f'jack{x:.0f}{z:.0f}{n}', tip=tip)
    return parts


def caltrops(spread=1.0, lift=0.0, spin=0.0, flash=False, dust=0.0):
    parts = []
    for n, ((x, z), yaw, lean) in enumerate(JACKS):
        hop = lift * (0.7 + 0.3 * ((n * 3) % 5) / 4)
        parts += jack((x * spread, 0.0, z * spread), yaw + n * spin * 0.7, lean, hop, spin * (1 if n % 2 else -1), flash)
    if dust > 0:
        parts += dust_ring(dust)
    return parts


def dust_ring(amount):
    """Puffs of dust in a ring round the middle, spreading and rising as `amount` grows."""
    out = []
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.5
        d = 3.0 + 6.0 * amount
        size = 0.7 + 1.2 * amount * (0.8 + 0.4 * ((k * 5) % 3) / 2)
        out.append(part((math.cos(a) * d, 0.5 + 2.2 * amount, math.sin(a) * d), (size, size * 0.8, size), 'dust', f'puff{k}'))
    return out


CALTROP_FRAMES = [
    dict(name='stepped on', spread=1.0, lift=0.0, spin=0.0, flash=True, dust=0.0),
    dict(name='pop', spread=1.05, lift=3.2, spin=0.5, flash=True, dust=0.25),
    dict(name='tumble', spread=1.1, lift=6.0, spin=1.3, flash=False, dust=0.6),
    dict(name='fall', spread=1.15, lift=3.2, spin=2.0, flash=False, dust=0.9),
    dict(name='land', spread=1.2, lift=0.6, spin=2.6, flash=False, dust=0.7),
    dict(name='rest', spread=1.22, lift=0.0, spin=2.7, flash=False, dust=0.35),
]


# --- bear trap ------------------------------------------------------------------
JAW_R = 6.4                      # the radius of each jaw's half-ring
HINGE_Z = 0.9                    # the hinge line of each jaw, either side of the pan
TEETH = 6


def jaw(side, theta, pressed):
    """One jaw: a half-ring of iron with teeth, hinged beside the pan and swung up by `theta` degrees about its hinge (side is +1 or -1)."""
    parts = []
    swing = rx(-side * math.radians(theta))
    hinge = (0.0, 0.7, side * HINGE_Z)

    def carry(p, R):
        rel = (p[0] - hinge[0], p[1] - hinge[1], p[2] - hinge[2])
        w = tuple(sum(swing[i][j] * rel[j] for j in range(3)) for i in range(3))
        return add(hinge, w), mm(swing, R)

    ring = 11
    for k in range(ring):
        t0, t1 = math.pi * k / ring, math.pi * (k + 1) / ring
        a = (JAW_R * math.cos(t0), 0.7, side * (HINGE_Z + JAW_R * math.sin(t0)))
        b = (JAW_R * math.cos(t1), 0.7, side * (HINGE_Z + JAW_R * math.sin(t1)))
        mid = tuple((a[i] + b[i]) / 2 for i in range(3))
        c, R = carry(mid, along((b[0] - a[0], 0.0, b[2] - a[2])))
        parts.append(part(c, (math.dist(a, b) / 2 + 0.35, 0.85, 0.85), 'iron', f'jaw{side}', R))
    for k in range(TEETH):                                          # teeth on the ring, pointing up when flat and so across the gap when shut
        t = math.pi * (k + 0.5 + (0.5 if side > 0 else 0.0)) / (TEETH + 0.5)
        p = ((JAW_R - 0.2) * math.cos(t), 1.6, side * (HINGE_Z + (JAW_R - 0.2) * math.sin(t)))
        c, R = carry(p, I3)
        parts.append(part(c, (0.55, 1.2, 0.55), 'tip', f'jaw{side}', R))
    return parts


I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def beartrap(theta=0.0, pressed=False, shake=0.0, dust=0.0, spark=False):
    parts = []
    drop = 0.35 if pressed else 0.0
    parts.append(part((0.0, 0.3, 0.0), (3.2, 0.45, 1.9), 'rust', 'plate'))                    # the base plate
    parts.append(part((0.0, 0.75 - drop, 0.0), (1.3, 0.3, 1.3), 'brass', 'pan'))              # the pressure pan
    for sx in (-1, 1):                                                                         # the leaf springs at either end
        parts.append(part((sx * 4.2, 0.55, 0.0), (1.3, 0.35, 1.1), 'brass', f'spring{sx}'))
    for k in range(5):                                                                         # a short chain off the back, laid in a bend
        parts.append(part((-4.6 - k * 1.5, 0.45, math.sin(k * 0.9) * 1.1), (0.95, 0.4, 0.55), 'iron', f'link{k}', ry(0.5 * k) if k % 2 else I3))
    parts += jaw(1, theta, pressed) + jaw(-1, theta, pressed)
    if shake:                                                                                  # the snap jolts the whole trap a little
        parts = [dict(q, c=(q['c'][0] + shake, q['c'][1], q['c'][2])) for q in parts]
    if dust > 0:
        parts += dust_ring(dust)
    if spark:
        for k in range(5):
            a = k * 2 * math.pi / 5 + 0.3
            parts.append(part((math.cos(a) * 3.6, 6.0 + (k % 2) * 1.8, math.sin(a) * 3.6), (0.5, 0.5, 0.5), 'spark', f'spark{k}'))
    return parts


BEARTRAP_FRAMES = [
    dict(name='pressed', theta=0.0, pressed=True, dust=0.0),
    dict(name='jaws lift', theta=24.0, pressed=True, dust=0.15),
    dict(name='swing', theta=58.0, pressed=True, dust=0.3),
    dict(name='closing', theta=84.0, pressed=True, dust=0.55, spark=True),
    dict(name='snap', theta=92.0, pressed=True, dust=0.8, shake=0.7, spark=True),
    dict(name='shut', theta=88.0, pressed=True, dust=0.45),
]

def rope(points, mat, name, radius=0.55):
    """A cord through `points`: one thin ellipsoid on each span, overlapping a little so it reads as one line."""
    out = []
    for a, b in zip(points, points[1:]):
        mid = tuple((a[i] + b[i]) / 2 for i in range(3))
        out.append(part(mid, (math.dist(a, b) / 2 + radius * 0.6, radius, radius), mat, name, along(tuple(b[i] - a[i] for i in range(3)))))
    return out


def stake(x, z, height, name, mat='wood', lean=(0.0, 0.0)):
    """A little wooden peg driven into the ground, with a lighter cut top."""
    top = (x + lean[0], height, z + lean[1])
    return [part(((x + top[0]) / 2, height / 2, (z + top[2]) / 2), (height / 2 + 0.2, 0.8, 0.8), mat, name, along((lean[0], height, lean[1]))),
            part(top, (0.8, 0.35, 0.8), 'rope' if mat == 'wood' else mat, name + 'top')], top


def shaken(parts, dx):
    return [dict(q, c=(q['c'][0] + dx, q['c'][1], q['c'][2])) for q in parts]


# --- snare ----------------------------------------------------------------------
SNARE_C = (1.6, 0.0, 1.0)        # the middle of the noose
SNARE_PEG = (-6.2, 3.8)          # where its peg is driven in: to the left of the noose as the camera sees it


def snare(radius=4.4, lift=0.0, tilt=0.0, tug=0.0, dust=0.0, shake=0.0):
    """A rope noose lying open on the ground, its running knot tied off to a peg. Sprung, the loop draws tight and leaps up on its taut line, turning on its edge."""
    parts, top = stake(SNARE_PEG[0], SNARE_PEG[1], 4.2, 'peg', lean=(-0.6 * tug, -0.3 * tug))
    cx, cy, cz = SNARE_C[0] - 1.2 * tug, 0.55 + lift, SNARE_C[2] - 0.6 * tug
    turn = about(SCREEN_ACROSS, tilt)                                               # sprung, the loop stands up facing the camera, so it reads as a ring
    ring = []
    for k in range(15):
        t = 2 * math.pi * k / 14 + math.pi + 0.35
        p = mv3(turn, (radius * math.cos(t), 0.0, radius * math.sin(t) * 0.95))
        ring.append((cx + p[0], cy + p[1], cz + p[2]))
    parts += rope(ring, 'rope', 'loop')
    knot = ring[0]
    parts.append(part(knot, (0.95, 0.75, 0.95), 'rope', 'knot'))
    sag = 0.0 if lift > 0.5 else 0.5                                                  # lying, the line sags along the ground; sprung, it is drawn straight and taut
    if lift <= 0.5:                                                                   # lying, it is tied low on the peg; sprung, it has run up to the peg's head
        top = (SNARE_PEG[0] + (top[0] - SNARE_PEG[0]) * 0.4, top[1] * 0.4, SNARE_PEG[1] + (top[2] - SNARE_PEG[1]) * 0.4)
    line = [(knot[0] + (top[0] - knot[0]) * s, knot[1] + (top[1] - knot[1]) * s - sag * math.sin(math.pi * s), knot[2] + (top[2] - knot[2]) * s + sag * 2 * math.sin(math.pi * s))
            for s in (0.0, 0.25, 0.5, 0.75, 1.0)]
    parts += rope(line, 'rope', 'line', 0.5)
    if shake:
        parts = shaken(parts, shake)
    if dust > 0:
        parts += [dict(q, c=(q['c'][0] + SNARE_C[0], q['c'][1], q['c'][2] + SNARE_C[2]), r=tuple(x * 0.7 for x in q['r'])) for q in dust_ring(dust * 0.7)]
    return parts


SCREEN_ACROSS = (0.7071, 0.0, -0.7071)    # the model direction that runs straight across the screen in the SE view
SCREEN_DEPTH = (0.7071, 0.0, 0.7071)      # and the one that runs towards the camera


def about(axis, a):
    """The rotation by `a` radians about a unit `axis` (Rodrigues)."""
    x, y, z = axis
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def mv3(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


SNARE_FRAMES = [
    dict(name='tug', radius=4.0, lift=0.0, tilt=0.0, tug=0.3, dust=0.15),
    dict(name='jerk', radius=3.2, lift=2.2, tilt=0.5, tug=0.7, dust=0.4),
    dict(name='snap up', radius=2.6, lift=5.6, tilt=1.1, tug=1.0, dust=0.7, shake=0.6),
    dict(name='whip', radius=2.2, lift=8.4, tilt=1.57, tug=1.0, dust=0.45),
    dict(name='bounce', radius=2.2, lift=6.6, tilt=1.45, tug=1.0, dust=0.2),
    dict(name='held tight', radius=2.2, lift=7.4, tilt=1.5, tug=1.0, dust=0.0),
]


# --- spike pit ------------------------------------------------------------------
PIT = 5.2                        # the half-width of the pit's square mouth
STAKES = [(x, z) for x in (-3.2, 0.0, 3.2) for z in (-3.2, 0.0, 3.2)]


def spikepit(reach=1.9, dust=0.0, shake=0.0):
    """A dark square hole framed in boards, with nine sharpened stakes standing in it. Sprung, they thrust up out of it in a burst of dust."""
    parts = [part((0.0, 0.05, 0.0), (PIT, 0.2, PIT), 'pit', 'pit', box=True)]
    for k, (sx, sz) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):                       # the frame of boards round the mouth
        long = (PIT + 0.7, 0.4, 0.6) if sx == 0 else (0.6, 0.4, PIT + 0.7)
        parts.append(part((sx * (PIT + 0.1), 0.35, sz * (PIT + 0.1)), long, 'wood', f'board{k}', box=True))
    for k, (x, z) in enumerate(STAKES):
        lean = ((hashed_unit(k, 1) - 0.5) * 0.35, 1.0, (hashed_unit(k, 2) - 0.5) * 0.35)
        length = reach * (0.8 + 0.4 * hashed_unit(k, 3))
        parts += spike((x, -0.4, z), lean, length + 0.4, 0.75, f'stake{k}', mat='rust', tip='bone')
    if shake:
        parts = shaken(parts, shake)
    if dust > 0:
        parts += dust_ring(dust)
    return parts


def hashed_unit(a, b):
    """A fixed number between 0 and 1 for (a, b), the same every run."""
    return hashed(a, b, 17)


SPIKEPIT_FRAMES = [
    dict(name='give', reach=1.2, dust=0.15),
    dict(name='thrust', reach=5.0, dust=0.4, shake=0.5),
    dict(name='full', reach=8.0, dust=0.75),
    dict(name='settle', reach=7.0, dust=0.6),
    dict(name='dust falls', reach=6.6, dust=0.35),
    dict(name='bristling', reach=6.6, dust=0.0),
]


# --- tripwire -------------------------------------------------------------------
WIRE_A, WIRE_B = (-6.8, -1.2), (6.8, 1.2)    # the two stakes, across the tile
WIRE_H = 2.2


def tripwire(bow=0.0, gap=-1.0, curl=0.0, lie=0.0, lean=0.0, spark=False, dust=0.0):
    """A thin pale cord drawn taut between two little stakes, a shin's height up. Sprung, it bows, snaps in the middle and the two ends whip back round their stakes.

    `bow` pushes the middle aside; `gap` >= 0 means it has snapped, the two ends drawn back that far from the middle; `curl` lifts and swings the loose ends; `lie` drops them to the ground."""
    pa, ta = stake(WIRE_A[0], WIRE_A[1], WIRE_H + 1.0, 'stakeA', lean=(lean, 0.0))
    pb, tb = stake(WIRE_B[0], WIRE_B[1], WIRE_H + 1.0, 'stakeB', lean=(-lean, 0.0))
    parts = pa + pb
    ta, tb = (ta[0], ta[1] - 0.9, ta[2]), (tb[0], tb[1] - 0.9, tb[2])
    if gap < 0:                                                                     # whole: a straight cord, or bowed in the middle
        pts = []
        for k in range(9):
            s = k / 8
            p = [ta[i] + (tb[i] - ta[i]) * s for i in range(3)]
            b = bow * math.sin(math.pi * s)
            pts.append((p[0] - b * 0.2, p[1] - b * 0.35, p[2] + b))
        parts += rope(pts, 'cord', 'cord', 0.42)
    else:                                                                           # snapped: each half runs from its stake to a loose end that whips
        for side, (t0, t1) in enumerate(((ta, tb), (tb, ta))):
            sgn = 1 if side == 0 else -1
            step = math.dist(t0, t1) * 0.5 / 5
            d0 = norm(tuple(t1[i] - t0[i] for i in range(3)))
            p = list(t0)
            pts = [tuple(p)]
            for k in range(5):                                                      # each span turns a little more, curling up and back in the plane facing the camera
                d = mv3(about(SCREEN_DEPTH, -sgn * curl * 0.55 * (k + 1)), d0)
                p = [p[i] + d[i] * step for i in range(3)]
                p[1] = max(0.4, p[1] - lie * (WIRE_H - 0.4) * (k + 1) / 5)
                pts.append(tuple(p))
            parts += rope(pts, 'cord', f'half{side}', 0.42)
    if spark:
        for k in range(5):
            a = k * 2 * math.pi / 5 + 0.4
            parts.append(part((math.cos(a) * 1.8, WIRE_H + 1.0 + math.sin(a) * 1.6, math.sin(a) * 0.8), (0.5, 0.5, 0.5), 'spark', f'spark{k}'))
    if dust > 0:
        parts += [dict(q, r=tuple(x * 0.6 for x in q['r'])) for q in dust_ring(dust * 0.6)]
    return parts


TRIPWIRE_FRAMES = [
    dict(name='caught', bow=1.0, lean=0.3),
    dict(name='strain', bow=1.9, lean=0.7, dust=0.15),
    dict(name='snap', gap=0.5, curl=0.25, lean=0.4, spark=True, dust=0.3),
    dict(name='whip', gap=2.0, curl=1.0, lean=0.1, dust=0.45),
    dict(name='lash', gap=3.0, curl=1.5, lie=0.3, lean=-0.2, dust=0.3),
    dict(name='slack', gap=3.0, curl=0.3, lie=1.0, lean=0.0),
]


# --- mine -----------------------------------------------------------------------
def mine(buried=1.0, fuse=False, fire=0.0, smoke=0.0, puff=1.0, clods=0.0, crater=False):
    """A small iron disc with a fuse nub, buried flush and half covered in earth. Sprung, the fuse fizzes, it bursts in fire and flung earth, and smoke rolls up off a scorched crater."""
    parts = []
    if crater:
        parts.append(part((0.0, 0.1, 0.0), (5.0, 0.3, 4.4), 'char', 'crater'))
        for k in range(7):                                                            # a lip of thrown earth round it
            a = k * 2 * math.pi / 7 + 0.2
            parts.append(part((math.cos(a) * 5.4, 0.35, math.sin(a) * 4.8), (1.5, 0.6, 1.2), 'earth', f'lip{k}', ry(-a)))
    else:
        parts.append(part((0.0, 0.45, 0.0), (3.6, 0.75, 3.6), 'iron', 'disc'))
        parts.append(part((0.0, 1.1, 0.0), (1.5, 0.45, 1.5), 'iron', 'boss'))
        parts.append(part((0.9, 1.8, -0.6), (0.6, 0.9, 0.6), 'brass', 'fuse'))
        if buried:
            for k in range(5):                                                        # earth heaped over the back half, so it lies half buried
                a = math.pi * (0.75 + k * 0.2)
                parts.append(part((math.cos(a) * 3.6, 0.6, math.sin(a) * 3.6), (1.7, 0.8, 1.3), 'earth', f'heap{k}', ry(-a)))
        if fuse:
            parts.append(part((1.0, 2.9, -0.7), (0.85, 0.85, 0.85), 'spark', 'fizz'))
            for k in range(3):
                parts.append(part((1.0 + math.cos(k * 2.1) * 1.2, 3.0 + (k % 2) * 0.8, -0.7 + math.sin(k * 2.1) * 1.0), (0.4, 0.4, 0.4), 'spark', f'fizz{k}'))
    if fire > 0:                                                                      # a fireball of separate billows (so each gets its own shaded edge), round a white-hot heart
        r = 1.8 + 3.0 * fire
        for k in range(6):
            a = k * 2 * math.pi / 6 + 0.6
            b = r * (0.5 + 0.12 * (k % 3))
            parts.append(part((math.cos(a) * r * 0.6, 1.0 + r * (0.55 + 0.35 * (k % 2)), math.sin(a) * r * 0.6), (b, b * 0.9, b), 'flame' if k % 2 else 'ember', f'billow{k}'))
        parts.append(part((0.0, 1.0 + r * 1.25, 0.0), (r * 0.5, r * 0.5, r * 0.5), 'ember', 'crown'))
        parts.append(part((r * 0.55, 1.0 + r * 0.6, r * 0.55), (r * 0.45, r * 0.4, r * 0.45), 'fire', 'core'))       # in front, towards the camera, so the white heart shows
    if smoke > 0:
        for k in range(5):
            a = k * 2 * math.pi / 5 + 1.1
            d = (1.5 + 2.6 * smoke) * puff
            s = (1.2 + 1.3 * smoke) * puff
            parts.append(part((math.cos(a) * d * 0.8, 2.0 + 6.0 * smoke + (k % 2) * 1.6 * puff, math.sin(a) * d * 0.8), (s, s * 0.85, s), 'smoke', f'smoke{k}'))
    if clods > 0:
        for k in range(6):
            a = k * 2 * math.pi / 6 + 0.25
            d = 4.0 + 5.0 * clods
            parts.append(part((math.cos(a) * d, 1.0 + 6.0 * clods * (1.0 - clods * 0.5) + (k % 3), math.sin(a) * d), (0.8, 0.7, 0.8), 'earth', f'clod{k}'))
    return parts


MINE_FRAMES = [
    dict(name='fuse', fuse=True),
    dict(name='flash', fire=0.25, clods=0.2),
    dict(name='burst', fire=1.0, clods=0.6),
    dict(name='billow', fire=0.55, smoke=0.35, clods=0.95, crater=True),
    dict(name='smoke', fire=0.0, smoke=0.75, crater=True),
    dict(name='scorched', smoke=0.6, puff=0.5, crater=True),
]


TRAPS = {
    'caltrops': dict(label='Caltrops', frames=CALTROP_FRAMES, build=lambda f: caltrops(f['spread'], f['lift'], f['spin'], f['flash'], f['dust']),
                     placed=dict(spread=1.0, lift=0.0, spin=0.0, flash=False, dust=0.0)),
    'beartrap': dict(label='Bear trap', frames=BEARTRAP_FRAMES, build=lambda f: beartrap(f['theta'], f['pressed'], f.get('shake', 0.0), f['dust'], f.get('spark', False)),
                     placed=dict(theta=0.0, pressed=False, dust=0.0)),
    'snare': dict(label='Snare', frames=SNARE_FRAMES, build=lambda f: snare(**{k: v for k, v in f.items() if k != 'name'}), placed=dict()),
    'spikepit': dict(label='Spike pit', frames=SPIKEPIT_FRAMES, build=lambda f: spikepit(**{k: v for k, v in f.items() if k != 'name'}), placed=dict()),
    'tripwire': dict(label='Tripwire', frames=TRIPWIRE_FRAMES, build=lambda f: tripwire(**{k: v for k, v in f.items() if k != 'name'}), placed=dict()),
    'mine': dict(label='Mine', frames=MINE_FRAMES, build=lambda f: mine(**{k: v for k, v in f.items() if k != 'name'}), placed=dict()),
}


# --- pixels -----------------------------------------------------------------------
def render_pixels(parts):
    """One frame as CELL rows of colour-role characters, outlined like the characters."""
    import creature as cr
    rows = cr.render_frame(parts, [], 'SE', ORIGIN, RAMPS, SCALE)
    return [''.join(row) for row in rows]


def frames_of(name):
    t = TRAPS[name]
    return render_pixels(t['build'](t['placed'])), [render_pixels(t['build'](f)) for f in t['frames']]


# --- previews ---------------------------------------------------------------------
def model_sheet(size=300):
    from PIL import Image, ImageDraw
    import preview3d as pv
    bounds = [(11, 0, 11), (-11, 0, -11), (11, 0, -11), (-11, 0, 11), (0, 10, 0)]
    cols = 7
    sheet = Image.new('RGBA', (size * cols, (size + 20) * len(TRAPS)), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(TRAPS):
        t = TRAPS[name]
        shown = [('placed', t['build'](t['placed']))] + [(f['name'], t['build'](f)) for f in t['frames']]
        for i, (label, parts) in enumerate(shown):
            tile = pv.render_view(parts, [], RAMPS, -45, size, fit_points=bounds)
            sheet.alpha_composite(tile, (i * size, row * (size + 20) + 20))
            draw.text((i * size + 6, row * (size + 20) + 4), f'{t["label"]}: {label}', fill=(235, 238, 245, 255))
    return sheet


def pixel_sheet(path, scale=6, names=None, ground=None):
    """The sprites, enlarged and labelled, a row per trap; with `ground` (a 32 x 32 ground cube) each is drawn on a tile, its anchor on the middle of the tile's top."""
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    names = list(names or TRAPS)
    cols = 7
    sheet = Image.new('RGB', (cols * CELL * scale, len(names) * (CELL * scale + 16)), (50, 44, 84))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(names):
        placed, anim = frames_of(name)
        for i, rows in enumerate([placed] + anim):
            ox, oy = i * CELL * scale, row * (CELL * scale + 16) + 16
            draw.text((ox + 4, oy - 13), f'{TRAPS[name]["label"]}: ' + ('placed' if i == 0 else TRAPS[name]['frames'][i - 1]['name']), fill=(235, 238, 245))
            cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
            if ground is not None:
                cell.alpha_composite(ground, (ANCHOR[0] - 16, ANCHOR[1] - 8))
            for y, line in enumerate(rows):
                for x, ch in enumerate(line):
                    if ch != '.':
                        cell.putpixel((x, y), rgb[ch] + (255,))
            sheet.paste(cell.resize((CELL * scale, CELL * scale), Image.NEAREST), (ox, oy), cell.resize((CELL * scale, CELL * scale), Image.NEAREST))
    sheet.save(path)
    return sheet


# --- the assets ---------------------------------------------------------------------
CATEGORY = 'Traps'
FOLDER = 'traps'


def build_assets():
    """Two assets per trap, one folder: each trap placed (one frame) and triggered (an animation), by the ids trap-NAME and trap-NAME-triggered."""
    make = family(CATEGORY, CELL, CELL, ANCHOR, folder=FOLDER)
    assets = []
    for name, t in TRAPS.items():
        placed, anim = frames_of(name)
        assets.append(make(f'trap-{name}', f'{t["label"]} - placed (waiting on the ground)', 'still', [placed], trap={'name': name, 'state': 'placed'}))
        assets.append(make(f'trap-{name}-triggered', f'{t["label"]} - triggered (animation)', 'animation', anim, fps=FPS,
                           trap={'name': name, 'state': 'triggered', 'plays': 'once, then holds the last frame'}))
    return assets


def write_package(folder):
    """Beside the sheets: traps.json, how a game uses them in numbers (README.md says it in words)."""
    write_json(folder, 'traps.json', 'The trap sheets in this folder. See README.md beside this file for the whole story.', {
        'cell': CELL, 'anchor': {'x': ANCHOR[0], 'y': ANCHOR[1]}, 'fps': FPS,
        'traps': {name: {'label': t['label'], 'placed': f'trap-{name}.png', 'triggered': f'trap-{name}-triggered.png',
                         'triggeredFrames': [f['name'] for f in t['frames']], 'triggeredPlays': 'once, then hold the last frame'}
                  for name, t in TRAPS.items()},
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, help='write the 3D preview of the traps here')
    parser.add_argument('--preview', type=Path, help='write the pixel sprites, enlarged, here')
    parser.add_argument('--on-ground', action='store_true', help='draw each sprite on a ground tile in the preview')
    parser.add_argument('--only', nargs='*', help='only these traps in the preview')
    args = parser.parse_args()
    if args.model:
        args.model.parent.mkdir(parents=True, exist_ok=True)
        model_sheet().save(args.model)
        print(f'3D preview of the traps -> {args.model}; no sprites were made')
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        ground = None
        if args.on_ground:
            from PIL import Image
            ground = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA').crop((0, 0, 32, 32))
        pixel_sheet(args.preview, names=args.only, ground=ground)
        print(f'the trap sprites, enlarged -> {args.preview}')


if __name__ == '__main__':
    main()
