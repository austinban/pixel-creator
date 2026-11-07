#!/usr/bin/env python3
"""The corrupted ground: the grass and water tile sets again, rotted. Teal and purple turf and soil, a murky glowing water, with mushrooms, hanging vines, thorny things and the odd pair of eyes.

sprites/assets/ground.png is a sheet of 32 x 32 cells, one tile or prop per cell. This makes sprites/assets/ground-corrupted.png in the same layout, cell for cell, so a tile has the same shape and
the same place on the sheet in both sets and the two can be swapped in a map. It is made from the original sheet (recoloured by role, and then drawn on), so a changed original comes through.

    1  recolour    by role: turf from green to teal with lavender patches, soil from orange and coral to plum and purple, water from blue to a deep teal, wood to a bruised grey-purple
    2  decorate    only on tiles that are full blocks, so a slope or an edge piece keeps its clean outline: mushrooms on the top, vines over the sides, a few pairs of glowing eyes in the dirt
    3  props       the bush, pine, stump, logs and rocks the same way, and the flowers become mushroom clusters

The crates, fences, stairs and the faint shadow sprites are not part of it. Assets are built from the sheet by make_ground.py (ids ground-corrupted-COL-ROW, categories 'Corrupted Grass', 'Corrupted Water'...).

    python3 tools/make_corrupted_ground.py                        write sprites/assets/ground-corrupted.png
    python3 tools/make_corrupted_ground.py --preview previews/ground-corrupted.png        the original and the corrupted set side by side, enlarged
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
from fx import hashed  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / 'sprites' / 'assets' / 'ground.png'
SHEET = ROOT / 'sprites' / 'assets' / 'ground-corrupted.png'
CELL = 32

# --- which cell is what ----------------------------------------------------------------------
BUSH, PINE, STUMP = (0, 3), (1, 3), (1, 5)
ROCKS = [(0, 4), (0, 5)]
LOGS = [(0, 6), (1, 6), (0, 7), (0, 8), (1, 8), (1, 9)]
FLOWERS = [(2, 8), (4, 8)]
WATER_CELLS = {(c, r) for c in range(2, 8) for r in range(2, 5)} | {(0, 2), (1, 2)}
SKIPPED = {(c, r) for c in range(0, 2) for r in (1,) if c < 2 and r == 1 and (c, r) in ((0, 1), (1, 1))}      # the stairs
SKIPPED |= {(c, r) for c in range(2, 8) for r in range(5, 10)} - set(FLOWERS)                                # crates and fences
SKIPPED |= {(c, r) for c in range(0, 8) for r in range(10, 13)}                                              # the faint shadows
PROP_CELLS = {BUSH, (1, 3), (1, 4), STUMP, *ROCKS, *LOGS, *FLOWERS}

# --- recolouring, by role --------------------------------------------------------------------
TILE_MAP = {'z': 's', 'A': 's', 'B': 'D', 'd': 'r', 'b': 'f', 'a': 'g', 'e': 'u', 'f': 'w', 'g': 'x'}
WATER_MAP = {'n': 'q', 'o': 's', 'm': 's', 'k': 'D', 'r': 'r', 't': 'v', 'A': 's', 'B': 'k', 'g': 'x'}      # a teal top with darker rings; the sides dark teal, the shaded one the abyss teal role (D)
TREE_MAP = {'A': 'q', 'B': 's', 's': 'w', 'k': 'x', 'g': 'x', 'f': 'w', 'a': 'u', 'e': 'u'}
WOOD_MAP = {'a': 'l', 'e': 'g', 'f': 'u', 'g': 'w', 'k': 'x'}
STUMP_MAP = {'a': 'g', 'e': 'u', 'f': 'w', 'b': 'f', 'm': 'u', 'n': 'l', 'o': 'q', 'k': 'w', 'A': 's', 'B': 'k', 's': 'w', 'h': 'x', 'g': 'x'}
ROCK_MAP = {'l': 'l', 'q': 'q', 'p': 'p', 'k': 'k', 'r': 'r'}

CAPS = {                                  # cap: light, base, shade, deep
    'teal': ('r', 'q', 's', 'k'),
    'violet': ('v', 'f', 'u', 'w'),
    'pink': ('j', 'i', 'h', 'u'),
}
STEM = ('t', 'r', 'p')


def rgb_roles():
    return {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): c for c, _, _, _, h in ep.ROLES}


class Sheet:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [['.'] * w for _ in range(h)]

    def get(self, x, y):
        return self.rows[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def put(self, x, y, c, box=None, only_on=False):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if box and not (box[0] <= x < box[2] and box[1] <= y < box[3]):
            return
        if only_on and self.rows[y][x] == '.':
            return
        self.rows[y][x] = c


# --- small things to draw ---------------------------------------------------------------------
def mushroom(s, x, y, size, kind, box, glow=True):
    """A mushroom standing with its stem foot at (x, y). size 1 is a few pixels across, 2 and 3 are bigger. A dark underside, a pale stem and a spotted cap, lit from the upper left."""
    hi, base, shade, deep = CAPS[kind]
    stem_h, cap_w, cap_h = {1: (2, 5, 3), 2: (3, 7, 4), 3: (4, 9, 5)}[size]
    stem_w = 1 if size == 1 else 2
    for k in range(stem_h):
        for i in range(stem_w):
            s.put(x - stem_w // 2 + i, y - k, STEM[0] if i == 0 else STEM[1], box)
    s.put(x, y + 1, 'x', box) if size > 1 else None
    top = y - stem_h
    for j in range(cap_h):
        # a dome: wide at the bottom, narrowing to the top
        t = j / max(1, cap_h - 1)
        half = (cap_w / 2) * math.sqrt(max(0.0, 1 - ((cap_h - 1 - j) / cap_h) ** 2)) + 0.4
        for i in range(-int(half), int(half) + 1):
            tone = hi if (i < -half * 0.35 and j < cap_h - 1) else base if i < half * 0.45 else shade
            if j == cap_h - 1:
                tone = deep                                          # the underside of the cap
            s.put(x + i, top - (cap_h - 1 - j), tone, box)
    if size >= 2:
        s.put(x - 1, top - cap_h + 2, 't', box)                     # the spots
        if size == 3:
            s.put(x + 2, top - cap_h + 3, 't', box)
            s.put(x - 3, top - 1, 't', box)
        else:
            s.put(x + 1, top - 1, 't', box)
    if glow:
        s.put(x + cap_w // 2 + 1, top - cap_h, 'r', box)             # a spore drifting off the cap


def vine(s, x, y0, length, box, seed=0):
    """A vine hanging down over a side face from (x, y0): dark teal with a lit edge, small violet leaves and a thorn or two. It is drawn only on what is already painted, so the tile's outline holds."""
    phase = hashed(x, y0, seed) * 6
    for k in range(length):
        dx = int(round(math.sin(k * 0.8 + phase) * 1.1))
        c = 's' if k % 3 else 'q'
        s.put(x + dx, y0 + k, c, box, only_on=True)
        s.put(x + dx + 1, y0 + k, 'k', box, only_on=True)
        if k % 4 == 2:
            s.put(x + dx - 1, y0 + k, 'v', box, only_on=True)         # a leaf
            s.put(x + dx - 2, y0 + k - 1, 'f', box, only_on=True)
        if k % 5 == 4:
            s.put(x + dx + 2, y0 + k, 'x', box, only_on=True)         # a thorn
    s.put(x + int(round(math.sin(length * 0.8 + phase) * 1.1)), y0 + length, 'x', box, only_on=True)


