#!/usr/bin/env python3
"""A menu panel: a frame that replaces the plain dark box behind a screen's text, built from the same parts as the buttons (see make_buttons.py).

A dark ink fill in an old steel bevel with gold corner brackets, worn and mossy, with mushrooms growing off the top corners, vines creeping along the frame and a few hanging into the panel.
It is a nine-slice: any size is made from nine pieces that join,

    TL  T  TR        the corners are 40 x 40 (the top row also has PAD rows above for the mushrooms, the bottom row SLAB rows under for the depth)
    L   C  R         T and B are 64 wide and wrap, L and R are 64 tall and wrap, C is a 64 x 64 fill that wraps both ways
    BL  B  BR

Draw the corners, then as many T, B, L, R and C pieces as the size needs (the last of each cut short). The pieces wrap, so the wear carries on across every join and a long panel does not repeat in steps.
The panel has no text: the game draws its own over the fill. Palette roles only.

    python3 tools/make_panel.py --preview previews/panel.png     a panel at two sizes next to a button, enlarged
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

FOLDER = 'panel'
CATEGORY = 'UI'
SAMPLE = (320, 120)     # the ready-made panel's body, `ui-panel`
CW = CH = 40            # a corner piece
TILE = 64               # the edges and the fill wrap at this
PAD = 14                # rows above the top row of the body, for the mushrooms
SLAB = 4                # the depth under the bottom edge, as the buttons have
RC = 12                 # the corner radius of the body
WEDGE = 18              # a gold bracket's legs
T = 5                   # the steel's thickness: rows 1 to T, with the dark outline either side
JOIN = 24               # where in the wrap a corner's inner edge picks up, so the moss carries on across the join
BIG = 10 ** 6
LIGHT = (-0.45, -0.89)
FRAME = 'klpt'          # the steel from its shaded side to its specular
FACE = 'kwxx'           # the slab's side face
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
DRIPS = [(5, 4), (14, 8), (33, 6), (47, 3), (58, 9)]       # x in the wrap, how far a drip of moss hangs
HANGING = [(6, 9), (17, 15), (29, 7), (41, 20), (55, 11)]   # x in the wrap and how far a vine hangs into the panel, on the top edge
REGIONS = ('TL', 'T', 'TR', 'L', 'C', 'R', 'BL', 'B', 'BR')
# the top edge has six pictures, all 64 wide, that can follow each other in any order: they share the moss hem and everything within 4 columns of their ends, so every pair joins
TOP_VARIANTS = ('T', 'T2', 'T3', 'T4', 'T5', 'T6')
TOP_LABELS = {'T': 'vines', 'T2': 'mossy', 'T3': 'mushrooms', 'T4': 'one vine', 'T5': 'big caps', 'T6': 'glow-worms'}
TOP_WEIGHTS = (0.12, 0.28, 0.2, 0.15, 0.13, 0.12)       # how often a game should pick each one: the busy one least


def rnd(*a):
    """A repeatable number in [0, 1) from some integers."""
    n = 0x9e3779b1
    for v in a:
        n = ((n ^ (v & 0xffffffff)) * 0x85ebca6b + 0x27d4eb2f) & 0xffffffff
        n ^= n >> 15
    return (n & 0xffff) / 65536


def size_of(region):
    """(width, height) of a piece's body rows, without the PAD above or the SLAB below."""
    w = CW if region in ('TL', 'TR', 'L', 'R', 'BL', 'BR') else TILE
    h = CH if region in ('TL', 'T', 'TR', 'BL', 'B', 'BR') else TILE
    return w, h


def distances(region, c, r):
    """How far the pixel is from each side the piece has: left, right, top, bottom (BIG on the sides it does not have)."""
    w, h = size_of(region)
    dl = c if region in ('TL', 'L', 'BL') else BIG
    dr = (w - 1 - c) if region in ('TR', 'R', 'BR') else BIG
    dt = r if region in ('TL', 'T', 'TR') else BIG
    db = (h - 1 - r) if region in ('BL', 'B', 'BR') else BIG
    return dl, dr, dt, db


