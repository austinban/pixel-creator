#!/usr/bin/env python3
"""A small isometric renderer for buildings, in exactly the ground tiles' projection and palette.

The ground tiles are 32 x 32 cubes: a top face 32 wide and 16 tall, and vertical edges 16 tall. One step along either grid axis moves the
picture 16 across and 8 down, and one level of height is 16 pixels up. A building is a set of solids placed on a footprint of whole ground
cells (FX x FY), drawn as one sprite that covers them, like the boss does, with the anchor at the middle of the footprint on the ground.

World axes (the same as terrain.js): X runs down and to the right (SE), Y down and to the left (SW), Z up, one unit = one cell = one level.
The camera sees the +X face (the right wall), the +Y face (the left wall) and the top. A screen point is

    sx = 16 * (X - Y) + OFFSET_X          sy = 8 * (X + Y) - 16 * Z + OFFSET_Y

and the view direction is (1, 1, 1): a pixel's ray is every point (X + t, Y + t, t), and the solid it hits at the largest t is the one in front.

A solid is a convex shape: a list of planes it lies under, and a material that says what colour (a palette role) any point on it is. Roofs and
towers are convex too, so a building is a few of them: boxes for walls, a prism for a gable roof, a pyramid for a hip or a spire.

The same scene is drawn two ways: `fine=True` is the sprite, with stone courses, tile rows, planks and mortar one pixel wide, like the ground tiles'
cobbles; `fine=False` is the model, flat colour per face, for judging the shapes at a large size before any pixel work.
"""
import math

LEVEL = 16          # pixels per level of height
STEP_X, STEP_Y = 16, 8
MARGIN = 8          # room each side of the footprint for a roof's overhang


def hashed(a, b, salt=0):
    n = (a * 374761393 + b * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


# --- solids ------------------------------------------------------------------------------------
def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def plane(n, point):
    n = norm(n)
    return (n, sum(n[i] * point[i] for i in range(3)))


class Solid:
    """A convex solid: the planes (outward normal, offset) it lies under, and how it is painted."""

    def __init__(self, planes, style, features=None, end=None, decay=None):
        self.planes = planes
        self.style = style
        self.decay = decay or []                 # weathering and growth painted over the surface: see overlay()
        self.end = end or style                  # what a roof's upright end (a gable) is made of
        self.features = features or []          # [(face 'R' or 'L', a0, a1, z0, z1, kind)], a along the face in world units

    def hit(self, origin, v=(1.0, 1.0, 1.0)):
        """(t, normal) where the pixel's ray first meets the solid coming from the camera, or None."""
        lo, hi = -1e9, 1e9
        face = None
        for n, d in self.planes:
            nv = sum(n[i] * v[i] for i in range(3))
            na = sum(n[i] * origin[i] for i in range(3))
            if abs(nv) < 1e-9:
                if na > d + 1e-9:
                    return None
                continue
            t = (d - na) / nv
            if nv > 0:                  # the ray leaves this plane's solid at t: an upper bound, and the face the camera sees
                if t < hi:
                    hi, face = t, n
            elif t > lo:
                lo = t
            if lo > hi + 1e-9:
                return None
        return (hi, face) if face is not None and lo <= hi + 1e-9 else None


def box(x0, x1, y0, y1, z0, z1, style, features=None, decay=None):
    return Solid([((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)], style, features, decay=decay)


def gable(x0, x1, y0, y1, z0, rise, style, ridge='x', end='timber'):
    """A roof prism: ridge along X (slopes facing +Y and -Y) or along Y (slopes facing +X and -X), `rise` above z0."""
    if ridge == 'x':
        ym = (y0 + y1) / 2
        return Solid([plane((0, rise, y1 - ym), (0, y1, z0)), plane((0, -rise, ym - y0), (0, y0, z0)),
                      ((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 0, -1), -z0)], style, end=end)
    xm = (x0 + x1) / 2
    return Solid([plane((rise, 0, x1 - xm), (x1, 0, z0)), plane((-rise, 0, xm - x0), (x0, 0, z0)),
                  ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, -1), -z0)], style, end=end)


def pyramid(x0, x1, y0, y1, z0, rise, style, top=0.0):
    """A hipped roof or spire: four slopes meeting `rise` above z0, at a point (top = 0) or a flat top `top` wide."""
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = top / 2, top / 2
    zt = z0 + rise
    return Solid([plane((rise, 0, x1 - (xm + hx)), (x1, ym, z0)), plane((-rise, 0, (xm - hx) - x0), (x0, ym, z0)),
                  plane((0, rise, y1 - (ym + hy)), (xm, y1, z0)), plane((0, -rise, (ym - hy) - y0), (xm, y0, z0)),
                  ((0, 0, 1), zt), ((0, 0, -1), -z0)], style)


