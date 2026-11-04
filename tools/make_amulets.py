#!/usr/bin/env python3
"""Amulets: pendant icons for the shop. Only an image each, nothing that is worn or animated.

A 32 x 32 icon in the shared palette roles: a short chain hanging from the top and a pendant under it, lit from the upper left like everything
else, with a one-pixel outline. Each is a stack of shapes (a mask and a ramp, shaded from the light), so a new one is a few lines.

    python3 tools/make_amulets.py --preview previews/amulets.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

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


def bail(icon, cy, ramp='gold'):
    icon.layer(ring(16, cy, 0.9, 2.2), ramp)


def ruby_heart():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8))
    bail(i, 9)
    i.layer(heart(16, 20, 9.5), 'gold')
    i.layer(heart(16, 20.4, 7.0), 'ruby')
    i.dot(12, 17, 't')
    return i.outline()


def sapphire_round():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8), 'silver')
    bail(i, 9, 'silver')
    i.layer(disc(16, 20, 9.2), 'silver')
    i.layer(disc(16, 20, 6.6), 'sapphire')
    i.layer(disc(16, 20, 3.0), 'sapphire', flat=3)
    i.layer(disc(15.5, 19.5, 1.6), 'sapphire', flat=0)
    i.dot(12, 16, 't')
    return i.outline()


def emerald_cut():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8))
    bail(i, 9)
    i.layer(diamond(16, 20, 8.6, 10.6), 'gold')
    i.layer(diamond(16, 20, 6.2, 8.2), 'emerald')
    i.layer(poly([(16, 12.5), (21.5, 20), (16, 27.5), (10.5, 20)]), 'emerald', flat=None)
    i.layer(poly([(16, 14.6), (19.4, 20), (16, 25.4), (12.6, 20)]), 'emerald', flat=2)
    i.dot(13, 17, 't')
    return i.outline()


def sunstone():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8))
    bail(i, 9)
    for k in range(8):
        a = k * math.pi / 4
        c, s = math.cos(a), math.sin(a)
        tip = (16 + c * 11.5, 20 + s * 11.5)
        l = (16 + math.cos(a - 0.38) * 7, 20 + math.sin(a - 0.38) * 7)
        r = (16 + math.cos(a + 0.38) * 7, 20 + math.sin(a + 0.38) * 7)
        i.layer(poly([tip, l, r]), 'gold', centre=(16, 20), radius=11)
    i.layer(disc(16, 20, 7.0), 'gold')
    i.layer(disc(16, 20, 4.6), 'topaz', centre=(16, 20), radius=5)
    i.layer(disc(16, 20, 2.6), 'topaz', flat=1)
    i.dot(14, 18, 't')
    return i.outline()


def moon():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8), 'silver')
    bail(i, 9, 'silver')
    i.layer(minus(disc(16, 20, 9.6), disc(20.4, 18.2, 8.2)), 'silver', centre=(16, 20), radius=10)
    i.layer(poly([(23.5, 21), (24.4, 23.6), (27, 24.4), (24.4, 25.2), (23.5, 27.8), (22.6, 25.2), (20, 24.4), (22.6, 23.6)]), 'gold', flat=1)
    return i.outline()


def skull():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8), 'cord')
    bail(i, 9, 'cord')
    i.layer(union(ellipse(16, 18.4, 8.6, 8.0), rect(11.5, 21, 20.5, 27.4)), 'bone', centre=(16, 20), radius=10)
    i.layer(ellipse(12.6, 18.4, 2.1, 2.6), 'hole', flat=0)
    i.layer(ellipse(19.4, 18.4, 2.1, 2.6), 'hole', flat=0)
    i.layer(poly([(16, 20.8), (14.7, 23.4), (17.3, 23.4)]), 'hole', flat=0)
    for x in (13, 15, 17, 19):
        i.layer(rect(x - 0.5, 25.2, x + 0.4, 27.4), 'bone', flat=2)
    return i.outline()


def rose():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8))
    bail(i, 9)
    i.layer(ellipse(9.6, 22.4, 4.8, 2.2), 'leaf')
    i.layer(ellipse(22.4, 22.4, 4.8, 2.2), 'leaf')
    i.layer(disc(16, 18.6, 8.2), 'rose')
    i.layer(ring(16, 18.6, 4.4, 5.4), 'rose', flat=3)
    i.layer(ring(16, 18.6, 1.8, 2.7), 'rose', flat=3)
    i.layer(disc(16, 18.6, 1.0), 'rose', flat=3)
    i.layer(poly([(14, 25.8), (18, 25.8), (16, 28.6)]), 'leaf')
    i.dot(12, 14, 't')
    return i.outline()


def rune_stone():
    i = Icon()
    i.chain(((5, 1), (27, 1)), (16, 8), 'steel')
    bail(i, 9, 'steel')
    hexagon = poly([(16, 11), (24.2, 15.6), (24.2, 24.4), (16, 29), (7.8, 24.4), (7.8, 15.6)])
    i.layer(hexagon, 'stone', centre=(16, 20), radius=10)
    i.layer(poly([(16, 13.4), (22.2, 16.9), (22.2, 23.1), (16, 26.6), (9.8, 23.1), (9.8, 16.9)]), 'stone', centre=(16, 20), radius=9, flat=1)
    # a carved rune: a vertical stroke with two arms and a foot
    for (x0, y0, x1, y1) in ((15, 15, 16, 25), (12, 17, 15, 18), (16, 20, 20, 21), (12, 23, 15, 24)):
        i.layer(rect(x0, y0, x1, y1), 'rune', flat=1)
    return i.outline()


AMULETS = [
    ('ruby-heart', 'Ruby heart', ruby_heart),
    ('sapphire', 'Sapphire', sapphire_round),
    ('emerald', 'Emerald', emerald_cut),
    ('sunstone', 'Sunstone', sunstone),
    ('moon', 'Moon', moon),
    ('skull', 'Bone skull', skull),
    ('rose', 'Rose', rose),
    ('rune-stone', 'Rune stone', rune_stone),
]


def preview(path, scale=8):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    sheet = Image.new('RGBA', (len(AMULETS) * (CELL * scale + 8), CELL * scale + 28), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    for k, (_, label, make) in enumerate(AMULETS):
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


if __name__ == '__main__':
    main()
