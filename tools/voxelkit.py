#!/usr/bin/env python3
"""A small voxel renderer in the ground tiles' projection, for pieces that are not convex (arched bridges, stairs, a bridge with a hole in it).

The scene is a grid of voxels, 16 to a ground cell and 16 to a level (so a voxel is one pixel high, and one pixel across the projection). x runs down and to the right,
y down and to the left, z up, exactly as in tools/buildings.py: a screen point is  sx = 16 * (X - Y) + OFFSET_X,  sy = 8 * (X + Y) - 16 * Z + OFFSET_Y  (X, Y, Z in cells),
and a pixel's ray is every point (X + t, Y + t, t), walked here from the top of the scene down through the voxels. The first filled voxel it enters is what the pixel
shows, and the face it entered by (z the top, x the wall that faces down-right, y the wall that faces down-left) says how it is lit, as in buildings.paint.

A `Scene` holds a material number per voxel (0 is empty) with a few voxels of padding round the footprint (for overhangs). A painter turns (material, face, voxel) into a palette
role. `render` returns the picture as rows of roles with a one-pixel outline round it, and the anchor at the middle of the footprint on the ground, as the rocks and buildings do.
"""
import math

from buildings import STONE as BD_STONE, hashed

PX = 16                  # voxels to a cell, and to a level
MARGIN = 6               # pixels of room each side of the footprint
PAD = 4                  # voxels of padding round the footprint, for things that overhang it

M_STONE, M_DECK, M_PARAPET, M_RING_A, M_RING_B, M_RUBBLE, M_MORTAR = 1, 2, 3, 4, 5, 6, 7
M_PLANK, M_BEAM, M_POST, M_ROPE = 10, 11, 12, 13
M_VINE, M_STALK, M_CAP, M_SPOT = 20, 21, 22, 23
WALK_MATS = (M_DECK, M_PLANK)          # what a unit can stand on


class Scene:
    """Voxels of a footprint of fx x fy cells and nz levels of voxels high. Coordinates are the footprint's own, 0 to 16 * fx and 16 * fy, padding allowed on each side."""

    def __init__(self, fx, fy, nz):
        self.fx, self.fy, self.nz = fx, fy, nz
        self.W, self.D = fx * PX, fy * PX
        self.nxa, self.nya = self.W + 2 * PAD, self.D + 2 * PAD
        self.data = bytearray(self.nxa * self.nya * nz)
        self.top = 0

    def idx(self, i, j, k):
        return ((k * self.nya) + (j + PAD)) * self.nxa + (i + PAD)

    def get(self, i, j, k):
        if k < 0 or k >= self.nz or i < -PAD or j < -PAD or i >= self.W + PAD or j >= self.D + PAD:
            return 0
        return self.data[self.idx(i, j, k)]

    def set(self, i, j, k, m):
        if 0 <= k < self.nz and -PAD <= i < self.W + PAD and -PAD <= j < self.D + PAD:
            self.data[self.idx(i, j, k)] = m
            if m and k + 1 > self.top:
                self.top = k + 1

    def box(self, i0, i1, j0, j1, k0, k1, m):
        for k in range(k0, k1):
            for j in range(j0, j1):
                for i in range(i0, i1):
                    self.set(i, j, k, m)


def hrole(i, j, k, salt=0, mod=65536):
    return hashed((i * 7 + k * 131) & 0xFFFF, (j * 11 + k * 17 + salt) & 0xFFFF, salt) % mod


# --- the stone: the buildings' own courses, with a palette to choose --------------------------------------
PAL = BD_STONE


def stone_role(pal, face, a, b):
    """Coursed stone as buildings.stone draws it (4 pixel courses, blocks 8 wide, every other course shifted half a block), in the palette `pal` (a table like buildings.STONE)."""
    s = pal[face]
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


def face_coords(face, i, j, k):
    """Texture coordinates for a voxel's visible face, as buildings.paint takes them: along the wall and up it, or across the top."""
    if face == 'x':
        return j, k
    if face == 'y':
        return i, k
    return i, j