# --- paint ---------------------------------------------------------------------------------
def face_of(n):
    """Which face the camera sees: 'top', 'R' (the +X wall), 'L' (the +Y wall), or a roof slope 'sR' / 'sL', else None."""
    if n[2] > 0.95:
        return 'top'
    if abs(n[2]) < 0.05:
        return 'R' if n[0] > 0.7 else 'L' if n[1] > 0.7 else None
    if n[2] > 0:
        return 'sR' if n[0] > 0.05 else 'sL' if n[1] > 0.05 else None
    return None


STONE = {'R': dict(base='q', alt=('r', 'p'), mortar='p', lit='r'), 'L': dict(base='p', alt=('q', 'l'), mortar='l', lit='q'),
         'top': dict(base='q', alt=('r', 'p'), mortar='p', lit='r')}
ROOFS = {      # base, the line under a row, the bright line at its top; the lit slope first, then the shaded one
    'tile': {'sR': ('e', 'f', 'c'), 'sL': ('f', 'g', 'e')},            # a soft terracotta: coral over orchid and plum
    'slate': {'sR': ('l', 'k', 'p'), 'sL': ('k', 'w', 'l')},           # lavender and indigo
    'teal': {'sR': ('q', 's', 'r'), 'sL': ('p', 's', 'q')},            # steel teal with deep teal between the rows
    'dark': {'sR': ('l', 'k', 'p'), 'sL': ('k', 'w', 'l')},
}


def stone(face, a, b, fine):
    """Coursed stone: 4 pixel courses, blocks 8 wide, every other course shifted half a block. It repeats every 16 pixels both ways."""
    s = STONE[face]
    if not fine:
        return s['base']
    row = b // 4
    col, c = divmod(a + (4 if row % 2 else 0), 8)
    r = b % 4
    if r == 3 or c == 7:
        return s['mortar']
    h = hashed(col % 2, row % 4) % 7
    if h == 0:
        return s['alt'][0]
    if h == 1:
        return s['alt'][1]
    if r == 0 and h < 5:
        return s['lit']
    return s['base']


def plaster(face, a, b, fine, timber=True, brace=False):
    """Plaster between timber: a post up each edge of the cell and a beam along its top, so stacked pieces make a frame. It repeats every 16."""
    base = 't' if face == 'R' else 'C'
    if not fine:
        return base
    a, b = a % 16, b % 16
    if timber:
        if b >= 14:
            return 'g' if b == 14 else 'w'
        if a in (0, 15):
            return 'g' if a == 0 else 'w'
        if brace and abs((15 - b) - a) <= 0 or brace and abs((15 - b) - a) == 1 and a % 2:
            return 'g'
    h = hashed(a, b) % 23
    return 'C' if h == 0 and face == 'R' else 'b' if h == 0 else base


