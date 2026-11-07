#!/usr/bin/env python3
"""Treasure chests for the ground: three rarities (common, rare, legendary), each shut and opening, each in NE and SE.

A chest stands on one ground tile. It is built as a small 3D model of convex solids (a hollow body of four walls and a floor, a hinged vaulted lid,
straps, a lock, feet, and the treasure inside) and drawn in exactly the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level,
the right-hand face lit and the left-hand face shaded), in the shared colour roles, then given the one-pixel outline.

    NE   the front of the chest (lock and hasp) is on the wall that runs NE-SW: the right-hand face as the camera sees it, lit
    SE   the front is on the wall that runs NW-SE: the left-hand face, shaded
    NW and SW are those two flipped, as for the characters.

Opening: the lid turns on its back hinge, the inside lights up, light rays and sparkles rise, and the lid settles open. It plays once and the last frame is
the open chest, the picture to keep drawing.

Rarity is size and richness: the common chest is a small banded wooden box; the rare one is bigger, on feet, in dark wood with steel corners, a sapphire lock
and a lined inside; the legendary one is the biggest, in violet lacquer trimmed in gold, with a crest and gems on the lid, claw feet, a ruby lock, velvet inside
and a heap of gold and jewels.

    python3 tools/make_chest.py --preview previews/chests.png        every chest, shut and opening, in NE and SE, enlarged
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

CELL_W, CELL_H = 48, 52       # a tile is 32 wide; the opening lid and the light swing out past it, so the cell has 8 pixels more each side
ANCHOR = (24, 40)               # the middle of the tile, on the ground: the point the game puts on the middle of the ground tile
FPS = 10
PX = 16.0                       # pixels per world unit (one cell, one level)
LIGHT = (0.3, -0.25, 0.92)      # towards the light: from above and a little to the right, so the right face is lit and the left face shaded


def hashed(a, b, salt=0):
    n = (int(a) * 374761393 + int(b) * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


# --- the rarities ------------------------------------------------------------------------
# Ramps are four roles, light to dark. Sizes are in world units (one cell = 1; a pixel = 1/16).
SPECS = {
    'common': dict(
        label='Common', dx=0.24, dy=0.35, zf=0.0, hb=0.38, lip=0.05, hl=0.17, facets=6, wall=1 / 16, lockw=2,
        wood=('b', 'a', 'g', 'w'), metal=('p', 'l', 'k', 'w'), lining=('g', 'w', 'x', 'x'), coins=('C', 'b', 'a', 'g'),
        straps=[(-0.23, 2), (0.23, 2)], band=0, posts=0, rim=False, feet=0,
        gems=[], lock='plain', lock_gem=None, heap=0.55, crest=False, glow=('t', 'C'), spark=('t', 'C'), plank=4,
    ),
    'rare': dict(
        label='Rare', dx=0.30, dy=0.43, zf=0.03, hb=0.46, lip=0.06, hl=0.23, facets=6, wall=1 / 16, lockw=2,
        wood=('a', 'e', 'g', 'w'), metal=('r', 'q', 'p', 'l'), lining=('l', 'k', 'w', 'x'), coins=('d', 'b', 'a', 'g'),
        straps=[(-0.26, 2), (0.26, 2)], band=1, posts=1, rim=True, feet=1,
        gems=[('o', 'n', 'm', 'k')], lock='gem', lock_gem=('o', 'n', 'm', 'k'), heap=0.7, crest=False, glow=('r', 'o'), spark=('r', 'o'), plank=4,
    ),
    'legendary': dict(
        label='Legendary', dx=0.34, dy=0.47, zf=0.06, hb=0.52, lip=0.07, hl=0.30, facets=8, wall=1.5 / 16, lockw=2,
        wood=('v', 'f', 'u', 'w'), metal=('d', 'b', 'a', 'g'), lining=('j', 'i', 'h', 'g'), coins=('d', 'b', 'a', 'g'),
        straps=[(-0.28, 2), (0.28, 2)], band=1, posts=1, rim=True, feet=2,
        gems=[('j', 'i', 'h', 'g'), ('o', 'n', 'm', 'k'), ('z', 'A', 'B', 's')], lock='gem', lock_gem=('j', 'i', 'h', 'g'),
        heap=1.0, crest=True, glow=('t', 'd'), spark=('t', 'd'), plank=4,
    ),
}
RARITIES = list(SPECS)

# the opening: (lid angle in degrees, inside glow 0-1, ray length in pixels, sparkles). The last frame is the chest resting open.
FRAMES = [(0, 0.0, 0, 0), (7, 0.3, 0, 0), (22, 0.5, 4, 1), (48, 0.7, 8, 2), (78, 0.9, 12, 3), (100, 1.0, 17, 5), (92, 1.0, 15, 4), (95, 1.0, 15, 4)]


# --- solids -------------------------------------------------------------------------------
def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def box_planes(x0, x1, y0, y1, z0, z1):
    return [((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)]


def affine(planes, sx, sy, sz, c):
    """The same convex shape scaled about the origin by (sx, sy, sz), then moved to c."""
    out = []
    for n, d in planes:
        m = (n[0] / sx, n[1] / sy, n[2] / sz)
        d2 = d + m[0] * c[0] + m[1] * c[1] + m[2] * c[2]
        k = math.sqrt(sum(a * a for a in m))
        out.append((tuple(a / k for a in m), d2 / k))
    return out


def octagon_frustum(r0, r1, z0, z1):
    """A round heap, eight-sided: radius r0 at z0 narrowing to r1 at z1 (flat top)."""
    planes = [((0, 0, 1), z1), ((0, 0, -1), -z0)]
    for k in range(8):
        a = k * math.pi / 4
        u = (math.cos(a), math.sin(a))
        n = norm((u[0] * (z1 - z0), u[1] * (z1 - z0), r0 - r1))
        planes.append((n, n[0] * u[0] * r0 + n[1] * u[1] * r0 + n[2] * z0))
    return planes


def octahedron(r):
    s = 1 / math.sqrt(3)
    return [(((sx * s), (sy * s), (sz * s)), r * s) for sx in (1, -1) for sy in (1, -1) for sz in (1, -1)]


def vault_planes(X, y, hl, lip, facets):
    """The lid, in its own frame: x from -X to X, base at z = 0, a short straight lip and a half ellipse over it, ends at y = +-y."""
    pts = [(X * math.cos(math.pi * i / facets), lip + hl * math.sin(math.pi * i / facets)) for i in range(facets + 1)]
    planes = [((1, 0, 0), X), ((-1, 0, 0), X), ((0, 0, -1), 0.0), ((0, 1, 0), y), ((0, -1, 0), y)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        ex, ez = x1 - x0, z1 - z0
        n = norm((ez, 0.0, -ex))
        planes.append((n, n[0] * x0 + n[2] * z0))
    return planes


class Part:
    """A convex solid in its own rest frame, how it is painted (kind), and whether it is part of the lid (it turns on the hinge)."""

    def __init__(self, planes, kind, lid=False, **info):
        self.planes, self.kind, self.lid, self.info = planes, kind, lid, info


def build_parts(spec):
    dx, dy, zf, hb, t = spec['dx'], spec['dy'], spec['zf'], spec['hb'], spec['wall']
    zt = zf + hb                                           # the top of the body: where the lid sits
    ov = 1 / 16
    parts = []
    # the hollow body: a floor and four walls, so the inside is really inside
    ft = zf + 0.04
    parts.append(Part(box_planes(-dx, dx, -dy, dy, zf, ft), 'wall'))
    parts.append(Part(box_planes(dx - t, dx, -dy, dy, zf, zt), 'wall'))
    parts.append(Part(box_planes(-dx, -dx + t, -dy, dy, zf, zt), 'wall'))
    parts.append(Part(box_planes(-dx, dx, dy - t, dy, zf, zt), 'wall'))
    parts.append(Part(box_planes(-dx, dx, -dy, -dy + t, zf, zt), 'wall'))
    # feet and corner posts
    if spec['feet']:
        f = spec['feet'] * 1.5 / 16 + 1 / 16
        for sx in (1, -1):
            for sy in (1, -1):
                x0, x1 = (dx - f, dx + 1 / 16) if sx > 0 else (-dx - 1 / 16, -dx + f)
                y0, y1 = (dy - f, dy + 1 / 16) if sy > 0 else (-dy - 1 / 16, -dy + f)
                parts.append(Part(box_planes(x0, x1, y0, y1, 0.0, zf + 0.02), 'foot'))
    if spec['posts']:
        pw = spec['posts'] / 16 + 1 / 16
        for sx in (1, -1):
            for sy in (1, -1):
                x0, x1 = (dx - pw + 1 / 16, dx + 1 / 16) if sx > 0 else (-dx - 1 / 16, -dx + pw - 1 / 16)
                y0, y1 = (dy - pw + 1 / 16, dy + 1 / 16) if sy > 0 else (-dy - 1 / 16, -dy + pw - 1 / 16)
                parts.append(Part(box_planes(x0, x1, y0, y1, zf, zt), 'post'))
    # the lock plate on the front of the body
    lw = spec['lockw'] / 16
    parts.append(Part(box_planes(dx, dx + 1 / 16, -lw, lw, zt - 6 / 16, zt - 1 / 16), 'lock'))
    # the lid, and what is fixed to it
    X = dx + ov
    lid = vault_planes(X, dy + ov, spec['hl'], spec['lip'], spec['facets'])
    # in its rest frame the lid is drawn with its hinge edge at x = -X; it is moved up to sit on the body here
    def lid_part(planes, kind, **info):
        return Part(planes, kind, lid=True, **info)

    parts.append(lid_part(lid, 'lid', X=X, y=dy + ov))
    parts.append(lid_part(box_planes(X, X + 1 / 16, -1.5 / 16, 1.5 / 16, -2 / 16, spec['lip'] + 1 / 16), 'hasp'))
    if spec['crest']:                                      # a gold spine along the lid's curve, with gems set in it
        parts.append(lid_part(vault_planes(X + 0.5 / 16, 1.5 / 16, spec['hl'] + 1.5 / 16, spec['lip'], spec['facets']), 'crest'))
        for fx, ramp, r in ((0.5, spec['gems'][1], 0.09), (0.0, spec['gems'][0], 0.12), (-0.5, spec['gems'][2], 0.09)):
            gx = fx * X
            gz = spec['lip'] + (spec['hl'] + 1.5 / 16) * math.sqrt(max(0.0, 1 - (gx / X) ** 2)) + 0.5 / 16
            parts.append(lid_part(affine(octahedron(r), 1, 1, 1.2, (gx, 0.0, gz)), 'gem', ramp=ramp))
    # the treasure
    ix, iy = dx - t, dy - t
    h = spec['heap']
    if h:
        top_h = ft + (hb - 0.05) * (0.45 + 0.4 * h) if h < 1 else zt + 0.07
        parts.append(Part(octagon_scaled(ix * 0.92, iy * 0.92, 0.5, ft - 0.001, top_h), 'heap'))
        if h >= 0.7:
            parts.append(Part(octagon_scaled(ix * 0.5, iy * 0.45, 0.5, ft, top_h + 0.05, (-ix * 0.2, iy * 0.25)), 'heap'))
        gems = spec['gems'] if h >= 0.7 else []
        for i, ramp in enumerate(gems):
            gx = (ix * 0.45) * (1 if i % 2 == 0 else -0.6)
            gy = (iy * 0.55) * (i - 1)
            parts.append(Part(affine(octahedron(0.06), 1, 1, 1.25, (gx, gy, top_h + 0.03)), 'gem', ramp=ramp))
    return parts


def octagon_scaled(rx, ry, shrink, z0, z1, centre=(0.0, 0.0)):
    return affine(octagon_frustum(1.0, shrink, z0, z1), rx, ry, 1.0, (centre[0], centre[1], 0.0))


def rotate_xz(p, theta):
    c, s = math.cos(theta), math.sin(theta)
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


class Placed:
    """A part posed for one frame and facing: planes in world space, and the way back to its rest frame to paint it."""

    def __init__(self, part, spec, theta, facing):
        self.part, self.facing, self.theta = part, facing, theta if part.lid else 0.0
        self.hinge = (-(spec['dx'] + 1 / 16), 0.0, spec['zf'] + spec['hb'])
        planes = []
        for n, d in part.planes:
            p0 = tuple(c * d for c in n)
            if part.lid:                                   # the lid's rest frame has its base on z = 0: sit it on the body, then turn it on the hinge
                p0 = (p0[0], p0[1], p0[2] + spec['zf'] + spec['hb'])
                p0 = tuple(self.hinge[i] + c for i, c in enumerate(rotate_xz(tuple(p0[i] - self.hinge[i] for i in range(3)), self.theta)))
                n = rotate_xz(n, self.theta)
            if facing == 'SE':
                n, p0 = (n[1], n[0], n[2]), (p0[1], p0[0], p0[2])
            planes.append((n[0], n[1], n[2], n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]))
        self.planes = [(a, b, c, d, a + b + c) for a, b, c, d in planes]
        self.zlift = spec['zf'] + spec['hb']

    def hit(self, ox, oy):
        """(t, world normal) of the pixel ray (ox + t, oy + t, t), or None."""
        lo, hi = -1e9, 1e9
        face = None
        for a, b, c, d, nv in self.planes:
            na = a * ox + b * oy
            if abs(nv) < 1e-9:
                if na > d + 1e-9:
                    return None
                continue
            t = (d - na) / nv
            if nv > 0:
                if t < hi:
                    hi, face = t, (a, b, c)
            elif t > lo:
                lo = t
            if lo > hi + 1e-9:
                return None
        return (hi, face) if face is not None and lo <= hi + 1e-9 else None

    def to_rest(self, p, n):
        """A world point and normal back in the part's rest frame."""
        if self.facing == 'SE':
            p, n = (p[1], p[0], p[2]), (n[1], n[0], n[2])
        if self.part.lid:
            h = self.hinge
            p = tuple(h[i] + c for i, c in enumerate(rotate_xz(tuple(p[i] - h[i] for i in range(3)), -self.theta)))
            n = rotate_xz(n, -self.theta)
            p = (p[0], p[1], p[2] - self.zlift)
        return p, n