def eyes(s, x, y, box):
    """A pair of glowing eyes looking out of the dirt, in a little dark hollow."""
    for dx in range(-2, 5):
        for dy in (-1, 0, 1):
            s.put(x + dx, y + dy, 'x', box, only_on=True)
    for dx in (0, 3):
        s.put(x + dx, y, 'o' if hashed(x, y) < 0.5 else 'j', box, only_on=True)


def spores(s, cx, cy, n, box, seed):
    for k in range(n):
        a = hashed(cx, cy, seed + k) * 6.28
        d = 3 + hashed(cx, cy, seed + 40 + k) * 6
        s.put(int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.6), 'r' if k % 2 else 'v', box)


# --- tiles ------------------------------------------------------------------------------------
def inside_top(lx, ly, shrink=0.75):
    """Is this point (in a cell) on the top face of a full block? The top is a diamond 32 wide and 16 tall."""
    return abs(lx + 0.5 - 16) / 16 + abs(ly + 0.5 - 8) / 8 <= shrink


def rim(lx):
    """Where the top face ends and the side begins, for a block, at this column of the cell."""
    return int(16 - abs(lx + 0.5 - 16) / 2)


def is_full_block(s, ox, oy):
    return all(s.get(ox + x, oy + y) != '.' for x, y in ((16, 1), (16, 30), (2, 12), (29, 12), (2, 22), (29, 22)))


