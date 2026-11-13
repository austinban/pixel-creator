#!/usr/bin/env python3
"""Amulets: pendant icons for the shop. Only an image each, nothing that is worn or animated.

A 32 x 32 icon in the shared palette roles: a short chain hanging from the top and a pendant under it, lit from the upper left like everything
else, with a one-pixel outline. They are small 3D models (make_weapon_icons3d.py); this module has the build, the preview, and the `Icon` shape-stack the equipment slot icons are
still drawn with, and the shared ramps.

    python3 tools/make_amulets.py --preview previews/amulets.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
from assetkit import sheet_layout  # noqa: E402

CELL = 32
LIGHT = (-0.55, -0.83)
RAMPS = {
    'gold': ('t', 'd', 'b', 'a'),
    'silver': ('t', 'r', 'q', 'p'),
    'steel': ('r', 'q', 'p', 'l'),
    'ruby': ('c', 'j', 'i', 'h'),
    'sapphire': ('r', 'o', 'n', 'm'),
    'emerald': ('r', 'A', 'B', 's'),
    'topaz': ('t', 'd', 'b', 'a'),
    'bone': ('t', 'C', 'c', 'e'),
    'stone': ('q', 'p', 'l', 'k'),
    'rose': ('c', 'j', 'i', 'h'),
    'leaf': ('z', 'A', 'B', 's'),
    'cord': ('e', 'f', 'h', 'g'),
    'rune': ('d', 'b', 'a', 'a'),
    'hole': ('x', 'x', 'w', 'w'),
}


def disc(cx, cy, r):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def diamond(cx, cy, rx, ry):
    return lambda x, y: abs(x - cx) / rx + abs(y - cy) / ry <= 1


def heart(cx, cy, size):
    def inside(x, y):
        u, v = (x - cx) / size, -(y - cy) / size + 0.15
        return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0
    return inside


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


def union(*fs):
    return lambda x, y: any(f(x, y) for f in fs)


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1


def ring(cx, cy, r0, r1):
    return minus(disc(cx, cy, r1), disc(cx, cy, r0))


def poly(points):
    def inside(x, y):
        hit = False
        j = len(points) - 1
        for i in range(len(points)):
            (xi, yi), (xj, yj) = points[i], points[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
                hit = not hit
            j = i
        return hit
    return inside


class Icon:
    def __init__(self):
        self.grid = [['.'] * CELL for _ in range(CELL)]
        self.solid = set()

    def layer(self, mask, ramp, centre=None, radius=None, flat=None):
        """Paint a shape. Shaded by how far toward the light each pixel is from the shape's middle, or a single tone if flat is 0..3."""
        pts = [(x, y) for y in range(CELL) for x in range(CELL) if mask(x + 0.5, y + 0.5)]
        if not pts:
            return
        cx = centre[0] if centre else sum(p[0] for p in pts) / len(pts) + 0.5
        cy = centre[1] if centre else sum(p[1] for p in pts) / len(pts) + 0.5
        r = radius or max(1.0, max(math.hypot(x + 0.5 - cx, y + 0.5 - cy) for x, y in pts))
        for x, y in pts:
            if flat is not None:
                tone = flat
            else:
                t = ((x + 0.5 - cx) * LIGHT[0] + (y + 0.5 - cy) * LIGHT[1]) / r
                tone = 0 if t > 0.42 else 1 if t > -0.12 else 2 if t > -0.55 else 3
            self.grid[y][x] = RAMPS[ramp][tone]
            self.solid.add((x, y))

    def dot(self, x, y, role):
        self.grid[y][x] = role
        self.solid.add((x, y))

    def chain(self, ends, hang, ramp='gold'):
        """Links along a sagging curve between two points near the top, down to the bail at `hang`."""
        (x0, y0), (x1, y1) = ends
        hx, hy = hang
        for side, (sx, sy) in enumerate(((x0, y0), (x1, y1))):
            steps = 11
            for i in range(steps + 1):
                t = i / steps
                x = sx + (hx - sx) * t
                y = sy + (hy - sy) * t + 2.6 * math.sin(math.pi * t) * 0.0 + (1 - (1 - t) ** 2) * 0
                px, py = int(round(x)), int(round(y))
                self.grid[py][px] = RAMPS[ramp][1 if (i + side) % 2 == 0 else 2]
                self.solid.add((px, py))

    def outline(self):
        for (x, y) in list(self.solid):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < CELL and 0 <= ny < CELL and (nx, ny) not in self.solid:
                    self.grid[ny][nx] = 'O'
        return [''.join(r) for r in self.grid]


def amulet_list():
    """The eight amulets as (id, label, drawing): small 3D models, drawn in make_weapon_icons3d.py (loaded here, when it is wanted, because that module builds on this one's ramps)."""
    import make_weapon_icons3d
    return make_weapon_icons3d.AMULETS


def preview(path, scale=8):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    sheet = Image.new('RGBA', (len(amulet_list()) * (CELL * scale + 8), CELL * scale + 28), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    for k, (_, label, make) in enumerate(amulet_list()):
        cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        for y, line in enumerate(make()):
            for x, ch in enumerate(line):
                if ch != '.':
                    cell.putpixel((x, y), rgb[ch] + (255,))
        sheet.alpha_composite(cell.resize((CELL * scale, CELL * scale), Image.NEAREST), (k * (CELL * scale + 8), 22))
        d.text((k * (CELL * scale + 8) + 4, 4), label, fill=(235, 238, 245, 255))
    sheet.save(path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
        print('wrote', args.preview)

def build_assets():
    # Amulets: pendant icons for the shop, one image each (nothing is worn), as the variants of one asset.
    amulet_frames = [make() for _, _, make in amulet_list()]
    cols, rows = sheet_layout(len(amulet_frames))
    amulet_asset = {
        'id': 'amulets', 'label': 'Amulets (shop icons)', 'category': 'Amulets', 'kind': 'variants', 'place': 'none',
        'names': [label for _, label, _ in amulet_list()],
        'w': CELL, 'h': CELL, 'cols': cols, 'rows': rows, 'fps': 0,
        'anchor': {'x': CELL // 2, 'y': CELL // 2},
        'frames': amulet_frames,
    }
    return [amulet_asset]


if __name__ == '__main__':
    main()
