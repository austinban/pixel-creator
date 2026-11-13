#!/usr/bin/env python3
"""A small ray-cast renderer for props on whole ground cells, shared by the water props (make_water_props.py) and the destructibles (make_destructibles.py).

It is the buildings' and the rocks' projection (tools/buildings.py, tools/make_rocks.py): a cell is a 32 x 16 diamond, one step along x moves the picture 16 across and 8 down, along y 16 across and
8 down-left, and one level of height is 16 pixels up. z = 0 is whatever the prop stands on (the ground, or the water's surface for the water props). A prop is a few convex solids (a Part is a
buildings.Solid with a material; a make_rocks.Blob is a lump) and a painter says which palette role every visible point is. The camera sees +x, +y and the top, and a solid nearer to it hides one behind.

A Scene is the picture being made: scene.draw(solids) paints the solids, scene.pixel / scene.disc / scene.ellipse put 2D marks on it (ripples, foam, sparks), and scene.finish() puts the one pixel
outline round everything and returns the rows and the anchor. Palette roles only, and deterministic: no random without a seed.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildings import Solid, plane, norm, hashed  # noqa: E402,F401
import buildings as bd  # noqa: E402

LEVEL = 16
LIGHT = norm((0.55, 0.15, 0.8))          # towards the light, as the buildings and rocks have it: the right wall lit, the left shaded, the top brightest
WOOD = [(0.72, 'a'), (0.50, 'e'), (0.30, 'f'), (0.12, 'g'), (-9, 'w')]            # the bridge's wood: orange, coral, orchid, plum
CRATE = [(0.72, 'e'), (0.50, 'f'), (0.30, 'h'), (0.12, 'g'), (-9, 'w')]           # the crates' wood: coral, orchid, magenta, plum
STONE = [(0.80, 'r'), (0.62, 'q'), (0.44, 'p'), (0.27, 'l'), (0.12, 'k'), (-9, 'w')]
HAY = [(0.70, 'd'), (0.48, 'b'), (0.28, 'C'), (0.12, 'a'), (-9, 'g')]
CLAY = [(0.72, 'c'), (0.50, 'e'), (0.30, 'f'), (0.12, 'g'), (-9, 'w')]
RED = [(0.55, 'c'), (0.34, 'e'), (0.16, 'h'), (0.04, 'u'), (-9, 'w')]
IRON = [(0.75, 'p'), (0.5, 'l'), (0.25, 'k'), (-9, 'w')]
WATER = [(0.70, 'o'), (0.45, 'n'), (0.2, 'm'), (-9, 'k')]
DARKER = {'r': 'q', 'q': 'p', 'p': 'l', 'l': 'k', 'k': 'w', 'w': 'x', 'a': 'e', 'e': 'f', 'f': 'g', 'g': 'w', 'c': 'e', 'h': 'u', 'u': 'w', 'd': 'b', 'b': 'a', 'C': 'b',
          'z': 'A', 'A': 'B', 'B': 's', 'o': 'n', 'n': 'm', 'm': 'k', 't': 'C', 's': 'D', 'D': 'D', 'x': 'x', 'y': 'h', 'j': 'y', 'v': 'u'}
LIGHTER = {v: k for k, v in DARKER.items() if v != k}


def ramp_of(table, v):
    for lo, role in table:
        if v >= lo:
            return role
    return table[-1][1]


def noise(a, b, salt=0):
    return hashed(a & 0xFFFF, b & 0xFFFF, salt & 0xFFFF) / 65535.0


def lum_of(n):
    return n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]


# --- solids ---------------------------------------------------------------------------------------
class Part(Solid):
    """A convex solid with a material (`mat`: wood, crate, stone, hay, clay, red, iron, water), and whatever the painters read: grain ('x', 'y'), worn (0 to 1), band, seed, top."""

    def __init__(self, planes, mat, top, seed=0, **attrs):
        super().__init__(planes, 'stone' if mat == 'stone' else 'wood', None, end='stone' if mat == 'stone' else 'wood')
        self.mat, self.top, self.seed = mat, top, seed
        self.natural = False
        self.walk = False
        self.__dict__.update(attrs)


def box(x0, x1, y0, y1, z0, z1, mat, seed=0, **attrs):
    """An upright box of a material."""
    planes = [((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)]
    return Part(planes, mat, z1, seed, bounds=(x0, x1, y0, y1, z0, z1), **attrs)


def prism(cx, cy, r, sides, z0, z1, mat, seed=0, turn=0.0, lean=0.0, ry=None, **attrs):
    """A regular prism (an octagon for a barrel, a post) standing on z0, `r` from the middle to a flat side; `lean` makes the sides slope in (positive) or out (negative) going up."""
    ry = ry or r
    planes = [((0, 0, 1), z1), ((0, 0, -1), -z0)]
    for k in range(sides):
        a = turn + 2 * math.pi * k / sides
        nx, ny = math.cos(a), math.sin(a)
        planes.append(plane((nx, ny, lean), (cx + nx * r, cy + ny * ry, z0)))
    return Part(planes, mat, z1, seed, centre=(cx, cy), radius=r, bounds=(cx - r, cx + r, cy - ry, cy + ry, z0, z1), **attrs)


def wheel(cx, cy, cz, r, thick, axis, mat, seed=0, **attrs):
    """A wheel or a disc: an octagon `r` across standing with its axis along `axis` ('y' or 'x' for a wheel on its side, 'z' for one lying flat), `thick` thick."""
    planes = []
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.15
        c, s = math.cos(a), math.sin(a)
        if axis == 'y':
            planes.append(plane((c, 0, s), (cx + c * r, cy, cz + s * r)))
        elif axis == 'x':
            planes.append(plane((0, c, s), (cx, cy + c * r, cz + s * r)))
        else:
            planes.append(plane((c, s, 0), (cx + c * r, cy + s * r, cz)))
    if axis == 'y':
        planes += [((0, 1, 0), cy + thick / 2), ((0, -1, 0), -(cy - thick / 2))]
    elif axis == 'x':
        planes += [((1, 0, 0), cx + thick / 2), ((-1, 0, 0), -(cx - thick / 2))]
    else:
        planes += [((0, 0, 1), cz + thick / 2), ((0, 0, -1), -(cz - thick / 2))]
    top = cz + (r if axis != 'z' else thick / 2)
    return Part(planes, mat, top, seed, wheel=(cx, cy, cz, r, axis), **attrs)


def pyramid(cx, cy, hw, z0, rise, mat, seed=0, **attrs):
    """A spike: a four-sided point `rise` high on a base `hw` from the middle to a side."""
    planes = [((0, 0, -1), -z0)]
    for nx, ny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        planes.append(plane((nx * rise, ny * rise, hw), (cx + nx * hw, cy + ny * hw, z0)))
    return Part(planes, mat, z0 + rise, seed, **attrs)


# --- painters -------------------------------------------------------------------------------------
def tint(role, steps):
    for _ in range(abs(steps)):
        role = (DARKER if steps > 0 else LIGHTER).get(role, role)
    return role


def paint_wood(s, n, P, table=None):
    """Boards: the top in planks 3 pixels wide along `grain` with butt joints and knots; a side in upright boards; a worn one is greyer, mossy and chipped."""
    x, y, z = P
    table = table or (CRATE if s.mat == 'crate' else WOOD)
    lum = lum_of(n)
    sd = s.seed & 0xFFF
    worn = getattr(s, 'worn', 0.0)
    if n[2] > 0.9:
        grain = getattr(s, 'grain', 'x')
        u, v = (y, x) if grain == 'x' else (x, y)
        pu, pv = int(math.floor(u * LEVEL)), int(math.floor(v * LEVEL))
        plank = pu // 3
        lum += (noise(plank, 1, sd) - 0.5) * 0.14
        role = ramp_of(table, lum)
        if pu % 3 == 2:
            role = tint(role, 1)                                                  # the gap between two planks
        elif (pv + noise(plank, 2, sd) * 13) % 13 < 0.7:
            role = tint(role, 1)                                                  # a butt joint
        elif noise(pu, pv // 2, sd + 5) > 0.93:
            role = tint(role, 1)                                                  # grain
        if noise(pu // 2, pv // 2, sd + 9) > 0.985:
            role = tint(role, 2)                                                  # a knot
        if worn and noise(pu // 2, pv // 2, sd + 21) > 1 - 0.5 * worn:
            role = 'A' if noise(pu, pv, sd + 4) > 0.5 else 'B'
        return role
    hn = math.hypot(n[0], n[1]) or 1
    along = (x * -n[1] + y * n[0]) / hn
    a, b = int(math.floor(along * LEVEL)), int(math.floor(z * LEVEL))
    if n[2] < -0.1:
        lum -= 0.1
    board = a // 3
    lum += (noise(board, 3, sd) - 0.5) * 0.12
    role = ramp_of(table, lum)
    if a % 3 == 2:
        role = tint(role, 1)
    elif noise(board, b // 4, sd + 1) > 0.9 and b % 4 == 0:
        role = tint(role, 1)
    if worn and (noise(a // 2, b // 2, sd + 33) > 1 - 0.55 * worn):
        role = tint(role, 1) if noise(a, b, sd) > 0.5 else role
    if worn and z > getattr(s, 'top', 1) - 0.1 and noise(a, 1, sd + 8) > 1 - 0.7 * worn:
        role = 'A' if noise(a, b, sd) > 0.5 else 'B'
    return role


def paint_plain(table):
    """A smooth, lit material by its normal, with a little noise: clay, hay, iron, red."""
    def painter(s, n, P):
        x, y, z = P
        ix, iy, iz = (int(math.floor(v * LEVEL)) for v in P)
        lum = lum_of(n) + (noise(ix + iz, iy + iz, s.seed & 0xFFF) - 0.5) * 0.08
        return ramp_of(table, lum)
    return painter


def paint_hay(s, n, P):
    """Straw: short dashes of a darker and a lighter tone lying every way, over a lit ramp."""
    x, y, z = P
    ix, iy, iz = (int(math.floor(v * LEVEL)) for v in P)
    lum = lum_of(n) + (noise(ix // 2 + iz, iy // 2 + iz, s.seed & 0xFFF) - 0.5) * 0.2
    role = ramp_of(HAY, lum)
    k = noise(ix + 3 * iz, iy + 5 * iz, 77 + (s.seed & 0xFF))
    if k > 0.86:
        role = tint(role, 1)
    elif k < 0.07:
        role = LIGHTER.get(role, role)
    return role


def paint_stone(s, n, P):
    """The buildings' coursed stone on the three faces the camera sees, and a plain lit ramp with speckle on any other face."""
    face = bd.face_of(n)
    if face in ('R', 'L', 'top') and abs(n[2]) < 0.05 or face == 'top':
        role = bd.paint(s, face, P, True)
    else:
        ix, iy, iz = (int(math.floor(v * LEVEL)) for v in P)
        role = ramp_of(STONE, lum_of(n) + (noise(ix + iz, iy + iz, s.seed & 0xFFF) - 0.5) * 0.14)
    return role or 'p'


