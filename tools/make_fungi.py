#!/usr/bin/env python3
"""Giant mushrooms for the corrupted lands, to stand where trees would: six of them, five on one ground tile and one that covers four and can be walked on.

Each is a small 3D model of round solids (ellipsoids for caps and bulbs, tapering cylinders for stems), drawn in exactly the ground tiles' projection (16 across and 8 down a
cell, 16 pixels a level, the right-hand face lit, the left-hand face shaded), in the shared colour roles, then given the one-pixel outline. A mushroom looks the same from every side,
so there is one picture of each (not an NE and an SE); NW and SW would be it flipped, which a game can do for variety.

    spotted     a tall toadstool: a plum cap with cream spots on a pale stem with a ring, swollen at the foot
    bell        a slender tall bell cap in deep teal with glowing pores, on a thin pale stem
    cluster     three small toadstools of different heights, growing together
    puffball    a pale round puffball with plum warts and glowing pores
    parasol     a very tall thin stem under a wide flat violet umbrella that shades the tile like a tree
    toadstool   the big one, on four tiles (2 x 2): a wide low hot-pink toadstool whose flat top is two levels up and can be walked on

    python3 tools/make_fungi.py --preview previews/fungi.png        every mushroom, enlarged, over its footprint

As assets they are the **Mushroom Trees** category (folder `mushroom-trees`), ids `fungus-NAME`.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

CELL_W = 48                      # a tile is 32 wide; caps hang out past it, so the cell has 8 pixels more each side
PX = 16.0                        # pixels per world unit (one cell, one level)
LIGHT = (0.3, -0.25, 0.92)       # towards the light: above and a little to the right, so the right face is lit and the left face shaded (x, y along the ground, then up)


# --- the solids --------------------------------------------------------------------------------
# World space: x and y run along the ground (a cell is one unit), h is up (a level is one unit). The ground tile's middle is (0, 0). A pixel's line of sight
# is the line (ox + t, oy + t, t), so the nearest solid to the camera is the one with the largest t.
class Ellipsoid:
    """A round body (a cap, a bulb), kept between heights `lo` and `hi`: with lo at its middle it is a dome, with hi below its top it has a flat top."""

    def __init__(self, mat, c, radii, lo=-1e9, hi=1e9, **extra):
        self.mat, self.c, self.r, self.lo, self.hi = mat, c, radii, lo, hi
        self.__dict__.update(dict(spots=(), pores=(), spotramp=None, poreramp=None, glow=False, mark=None), **extra)

    def hit(self, ox, oy):
        (cx, cy, ch), (rx, ry, rh) = self.c, self.r
        a, b, d = ox - cx, oy - cy, -ch
        A = 1 / rx ** 2 + 1 / ry ** 2 + 1 / rh ** 2
        B = 2 * (a / rx ** 2 + b / ry ** 2 + d / rh ** 2)
        C = a * a / rx ** 2 + b * b / ry ** 2 + d * d / rh ** 2 - 1
        disc = B * B - 4 * A * C
        if disc < 0:
            return None
        sq = math.sqrt(disc)
        lo, up = (-B - sq) / (2 * A), (-B + sq) / (2 * A)
        top = False
        if self.hi < up:
            up, top = self.hi, True
        lo = max(lo, self.lo)
        if lo > up:
            return None
        if top:
            return up, (0.0, 0.0, 1.0)
        n = ((a + up) / rx ** 2, (b + up) / ry ** 2, (up - ch) / rh ** 2)
        m = math.sqrt(sum(v * v for v in n))
        return up, tuple(v / m for v in n)


class Frustum:
    """A tapering upright cylinder (a stem, a ring, a skirt of gills) from height h0 to h1, radius r0 at the bottom and r1 at the top."""

    def __init__(self, mat, c, h0, h1, r0, r1, **extra):
        self.mat, self.c, self.h0, self.h1, self.r0, self.r1 = mat, c, h0, h1, r0, r1
        self.__dict__.update(dict(spots=(), pores=(), spotramp=None, poreramp=None, glow=False, mark=None), **extra)
        self.k = (r1 - r0) / (h1 - h0)

    def hit(self, ox, oy):
        a, b = ox - self.c[0], oy - self.c[1]
        k = self.k
        m = self.r0 - k * self.h0
        A, B, C = 2 - k * k, 2 * (a + b) - 2 * m * k, a * a + b * b - m * m
        disc = B * B - 4 * A * C
        if disc < 0:
            return None
        sq = math.sqrt(disc)
        lo, up = max((-B - sq) / (2 * A), self.h0), (-B + sq) / (2 * A)
        top = False
        if self.h1 < up:
            up, top = self.h1, True
        if lo > up:
            return None
        if top:
            return up, (0.0, 0.0, 1.0)
        x, y = a + up, b + up
        r = math.hypot(x, y)
        if r < 1e-9:
            return up, (0.0, 0.0, 1.0)
        n = (x / r, y / r, -k)
        m = math.sqrt(sum(v * v for v in n))
        return up, tuple(v / m for v in n)


# --- one mushroom, from a few numbers ------------------------------------------------------------
def mushroom(cx, cy, stem_h, stem_r, cap_r, cap_h, ramps, foot=0.0, ring=None, flare=0.0, spots=(), pores=(), gill_drop=0.0, base_h=0.0):
    """A toadstool at (cx, cy): a stem that tapers up (and swells at the foot by `foot`), an optional ring, a dome cap on it with spots and glowing pores painted on, and a skirt of gills under the rim."""
    parts = [Frustum(ramps['stem'], (cx, cy), base_h, base_h + stem_h, stem_r * (1 + foot), stem_r * 0.8, mark='speckle')]
    if foot:
        parts.append(Ellipsoid(ramps['stem'], (cx, cy, base_h + stem_r * 0.7), (stem_r * (1 + foot) * 1.15, stem_r * (1 + foot) * 1.15, stem_r * 1.1), lo=base_h, mark='speckle'))
    if ring:
        rh = base_h + stem_h * ring
        parts.append(Frustum(ramps['ring'], (cx, cy), rh - 0.16, rh, stem_r * 1.15, stem_r * 1.9))
    top = base_h + stem_h
    if gill_drop:
        parts.append(Frustum(ramps['gill'], (cx, cy), top - gill_drop, top + 0.1, cap_r * 0.55, cap_r * 0.97, mark='gills'))
    parts.append(Ellipsoid(ramps['cap'], (cx, cy, top), (cap_r, cap_r, cap_h), lo=top - 0.04 - flare, spots=spots, pores=pores, spotramp=ramps.get('spot'), poreramp=ramps.get('glow'), mark='cap'))
    return parts


GLOW = ('r', 'o', 'o', 'q')                          # the teal glow of a pore or an eye


def ramp(*letters):
    return tuple(letters)


# --- the six ----------------------------------------------------------------------------------
def spotted():
    ramps = dict(cap=ramp('e', 'f', 'g', 'w'), stem=ramp('t', 'C', 'c', 'f'), ring=ramp('C', 'c', 'f', 'g'), gill=ramp('C', 'c', 'e', 'g'), spot=ramp('t', 't', 'C', 'c'))
    spots = ((0.0, 0.0, 0.17), (0.32, 0.12, 0.13), (-0.2, 0.34, 0.13), (-0.38, -0.12, 0.12), (0.12, -0.38, 0.13), (0.42, -0.26, 0.1), (-0.08, 0.6, 0.1), (0.55, 0.2, 0.1))
    return mushroom(0, 0, 2.2, 0.2, 0.78, 0.62, ramps, foot=0.55, ring=0.62, spots=spots, gill_drop=0.16)


def bell():
    ramps = dict(cap=ramp('r', 'q', 's', 'D'), stem=ramp('t', 'C', 'p', 'l'), ring=ramp('t', 'C', 'p', 'l'), gill=ramp('t', 'r', 'q', 's'), glow=GLOW)
    pores = ((0.0, 0.0, 0.1), (0.22, 0.1, 0.08), (-0.2, 0.18, 0.08), (0.02, 0.3, 0.07), (-0.1, -0.22, 0.08))
    return mushroom(0, 0, 2.7, 0.14, 0.5, 1.0, ramps, foot=0.7, pores=pores, gill_drop=0.2)


def cluster():
    ramps = dict(cap=ramp('l', 'u', 'w', 'x'), stem=ramp('t', 'C', 'c', 'f'), ring=ramp('C', 'c', 'f', 'g'), gill=ramp('C', 'c', 'e', 'g'), spot=ramp('r', 'r', 'q', 's'))
    out = []
    for cx, cy, h, sr, cr, ch in ((-0.2, 0.18, 1.0, 0.1, 0.38, 0.3), (0.26, 0.2, 0.62, 0.1, 0.32, 0.26), (0.0, -0.22, 1.7, 0.14, 0.5, 0.4)):
        spots = ((0.0, 0.0, 0.11), (cr * 0.55, 0.05, 0.08), (-cr * 0.4, -cr * 0.35, 0.08))
        out += mushroom(cx, cy, h, sr, cr, ch, ramps, foot=0.45, spots=spots, gill_drop=0.1)
    return sorted(out, key=lambda b: b.c[0] + b.c[1])        # nearest last: it does not matter for the hit test, but keeps the order stable


def puffball():
    pale, plum = ramp('t', 'C', 'c', 'f'), ramp('f', 'g', 'w', 'x')
    out = [Ellipsoid(pale, (0, 0, 0.78), (0.52, 0.52, 0.78), lo=0.0, spots=(), mark='speckle'),
           Frustum(pale, (0, 0), 0.0, 0.3, 0.3, 0.42, mark='speckle')]
    warts = ((0.0, 0.0, 0.18), (0.26, 0.1, 0.12), (-0.22, 0.2, 0.12), (0.12, -0.3, 0.12), (-0.28, -0.14, 0.1), (0.36, -0.12, 0.09))
    out[0].spots, out[0].spotramp = warts, plum
    out[0].pores, out[0].poreramp = ((0.0, 0.0, 0.07), (0.15, 0.2, 0.06)), GLOW
    out.append(Ellipsoid(plum, (0.47, 0.0, 0.7), (0.17, 0.17, 0.2)))
    out.append(Ellipsoid(plum, (0.0, 0.47, 0.5), (0.17, 0.17, 0.2)))
    out.append(Ellipsoid(ramp('r', 'o', 'o', 'q'), (0.5, 0.16, 0.9), (0.11, 0.11, 0.13), glow=True))
    out.append(Ellipsoid(ramp('r', 'o', 'o', 'q'), (0.2, 0.46, 0.84), (0.11, 0.11, 0.13), glow=True))
    return out


def parasol():
    ramps = dict(cap=ramp('v', 'l', 'k', 'w'), stem=ramp('C', 'c', 'f', 'g'), ring=ramp('C', 'c', 'f', 'g'), gill=ramp('t', 'p', 'l', 'k'), spot=ramp('t', 't', 'C', 'p'), glow=GLOW)
    spots = ((0.0, 0.0, 0.16), (0.4, 0.1, 0.13), (-0.3, 0.35, 0.13), (-0.42, -0.2, 0.12), (0.2, -0.45, 0.13), (0.62, -0.3, 0.1), (0.0, 0.66, 0.1), (-0.66, 0.1, 0.1))
    return mushroom(0, 0, 3.0, 0.11, 0.98, 0.5, ramps, foot=0.9, spots=spots, gill_drop=0.12)


def toadstool():
    """The walkable one. Its flat top is two levels up (32 pixels) and spans the four tiles; the stem that holds it is out of the way under it."""
    cap, stem, gill, spot = ramp('j', 'i', 'h', 'u'), ramp('t', 'C', 'c', 'f'), ramp('C', 'c', 'e', 'g'), ramp('t', 't', 'C', 'c')
    top = 2.0
    out = [Frustum(stem, (0, 0), 0.0, 1.7, 0.62, 0.5, mark='speckle'),
           Ellipsoid(stem, (0, 0, 0.45), (0.78, 0.78, 0.5), lo=0.0, mark='speckle'),
           Frustum(gill, (0, 0), 0.95, 1.8, 0.7, 1.45, mark='gills')]
    spots = ((0.0, 0.0, 0.34), (0.82, 0.3, 0.26), (-0.7, 0.62, 0.26), (-0.72, -0.5, 0.24), (0.4, -0.86, 0.26), (0.98, -0.62, 0.2), (-0.1, 1.06, 0.2), (1.02, 0.86, 0.18), (-1.12, 0.0, 0.2), (-0.42, -1.02, 0.18))
    out.append(Ellipsoid(cap, (0, 0, 1.62), (1.8, 1.8, 0.4), mark='cap'))          # the rounded rim, widest at the middle of its edge
    out.append(Frustum(cap, (0, 0), 1.86, top, 1.46, 1.44, spots=spots, spotramp=spot, mark='cap'))          # the flat top
    return out


# name, label, builder, footprint (cells each way), the height of the tallest thing in levels
SHAPES = [
    ('spotted', 'Spotted toadstool', spotted, 1, 3.55),
    ('bell', 'Bell mushroom', bell, 1, 3.8),
    ('cluster', 'Toadstool cluster', cluster, 1, 2.2),
    ('puffball', 'Puffball', puffball, 1, 1.6),
    ('parasol', 'Parasol mushroom', parasol, 1, 3.55),
    ('toadstool', 'Giant toadstool (walkable)', toadstool, 2, 2.0),
]


def cell_of(footprint, tall):
    """The picture's size and its anchor (the middle of the footprint on the ground): wide enough for the cap to hang out, tall enough for the top, with room below for the near corner."""
    if footprint == 2:
        return 96, 80, (48, 60)
    h = int(math.ceil(tall * PX)) + 22
    return CELL_W, h, (CELL_W // 2, h - 12)


# --- drawing ---------------------------------------------------------------------------------
def hashed(a, b, salt=0):
    n = (int(a) * 374761393 + int(b) * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


def step_of(n):
    s = sum(n[i] * LIGHT[i] for i in range(3)) / math.sqrt(sum(c * c for c in LIGHT))
    return 0 if s > 0.62 else 1 if s > 0.05 else 2 if s > -0.45 else 3


def colour(body, p, n, step, px, py):
    """The colour role of one pixel of a body: its ramp at the lit step, with its spots, pores and texture."""
    if body.glow:
        return body.mat[0 if step < 2 else 1]
    r = body.mat
    c = (p[0] - body.c[0], p[1] - body.c[1])
    if n[2] > 0.12:
        for dx, dy, rho in body.pores:
            if (c[0] - dx) ** 2 + (c[1] - dy) ** 2 < rho * rho:
                return body.poreramp[0 if step < 2 else 1]
        for dx, dy, rho in body.spots:
            if (c[0] - dx) ** 2 + (c[1] - dy) ** 2 < rho * rho:
                return body.spotramp[step]
    mark = body.mark
    if mark == 'speckle' and step < 3 and hashed(px, py, 1) % 19 == 0:
        return r[min(3, step + 1)]
    if mark == 'bark' and step < 3 and (px + hashed(0, py // 3, 2) % 3) % 4 == 0:
        return r[min(3, step + 1)]
    if mark == 'gills':
        ang = math.atan2(c[1], c[0])
        if int((ang + math.pi) / (2 * math.pi) * 28) % 2 == 0:
            return r[min(3, step + 1)]
    if mark == 'cap' and step == 1 and hashed(px, py, 3) % 23 == 0:
        return r[0]
    return r[step]


def render(builder, footprint, tall):
    w, h, (ax, ay) = cell_of(footprint, tall)
    bodies = builder()
    grid = [[None] * w for _ in range(h)]
    depth = [[0.0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            a, b = (px + 0.5 - ax) / 16.0, (py + 0.5 - ay) / 8.0
            ox, oy = (a + b) / 2, (b - a) / 2
            best = None
            for body in bodies:
                got = body.hit(ox, oy)
                if got and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], body)
            if best is None:
                continue
            t, n, body = best
            p = (ox + t, oy + t, t)
            grid[py][px] = (colour(body, p, n, step_of(n), px, py), id(body))
            depth[py][px] = t
    out = [[(c[0] if c else '.') for c in row] for row in grid]
    # where a nearer body overlaps another, the edge falls into shadow
    for y in range(h):
        for x in range(w):
            cell = grid[y][x]
            if not cell:
                continue
            for nx, ny in ((x - 1, y), (x, y - 1)):
                other = grid[ny][nx] if 0 <= nx < w and 0 <= ny < h else None
                if other and other[1] != cell[1] and depth[ny][nx] - depth[y][x] > 0.22:
                    out[y][x] = 'x' if out[y][x] in 'jiehgfuwxlkDsq' else out[y][x]
    final = [row[:] for row in out]
    for y in range(h):
        for x in range(w):
            if grid[y][x] is None and any(0 <= x + dx < w and 0 <= y + dy < h and grid[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                final[y][x] = 'O'
    return [''.join(r) for r in final], (w, h), (ax, ay)


def preview(path, scale=5):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}
    drawn = [(label, footprint, render(builder, footprint, tall)) for _, label, builder, footprint, tall in SHAPES]
    width = sum(d[2][1][0] for d in drawn) + 8 * (len(drawn) + 1)
    height = max(d[2][1][1] for d in drawn) + 24
    sheet = Image.new('RGB', (width * scale, height * scale), (48, 70, 84))
    draw = ImageDraw.Draw(sheet)
    x0 = 8
    for label, footprint, (rows, (w, h), (ax, ay)) in drawn:
        oy = height - h - 4
        # the footprint on the ground, so the anchor can be checked: a diamond one or two cells across each way
        n = footprint
        corners = [(ax + 16 * (x - y), ay + 8 * (x + y)) for x, y in ((-n / 2 * 0 - n / 2 * 1, -n / 2), (n / 2, -n / 2), (n / 2, n / 2), (-n / 2, n / 2))]
        corners = [(ax + 16 * (x - y), ay + 8 * (x + y)) for x, y in ((-n / 2, -n / 2), (n / 2, -n / 2), (n / 2, n / 2), (-n / 2, n / 2))]
        draw.polygon([((x0 + cx) * scale, (oy + cy) * scale) for cx, cy in corners], fill=(70, 120, 120), outline=(120, 170, 160))
        for y, line in enumerate(rows):
            for x, ch in enumerate(line):
                if ch != '.':
                    draw.rectangle([(x0 + x) * scale, (oy + y) * scale, (x0 + x + 1) * scale - 1, (oy + y + 1) * scale - 1], fill=rgb[ch])
        draw.text((x0 * scale, 2 * scale), label, fill=(235, 238, 245))
        x0 += w + 8
    sheet.save(path)


# --- the assets ----------------------------------------------------------------------------
CATEGORY = 'Mushroom Trees'
FOLDER = 'mushroom-trees'
WALKABLE_TOP = 2.0            # the giant toadstool's flat top, in levels (16 pixels each)


def build_assets():
    """One still asset per mushroom (`fungus-NAME`), each in its own cell with the anchor at the middle of its footprint on the ground."""
    assets = []
    for name, label, builder, footprint, tall in SHAPES:
        rows, (w, h), anchor = render(builder, footprint, tall)
        extra = {'fungus': {'footprint': [footprint, footprint], 'blocks': footprint == 1}}
        if name == 'toadstool':
            extra['fungus']['walkableTop'] = {'level': WALKABLE_TOP, 'pixels': int(WALKABLE_TOP * PX), 'covers': 'the whole 2 x 2 footprint'}
        assets.append(family(CATEGORY, w, h, anchor, folder=FOLDER)(f'fungus-{name}', label, 'still', [rows], **extra))
    return assets


def write_package(folder):
    """Beside the sheets: mushroom-trees.json, how a game uses them in numbers (README.md says it in words)."""
    body = {}
    for name, label, builder, footprint, tall in SHAPES:
        rows, (w, h), (ax, ay) = render(builder, footprint, tall)
        body[name] = {'label': label, 'file': f'fungus-{name}.png', 'cell': [w, h], 'anchor': {'x': ax, 'y': ay}, 'footprint': [footprint, footprint]}
        if name == 'toadstool':
            body[name]['walkableTop'] = {'level': WALKABLE_TOP, 'pixels': int(WALKABLE_TOP * PX)}
    write_json(folder, 'mushroom-trees.json', 'The mushroom sheets in this folder. See README.md beside this file for the whole story.', {'mushrooms': body})


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write every mushroom, enlarged, here')
    parser.add_argument('--scale', type=int, default=5)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, args.scale)
        print(f'the mushrooms, enlarged -> {args.preview}')


if __name__ == '__main__':
    main()
