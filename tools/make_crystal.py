#!/usr/bin/env python3
"""The turn crystal: an elongated octahedron, flat-shaded, turning about its vertical axis and bobbing as it goes. Four faces repeat every quarter turn, so the frames loop with no seam."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import inside, normalise, sheet_layout  # noqa: E402

# Roles used, by palette character: spark, then the green ramp, then the outline.
SPARK, LIT, BASE, SHADE, DEEP, OUTLINE = 't', 'z', 'A', 'B', 's', 'O'

# --- the turn crystal -------------------------------------------------------
CRYSTAL = dict(
    id='crystal', label='Turn crystal',
    w=32, h=32, frames=8, fps=8,   # a square cell like the characters', with room around the crystal
    half_height=10.0,   # apex to the middle
    radius=5.6,         # the middle's radius
    tilt=14,            # degrees the camera looks down
    bob=1,              # rows the whole crystal rises and falls
    light=(-0.45, 0.62, 0.64),
)


def render_crystal(spec, frame):
    w, h = spec['w'], spec['h']
    theta = math.radians(frame * 90 / spec['frames'])
    tilt = math.radians(spec['tilt'])
    light = normalise(spec['light'])
    bob = round(math.sin(2 * math.pi * frame / spec['frames']) * spec['bob'])
    cx, cy = w / 2, h / 2

    def project(p):
        x, y, z = p
        x, z = x * math.cos(theta) + z * math.sin(theta), -x * math.sin(theta) + z * math.cos(theta)  # turn
        y, z = y * math.cos(tilt) - z * math.sin(tilt), z * math.cos(tilt) + y * math.sin(tilt)         # look down
        return (x, y, z)

    top, bottom = (0, spec['half_height'], 0), (0, -spec['half_height'], 0)
    ring = [(spec['radius'] * math.cos(a), 0, spec['radius'] * math.sin(a)) for a in (k * math.pi / 2 for k in range(4))]
    faces = []
    for k in range(4):
        a, b = ring[k], ring[(k + 1) % 4]
        faces.append((top, a, b))
        faces.append((bottom, b, a))

    visible = []
    for tri in faces:
        p = [project(v) for v in tri]
        u = tuple(p[1][i] - p[0][i] for i in range(3))
        v = tuple(p[2][i] - p[0][i] for i in range(3))
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        centre = tuple(sum(q[i] for q in p) / 3 for i in range(3))
        if sum(n[i] * centre[i] for i in range(3)) < 0:
            n = tuple(-c for c in n)        # point it away from the middle
        if n[2] <= 0:
            continue                         # facing away
        n = normalise(n)
        shade = 0.22 + 0.78 * max(0.0, sum(n[i] * light[i] for i in range(3)))
        visible.append((p, shade))

    grid = [['.'] * w for _ in range(h)]
    filled = {}
    for py in range(h):
        for px in range(w):
            x, y = px + 0.5 - cx, -(py + 0.5 - cy - bob)
            hit = [(max(q[2] for q in p), shade) for p, shade in visible if inside(p, x, y)]
            if hit:
                filled[(px, py)] = max(hit)[1]

    for (px, py), shade in filled.items():
        grid[py][px] = LIT if shade > 0.80 else BASE if shade > 0.52 else SHADE if shade > 0.34 else DEEP

    # A glint on the brightest face, up and to the left of its middle, never on the tip.
    if filled:
        brightest = max(filled.values())
        lit = [c for c, s in filled.items() if s == brightest]
        if len(lit) >= 6:
            mx = sum(c[0] for c in lit) / len(lit)
            my = sum(c[1] for c in lit) / len(lit)
            x, y = min(lit, key=lambda c: (c[0] - (mx - 1)) ** 2 + (c[1] - (my - 2)) ** 2)
            grid[y][x] = SPARK
            if (x, y + 1) in filled and filled[(x, y + 1)] == brightest:
                grid[y + 1][x] = SPARK

    for (px, py) in list(filled):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == '.':
                    grid[ny][nx] = OUTLINE
    return [''.join(row) for row in grid]


def build_assets():
    crystal = CRYSTAL
    crystal_frames = [render_crystal(crystal, f) for f in range(crystal['frames'])]
    cols, rows = sheet_layout(len(crystal_frames))
    crystal_asset = {
        'id': crystal['id'], 'label': crystal['label'], 'category': 'Markers', 'kind': 'animation', 'place': 'above',
        'w': crystal['w'], 'h': crystal['h'], 'cols': cols, 'rows': rows, 'fps': crystal['fps'],
        # Where the tip hangs: the bottom edge of the lowest pixel, in the frame where it is at rest.
        'anchor': {'x': crystal['w'] // 2, 'y': 1 + max(y for y, row in enumerate(crystal_frames[0]) if row.strip('.'))},
        'frames': crystal_frames,
    }
    return [crystal_asset]
