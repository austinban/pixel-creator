#!/usr/bin/env python3
"""Reusable menu buttons, drawn after the game's main menu: a dark purple bar in an old steel bevel with gold corner brackets, worn and mossy, that lights up blue.

The button is 48 pixels high and as wide as you need, so it is made in three pieces that join: a LEFT cap (40 wide), a MIDDLE (64 wide, and it wraps on itself, so any number
of them in a row join with no seam) and a RIGHT cap (40 wide, its own picture, not the left one flipped: the moss and the wear are different at each end).
Draw the left cap, as many middles as fill the width (the last one cut short if need be), then the right cap.
Three states, each one row of the parts sheet:
    default   the purple bar
    hovered   the bright blue bar, lit along the top (the menu's focused row)
    active    a dark blue bar in a cyan glow (the chosen or current row, and a pressed button)
The wear is the same in every state (moss over the top edge with a few drips, scratches, chipped bevel, verdigris on the gold, a vine at each end), so they swap without anything jumping.
`ui-button` is the three states already put together at one width (256 x 48), for a button that does not need another. The button has no label: the game draws its own text over the middle.
Palette roles only.

    python3 tools/make_buttons.py --preview previews/buttons.png     the three states at three widths, with a label, and the parts sheet
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

H = 48                  # the button's height, the slab under it included
HB = 44                 # the body, lit from the upper left; the slab under it is the other 4 rows
SLAB = H - HB
R = 14                  # the radius of the rounded ends
CAP = 40                # a cap's width
MID = 64                # the middle's width; it wraps
WIDE = 256              # the ready-made width
FOLDER = 'buttons'
CATEGORY = 'UI'
WEDGE = 17              # a gold bracket's legs
JOIN = 24               # where in the middle's wrap the left cap's inner edge picks up, so the wear carries on across the join
LIGHT = (-0.45, -0.89)  # towards the light, on the screen

# per state: the steel frame from its shaded side to its specular (4 roles), the fill's ramp from the top to the bottom, and the slab's side face from its top row down
PRIMARY = {
    'default': dict(label='Default', frame='klpt', ramp='lkkwx', face='kwxx'),
    'hovered': dict(label='Hovered', frame='klpt', ramp='onnmk', face='mkwx'),
    'active': dict(label='Active', frame='mnot', ramp='nmmkw', face='mkkw'),
}
# low contrast: the same button with its values squeezed together, a quiet one to sit behind a busy screen; the gold goes to a dull plum and the moss to deep teal
LOW = {
    'default': dict(label='Default', frame='xwkl', ramp='kkwwx', face='wxxx'),
    'hovered': dict(label='Hovered', frame='wklp', ramp='lkkwk', face='kwxx'),
    'active': dict(label='Active', frame='kllp', ramp='lklkw', face='kwxx'),
}
# red: the palette has no pure red, so the purple and blue become its coral, magenta and plum family; the gold and the moss stay
RED = {
    'default': dict(label='Default', frame='gect', ramp='ehhgu', face='ghuu'),
    'hovered': dict(label='Hovered', frame='gect', ramp='cceeh', face='hgug'),
    'active': dict(label='Active', frame='hijt', ramp='jiihg', face='hguu'),
}
COLOURWAYS = {
    'primary': dict(label='Primary', states=PRIMARY, remap={}),
    'low': dict(label='Low contrast', states=LOW, remap={'d': 'f', 'b': 'g', 'a': 'w', 'z': 'B', 'A': 's', 'B': 'D'}),
    'red': dict(label='Red', states=RED, remap={}),
}
# heights (the body and its slab) and widths: the corner radius and the gold brackets follow the height
HEIGHTS = {'std': dict(label='Standard', h=48, slab=4), 'short': dict(label='Short', h=32, slab=3),
           'compact': dict(label='Compact', h=40, slab=4), 'icon': dict(label='Icon', h=36, slab=3)}
WIDTHS = {'sm': 128, 'md': 192, 'lg': 256, 'xl': 384}
GRID_HEIGHTS = ('std', 'short')                       # the grid: these heights at each of WIDTHS
# sizes of their own, by name: (height, width name, width). A button this narrow is two half-caps, no middle.
EXTRA = {'short-xs': ('short', 'xs', 48), 'compact-sm': ('compact', 'sm', 112), 'icon-sq': ('icon', 'sq', 36)}
STATES = PRIMARY
REMAP = {}
ORDER = ['default', 'hovered', 'active']
PIECES = ['left', 'middle', 'right']

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
DRIPS = [(5, 4), (14, 9), (33, 6), (47, 3), (58, 10)]       # x in the wrap, how far down a drip of moss hangs
SCRATCHES = [(12, 14, 6, 1), (40, 28, 7, -1), (55, 19, 5, 1), (27, 34, 4, 1), (3, 24, 5, -1)]       # x, y, length, slope
CHIPS = [(20, 1), (21, 1), (47, 2), (58, 41), (59, 41), (8, 40), (36, 2)]                           # bits of the bevel gone
VINE_LEFT = [(9, 6), (9, 7), (10, 8), (10, 9), (9, 10), (9, 11), (8, 12), (8, 13), (9, 14), (9, 15), (10, 16), (10, 17)]
VINE_RIGHT = [(8, 5), (8, 6), (7, 7), (7, 8), (8, 9), (8, 10), (9, 11), (9, 12), (8, 13), (8, 14)]
LEAVES_LEFT = [(11, 9, 'z'), (7, 12, 'z'), (11, 16, 'A'), (8, 14, 'A')]
LEAVES_RIGHT = [(6, 8, 'z'), (10, 11, 'A'), (7, 14, 'z')]


def configure(height, colourway):
    """Set the button's height ('std' or 'short') and colourway ('primary', 'low' or 'red') for the drawing that follows."""
    global H, HB, SLAB, R, WEDGE, STATES, REMAP, CHIPS, SCRATCH, DRIP
    H, SLAB = HEIGHTS[height]['h'], HEIGHTS[height]['slab']
    HB = H - SLAB
    R = round(HB * 14 / 44)
    WEDGE = round(HB * 17 / 44)
    STATES = COLOURWAYS[colourway]['states']
    REMAP = COLOURWAYS[colourway]['remap']
    CHIPS = [(20, 1), (21, 1), (47, 2), (58, HB - 3), (59, HB - 3), (8, HB - 4), (36, 2)]
    SCRATCH = [(x, round(y * HB / 44), ln, sl) for x, y, ln, sl in SCRATCHES]
    DRIP = [(x, max(2, round(dl * HB / 44))) for x, dl in DRIPS]


