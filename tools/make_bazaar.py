#!/usr/bin/env python3
"""The bazaar: a shop seen from the inside, as a single 256 x 256 asset floating in the air like the ground tiles.

A cut-away room in the ground's own projection (16 pixels across and 8 down a cell): a 7 x 7 cell wooden floor on a slab of the ground's clay, two back walls, the front and the sides
open to the camera, and the slab narrowing underneath into a hanging rock. The wares are the game's own items: the weapon icons hang on the left wall and stand in barrels, the amulets hang on
the right wall, and the crystals, rocks and arrows (the sheets in sprites/assets) lie on the counter and the tables, at half size, with potions, books and scrolls drawn here.

    python3 tools/make_bazaar.py --preview previews/bazaar.png        the shop, once as it is and once enlarged
    python3 tools/make_bazaar.py --png previews/bazaar-plain.png      write the 256 x 256 image alone (make_assets.py builds it as sprites/assets/bazaar-shop.png)
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
from fx import Grid, hashed, rgb_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'sprites' / 'assets'
SIZE = 256
CX, YB = 128, 92               # the back corner of the floor
N = 7                          # the floor is 7 x 7 cells
SPAN = N * 16                  # 112 world units a side
WALL = 84                      # how high the back walls stand
SLAB = 14                      # how thick the floor slab is
TIP = 252                      # the lowest point of the rock underneath

WOOD = {'top': ('b', 'a', 'e'), 'right': ('a', 'e', 'f'), 'left': ('e', 'f', 'g')}      # a box's three faces: base, alt, line


def screen(wx, wy, z=0):
    return CX + (wx - wy), YB + (wx + wy) / 2 - z


# --- drawing ------------------------------------------------------------------------------------
class Layer(Grid):
    def __init__(self):
        super().__init__(SIZE, SIZE)

    def polygon(self, pts, fn):
        from PIL import Image, ImageDraw
        mask = Image.new('L', (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in pts], fill=255)
        px = mask.load()
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for y in range(max(0, int(min(ys)) - 1), min(SIZE, int(max(ys)) + 2)):
            for x in range(max(0, int(min(xs)) - 1), min(SIZE, int(max(xs)) + 2)):
                if px[x, y]:
                    c = fn(x + 0.5, y + 0.5)
                    if c:
                        self.rows[y][x] = c

    def outline(self, c='O'):
        """A one-pixel outline round whatever is drawn here."""
        edge = []
        for y in range(SIZE):
            for x in range(SIZE):
                if self.rows[y][x] == '.':
                    if any(0 <= x + dx < SIZE and 0 <= y + dy < SIZE and self.rows[y + dy][x + dx] != '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        edge.append((x, y))
        for x, y in edge:
            self.rows[y][x] = c

    def over(self, other):
        for y in range(SIZE):
            row, src = self.rows[y], other.rows[y]
            for x in range(SIZE):
                if src[x] != '.':
                    row[x] = src[x]


def pick(ramp_or_pair, a, b, size=4, line=None, offset=0):
    """Planks or bricks: alternate two tones in strips of `size` along `a`, a line between."""
    base, alt, edge = ramp_or_pair
    k = int(math.floor((a + offset) / size))
    if (a + offset) - k * size < 1 and line is not False:
        return edge
    return base if (k + int(hashed(k, 3)) * 0) % 2 == 0 and hashed(k, int(b // 9), 5) < 0.7 else alt


def box(layer, wx0, wy0, wx1, wy1, z0, z1, ramps=WOOD, pattern='planks', top_pattern='planks'):
    """An upright box on the floor: a lit right face, a shaded left face and a top, each a plank or a plain tone."""
    def face_fn(ramp, kind):
        base, alt, line = ramp

        def fn(X, Y):
            if kind == 'right':
                u = wy1 - (X - CX)
                v = YB + (wx1 + u) / 2 - Y - z0
            elif kind == 'left':
                u = (X - CX) + wy1 if False else (X - CX) + wy1
                v = YB + (u + wy1) / 2 - Y - z0
            else:
                zz = z1
                u = (X - CX) / 2 + (Y - YB + zz)
                v = (Y - YB + zz) - (X - CX) / 2
            if pattern == 'plain' and kind != 'top':
                return base
            if kind == 'top':
                return pick(ramp, v, u, 4) if top_pattern == 'planks' else base
            return pick(ramp, u, v, 5)
        return fn
    layer.polygon([screen(wx1, wy0, z1), screen(wx1, wy1, z1), screen(wx1, wy1, z0), screen(wx1, wy0, z0)], face_fn(ramps['right'], 'right'))
    layer.polygon([screen(wx0, wy1, z1), screen(wx1, wy1, z1), screen(wx1, wy1, z0), screen(wx0, wy1, z0)], face_fn(ramps['left'], 'left'))
    layer.polygon([screen(wx0, wy0, z1), screen(wx1, wy0, z1), screen(wx1, wy1, z1), screen(wx0, wy1, z1)], face_fn(ramps['top'], 'top'))


def sprite_of(path):
    """A PNG of the game's own as rows of roles."""
    from PIL import Image
    rev = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): c for c, _, _, _, h in ep.ROLES}
    im = Image.open(path).convert('RGBA')
    return [[rev.get(im.getpixel((x, y))[:3], 'O') if im.getpixel((x, y))[3] > 127 else '.' for x in range(im.width)] for y in range(im.height)]


