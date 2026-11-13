#!/usr/bin/env python3
"""Settings controls to go with the buttons and the panel: a slider (track, fill and knob) and an on/off toggle, in the same old steel bevel, with moss and a gold bead. Palette roles only.

    slider    TRACK in three pieces that join (a left cap, a middle that wraps, a right cap), 16 high; FILL in two (a left cap and a middle that wraps) that lies on the track in the same place,
              inset 3 pixels, cut short wherever the value is (the knob covers its right end); and a KNOB, 24 x 24, in three states (default, hovered, pressed)
    toggle    one 44 x 22 picture per state: off and on, each default and hovered. On is the lit blue trough with the knob at the right, off a dark trough with the knob at the left.

    python3 tools/make_ui_controls.py --preview previews/ui-controls.png     every piece enlarged, then a settings panel using them at the size of the buttons
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

FOLDER = 'ui-controls'
CATEGORY = 'UI'
LIGHT = (-0.45, -0.89)
TH = 16                  # track height
TR = 7                   # its corner radius
CAP = 8                  # a track cap's width
MID = 32                 # the middle's width; it wraps
INSET = 3                # fill inset from the track's edge
KNOB = 24
TOG_W, TOG_H = 44, 22

FRAME = 'kllpp'           # steel, shaded side to specular
MOSS = ['z', 'A']
MOSS_X = [(4, 'z'), (5, 'A'), (6, 'z'), (19, 'A'), (20, 'z'), (21, 'z'), (22, 'A')]      # moss on the top edge, x in the wrap
DRIP_X = [(5, 3), (20, 2)]                                                    # x in the wrap, how far it hangs down inside the trough


def canvas(w, h):
    return [['.'] * w for _ in range(h)]


def rows(g):
    return [''.join(r) for r in g]


def sdf(x, y, w, h, r):
    """Signed distance (negative inside) of pixel (x, y)'s centre to a w x h rounded rectangle."""
    px, py = x + 0.5 - w / 2, y + 0.5 - h / 2
    qx, qy = abs(px) - (w / 2 - r), abs(py) - (h / 2 - r)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


def normal(x, y, w, h, r):
    e = 0.4
    gx = sdf(x + e, y, w, h, r) - sdf(x - e, y, w, h, r)
    gy = sdf(x, y + e, w, h, r) - sdf(x, y - e, w, h, r)
    n = math.hypot(gx, gy) or 1
    return gx / n, gy / n


def shade(nx, ny, ramp):
    """A ramp from lit (index 0) to shaded for a surface with the normal (nx, ny) on the screen."""
    t = 0.5 + 0.5 * (nx * LIGHT[0] + ny * LIGHT[1])
    return ramp[max(0, min(len(ramp) - 1, int(t * len(ramp))))]


# --- the track and fill ----------------------------------------------------------------------------
def bar_xy(piece, x, w):
    """The x in a long bar, and the x in the wrap, for a column of a piece (a cap, or the wrapping middle)."""
    if piece == 'mid':
        return 500 + x, x
    if piece == 'left':
        return x, x
    return 1000 - (w - x), 1000 - (w - x)


def track_px(piece, w, x, y, trough='wx'):
    """One pixel of the track. Outline, then a steel bevel 1 pixel thick, then a dark trough with its top row in shadow."""
    X, wx = bar_xy(piece, x, w)
    W = 1000 if piece == 'right' else (1000 if piece == 'mid' else 2000)
    off = 0 if piece != 'right' else 0
    d = -sdf(X, y, W if piece != 'left' else 2000, TH, TR)
    if piece == 'mid':
        d = -sdf(X, y, 1000, TH, TR)
    elif piece == 'right':
        d = -sdf(X, y, 1000, TH, TR)
        # the bar spans 0..1000 and the right cap is its last w columns
    elif piece == 'left':
        d = -sdf(X, y, 1000, TH, TR)
    if d < 0:
        return '.'
    if d < 1:
        return 'O'
    if d < 2:
        nx, ny = normal(X, y, 1000, TH, TR)
        return shade(nx, ny, FRAME)
    # the trough
    if d < 3:
        return 'O'                                 # a hard shadow under the lip
    row = y - 3
    ch = trough[0] if row > 0 else 'O'
    if row == 1:
        ch = trough[0]
    if row >= 2:
        ch = trough[-1] if row > TH - 8 else trough[0]
    return ch