configure('std', 'primary')


def rnd(*a):
    """A repeatable number in [0, 1) from some integers."""
    n = 0x9e3779b1
    for v in a:
        n = ((n ^ (v & 0xffffffff)) * 0x85ebca6b + 0x27d4eb2f) & 0xffffffff
        n ^= n >> 15
    return (n & 0xffff) / 65536


def moss_depth(X):
    s = math.sin(2 * math.pi * X * 2 / MID + 0.7) + 0.5 * math.sin(2 * math.pi * X * 5 / MID + 2) + 0.3 * math.sin(2 * math.pi * X * 9 / MID)
    return max(0, round(1.2 + 1.5 * s))


def ramp_role(state, y, x, lift=0.0):
    """The fill at row y (the fill runs from row 4 down to the frame at the bottom), dithered between the ramp's steps."""
    ramp = STATES[state]['ramp']
    pos = (y - 4) / (HB - 9) * (len(ramp) - 1) - lift
    pos += (BAYER[y % 4][x % 4] / 16 - 0.5) * 0.9
    return ramp[max(0, min(len(ramp) - 1, int(math.floor(pos + 0.5))))]


def geom(kind, c, y):
    """How far inside the body's edge the pixel is (below 0: outside it) and which way the edge faces there, for a cap's column c (kind 'L' or 'R') or the middle's ('M')."""
    if y < 0 or y >= HB:
        return -1.0, (0.0, 0.0)
    py = y + 0.5
    best = (py, (0.0, -1.0)) if py <= HB - py else (HB - py, (0.0, 1.0))
    if kind == 'M':
        return best
    ex = (c if kind == 'L' else CAP - 1 - c) + 0.5            # across from the cap's own end
    sgn = -1.0 if kind == 'L' else 1.0
    if ex < R and (py < R or py > HB - R):
        cy = R if py < R else HB - R
        dx, dy = R - ex, py - cy
        r = math.hypot(dx, dy) or 1e-6
        return R - r, (sgn * dx / r, dy / r)
    if ex < best[0]:
        best = (ex, (sgn, 0.0))
    return best


