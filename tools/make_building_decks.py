#!/usr/bin/env python3
"""Flat roofs and balconies for the building kit, in the kit's own format (tools/buildings.py, tools/make_buildings.py): one cell, one level, a 32 x 32 picture anchored at the middle of its base.

    FLAT ROOFS    a deck half a level (8 pixels, one game step) thick that a unit can walk on, with a low parapet round the open sides. Six materials, to go with the kit's two wall families and
                  its three roofs: stone (coursed stone, like the stone walls), timber (a plum plank deck with a plaster parapet in timber, like the timber-framed walls), terracotta, slate and teal
                  (the kit's roof tiles laid flat, for a house with those roofs) and plank (warm planks, like the docks, bridges and scaffolds)
                  deck (no parapet), hatch (a trapdoor), edge-+x/-x/+y/-y (a parapet along one side) and corner-(+x+y, -x-y, +x-y, -x+y) (a parapet along two)
    BALCONIES     a floor half a level thick on the upper storey, open to the air below, with a balustrade on the sides that face out, in three materials: stone (a stone balustrade on corbels,
                  for the stone walls), timber (plaster panels between plum beams and posts, for the timber-framed walls) and plank (a warm plank deck on posts)
                  Named by where the rail is: alcove-x (wall at -x, rail on the other three), alcove-y, run-x and run-y (a rail on the front only, so they join in a row), run-start-x / run-start-y
                  and corner (rail on the two sides that face the camera)
    SUPPORTS      a plum timber post (for the timber walls), a plank post and a stone pillar, one level tall, to stand under a balcony

x runs down and to the right (SE), y down and to the left (SW), as everywhere (tools/buildings.py). A piece is the same picture on every wall: unlike the kit's windows and doors it has no NE/SE twin,
because its sides are named for the world axes. Walkable top = `deck_top` (0.5 level) above the piece's base. Palette roles only, deterministic.

    python3 tools/make_building_decks.py --preview previews/building-decks.png     every piece, then a small house with a flat roof and a balcony
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildings as bd  # noqa: E402
from buildings import Solid, box, hashed  # noqa: E402

FOLDER = 'building-decks'
CATEGORY = 'Buildings'
CELL = 32
LEVEL = 16
DECK = 0.5               # the walkable top, in levels above the piece's base: one game step (8 pixels)
RAIL = 0.82              # the top of a parapet
SIDES = ('+x', '-x', '+y', '-y')


# --- paint ---------------------------------------------------------------------------------------
def plank_role(face, a, b, warm=True):
    n = a // 4
    if face == 'top':
        if a % 4 == 3:
            return 'g' if warm else 'w'
        if warm:
            return ('a', 'e', 'a', 'b', 'e')[hashed(n, b // 16, 3) % 5] if hashed(a, b, 4) % 7 else 'b'
        return ('f', 'e', 'f', 'g', 'f')[hashed(n, b // 16, 3) % 5] if hashed(a, b, 4) % 7 else 'e'      # plum planks, to sit with the timber walls' beams
    if b % 4 == 3:
        return ('g' if face == 'R' else 'w')
    if warm:
        return ('e' if face == 'R' else 'f') if hashed(n, 4) % 3 else ('f' if face == 'R' else 'g')
    return ('g' if face == 'R' else 'w') if hashed(n, 4) % 4 else ('f' if face == 'R' else 'g')


FLAT_ROOF = {'tiles': 'tile', 'slate': 'slate', 'teal': 'teal'}        # style -> the kit's roof style, laid flat


def paint2(solid, face, P):
    x, y, z = P
    a, b, c = int(math.floor(x * LEVEL)), int(math.floor(y * LEVEL)), int(math.floor(z * LEVEL + 1e-6))
    along = int(math.floor((y if face == 'R' else x) * LEVEL + 1e-6))
    if solid.style in ('plank', 'plum'):
        return plank_role('top' if face == 'top' else face, a if face == 'top' else along, b if face == 'top' else c, warm=solid.style == 'plank')
    if solid.style in FLAT_ROOF:
        if face == 'top':
            return bd.roof(FLAT_ROOF[solid.style], 'sR', a, b, True)          # the kit's roof tiles, flat: rows of tile and a bright line along each
        return bd.roof(FLAT_ROOF[solid.style], 'sR' if face == 'R' else 'sL', along, c, True)
    return bd.paint(solid, face, P, True)


def render(solids, levels):
    """The 32-wide picture of one cell and `levels` levels, as palette roles with the kit's outline, and its anchor."""
    fx = fy = 1
    w = 32
    oy = int(round(LEVEL * levels))
    h = 8 * (fx + fy) + oy
    grid = [['.'] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            a, b = (px + 0.5 - 16) / 16.0, (py + 0.5 - oy) / 8.0
            origin = ((a + b) / 2, (b - a) / 2, 0.0)
            best = None
            for s in solids:
                got = s.hit(origin)
                if got and (best is None or got[0] > best[0]):
                    best = (got[0], got[1], s)
            if best is None:
                continue
            t, n, s = best
            face = bd.face_of(n)
            if face:
                grid[py][px] = paint2(s, face, (origin[0] + t, origin[1] + t, t)) or '.'
    return [''.join(r) for r in grid]


# --- the pieces ----------------------------------------------------------------------------------
def deck_of(mat):
    edge = lambda style: [box(0, 1, 0, 1, 0, DECK - 0.07, 'stone'), box(0, 1, 0, 1, DECK - 0.07, DECK, style)]
    return {'stone': [box(0, 1, 0, 1, 0, DECK, 'stone')],
            'tile': edge('tiles'), 'slate': edge('slate'), 'teal': edge('teal'),
            'plank': [box(0, 1, 0, 1, 0, DECK, 'plank')],
            'timber': [box(0, 1, 0, 1, 0, DECK - 0.1, 'timber'), box(0, 1, 0, 1, DECK - 0.1, DECK, 'plum')]}[mat]


def parapet(mat, sides):
    t = 0.14
    spans = {'+x': (1 - t, 1, 0, 1), '-x': (0, t, 0, 1), '+y': (0, 1, 1 - t, 1), '-y': (0, 1, 0, t)}
    if mat == 'timber':                                           # plaster between timber, with a beam along the top
        out = [box(*spans[s], DECK, RAIL - 0.06, 'timber') for s in sides]
        return out + [box(*spans[s], RAIL - 0.06, RAIL, 'wood') for s in sides]
    style = 'plank' if mat == 'plank' else 'stone'
    return [box(*spans[s], DECK, RAIL, style) for s in sides]


def flat_roof(mat, sides=(), hatch=False):
    solids = deck_of(mat) + parapet(mat, sides)
    if hatch:
        solids += [box(0.26, 0.74, 0.26, 0.74, DECK, DECK + 0.07, 'plank'), box(0.44, 0.56, 0.44, 0.56, DECK + 0.07, DECK + 0.11, 'stone')]
    return solids


def balustrade(rails, mat):
    """The rail along the sides in `rails`: a stone balustrade (plinth, balusters, coping), a timber-house rail (plaster panels between plum posts, a plum beam on top) or a plank rail (posts and two rails)."""
    out = []
    top = DECK
    for s in rails:
        horiz = s in ('+x', '-x')
        lo, hi = ((0.86, 1.0) if s in ('+x', '+y') else (0.0, 0.14)) if mat != 'plank' else ((0.9, 1.0) if s in ('+x', '+y') else (0.0, 0.1))

        def seg(a0, a1, z0, z1, style):
            return box(lo, hi, a0, a1, z0, z1, style) if horiz else box(a0, a1, lo, hi, z0, z1, style)
        if mat == 'stone':
            out.append(seg(0, 1, top, top + 0.1, 'stone'))                           # the plinth
            out.append(seg(0, 1, top + 0.38, top + 0.46, 'stone'))                   # the coping
            for k in range(6):
                a0 = 0.06 + k * 0.17
                out.append(seg(a0, a0 + 0.07, top + 0.1, top + 0.38, 'stone'))       # the balusters
        elif mat == 'timber':
            out.append(seg(0, 1, top, top + 0.1, 'plum'))                            # a sill beam
            out.append(seg(0.1, 0.9, top + 0.1, top + 0.36, 'timber'))               # the plaster panel
            out.append(seg(0, 1, top + 0.36, top + 0.46, 'plum'))                    # the top beam
            for a0 in (0.0, 0.46, 0.9):
                out.append(seg(a0, a0 + 0.1, top, top + 0.46, 'plum'))               # posts at the ends and the middle
        else:
            for z0 in (top + 0.14, top + 0.34):
                out.append(seg(0, 1, z0, z0 + 0.07, 'plank'))
    if mat in ('plank', 'timber'):
        style = 'plank' if mat == 'plank' else 'plum'
        for (cx, cy) in sorted({(x, y) for x in (0, 1) for y in (0, 1)}):            # a post wherever a rail meets the edge
            if ('+x' if cx else '-x') in rails or ('+y' if cy else '-y') in rails:
                px0, py0 = (0.86 if cx else 0.0), (0.86 if cy else 0.0)
                out.append(box(px0, px0 + 0.14, py0, py0 + 0.14, 0 if mat == 'plank' else DECK - 0.1, top + (0.5 if mat == 'plank' else 0.5), style))
    return out


def balcony(mat, rails):
    if mat == 'stone':
        # a slab on corbels: the underside is open, and two corbel blocks step down at the wall
        solids = [box(0, 1, 0, 1, 0.16, DECK, 'stone')]
        wall_sides = [s for s in SIDES if s not in rails]
        for s in wall_sides[:2]:
            if s == '-x':
                solids += [box(0, 0.22, 0.12, 0.34, 0.0, 0.16, 'stone'), box(0, 0.22, 0.66, 0.88, 0.0, 0.16, 'stone')]
            elif s == '-y':
                solids += [box(0.12, 0.34, 0, 0.22, 0.0, 0.16, 'stone'), box(0.66, 0.88, 0, 0.22, 0.0, 0.16, 'stone')]
    elif mat == 'timber':
        # a plum plank floor on joists, a plaster fascia along the open edge, like the jetty of a timber house
        solids = [box(0, 1, 0, 1, DECK - 0.1, DECK, 'plum'), box(0.04, 0.96, 0.04, 0.96, DECK - 0.24, DECK - 0.1, 'timber')]
    else:
        solids = [box(0, 1, 0, 1, DECK - 0.1, DECK, 'plank'), box(0.04, 0.96, 0.04, 0.96, DECK - 0.22, DECK - 0.1, 'plank')]
    return solids + balustrade(rails, mat)


def support_post(style='plank'):
    return [box(0.4, 0.6, 0.4, 0.6, 0, 1.0, style), box(0.3, 0.7, 0.3, 0.7, 0, 0.08, style), box(0.3, 0.7, 0.3, 0.7, 0.92, 1.0, style)]


def support_pillar():
    return [box(0.3, 0.7, 0.3, 0.7, 0.06, 0.94, 'stone'), box(0.2, 0.8, 0.2, 0.8, 0, 0.06, 'stone'), box(0.2, 0.8, 0.2, 0.8, 0.94, 1.0, 'stone')]


ROOF_NAMES = {(): 'deck', ('+x',): 'edge-px', ('-x',): 'edge-nx', ('+y',): 'edge-py', ('-y',): 'edge-ny',
              ('+x', '+y'): 'corner-px-py', ('-x', '-y'): 'corner-nx-ny', ('+x', '-y'): 'corner-px-ny', ('-x', '+y'): 'corner-nx-py'}
BALCONIES = {'alcove-x': ('+x', '+y', '-y'), 'alcove-y': ('+x', '+y', '-x'), 'run-x': ('+x',), 'run-y': ('+y',),
             'run-start-x': ('+x', '-y'), 'run-start-y': ('+y', '-x'), 'corner': ('+x', '+y')}
ROOF_LABEL = {'stone': 'Flat roof, stone', 'timber': 'Flat roof, timber house', 'tile': 'Flat roof, terracotta tile', 'slate': 'Flat roof, slate', 'teal': 'Flat roof, teal', 'plank': 'Flat roof, plank'}
BALCONY_LABEL = {'stone': 'Balcony, stone', 'timber': 'Balcony, timber house', 'plank': 'Balcony, plank'}


def kit():
    """[(group id, group label, [(piece id, label, solids, levels, kind, sides)])] in order."""
    groups = []
    for mat in ('stone', 'timber', 'tile', 'slate', 'teal', 'plank'):
        pcs = []
        for sides, name in ROOF_NAMES.items():
            pcs.append((f'{name}', f'{name.replace("-", " ")}', flat_roof(mat, sides), 1, 'roof', list(sides)))
        pcs.append(('hatch', 'hatch', flat_roof(mat, (), True), 1, 'roof', []))
        groups.append((f'bld-flat-roof-{mat}', ROOF_LABEL[mat], pcs))
    for mat in ('stone', 'timber', 'plank'):
        pcs = [(name, name.replace('-', ' '), balcony(mat, rails), 1, 'balcony', list(rails)) for name, rails in BALCONIES.items()]
        groups.append((f'bld-balcony-{mat}', BALCONY_LABEL[mat], pcs))
    groups.append(('bld-supports', 'Balcony supports', [('post-plank', 'plank post', support_post(), 1, 'support', []), ('post-timber', 'plum timber post', support_post('plum'), 1, 'support', []),
                                                        ('pillar-stone', 'stone pillar', support_pillar(), 1, 'support', [])]))
    return groups


_CACHE = {}


def rows_of(gid, pid, solids, levels):
    key = (gid, pid)
    if key not in _CACHE:
        _CACHE[key] = render(solids, levels)
    return _CACHE[key]


def build_assets():
    """Eleven variants sheets in category Buildings (folder building-decks): six flat roofs, three balconies and the supports, 32 x 32 per piece, anchored (16, 24) like the kit."""
    out = []
    for gid, label, pcs in kit():
        frames = [rows_of(gid, pid, solids, lv) for pid, _, solids, lv, _, _ in pcs]
        n = len(frames)
        out.append({'id': gid, 'label': f'Buildings - {label}', 'category': CATEGORY, 'folder': FOLDER, 'kind': 'variants', 'place': 'ground',
                    'names': [p[1] for p in pcs], 'w': CELL, 'h': 32, 'cols': 8, 'rows': -(-n // 8), 'fps': 0, 'anchor': {'x': 16, 'y': 24},
                    'buildings': {'role': 'deck', 'pieces': [p[0] for p in pcs], 'deck_top': DECK, 'kinds': [p[4] for p in pcs], 'sides': [p[5] for p in pcs]},
                    'walkable': gid != 'bld-supports', 'levels': 1, 'frames': frames})
    return out


def write_package(folder):
    from assetkit import write_json
    write_json(folder, 'building-decks.json', 'The flat roofs and balconies in this folder. See README.md beside this file.',
               {'cell': [CELL, CELL], 'anchor': [16, 24], 'deck_top_levels': DECK, 'parapet_top_levels': RAIL,
                'groups': {gid: {'label': label, 'pieces': [{'id': pid, 'kind': kind, 'sides': sides} for pid, _, _, _, kind, sides in pcs]} for gid, label, pcs in kit()}})


# --- preview -------------------------------------------------------------------------------------
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


def demo_house(mat, roof, balcony_mat, post):
    """A small two-storey house, 3 x 3 cells, in `mat` walls ('stone' or 'timber') with a flat roof (parapet and hatch) and a balcony on the front of the upper floor. Returns an image."""
    import make_buildings as mb
    from PIL import Image
    rgb = _rgb()
    kitp = {p['id']: p for p in mb.KIT}
    wall = lambda pid: _image(mb.piece_rows(kitp[f'{mat}-{pid}'], 'NE')[0], rgb)
    imgs = []                                                            # (x, y, level, image)
    X, Y = 3, 3
    for x in range(X):
        for y in range(Y):
            if x in (0, X - 1) or y in (0, Y - 1):
                for lv in range(4):
                    pid = 'plain'
                    if x == X - 1 and y == 1 and lv in (0, 1):
                        pid = 'door-low' if lv == 0 else 'door-up'
                    if lv == 2 and ((x == X - 1 and y == 1) or (y == Y - 1 and x == 1)):
                        pid = 'window'
                    imgs.append((x, y, lv, wall(pid)))
    gid = {g[0]: g for g in kit()}
    pick = lambda g, pid: _image(rows_of(g, pid, *[(p[2], p[3]) for p in gid[g][2] if p[0] == pid][0]), rgb)
    for x in range(X):
        for y in range(Y):
            sides = tuple(sd for sd, edge in (('+x', x == X - 1), ('-x', x == 0), ('+y', y == Y - 1), ('-y', y == 0)) if edge)
            name = 'hatch' if (x, y) == (1, 1) else ROOF_NAMES.get(sides, 'deck')
            imgs.append((x, y, 4, pick(f'bld-flat-roof-{roof}', name)))
    # the balcony: on the +x front, one cell out from the wall, at the height of the second storey (level 2)
    imgs.append((X, 0, 2, pick(f'bld-balcony-{balcony_mat}', 'run-start-x')))
    imgs.append((X, 1, 2, pick(f'bld-balcony-{balcony_mat}', 'run-x')))
    imgs.append((X, 2, 2, pick(f'bld-balcony-{balcony_mat}', 'corner')))
    for yy in (0, 2):
        for lv in (0, 1):
            imgs.append((X, yy, lv, pick('bld-supports', post)))
    imgs.sort(key=lambda t: (t[0] + t[1], t[2]))
    W, H = 16 * (X + 1 + Y) + 40, 8 * (X + 1 + Y) + 16 * 6 + 60
    canvas = Image.new('RGBA', (W, H), (47, 26, 69, 255))
    ox, oy = 16 * Y + 20, 16 * 6 + 30
    for x, y, lv, im in imgs:
        sx = (x - y) * 16 + ox
        sy = (x + y) * 8 + 8 - lv * 16 + oy - 24
        canvas.alpha_composite(im, (sx, sy - 8))
    return canvas


HOUSES = (('stone', 'stone', 'stone', 'pillar-stone', 'stone walls, stone roof and balcony'),
          ('timber', 'timber', 'timber', 'post-timber', 'timber-framed walls, timber roof and balcony'),
          ('timber', 'tile', 'plank', 'post-plank', 'timber walls, terracotta flat roof, plank balcony'),
          ('stone', 'slate', 'stone', 'pillar-stone', 'stone walls, slate flat roof'))


def demo_rows():
    from PIL import Image
    ims = [(demo_house(*h[:4]), h[4]) for h in HOUSES]
    return ims


def preview(path, scale=3):
    from PIL import Image, ImageDraw
    rgb = _rgb()
    cols = 10
    cells = []
    for gid, label, pcs in kit():
        for pid, plabel, solids, lv, kind, sides in pcs:
            cells.append((f'{gid.replace("bld-", "")}\n{pid}', _image(rows_of(gid, pid, solids, lv), rgb)))
    pad, lw = 8, 40
    cw, ch = 32 * scale + pad, 32 * scale + lw
    rows = -(-len(cells) // cols)
    houses = demo_rows()
    dscale = 3
    hw, hh = houses[0][0].width * dscale, houses[0][0].height * dscale
    W = max(cols * cw + pad, 2 * (hw + pad) + pad)
    H = rows * ch + pad + 2 * (hh + 24 + pad) + pad
    sheet = Image.new('RGBA', (W, H), (36, 38, 56, 255))
    d = ImageDraw.Draw(sheet)
    for n, (label, im) in enumerate(cells):
        x, y = pad + (n % cols) * cw, pad + (n // cols) * ch
        sheet.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y))
        d.text((x, y + 32 * scale + 2), label, fill=(230, 220, 200, 255))
    y0 = rows * ch + pad
    for n, (im, label) in enumerate(houses):
        x, y = pad + (n % 2) * (hw + pad), y0 + (n // 2) * (hh + 24 + pad)
        d.text((x, y), label, fill=(230, 220, 200, 255))
        sheet.alpha_composite(im.resize((im.width * dscale, im.height * dscale), Image.NEAREST), (x, y + 18))
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the roofs and balconies ->', args.preview)


if __name__ == '__main__':
    main()
