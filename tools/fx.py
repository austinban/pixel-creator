"""Small drawing helpers for the ability animations (make_burst.py, make_ring.py, make_icons.py, make_vanish.py, make_ground_fx.py).

A frame is a grid of colour roles (a list of lists of single letters, '.' for empty). Everything is drawn pixel by pixel with no smoothing, lit from the upper left like the
rest of the game, and in the shared palette's roles. Randomness is a hash of the position, so a frame is always drawn the same way.
"""
import math

import extract_poses as ep


def hashed(a, b, salt=0):
    n = (int(a) * 374761393 + int(b) * 668265263 + int(salt) * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [['.'] * w for _ in range(h)]

    def put(self, x, y, c):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h and c != '.':
            self.rows[y][x] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        return self.rows[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def lines(self):
        return [''.join(r) for r in self.rows]

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def ellipse(self, cx, cy, rx, ry, c, thick=1.0):
        """A ring (its outline only) of the given thickness, in pixels across, for the ground."""
        rx_o, ry_o = rx + thick / 2, ry + thick / 4
        rx_i, ry_i = max(0.0, rx - thick / 2), max(0.0, ry - thick / 4)
        for y in range(int(cy - ry_o - 1), int(cy + ry_o + 2)):
            for x in range(int(cx - rx_o - 1), int(cx + rx_o + 2)):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                outer = (dx / rx_o) ** 2 + (dy / ry_o) ** 2 <= 1.0
                inner = rx_i > 0 and ry_i > 0 and (dx / rx_i) ** 2 + (dy / ry_i) ** 2 < 1.0
                if outer and not inner:
                    self.put(x, y, c)

    def blob(self, cx, cy, r, ramp, ry=None, edge=0.0, seed=0):
        """A shaded round blob: lit tone on the upper left, then base, shade and deep towards the lower right. `edge` makes the rim ragged (0-1)."""
        ry = r if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = (x + 0.5 - cx) / max(r, 0.3), (y + 0.5 - cy) / max(ry, 0.3)
                d = math.hypot(dx, dy)
                if edge:
                    d += (hashed(x, y, seed) - 0.5) * edge
                if d > 1.0:
                    continue
                lit = -(dx * 0.55 + dy * 0.83)
                tone = 0 if lit > 0.5 else 1 if lit > -0.15 else 2 if lit > -0.6 else 3
                if d > 0.88:
                    tone = max(tone, 2)
                self.put(x, y, ramp[tone])

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                    self.put(x, y, c)

    def sparkle(self, cx, cy, size, c, core=None):
        """A four-point star: a plus with a longer vertical, and a brighter middle."""
        for k in range(1, size + 1):
            self.put(cx + k, cy, c)
            self.put(cx - k, cy, c)
            self.put(cx, cy + k, c)
            self.put(cx, cy - k, c)
        self.put(cx, cy, core or c)


def diamond_inside(cx, cy, x, y, half_w=16.0, half_h=8.0, shrink=0.0):
    """Is a pixel inside the diamond (a ground tile's top face) whose middle is (cx, cy)?"""
    return abs(x + 0.5 - cx) / half_w + abs(y + 0.5 - cy) / half_h <= 1.0 - shrink + 1e-9


def smoothstep(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def dither(x, y, level):
    """An ordered dither: True where a pixel is on at `level` (0 to 1), in a 4 x 4 pattern."""
    order = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
    return order[int(y) % 4][int(x) % 4] / 16.0 < level


def rgb_of():
    return {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}


def save_preview(path, frames, w, h, cols=4, scale=4, plots=None, ground_tile=None, label=None):
    """A sheet of frames, enlarged, over ground tiles at the plot centres in `plots` (a list of (x, y) in the cell)."""
    from PIL import Image
    rgb = rgb_of()
    rows = -(-len(frames) // cols)
    sheet = Image.new('RGBA', (cols * (w + 4) * scale, rows * (h + 4) * scale), (36, 38, 56, 255))
    for f, lines in enumerate(frames):
        cell = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for (px, py) in (plots or []):
            if ground_tile is not None:
                cell.alpha_composite(ground_tile, (px - 16, py - 8))
        over = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for y, line in enumerate(lines):
            for x, c in enumerate(line):
                if c != '.':
                    over.putpixel((x, y), rgb[c] + (255,))
        cell.alpha_composite(over)
        sheet.alpha_composite(cell.resize((w * scale, h * scale), Image.NEAREST), (((f % cols) * (w + 4) + 2) * scale, ((f // cols) * (h + 4) + 2) * scale))
    sheet.save(path)
    return sheet
