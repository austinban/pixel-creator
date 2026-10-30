#!/usr/bin/env python3
"""Build the assets: things that aren't characters.

Each asset is painted in the same colour roles as the characters, so it recolours
the same way. The turn crystal is rendered from a small 3D model: an elongated
octahedron, flat-shaded, turning about its vertical axis and bobbing as it goes.
Four faces repeat every quarter turn, so the frames loop with no seam.

    python3 tools/make_assets.py [--png-dir DIR]

Writes assets/data.js. With --png-dir it also writes each asset's sheet as a PNG,
and every frame is checked to re-render identically from its roles.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

# Roles used, by palette character: spark, then the green ramp, then the outline.
SPARK, LIT, BASE, SHADE, DEEP, OUTLINE = 't', 'z', 'A', 'B', 's', 'O'

SHEET_COLS = 8  # frames per row in an asset's sheet

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


def normalise(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


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

    def inside(p, x, y):
        (x0, y0, _), (x1, y1, _), (x2, y2, _) = p
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
        b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
        return a >= 0 and b >= 0 and 1 - a - b >= 0

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


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--png-dir', type=Path, help='also write each asset as a PNG sheet here, and check it')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'assets' / 'data.js')
    args = parser.parse_args()

    spec = CRYSTAL
    frames = [render_crystal(spec, f) for f in range(spec['frames'])]
    asset = {
        'id': spec['id'], 'label': spec['label'], 'w': spec['w'], 'h': spec['h'],
        'cols': min(spec['frames'], SHEET_COLS), 'rows': -(-spec['frames'] // SHEET_COLS), 'fps': spec['fps'],
        # Where the tip hangs: the bottom edge of the lowest pixel, in the frame where it is at rest.
        'anchor': {'x': spec['w'] // 2, 'y': 1 + max(y for y, row in enumerate(frames[0]) if row.strip('.'))},
        'frames': frames,
    }
    data = {
        'groups': [{'id': i, 'label': l, 'hue': i not in ('outline', 'neutral')} for i, l in ep.GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ep.ROLES],
        'assets': [asset],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.ASSETS = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(f'wrote {len(data["assets"])} asset(s) -> {args.out}')

    if args.png_dir:
        from PIL import Image
        to_rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
        args.png_dir.mkdir(parents=True, exist_ok=True)
        sheet = Image.new('RGBA', (asset['w'] * asset['cols'], asset['h'] * asset['rows']), (0, 0, 0, 0))
        px = sheet.load()
        origin = lambda f: ((f % asset['cols']) * asset['w'], (f // asset['cols']) * asset['h'])
        for f, rows in enumerate(asset['frames']):
            ox, oy = origin(f)
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch != '.':
                        px[ox + x, oy + y] = (*to_rgb[ch], 255)
        path = args.png_dir / f'{asset["id"]}.png'
        sheet.save(path)
        # Re-read the PNG and compare every pixel with what the roles say it should be.
        back = Image.open(path).convert('RGBA').load()
        for f, rows in enumerate(asset['frames']):
            ox, oy = origin(f)
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    want = (0, 0, 0, 0) if ch == '.' else (*to_rgb[ch], 255)
                    if back[ox + x, oy + y] != want:
                        sys.exit(f'{path}: round trip differs at frame {f} ({x}, {y})')
        print(f'{len(asset["frames"])} frames written and re-read identical -> {path}')


if __name__ == '__main__':
    main()