def recolour(orig, out, c, r, mapping):
    ox, oy = c * CELL, r * CELL
    height = CELL * 2 if (c, r) in ((1, 3),) else CELL
    for y in range(height):
        for x in range(CELL):
            ch = orig.get(ox + x, oy + y)
            if ch == '.':
                continue
            out.put(ox + x, oy + y, mapping.get(ch, ch))


def patch_turf(out, orig, ox, oy, to=None, salt=0):
    """Soft blotches of a slightly darker teal and the odd bright glint over the turf (repeating every 16 pixels, so tiles still line up). Kept quiet on purpose: the top of a grass tile is the most-seen
    surface in a map, so it is low in contrast (the lime highlights of the original are the base teal here, the dark flecks and the blotches are one step darker).
    `to` is the cell's corner to draw them at, if it is not where the original is read (the plain blocks); `salt` makes another pattern."""
    tx, ty = to or (ox, oy)
    for y in range(CELL):
        for x in range(CELL):
            if orig.get(ox + x, oy + y) != 'A':
                continue
            u = hashed((x % 16) // 3, (y % 16) // 3, 5 + salt)
            if u < 0.2:
                out.put(tx + x, ty + y, 'D')
            elif hashed(x % 16, y % 16, 9 + salt) < 0.015:
                out.put(tx + x, ty + y, 'q')


# Plain grass: the (0, 0) block with no mushrooms, vines, thorns or eyes, in three turf patterns, in cells that were empty. The game lays these as everyday
# grass and keeps the (0, 0) block, mushrooms and all, as the occasional accent.
CLEAN_GRASS = [(4, 11), (5, 11), (6, 11)]
CLEAN_SOURCE = (0, 0)


def plain_grass(out, orig):
    sc, sr = CLEAN_SOURCE
    for k, (c, r) in enumerate(CLEAN_GRASS):
        for y in range(CELL):
            for x in range(CELL):
                ch = orig.get(sc * CELL + x, sr * CELL + y)
                if ch != '.':
                    out.put(c * CELL + x, r * CELL + y, TILE_MAP.get(ch, ch))
        patch_turf(out, orig, sc * CELL, sr * CELL, to=(c * CELL, r * CELL), salt=101 + 17 * k)


def decorate_tile(out, orig, c, r, water):
    ox, oy = c * CELL, r * CELL
    box = (ox, oy, ox + CELL, oy + CELL)
    if not is_full_block(orig, ox, oy):
        return
    seed = c * 31 + r * 17
    roll = hashed(c, r, 3)
    # mushrooms on the top face
    if not water:
        count = 0 if roll < 0.18 else 1 if roll < 0.45 else 2 if roll < 0.78 else 3
        placed = []
        tries = 0
        while len(placed) < count and tries < 30:
            tries += 1
            lx = int(6 + hashed(c, r, 20 + tries) * 20)
            ly = int(4 + hashed(c, r, 60 + tries) * 9)
            if not inside_top(lx, ly, 0.62) or any(abs(lx - px) + abs(ly - py) < 8 for px, py in placed):
                continue
            pick = hashed(c, r, 90 + tries)
            size = 1 if pick < 0.3 else 2 if pick < 0.75 else 3
            if ly < {1: 5, 2: 7, 3: 9}[size] or (size == 3 and abs(lx - 16) > 7):
                continue
            placed.append((lx, ly))
            kind = ('teal', 'violet', 'teal', 'pink')[int(hashed(c, r, 120 + tries) * 4)]
            mushroom(out, ox + lx, oy + ly, size, kind, box)
        if roll > 0.9:
            spores(out, ox + 16, oy + 6, 3, box, seed)
    else:
        # the water: a fungal pad with a mushroom on it, and glints
        if roll < 0.5:
            px, py = int(9 + hashed(c, r, 4) * 14), int(7 + hashed(c, r, 5) * 4)
            if inside_top(px, py, 0.55):
                for dx in range(-3, 4):
                    for dy in (0, 1):
                        if abs(dx) < 3 or dy == 1:
                            out.put(ox + px + dx, oy + py + dy, 'q' if dy == 0 else 's', box, only_on=True)
                mushroom(out, ox + px, oy + py, 1, 'violet', box)
        for k in range(3):
            gx, gy = int(7 + hashed(c, r, 30 + k) * 18), int(3 + hashed(c, r, 33 + k) * 10)
            if inside_top(gx, gy, 0.7):
                out.put(ox + gx, oy + gy, 'r', box, only_on=True)
    # thorns: a few dark spikes standing on the top
    if not water and hashed(c, r, 15) < 0.4:
        for k in range(2):
            tx, ty = int(8 + hashed(c, r, 16 + k) * 16), int(8 + hashed(c, r, 18 + k) * 5)
            if inside_top(tx, ty, 0.6):
                for j in range(4):
                    out.put(ox + tx, oy + ty - j, 'x' if j < 3 else 'l', box)
                out.put(ox + tx + 1, oy + ty, 'k', box)
    # vines over the sides (not on water: it has none)
    side_roll = hashed(c, r, 7)
    for k in range(0 if water else 2):
        if side_roll < (0.62 if k == 0 else 0.34):
            x = int(4 + hashed(c, r, 70 + k) * 24)
            vine(out, ox + x, oy + rim(x) + 1, int(6 + hashed(c, r, 80 + k) * 9), box, seed + k)
    # a pair of eyes in the dirt
    if not water and hashed(c, r, 11) < 0.2:
        x = int(6 + hashed(c, r, 12) * 6) if hashed(c, r, 13) < 0.5 else int(18 + hashed(c, r, 14) * 6)
        eyes(out, ox + x, oy + rim(x) + 9, box)


# --- props ------------------------------------------------------------------------------------
def clear(out, ox, oy, h=CELL):
    for y in range(oy, oy + h):
        for x in range(ox, ox + CELL):
            out.rows[y][x] = '.'


def decorate_props(out, orig):
    def box_of(c, r, h=CELL):
        return (c * CELL, r * CELL, c * CELL + CELL, r * CELL + h)
    # the bush: thorny, with glowing berries and a couple of mushrooms at its foot
    ox, oy = BUSH[0] * CELL, BUSH[1] * CELL
    b = box_of(*BUSH)
    for k in range(9):
        x, y = int(7 + hashed(1, k, 1) * 18), int(8 + hashed(2, k, 1) * 15)
        if out.get(ox + x, oy + y) != '.':
            out.put(ox + x, oy + y, 'j' if k % 3 else 'y', b)
            out.put(ox + x + 1, oy + y, 'h', b, only_on=True)
    for x, y, kind in ((7, 29, 'teal'), (24, 30, 'violet')):
        mushroom(out, ox + x, oy + y, 1, kind, b)
    for x in (9, 17, 23):                                                 # thorns sticking out of the top
        out.put(ox + x, oy + 4 + int(hashed(x, 1) * 3), 'x', b, only_on=False)
    # the pine: vines hanging from its branches, and mushrooms round the roots
    ox, oy = PINE[0] * CELL, PINE[1] * CELL
    b = box_of(PINE[0], PINE[1], CELL * 2)
    for x, y0, n in ((9, 30, 9), (22, 34, 7), (16, 40, 6)):
        vine(out, ox + x, oy + y0, n, b, 3)
    for x, y, size, kind in ((6, 59, 2, 'violet'), (26, 60, 1, 'teal'), (22, 61, 1, 'pink')):
        mushroom(out, ox + x, oy + y, size, kind, b)
    # the stump: a ring of mushrooms on its top
    ox, oy = STUMP[0] * CELL, STUMP[1] * CELL
    b = box_of(*STUMP)
    for x, y, size, kind in ((10, 14, 1, 'teal'), (20, 13, 2, 'violet'), (15, 18, 1, 'pink'), (25, 19, 1, 'teal')):
        mushroom(out, ox + x, oy + y, size, kind, b)
    # the logs: shelves of bracket fungus along them
    for c, r in LOGS:
        ox, oy = c * CELL, r * CELL
        b = box_of(c, r)
        for k in range(3):
            x, y = int(7 + hashed(c, r, 50 + k) * 16), int(9 + hashed(c, r, 55 + k) * 10)
            if out.get(ox + x, oy + y) == '.':
                continue
            for dx in range(-2, 3):
                out.put(ox + x + dx, oy + y, 'v' if dx < 0 else 'f', b)
                if abs(dx) < 2:
                    out.put(ox + x + dx, oy + y + 1, 'u', b)
            out.put(ox + x - 1, oy + y, 't', b)
    # the rocks: moss on top and a couple of mushrooms
    for c, r in ROCKS:
        ox, oy = c * CELL, r * CELL
        b = box_of(c, r)
        for k in range(14):
            x, y = int(7 + hashed(c, r, 40 + k) * 18), int(6 + hashed(c, r, 44 + k) * 12)
            if out.get(ox + x, oy + y) not in ('.', 'k'):
                out.put(ox + x, oy + y, 's' if k % 3 else 'q', b)
        mushroom(out, ox + 8, oy + 29, 1, 'teal', b)
        mushroom(out, ox + 25, oy + 28, 1, 'violet', b)
    # the flowers become little clusters of mushrooms
    for (c, r), kinds in zip(FLOWERS, (('teal', 'violet', 'teal'), ('violet', 'pink', 'violet'))):
        ox, oy = c * CELL, r * CELL
        b = box_of(c, r)
        clear(out, ox, oy)
        for x, y, size, kind in ((10, 24, 3, kinds[0]), (21, 25, 2, kinds[1]), (16, 28, 1, kinds[2])):
            mushroom(out, ox + x, oy + y, size, kind, b)
        spores(out, ox + 15, oy + 17, 3, b, 7)


# --- the sheet --------------------------------------------------------------------------------
def load_roles(path):
    from PIL import Image
    rev = rgb_roles()
    near = {}
    im = Image.open(path).convert('RGBA')
    s = Sheet(im.width, im.height)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] < 128:
                continue
            if p[:3] not in rev:
                if p[:3] not in near:
                    near[p[:3]] = rev[min(rev, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, p[:3])))]
                s.rows[y][x] = near[p[:3]]
            else:
                s.rows[y][x] = rev[p[:3]]
    return s


