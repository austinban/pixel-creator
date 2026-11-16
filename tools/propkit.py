"""Shared by the small scenery kits (corrupted terrain, graveyard): solids for tools/make_fungi.py's ray caster, a renderer, ground decals, flat-top coverage and a contact sheet.

Everything is in the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level, the right face lit, the left face shaded), world x running down and to the right,
y down and to the left, h up, with the origin at the middle of the footprint on the ground. A pixel's line of sight is (ox + t, oy + t, t), and the nearest solid has the largest t.
A body is anything with `hit(ox, oy)` giving (t, normal) and the attributes make_fungi.colour reads (mat, c, spots, pores, glow, mark); `mark` may also be a function
`mark(body, p, n, step, px, py)` that returns a palette role or None, for painted details (moss, runes, strata).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildings import Solid, plane, norm  # noqa: E402
import make_fungi as fg  # noqa: E402
from make_fungi import Ellipsoid, Frustum, hashed, step_of  # noqa: E402,F401

PX = 16.0


def rnd(seed, *k):
    """A repeatable number in [0, 1) from a seed and some integers."""
    n = 0
    for v in k:
        n = n * 31 + int(v) + 17
    return hashed(seed & 0xFFFF, (n + (seed >> 16)) & 0xFFFF, 5) / 65536.0


# --- bodies ----------------------------------------------------------------------------------
class Poly:
    """A convex solid given by planes (outward normal, offset), drawn with a four-step ramp (lit to shaded)."""

    def __init__(self, planes, mat, c=(0.0, 0.0), mark=None, glow=False, **extra):
        self.solid = Solid(planes, 'x')
        self.mat, self.c, self.mark, self.glow = mat, c, mark, glow
        self.spots, self.pores, self.spotramp, self.poreramp = (), (), None, None
        self.__dict__.update(extra)

    def hit(self, ox, oy):
        return self.solid.hit((ox, oy, 0.0))


def box(x0, x1, y0, y1, z0, z1, mat, **kw):
    return Poly([((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)], mat, c=((x0 + x1) / 2, (y0 + y1) / 2), **kw)


def taper(cx, cy, z0, z1, hx0, hy0, hx1, hy1, mat, top=True, **kw):
    """A four-sided post that narrows from half-widths (hx0, hy0) at z0 to (hx1, hy1) at z1: an obelisk, a pillar, a stone with sloping sides."""
    dz = z1 - z0
    planes = [plane((dz, 0, hx0 - hx1), (cx + hx0, cy, z0)), plane((-dz, 0, hx0 - hx1), (cx - hx0, cy, z0)),
              plane((0, dz, hy0 - hy1), (cx, cy + hy0, z0)), plane((0, -dz, hy0 - hy1), (cx, cy - hy0, z0)), ((0, 0, -1), -z0)]
    if top:
        planes.append(((0, 0, 1), z1))
    return Poly(planes, mat, c=(cx, cy), **kw)


def lean_slab(cx, cy, z0, z1, hx, hy, lean, mat, lean_axis='x', **kw):
    """An upright slab (half-widths hx, hy) whose top has moved `lean` units along an axis: a gravestone that has settled."""
    dz = z1 - z0
    if lean_axis == 'x':
        planes = [plane((dz, 0, -lean), (cx + hx, cy, z0)), plane((-dz, 0, lean), (cx - hx, cy, z0)),
                  ((0, 1, 0), cy + hy), ((0, -1, 0), -(cy - hy))]
    else:
        planes = [plane((0, dz, -lean), (cx, cy + hy, z0)), plane((0, -dz, lean), (cx, cy - hy, z0)),
                  ((1, 0, 0), cx + hx), ((-1, 0, 0), -(cx - hx))]
    planes += [((0, 0, 1), z1), ((0, 0, -1), -z0)]
    return Poly(planes, mat, c=(cx, cy), **kw)


def cut_top(body, nx, ny, nz, px, py, pz):
    """Take a corner off a Poly with one more plane through (px, py, pz): a broken top."""
    body.solid.planes.append(plane((nx, ny, nz), (px, py, pz)))
    return body


def colour(body, p, n, step, px, py):
    if callable(body.mark):
        got = body.mark(body, p, n, step, px, py)
        if got:
            return got
    return fg.colour(body, p, n, step, px, py)


# --- drawing -----------------------------------------------------------------------------------
def size_for(fx, fy, tall, pad=8, low=8):
    """(w, h, anchor) of a picture for a footprint of fx x fy cells and a thing `tall` levels high, anchored at the middle of the footprint on the ground."""
    w = int(16 * (fx + fy)) + 2 * pad
    up = int(math.ceil(tall * PX)) + 4
    h = up + int(4 * (fx + fy)) + low
    return w, h, (w // 2, up + int(4 * (fx + fy)))


def render(bodies, w, h, anchor, outline=True, seams=True):
    ax, ay = anchor
    grid = [[None] * w for _ in range(h)]
    depth = [[0.0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            a, b = (px + 0.5 - ax) / 16.0, (py + 0.5 - ay) / 8.0
            ox, oy = (a + b) / 2, (b - a) / 2
            best = None
            for body in bodies:
                got = body.hit(ox, oy)
                if got and got[0] > 0 and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], body)
            if best is None:
                continue
            t, n, body = best
            p = (ox + t, oy + t, t)
            grid[py][px] = (colour(body, p, n, step_of(n), px, py), id(body))
            depth[py][px] = ox + t + oy + t + t
    out = [[(c[0] if c else '.') for c in row] for row in grid]
    if seams:
        for y in range(h):
            for x in range(w):
                cell = grid[y][x]
                if not cell:
                    continue
                for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                    other = grid[ny][nx] if 0 <= nx < w and 0 <= ny < h else None
                    if other and other[1] != cell[1] and depth[y][x] < depth[ny][nx] - 0.3:
                        out[y][x] = DARKER.get(out[y][x], out[y][x])
                        break
    final = [r[:] for r in out]
    if outline:
        for y in range(h):
            for x in range(w):
                if grid[y][x] is None and any(0 <= x + dx < w and 0 <= y + dy < h and grid[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    final[y][x] = 'O'
    return [''.join(r) for r in final]


DARKER = {'r': 'q', 'q': 'p', 'p': 'l', 'l': 'k', 'k': 'w', 'w': 'x', 't': 'C', 'C': 'c', 'c': 'f', 'f': 'g', 'g': 'w', 'j': 'i', 'i': 'h', 'h': 'u', 'e': 'f',
          'z': 'A', 'A': 'B', 'B': 's', 'o': 'n', 'n': 'm', 'm': 'k', 'd': 'b', 'b': 'a', 'a': 'x', 'v': 'l', 'u': 'w'}


def add_outline(rows):
    """A one-pixel `O` round everything painted, on the empty pixels that touch it (the sprites' outline)."""
    h, w = len(rows), len(rows[0])
    out = [list(r) for r in rows]
    for y in range(h):
        for x in range(w):
            if rows[y][x] == '.' and any(0 <= x + dx < w and 0 <= y + dy < h and rows[y + dy][x + dx] not in '.O' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'O'
    return [''.join(r) for r in out]


def top_cover(bodies, cells, level_of, n=8):
    """For each cell, the share of its area (n x n samples) where the nearest surface is the flat plane at that cell's level. `cells` are (i, j) from the footprint's back corner,
    in cell units centred on the footprint: cell (i, j) spans x in [i - fx/2, i + 1 - fx/2]."""
    fx, fy = max(i for i, _ in cells) + 1, max(j for _, j in cells) + 1
    out = {}
    for i, j in sorted(cells):
        h = float(level_of(i, j))
        got = 0
        for a in range(n):
            for b in range(n):
                x, y = i - fx / 2 + (a + 0.5) / n, j - fy / 2 + (b + 0.5) / n
                best = None
                for body in bodies:
                    g = body.hit(x - h, y - h)
                    if g and (best is None or g[0] > best[0]):
                        best = g
                got += bool(best and abs(best[0] - h) < 1e-6 and best[1][2] > 0.99)
        out[(i, j)] = got / (n * n)
    return out


# --- ground decals --------------------------------------------------------------------------
def decal(fx, fy, painter, margin=0):
    """A picture of a flat thing on the ground: (rows, anchor), size 32 fx.. across by 16.. down for a footprint of fx x fy cells. `painter(X, Y)` gives a role or None for the
    ground point (X, Y) in cell units from the middle (the diamond is |X| <= fx/2, |Y| <= fy/2)."""
    w, h = 16 * (fx + fy), 8 * (fx + fy)
    anchor = (w // 2, h // 2)
    rows = []
    for py in range(h):
        row = ''
        for px in range(w):
            a, b = (px + 0.5 - anchor[0]) / 16.0, (py + 0.5 - anchor[1]) / 8.0
            X, Y = (a + b) / 2, (b - a) / 2
            if abs(X) > fx / 2 - margin or abs(Y) > fy / 2 - margin:
                row += '.'
                continue
            row += painter(X, Y, px, py) or '.'
        rows.append(row)
    return rows, anchor


# --- a contact sheet ----------------------------------------------------------------------------
def contact_sheet(path, items, scale=2, width=1500, bg=(30, 34, 56)):
    """items: dicts with label, frames (a list of row-lists), anchor, fp (fx, fy), walk (None, or {cell: cover}), levels (a function (i, j) -> level, for the walkable colour)."""
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}
    placed, x, y, rowh = [], 14, 14, 0
    for it in items:
        fw, fh = len(it['frames'][0][0]), len(it['frames'][0])
        w, h = (fw * len(it['frames']) + 4 * (len(it['frames']) - 1)) * scale, fh * scale + 30
        if x + w > width - 14:
            x, y, rowh = 14, y + rowh + 12, 0
        placed.append((it, x, y, fw, fh))
        x += max(w, 90) + 16
        rowh = max(rowh, h)
    sheet = Image.new('RGBA', (width, y + rowh + 20), bg + (255,))
    d = ImageDraw.Draw(sheet)
    for it, x, y, fw, fh in placed:
        top = y + 14
        ax, ay = it['anchor']
        fx, fy = it['fp']
        for k, rows in enumerate(it['frames']):
            ox = x + k * (fw + 4) * scale
            for i, j in sorted(it.get('cells') or [(a, b) for a in range(fx) for b in range(fy)]):
                pts = [(ax + 16 * ((i - fx / 2 + dx) - (j - fy / 2 + dy)), ay + 8 * ((i - fx / 2 + dx) + (j - fy / 2 + dy))) for dx, dy in ((0, 0), (1, 0), (1, 1), (0, 1))]
                walk = it.get('walk')
                fill = (70, 110, 70, 255) if walk and walk.get((i, j), 0) >= 0.6 else ((100, 70, 70, 255) if walk else it.get('ground', (58, 62, 90, 255)))
                d.polygon([(ox + p * scale, top + q * scale) for p, q in pts], fill=fill, outline=(0, 0, 0, 90))
            im = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
            for yy, line in enumerate(rows):
                for xx, ch in enumerate(line):
                    if ch != '.':
                        im.putpixel((xx, yy), rgb[ch] + (255,))
            sheet.alpha_composite(im.resize((fw * scale, fh * scale), Image.NEAREST), (ox, top))
        note = ''
        if it.get('walk'):
            note = f"  WALK min {min(it['walk'].values()):.2f}"
        d.text((x, y), it['label'] + note, fill=(230, 220, 200, 255))
    sheet.save(path)