def pixel(state, c, y, kind):
    """The role at column c, row y of a cap (kind 'L' or 'R') or of the middle ('M'). '.' is empty."""
    s = STATES[state]
    end = {'L': c, 'R': CAP - 1 - c, 'M': 999}[kind]
    X = {'L': (c + JOIN) % MID, 'R': c, 'M': c}[kind]            # the place in the wrap, so the wear carries on over the joins
    dist, (nx, ny) = geom(kind, c, y)
    if dist < 0:
        # under the body: the slab's side face, the body's own shape shifted down
        d2, _ = geom(kind, c, y - SLAB)
        if d2 < 0:
            return '.'
        return 'O' if d2 < 1 else s['face'][max(0, min(len(s['face']) - 1, y - (HB - 2)))]
    d = int(dist)
    top = y
    facing = nx * LIGHT[0] + ny * LIGHT[1]                        # 1 where the edge faces the light, -1 where it faces away
    role = None
    # the gold brackets, in the corners at each end
    if end < 999:
        ey = min(y, HB - 1 - y)
        if end + ey <= WEDGE:
            t = WEDGE - (end + ey)
            role = 'O' if (d == 0 or t == 0) else 'a' if t == 1 else 'd' if (d == 1 or t == 2) else 'b'
            if role in 'bd' and rnd(kind == 'L', end, ey, 7) < 0.16:
                role = 'B' if rnd(end, ey, 9) < 0.5 else 'A'          # verdigris on the gold
            elif role in 'bd' and rnd(kind == 'L', end, ey, 3) < 0.06:
                role = 'a'                                           # a worn spot
    if role is None:
        if d == 0 or d == 3:
            role = 'O'
        elif d in (1, 2):
            i = 3 if facing > 0.93 else 2 if facing > 0.25 else 1 if facing > -0.35 else 0
            role = s['frame'][max(0, i - (d == 2))]
        else:
            lift = 0.0
            if d == 4:
                lift = -0.9 if facing > 0.25 else 0.6 if facing < -0.25 else 0.0      # a shadow under the frame on the lit side, a bounce of light on the other
            elif d == 5 and facing > 0.25:
                lift = -0.5
            role = ramp_role(state, y, X, lift)
            for sx, sy, ln, sl in SCRATCH:                          # scratches: a lighter line
                for i in range(ln):
                    if (sx + i) % MID == X and sy + i * sl == y and d >= 5:
                        role = ramp_role(state, y, X, lift=0.9)
    if (X, y) in CHIPS and d in (1, 2):
        role = s['ramp'][-1]
    # moss over the top edge: a ragged hem, thicker in the corners, with a few drips that taper
    depth = moss_depth(X)
    if end < 14:
        depth += 3 - end // 5
    for dx, dl in DRIPS:
        if X == dx:
            depth = max(depth, dl)
        elif (X - dx) % MID in (1, MID - 1):
            depth = max(depth, min(3, dl // 2 + 1))
    if top < depth and d >= 0:
        role = 'B' if top == depth - 1 and depth > 1 else ('z' if rnd(X, y, 5) < 0.3 else 'A')
    # a vine at each end, over the bracket
    if kind != 'M':
        path, leaves = (VINE_LEFT, LEAVES_LEFT) if kind == 'L' else (VINE_RIGHT, LEAVES_RIGHT)
        for px_, py_ in path:
            if (px_, py_) == (end, y) and y < HB - 8:
                role = 'A' if (y % 3) else 'B'
        for px_, py_, ch in leaves:
            if (px_, py_) == (end, y) and y < HB - 8:
                role = ch
    return REMAP.get(role, role)


def piece(state, which):
    """One piece as H rows of roles."""
    kind = {'left': 'L', 'right': 'R', 'middle': 'M'}[which]
    width = CAP if kind != 'M' else MID
    return [''.join(pixel(state, c, y, kind) for c in range(width)) for y in range(H)]


def assemble(state, width):
    """A whole button `width` wide: left cap, as many middles as it takes, right cap. Under two caps wide it is two halves that meet in the middle."""
    if width < 2 * CAP:
        half = width // 2
        return [''.join(pixel(state, c, y, 'L') for c in range(half)) + ''.join(pixel(state, CAP - (width - x), y, 'R') for x in range(half, width)) for y in range(H)]
    left, mid, right = piece(state, 'left'), piece(state, 'middle'), piece(state, 'right')
    inner = width - 2 * CAP
    return [left[y] + (mid[y] * (-(-inner // MID)))[:inner] + right[y] for y in range(H)]


def sheet_id(colourway, height, width):
    return f'ui-button-{colourway}-{height}-{width}'


def build_assets():
    """33 buttons: 3 colourways by (2 heights by 4 widths, and the 3 sizes of their own), each its own sheet of its 3 states (default, hovered, active), `ui-button-COLOURWAY-HEIGHT-WIDTH`."""
    out = []
    for colourway, cw in COLOURWAYS.items():
        sizes = [(h, wn, WIDTHS[wn]) for h in GRID_HEIGHTS for wn in WIDTHS] + list(EXTRA.values())
        for height, width, w in sizes:
            configure(height, colourway)
            make = family(CATEGORY, w, H, (0, 0), place='none', folder=FOLDER)
            out.append(make(sheet_id(colourway, height, width), f"Button, {cw['label'].lower()}, {HEIGHTS[height]['label'].lower()}, {width}", 'variants', [assemble(st, w) for st in ORDER],
                            names=[STATES[st]['label'] for st in ORDER], cols=3, rows=1,
                            button={'colourway': colourway, 'height': height, 'width': width, 'states': ORDER, 'cell': [w, H], 'body': HB}))
    configure('std', 'primary')
    return out


def write_package(folder):
    sizes = {f'{h}-{wn}': [WIDTHS[wn], HEIGHTS[h]['h']] for h in GRID_HEIGHTS for wn in WIDTHS}
    sizes.update({name: [w, HEIGHTS[h]['h']] for name, (h, wn, w) in EXTRA.items()})
    body = {f'{h}-{wn}': HEIGHTS[h]['h'] - HEIGHTS[h]['slab'] for h in GRID_HEIGHTS for wn in WIDTHS}
    body.update({name: HEIGHTS[h]['h'] - HEIGHTS[h]['slab'] for name, (h, wn, w) in EXTRA.items()})
    write_json(folder, 'buttons.json', 'The button sheets in this folder. See README.md beside this file for the whole story.',
               {'colourways': list(COLOURWAYS), 'states': ORDER, 'cells': sizes, 'body': body,
                'files': 'ui-button-COLOURWAY-SIZE.png, three cells side by side: default, hovered, active; SIZE is HEIGHT-WIDTH, a key of `cells`'})


def _rgb():
    import extract_poses as ep
    return {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}


def _image(rows, rgb):
    from PIL import Image
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    return im


def preview(path, scale=2):
    """Write the 24 sheets beside `path` (a folder) and one contact sheet, `path`/contact.png, with every button in its three states."""
    from PIL import Image, ImageDraw
    rgb = _rgb()
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for colourway in COLOURWAYS:
        for height, width, w in [(h, wn, WIDTHS[wn]) for h in GRID_HEIGHTS for wn in WIDTHS] + list(EXTRA.values()):
            configure(height, colourway)
            sheet = Image.new('RGBA', (3 * w, H), (0, 0, 0, 0))
            for i, st in enumerate(ORDER):
                sheet.alpha_composite(_image(assemble(st, w), rgb), (i * w, 0))
            sheet.save(folder / (sheet_id(colourway, height, width) + '.png'))
            rows.append((colourway, height, width, sheet))
    configure('std', 'primary')
    # contact sheet: per colourway a block; per height a row of the four widths' default, then hovered, then active
    blocks = []
    for colourway in COLOURWAYS:
        mine = [r for r in rows if r[0] == colourway]
        block_h = sum(sh.height + 6 for _, _, _, sh in mine if _ == colourway) // 1
        blocks.append(mine)
    pad = 8
    total_w = max(sh.width for *_, sh in rows) + 2 * pad
    total_h = sum(sh.height + pad for *_, sh in rows) + pad
    contact = Image.new('RGBA', (total_w, total_h), (30, 38, 40, 255))
    y = pad
    for colourway, height, width, sh in rows:
        contact.alpha_composite(sh, (pad, y))
        y += sh.height + pad
    contact.save(folder / 'contact-1x.png')
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='a folder to write the 24 sheets and a contact sheet to')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the buttons ->', args.preview)


if __name__ == '__main__':
    main()