def geom(region, c, r):
    """How far inside the body's edge (below 0: outside it) and which way the edge faces (screen x, y), with the round corners."""
    dl, dr, dt, db = distances(region, c, r)
    best, normal = BIG, (0.0, 0.0)
    for d, n in ((dl, (-1.0, 0.0)), (dr, (1.0, 0.0)), (dt, (0.0, -1.0)), (db, (0.0, 1.0))):
        if d < best:
            best, normal = d, n
    for (a, b, sx, sy) in ((dl, dt, -1, -1), (dr, dt, 1, -1), (dl, db, -1, 1), (dr, db, 1, 1)):
        if a < RC and b < RC:
            dx, dy = RC - (a + 0.5), RC - (b + 0.5)
            rad = math.hypot(dx, dy) or 1e-6
            return RC - rad, (sx * dx / rad, sy * dy / rad)
    if r < 0 or best < 0 or best >= BIG:
        return (best if best < BIG else 99), normal
    return best, normal


def moss_depth(X):
    s = math.sin(2 * math.pi * X * 2 / TILE + 0.7) + 0.5 * math.sin(2 * math.pi * X * 5 / TILE + 2) + 0.3 * math.sin(2 * math.pi * X * 9 / TILE)
    return max(0, round(1.2 + 1.5 * s))


def fill_role(X, Y, d, facing):
    """The ink inside the frame: eggplant with a few grape flecks, darker towards the frame, a shadow under it on the lit sides."""
    if d == T + 2 and facing > 0.25:
        return 'w'
    near = max(0.0, (T + 7 - d) / 7)                              # 1 at the frame, 0 a few rows in
    if rnd(X % TILE, Y % TILE, 1) < 0.035:
        return 'k' if near < 0.3 else 'w'
    if rnd(X % TILE, Y % TILE, 2) < 0.07 + 0.35 * near * BAYER[Y % 4][X % 4] / 16 * 2:
        return 'w'
    return 'x'


