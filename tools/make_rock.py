#!/usr/bin/env python3
"""The rock barrier: a jittered, subdivided icosahedron with a flat base, flat-shaded in the cool stone ramp with a little moss, as the variants of one asset (`rock`)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import GROUND_ROW, inside, normalise, sheet_layout  # noqa: E402

# Roles used, by palette character: spark, then the green ramp, then the outline.
SPARK, LIT, BASE, SHADE, DEEP, OUTLINE = 't', 'z', 'A', 'B', 's', 'O'

# --- rocks ------------------------------------------------------------------
# A rock is a jittered, subdivided icosahedron with a flat base, flat-shaded. Stone
# is the cool ramp (steel, lavender, indigo) held to a narrow range so it reads as
# rock and not as a gem. Moss is small green speckle on the upward-facing surfaces.
STONE = ((0.84, 'q'), (0.62, 'p'), (0.44, 'l'), (0.30, 'k'), (0.0, 'w'))
MOSS = ((0.62, 'z'), (0.44, 'A'), (0.0, 'B'))
CRACK = 'w'
PHI = (1 + 5 ** 0.5) / 2
ICO_VERTS = [(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0), (0, -1, PHI), (0, 1, PHI),
             (0, -1, -PHI), (0, 1, -PHI), (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)]
ICO_FACES = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
             (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
             (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]


def subdivided_sphere():
    """The icosahedron with every face split in four, on the unit sphere."""
    verts = [normalise(v) for v in ICO_VERTS]
    midpoints = {}

    def mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in midpoints:
            verts.append(normalise(tuple((verts[i][c] + verts[j][c]) / 2 for c in range(3))))
            midpoints[key] = len(verts) - 1
        return midpoints[key]

    faces = []
    for a, b, c in ICO_FACES:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return verts, faces


SPHERE = subdivided_sphere()


class Lcg:
    """A tiny seeded random source, so the same seed always gives the same rock."""
    def __init__(self, seed):
        self.state = (seed * 2654435761) % 2 ** 32 or 1

    def next(self):
        self.state = (self.state * 1664525 + 1013904223) % 2 ** 32
        return self.state / 2 ** 32


ROCK = dict(
    id='rock', label='Rock barrier', w=32, h=32,
    tilt=28,          # degrees the camera looks down
    flat=0.5,         # how much of the bottom is cut away, so it sits on the ground
    light=(-0.45, 0.62, 0.64),
    variants=[
        dict(name='Boulder', moss=40, cracks=2, rocks=[dict(rx=11.5, ry=11.0, rz=9.0, jitter=0.16, seed=4, yaw=20, ox=0, oz=0)]),
        dict(name='Tall rock', moss=30, cracks=2, rocks=[dict(rx=8.0, ry=14.0, rz=7.0, jitter=0.16, seed=2, yaw=-25, ox=0, oz=0)]),
        dict(name='Twin rocks', moss=40, cracks=2, rocks=[dict(rx=7.6, ry=9.2, rz=7.0, jitter=0.16, seed=3, yaw=10, ox=-4.4, oz=-2),
                                                         dict(rx=4.8, ry=5.2, rz=4.6, jitter=0.18, seed=14, yaw=-30, ox=6.4, oz=3)]),
        dict(name='Slab', moss=25, cracks=2, rocks=[dict(rx=11.6, ry=5.6, rz=7.6, jitter=0.14, seed=5, yaw=8, ox=0, oz=0)]),
    ],
)


def tone(table, value):
    return next(char for floor, char in table if value > floor)


def hash2(x, y, seed):
    return ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) % 1000 / 1000


def render_rock_variant(spec, variant, seed_override=None):
    w, h = spec['w'], spec['h']
    tilt = math.radians(spec['tilt'])
    light = normalise(spec['light'])
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    sphere_verts, sphere_faces = SPHERE
    tris = []
    first_seed = None
    for index, rock in enumerate(variant['rocks']):
        seed = rock['seed'] if seed_override is None else seed_override + index * 17
        first_seed = seed if first_seed is None else first_seed
        rng = Lcg(seed)
        yaw = math.radians(rock['yaw'])
        verts = []
        for nx, ny, nz in sphere_verts:
            k = 1 + (rng.next() - 0.5) * 2 * rock['jitter']
            x, y, z = nx * rock['rx'] * k, ny * rock['ry'] * k, nz * rock['rz'] * k
            y = max(y, -spec['flat'] * rock['ry'])
            x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
            verts.append((x + rock['ox'], y, z + rock['oz']))
        centre = (rock['ox'], 0, rock['oz'])
        for fid, face in enumerate(sphere_faces):
            pts = [verts[i] for i in face]
            u = tuple(pts[1][i] - pts[0][i] for i in range(3))
            v2 = tuple(pts[2][i] - pts[0][i] for i in range(3))
            n = (u[1] * v2[2] - u[2] * v2[1], u[2] * v2[0] - u[0] * v2[2], u[0] * v2[1] - u[1] * v2[0])
            mid = tuple(sum(q[i] for q in pts) / 3 - centre[i] for i in range(3))
            if sum(n[i] * mid[i] for i in range(3)) < 0:
                n = tuple(-c for c in n)
            if not any(n):
                continue
            n = normalise(n)
            vn = (n[0], n[1] * cos_t - n[2] * sin_t, n[2] * cos_t + n[1] * sin_t)   # as the camera sees it
            if vn[2] <= 0:
                continue
            shade = 0.2 + 0.8 * max(0.0, sum(vn[i] * light[i] for i in range(3)))
            shade += (hash2(fid, index, seed) - 0.5) * 0.10      # a little grain between neighbouring facets
            screen = [(x, y * cos_t - z * sin_t, z * cos_t + y * sin_t) for x, y, z in pts]
            tris.append((screen, shade, n[1]))

    big = 80
    ox, oy = big / 2, big * 0.75
    cells = {}
    for py in range(big):
        for px in range(big):
            x, y = px + 0.5 - ox, oy - (py + 0.5)
            hit = [(max(q[2] for q in p), shade, up) for p, shade, up in tris if inside(p, x, y)]
            if hit:
                _, shade, up = max(hit)
                cells[(px, py)] = (shade, up)
    if not cells:
        return ['.' * w] * h
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    dx = round(w / 2 - (min(xs) + max(xs) + 1) / 2)
    dy = (GROUND_ROW - 1) - max(ys)          # the lowest body row sits just above the outline row
    grid = [['.'] * w for _ in range(h)]
    placed = {}
    for (px, py), (shade, up) in cells.items():
        qx, qy = px + dx, py + dy
        if not (0 <= qx < w and 0 <= qy < h):
            continue
        # Moss: speckle, in small clumps, on surfaces that face up.
        mossy = up > 0.5 and hash2(qx // 2, qy // 2, first_seed) * 100 < variant['moss'] * (up - 0.3) * 2.2
        grid[qy][qx] = tone(MOSS if mossy else STONE, shade)
        placed[(qx, qy)] = shade

    # Cracks: short runs down and to the right from near the top.
    rng = Lcg(first_seed * 7 + 1)
    top = min(y for _, y in placed)
    for _ in range(variant.get('cracks', 0)):
        cx_, cy_ = int(w / 2 + (rng.next() - 0.5) * 12), top + 2 + int(rng.next() * 5)
        for step in range(3 + int(rng.next() * 3)):
            for q in ((cx_ + step, cy_ + step), (cx_ + step + 1, cy_ + step)):
                if q in placed and grid[q[1]][q[0]] not in ('z', 'A', 'B'):
                    grid[q[1]][q[0]] = CRACK
    for (px, py) in placed:
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                nx, ny = px + ddx, py + ddy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == '.':
                    grid[ny][nx] = OUTLINE
    return [''.join(row) for row in grid]


def build_assets():
    rock = ROCK
    rock_frames = [render_rock_variant(rock, v) for v in rock['variants']]
    cols, rows = sheet_layout(len(rock_frames))
    rock_asset = {
        'id': rock['id'], 'label': rock['label'], 'category': 'Nature', 'kind': 'variants', 'place': 'ground',
        'names': [v['name'] for v in rock['variants']],
        'w': rock['w'], 'h': rock['h'], 'cols': cols, 'rows': rows, 'fps': 0,
        # The middle of the base, on the ground row characters stand on.
        'anchor': {'x': rock['w'] // 2, 'y': GROUND_ROW + 1},
        'frames': rock_frames,
    }
    return [rock_asset]