# --- paint ---------------------------------------------------------------------------------
def step_of(n):
    s = sum(n[i] * LIGHT[i] for i in range(3)) / math.sqrt(sum(c * c for c in LIGHT))
    return 0 if s > 0.78 else 1 if s > 0.08 else 2 if s > -0.5 else 3


def clamp(v):
    return max(0, min(3, v))


def wood(spec, face, u, v, step):
    """Planks: rows of `plank` pixels with a darker seam under each and a butt joint now and then. On the lid the planks run front to back."""
    ramp = spec['wood']
    ui, vi = int(math.floor(u * PX + 1e-6)), int(math.floor(v * PX + 1e-6))
    if face == 'lid':
        return ramp[clamp(step + 1)] if ui % 5 == 0 and step <= 1 else ramp[step]
    pl = spec['plank']
    if vi % pl == 0:
        return ramp[clamp(step + 1)]
    if (ui + (vi // pl) * 5) % 13 == 0:
        return ramp[clamp(step + 1)]
    return ramp[step]


def strap(spec, u, step):
    """The metal at u if a strap is there (a role), else None. Straps have a lit edge and a dark one."""
    for cy, w in spec['straps']:
        lo = cy - w / 32.0
        a = (u - lo) * PX
        if 0 <= a < w:
            ramp = spec['metal']
            k = int(a)
            s = step
            if k == 0:
                s = clamp(step - 1)
            elif k == w - 1 and w > 1:
                s = clamp(step + 1)
            return ramp[s], k
    return None


def metal(spec, step):
    return spec['metal'][step]


def paint_lining(spec, step, glow):
    ramp = spec['lining']
    s = clamp(step + 1 - int(glow * 1.6))
    return ramp[s]


def paint(spec, placed, p, n, glow):
    """The role of the point p (world) on a part of the chest, seen along its world normal n."""
    part = placed.part
    pr, nr = placed.to_rest(p, n)
    step = step_of(n)
    x, y, z = pr
    dx, dy, zf, hb = spec['dx'], spec['dy'], spec['zf'], spec['hb']
    zt = zf + hb
    kind = part.kind
    if kind == 'gem':
        ramp = part.info['ramp']
        hi = step == 0 and hashed(int(x * 40), int(y * 40), int(z * 40)) % 3 == 0
        return 'r' if hi and ramp[0] == 'o' else ('t' if hi else ramp[clamp(step - (1 if glow > 0.6 else 0))])
    if kind == 'heap':
        base = clamp(step - int(glow * 1.5))
        r = hashed(int(x * PX), int(y * PX), int(z * PX))
        s = clamp(base + (1 if r % 5 == 0 else 0) - (1 if r % 7 == 0 else 0))
        c = spec['coins'][s]
        if base == 0 and r % 6 == 0:
            return 't'
        return c
    if kind == 'foot':
        return metal(spec, clamp(step + (1 if nr[2] > 0.7 else 0)))
    if kind == 'post':
        # a corner post: metal with a bright edge down its lit side
        lit_edge = (abs(nr[0]) > 0.7 and abs(y) > dy - 1.5 / 16) or (abs(nr[1]) > 0.7 and abs(x) > dx - 1.5 / 16)
        return metal(spec, clamp(step - (1 if lit_edge else 0)))
    if kind == 'lock':
        lw = spec['lockw']
        pw = int(round(2 * lw))
        ui = int(math.floor((y + lw / 16) * PX + 1e-6))
        vi = int(math.floor((z - (zt - 6 / 16)) * PX + 1e-6))             # 0 at the bottom of the plate
        if nr[0] > 0.7:
            cx = (pw - 1) / 2
            if spec['lock'] == 'gem' and abs(ui - cx) + abs(vi - 2) <= 1.5:
                g = spec['lock_gem']
                return g[0] if vi >= 3 else (g[1] if abs(ui - cx) < 1 else g[2])
            if spec['lock'] != 'gem' and vi in (1, 2) and ui in (pw // 2 - 1, pw // 2):
                return 'x'
            s2 = step + (1 if (ui == pw - 1 or vi == 0) else 0) - (1 if (ui == 0 or vi == 4) else 0)
            return metal(spec, clamp(s2))
        return metal(spec, step)
    if kind == 'hasp':
        return metal(spec, step)
    if kind == 'crest':
        return metal(spec, clamp(step + (1 if abs(nr[2]) > 0.7 and int(math.floor(x * PX)) % 4 == 0 else 0)))
    if kind == 'lid':
        X = part.info['X']
        if nr[2] < -0.7:                                     # the underside, the inside of the lid
            return paint_lining(spec, step, glow)
        if abs(nr[1]) > 0.7:                                 # an end of the vault: wood, with a metal edge on the dearer chests
            edge = min(d - (a * x + b * y + c * z) for (a, b, c), d in part.planes if abs(b) < 0.5)
            if edge < 1.2 / 16 and (spec['band'] or edge < 0.6 / 16):
                return metal(spec, step)
            return wood(spec, 'side', x + X, z, step)
        s = strap(spec, y, step)
        if s:
            return s[0]
        if z < spec['lip'] and nr[0] > 0.7:                  # the front lip of the lid
            return metal(spec, clamp(step + (1 if z < 1 / 16 else 0))) if spec['band'] else wood(spec, 'front', y + 1, z, clamp(step + 1))
        return wood(spec, 'lid', y, x, step)
    # the walls of the body
    interior = (nr[0] > 0.7 and x < dx - 0.01) or (nr[1] > 0.7 and y < dy - 0.01) or (nr[2] > 0.7 and z < zt - 0.01)
    if interior:
        return paint_lining(spec, step, glow)
    if nr[2] > 0.7:                                          # the rim of the open walls
        return metal(spec, step) if spec['rim'] else wood(spec, 'top', x, y, step)
    face = 'front' if nr[0] > 0.7 else 'side'
    u = y if face == 'front' else x
    half = dy if face == 'front' else dx
    v = z - zf
    if spec['band'] and v < spec['band'] / 16:               # a band along the bottom edge
        return metal(spec, clamp(step + 1))
    shade = 1 if z > zt - 1.5 / 16 else 0                    # the lid's shadow along the top
    return wood(spec, face, u + half, v, clamp(step + shade))


# --- drawing -------------------------------------------------------------------------------
def render_chest(spec, facing, theta_deg, glow, rays, sparks, frame_no=0):
    theta = math.radians(theta_deg)
    placed = [Placed(p, spec, theta, facing) for p in build_parts(spec)]
    w, h = CELL_W, CELL_H
    ox, oy = ANCHOR
    grid = [['.'] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            a, b = (px + 0.5 - ox) / 16.0, (py + 0.5 - oy) / 8.0
            org = ((a + b) / 2, (b - a) / 2)
            best = None
            for pl in placed:
                got = pl.hit(org[0], org[1])
                if got and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], pl)
            if best is None:
                continue
            t, n, pl = best
            grid[py][px] = paint(spec, pl, (org[0] + t, org[1] + t, t), n, glow)
    mask = [[c != '.' for c in row] for row in grid]
    # the light that comes out of the open chest, behind it
    back = [['.'] * w for _ in range(h)]
    cx = ox
    cy = oy - (spec['zf'] + spec['hb']) * PX
    if rays:
        ramp = spec['glow']
        for k, ang in enumerate((-32, -16, 0, 16, 32)):
            ln = rays if abs(ang) < 20 else int(rays * 0.65)
            dxr, dyr = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
            for i in range(3, ln):
                if (i + k) % 2:
                    continue
                x, y = int(round(cx + dxr * i * 0.8)), int(round(cy - 3 + dyr * i))
                if 0 <= x < w and 0 <= y < h:
                    back[y][x] = ramp[0] if i < ln * 0.6 else ramp[1]
    out = [[grid[y][x] if mask[y][x] else back[y][x] for x in range(w)] for y in range(h)]
    # the outline round the chest
    for y in range(h):
        for x in range(w):
            if not mask[y][x] and any(0 <= x + dx_ < w and 0 <= y + dy_ < h and mask[y + dy_][x + dx_] for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'O'
    # sparkles over everything
    ramp = spec['spark']
    spots = [(-0.55, -0.2), (0.6, -0.5), (-0.1, -0.85), (0.3, -0.1), (-0.75, -0.7), (0.8, -0.8)]
    for i in range(min(sparks, len(spots))):
        sx, sy = spots[(i + frame_no) % len(spots)]
        x = int(round(cx + sx * 14))
        y = int(round(cy - 4 + sy * 16))
        big = i % 2 == 0
        pts = [(0, 0, ramp[0])] + ([(1, 0, ramp[1]), (-1, 0, ramp[1]), (0, 1, ramp[1]), (0, -1, ramp[1])] if big else [])
        for ddx, ddy, c in pts:
            if 0 <= x + ddx < w and 0 <= y + ddy < h and not mask[y + ddy][x + ddx]:
                out[y + ddy][x + ddx] = c
    return [''.join(r) for r in out]


def closed(rarity, facing):
    return render_chest(SPECS[rarity], facing, 0, 0.0, 0, 0)


def opening(rarity, facing):
    return [render_chest(SPECS[rarity], facing, a, g, r, s, i) for i, (a, g, r, s) in enumerate(FRAMES)]


# --- preview -------------------------------------------------------------------------------
def preview(path, scale=4):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}
    cols = 1 + len(FRAMES)
    rowh = CELL_H * scale + 14
    sheet = Image.new('RGB', (cols * CELL_W * scale, rowh * len(RARITIES) * 2), (50, 44, 84))
    draw = ImageDraw.Draw(sheet)
    r = 0
    for rarity in RARITIES:
        for facing in ('NE', 'SE'):
            frames = [closed(rarity, facing)] + opening(rarity, facing)
            for i, rows in enumerate(frames):
                ox, oy = i * CELL_W * scale, r * rowh + 14
                draw.text((ox + 3, oy - 12), f'{SPECS[rarity]["label"]} {facing} ' + ('closed' if i == 0 else f'open {i}'), fill=(235, 238, 245))
                for y, line in enumerate(rows):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            draw.rectangle([ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1], fill=rgb[ch])
            r += 1
    sheet.save(path)


# --- the assets ----------------------------------------------------------------------------
CATEGORY = 'Chests'
FOLDER = 'chests'


def build_assets():
    """Twelve assets in one folder: for each rarity and facing, the shut chest (chest-RARITY-ne, one frame) and the opening (chest-RARITY-ne-open, 8 frames)."""
    make = family(CATEGORY, CELL_W, CELL_H, ANCHOR, folder=FOLDER)
    assets = []
    for rarity in RARITIES:
        label = f'{SPECS[rarity]["label"]} chest'
        for facing in ('NE', 'SE'):
            f = facing.lower()
            assets.append(make(f'chest-{rarity}-{f}', f'{label} - {facing}, shut', 'still', [closed(rarity, facing)],
                               chest={'rarity': rarity, 'facing': facing, 'state': 'shut'}))
            assets.append(make(f'chest-{rarity}-{f}-open', f'{label} - {facing}, opening (animation)', 'animation', opening(rarity, facing), fps=FPS,
                               chest={'rarity': rarity, 'facing': facing, 'state': 'opening', 'plays': 'once, then holds the last frame'}))
    return assets


def write_package(folder):
    """Beside the sheets: chests.json, how a game uses them in numbers (README.md says it in words)."""
    write_json(folder, 'chests.json', 'The chest sheets in this folder. See README.md beside this file for the whole story.', {
        'cell': [CELL_W, CELL_H], 'anchor': {'x': ANCHOR[0], 'y': ANCHOR[1]}, 'fps': FPS, 'openingFrames': len(FRAMES),
        'rarities': {r: {'label': SPECS[r]['label'],
                         'shut': {f: f'chest-{r}-{f.lower()}.png' for f in ('NE', 'SE')},
                         'opening': {f: f'chest-{r}-{f.lower()}-open.png' for f in ('NE', 'SE')},
                         'openingPlays': 'once, then hold the last frame'} for r in RARITIES},
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='write every chest, enlarged, here')
    parser.add_argument('--scale', type=int, default=4)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, args.scale)
        print(f'the chests, enlarged -> {args.preview}')


if __name__ == '__main__':
    main()