def fill_px(piece, w, x, y):
    """One pixel of the fill: a lit blue bar with a cyan top row, 2 pixels inside the trough."""
    X, wx = bar_xy(piece, x, w)
    fh = TH - 2 * INSET
    yy = y - INSET
    if yy < 0 or yy >= fh:
        return '.'
    d = -sdf(X, yy, 1000, fh, fh / 2 - 0.5)
    if d < 0:
        return '.'
    if d < 1:
        return 'm' if yy > 0 else 'n'
    ramp = 'onnmk'
    return ramp[min(len(ramp) - 1, yy)] if yy < len(ramp) - 1 else 'k'


def decorate_track(g, piece, w):
    """Moss over the top edge and a drip or two, the same wrap in every middle."""
    for x in range(w):
        X = x if piece != 'mid' else x
        wx = (x if piece == 'left' else (x if piece == 'mid' else 1000 - (w - x))) % MID if piece != 'right' else (1000 - (w - x)) % MID
        for mx, ch in MOSS_X:
            if wx == mx and g[0][x] in 'OklptT.':
                if g[1][x] != '.':
                    g[0][x] = ch
                    g[1][x] = ch if g[1][x] in FRAME else g[1][x]
        for mx, depth in DRIP_X:
            if wx == mx and piece != 'left' or (piece == 'left' and wx == mx):
                for k in range(depth):
                    if 3 + k < TH - 3 and g[3 + k][x] in 'wxO':
                        g[3 + k][x] = 'z' if k < depth - 1 else 'A'


def track_piece(piece):
    w = {'left': CAP, 'mid': MID, 'right': CAP}[piece]
    g = canvas(w, TH)
    for y in range(TH):
        for x in range(w):
            g[y][x] = track_px(piece, w, x, y)
    decorate_track(g, piece, w)
    return rows(g)


def fill_piece(piece):
    w = {'left': CAP, 'mid': MID}[piece]
    g = canvas(w, TH)
    for y in range(TH):
        for x in range(w):
            g[y][x] = fill_px(piece, w, x, y)
    return rows(g)


# --- the knob and toggle ------------------------------------------------------------------------------
def disc(d, bead, ring='kllpp', body='tpllk', rim=None):
    """A steel disc of diameter d with a round bead at its middle, lit from the upper left, and a dab of moss on the rim."""
    g = canvas(d, d)
    r = d / 2
    for y in range(d):
        for x in range(d):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            dist = math.hypot(dx, dy)
            if dist > r:
                continue
            if dist > r - 1:
                g[y][x] = 'O'
                continue
            n = (dx / (dist or 1), dy / (dist or 1))
            if dist > r - 2.6:
                g[y][x] = shade(n[0], n[1], ring)
                continue
            # the face: a shallow dome
            t = 0.5 - 0.5 * ((dx * LIGHT[0] + dy * LIGHT[1]) / r)
            g[y][x] = body[max(0, min(len(body) - 1, int(t * len(body))))]
    br = d * 0.2
    for y in range(d):
        for x in range(d):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            dist = math.hypot(dx, dy)
            if dist <= br + 1 and dist > br:
                g[y][x] = 'O'
            elif dist <= br:
                t = 0.5 - 0.5 * ((dx * LIGHT[0] + dy * LIGHT[1]) / (br or 1))
                g[y][x] = bead[max(0, min(len(bead) - 1, int(t * len(bead))))]
    # moss on the upper left rim
    for (x, y, c) in ((int(r * 0.45), 1, 'z'), (int(r * 0.45) + 1, 1, 'A'), (int(r * 0.2), 2, 'A'), (int(r * 0.7), 1, 'z')):
        if g[y][x] not in '.':
            g[y][x] = c
    return g