def roof(style, face, a, up, fine):
    """Tile rows 4 pixels high and 8 wide, every other row shifted half a tile. It repeats every 16 pixels both ways."""
    base, line, high = ROOFS[style][face]
    if not fine:
        return base
    row, r = divmod(up, 4)
    col = (a + (4 if row % 2 else 0)) % 8
    if r == 3 or col == 7:
        return line
    if r == 0:
        return high if hashed(a // 8, row % 4) % 3 else base
    return base


def inside_arch(lx, ly, w):
    """Whether a pixel of an opening w wide is inside its rounded top (ly counted down from the top of the opening)."""
    r = w / 2
    return ly >= r or math.hypot(lx + 0.5 - r, ly + 0.5 - r) <= r


def feature_colour(kind, lx, ly, w, h, face):
    """A window, door or opening: lx from the left edge of its rectangle, ly down from the top, in pixels. None means plain wall."""
    if kind in ('doorlow', 'doorup', 'open', 'arch'):
        rounded = kind != 'doorlow'                  # a door's lower piece is square; its upper piece, a belfry or a gate has the arch
        if rounded and not inside_arch(lx, ly, w):
            return None
        edge = lx == 0 or lx == w - 1 or (rounded and (ly == 0 or not inside_arch(lx - 1, ly, w) or not inside_arch(lx + 1, ly, w) or not inside_arch(lx, ly - 1, w)))
        if kind == 'open':
            return 'w' if edge else 'k'
        if kind == 'arch':
            return 'l' if edge else 'k'
        if edge or lx % 4 == 3:
            return 'x'
        if kind == 'doorlow' and lx == w - 3 and ly == h // 2:
            return 'd'
        if lx % 4 == 0:
            return 'f' if face == 'R' else 'g'           # the lit edge of each plank
        return 'g' if face == 'R' else 'w'
    if kind == 'slit':
        return 'k'
    edge = lx == 0 or ly == 0 or lx == w - 1 or ly == h - 1                         # a window: a frame, dark glass, a glint, a mullion
    if edge:
        return 'g' if face == 'R' else 'w'
    if lx == w // 2 or ly == h // 2:
        return 'g' if face == 'R' else 'w'
    return 'p' if (lx + ly) % 5 == 0 else 'k'


# --- weathering, damage and growth --------------------------------------------------------------
# Painted over a surface by pixel (a along the face, b up it, both 0..15 inside one cell and repeating, so stacked blocks stay continuous).
DARKER = {'r': 'q', 'q': 'p', 'p': 'l', 'l': 'k', 'C': 'b', 'b': 'a', 't': 'C', 'a': 'e', 'e': 'f', 'f': 'g', 'm': 'k', 'n': 'm', 's': 'k'}
LEAF = {True: ('B', 'A', 's'), False: ('s', 'B', 'k')}        # base, highlight and shade of a leaf on a lit wall and on a shaded one


def noise(a, b, salt=0, cell=3):
    """Soft blobs: a value that changes slowly across the surface, 0..99, and repeats every 16 pixels."""
    return hashed((a % 16) // cell, (b % 16) // cell, salt) % 100


def leaf(lit, a, b, salt=0):
    base, high, shade = LEAF[lit]
    h = hashed(a, b, salt) % 6
    return high if h == 0 else shade if h == 1 else base


def vine_columns(kind):
    # (column, length) of each stem; the middle one runs the full height so a vine rises from one block into the next
    return {'vines-low': [(3, 10), (8, 16), (12, 7)], 'vines-hang': [(2, 6), (8, 16), (13, 11)]}[kind]


def overlay(kind, lit, a, b, base):
    """The colour a decay `kind` gives the pixel (a, b), or `base` where it leaves it alone. lit: the lit wall or slope (else the shaded one)."""
    a, b = a % 16, b % 16
    if kind in ('vines-low', 'vines-hang'):
        for i, (col, length) in enumerate(vine_columns(kind)):
            depth = b if kind == 'vines-low' else 15 - b
            if depth >= length:
                continue
            c = col + ((b // 3) % 2)                                   # the stem wanders a pixel either side
            if a == c:
                return LEAF[lit][2]
            if abs(a - c) == 1 and (b + 2 * i) % 3 == 0:
                return leaf(lit, a, b, i)
            if abs(a - c) == 2 and (b + i) % 5 == 0:
                return leaf(lit, a, b, i + 9)
        return base
    if kind == 'vines-heavy':
        n = hashed(a, b, 7) % 100
        return leaf(lit, a, b, 3) if n < 64 + (10 if b < 6 else 0) else base
    if kind == 'vines-frame':                                         # around a window: up each side and over the top
        for i, c in enumerate((2, 13)):
            if a == c + ((b // 4) % 2) and b < 16:
                return LEAF[lit][2]
            if abs(a - c) == 1 and (b + i) % 3 == 0:
                return leaf(lit, a, b, i)
        if b >= 13 and hashed(a, b, 5) % 100 < 55:
            return leaf(lit, a, b, 2)
        return base
    if kind == 'mossy':
        if (b < 3 and hashed(a, b, 1) % 100 < 70) or (noise(a, b, 4) < 20 and hashed(a, b, 2) % 3):
            return leaf(lit, a, b, 5) if hashed(a, b, 6) % 3 else DARKER.get(base, base)
        return base
    if kind == 'worn':
        crack = 5 + int(2.4 * math.sin(b * 0.55)) + (15 - b) // 6
        if a == crack % 16 and 2 <= b <= 15:
            return 'k'
        if a in (10, 11) and b >= 7:                                  # a stain running down from above
            return DARKER.get(base, base)
        return base
    if kind == 'hole':
        d = math.hypot(a - 7.5, b - 7.5)
        edge = 4.0 + (hashed(a, b, 11) % 3) * 0.5
        if d < edge - 0.6:
            return 'k' if b > 4 else 'w'
        if d < edge + 1.4:
            return DARKER.get(base, base)
        if b < 3 and hashed(a, b, 12) % 3 == 0:
            return 'p'
        return base
    if kind == 'peeled':                                              # plaster fallen away, the stone and laths showing
        d = math.hypot(a - 9, b - 7)
        if d < 4.5 + (hashed(a, b, 13) % 3) * 0.6:
            return 'l' if b % 4 == 3 else 'p'
        if d < 5.8:
            return 'C' if lit else 'b'
        return base
    if kind == 'roof-moss':
        if noise(a, b, 21, 4) < 28 and hashed(a, b, 22) % 4:
            return leaf(lit, a, b, 8)
        return base
    if kind == 'roof-broken':
        d = math.hypot(a - 8, b - 8)
        if d < 3.2 + (hashed(a, b, 31) % 2) * 0.6:
            return 'k'
        if d < 4.6:
            return DARKER.get(base, base)
        return base
    return base


def solid_feature_ok(kind):
    return kind in ('window', 'slit')


def paint(solid, face, P, fine):
    """The palette role at point P of a solid's visible face."""
    x, y, z = P
    if face in ('R', 'L'):
        along = y if face == 'R' else x
        a, b = int(math.floor(along * LEVEL + 1e-6)), int(math.floor(z * LEVEL + 1e-6))
        for f, a0, a1, z0, z1, kind in solid.features:
            if f == face and a0 <= along < a1 and z0 <= z < z1:
                w, h = int(round((a1 - a0) * LEVEL)), int(round((z1 - z0) * LEVEL))
                colour = feature_colour(kind, a - int(round(a0 * LEVEL)), int(round(z1 * LEVEL)) - 1 - b, w, h, face)
                if colour:
                    for item in solid.decay:                   # vines may creep over a window, but never a door or an opening
                        only, kind2 = item if isinstance(item, tuple) else (None, item)
                        if kind2.startswith('vines') and solid_feature_ok(kind) and only in (None, face):
                            colour = overlay(kind2, face == 'R', a, b, colour)
                    return colour
        style = solid.end
        if style in ROOFS:                                    # a box made of roofing: a cap, a band
            colour = roof(style, 'sR' if face == 'R' else 'sL', a, b, fine)
        elif style == 'stone':
            colour = stone(face, a, b, fine)
        elif style == 'wood':
            colour = 'x' if a % 4 == 3 else ('g' if face == 'R' else 'w')
        else:
            colour = plaster(face, a, b, fine, timber=style in ('timber', 'brace'), brace=style == 'brace')
        for item in solid.decay:
            only, kind = item if isinstance(item, tuple) else (None, item)
            if only in (None, face):
                colour = overlay(kind, face == 'R', a, b, colour)
        return colour
    if face == 'top':
        a, b = int(math.floor(x * LEVEL)), int(math.floor(y * LEVEL))
        if solid.style in ROOFS:
            return ROOFS[solid.style]['sR'][0]
        return stone('top', a, b, fine) if fine else STONE['top']['base']
    # a roof slope: courses run along it
    along = y if face == 'sR' else x
    a, up = int(math.floor(along * LEVEL + 1e-6)), int(math.floor(z * LEVEL + 1e-6))
    colour = roof(solid.style, face, a, up, fine)
    for kind in solid.decay:
        colour = overlay(kind, face == 'sR', a, up, colour)
    return colour


# --- drawing ---------------------------------------------------------------------------------
def render(solids, fx, fy, zmax, fine=True, scale=1, margin=MARGIN, extra_row=1):
    """The building as rows of palette roles, size (16 * (fx + fy) + 2 * MARGIN) x (8 * (fx + fy) + 16 * zmax + 1) times `scale`.
    Returns (rows, anchor): the anchor is the middle of the footprint on the ground, in pixels (before scaling)."""
    w = 16 * (fx + fy) + 2 * margin
    h = 8 * (fx + fy) + int(round(LEVEL * zmax)) + extra_row
    ox, oy = 16 * fy + margin, int(round(LEVEL * zmax))
    rows = []
    for py in range(h * scale):
        row = ''
        for px in range(w * scale):
            sx, sy = (px + 0.5) / scale, (py + 0.5) / scale
            a, b = (sx - ox) / STEP_X, (sy - oy) / STEP_Y          # X - Y at z = 0, and X + Y
            origin = ((a + b) / 2, (b - a) / 2, 0.0)
            best = None
            for s in solids:
                got = s.hit(origin)
                if got and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], s)
            if best is None:
                row += '.'
                continue
            t, n, s = best
            face = face_of(n)
            colour = paint(s, face, (origin[0] + t, origin[1] + t, t), fine) if face else None
            row += colour or '.'
        rows.append(row)
    return rows, (8 * (fx + fy) + margin, int(round(LEVEL * zmax)) + 8 * (fx + fy))
