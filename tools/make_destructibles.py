#!/usr/bin/env python3
"""Things on the battlefield that can be broken: a wooden barricade, an explosive barrel and a stack of plain ones, a breakable stone wall, a cluster of clay urns and a hay cart.

Each piece comes in three states, one asset of kind `variants` (the frames are Intact, Damaged, Destroyed), and a short destruction animation of its own, `<id>-destroy`, 6 frames at 12 a second:

    1  the piece is lit up: a flash (a fireball for the barrel)
    2  it breaks into chunks, the chunks being its own pixels, thrown out in every direction on the ground's isometric plane, with a cloud of dust
    3  the chunks are at the top of their arc and the cloud is at its biggest; the wreck shows underneath
    4  the chunks fall
    5  the chunks land and the cloud thins
    6  the destroyed state, with a last wisp

It is the body explosion's way (tools/make_body_explosion.py: a burst, chunks on a ballistic arc that land and leave something behind) in dust colours instead of blood: bone and sand and grey stone for dust, orange and yellow for fire,
and the chunks keep the colours of what they were. All six frames and the three states of a piece are the same size and have the same anchor, so a piece can swap between them in place.

The records say what a piece is for the game: `blocks` (it occupies its cells: nothing walks through it while it is intact or damaged), `blocks_when_destroyed` (False for all: the wreck is low enough to walk over), `cover_levels` (how high it stands, in
levels of 16 pixels: more than half a level is cover), `explosive` (it goes off when destroyed), `footprint`, and `states`. Everything is in the buildings' and rocks' projection (tools/prop3d.py), palette roles only, deterministic.

    python3 tools/make_destructibles.py --preview previews/destructibles.png     every piece in its three states, then its destruction strip, at 2x on its footprint
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
import prop3d as p3  # noqa: E402
from prop3d import Scene, box, prism, noise, tint  # noqa: E402

FOLDER = 'destructibles'
CATEGORY = 'Destructibles'
FPS = 12
FRAMES = 6
PAD = 10                       # room round the piece for chunks and the cloud, all states and frames
UP = 16
STATES = ('intact', 'damaged', 'destroyed')

p3.MATERIALS['char'] = lambda s, n, P: 'x' if noise(int(P[0] * 16), int(P[1] * 16), 3) > 0.45 else 'w'
FLAME = ['..#..', '..##.', '.###.', '.####', '#####', '#####', '.###.', '..#..']


def rect(fx, fy):
    return {(i, j) for i in range(fx) for j in range(fy)}


def lump(cx, cy, rx, ry, h, seed, mat='stone', cz=0.0, yaw=None, facets=5):
    """A small broken lump standing on the ground: a faceted half-ellipsoid, for rubble and shards."""
    import make_rocks as mr
    c, r = (cx, cy, cz), (rx, ry, h * 1.15)
    b = mr.Blob(c, r, (mr.rnd(seed, 1) * math.pi) if yaw is None else yaw, seed, top=cz + h, planes=mr.facets(seed, c, r, facets, 0.65, 0.9, (8, 70)))
    b.natural, b.mat, b.style, b.end, b.features, b.decay = False, mat, 'stone', 'stone', [], []
    b.walk = False
    return b


def blob(c, r, mat, seed, top=None, yaw=0.0):
    """A smooth lump of a material (hay, clay): an ellipsoid."""
    import make_rocks as mr
    b = mr.Blob(c, r, yaw, seed, top=top)
    b.natural, b.mat, b.style, b.end, b.features, b.decay = False, mat, 'stone', 'stone', [], []
    b.walk = False
    return b


# --- the barricade ------------------------------------------------------------------------------
def barricade(fx, fy, state, seed):
    along_y = fy > fx
    L = fy if along_y else fx

    def mk(u0, u1, v0, v1, z0, z1, mat='wood', grain='x', **a):
        x0, x1, y0, y1 = (v0, v1, u0, u1) if along_y else (u0, u1, v0, v1)
        return box(x0, x1, y0, y1, z0, z1, mat, seed + int(u0 * 31 + z0 * 17), grain='y' if (grain == 'x') == along_y else 'x', worn=0.15, **a)
    n = 2 * L
    posts_u = [0.14 + k * (L - 0.28) / n for k in range(n + 1)]
    parts = []
    for k, u in enumerate(posts_u):
        h = 0.78 + 0.1 * noise(k, 1, seed)
        if state == 'destroyed':
            if k % 2 == 0:
                parts.append(mk(u - 0.06, u + 0.06, 0.44, 0.56, 0.0, 0.1 + 0.12 * noise(k, 2, seed), grain='y'))
            continue
        broken = state == 'damaged' and k in (2, 3)
        top = h - (0.3 if broken else 0.0)
        parts.append(mk(u - 0.06, u + 0.06, 0.44, 0.56, 0.0, top, grain='y'))
        if not broken:
            parts.append(p3.pyramid(*((0.5, u) if along_y else (u, 0.5)), 0.06, top, 0.2, 'wood', seed + k))
    rails = [(0.12, 0.23), (0.34, 0.45), (0.56, 0.67)]
    for r, (z0, z1) in enumerate(rails):
        for k in range(len(posts_u) - 1):
            u0, u1 = posts_u[k] - 0.03, posts_u[k + 1] + 0.03
            zz0, zz1, vv = z0, z1, (0.56, 0.64)
            if state == 'damaged':
                if r == 1 and k in (1, 2):
                    continue                                                 # planks gone from the middle
                if r == 2 and k == 2:
                    zz0, zz1, vv = z0 - 0.14, z1 - 0.14, (0.6, 0.68)          # one hanging
            if state == 'destroyed':
                # planks down on the ground, lying about
                if noise(k, r, seed + 4) > 0.45:
                    cu = 0.2 + (L - 0.4) * noise(k, r, seed + 5)
                    cv = 0.25 + 0.5 * noise(k, r, seed + 6)
                    ln = 0.35 + 0.2 * noise(k, r, seed + 7)
                    parts.append(mk(cu - ln / 2, cu + ln / 2, cv - 0.045, cv + 0.045, 0.0, 0.07 + 0.03 * r))
                continue
            parts.append(mk(u0, u1, vv[0], vv[1], zz0, zz1))
    if state == 'destroyed':
        for k in range(3):                                                    # a couple of splinters
            parts.append(lump(*(((0.3 + 0.4 * noise(k, 9, seed)), 0.2 + (L - 0.4) * noise(k, 10, seed)) if along_y else (0.2 + (L - 0.4) * noise(k, 10, seed), 0.3 + 0.4 * noise(k, 9, seed))), 0.05, 0.04, 0.05, seed + k, mat='wood'))
    return parts


# --- barrels ------------------------------------------------------------------------------------
def barrel_deco(cx, cy, explosive, state, hoops=((0.05, 0.1), (0.5, 0.55)), mark=True):
    def deco(s, n, P, role):
        x, y, z = P
        if n[2] > 0.9:
            d = math.hypot(x - cx, y - cy)
            if state == 'damaged' and explosive:                                      # the lid blown off: dark inside with sparks in it
                if d < 0.17:
                    k = noise(int(x * 16), int(y * 16), 7)
                    return 'd' if k > 0.9 else ('b' if k > 0.8 else 'w')
            if d > s.radius - 0.035:
                return 'p'
            if explosive:
                return 'd' if d < 0.045 else ('u' if (int(d * 16) % 3) else 'h')
            return 'e' if int(x * 16) % 3 else 'f'
        if abs(n[2]) < 0.6:
            for lo, hi in hoops:
                if lo <= z < hi:
                    return p3.ramp_of(p3.IRON, p3.lum_of(n))
            if explosive and mark and n[0] > 0.55 and n[1] > 0.55 and state != 'destroyed':
                hn = math.hypot(n[0], n[1])
                u = ((x - cx) * -n[1] + (y - cy) * n[0]) / hn
                a, b = int(math.floor(u * 16)) + 2, int(math.floor((z - 0.16) * 16))
                if 0 <= a < 5 and 0 <= b < 8 and FLAME[7 - b][a] == '#':
                    return 'd' if b > 2 else 'b'
            if explosive and state == 'damaged':                                       # a crack with the glow behind it
                hn = math.hypot(n[0], n[1])
                u = ((x - cx) * -n[1] + (y - cy) * n[0]) / hn
                a, b = int(math.floor(u * 16)), int(math.floor(z * 16))
                if a == int(2 * math.sin(b * 0.9)) - 3 and 3 <= b < 12:
                    return 'd' if b % 3 else 'b'
        return None
    return deco


def barrel_parts(cx, cy, z0, mat, explosive, state, seed, scale=1.0):
    r = 0.2 * scale
    h = 0.62 * scale
    deco = barrel_deco(cx, cy, explosive, state)
    low = prism(cx, cy, r, 8, z0, z0 + h / 2, 'red' if explosive else 'crate', seed, turn=math.pi / 8, lean=-0.14, deco=deco, grain='y', worn=0.1)
    up = prism(cx, cy, r + 0.14 * h / 2 * 0.5, 8, z0 + h / 2, z0 + h, 'red' if explosive else 'crate', seed + 1, turn=math.pi / 8, lean=0.14, deco=deco, grain='y', worn=0.1)
    # the lower half is shifted down in z for the deco's z (it reads absolute z, so pass the barrel's own: hoops are given relative to the barrel's base)
    for part in (low, up):
        part.radius = r + 0.03
    return [low, up]


def barrel(state, seed):
    cx = cy = 0.5
    if state == 'destroyed':
        parts = [prism(cx, cy, 0.26, 10, 0.0, 0.025, 'char', seed, turn=0.3), p3.wheel(cx, cy, 0.05, 0.2, 0.03, 'z', 'iron', seed + 1)]
        for k in range(5):
            a = k * 1.3 + 0.4
            parts.append(lump(cx + 0.3 * math.cos(a), cy + 0.26 * math.sin(a), 0.07, 0.035, 0.07, seed + 5 + k, mat='crate'))
        return parts
    return barrel_parts(cx, cy, 0.0, 'red', True, state, seed)


def barrel_stack(state, seed):
    spots = [(0.27, 0.5, 0.0), (0.73, 0.5, 0.0), (0.5, 0.5, 0.58)]
    parts = []
    if state == 'destroyed':
        for k in range(8):
            a = 0.9 * k + 0.5
            parts.append(lump(0.5 + 0.34 * math.cos(a), 0.5 + 0.3 * math.sin(a), 0.055, 0.035, 0.05 + 0.03 * (k % 3), seed + k, mat='crate'))
        parts.append(p3.wheel(0.34, 0.6, 0.05, 0.18, 0.03, 'z', 'iron', seed + 40))
        parts.append(lump(0.62, 0.42, 0.16, 0.1, 0.08, seed + 50, mat='crate'))
        return parts
    for k, (cx, cy, z0) in enumerate(spots):
        if state == 'damaged' and k == 2:
            continue                                                                  # the top one is gone
        parts += barrel_parts(cx, cy, z0, 'crate', False, state, seed + 7 * k, 0.92)
    if state == 'damaged':
        parts.append(lump(0.5, 0.82, 0.09, 0.05, 0.07, seed + 90, mat='crate'))
        parts.append(lump(0.2, 0.2, 0.07, 0.04, 0.05, seed + 91, mat='crate'))
    return parts


# --- the wall -----------------------------------------------------------------------------------
def wall(fx, fy, state, seed):
    along_y = fy > fx
    L = fy if along_y else fx

    def mk(u0, u1, z1, z0=0.0, v0=0.2, v1=0.8, deco=None):
        x0, x1, y0, y1 = (v0, v1, u0, u1) if along_y else (u0, u1, v0, v1)
        b = box(x0, x1, y0, y1, z0, z1, 'stone', seed + int(u0 * 13 + z1 * 7))
        b.deco = deco
        return b

    def cracks(s, n, P, role):
        x, y, z = P
        if abs(n[2]) > 0.6:
            return None
        face_along = (y if n[0] > 0.7 else x)
        a, b = int(math.floor(face_along * 16)), int(math.floor(z * 16))
        for a0 in cracks.starts:
            if 2 <= b <= 14 and a == a0 + int(2.2 * math.sin(b * 0.8 + a0)):
                return 'x'
        if cracks.hole and cracks.hole[0] <= a < cracks.hole[0] + 4 and 3 <= b < 7:
            return 'w'
        return None
    parts = []
    if state == 'intact':
        parts.append(mk(0.0, L, 1.0))
    elif state == 'damaged':
        cracks.starts = [int(L * 5), int(L * 11)]
        cracks.hole = (int(L * 8), 0)
        segs = [(0.0, 0.42 * L, 1.0), (0.42 * L, 0.7 * L, 0.68), (0.7 * L, L, 0.88)]
        for u0, u1, h in segs:
            parts.append(mk(u0, u1, h, deco=cracks))
        parts.append(mk(0.42 * L + 0.05, 0.42 * L + 0.2, 0.84, z0=0.68, v0=0.3, v1=0.6))               # a stone left standing on the broken top
        parts.append(lump(*(((0.5, L * 0.55 + 0.45) if along_y else (L * 0.55 + 0.45, 0.5))), 0.12, 0.08, 0.1, seed + 3))
    else:
        n = 7 * L
        for k in range(n):
            u = 0.12 + (L - 0.24) * noise(k, 1, seed)
            v = 0.2 + 0.6 * noise(k, 2, seed)
            h = 0.08 + 0.26 * noise(k, 3, seed) * (1 - abs(u / L - 0.5))
            cx, cy = (v, u) if along_y else (u, v)
            parts.append(lump(cx, cy, 0.11 + 0.07 * noise(k, 4, seed), 0.09 + 0.06 * noise(k, 5, seed), h, seed + 11 * k))
    return parts


# --- the urns -----------------------------------------------------------------------------------
def urns(state, seed):
    spots = [(0.3, 0.34, 1.0), (0.68, 0.4, 0.82), (0.46, 0.72, 1.15)]
    parts = []
    band = lambda s, n, P, role: ('b' if 0.18 < P[2] < 0.22 and abs(n[2]) < 0.6 else None)
    for k, (cx, cy, sc) in enumerate(spots):
        s = seed + 13 * k
        if state == 'destroyed':
            if k == 0:
                parts.append(blob((cx, cy, 0.0), (0.12 * sc, 0.12 * sc, 0.09), 'clay', s, top=0.09))
            for j in range(4):
                a = k * 2.1 + j * 1.6
                parts.append(lump(cx + 0.14 * math.cos(a), cy + 0.12 * math.sin(a), 0.06, 0.04, 0.045, s + j, mat='clay'))
            continue
        if state == 'damaged' and k == 1:
            parts.append(blob((cx, cy, 0.0), (0.13 * sc, 0.13 * sc, 0.12), 'clay', s, top=0.12))                  # the body broken off low
            for j in range(3):
                parts.append(lump(cx + 0.17 * math.cos(j * 2.2), cy + 0.13 * math.sin(j * 2.2), 0.05, 0.035, 0.04, s + j, mat='clay'))
            continue
        body = blob((cx, cy, 0.14 * sc), (0.14 * sc, 0.14 * sc, 0.17 * sc), 'clay', s, top=0.31 * sc)
        body.deco = band
        parts.append(body)
        parts.append(blob((cx, cy, 0.3 * sc), (0.07 * sc, 0.07 * sc, 0.08 * sc), 'clay', s + 1, top=0.38 * sc))
        parts.append(blob((cx, cy, 0.38 * sc), (0.09 * sc, 0.09 * sc, 0.035 * sc), 'clay', s + 2, top=0.415 * sc))
        if state == 'damaged' and k == 0:                                           # a chip out of the rim
            parts.append(lump(cx - 0.12, cy + 0.12, 0.05, 0.035, 0.035, s + 5, mat='clay'))
    return parts


# --- the hay cart -------------------------------------------------------------------------------
def haycart(state, seed):
    parts = []

    def wheel_deco(s, n, P, role):
        cx, cy, cz, r, axis = s.wheel
        x, y, z = P
        if axis == 'y' and abs(n[1]) > 0.7:
            d = math.hypot(x - cx, z - cz) / r
            ang = math.atan2(z - cz, x - cx)
            if d < 0.2:
                return 'a'
            if d > 0.8:
                return 'g'
            if abs(math.sin(ang * 4)) < 0.22 and d < 0.8:
                return 'e'
            return 'x'
        return None
    if state == 'destroyed':
        parts.append(p3.wheel(0.9, 0.35, 0.03, 0.26, 0.05, 'z', 'wood', seed))
        parts.append(p3.wheel(1.35, 0.78, 0.07, 0.24, 0.05, 'z', 'wood', seed + 1))
        for k in range(6):
            u = 0.35 + 1.3 * noise(k, 1, seed)
            v = 0.2 + 0.6 * noise(k, 2, seed)
            parts.append(box(u - 0.2, u + 0.2, v - 0.04, v + 0.04, 0.0, 0.07, 'wood', seed + 5 + k, grain='x', worn=0.2))
        parts.append(blob((0.95, 0.52, 0.0), (0.65, 0.3, 0.12), 'hay', seed + 30, top=0.12))
        for k in range(4):
            parts.append(blob((0.3 + 0.45 * k, 0.5 + 0.28 * ((k % 2) - 0.5), 0.0), (0.2, 0.15, 0.07), 'hay', seed + 31 + k, top=0.07))
        return parts
    sag = 0.07 if state == 'damaged' else 0.0
    bz = 0.26 - sag
    parts.append(box(0.4, 1.6, 0.22, 0.78, bz - 0.02, bz + 0.04, 'wood', seed, grain='x', worn=0.2))                       # the floor
    parts.append(box(0.4, 1.6, 0.2, 0.26, bz + 0.04, bz + 0.26, 'wood', seed + 1, grain='x', worn=0.2))                    # the sides
    parts.append(box(0.4, 1.6, 0.74, 0.8, bz + 0.04, bz + 0.26, 'wood', seed + 2, grain='x', worn=0.2))
    parts.append(box(1.56, 1.62, 0.22, 0.78, bz + 0.04, bz + 0.26, 'wood', seed + 3, grain='y', worn=0.2))                 # the front board
    if state == 'intact':
        parts.append(box(0.38, 0.44, 0.22, 0.78, bz + 0.04, bz + 0.26, 'wood', seed + 4, grain='y', worn=0.2))             # the tail board
    for k, sy in enumerate((0.38, 0.62)):                                                                                   # the shafts
        end = 1.98 if not (state == 'damaged' and k == 1) else 1.8
        parts.append(box(1.6, end, sy - 0.025, sy + 0.025, bz - 0.01, bz + 0.03, 'wood', seed + 6 + k, grain='x', worn=0.2))
    for k, wy in enumerate((0.1, 0.9)):
        if state == 'damaged' and k == 1:
            continue                                                                                                       # a wheel off
        w = p3.wheel(0.95, wy, 0.3, 0.3, 0.08, 'y', 'wood', seed + 10 + k)
        w.deco = wheel_deco
        parts.append(w)
    hay = blob((1.0, 0.5, bz + 0.1), (0.55, 0.25, 0.2), 'hay', seed + 20, top=bz + 0.3)
    parts.append(hay)
    if state == 'damaged':
        parts.append(blob((0.95, 0.95, 0.0), (0.32, 0.12, 0.13), 'hay', seed + 21, top=0.13))
        parts.append(blob((0.5, 0.92, 0.0), (0.18, 0.1, 0.08), 'hay', seed + 22, top=0.08))
    return parts


# --- the pieces -----------------------------------------------------------------------------------
PIECES = [
    # id, label, footprint, builder, zmax (the canvas), cover_levels, blocks, explosive
    dict(id='barricade-1x1', label='Barricade 1 x 1', fx=1, fy=1, build=lambda st: barricade(1, 1, st, 100), zmax=1.0, cover=0.8, explosive=False),
    dict(id='barricade-1x2', label='Barricade 1 x 2', fx=1, fy=2, build=lambda st: barricade(1, 2, st, 110), zmax=1.0, cover=0.8, explosive=False),
    dict(id='barrel-explosive', label='Explosive barrel', fx=1, fy=1, build=lambda st: barrel(st, 120), zmax=0.7, cover=0.62, explosive=True),
    dict(id='barrel-stack', label='Barrel stack', fx=1, fy=1, build=lambda st: barrel_stack(st, 130), zmax=1.25, cover=1.2, explosive=False),
    dict(id='wall-1x1', label='Breakable wall 1 x 1', fx=1, fy=1, build=lambda st: wall(1, 1, st, 140), zmax=1.0, cover=1.0, explosive=False),
    dict(id='wall-1x2', label='Breakable wall 1 x 2', fx=1, fy=2, build=lambda st: wall(1, 2, st, 150), zmax=1.0, cover=1.0, explosive=False),
    dict(id='urns', label='Clay urns', fx=1, fy=1, build=lambda st: urns(st, 160), zmax=0.5, cover=0.45, explosive=False),
    dict(id='haycart', label='Hay cart', fx=2, fy=1, build=lambda st: haycart(st, 170), zmax=0.8, cover=0.75, explosive=False),
]


def render_state(piece, state):
    sc = Scene(piece['fx'], piece['fy'], piece['zmax'], pad=PAD, up=UP)
    parts = piece['build'](state)
    sc.draw(parts, p3.paint)
    if piece['explosive'] and state == 'damaged':
        for k in range(4):                                                      # sparks off the cracked barrel
            x, y = sc.project(0.5, 0.5, 0.7)
            sc.pixel(x + (k - 1.5) * 3, y - 2 - (k % 2) * 3, 'd')
    return sc.finish(), sc.anchor, sc


# --- the destruction animation ------------------------------------------------------------------
DUST = ['t', 'C', 'p', 'l']
FIRE = ['d', 'b', 'a', 'c']
SMOKE = ['l', 'k', 'w']
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def cloud(g, cx, cy, rx, ry, ramp, coverage, seed):
    """A ragged cloud: an ellipse of dithered pixels from the ramp, light in the middle, thinning at the rim; `coverage` 0 to 1 is how much of it is there."""
    h, w = len(g), len(g[0])
    for y in range(max(0, int(cy - ry) - 1), min(h, int(cy + ry) + 2)):
        for x in range(max(0, int(cx - rx) - 1), min(w, int(cx + rx) + 2)):
            dx, dy = (x + 0.5 - cx) / max(rx, 0.1), (y + 0.5 - cy) / max(ry, 0.1)
            d = math.hypot(dx, dy) + 0.18 * (noise(x // 2, y // 2, seed) - 0.5)
            if d > 1:
                continue
            if noise(x, y, seed + 77) > coverage * (1.15 - 0.9 * d):
                continue
            g[y][x] = ramp[min(len(ramp) - 1, int(d * len(ramp)))] if d > 0.3 else ramp[0]


def chunks_of(rows, anchor, seed):
    """The sprite's own pixels cut into 4 x 4 blocks, each a chunk with a velocity: out from the anchor on the ground's plane, and up."""
    h, w = len(rows), len(rows[0])
    out = []
    ax, ay = anchor
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            px = [(x, y, rows[y][x]) for y in range(by, min(by + 4, h)) for x in range(bx, min(bx + 4, w)) if rows[y][x] != '.']
            if len(px) < 5:
                continue
            cx, cy = bx + 2, by + 2
            k = len(out)
            ang = math.atan2((cy - ay) * 2, cx - ax) + (noise(k, 1, seed) - 0.5) * 0.8
            height = max(0.0, ay - cy)
            speed = 1.4 + 2.4 * noise(k, 2, seed)
            out.append(dict(px=px, c=(cx, cy), vx=math.cos(ang) * speed * 1.6, vy=math.sin(ang) * speed * 0.8 - (1.2 + 3.2 * noise(k, 3, seed) + height * 0.06),
                            land=ay + (noise(k, 4, seed) - 0.3) * 9))
    return out


G = 2.6


def chunk_at(ch, t):
    cx, cy = ch['c']
    x = cx + ch['vx'] * t
    y = cy + ch['vy'] * t + 0.5 * G * t * t
    if y >= ch['land']:                                                  # landed: it stays where it hit
        t_land = (-ch['vy'] + math.sqrt(max(0.0, ch['vy'] ** 2 + 2 * G * (ch['land'] - cy)))) / G
        x = cx + ch['vx'] * t_land
        y = ch['land']
    return x, y


def destroy_frames(intact, destroyed, anchor, explosive, seed, size):
    """The six frames from the piece's intact and destroyed rows."""
    h, w = len(intact), len(intact[0])
    ax, ay = anchor
    chs = chunks_of(intact, anchor, seed)
    ys = [y for y, r in enumerate(intact) if r.strip('.')]
    mid = (min(ys) + max(ys)) / 2
    spread = size
    frames = []
    for f in range(FRAMES):
        g = [['.'] * w for _ in range(h)]
        if f == 0:
            for y, r in enumerate(intact):
                for x, c in enumerate(r):
                    if c != '.':
                        g[y][x] = p3.LIGHTER.get(c, c) if noise(x, y, seed + 8) > 0.35 else ('d' if explosive else 't')
            if explosive:
                cloud(g, ax, mid, 12, 9, FIRE, 0.9, seed + 1)
            else:
                cloud(g, ax, mid + 2, 10, 5, DUST, 0.5, seed + 1)
        else:
            if f >= 2:                                                   # the wreck shows under the falling chunks, coming in
                for y, r in enumerate(destroyed):
                    for x, c in enumerate(r):
                        if c != '.' and (f >= 3 or noise(x, y, seed + 3) > 0.5):
                            g[y][x] = c
            t = f * 0.85
            if f < FRAMES - 1:
                for ch in chs:
                    x, y = chunk_at(ch, t)
                    dx, dy = round(x - ch['c'][0]), round(y - ch['c'][1])
                    for px, py, c in ch['px']:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            g[ny][nx] = c
            if explosive:
                if f == 1:
                    cloud(g, ax, mid, 18, 12, FIRE, 0.95, seed + 2)
                elif f == 2:
                    cloud(g, ax, mid - 2, 20, 13, FIRE[1:], 0.55, seed + 2)
                    cloud(g, ax, mid - 6, 22, 14, SMOKE, 0.5, seed + 3)
                elif f == 3:
                    cloud(g, ax, mid - 6, 20, 12, SMOKE, 0.6, seed + 4)
                elif f == 4:
                    cloud(g, ax, mid - 10, 16, 9, SMOKE, 0.4, seed + 5)
                else:
                    cloud(g, ax - 3, mid - 12, 7, 4, SMOKE, 0.35, seed + 6)
            else:
                radius = [0, 11, 15, 16, 13, 6][f]
                cover = [0, 0.8, 0.7, 0.55, 0.4, 0.3][f]
                cloud(g, ax, mid + 1 - (f > 2) * 2, radius * spread, radius * spread * 0.5, DUST, cover, seed + 10 + f)
        frames.append([''.join(r) for r in g])
    return frames