def crop(rows, x0, w):
    return [r[x0:x0 + w] for r in rows]


def half(rows):
    """Half size: each 2 x 2 block becomes the commonest tone in it (the outline only when nothing else is there)."""
    out = []
    for y in range(0, len(rows) - 1, 2):
        line = []
        for x in range(0, len(rows[0]) - 1, 2):
            block = [rows[y + j][x + i] for j in (0, 1) for i in (0, 1) if rows[y + j][x + i] != '.']
            if len(block) < 2:
                line.append('.')
                continue
            body = [c for c in block if c != 'O'] or block
            line.append(max(sorted(set(body)), key=body.count))
        out.append(line)
    return out


def scaled(rows, num, den):
    """Smaller by num / den (nearest pixel), keeping the outline whole: a pixel whose neighbour was dropped is not left without its outline."""
    h, w = len(rows), len(rows[0])
    H, W = h * num // den, w * num // den
    out = [[rows[min(h - 1, int((y + 0.5) * den / num))][min(w - 1, int((x + 0.5) * den / num))] for x in range(W)] for y in range(H)]
    lay = Layer()
    stamp(lay, out, 4, 4)
    lay.outline()
    return lay.rows


def shrink(rows, num, den):
    """Smaller by num / den, each new pixel taking the commonest tone of the block it covers (the outline is redrawn after), so small shapes keep their colours."""
    h, w = len(rows), len(rows[0])
    H, W = -(-h * num // den), -(-w * num // den)
    out = []
    for y in range(H):
        line = []
        for x in range(W):
            ys, xs = range(int(y * den / num), min(h, int(-(-(y + 1) * den // num)))), range(int(x * den / num), min(w, int(-(-(x + 1) * den // num))))
            block = [rows[j][i] for j in ys for i in xs if rows[j][i] != '.']
            body = [c for c in block if c != 'O']
            if len(block) * 2 < len(ys) * len(xs) or not body:
                line.append('.')
            else:
                line.append(max(sorted(set(body)), key=body.count))
        out.append(line)
    lay = Layer()
    stamp(lay, out, 4, 4)
    lay.outline()
    return lay.rows


def trim(rows):
    ys = [y for y, r in enumerate(rows) if any(c != '.' for c in r)]
    xs = [x for r in rows for x, c in enumerate(r) if c != '.']
    return [r[min(xs):max(xs) + 1] for r in rows[min(ys):max(ys) + 1]]


def stamp(layer, rows, x, y):
    """Rows of roles with their top left at (x, y)."""
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != '.':
                layer.put(x + i, y + j, c)


def stand(layer, rows, wx, wy, z=0, shade=None, flip=False):
    """A sprite standing on the floor (or on something at height z), its bottom middle at that spot. `shade` draws a small contact shadow in that tone under it."""
    sx, sy = screen(wx, wy, z)
    if flip:
        rows = [r[::-1] for r in rows]
    w = len(rows[0])
    if shade:
        for dx in range(-int(w * 0.45), int(w * 0.45) + 1):
            layer.put(sx + dx + 1, sy - 1, shade)
            if abs(dx) < w * 0.3:
                layer.put(sx + dx + 2, sy, shade)
    stamp(layer, rows, int(sx - w / 2), int(sy - len(rows)))


def on_wall(layer, rows, side, u0, v0, shadow=None, drop=(2, 2)):
    """A sprite hung on a back wall, sheared to the wall's slope. `side` is 'L' (the wall on the left, running toward the camera) or 'R'. `shadow` is the tone of the shadow it throws
    on the wall, down and to the right by `drop`."""
    h, w = len(rows), len(rows[0])
    if shadow:
        mark = Layer()
        on_wall(mark, rows, side, u0, v0)
        for y in range(SIZE):
            for x in range(SIZE):
                if mark.rows[y][x] != '.':
                    layer.put(x + drop[0], y + drop[1], shadow)
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c == '.':
                continue
            if side == 'L':
                u = u0 + (w - 1 - i)
                layer.put(CX - u - 1, YB + u / 2 - (v0 + h - 1 - j) - 1, c)
            else:
                u = u0 + i
                layer.put(CX + u, YB + u / 2 - (v0 + h - 1 - j) - 1, c)


# --- small wares --------------------------------------------------------------------------------
def potion(colour, tall=9, round_=False):
    """A glass bottle with a cork, the liquid shaded across (a bright rim, the body, a dark side), a pale glint down the glass, a bright surface and a thick base."""
    ramps = {'red': ('j', 'i', 'h'), 'blue': ('o', 'n', 'm'), 'green': ('z', 'A', 'B'), 'violet': ('v', 'f', 'u'), 'gold': ('d', 'b', 'a')}
    hi, mid, lo = ramps[colour]
    if round_:
        widths = [3, 3, 3, 5, 7, 9, 9, 9, 9, 7, 5]          # a round flask: a neck and a ball
        liquid_from, neck_rows = 5, 3
    else:
        widths = [3, 3, 3, 5, 7, 7, 7, 7, 7, 7, 5]          # a tall vial: a neck, shoulders and a straight body
        liquid_from, neck_rows = 5, 3
    W = max(widths)
    g = Grid(W + 2, len(widths) + 2)
    for y, w in enumerate(widths):
        x0 = (W - w) // 2 + 1
        for i in range(w):
            x = x0 + i
            t = i / max(1, w - 1)
            if y < 2:                                           # the cork
                g.put(x, y + 1, 'C' if y == 0 else 'a')
            elif y < liquid_from:                               # empty glass: pale, with a lit left edge
                g.put(x, y + 1, 't' if i == 0 else 'r' if t < 0.5 else 'q')
            else:
                row_in = y - liquid_from
                c = hi if t < 0.25 else mid if t < 0.7 else lo
                if row_in == 0:
                    c = hi if t < 0.6 else mid                 # the surface of the liquid
                if y == len(widths) - 1:
                    c = lo                                      # the thick base
                if i == 1 and 1 <= row_in <= 3 and w > 4:
                    c = 't'                                     # the glint on the glass
                g.put(x, y + 1, c)
    lay = Layer()
    stamp(lay, g.rows, 5, 5)
    lay.outline()
    return trim(lay.rows)


def book(colour='i', w=4, h=9):
    ramps = {'i': ('j', 'i', 'h'), 'b': ('d', 'b', 'a'), 'n': ('o', 'n', 'm'), 'g': ('z', 'A', 'B'), 'v': ('v', 'f', 'u')}
    hi, mid, lo = ramps[colour]
    rows = [['O'] * (w + 2)] + [['O', hi] + [mid] * (w - 2) + [lo, 'O'] for _ in range(h)] + [['O'] * (w + 2)]
    rows[2][2], rows[h - 1][2] = 't', 't'
    return rows


def scroll(colour='t'):
    lay = Layer()
    for i in range(11):
        lay.put(10 + i // 3, 10 + i // 2, 'O')
    g = Grid(12, 6)
    for y in range(6):
        for x in range(12):
            if 1 <= y <= 4 and 1 <= x <= 10:
                g.put(x, y, 't' if y < 3 else 'C')
            elif (y in (0, 5) and 0 <= x <= 11) or (x in (0, 11)):
                g.put(x, y, 'O')
    g.put(0, 2, 'b')
    g.put(0, 3, 'a')
    g.put(11, 2, 'b')
    g.put(11, 3, 'a')
    for x in (3, 5, 7, 8):
        g.put(x, 2, 'e')
    return g.rows


def jar(ramp=('t', 'q', 'p'), lid='a'):
    hi, mid, lo = ramp
    rows = ['.OOO.', 'OabaO', '.OOO.', 'OhmlO', 'OhmlO', 'OhmlO', '.OOO.']
    out = []
    for r in rows:
        out.append([{'h': hi, 'm': mid, 'l': lo, 'a': lid, 'b': 'b'}.get(c, c) for c in r])
    return out


def sack(ramp=('C', 't', 'b')):
    g = Grid(14, 14)
    g.blob(7, 8, 5.6, ('t', 'C', 'b', 'a'), ry=5.6)
    for x in range(5, 10):
        g.put(x, 2, 'C')
    g.put(6, 3, 'a')
    g.put(8, 3, 'a')
    for x in range(4, 11):
        g.put(x, 3, 'a')
    lay = Layer()
    stamp(lay, g.rows, 5, 5)
    lay.outline()
    return trim(lay.rows)


def coins():
    g = Grid(12, 7)
    g.blob(6, 4.5, 5, ('d', 'b', 'a', 'a'), ry=2.6)
    g.put(3, 2, 'd')
    g.put(5, 1, 'd')
    g.put(8, 2, 't')
    lay = Layer()
    stamp(lay, g.rows, 5, 5)
    lay.outline()
    return trim(lay.rows)


def lantern(glow=True):
    g = Grid(9, 15)
    for y in range(0, 3):
        g.put(4, y, 'O')
    g.put(3, 3, 'O')
    g.put(4, 3, 'b')
    g.put(5, 3, 'O')
    for y in range(4, 11):
        for x in range(2, 7):
            g.put(x, y, 'O' if x in (2, 6) else 'd' if y in (6, 7) and x == 4 else 'b' if (x + y) % 2 else 'd')
    g.put(4, 6, 't')
    g.put(4, 7, 't')
    for x in range(2, 7):
        g.put(x, 11, 'O')
    g.put(4, 12, 'O')
    return g.rows


def barrel_box(layer, cx, cy, z0, h, r=8):
    """A barrel: a round shaded body with two hoops, standing on the floor at world (cx, cy)."""
    sx, sy = screen(cx, cy, z0)
    rx, ry = r * 1.15, r * 0.58
    ramp = ('f', 'g', 'w', 'x')
    for y in range(int(sy - h - ry), int(sy + ry) + 1):
        for x in range(int(sx - rx) - 1, int(sx + rx) + 2):
            dx = (x + 0.5 - sx) / rx
            if abs(dx) > 1:
                continue
            top_y = sy - h + ry * math.sqrt(max(0, 1 - dx * dx))
            bot_y = sy + ry * math.sqrt(max(0, 1 - dx * dx))
            if y + 0.5 <= bot_y:
                if y + 0.5 >= sy - h - ry * math.sqrt(max(0, 1 - dx * dx)):
                    inside_top = y + 0.5 < top_y
                    if inside_top:
                        layer.put(x, y, 'g' if hashed(x, y) < 0.8 else 'w')           # the open top: the dark inside
                    else:
                        tone = 0 if dx < -0.45 else 1 if dx < 0.3 else 2 if dx < 0.75 else 3
                        c = ramp[tone]
                        for hoop in (0.25, 0.72):
                            if abs((y + 0.5) - (sy - h * hoop - ry * math.sqrt(max(0, 1 - dx * dx)) * 0.0) - (bot_y - sy) * 0.0) < 1.2:
                                c = 'p' if tone < 2 else 'l'
                        if int(x + 0.5 - sx) % 4 == 0:
                            c = ramp[min(3, tone + 1)]
                        layer.put(x, y, c)
    for x in range(int(sx - rx), int(sx + rx) + 1):               # the rim
        dx = (x + 0.5 - sx) / rx
        if abs(dx) <= 1:
            layer.put(x, sy - h - ry * math.sqrt(max(0, 1 - dx * dx)), 'f')


# --- the room -----------------------------------------------------------------------------------
def underside(layer):
    """The slab's clay sides and, under them, the rock that hangs from it."""
    top = YB + 56
    for y in range(top, TIP + 1):
        t = (y - top) / (TIP - top)
        for x in range(CX - SPAN, CX + SPAN + 1):
            wob = (hashed(y // 3, 11) - 0.5) * 12 * min(1, t * 2.5)
            reach = SPAN * (1 - t) ** 0.72 + wob
            if abs(x - CX) > reach:
                continue
            right = x >= CX
            band = ((y - top) // 6 + (1 if hashed(x // 14, (y - top) // 6, 5) < 0.3 else 0)) % 3
            if t < 0.5:
                c = (('a', 'e', 'a') if right else ('e', 'f', 'e'))[band]
            else:
                c = (('e', 'f', 'e') if right else ('f', 'g', 'f'))[band] if t < 0.78 else ('g' if right else 'w')
            layer.put(x, y, c)
    L, F, R = screen(0, SPAN), screen(SPAN, SPAN), screen(SPAN, 0)

    def side(lit):
        tones = ('a', 'e') if lit else ('e', 'f')
        return lambda X, Y: tones[(int(Y) // 5) % 2] if hashed(int(X) // 5, int(Y) // 5, 3) > 0.15 else ('b' if lit else 'f')
    layer.polygon([(F[0], F[1]), (R[0], R[1]), (R[0], R[1] + SLAB), (F[0], F[1] + SLAB)], side(True))
    layer.polygon([(L[0], L[1]), (F[0], F[1]), (F[0], F[1] + SLAB), (L[0], L[1] + SLAB)], side(False))
    for k, x in enumerate((70, 104, 150, 176, 128)):                                    # roots hanging off the rock
        y0 = int(YB + 112 + SLAB + 6 - abs(x - CX) * 0.3 + hashed(k, 2) * 10)
        for y in range(y0, min(y0 + 6 + int(hashed(k, 3) * 8), TIP - 2)):
            layer.put(x + int(math.sin(y * 0.5 + k) * 1.3), y, 'g' if (y - y0) < 10 else 'f')


def floor(layer):
    def board(X, Y):
        wx = (X - CX) / 2 + (Y - YB)
        wy = (Y - YB) - (X - CX) / 2
        i = int(wy // 4)
        c = 'b'
        if wy % 4 < 1:
            c = 'a'                                                   # the gap between boards
        elif (wx + (i % 3) * 9) % 32 < 1:
            c = 'a'                                                   # a joint, staggered from board to board
        elif hashed(i, int((wx + (i % 3) * 9) // 32), 2) < 0.22:
            c = 'd'                                                   # an odd paler board
        return c
    layer.polygon([screen(0, 0), screen(SPAN, 0), screen(SPAN, SPAN), screen(0, SPAN)], board)


def shadow(layer, wx0, wy0, wx1, wy1, reach=4):
    """A darker patch on the floor round the foot of something standing there (a little more to the right and the front)."""
    dark = {'b': 'a', 'd': 'b', 'a': 'e', 'e': 'f', 'h': 'g', 'i': 'h', 'j': 'i'}

    def fn(X, Y):
        c = layer.get(X, Y)
        return dark.get(c, c) if c in dark else None
    layer.polygon([screen(wx0, wy0), screen(wx1 + reach, wy0), screen(wx1 + reach, wy1 + reach), screen(wx0, wy1 + reach)], fn)


def rug(layer, wx0, wy0, wx1, wy1):
    def fn(X, Y):
        wx = (X - CX) / 2 + (Y - YB)
        wy = (Y - YB) - (X - CX) / 2
        u, v = wx - wx0, wy - wy0
        du, dv = min(u, wx1 - wx0 - u), min(v, wy1 - wy0 - v)
        d = min(du, dv)
        if d < 1.5:
            return 'h'
        if d < 3.5:
            return 'b'
        if d < 5:
            return 'i'
        if d < 6:
            return 'd'
        cu, cv = abs(u - (wx1 - wx0) / 2), abs(v - (wy1 - wy0) / 2)
        if cu / 22 + cv / 12 < 1:
            return 'd' if (cu / 22 + cv / 12 > 0.8) else 'j' if cu / 22 + cv / 12 > 0.45 else 'b'
        return 'i' if (int(u) // 3 + int(v) // 3) % 2 else 'h'
    layer.polygon([screen(wx0, wy0), screen(wx1, wy0), screen(wx1, wy1), screen(wx0, wy1)], fn)


def walls(layer):
    """The two back walls: a stone wall above a timber panel, a cap on top. Left wall (wx = 0) catches the light, the right one (wy = 0) is in shade."""
    def wall_fn(lit):
        stone = ('p', 'q', 'l') if lit else ('l', 'p', 'k')
        beam = ('f', 'g', 'w') if lit else ('g', 'w', 'x')

        def fn(X, Y, side):
            u = (CX - X) if side == 'L' else (X - CX)
            v = YB + u / 2 - Y
            if v < 22:                                                      # the timber panel
                return beam[0] if int(u) % 6 else beam[2] if v > 1 else beam[1]
            if v < 24:
                return beam[2]
            row = int((v - 24) // 7)
            off = (row % 2) * 6
            k = int((u + off) // 12)
            if (v - 24) % 7 < 1:
                return stone[2]
            if (u + off) % 12 < 1:
                return stone[2]
            return stone[0] if hashed(k, row, 3) < 0.55 else stone[1]
        return fn
    lf, rf = wall_fn(True), wall_fn(False)
    layer.polygon([screen(0, 0, WALL), screen(0, SPAN, WALL), screen(0, SPAN, 0), screen(0, 0, 0)], lambda X, Y: lf(X, Y, 'L'))
    layer.polygon([screen(0, 0, WALL), screen(SPAN, 0, WALL), screen(SPAN, 0, 0), screen(0, 0, 0)], lambda X, Y: rf(X, Y, 'R'))
    # the cap along the top of each wall and the thickness of the wall at its open end
    cap = lambda c: (lambda X, Y: c)
    layer.polygon([screen(0, 0, WALL), screen(0, SPAN, WALL), (screen(0, SPAN, WALL)[0] + 0, screen(0, SPAN, WALL)[1] - 3), (screen(0, 0, WALL)[0] + 0, screen(0, 0, WALL)[1] - 3)], cap('t'))
    layer.polygon([screen(0, 0, WALL), screen(SPAN, 0, WALL), (screen(SPAN, 0, WALL)[0] - 0, screen(SPAN, 0, WALL)[1] - 3), (screen(0, 0, WALL)[0] - 0, screen(0, 0, WALL)[1] - 3)], cap('C'))
    for sx, sy in (screen(0, SPAN, 0), screen(SPAN, 0, 0)):
        pass


def wall_features(layer, icons, amulets, wares):
    """Window, weapons and shelves. u runs along the wall away from the back corner; v is height above the floor."""
    # the left wall: an arched window, and the weapons
    def window(X, Y):
        u = CX - X
        v = YB + u / 2 - Y
        du, dv = u - 12, v - 28
        if not (0 <= du <= 32 and 0 <= dv <= 44):
            return None
        arch = dv > 30 and (du - 16) ** 2 / 256 + (dv - 30) ** 2 / 196 > 1
        if arch:
            return None
        if du < 2 or du > 30 or dv < 2:
            return 'f'
        if abs(du - 16) < 1 or abs(dv - 20) < 1:
            return 'g'
        return 'r' if (du + dv) % 11 < 3 else 'o' if dv > 24 else 'n'
    poly = [screen(0, 12, 28), screen(0, 44, 28), screen(0, 44, 74), screen(0, 12, 74)]
    layer.polygon([(x, y - 2) for x, y in [screen(0, 12, 28), screen(0, 44, 28), screen(0, 44, 74), screen(0, 12, 74)]], window)
    # a sill under the window
    layer.polygon([screen(0, 10, 25), screen(0, 46, 25), screen(0, 46, 28), screen(0, 10, 28)], lambda X, Y: 'e')
    # weapons hung on pegs, the game's own icons at full size
    for name, u in (('iron-sword', 36), ('war-hammer', 80)):
        rows = trim(icons[name])
        w = len(rows[0])
        on_wall(layer, rows, 'L', u, 34)
        for peg in (0.2, 0.75):                                      # the pegs it rests on, one near each end of the weapon
            pu = u + int(w * peg)
            layer.polygon([screen(0, pu - 1, 31), screen(0, pu + 2, 31), screen(0, pu + 2, 34), screen(0, pu - 1, 34)], lambda X, Y: 'b')
    # the right wall: a door at the back, shelves of wares, amulets on a rail
    def door(X, Y):
        u = X - CX
        v = YB + u / 2 - Y
        du = u - 4
        if not (0 <= du <= 26 and 0 <= v <= 52):
            return None
        if v > 38 and (du - 13) ** 2 / 169 + (v - 38) ** 2 / 196 > 1:
            return None
        if du < 2 or du > 24 or v > 49 or (v > 36 and ((du - 13) ** 2 / 121 + (v - 38) ** 2 / 144 > 1)):
            return 'b'
        return 'x' if int(du) % 5 else 'w'
    layer.polygon([screen(0, 0, 0), screen(34, 0, 0), screen(34, 0, 60), screen(0, 0, 60)], lambda X, Y: door(X, Y + 1))
    for shelf_v, items in ((20, wares['shelf1']), (38, wares['shelf2'])):
        layer.polygon([screen(38, 0, shelf_v - 3), screen(108, 0, shelf_v - 3), screen(108, 0, shelf_v - 6), screen(38, 0, shelf_v - 6)], lambda X, Y: 'k')   # its shadow on the wall
        layer.polygon([screen(37, 0, shelf_v), screen(109, 0, shelf_v), screen(109, 0, shelf_v - 3), screen(37, 0, shelf_v - 3)], lambda X, Y: 'f' if Y < YB + (X - CX) / 2 - shelf_v + 1.5 else 'g')
        u = 41
        for rows in items:
            on_wall(layer, rows, 'R', u, shelf_v, shadow='k', drop=(2, 1))
            u += len(rows[0]) + 1
    # a rail with amulets hanging from it on their chains, each throwing a shadow on the wall
    layer.polygon([screen(40, 0, 83), screen(108, 0, 83), screen(108, 0, 81), screen(40, 0, 81)], lambda X, Y: 'f')
    for k, am in enumerate(amulets):
        u = 52 + k * 18
        mid = u + len(am[0]) // 2
        layer.polygon([screen(mid, 0, 83), screen(mid + 1, 0, 83), screen(mid + 1, 0, 76), screen(mid, 0, 76)], lambda X, Y: 'b')           # the cord it hangs by, from a hook on the rail
        on_wall(layer, am, 'R', u, 77 - len(am), shadow='k', drop=(2, 2))
    # lanterns on brackets, one on each wall
    on_wall(layer, lantern(), 'L', 6, 38)


def build():
    icons = {n: sprite_of(ASSETS / f'icon-weapon-{n}.png') for n in
             ('iron-sword', 'war-hammer', 'longbow', 'spear', 'battle-axe', 'wooden-staff', 'scimitar', 'crystal-staff', 'hatchet', 'spiked-mace', 'dagger', 'elven', 'iron-axe')}
    amulet_sheet = sprite_of(ASSETS / 'amulets.png')
    amulets = [half(crop(amulet_sheet, 32 * i, 32)) for i in (0, 1, 2, 3, 5)]
    amulets = [trim(a) for a in amulets]
    amulets_wall = [trim(shrink(trim(crop(amulet_sheet, 32 * i, 32)), 3, 8)) for i in (0, 2, 3)]
    crystals = sprite_of(ASSETS / 'crystal.png')
    crystal_small = [trim(half(crop(crystals, 32 * i, 32))) for i in (0, 2, 5)]
    rocks = sprite_of(ASSETS / 'rock.png')
    rock_small = [trim(half(crop(rocks, 32 * i, 32))) for i in (0, 1)]
    wares = {
        'shelf1': [potion('red'), potion('blue', round_=True), potion('green'), jar(), potion('violet'), jar(('d', 'b', 'a'), 'g'), potion('gold', round_=True), book('i'), book('n'), book('g', 5), scroll(), potion('blue')],
        'left': [rock_small[0], crystal_small[0], jar(('r', 'q', 'p')), crystal_small[1], rock_small[1], jar(('t', 'C', 'b'), 'a'), crystal_small[2], rock_small[0], potion('violet')],
        'shelf2': [book('v'), book('b', 5), book('n'), book('i'), potion('gold'), potion('green', round_=True), potion('red'), jar(), scroll(), potion('violet', round_=True), book('g')],
    }
    out = Layer()
    underside(out)
    floor(out)
    rug(out, 38, 38, 92, 84)
    for fp in ((6, 6, 26, 26), (40, 14, 104, 32), (8, 52, 30, 98), (46, 74, 70, 90), (75, 77, 93, 95), (95, 54, 109, 66), (84, 100, 108, 112), (6, 98, 30, 112)):
        shadow(out, *fp)
    walls(out)
    decor = Layer()
    wall_features(decor, icons, amulets_wall, wares)
    inside = Layer()
    inside.polygon([screen(0, 0, WALL), screen(0, SPAN, WALL), screen(0, SPAN, 0), screen(SPAN, 0, 0), screen(SPAN, 0, WALL)], lambda X, Y: 'x')
    for y in range(SIZE):
        for x in range(SIZE):
            if inside.rows[y][x] == '.':
                decor.rows[y][x] = '.'
    out.over(decor)

    # the things standing on the floor, drawn back to front
    props = []

    def prop(depth, draw):
        props.append((depth, draw))

    def crates(lay):
        box(lay, 6, 6, 26, 26, 0, 17, pattern='planks')
        box(lay, 9, 9, 22, 22, 17, 27)
        stand(lay, crystal_small[0], 15, 15, 27)
        stand(lay, rock_small[0], 18, 20, 27)
        lay.outline()
    prop(26 + 26, crates)

    def counter(lay):
        box(lay, 40, 14, 104, 32, 0, 22, ramps={'top': ('t', 'C', 'b'), 'right': ('f', 'g', 'w'), 'left': ('g', 'w', 'x')}, pattern='planks', top_pattern='plain')
        lay.outline()
    prop(104 + 32, counter)

    def counter_goods(lay):
        z, t = 22, 'C'
        stand(lay, half(icons['iron-axe']), 56, 25, z + 1, t)             # one axe laid across the counter
        stand(lay, amulets[0], 68, 26, z, t)
        stand(lay, amulets[2], 73, 24, z, t, flip=True)
        stand(lay, coins(), 82, 25, z, t)
        stand(lay, potion('red'), 91, 27, z, t)
        stand(lay, potion('green', round_=True), 96, 25, z, t)
        stand(lay, potion('blue'), 100, 27, z, t)
        stand(lay, book('i', 4, 3), 46, 25, z, t)                         # two books lying flat, one on the other
        stand(lay, book('n', 4, 3), 46, 25, z + 5, t)
    prop(104 + 33, counter_goods)

    def table(lay):
        box(lay, 8, 52, 30, 98, 0, 15, ramps={'top': ('i', 'h', 'h'), 'right': ('f', 'g', 'w'), 'left': ('g', 'w', 'x')}, pattern='planks', top_pattern='plain')
        lay.outline()
    prop(30 + 98, table)

    def table_goods(lay):
        z, t = 15, 'h'
        stand(lay, half(icons['dagger']), 17, 58, z, t)               # three blades laid in a row, each resting on the cloth
        stand(lay, half(icons['elven']), 17, 68, z, t)
        stand(lay, half(icons['scimitar']), 18, 78, z, t, flip=True)
        stand(lay, amulets[3], 24, 63, z, t)                          # a pendant and a few small things beside them
        stand(lay, potion('gold', round_=True), 24, 88, z, t)
        stand(lay, potion('blue'), 21, 92, z, t)
        stand(lay, crystal_small[2], 12, 90, z, t)
        stand(lay, book('b'), 13, 74, z, t)
    prop(30 + 99, table_goods)

    def chest(lay):
        box(lay, 46, 74, 70, 90, 0, 11, ramps={'top': ('f', 'g', 'w'), 'right': ('f', 'g', 'w'), 'left': ('g', 'w', 'x')}, pattern='planks')
        for gx in (50, 66):
            box(lay, gx, 73, gx + 3, 91, 0, 11, ramps={'top': ('b', 'a', 'a'), 'right': ('b', 'a', 'a'), 'left': ('a', 'e', 'e')}, pattern='plain')
        box(lay, 44, 73, 72, 91, 11, 14, ramps={'top': ('g', 'w', 'w'), 'right': ('f', 'g', 'g'), 'left': ('g', 'w', 'x')}, pattern='plain')
        lay.outline()
    prop(70 + 90, chest)

    def chest_gold(lay):
        stand(lay, coins(), 55, 84, 14)
        stand(lay, coins(), 62, 80, 14)
        stand(lay, coins(), 58, 76, 14)
        stand(lay, coins(), 60, 84, 14)
    prop(70 + 91, chest_gold)

    def basket(cx, cy, goods):
        def draw(lay):
            barrel_box(lay, cx, cy, 0, 9, 6)
            for k, g_ in enumerate(goods):
                stand(lay, g_, cx - 4 + k * 5, cy + 1 - (k % 2), 9, 'g')
            lay.outline()
        prop(cx + cy + 3, draw)

    def low_crate(lay):
        box(lay, 84, 100, 108, 112, 0, 7, pattern='planks')
        for k, g_ in enumerate([crystal_small[0], rock_small[0], crystal_small[2], rock_small[1], crystal_small[1]]):
            stand(lay, g_, 88 + k * 5, 106 + (k % 2) * 2, 7, 'a')
        lay.outline()
    prop(108 + 112, low_crate)
    basket(14, 34, [crystal_small[1], crystal_small[0]])

    def sacks(lay):
        stand(lay, sack(), 14, 106, 0)
        stand(lay, sack(('t', 'C', 'b')), 24, 108, 0)
        stand(lay, sack(), 20, 100, 6)
        lay.outline()
    prop(14 + 106, sacks)

    for _, draw in sorted(props, key=lambda p: p[0]):
        lay = Layer()
        draw(lay)
        out.over(lay)
    # everything floating: a few wisps and pebbles drifting about the room and under it
    for (x, y, c) in ((26, 128, 'r'), (230, 120, 'o'), (214, 168, 'r'), (40, 190, 'q'), (200, 214, 'r'), (60, 236, 'q'), (190, 150, 'o')):
        out.put(x, y, c)
        if (x + y) % 2:
            out.put(x + 1, y - 1, 't')
    for (cx, cy, r) in ((30, 210, 4), (222, 204, 3), (100, 248, 2)):
        out.blob(cx, cy, r, ('f', 'e', 'f', 'g'), ry=r * 0.8, edge=0.5, seed=cx)
    out.outline()
    return out.lines()


CATEGORY = 'Buildings'
ANCHOR = (CX, int(YB + SPAN / 2))        # the middle of the floor


def build_assets():
    """One asset: the whole shop interior as a single still, 256 x 256, anchored on the middle of its floor."""
    return [{
        'id': 'bazaar-shop', 'label': 'Bazaar - the inside of a shop, floating (one image)', 'category': CATEGORY, 'kind': 'still', 'place': 'none',
        'w': SIZE, 'h': SIZE, 'cols': 1, 'rows': 1, 'fps': 0, 'anchor': {'x': ANCHOR[0], 'y': ANCHOR[1]},
        'frames': [build()],
    }]


def preview(path, scale=3):
    from PIL import Image
    rgb = rgb_of()
    lines = build()
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    for y, line in enumerate(lines):
        for x, c in enumerate(line):
            if c != '.':
                img.putpixel((x, y), rgb[c] + (255,))
    sheet = Image.new('RGBA', (SIZE + SIZE * scale + 24, SIZE * scale + 16), (36, 38, 56, 255))
    sheet.alpha_composite(img, (8, 8))
    sheet.alpha_composite(img.resize((SIZE * scale, SIZE * scale), Image.NEAREST), (SIZE + 16, 8))
    sheet.save(path)
    return img


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--png', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        img = preview(args.preview)
        print('wrote', args.preview)
        if args.png:
            img.save(args.png)
            print('wrote', args.png)
    elif args.png:
        from PIL import Image
        rgb = rgb_of()
        img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
        for y, line in enumerate(build()):
            for x, c in enumerate(line):
                if c != '.':
                    img.putpixel((x, y), rgb[c] + (255,))
        img.save(args.png)
        print('wrote', args.png)


if __name__ == '__main__':
    main()