# --- rendering ---------------------------------------------------------------------------------------
def render(scene, painter, margin=MARGIN):
    """(rows, anchor): the picture of the scene as palette roles with an outline, and the anchor (the middle of the footprint on the ground), in pixels."""
    fx, fy = scene.fx, scene.fy
    zmax = scene.top
    w = 16 * (fx + fy) + 2 * margin
    oy = zmax + 4
    h = 8 * (fx + fy) + oy + 2
    ox = 16 * fy + margin
    nxa, nya, nz = scene.nxa, scene.nya, scene.nz
    data = scene.data
    grid = [['.'] * w for _ in range(h)]
    eps_x, eps_y = 1.1e-6, 2.3e-6
    for py in range(h):
        sy = py + 0.5 - oy
        for px in range(w):
            sx = px + 0.5 - ox
            a, b = sx / 16.0, sy / 8.0
            ox_v = 8.0 * (a + b) + PAD + eps_x                    # the ray's x and y at z = 0, in array voxels
            oy_v = 8.0 * (b - a) + PAD + eps_y
            s = min(float(zmax), nxa - ox_v, nya - oy_v)
            if s <= 0:
                continue
            ci, cj, ck = int(math.floor(ox_v + s - 1e-9)), int(math.floor(oy_v + s - 1e-9)), int(math.ceil(s)) - 1
            if ck >= nz:
                ck = nz - 1
            face = 'z'
            while True:
                if 0 <= ci < nxa and 0 <= cj < nya and ck >= 0:
                    m = data[(ck * nya + cj) * nxa + ci]
                    if m:
                        grid[py][px] = painter(m, face, ci - PAD, cj - PAD, ck)
                        break
                sx_ = ci - ox_v
                sy_ = cj - oy_v
                sz_ = float(ck)
                if sz_ >= sx_ and sz_ >= sy_:
                    ck -= 1
                    face = 'z'
                elif sx_ >= sy_:
                    ci -= 1
                    face = 'x'
                else:
                    cj -= 1
                    face = 'y'
                if ck < 0 or ci < 0 or cj < 0:
                    break
    out = [r[:] for r in grid]
    for y in range(h):
        for x in range(w):
            if grid[y][x] != '.':
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] != '.':
                    out[y][x] = 'O'
                    break
    return [''.join(r) for r in out], (8 * (fx + fy) + margin, oy + 4 * (fx + fy))


def column_top(scene, i, j):
    """(height, material) of the highest voxel in the column (i, j), or (0, 0)."""
    for k in range(scene.nz - 1, -1, -1):
        m = scene.get(i, j, k)
        if m:
            return k + 1, m
    return 0, 0


def walk_cover(scene, cells, walk_mats=WALK_MATS):
    """For every cell (ci, cj) of the footprint, the share of its 16 x 16 columns whose top voxel is something a unit can stand on, as {(ci, cj): 0..1}."""
    out = {}
    for ci, cj in sorted(cells):
        n = 0
        for j in range(cj * PX, cj * PX + PX):
            for i in range(ci * PX, ci * PX + PX):
                if column_top(scene, i, j)[1] in walk_mats:
                    n += 1
        out[(ci, cj)] = n / float(PX * PX)
    return out


def lip_is_exposed(scene, i, j, k):
    """Whether a top voxel has lower ground (or nothing) just beyond it on the side the camera sees (+x or +y): the edge that catches the light."""
    return scene.get(i + 1, j, k) == 0 and scene.get(i, j + 1, k) == 0 or scene.get(i + 1, j, k) == 0 or scene.get(i, j + 1, k) == 0


def moss_role(face, r):
    """A moss colour for a voxel: lit on top, deep on the shaded wall."""
    if face == 'z':
        return 'z' if r % 3 == 0 else 'A'
    return 'A' if face == 'x' else 'B'


# --- a preview sheet shared by the families built on this --------------------------------------------------
def sheet(pieces, path, scale=2, width=1500, title=None):
    """Every piece enlarged on its footprint's cells, labelled with its id, WALK if it is walkable and its smallest cell cover. A piece is a dict with id, rows, anchor,
    size (fx, fy), cells, walkable, cover ({cell: share}); the rest is ignored."""
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    margin, x, y, rowh = 14, 14, 24, 0
    placed = []
    for p in pieces:
        w, h = len(p['rows'][0]) * scale, len(p['rows']) * scale + 26
        if x + w > width - margin:
            x, y, rowh = margin, y + rowh + 12, 0
        placed.append((p, x, y))
        x += max(w, 110) + 16
        rowh = max(rowh, h)
    img = Image.new('RGBA', (width, y + rowh + 20), (30, 34, 56, 255))
    d = ImageDraw.Draw(img)
    if title:
        d.text((14, 6), title, fill=(230, 220, 200, 255))
    for p, x, y in placed:
        rows = p['rows']
        fx, fy = p['size']
        ax, ay = p['anchor']
        top = y + 14
        ox = 16 * fy + MARGIN
        oy = ay - 4 * (fx + fy)
        for i, j in p['cells']:
            pts = [(ox + 16 * (X - Y), oy + 8 * (X + Y)) for X, Y in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            d.polygon([(x + a * scale, top + b * scale) for a, b in pts], fill=(70, 110, 70, 255) if p['walkable'] else (90, 70, 70, 255), outline=(0, 0, 0, 90))
        im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
        for yy, row in enumerate(rows):
            for xx, c in enumerate(row):
                if c != '.':
                    im.putpixel((xx, yy), rgb[c] + (255,))
        img.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, top))
        cover = min(p['cover'].values()) if p['cover'] else 0
        d.text((x, y), f"{p['id'].replace('bridge-', '').replace('stair-', 's-')} {'WALK' if p['walkable'] else 'no'} {cover:.2f}", fill=(230, 220, 200, 255))
    img.save(path)