MATERIALS = {'wood': paint_wood, 'crate': paint_wood, 'stone': paint_stone, 'hay': paint_hay, 'clay': paint_plain(CLAY), 'red': paint_plain(RED), 'iron': paint_plain(IRON)}


def paint(s, n, P):
    """The palette role at P of the solid `s`, from its material; a make_rocks.Blob (natural) is painted by its own."""
    if getattr(s, 'natural', False):
        import make_rocks as mr
        return mr.paint_natural(s, n, P)
    role = MATERIALS[s.mat](s, n, P)
    deco = getattr(s, 'deco', None)
    if deco:
        role = deco(s, n, P, role) or role
    return role


# --- the picture ----------------------------------------------------------------------------------
class Scene:
    """The picture of a prop on a footprint of fx x fy cells with its highest point `zmax` levels up. `pad` more pixels each side and `up` more above (room for debris and sparks)."""

    def __init__(self, fx, fy, zmax, margin=6, pad=0, up=2, down=2):
        self.fx, self.fy = fx, fy
        self.margin = margin + pad
        self.oy = int(math.ceil(LEVEL * zmax)) + up
        self.w = 16 * (fx + fy) + 2 * self.margin
        self.h = 8 * (fx + fy) + self.oy + down
        self.ox = 16 * fy + self.margin
        self.grid = [['.'] * self.w for _ in range(self.h)]
        self.who = [[None] * self.w for _ in range(self.h)]
        self.depth = [[0.0] * self.w for _ in range(self.h)]
        self.anchor = (8 * (fx + fy) + self.margin, self.oy + 4 * (fx + fy))

    def project(self, X, Y, Z=0.0):
        """Where the point (X, Y, Z) of the prop's space lands in the picture."""
        return self.ox + 16 * (X - Y), self.oy + 8 * (X + Y) - LEVEL * Z

    def draw(self, solids, painter=paint, offset=0):
        for py in range(self.h):
            for px in range(self.w):
                sx, sy = px + 0.5, py + 0.5
                a, b = (sx - self.ox) / 16.0, (sy - self.oy) / 8.0
                origin = ((a + b) / 2, (b - a) / 2, 0.0)
                best = None
                for k, s in enumerate(solids):
                    got = s.hit(origin)
                    if got and (best is None or got[0] > best[0] + 1e-9):
                        best = (got[0], got[1], s, k)
                if best is None:
                    continue
                t, n, s, k = best
                P = (origin[0] + t, origin[1] + t, t)
                role = painter(s, n, P)
                if role:
                    self.grid[py][px] = role
                    self.who[py][px] = k + offset
                    self.depth[py][px] = P[0] + P[1] + P[2]

    def seams(self, role_steps=1, threshold=0.2):
        """A darker pixel where one solid stands well in front of another."""
        for y in range(self.h):
            for x in range(self.w):
                if self.who[y][x] is None:
                    continue
                for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                    if 0 <= nx < self.w and 0 <= ny < self.h and self.who[ny][nx] is not None and self.who[ny][nx] != self.who[y][x] and self.depth[y][x] < self.depth[ny][nx] - threshold:
                        self.grid[y][x] = tint(self.grid[y][x], role_steps)
                        break

    def pixel(self, x, y, role, under=False):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and (not under or self.grid[y][x] == '.'):
            self.grid[y][x] = role

    def ellipse(self, cx, cy, rx, ry, role, ring=True, under=True, skip=None):
        """An ellipse outline (or filled, ring=False) on the picture, only over empty pixels if `under`; `skip(angle)` says where not to draw (a ripple broken at the front)."""
        n = int(max(rx, ry) * 8) + 8
        for k in range(n):
            a = 2 * math.pi * k / n
            if skip and skip(a):
                continue
            if ring:
                self.pixel(round(cx + rx * math.cos(a)), round(cy + ry * math.sin(a)), role, under)
        if not ring:
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                        self.pixel(x, y, role, under)

    def ripple(self, X, Y, r, role='o', inner=None):
        """A ripple round a thing standing in the water at the ground point (X, Y): a ring on the water plane (an ellipse twice as wide as tall), broken in two places."""
        cx, cy = self.project(X, Y)
        self.ellipse(cx, cy, r * 16, r * 8, role, skip=lambda a: 0.3 < (a % math.pi) < 0.7, under=True)
        if inner:
            self.ellipse(cx, cy, r * 11, r * 5.5, inner, skip=lambda a: 1.0 < (a % math.pi) < 1.9, under=True)

    def finish(self, outline='O', inner_outline=False):
        """The rows with a one-pixel outline round everything painted (on the empty pixels that touch it)."""
        out = [r[:] for r in self.grid]
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] != '.':
                    continue
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < self.w and 0 <= ny < self.h and self.grid[ny][nx] != '.':
                        out[y][x] = outline
                        break
        return [''.join(r) for r in out]


def top_cover(solids, cells, h, n=8):
    """For each cell, the share of its area (n x n samples) where the visible top is the flat plane z = h: a unit can stand there. {(i, j): 0..1}."""
    out = {}
    for i, j in sorted(cells):
        got = 0
        for a in range(n):
            for b in range(n):
                x, y = i + (a + 0.5) / n, j + (b + 0.5) / n
                best = None
                for s in solids:
                    g = s.hit((x - h, y - h, 0.0))
                    if g and (best is None or g[0] > best[0]):
                        best = g
                got += bool(best and abs(best[0] - h) < 1e-6 and best[1][2] > 0.99)
        out[(i, j)] = got / (n * n)
    return out


def rows_to_image(rows, rgb, scale=1):
    from PIL import Image
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST) if scale != 1 else im


def role_rgb():
    import extract_poses as ep
    return {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