_CACHE = {}


def piece_states(piece):
    if piece['id'] not in _CACHE:
        states = {}
        anchor = None
        for st in STATES:
            rows, anchor, sc = render_state(piece, st)
            states[st] = rows
        size = 0.6 + 0.2 * (piece['fx'] + piece['fy'] - 1) ** 0.5
        anim = destroy_frames(states['intact'], states['destroyed'], anchor, piece['explosive'], hash_id(piece['id']), size)
        _CACHE[piece['id']] = (states, anim, anchor)
    return _CACHE[piece['id']]


def hash_id(s):
    n = 0
    for ch in s:
        n = (n * 131 + ord(ch)) & 0xFFFFFF
    return n


def build_assets():
    out = []
    for piece in PIECES:
        states, anim, anchor = piece_states(piece)
        rows = states['intact']
        make = family(CATEGORY, len(rows[0]), len(rows), anchor, place='ground', folder=FOLDER)
        fp = {'size': [piece['fx'], piece['fy']], 'cells': [list(c) for c in sorted(rect(piece['fx'], piece['fy']))]}
        meta = dict(footprint=fp, blocks=True, blocks_when_destroyed=False, explosive=piece['explosive'], cover_levels=piece['cover'], walkable=False, states=list(STATES))
        out.append(make(piece['id'], piece['label'], 'variants', [states[s] for s in STATES], names=['Intact', 'Damaged', 'Destroyed'], **meta))
        out.append(make(piece['id'] + '-destroy', piece['label'] + ', destroyed', 'animation', anim, fps=FPS, **meta))
    return out