def hanging_pixels(region):
    """Vines that hang into the panel from the top edge, wavy, with leaves: {(c, r): role}."""
    out = {}
    if region == 'T':
        strands = HANGING
    elif region == 'T2':
        strands = [(21, 5), (46, 4)]                                  # a couple of short roots
    elif region == 'T4':
        strands = [(34, 21), (14, 6)]                                 # one long vine and a short one
    elif region == 'T6':                                              # glow-worm threads: a thin teal line with a bright bead on the end
        for x, length in ((12, 6), (26, 11), (41, 8), (53, 13)):
            for i in range(length):
                out[(x, T + 2 + i)] = 'q'
            out[(x, T + 2 + length)] = 'o'
            out[(x, T + 3 + length)] = 'r'
            out[(x - 1, T + 2 + length)] = 's'
            out[(x + 1, T + 2 + length)] = 's'
        return out
    elif region == 'TL':
        strands = [(26, 13), (35, 7)]
    elif region == 'TR':
        strands = [(8, 10), (CW - 14, 16)]
    else:
        return out
    for x, length in strands:
        for i in range(length):
            xo = round(1.2 * math.sin(i * 0.8 + x))
            r = T + 2 + i
            out[(x + xo, r)] = 'A' if i % 3 else 'B'
            if i % 4 == 2:
                out[(x + xo + (1 if (i // 4 + x) % 2 else -1), r)] = 'z'
        out[(x + round(1.2 * math.sin((length - 1) * 0.8 + x)), T + 2 + length)] = 'z'
    return out


def vine_pixels(region):
    """Vines crawling over the frame, in the top left and bottom right corners, two thick: {(c, r): role}, tapering off."""
    out = {}
    if region == 'T4':                                            # a vine crawling along the steel, to the right of the long one
        for k in range(42, 60):
            wob = 3 + round(1.4 * math.sin(k * 0.5))
            for t, role in ((0, 'A'), (1, 'B')):
                out[(k, wob + t)] = role if k % 4 else 'z'
            if k % 5 == 0:
                out[(k, wob + (-1 if (k // 5) % 2 else 2))] = 'z'
        return out
    if region == 'T2':                                            # clumps of moss on the steel below the hem, and a chip or two
        for cx, cy, wd in ((19, 3, 6), (42, 4, 7), (55, 3, 3)):
            for i in range(wd):
                for j in range(2 if i % 3 else 1):
                    out[(cx + i, cy + j)] = 'A' if (i + j) % 2 else ('z' if i % 4 == 1 else 'B')
        for cx in (10, 31, 50):
            out[(cx, 5)] = 'k'
        return out
    if region not in ('TL', 'BR'):
        return out
    flip = region == 'BR'
    for k in range(14, 39):                                   # along the top (or bottom) edge
        wob = 3 + round(1.6 * math.sin(k * 0.5))
        for t, role in ((0, 'A'), (1, 'B')):
            if k > 33 and t == 1:
                continue
            c, r = (CW - 1 - k, CH - 1 - wob - t) if flip else (k, wob + t)
            out[(c, r)] = role if k % 4 else 'z'
        if k % 5 == 0:                                        # a leaf, on alternate sides
            c, r = (CW - 1 - k, CH - 1 - wob) if flip else (k, wob)
            out[(c, r + (-1 if (k // 5) % 2 else 2) * (-1 if flip else 1))] = 'z'
    for k in range(15, 36):                                   # down the side
        wob = 3 + round(1.6 * math.sin(k * 0.55 + 1))
        for t, role in ((0, 'A'), (1, 'B')):
            if k > 31 and t == 1:
                continue
            c, r = (CW - 1 - wob - t, CH - 1 - k) if flip else (wob + t, k)
            out[(c, r)] = role if k % 4 else 'z'
        if k % 6 == 1:
            c, r = (CW - 1 - wob, CH - 1 - k) if flip else (wob, k)
            out[(c + (-2 if flip else 2), r)] = 'z'
    return out


def mushroom(fill, cx, base_y, cap_w, cap_h, stem_h, kind='pink'):
    """Paint a mushroom into `fill` ({(c, r): role}), its stem standing on row `base_y` and growing up (towards smaller r)."""
    ramps = {'pink': ('j', 'i', 'i', 'h', 'w'), 'teal': ('r', 'q', 'q', 's', 'D')}
    spots = {'pink': 't', 'teal': 'o'}
    ramp = ramps[kind]
    sw = 4 if cap_w >= 13 else 3 if cap_w >= 9 else 2
    x0 = cx - (sw - 1) // 2 - (1 if sw == 4 else 0) if False else cx - sw // 2
    for i in range(stem_h):
        for k in range(sw):
            fill[(x0 + k, base_y - i)] = 't' if k == 0 else ('c' if k == sw - 1 else 'C')
    y_cap = base_y - stem_h                                   # the cap's lowest row
    for i in range(cap_h):
        row = y_cap - (cap_h - 1 - i)
        half = cap_w * math.sqrt(max(0.0, 1 - ((cap_h - 1 - i + 0.0) / cap_h) ** 2)) / 2
        half = max(half, 1.0)
        for x in range(int(cx - half + 0.5), int(cx + half + 0.5) + 1):
            shade = min(len(ramp) - 1, i * len(ramp) // cap_h + (1 if x > cx + half * 0.35 else 0))
            fill[(x, row)] = ramp[shade] if not (i == 0 and x > cx) else ramp[1]
    if cap_w >= 7:
        top = y_cap - (cap_h - 1)
        for dx, dy in ((-2, 1), (cap_w // 4 + 1, 2), (-cap_w // 4 - 1, 3) if cap_w >= 11 else (1, 1)) if cap_h >= 3 else ((-1, 1),):
            if (cx + dx, top + dy) in fill:
                fill[(cx + dx, top + dy)] = spots[kind]


def growth(region):
    """The mushrooms: a cluster of pink ones growing off the top left corner, a glowing teal pair off the top right, and a few teal ones inside the bottom left corner."""
    fill = {}
    floor = 1
    if region == 'TL':
        mushroom(fill, 22, 2, 15, 7, 8, 'pink')
        mushroom(fill, 33, 2, 9, 4, 5, 'pink')
        mushroom(fill, 12, 2, 7, 3, 4, 'pink')
        mushroom(fill, 38, 2, 5, 2, 2, 'pink')
        mushroom(fill, 6, 2, 5, 2, 2, 'pink')
    elif region == 'TR':
        mushroom(fill, CW - 21, 2, 11, 5, 7, 'teal')
        mushroom(fill, CW - 31, 2, 7, 3, 3, 'teal')
        mushroom(fill, CW - 11, 2, 7, 3, 4, 'pink')
        mushroom(fill, CW - 5, 2, 5, 2, 2, 'teal')
    elif region == 'T5':                                          # a few big caps: two large ones and a sprout
        mushroom(fill, 21, 2, 11, 5, 6, 'pink')
        mushroom(fill, 45, 2, 9, 4, 5, 'teal')
        mushroom(fill, 33, 2, 5, 2, 2, 'pink')
    elif region == 'T6':
        mushroom(fill, 19, 2, 7, 3, 3, 'teal')
        mushroom(fill, 47, 2, 5, 2, 3, 'teal')
    elif region == 'T3':
        mushroom(fill, 16, 2, 7, 3, 4, 'pink')
        mushroom(fill, 24, 2, 5, 2, 2, 'teal')
        mushroom(fill, 46, 2, 9, 4, 5, 'pink')
        mushroom(fill, 54, 2, 5, 2, 3, 'teal')
    elif region == 'BL':
        floor = CH - 1 - T - 2
        mushroom(fill, 14, floor, 9, 4, 4, 'teal')
        mushroom(fill, 23, floor, 7, 3, 2, 'teal')
        mushroom(fill, 7, floor, 5, 2, 2, 'pink')
    if not fill:
        return {}
    out = dict(fill)
    for (x, y) in list(fill):
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in fill and ny <= floor and (region in ('BL',) or ny < 0):
                out[(nx, ny)] = 'O'
    return out


def pixel(region, c, r):
    """The role at column c, row r of a piece (r below 0 is the PAD above it, r from the body's height on is the SLAB below). '.' is empty."""
    variant = region
    region = 'T' if region in TOP_VARIANTS else region               # a top edge variant is drawn as the top edge, then given its own extras
    w, h = size_of(region)
    top_row, bottom_row = region in ('TL', 'T', 'TR'), region in ('BL', 'B', 'BR')
    over = growth(variant).get((c, r))
    if r < 0:
        return over or '.'
    if bottom_row and r >= h:                                  # the slab: the body's shape shifted down
        d2, _ = geom(region, c, r - SLAB)
        if d2 < 0:
            return '.'
        return 'O' if d2 < 1 else FACE[max(0, min(len(FACE) - 1, r - h))]
    dist, (nx, ny) = geom(region, c, r)
    if dist < 0:
        if bottom_row:
            d2, _ = geom(region, c, r - SLAB)
            if d2 >= 0:
                return 'O' if d2 < 1 else FACE[0]
        return over or '.'
    d = int(dist)
    dl, dr, dt, db = distances(region, c, r)
    X = {'TL': (c + JOIN) % TILE, 'TR': c, 'T': c, 'B': c, 'BL': (c + JOIN) % TILE, 'BR': c}.get(region, c)
    Y = r % TILE
    facing = nx * LIGHT[0] + ny * LIGHT[1]
    role = None
    ex, ey = min(dl, dr), min(dt, db)
    if ex < BIG and ey < BIG and ex + ey <= WEDGE:               # the gold brackets, in the four corners
        t = WEDGE - (ex + ey)
        role = 'O' if (d == 0 or t == 0) else 'a' if t == 1 else 'd' if (d == 1 or t == 2) else 'b'
        if role in 'bd' and rnd(REGIONS.index(region), c, r, 7) < 0.16:
            role = 'B' if rnd(c, r, 9) < 0.5 else 'A'              # verdigris on the gold
        elif role in 'bd' and rnd(REGIONS.index(region), c, r, 3) < 0.06:
            role = 'a'
    if role is None:
        if d == 0 or d == T + 1:
            role = 'O'
        elif 1 <= d <= T:
            i = 3 if facing > 0.93 else 2 if facing > 0.25 else 1 if facing > -0.35 else 0
            role = FRAME[max(0, i - (d >= T - 1) - (d == T))]
            if rnd(X if (top_row or bottom_row) else Y, Y if (top_row or bottom_row) else X, 5) < 0.03:
                role = FRAME[0]                                  # a chip in the bevel
        else:
            role = fill_role(c if region in ('L', 'R', 'TL', 'TR', 'BL', 'BR') else X, Y, d, facing)
            role = hanging_pixels(variant).get((c, r), role)
    if top_row:                                                  # moss over the top edge: a ragged hem, thicker in the corners, with drips that taper
        depth = moss_depth(X) + 1
        end = min(dl, dr)
        if end < 14:
            depth += 3 - end // 5
        for dx, dl_ in DRIPS:
            if X == dx:
                depth = max(depth, dl_)
            elif (X - dx) % TILE in (1, TILE - 1):
                depth = max(depth, min(3, dl_ // 2 + 1))
        if r < depth and d >= 0:
            role = 'B' if r == depth - 1 and depth > 1 else ('z' if rnd(X, r, 5) < 0.3 else 'A')
    vine = vine_pixels(variant).get((c, r))
    if vine and d >= 0:
        role = vine
    if over and (over != 'O' or region == 'BL') and d >= 0:
        return over
    return role


def piece(region):
    """One piece as rows of roles, with the PAD rows above if it is in the top row and the SLAB rows below if it is in the bottom row."""
    base = 'T' if region in TOP_VARIANTS else region
    w, h = size_of(base)
    top = -PAD if base in ('TL', 'T', 'TR') else 0
    bottom = h + (SLAB if base in ('BL', 'B', 'BR') else 0)
    return [''.join(pixel(region, c, r) for c in range(w)) for r in range(top, bottom)]


def pick_top(i, seed=1):
    """Which top edge picture the i-th run of the top edge uses, at random by TOP_WEIGHTS (the same every time for the same seed)."""
    x = rnd(i, seed, 41)
    for name, wt in zip(TOP_VARIANTS, TOP_WEIGHTS):
        if x < wt:
            return name
        x -= wt
    return TOP_VARIANTS[-1]


def assemble(width, height, seed=1, tops=None):
    """A panel `width` x `height` (the body, without the PAD above or the SLAB below), at least 80 x 80, as rows of roles. The top edge mixes its four pictures (`tops`: a list of their names, one per run, or random by `seed`)."""
    width, height = max(80, width), max(80, height)
    pieces = {k: piece(k) for k in REGIONS + TOP_VARIANTS[1:]}
    inner_w, inner_h = width - 2 * CW, height - 2 * CH
    runs = -(-inner_w // TILE)
    chosen = [(tops[i % len(tops)] if tops else pick_top(i, seed)) for i in range(runs)]

    def row_of(left, mids, right, y_mid, y_left):
        m = ''.join(pieces[k][y_mid] for k in mids)
        return pieces[left][y_left] + m[:inner_w] + pieces[right][y_left]

    rows = []
    for y in range(PAD + CH):
        rows.append(row_of('TL', chosen, 'TR', y, y))
    for y in range(inner_h):
        rows.append(row_of('L', ['C'] * runs, 'R', y % TILE, y % TILE) if False else pieces['L'][y % TILE] + (pieces['C'][y % TILE] * runs)[:inner_w] + pieces['R'][y % TILE])
    for y in range(CH + SLAB):
        rows.append(row_of('BL', ['B'] * runs, 'BR', y, y))
    return rows


def piece_size(region):
    """(width, height) of a piece's picture, the PAD above and the SLAB below included."""
    base = 'T' if region in TOP_VARIANTS else region
    w, h = size_of(base)
    return w, h + (PAD if base in ('TL', 'T', 'TR') else 0) + (SLAB if base in ('BL', 'B', 'BR') else 0)


def build_assets():
    """Fourteen stills in category UI: the nine pieces `ui-panel-tl`, `-t`, `-tr`, `-l`, `-c`, `-r`, `-bl`, `-b`, `-br`, each its own size; five more top edges `ui-panel-t2` to `-t6` that take `-t`'s place now and then; and `ui-panel`, a ready-made panel at 320 x 120 (plus the PAD and the SLAB)."""
    out = []
    for region in REGIONS + TOP_VARIANTS[1:]:
        w, h = piece_size(region)
        make = family(CATEGORY, w, h, (0, 0), place='none', folder=FOLDER)
        base = 'T' if region in TOP_VARIANTS else region
        label = f'Panel, {region}' + (f', {TOP_LABELS[region]}' if region in TOP_VARIANTS else '')
        out.append(make(f'ui-panel-{region.lower()}', label, 'still', [piece(region)],
                        panel={'piece': region, 'body': list(size_of(base)), 'pad': PAD if base in ('TL', 'T', 'TR') else 0, 'slab': SLAB if base in ('BL', 'B', 'BR') else 0}))
    rows = assemble(*SAMPLE)
    make = family(CATEGORY, len(rows[0]), len(rows), (0, 0), place='none', folder=FOLDER)
    out.append(make('ui-panel', 'Panel, ready-made', 'still', [rows], panel={'piece': 'all', 'body': list(SAMPLE), 'pad': PAD, 'slab': SLAB}))
    return out


def write_package(folder):
    sizes = {r.lower(): list(piece_size(r)) for r in REGIONS + TOP_VARIANTS[1:]}
    write_json(folder, 'panel.json', 'The nine-slice panel pieces in this folder. See README.md beside this file for the whole story.',
               {'pieces': sizes, 'order': [r.lower() for r in REGIONS], 'top_edges': [v.lower() for v in TOP_VARIANTS], 'top_edge_weights': list(TOP_WEIGHTS), 'slice': [CW, CH], 'wrap': TILE, 'pad': PAD, 'slab': SLAB, 'minimum': [80, 80],
                'steel': T + 2, 'files': 'ui-panel-PIECE.png, PIECE is a key of `pieces`; the top edge is any of `top_edges` (t, t2 ... t6), picked by `top_edge_weights`; ui-panel.png is a ready-made panel, body 320 x 120'})


def _rgb():
    import extract_poses as ep
    return {c: tuple(int(h[i:i + 2], 16) for i, _ in ((0, 0), (2, 0), (4, 0))) for c, _, _, _, h in ep.ROLES}


def _image(rows, rgb):
    from PIL import Image
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    return im


def preview(path, scale=2):
    """Long panels with the top edge's four pictures mixed at random (two seeds), the four pictures side by side, and a standard button for scale; enlarged."""
    from PIL import Image
    import make_buttons
    rgb = _rgb()
    first = _image(assemble(960, 110, seed=1), rgb)
    second = _image(assemble(960, 110, seed=7), rgb)
    make_buttons.configure('std', 'primary')
    button = _image(make_buttons.assemble('default', 192), make_buttons._rgb())
    variants = [_image(piece(v), rgb) for v in TOP_VARIANTS]
    pad = 16
    strip_w = sum(v.width + pad for v in variants)
    sheet = Image.new('RGBA', (first.width + 2 * pad, pad + first.height + pad + second.height + pad + max(v.height for v in variants) + pad), (24, 30, 40, 255))
    y = pad
    sheet.alpha_composite(first, (pad, y))
    y += first.height + pad
    sheet.alpha_composite(second, (pad, y))
    y += second.height + pad
    x = pad
    for v in variants:
        sheet.alpha_composite(v, (x, y))
        x += v.width + pad
    sheet.alpha_composite(button, (strip_w + pad, y + 20))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='a panel at two sizes beside a button, and the nine pieces, enlarged')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the panel, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
