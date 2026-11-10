#!/usr/bin/env python3
"""The All Tree: the victory screen's display piece, a massive ancient tree being corrupted by the mushrooms. Two assets, `all-tree` (the 12-frame loop) and `all-tree-still`, in the Victory Screen category and the `all-tree` folder.

One flat image, ray-cast from a small 3D model in exactly the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level), in the shared colour roles, with the one-pixel outline.

    base      TEN by TEN tiles: a 320 x 160 pixel diamond on the ground, anchored at its middle, ANCHOR = (192, 336)
    height    it rises 20 levels (320 pixels) and more: the image is CROPPED by its top edge, so the trunk and the great boughs go on up out of view
    the tree  an ancient oak at heart: a gnarled trunk with ridged bark, a hollow, knots, buttress roots gripping the ground across the whole base, thick low boughs, moss
    the rot   bracket fungi in bands up the trunk (thickest at the roots, thinning higher), toadstools round the base, teal and purple vines winding up it with thorns, glowing eyes in a few knots,
              spore motes in the air, and corrupted ground (teal turf, plum soil, dark teal pools) under it

    python3 tools/make_all_tree.py --preview previews/all-tree.png        the image over its footprint, plus -base and -top crops enlarged
    python3 tools/make_all_tree.py --png out.png                          just the flat 384 x 448 picture, transparent
    python3 tools/make_all_tree.py --animate previews/all-tree-anim.png --gif previews/all-tree-anim.gif      the 12-frame loop: shimmer and dripping spores
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from make_fungi import hashed, step_of  # noqa: E402

W, H = 384, 448
ANCHOR = (192, 336)              # the middle of the base on the ground
AX, AY = ANCHOR
BASE_W = 384                     # the cell the first (narrow) pictures are drawn in; the wide ones add width on both sides of the same drawing


def set_canvas(width):
    """Make the canvas `width` pixels wide, with the anchor at its middle (the height, the anchor's row and the model stay the same)."""
    global W, ANCHOR, AX
    W, ANCHOR, AX = width, (width // 2, AY), width // 2


class wide_canvas:
    """`with wide_canvas(1024):` draws everything on a wider canvas and puts the narrow one back afterwards."""
    def __init__(self, width):
        self.width = width

    def __enter__(self):
        self.old = W
        set_canvas(self.width)

    def __exit__(self, *exc):
        set_canvas(self.old)


def off():
    """How far a wide canvas shifts the narrow picture right: zero for the narrow one. Things placed by hash keep their place in the middle 384 columns."""
    return AX - BASE_W // 2
FOOT = 10                        # tiles each way

# colour ramps, light to dark
BARK = ('e', 'g', 'w', 'x')
MOSS = ('A', 'B', 'B', 's')
ROT = ('u', 'w', 'x', 'x')
LICHEN = ('p', 'l', 'l', 'k')
CREAM = ('t', 'C', 'c', 'e')
PINK = ('j', 'i', 'h', 'u')
TEAL = ('r', 'q', 's', 'k')
VIOLET = ('v', 'f', 'u', 'w')
CORAL = ('c', 'e', 'g', 'w')
VINE_TEAL = ('q', 's', 'D', 'x')
VINE_PURPLE = ('f', 'u', 'w', 'x')
LEAF = ('q', 's', 'D', 'x')
GLOW = ('r', 'o', 'o', 'q')
SPOT = ('t', 't', 'C', 'c')
BONE = ('t', 'C', 'c', 'e')
SHELF_RAMPS = (TEAL, VIOLET, BONE, PINK, TEAL, VIOLET)


# --- the solids, vectorised: a hit is, for every pixel of a box, the ray parameter t (or -inf) and the surface normal -----------------------------
class Solid:
    spots = ()
    spotramp = None
    glow = False
    mark = None
    group = None

    def __init__(self, mat, mark=None, group=None, **extra):
        self.mat, self.mark = mat, mark
        self.group = group if group is not None else id(self)
        self.__dict__.update(extra)


class Ell(Solid):
    """A round body, kept between heights lo and hi."""

    def __init__(self, mat, c, radii, lo=-1e9, hi=1e9, **kw):
        super().__init__(mat, **kw)
        self.c, self.r, self.lo, self.hi = c, radii, lo, hi

    def box(self):
        (cx, cy, ch), (rx, ry, rh) = self.c, self.r
        sx, sy = AX + 16 * (cx - cy), AY + 8 * (cx + cy) - 16 * ch
        return sx - 16 * (rx + ry) - 2, sx + 16 * (rx + ry) + 2, sy - 8 * (rx + ry) - 16 * rh - 2, sy + 8 * (rx + ry) + 16 * rh + 2

    def hit(self, ox, oy):
        (cx, cy, ch), (rx, ry, rh) = self.c, self.r
        a, b, d = ox - cx, oy - cy, -ch
        A = 1 / rx ** 2 + 1 / ry ** 2 + 1 / rh ** 2
        B = 2 * (a / rx ** 2 + b / ry ** 2 + d / rh ** 2)
        C = a * a / rx ** 2 + b * b / ry ** 2 + d * d / rh ** 2 - 1
        disc = B * B - 4 * A * C
        valid = disc >= 0
        sq = np.sqrt(np.where(valid, disc, 0))
        lo = np.maximum((-B - sq) / (2 * A), self.lo)
        up = (-B + sq) / (2 * A)
        top = self.hi < up
        up = np.where(top, self.hi, up)
        valid &= lo <= up
        nx, ny, nz = (a + up) / rx ** 2, (b + up) / ry ** 2, (up - ch) / rh ** 2
        m = np.sqrt(nx * nx + ny * ny + nz * nz)
        m = np.where(m < 1e-12, 1, m)
        nx, ny, nz = np.where(top, 0, nx / m), np.where(top, 0, ny / m), np.where(top, 1, nz / m)
        return np.where(valid, up, -np.inf), nx, ny, nz


class Frus(Solid):
    """A tapering upright cylinder from height h0 to h1, radius r0 at the bottom and r1 at the top."""

    def __init__(self, mat, c, h0, h1, r0, r1, **kw):
        super().__init__(mat, **kw)
        self.c, self.h0, self.h1, self.r0, self.r1 = c, h0, h1, r0, r1
        self.k = (r1 - r0) / (h1 - h0)

    def box(self):
        cx, cy = self.c
        rm = max(self.r0, self.r1)
        sx, sy = AX + 16 * (cx - cy), AY + 8 * (cx + cy)
        return sx - 23 * rm - 2, sx + 23 * rm + 2, sy - 16 * self.h1 - 12 * rm - 2, sy - 16 * self.h0 + 12 * rm + 2

    def hit(self, ox, oy):
        a, b = ox - self.c[0], oy - self.c[1]
        k = self.k
        m = self.r0 - k * self.h0
        A, B, C = 2 - k * k, 2 * (a + b) - 2 * m * k, a * a + b * b - m * m
        disc = B * B - 4 * A * C
        valid = disc >= 0
        sq = np.sqrt(np.where(valid, disc, 0))
        lo = np.maximum((-B - sq) / (2 * A), self.h0)
        up = (-B + sq) / (2 * A)
        top = self.h1 < up
        up = np.where(top, self.h1, up)
        valid &= lo <= up
        x, y = a + up, b + up
        r = np.hypot(x, y)
        r = np.where(r < 1e-9, 1, r)
        nx, ny, nz = x / r, y / r, np.full_like(r, -k)
        m2 = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = np.where(top, 0, nx / m2), np.where(top, 0, ny / m2), np.where(top, 1, nz / m2)
        return np.where(valid, up, -np.inf), nx, ny, nz


def ground_limit(theta):
    return 4.78 + 0.28 * math.sin(5 * theta + 0.7) + 0.22 * math.cos(9 * theta + 1.0)


class Ground(Solid):
    """The ground patch under the tree: a ragged rounded square on the tile grid, behind everything."""

    def __init__(self):
        super().__init__(('s', 's', 'D', 'D'), mark='ground', group='ground')

    def box(self):
        return AX - 16 * 2 * 5.4, AX + 16 * 2 * 5.4, AY - 8 * 2 * 5.4, AY + 8 * 2 * 5.4

    def hit(self, ox, oy):
        rho = (np.abs(ox) ** 4 + np.abs(oy) ** 4) ** 0.25
        th = np.arctan2(oy, ox)
        lim = 4.78 + 0.28 * np.sin(5 * th + 0.7) + 0.22 * np.cos(9 * th + 1.0)
        ok = rho <= lim
        zero = np.zeros_like(ox)
        return np.where(ok, -0.01, -np.inf), zero, zero, zero + 1


# --- the model ---------------------------------------------------------------------------------------------------
def trunk_r(h):
    bump = sum(w * math.exp(-((h - c) / s) ** 2) for c, w, s in ((3.4, 0.28, 0.7), (7.6, 0.34, 0.8), (12.6, 0.3, 0.9), (17.8, 0.22, 1.0)))
    return 2.45 * (1 - 0.006 * h) + 1.6 * math.exp(-h / 1.9) + 0.1 * math.sin(h * 1.7) + 0.08 * math.sin(h * 0.6 + 1) + bump


def trunk_c(h):
    return 0.32 * math.sin(h * 0.31) + 0.12 * math.sin(h * 0.9), 0.28 * math.sin(h * 0.27 + 2) + 0.1 * math.cos(h * 0.8)


def on_trunk(theta_deg, h, out=0.0):
    """A point on the trunk's surface at an angle (45 is straight at the camera) and a height, `out` further out."""
    cx, cy = trunk_c(h)
    th = math.radians(theta_deg)
    r = trunk_r(h) + out
    return cx + r * math.cos(th), cy + r * math.sin(th)


TRUNK_TOP = 26


def trunk():
    out = []
    n = int(TRUNK_TOP / 0.5)
    for i in range(n):
        h0, h1 = i * 0.5, (i + 1) * 0.5
        cx, cy = trunk_c((h0 + h1) / 2)
        out.append(Frus(BARK, (cx, cy), h0, h1, trunk_r(h0), trunk_r(h1), mark='trunk', group='trunk'))
    return out


def chain(pts, radius, mat, mark='bark', group=None, flat=0.85):
    """Spheres along a path of (x, y, h) points, one piece, so there are no seams."""
    group = group if group is not None else object()
    return [Ell(mat, (x, y, h), (r, r, r * flat), mark=mark, group=group) for (x, y, h), r in zip(pts, radius)]


def root(phi_deg, reach, lift, r0, wob=0.3, d0=1.9, group=None):
    """A buttress root: stands out of the trunk's flank and sinks into the ground as it runs out."""
    phi = math.radians(phi_deg)
    n = max(8, int((reach) / 0.2))
    pts, rad = [], []
    for i in range(n + 1):
        s = i / n
        d = d0 + reach * s
        w = wob * math.sin(s * 5 + phi * 3) * s
        x, y = d * math.cos(phi) - w * math.sin(phi), d * math.sin(phi) + w * math.cos(phi)
        rr = r0 * (1 - s) ** 0.85 + 0.17
        pts.append((x, y, rr * 0.7 + lift * (1 - s) ** 2.2))
        rad.append(rr)
    return chain(pts, rad, BARK, 'root', group, flat=0.62)


def branch(p0, phi_deg, run, rise, r0, r1, curve=0.0, droop=0.0, group=None, step=0.22):
    """A bough from p0 going out along phi for `run` and up for `rise`, tapering from r0 to r1, optionally arching (curve) or sagging at the end (droop)."""
    phi = math.radians(phi_deg)
    L = math.hypot(run, rise)
    n = max(6, int(L / step))
    pts, rad = [], []
    for i in range(n + 1):
        s = i / n
        d = run * s
        sway = curve * math.sin(s * math.pi) * run * 0.12
        x = p0[0] + d * math.cos(phi) - sway * math.sin(phi)
        y = p0[1] + d * math.sin(phi) + sway * math.cos(phi)
        h = p0[2] + rise * s ** 1.15 - droop * s ** 3
        pts.append((x, y, h))
        rad.append((r0 + (r1 - r0) * s ** 0.8) * (1 + 0.12 * math.sin(i * 0.55 + r0 * 9) + 0.07 * math.sin(i * 1.3)))
    return chain(pts, rad, BARK, 'bark', group), pts


def point_on(pts, s):
    return pts[min(len(pts) - 1, int(s * (len(pts) - 1)))]


def shelf(theta, h, size, ramp, tilt=0.0):
    """A bracket fungus on the trunk: a flat half disc standing out of it."""
    cx, cy = on_trunk(theta, h, 0.12 * size)
    rx, ry = (0.62 * size, 0.46 * size) if abs(math.sin(math.radians(theta))) > abs(math.cos(math.radians(theta))) else (0.46 * size, 0.62 * size)
    return Ell(ramp, (cx, cy, h), (rx, ry, 0.15 * size + 0.04), mark='shelf', rim=CREAM)


def toadstool(x, y, stem_h, stem_r, cap_r, cap_h, cap, spots=True, base=0.0):
    stem = Frus(CREAM, (x, y), base, base + stem_h, stem_r * 1.35, stem_r * 0.85, mark='speckle', group=('mush', x, y))
    top = base + stem_h
    sp = ()
    if spots:
        sp = ((0.0, 0.0, cap_r * 0.2), (cap_r * 0.5, cap_r * 0.18, cap_r * 0.15), (-cap_r * 0.4, cap_r * 0.4, cap_r * 0.15), (-cap_r * 0.35, -cap_r * 0.45, cap_r * 0.14), (cap_r * 0.2, -cap_r * 0.62, cap_r * 0.13))
    capb = Ell(cap, (x, y, top), (cap_r, cap_r, cap_h), lo=top - 0.05, mark='cap', group=('mush', x, y), spots=sp, spotramp=SPOT)
    return [stem, capb]


def vine(theta0, turns, h0, h1, ramp, group, thorns=True, leaf_ramp=LEAF):
    out = []
    h = h0
    k = 0
    while h < h1:
        th = theta0 + turns * (h - h0) * 360 / 8.0 + 14 * math.sin(h * 0.9)
        x, y = on_trunk(th, h, 0.1)
        out.append(Ell(ramp, (x, y, h), (0.13, 0.13, 0.13), mark='vine', group=group))
        if thorns and k % 9 == 4:
            tx, ty = on_trunk(th, h, 0.32)
            out.append(Ell(CREAM, (tx, ty, h + 0.05), (0.07, 0.07, 0.09), mark='thorn', group=group))
        if k % 19 == 8:
            lx, ly = on_trunk(th + 10, h, 0.36)
            out.append(Ell(leaf_ramp, (lx, ly, h), (0.34, 0.34, 0.1), mark='leaf', group=(group, k)))
        h += 0.11
        k += 1
    return out


def hanging(p, length, ramp, group, sway=0.4):
    out = []
    n = int(length / 0.14)
    for i in range(n + 1):
        s = i / n
        out.append(Ell(ramp, (p[0] + sway * math.sin(s * 3 + p[0]) * s, p[1] + sway * 0.6 * math.cos(s * 2.4) * s, p[2] - length * s), (0.1, 0.1, 0.12), mark='vine', group=group))
    out.append(Ell(LEAF, (p[0] + sway * math.sin(3 + p[0]), p[1] + sway * 0.6 * math.cos(2.4), p[2] - length - 0.05), (0.14, 0.14, 0.26), mark='leaf', group=(group, 'tip')))
    return out


def knot(theta, h, ramp_eye=GLOW):
    """A swollen knot in the bark with two glowing eyes in it."""
    x, y = on_trunk(theta, h, 0.1)
    th = math.radians(theta)
    out = [Ell(BARK, (x, y, h), (0.95, 0.95, 0.7), mark='knot', group=('knot', theta, h))]
    fx, fy = on_trunk(theta, h, 0.7)
    tx, ty = -math.sin(th), math.cos(th)
    for s in (-1, 1):
        out.append(Ell(ramp_eye, (fx + s * 0.34 * tx, fy + s * 0.34 * ty, h + 0.08), (0.2, 0.2, 0.24), glow=True, mark='eye', group=('eye', theta, h, s)))
    return out


def build():
    bodies = [Ground()]
    # the roots: a ring of buttress roots across the whole base (the far ones show at the edges)
    roots = ((-80, 3.4, 1.3, 1.7), (-40, 3.6, 1.1, 1.6), (-5, 3.4, 1.4, 1.7), (28, 3.5, 1.2, 1.6), (62, 3.4, 1.3, 1.8), (96, 3.5, 1.2, 1.7), (132, 3.6, 1.3, 1.7), (168, 3.4, 1.1, 1.6),
             (205, 3.5, 1.3, 1.7), (243, 3.4, 1.2, 1.6), (-115, 3.5, 1.2, 1.6))
    for i, (phi, reach, lift, r0) in enumerate(roots):
        bodies += root(phi, reach, lift, r0, wob=0.45 if i % 2 else -0.4, d0=1.3, group=('root', i))
    # thin roots gripping the ground beyond them
    for i, (phi, reach) in enumerate(((10, 1.5), (47, 1.4), (80, 1.5), (115, 1.4), (150, 1.5), (-25, 1.4), (-60, 1.3), (185, 1.4))):
        bodies += root(phi, reach, 0.1, 0.4, wob=0.3 if i % 2 else -0.25, d0=3.6, group=('root2', i))
    bodies += trunk()
    # the great boughs at the top, spreading out and up out of the picture
    tops = ((-45, 12.0, 10.0, 1.7, 0.4, 16.0, 1.5), (135, 12.0, 9.0, 1.7, 0.4, 15.0, -1.5), (-135, 8.0, 10.0, 1.4, 0.4, 18.0, 0), (-90, 8.0, 10.0, 1.3, 0.35, 14.5, 1.0), (180, 9.0, 9.0, 1.3, 0.35, 19.0, -1.0),
            (-12, 9.0, 9.0, 0.95, 0.35, 19.0, 1.0), (90, 9.0, 7.0, 0.95, 0.35, 13.5, -1.0), (-160, 9.0, 10.0, 0.95, 0.35, 14.5, 0.5), (50, 7.0, 7.0, 0.9, 0.35, 20.5, 0), (-60, 7.0, 10.0, 0.85, 0.3, 21.5, 0))
    for i, (phi, run, rise, r0, r1, h0, curve) in enumerate(tops):
        cx, cy = trunk_c(h0)
        start = (cx + 0.6 * math.cos(math.radians(phi)), cy + 0.6 * math.sin(math.radians(phi)), h0)
        b, pts = branch(start, phi, run, rise, r0, r1, curve=curve, group=('top', i))
        bodies += b
        for j, (s, dphi, rr, rn, ri) in enumerate(((0.45, 28, 0.55, 5.0, 4.0), (0.65, -30, 0.45, 4.5, 3.5))):
            sx, sy, sh = point_on(pts, s)
            sb, spts = branch((sx, sy, sh), phi + dphi, rn, ri, rr, 0.22, group=('top', i, j))
            bodies += sb
    # the thick low boughs
    lows = ((-45, 8.5, 5.0, 1.7, 0.3, 8.0, 0.8, 0.0), (135, 8.0, 5.6, 1.7, 0.3, 9.2, -0.8, 0.0), (-5, 5.5, 2.4, 1.3, 0.28, 6.2, 0.4, 0.8), (100, 5.5, 2.6, 1.3, 0.28, 7.0, -0.4, 1.0), (-100, 7.0, 4.0, 1.2, 0.28, 11.0, 0.6, 0.0))
    low_pts = []
    for i, (phi, run, rise, r0, r1, h0, curve, droop) in enumerate(lows):
        cx, cy = trunk_c(h0)
        start = (cx + 1.0 * math.cos(math.radians(phi)), cy + 1.0 * math.sin(math.radians(phi)), h0)
        b, pts = branch(start, phi, run, rise, r0, r1, curve=curve, droop=droop, group=('low', i))
        bodies += b
        low_pts.append(pts)
        sx, sy, sh = point_on(pts, 0.55)
        sb, spts = branch((sx, sy, sh), phi + (35 if i % 2 else -35), 4.2, 1.6, 0.42, 0.2, droop=0.6, group=('low', i, 's'))
        bodies += sb
    # knots with eyes
    for theta, h in ((38, 6.0), (72, 10.2), (14, 13.4), (55, 16.6)):
        bodies += knot(theta, h)
    # two eyes watching from the dark of the hollow
    for sgn in (-1, 1):
        ex, ey = on_trunk(45 + sgn * 9, 4.1, -0.05)
        bodies.append(Ell(GLOW, (ex, ey, 4.1), (0.22, 0.22, 0.3), glow=True, mark='eye', group=('hollow-eye', sgn)))
    # bracket fungi up the trunk: thick at the roots, thinning
    shelves = ((2, 0.9, 1.0), (96, 1.4, 1.2), (-18, 1.5, 1.0), (118, 2.3, 0.9), (104, 4.4, 0.9), (-5, 4.6, 0.85), (126, 5.6, 0.75),
               (62, 7.0, 1.0), (16, 8.1, 0.9), (96, 7.8, 0.8), (40, 9.4, 1.05), (-8, 10.6, 0.8), (78, 11.5, 0.8), (118, 10.2, 0.7), (30, 14.8, 0.9), (82, 15.8, 0.7), (4, 18.4, 0.8), (58, 19.8, 0.7), (104, 13.6, 0.6), (70, 8.6, 1.2), (125, 12.3, 0.9), (20, 12.2, 1.0), (92, 17.2, 0.9), (-20, 15.6, 0.8), (50, 5.6, 0.95), (68, 21.5, 0.8), (115, 20.4, 0.7))
    for i, (theta, h, size) in enumerate(shelves):
        bodies.append(shelf(theta, h, size, SHELF_RAMPS[i % len(SHELF_RAMPS)]))
        if i % 3 == 0:
            bodies.append(shelf(theta + 8, h - 0.5 * size, size * 0.7, SHELF_RAMPS[(i + 2) % len(SHELF_RAMPS)]))
    # shelves out along the low boughs
    for pts in low_pts[:2]:
        for k, (s, ramp) in enumerate(((0.35, PINK), (0.62, TEAL), (0.85, VIOLET))):
            x, y, h = point_on(pts, s)
            bodies.append(Ell(ramp, (x, y, h + 0.16), (0.55, 0.45, 0.13), mark='shelf', rim=CREAM))
    for pts in low_pts[:4]:
        for s_, ramp, size in ((0.3, PINK, 1.0), (0.5, TEAL, 0.8), (0.72, VIOLET, 0.9)):
            x, y, h = point_on(pts, s_)
            bodies += toadstool(x, y, 0.55 * size, 0.1 * size, 0.38 * size, 0.28 * size, ramp, base=h + 0.2)
    # toadstools round the base and on the roots
    for i, (x, y, sh, sr, cr, ch, cap) in enumerate(((3.6, 3.0, 1.1, 0.16, 0.62, 0.5, PINK), (2.4, 4.2, 0.7, 0.13, 0.45, 0.36, TEAL), (4.3, 1.4, 0.8, 0.14, 0.5, 0.4, VIOLET), (1.2, 4.5, 1.4, 0.17, 0.7, 0.55, TEAL),
                                                      (-1.0, 4.3, 0.6, 0.11, 0.38, 0.3, PINK), (4.5, -0.6, 0.55, 0.11, 0.4, 0.32, TEAL), (-3.8, 2.4, 0.9, 0.13, 0.5, 0.4, PINK), (-2.8, 3.9, 0.5, 0.1, 0.34, 0.28, VIOLET),
                                                      (3.2, -3.4, 0.7, 0.12, 0.45, 0.34, TEAL), (-3.9, -2.2, 0.8, 0.13, 0.48, 0.38, VIOLET), (0.2, 3.8, 0.4, 0.09, 0.3, 0.24, PINK), (4.2, 3.9, 0.5, 0.1, 0.34, 0.26, VIOLET))):
        bodies += toadstool(x, y, sh, sr, cr, ch, cap)
    # vines winding up, and hanging from the boughs
    bodies += vine(20, 1.0, 0.4, 25.0, VINE_TEAL, 'vine1')
    bodies += vine(150, 0.85, 0.8, 25.0, VINE_PURPLE, 'vine2')
    for i, (pts, s, ln, ramp) in enumerate(((low_pts[0], 0.5, 4.2, VINE_TEAL), (low_pts[0], 0.8, 3.0, VINE_PURPLE), (low_pts[1], 0.45, 4.6, VINE_PURPLE), (low_pts[1], 0.75, 3.4, VINE_TEAL),
                                           (low_pts[2], 0.7, 2.6, VINE_TEAL), (low_pts[3], 0.7, 3.0, VINE_PURPLE))):
        x, y, h = point_on(pts, s)
        bodies += hanging((x, y, h - 0.1), ln, ramp, ('hang', i))
    return bodies


# --- drawing ---------------------------------------------------------------------------------------------------
def noise(x, y, z=0.0):
    return math.sin(x * 1.7 + z) * math.sin(y * 1.9 + 1.0) + 0.6 * math.sin(z * 2.3 + x * 0.8 - y * 0.6)


def colour(body, p, n, step, px, py):
    px = px - off()                  # textures are laid out from the narrow picture's left edge, so a wide canvas draws the same bark in the same places
    m = body.mark
    r = body.mat
    if body.glow:
        return r[0 if step < 2 else 1]
    if m == 'ground':
        return ground_colour(p, px, py)
    if m == 'trunk':
        return trunk_colour(body, p, n, step, px, py)
    if m in ('bark', 'root', 'knot'):
        s = step
        if s < 3 and hashed(px, py, 4) % 13 == 0:
            s += 1
        if n[2] > 0.5 and p[2] < 14 and noise(p[0] * 2.4, p[1] * 2.4, p[2] * 1.3) > 0.55:
            return MOSS[min(3, s)]
        if hashed(px // 2, py // 2, 12) % 61 == 0 and s < 3:
            return LICHEN[min(3, s)]
        if m == 'root' and noise(p[0] * 0.8, p[1] * 0.8, 7) > 0.9:
            return ROT[min(3, s)]
        return r[s]
    if m == 'shelf':
        cx, cy = body.c[0], body.c[1]
        rr = math.hypot((p[0] - cx) / body.r[0], (p[1] - cy) / body.r[1])
        if rr > 0.86 and step < 3:
            return body.rim[min(3, step)]
        if int(rr * 4.0) % 2 == 1 and step < 3:
            return r[min(3, step + 1)]
        return r[step]
    if m == 'cap':
        c = (p[0] - body.c[0], p[1] - body.c[1])
        if n[2] > 0.12:
            for dx, dy, rho in body.spots:
                if (c[0] - dx) ** 2 + (c[1] - dy) ** 2 < rho * rho:
                    return body.spotramp[step]
        return r[step]
    if m == 'speckle':
        if step < 3 and hashed(px, py, 1) % 9 == 0:
            return r[min(3, step + 1)]
        return r[step]
    if m == 'vine':
        return r[step]
    return r[step]


def trunk_colour(body, p, n, step, px, py):
    r = body.mat
    dx, dy = p[0] - body.c[0], p[1] - body.c[1]
    ang = math.atan2(dy, dx)
    h = p[2]
    R = body.r0
    u = ang * R
    da = (ang - math.radians(45) + math.pi) % (2 * math.pi) - math.pi
    hx, hy = da * R / 1.65, (h - 3.6) / 2.5
    q = hx * hx + hy * hy
    if q < 1.0:                                       # the hollow
        if hy > 0.55 and hx * hx + (hy - 0.55) ** 2 > 0.75:
            return 'w'
        if q > 0.72:
            return 'w' if step < 3 else 'x'
        if h < 1.7 and q < 0.6:
            return 'D' if hashed(px, py, 5) % 3 else 's'
        return 'x'
    if q < 1.42:                                      # its lip
        if step < 2 and hy > -0.2:
            return 'g'
        return 'w' if step < 3 else 'x'
    s = step
    ridge = math.sin(u * 2.4 + 1.3 * math.sin(h * 0.5 + ang * 2.0)) + 0.5 * math.sin(u * 5.1 + h * 0.3)
    if ridge < -0.85:
        s = min(3, s + 1)
    elif ridge > 1.0:
        s = max(0, s - 1)
    elif hashed(px, py, 6) % 14 == 0:
        s = min(3, s + 1)
    tongue = 1.8 + 3.4 * (0.5 + 0.5 * math.sin(u * 2.9 + 1.0)) * (0.5 + 0.5 * math.sin(u * 1.3 + 4.0))
    if h < tongue and hashed(px, py, 13) % 7 != 0:
        return MOSS[min(3, s)]
    if 5 < h < 22 and noise(u * 1.5, h * 0.8, 2.0) < -1.0:
        return ROT[min(3, s)]
    if hashed(px // 2, py // 2, 14) % 70 == 0 and s < 3:
        return LICHEN[min(3, s)]
    if s == 0 and ridge > 0.55:
        return 'c'
    if h > 3 and abs(math.sin(u * 3.7 + h * 0.15 + math.sin(h * 0.4))) > 0.9993 and h > 5 and n[2] < 0.5:
        return 'r' if s < 2 else 'q'
    if ridge < -1.3 and h > 4:
        return 'q' if s < 3 else 's'                  # a glowing crack
    return r[s]


def ground_colour(p, px, py):
    x, y = p[0], p[1]
    rho = (abs(x) ** 4 + abs(y) ** 4) ** 0.25
    th = math.atan2(y, x)
    lim = ground_limit(th)
    if rho > lim - 0.5 and (px + py) % 2 == 0:
        return None
    r = math.hypot(x, y)
    v = noise(x, y, 1.0)
    soil = r < 3.3 + 0.5 * math.sin(th * 3)
    if soil:
        return 'g' if (v > 0.1 and hashed(px, py, 7) % 4) else 'w'
    if v < -0.8:
        return 'D' if hashed(px, py, 8) % 5 else 's'  # a dark pool
    if v > 0.55:
        return 'q' if hashed(px, py, 9) % 3 == 0 else 's'
    return 's' if hashed(px, py, 10) % 6 else 'D'


DARKER = {'A': 'D', 'B': 'D', 's': 'D', 'q': 's', 'r': 's', 't': 'g', 'C': 'g', 'c': 'g', 'v': 'u', 'j': 'h', 'i': 'h', 'p': 'k', 'l': 'k', 'o': 's'}


def render(bodies=None, with_grid=False, still_motes=True):
    """The picture as role rows. `with_grid` also hands back, for every pixel, (colour, group, depth, body) or None; `still_motes=False` leaves the static spore motes out (the animation twinkles its own)."""
    bodies = bodies or build()
    a = (np.arange(W) + 0.5 - AX) / 16.0
    b = (np.arange(H) + 0.5 - AY) / 8.0
    A, B = np.meshgrid(a, b)
    OX, OY = (A + B) / 2, (B - A) / 2
    depth = np.full((H, W), -np.inf)
    idx = np.full((H, W), -1, dtype=np.int32)
    NX, NY, NZ = np.zeros((H, W)), np.zeros((H, W)), np.zeros((H, W))
    with np.errstate(all='ignore'):
        for i, body in enumerate(bodies):
            x0, x1, y0, y1 = body.box()
            x0, y0, x1, y1 = max(0, int(math.floor(x0))), max(0, int(math.floor(y0))), min(W, int(math.ceil(x1))), min(H, int(math.ceil(y1)))
            if x0 >= x1 or y0 >= y1:
                continue
            t, nx, ny, nz = body.hit(OX[y0:y1, x0:x1], OY[y0:y1, x0:x1])
            sub = depth[y0:y1, x0:x1]
            better = t > sub
            if not better.any():
                continue
            sub[better] = t[better]
            idx[y0:y1, x0:x1][better] = i
            NX[y0:y1, x0:x1][better], NY[y0:y1, x0:x1][better], NZ[y0:y1, x0:x1][better] = nx[better], ny[better], nz[better]
    grid = [[None] * W for _ in range(H)]
    ys, xs = np.nonzero(idx >= 0)
    for y, x in zip(ys.tolist(), xs.tolist()):
        body = bodies[idx[y, x]]
        t = depth[y, x]
        p = (OX[y, x] + t, OY[y, x] + t, t)
        nrm = (NX[y, x], NY[y, x], NZ[y, x])
        c = colour(body, p, nrm, step_of(nrm), x, y)
        if c is not None:
            grid[y][x] = (c, body.group, t, body)
    out = [[(c[0] if c else '.') for c in row] for row in grid]
    for y in range(H):
        for x in range(W):
            cell = grid[y][x]
            if not cell or cell[1] == 'ground':
                continue
            for nx_, ny_ in ((x - 1, y), (x, y - 1)):
                other = grid[ny_][nx_] if 0 <= nx_ < W and 0 <= ny_ < H else None
                if other and other[1] != cell[1] and other[1] != 'ground' and other[2] - cell[2] > 0.3:
                    out[y][x] = DARKER.get(out[y][x], 'x') if out[y][x] not in 'xDwk' else out[y][x]
    final = [row[:] for row in out]
    for y in range(H):
        for x in range(W):
            if grid[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx_, ny_ = x + dx, y + dy
                    if 0 <= nx_ < W and 0 <= ny_ < H and grid[ny_][nx_] and grid[ny_][nx_][1] != 'ground':
                        final[y][x] = 'O'
                        break
    if still_motes:
        motes(final, grid)
    rows = [''.join(r) for r in final]
    return (rows, grid) if with_grid else rows


def mote_spots(final):
    """Where the spore motes float: single glowing pixels on clear ground-and-sky, more of them low. Each is (x, y, colour, has a glow round it)."""
    out = []
    for i in range(70):
        x = off() + 10 + hashed(i, 1, 11) % (BASE_W - 20)
        y = 60 + (hashed(i, 2, 11) % 330)
        if hashed(i, 3, 11) % 3 == 0:
            y = 200 + hashed(i, 4, 11) % 200
        if any(0 <= x + dx < W and 0 <= y + dy < H and final[y + dy][x + dx] != '.' for dx in range(-2, 3) for dy in range(-2, 3)):
            continue
        out.append((x, y, 'r' if hashed(i, 5, 11) % 3 else 'o', hashed(i, 6, 11) % 5 == 0))
    return out


def motes(final, grid):
    """Spore motes in the air."""
    for x, y, c, halo in mote_spots(final):
        final[y][x] = c
        if halo:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if final[y + dy][x + dx] == '.':
                    final[y + dy][x + dx] = 'q'


def rgb_of():
    import extract_poses as ep
    return {c: tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, hx in ep.ROLES}


def to_image(rows):
    from PIL import Image
    rgb = rgb_of()
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch != '.':
                px[x, y] = rgb[ch] + (255,)
    return img


def preview(path, rows):
    from PIL import Image, ImageDraw
    img = to_image(rows)
    back = Image.new('RGBA', (W, H), (30, 40, 54, 255))
    d = ImageDraw.Draw(back)
    half = FOOT / 2
    corners = [(AX + 16 * (x - y), AY + 8 * (x + y)) for x, y in ((-half, -half), (half, -half), (half, half), (-half, half))]
    d.polygon(corners, outline=(90, 130, 130))
    d.ellipse([AX - 2, AY - 2, AX + 2, AY + 2], outline=(230, 80, 80))
    back.alpha_composite(img)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    back.resize((W * 2, H * 2), Image.NEAREST).save(path)
    base = back.crop((0, 230, W, H)).resize((W * 3, (H - 230) * 3), Image.NEAREST)
    base.save(path.with_name(path.stem + '-base.png'))
    top = back.crop((0, 0, W, 190)).resize((W * 3, 190 * 3), Image.NEAREST)
    top.save(path.with_name(path.stem + '-top.png'))


# --- the animation ----------------------------------------------------------------------------------------------
# 12 frames that loop. Everything moves with a period that divides 12, so frame 12 runs into frame 1. The bark and the silhouette never move; only colours step along their ramps (the shimmer)
# and particles are added on top (sparkles, drips, motes).
FRAMES = 12
SHIMMER_MARKS = {'shelf': 1, 'cap': 1, 'vine': 1, 'leaf': 1, 'thorn': 1, 'eye': 2}     # which parts shimmer, and by how many steps at most
BARKY = {'trunk', 'bark', 'root', 'knot'}
DRIP_RAMPS = (('r', 'o', 'q', 's'), ('j', 'i', 'h', 'u'), ('t', 'r', 'o', 'q'))          # teal, magenta, pale cyan: bright to dark
FALL = (0, 2, 5, 9, 14, 20, 27, 35)                                                       # how far a drop has fallen after 0, 1, 2... frames of falling: 2, 3, 4, 5, 6, 7, 8 a frame
MAX_FALL = FALL[-1]
DRIPS = 22


def ramp_of(body, c):
    for ramp in (body.mat, getattr(body, 'rim', None), body.spotramp):
        if ramp and c in ramp:
            return ramp
    return None


def shimmer_wave(x, y, frame):
    """-1 .. 1: a slow wave of brightness travelling up the tree from the roots (one wavelength over the height of the picture), a little different from place to place."""
    jitter = (hashed((x - off()) // 14, y // 14, 21) % 100) / 100 * 0.16
    return math.sin(2 * math.pi * (frame / FRAMES - (AY - y) / 330.0 - jitter))


def sparkle_spots(grid, count=26):
    """Fixed random places on the bark where a sparkle flashes, each with its own start frame."""
    spots = []
    tries = 0
    while len(spots) < count and tries < 4000:
        tries += 1
        x, y = off() + 12 + hashed(tries, 1, 31) % (BASE_W - 24), 20 + hashed(tries, 2, 31) % (AY + 40)
        cell = grid[y][x]
        if not cell or cell[3].mark not in BARKY or any(abs(x - sx) + abs(y - sy) < 22 for sx, sy, _ in spots):
            continue
        spots.append((x, y, hashed(tries, 3, 31) % FRAMES))
    return spots


def drip_sources(rows, grid):
    """Where drops form: the undersides of the fungi, the tips of the hanging vines and the boughs, picked in a fixed order with room between them."""
    cand = []
    for y in range(40, AY + 70):
        for x in range(4, W - 4):
            cell = grid[y][x]
            if not cell or rows[y][x] == 'O' or rows[y + 1][x] != 'O':
                continue
            body = cell[3]
            kind = body.mark
            if kind in ('shelf', 'cap', 'leaf'):
                cand.append((hashed(x - off(), y, 41), x, y + 2, 'fungus' if kind != 'leaf' else 'vine'))
            elif kind == 'bark' and isinstance(cell[1], tuple) and cell[1][0] in ('low', 'top'):
                cand.append((hashed(x - off(), y, 42) + 7, x, y + 2, 'bough'))
    cand.sort()
    # the middle 384 columns pick first, as the narrow picture does, so a wide canvas keeps the same drops there; the sides pick after, in proportion to their width
    lo, hi = off() + 4, off() + BASE_W - 4
    batches = [([c for c in cand if lo <= c[1] < hi], DRIPS), ([c for c in cand if not lo <= c[1] < hi], round(DRIPS * (W - BASE_W) / BASE_W))]
    out = []
    for batch, share in batches:
        limit = len(out) + share
        for kind_quota in (('vine', 5), ('fungus', 7), ('bough', 5), ('fungus', 10), ('bough', 4)):
            want = kind_quota[1]
            for _, x, y, kind in batch:
                if want == 0 or len(out) >= limit:
                    break
                if kind != kind_quota[0] or any(math.hypot(x - ox, y - oy) < 17 for ox, oy, _ in out):
                    continue
                out.append((x, y, kind))
                want -= 1
    return out


def landing(rows, grid, x, y):
    """The row a drop falling from (x, y) lands on, if there is something to splash on (the ground, or the top of a fungus) within its fall; else None."""
    for yy in range(y + 8, min(H - 2, y + MAX_FALL + 1)):
        cell = grid[yy][x]
        if cell and cell[3].mark in ('ground', 'shelf', 'cap') and rows[yy][x] != 'O':
            return yy
    return None


def build_animation():
    """All 12 frames, as lists of role rows, plus nothing else: the same picture every time."""
    rows, grid = render(with_grid=True, still_motes=False)
    base = [list(r) for r in rows]
    spots = mote_spots(base)
    sparkles = sparkle_spots(grid)
    drips = [(x, y, kind, landing(rows, grid, x, y), (i * 5 + 3) % FRAMES, DRIP_RAMPS[i % 3]) for i, (x, y, kind) in enumerate(drip_sources(rows, grid))]
    # the slow motes drifting up beside the canopy, on clear sky only
    drifters = []
    for i in range(40):
        x, y = off() + 8 + hashed(i, 1, 51) % (BASE_W - 16), 40 + hashed(i, 2, 51) % 330
        if all(base[yy][xx] == '.' for xx in range(max(0, x - 4), min(W, x + 5)) for yy in range(max(0, y - 22), min(H, y + 3))):
            drifters.append((x, y, hashed(i, 3, 51) % FRAMES, 1 + hashed(i, 4, 51) % 2))
    frames = []
    for f in range(FRAMES):
        g = [row[:] for row in base]

        def put(x, y, c, over=True):
            if 0 <= x < W and 0 <= y < H and (over or g[y][x] == '.'):
                g[y][x] = c
        # 1. the shimmer: the glowing parts step along their own ramps, in a wave that climbs the tree
        for y in range(H):
            for x in range(W):
                cell = grid[y][x]
                if not cell or g[y][x] == 'O':
                    continue
                body = cell[3]
                amp = SHIMMER_MARKS.get(body.mark)
                if not amp:
                    continue
                ramp = ramp_of(body, g[y][x])
                if not ramp:
                    continue
                w = shimmer_wave(x, y, f)
                shift = 0 if abs(w) < 0.5 else (1 if w > 0 else -1) * (amp if abs(w) > 0.85 else 1)
                i = ramp.index(g[y][x])
                g[y][x] = ramp[max(0, min(3, i - shift))]
        # 2. the motes that were already there twinkle (bright, dim, bright; two frames out of twelve they dim right down)
        for n, (x, y, c, halo) in enumerate(spots):
            k = (f + hashed(n, 7, 61)) % FRAMES
            put(x, y, c if k < 8 else ('q' if k < 10 else 's'))
            if halo and k < 8:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(x + dx, y + dy, 'q', over=False)
        # 3. spores drifting up, fading in and out so the wrap is not seen
        for x, y, ph, speed in drifters:
            k = (f + ph) % FRAMES
            c = ('s', 'q', 'o', 'r', 'r', 'r', 'o', 'o', 'o', 'q', 's', 's')[k]
            put(x + round(1.4 * math.sin(2 * math.pi * (k / FRAMES + ph / 7.0))), y - speed * k, c, over=False)
        # 4. sparkles on the bark: a single pixel, then a bright pair, then a single pixel again
        for x, y, start in sparkles:
            k = (f - start) % FRAMES
            if k == 0 or k == 2:
                put(x, y, 'r')
            elif k == 1:
                put(x, y, 't')
                put(x + 1, y, 'r')
                put(x, y - 1, 'r')
        # 5. the drips: a bead forms, swells, falls faster and faster, fades, and splashes if there is something to land on
        for x, y, kind, hit, phase, ramp in drips:
            k = (f - phase) % FRAMES
            if k == 0:
                put(x, y, ramp[1])
                put(x + 1, y, ramp[1])
            elif k == 1:
                for dx in (0, 1):
                    put(x + dx, y, ramp[1])
                    put(x + dx, y + 1, ramp[0])
            elif k == 2:
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)):
                    put(x + dx, y + dy, ramp[0] if dy else ramp[1])
            else:
                m = k - 3                                            # frames since it began to fall
                arrive = None                                        # the frame it reaches the surface it lands on
                if hit is not None:
                    arrive = next((j for j in range(len(FALL)) if y + 1 + FALL[j] >= hit - 1), None)
                if arrive is not None and m == arrive:               # a bright splash across the surface
                    for dx in (-1, 0, 1):
                        put(x + dx, hit - 1, ramp[0])
                    put(x, hit - 2, ramp[1])
                elif arrive is not None and m == arrive + 1:         # the ripple spreads, dimmer
                    for dx in (-2, 2):
                        put(x + dx, hit - 1, ramp[2])
                    for dx in (-1, 1):
                        put(x + dx, hit - 2, ramp[3])
                elif m < len(FALL) and (arrive is None or m < arrive):
                    head = y + 1 + FALL[m]
                    fade = max(0, m - 3) if arrive is None else 0   # one that lands stays bright; one that falls on and on fades out
                    for dx in (0, 1):                                # a drop two pixels wide: a bright head, and a tail that gets dimmer
                        put(x + dx, head, ramp[min(3, fade)])
                        put(x + dx, head - 1, ramp[min(3, fade)])
                    put(x, head - 2, ramp[min(3, 1 + fade)])
                    put(x, head - 3 if m >= 2 else head - 2, ramp[min(3, 2 + fade)])
                    if m >= 4:
                        put(x, head - 4, ramp[min(3, 3 + fade)])
        frames.append([''.join(r) for r in g])
    return frames


BACKDROP = (30, 40, 54, 255)


def frame_images(frames, scale=1, crop=None):
    """The frames as RGBA pictures on a dark backdrop (so a GIF has no transparency to fringe), optionally cropped and enlarged."""
    from PIL import Image
    out = []
    for rows in frames:
        img = Image.new('RGBA', (W, H), BACKDROP)
        img.alpha_composite(to_image(rows))
        if crop:
            img = img.crop(crop)
        out.append(img.resize((img.width * scale, img.height * scale), Image.NEAREST) if scale != 1 else img)
    return out


def write_gif(path, images, fps=10):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pal = [im.convert('RGB') for im in images]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / fps), loop=0, optimize=False, disposal=1)


def write_sheet(path, frames, cols=4):
    from PIL import Image
    imgs = [im.resize((W // 2, H // 2), Image.NEAREST) for im in frame_images(frames)]
    rows_n = -(-len(imgs) // cols)
    sheet = Image.new('RGBA', (cols * (W // 2 + 4), rows_n * (H // 2 + 4)), (12, 14, 20, 255))
    for i, im in enumerate(imgs):
        sheet.alpha_composite(im, ((i % cols) * (W // 2 + 4), (i // cols) * (H // 2 + 4)))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


BASE_CROP = (100, 318, 260, 420)         # the foot of the tree: the hollow, the roots and the toadstools


def base_crop():
    """BASE_CROP on whatever canvas is in use (the wide canvas shifts the tree right)."""
    return (BASE_CROP[0] + off(), BASE_CROP[1], BASE_CROP[2] + off(), BASE_CROP[3])


CATEGORY = 'Victory Screen'
FOLDER = 'all-tree'
FPS = 10


def build_assets():
    """`all-tree`, the 12-frame loop (shimmer and dripping spores, 10 a second), and `all-tree-still`, the flat picture; 384 x 448, anchored at the middle of the base. Nothing is placed on a map: it is a display piece."""
    make = family(CATEGORY, W, H, ANCHOR, place='none', folder=FOLDER)
    rows_of = lambda frame: [r if isinstance(r, str) else ''.join(r) for r in frame]
    return [make('all-tree', 'The All Tree (animated)', 'animation', [rows_of(f) for f in build_animation()], fps=FPS),
            make('all-tree-still', 'The All Tree (still)', 'still', [rows_of(render())])]


WIDE_W = 704                     # the wide canvas: the boughs reach 335 px left and 294 px right of the anchor in the autumn tree (286 and 233 here), and this leaves a margin of at least 16 px, in whole 64s
WIDE_FOLDER = 'all-tree'


def build_wide_assets():
    """The same two assets on the wide canvas: `all-tree-wide` (the loop) and `all-tree-wide-still`, 704 x 448, anchored at (352, 336): the sides of the tree are no longer cut off."""
    with wide_canvas(WIDE_W):
        make = family(CATEGORY, W, H, ANCHOR, place='none', folder=WIDE_FOLDER)
        rows_of = lambda frame: [r if isinstance(r, str) else ''.join(r) for r in frame]
        return [make('all-tree-wide', 'The All Tree (animated, wide)', 'animation', [rows_of(f) for f in build_animation()], fps=FPS),
                make('all-tree-wide-still', 'The All Tree (still, wide)', 'still', [rows_of(render())])]


def write_package(folder):
    """Beside the sheets: all-tree.json, the numbers a screen needs (README.md says it in words)."""
    write_json(folder, 'all-tree.json', 'The All Tree sheets in this folder. See README.md beside this file.',
               {'cell': [W, H], 'anchor': {'x': AX, 'y': AY}, 'frames': FRAMES, 'fps': FPS, 'footprint': [FOOT, FOOT], 'levels': 20,
                'animated': 'all-tree.png', 'still': 'all-tree-still.png', 'sheet': {'cols': 8, 'rows': 2},
                'wide': {'cell': [WIDE_W, H], 'anchor': {'x': WIDE_W // 2, 'y': AY}, 'animated': 'all-tree-wide.png', 'still': 'all-tree-wide-still.png', 'sheet': {'cols': 8, 'rows': 2}, 'about': 'the same tree on a wider canvas so the sides are not cut off'}})


def main():
    parser = argparse.ArgumentParser(description='The All Tree: the victory screen\'s massive corrupted ancient tree (preview).')
    parser.add_argument('--preview', type=Path, help='write the picture over its footprint here, enlarged, plus -base and -top crops')
    parser.add_argument('--png', type=Path, help='write the flat 384 x 448 transparent picture here')
    parser.add_argument('--animate', type=Path, help='write a contact sheet of the 12 animation frames here (4 x 3, half size)')
    parser.add_argument('--gif', type=Path, help='write the looping animation here (10 frames a second, 1x), and an 8x one of the foot of the tree beside it (NAME-base.gif)')
    parser.add_argument('--frame-dir', type=Path, help='also write every frame as a transparent PNG here')
    parser.add_argument('--wide', action='store_true', help=f'draw on the wide {WIDE_W} x 448 canvas, so the sides of the tree are not cut off')
    args = parser.parse_args()
    if not (args.preview or args.png or args.animate or args.gif or args.frame_dir):
        parser.error('say --preview, --png, --animate, --gif or --frame-dir')
    if args.wide:
        with wide_canvas(WIDE_W):
            return run(args)
    return run(args)


def run(args):
    if args.animate or args.gif or args.frame_dir:
        frames = build_animation()
        if args.animate:
            write_sheet(args.animate, frames)
            print('the 12 frames, half size ->', args.animate)
        if args.gif:
            write_gif(args.gif, frame_images(frames))
            write_gif(args.gif.with_name(args.gif.stem + '-base.gif'), frame_images(frames, 8, base_crop()))
            print('the looping animation ->', args.gif, 'and', args.gif.with_name(args.gif.stem + '-base.gif'))
        if args.frame_dir:
            args.frame_dir.mkdir(parents=True, exist_ok=True)
            for i, fr in enumerate(frames):
                to_image(fr).save(args.frame_dir / f'all-tree-{i:02d}.png')
            print('frames ->', args.frame_dir)
    if not (args.preview or args.png):
        return
    rows = render()
    if args.png:
        args.png.parent.mkdir(parents=True, exist_ok=True)
        to_image(rows).save(args.png)
        print('the All Tree ->', args.png)
    if args.preview:
        preview(args.preview, rows)
        print('the All Tree, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