def write_package(folder):
    write_json(folder, 'destructibles.json', 'The destructibles in this folder. See README.md beside this file.',
               {'fps': FPS, 'frames': FRAMES, 'states': list(STATES),
                'pieces': {p['id']: {'label': p['label'], 'size': [p['fx'], p['fy']], 'blocks': True, 'blocks_when_destroyed': False, 'explosive': p['explosive'], 'cover_levels': p['cover'],
                                     'files': {'intact': f"{p['id']}.png (frame 1)", 'damaged': f"{p['id']}.png (frame 2)", 'destroyed': f"{p['id']}.png (frame 3)", 'animation': f"{p['id']}-destroy.png"}} for p in PIECES}})


# --- preview ------------------------------------------------------------------------------------
def preview(path, scale=2):
    from PIL import Image, ImageDraw
    rgb = p3.role_rgb()
    grass, edge = (62, 98, 74, 255), (90, 130, 100, 255)
    cells = []
    W = 1640
    pad = 16
    heights = []
    sheet_items = []
    for piece in PIECES:
        states, anim, anchor = piece_states(piece)
        sheet_items.append((piece, states, anim, anchor))
    rowh = [max(len(s['intact']) for s in [st]) * scale + 34 for _, st, _, _ in sheet_items]
    H = pad + sum(2 * (len(st['intact']) * scale + 34) for _, st, _, _ in sheet_items) + pad
    sheet = Image.new('RGBA', (W, H), (30, 34, 56, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    for piece, states, anim, anchor in sheet_items:
        fx, fy = piece['fx'], piece['fy']
        h = len(states['intact']) * scale
        for line, frames, names in ((0, [states[s] for s in STATES], list(STATES)), (1, anim, [f'frame {k + 1}' for k in range(FRAMES)])):
            x = pad
            for rows, name in zip(frames, names):
                im = p3.rows_to_image(rows, rgb, scale)
                ax, ay = anchor
                pts = [(ax + 16 * ((X - fx / 2) - (Y - fy / 2)), ay + 8 * ((X - fx / 2) + (Y - fy / 2))) for X, Y in ((0, 0), (fx, 0), (fx, fy), (0, fy))]
                d.polygon([(x + a * scale, y + 14 + b * scale) for a, b in pts], fill=grass, outline=edge)
                sheet.alpha_composite(im, (x, y + 14))
                d.text((x, y), (piece['id'] + '  ' if x == pad else '') + name, fill=(230, 220, 200, 255))
                x += im.width + 8
            y += h + 34
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the destructibles ->', args.preview)


if __name__ == '__main__':
    main()