def build():
    orig = load_roles(ORIGINAL)
    out = Sheet(orig.w, orig.h)
    cols, rows = orig.w // CELL, orig.h // CELL
    for r in range(rows):
        for c in range(cols):
            cell = (c, r)
            if cell in SKIPPED:
                continue
            if cell in PROP_CELLS:
                if cell == (1, 4):
                    continue                                              # the lower half of the pine, done with the upper
                mapping = WOOD_MAP if cell in LOGS else TREE_MAP if cell in (BUSH, (1, 3)) else STUMP_MAP if cell == STUMP else ROCK_MAP if cell in ROCKS else TILE_MAP
                if cell not in FLOWERS:
                    recolour(orig, out, c, r, mapping)
                if cell == (1, 3):
                    recolour(orig, out, 1, 4, TREE_MAP)
                continue
            water = cell in WATER_CELLS
            recolour(orig, out, c, r, WATER_MAP if water else TILE_MAP)
            if not water:
                patch_turf(out, orig, c * CELL, r * CELL)
    for r in range(rows):
        for c in range(cols):
            cell = (c, r)
            if cell in SKIPPED or cell in PROP_CELLS:
                continue
            decorate_tile(out, orig, c, r, cell in WATER_CELLS)
    decorate_props(out, orig)
    plain_grass(out, orig)
    return out


def save(sheet, path):
    from PIL import Image
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    im = Image.new('RGBA', (sheet.w, sheet.h), (0, 0, 0, 0))
    for y in range(sheet.h):
        for x in range(sheet.w):
            c = sheet.rows[y][x]
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    im.save(path)
    return im


def preview(path, scale=2):
    from PIL import Image
    new = Image.open(SHEET).convert('RGBA')
    old = Image.open(ORIGINAL).convert('RGBA')
    w, h = old.size
    sheet = Image.new('RGBA', (w * scale * 2 + 24, h * scale + 16), (44, 40, 70, 255))
    for k, im in enumerate((old, new)):
        sheet.alpha_composite(im.resize((w * scale, h * scale), Image.NEAREST), (8 + k * (w * scale + 8), 8))
    sheet.save(path)


_made = False


def ensure_sheet():
    """Make ground-corrupted.png from the original sheet (once a run): make_assets.py calls this so the corrupted set always follows the original and the palette."""
    global _made
    if not _made:
        save(build(), SHEET)
        _made = True


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    save(build(), SHEET)
    print('wrote', SHEET)
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