KNOB_STATES = {
    'default': dict(bead='dbba', body='tplkk'),
    'hovered': dict(bead='rorq', body='tptlk'),
    'pressed': dict(bead='oqqs', body='lkkww'),
}


def knob(state):
    s = KNOB_STATES[state]
    return rows(disc(KNOB, s['bead'], body=s['body']))


def toggle(on, hovered):
    w, h = TOG_W, TOG_H
    g = canvas(w, h)
    frame = 'lppt' if hovered else FRAME
    for y in range(h):
        for x in range(w):
            d = -sdf(x, y, w, h, h / 2 - 1)
            if d < 0:
                continue
            if d < 1:
                g[y][x] = 'O'
            elif d < 2:
                nx, ny = normal(x, y, w, h, h / 2 - 1)
                g[y][x] = shade(nx, ny, frame)
            elif d < 3:
                g[y][x] = 'O'
            else:
                row = y - 3
                if on:
                    ramp = 'onnmmmkkk' if hovered else 'nnmmmkkkk'
                    g[y][x] = ramp[min(len(ramp) - 1, max(0, row))] if row < len(ramp) else 'k'
                else:
                    ramp = 'xwwwwwww' if not hovered else 'wkkkkwww'
                    g[y][x] = 'O' if row < 1 else ramp[min(len(ramp) - 1, row)]
    k = disc(16, 'dbba' if on else 'ggfw', body='tplkk' if on else 'plkkw')
    kx = w - 16 - 3 if on else 3
    for y in range(16):
        for x in range(16):
            if k[y][x] != '.':
                g[y + 3][kx + x] = k[y][x]
    # a little moss over the top edge, in the same place on every state
    for x, c in ((6, 'z'), (7, 'A'), (14, 'z'), (31, 'A'), (32, 'z')):
        if g[0][x] == 'O' or g[1][x] == 'O':
            pass
        if g[1][x] != '.':
            g[1][x] = c
    return rows(g)


def build_assets():
    """Eleven stills in category UI: `ui-slider-track-left`, `-mid`, `-right`; `ui-slider-fill-left`, `-mid`; `ui-slider-knob-default`, `-hovered`, `-pressed`; and `ui-toggle-off`, `-off-hovered`, `-on`, `-on-hovered`."""
    out = []

    def add(id, label, w, h, rows_, anchor=(0, 0)):
        out.append(family(CATEGORY, w, h, anchor, place='none', folder=FOLDER)(id, label, 'still', [rows_]))
    for piece, w in (('left', CAP), ('mid', MID), ('right', CAP)):
        add(f'ui-slider-track-{piece}', f'Slider track, {piece}', w, TH, track_piece(piece))
    for piece, w in (('left', CAP), ('mid', MID)):
        add(f'ui-slider-fill-{piece}', f'Slider fill, {piece}', w, TH, fill_piece(piece))
    for st in KNOB_STATES:
        add(f'ui-slider-knob-{st}', f'Slider knob, {st}', KNOB, KNOB, knob(st), (KNOB // 2, KNOB // 2))
    for on in (False, True):
        for hov in (False, True):
            add(f"ui-toggle-{'on' if on else 'off'}{'-hovered' if hov else ''}", f"Toggle {'on' if on else 'off'}{', hovered' if hov else ''}", TOG_W, TOG_H, toggle(on, hov))
    return out


def write_package(folder):
    write_json(folder, 'ui-controls.json', 'The slider and toggle pieces in this folder. See README.md beside this file.',
               {'slider': {'track_height': TH, 'cap': CAP, 'mid': MID, 'fill_inset': INSET, 'knob': [KNOB, KNOB], 'knob_states': list(KNOB_STATES)},
                'toggle': {'size': [TOG_W, TOG_H], 'states': ['off', 'off-hovered', 'on', 'on-hovered']}})


# --- preview ------------------------------------------------------------------------------------------
def _img(rows_, rgb):
    from PIL import Image
    im = Image.new('RGBA', (len(rows_[0]), len(rows_)), (0, 0, 0, 0))
    for y, row in enumerate(rows_):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), rgb[c] + (255,))
    return im


def slider_image(width, value, rgb, state='default'):
    from PIL import Image
    im = Image.new('RGBA', (width, KNOB), (0, 0, 0, 0))
    ty = (KNOB - TH) // 2

    def lay(piece_rows, x, y=ty, w=None):
        p = _img(piece_rows, rgb)
        if w is not None and w < p.width:
            p = p.crop((0, 0, w, p.height))
        im.alpha_composite(p, (x, y))
    lay(track_piece('left'), 0)
    x = CAP
    while x < width - CAP:
        lay(track_piece('mid'), x, w=width - CAP - x)
        x += MID
    lay(track_piece('right'), width - CAP)
    fw = int((width - KNOB) * value) + KNOB // 2
    lay(fill_piece('left'), 0, w=min(CAP, fw))
    x = CAP
    while x < fw:
        lay(fill_piece('mid'), x, w=fw - x)
        x += MID
    im.alpha_composite(_img(knob(state), rgb), (fw - KNOB // 2, 0))
    return im


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    pieces = ([('track L', _img(track_piece('left'), rgb)), ('track M', _img(track_piece('mid'), rgb)), ('track R', _img(track_piece('right'), rgb)),
               ('fill L', _img(fill_piece('left'), rgb)), ('fill M', _img(fill_piece('mid'), rgb))]
              + [(f'knob {s}', _img(knob(s), rgb)) for s in KNOB_STATES]
              + [(f"toggle {'on' if o else 'off'}{' hov' if h else ''}", _img(toggle(o, h), rgb)) for o in (False, True) for h in (False, True)])
    pad = 14
    big_w = 1180
    sheet = Image.new('RGBA', (big_w, 900), (47, 26, 69, 255))
    d = ImageDraw.Draw(sheet)
    x, y, rowh = pad, pad, 0
    for label, im in pieces:
        e = im.resize((im.width * scale // 2 * 1, im.height * scale // 2 * 1), Image.NEAREST) if im.width > 60 else im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        if x + e.width > big_w - pad:
            x, y, rowh = pad, y + rowh + 28, 0
        sheet.alpha_composite(e, (x, y + 14))
        d.text((x, y), label, fill=(230, 220, 200, 255))
        x += max(e.width, 80) + 14
        rowh = max(rowh, e.height + 14)
    # in use, 2x like the game: three sliders and two toggles beside labels
    y0 = y + rowh + 40
    d.text((pad, y0 - 18), 'in use, 2x', fill=(230, 220, 200, 255))
    for i, (label, v, st) in enumerate((('Volume', 0.1, 'default'), ('Music volume', 1.0, 'hovered'), ('SFX volume', 0.62, 'pressed'))):
        d.text((pad, y0 + i * 62 + 18), label, fill=(230, 220, 200, 255))
        s = slider_image(200, v, rgb, st)
        sheet.alpha_composite(s.resize((s.width * 2, s.height * 2), Image.NEAREST), (200, y0 + i * 62))
        d.text((200 + 420, y0 + i * 62 + 18), f'{int(v * 100)}%', fill=(230, 220, 200, 255))
    for i, (label, on, hov) in enumerate((('Show health bars', True, False), ('Screen shake', False, False), ('Show grid', True, True), ('Show grid', False, True))):
        t = _img(toggle(on, hov), rgb)
        sheet.alpha_composite(t.resize((t.width * 2, t.height * 2), Image.NEAREST), (780, y0 + i * 52))
        d.text((660, y0 + i * 52 + 14), label, fill=(230, 220, 200, 255))
    sheet.crop((0, 0, big_w, y0 + 4 * 52 + 20)).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the controls ->', args.preview)


if __name__ == '__main__':
    main()
