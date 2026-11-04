#!/usr/bin/env python3
"""A kit of building tiles for the isometric ground, in the ground tiles' own format, to build houses, towers and whole streets from.

Every piece is one cell and one level: a 32 x 32 cube (the same size and projection as a ground tile; the tall ones are 32 x 48), drawn by
tools/buildings.py with the ground's palette and a texture that repeats every 16 pixels, so pieces line up when they are stacked or set side by side.
A storey is two levels. A piece sits on the ground tile of its cell, or on the piece below it, the way ground tiles sit on each other.

NE and SE: like the characters and the bridge, every piece that has a direction comes in two drawn versions.
    NE   the feature is on the wall that runs NE-SW (the right-hand wall as the camera sees it); a roof slope or ridge that runs that way
    SE   the feature is on the wall that runs NW-SE (the left-hand wall);                          a roof slope or ridge that runs that way
NW and SW are those two flipped, as for the characters. A piece with no direction (a plain block, a corner, a spire) is the same picture in both.

    python3 tools/make_buildings.py --kit previews/building-kit.png        every piece, NE beside SE, in groups
    python3 tools/make_buildings.py --city previews/building-city.png      a street built only from the pieces
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildings as bd  # noqa: E402
from buildings import Solid, box, pyramid, plane  # noqa: E402
import extract_poses as ep  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ORIENTS = ('NE', 'SE')
SIDE = {'NE': 'R', 'SE': 'L'}                        # the wall the feature is on
ROOF_END = {'tile': 'timber', 'slate': 'stone', 'teal': 'stone', 'dark': 'stone'}      # what a roof's end (a gable) is made of


# --- the walls ---------------------------------------------------------------------------------
def wall(style, features, orient):
    return [box(0, 1, 0, 1, 0, 1, style, [(SIDE[orient], *f) if isinstance(f[0], float) or isinstance(f[0], int) else f for f in features])]


def both(kind, a=(0.3, 0.7), z=(0.2, 0.8)):
    """The same opening on both walls: for a corner cell, which shows two."""
    return [('R', a[0], a[1], z[0], z[1], kind), ('L', a[0], a[1], z[0], z[1], kind)]


def wall_piece(style, features=None, both_faces=None, decay=None, corner=False):
    """A wall block. `decay` (weathering, damage, vines) goes on the wall the piece is for, or on both if it is a corner piece."""
    def make(orient):
        side = SIDE[orient]
        marks = [(f, d) for d in (decay or []) for f in (('R', 'L') if corner else (side,))]
        if both_faces:
            return [box(0, 1, 0, 1, 0, 1, style, both_faces, decay=marks)], 1
        return [box(0, 1, 0, 1, 0, 1, style, [(side, *f) for f in (features or [])], decay=marks)], 1
    return make


def ruined(mat):
    """A wall broken off along its top: a low block with ragged stumps, and bare posts standing up where it is timber."""
    def make(orient):
        solids = [box(0, 1, 0, 1, 0, 0.5, mat, decay=['worn']),
                  box(0, 0.45, 0, 0.6, 0.5, 0.88, mat), box(0.55, 1, 0.4, 1, 0.5, 0.72, mat), box(0.12, 0.4, 0.62, 1, 0.5, 0.64, mat)]
        if mat != 'stone':
            solids += [box(0.02, 0.14, 0.02, 0.14, 0.5, 1.0, 'wood'), box(0.86, 0.98, 0.86, 0.98, 0.5, 0.85, 'wood')]
        return solids, 1
    return make


def rubble(orient):
    spots = [(0.1, 0.45, 0.1, 0.4, 0.22), (0.5, 0.9, 0.15, 0.5, 0.3), (0.2, 0.6, 0.55, 0.9, 0.18), (0.65, 0.95, 0.6, 0.9, 0.12), (0.4, 0.55, 0.4, 0.55, 0.36)]
    return [box(x0, x1, y0, y1, 0, h, 'stone', decay=['worn']) for x0, x1, y0, y1, h in spots], 1


def battlement(orient):
    solids = [box(0, 1, 0, 1, 0, 0.5, 'stone')]
    for x0, y0 in ((0, 0), (0.68, 0), (0, 0.68), (0.68, 0.68)):
        solids.append(box(x0, x0 + 0.32, y0, y0 + 0.32, 0.5, 0.95, 'stone'))
    return solids, 1


# --- the roofs: wedges that rise one level over one cell -------------------------------------
def roof_solid(planes, style, decay=None):
    return Solid(planes + [((1, 0, 0), 1), ((-1, 0, 0), 0), ((0, 1, 0), 1), ((0, -1, 0), 0), ((0, 0, -1), 0)], style, end=ROOF_END[style], decay=decay)


SLOPES = {      # z <= something, for the planes that make each piece
    'slope-SE': [plane((0, 1, 1), (0, 1, 0))],                     # the front slope of a ridge along X: up toward the back
    'back-SE': [plane((0, -1, 1), (0, 0, 0))],                     # its back half (only its end shows)
    'slope-NE': [plane((1, 0, 1), (1, 0, 0))],                     # the front slope of a ridge along Y
    'back-NE': [plane((-1, 0, 1), (0, 0, 0))],
    'hip-NE': [plane((0, -1, 1), (0, 0, 0)), plane((1, 0, 1), (1, 0, 0))],      # a hip's side slope, up toward the apex
    'hip-SE': [plane((-1, 0, 1), (0, 0, 0)), plane((0, 1, 1), (0, 1, 0))],
    'corner': [plane((0, 1, 1), (0, 1, 0)), plane((1, 0, 1), (1, 0, 0))],      # a hip's front corner: both slopes
}


def roof_piece(kind, style, decay=None):
    def make(orient):
        key = 'corner' if kind == 'corner' else f'{kind}-{orient}'
        return [roof_solid(list(SLOPES[key]), style, decay)], 1
    return make


def chimney(orient):
    return [box(0.3, 0.7, 0.3, 0.7, 0, 0.88, 'stone'), box(0.22, 0.78, 0.22, 0.78, 0.88, 1.0, 'stone')], 1


def spire(style):
    def make(orient):
        return [pyramid(0.04, 0.96, 0.04, 0.96, 0, 1.85, style)], 2
    return make


def pinnacle(orient):
    return [box(0.3, 0.7, 0.3, 0.7, 0, 0.3, 'stone'), pyramid(0.26, 0.74, 0.26, 0.74, 0.3, 0.7, 'dark')], 1


DOOR = (0.2, 0.8)
# The kit, in groups: (group, piece id, label, builder). Each is drawn for NE and SE; `same` pieces are one picture for both.
KIT = []


def add(group, pid, label, make, same=False):
    KIT.append(dict(group=group, id=pid, label=label, make=make, same=same))


for mat, name in (('stone', 'Stone wall'), ('timber', 'Timber-framed wall')):
    add(name, f'{mat}-plain', 'plain block', wall_piece(mat), same=True)
    if mat == 'timber':
        add(name, f'{mat}-brace', 'braced block', wall_piece('brace'), same=True)
    add(name, f'{mat}-window', 'window', wall_piece(mat, [(0.3, 0.7, 0.2, 0.8, 'window')]))
    add(name, f'{mat}-corner-window', 'window on both walls (a corner)', wall_piece(mat, both_faces=both('window')), same=True)
    add(name, f'{mat}-door-low', 'door, lower half', wall_piece(mat, [(*DOOR, 0.0, 1.0, 'doorlow')]))
    add(name, f'{mat}-door-up', 'door, upper half (arched)', wall_piece(mat, [(*DOOR, 0.0, 0.62, 'doorup')]))
    if mat == 'stone':
        add(name, f'{mat}-slit', 'arrow slit', wall_piece(mat, [(0.4, 0.6, 0.15, 0.85, 'slit')]))
        add(name, f'{mat}-corner-slit', 'arrow slit on both walls', wall_piece(mat, both_faces=both('slit', (0.4, 0.6), (0.15, 0.85))), same=True)
        add(name, f'{mat}-open', 'belfry arch', wall_piece(mat, [(0.2, 0.8, 0.1, 0.9, 'open')]))
        add(name, f'{mat}-corner-open', 'belfry arch on both walls', wall_piece(mat, both_faces=both('open', (0.2, 0.8), (0.1, 0.9))), same=True)
        add(name, f'{mat}-gate', 'gate arch', wall_piece(mat, [(0.1, 0.9, 0.0, 0.95, 'arch')]))
        add(name, f'{mat}-battlement', 'battlement', battlement, same=True)

for style, name in (('tile', 'Terracotta roof'), ('slate', 'Slate roof'), ('teal', 'Teal roof')):
    add(name, f'roof-{style}-slope', 'front slope', roof_piece('slope', style))
    add(name, f'roof-{style}-back', 'back slope (its end shows)', roof_piece('back', style))
    add(name, f'roof-{style}-hip', 'hip slope', roof_piece('hip', style))
    add(name, f'roof-{style}-corner', 'hip corner', roof_piece('corner', style), same=True)

# Weathered, damaged and overgrown variants, to break up a run of plain wall and roof. Same size and fit as the plain ones.
for mat, name in (('stone', 'Stone wall - worn, damaged, overgrown'), ('timber', 'Timber-framed wall - worn, damaged, overgrown')):
    plain_style = 'brace' if False else mat
    if mat == 'stone':
        add(name, f'{mat}-worn', 'worn: cracked and stained', wall_piece(mat, decay=['worn']))
        add(name, f'{mat}-mossy', 'mossy', wall_piece(mat, decay=['mossy']))
    else:
        add(name, f'{mat}-peeled', 'plaster peeling off', wall_piece(mat, decay=['peeled']))
    add(name, f'{mat}-hole', 'damaged: a hole', wall_piece(mat, decay=['hole']))
    add(name, f'{mat}-vines', 'vines growing up', wall_piece(mat, decay=['vines-low']))
    add(name, f'{mat}-vines-hang', 'vines hanging down', wall_piece(mat, decay=['vines-hang']))
    add(name, f'{mat}-vines-heavy', 'covered in vines', wall_piece(mat, decay=['vines-heavy']))
    add(name, f'{mat}-window-vines', 'window with vines round it', wall_piece(mat, [(0.3, 0.7, 0.2, 0.8, 'window')], decay=['vines-frame']))
    add(name, f'{mat}-corner-vines', 'vines on both walls (a corner)', wall_piece(mat, decay=['vines-low'], corner=True), same=True)
    add(name, f'{mat}-ruined', 'ruined: broken off along the top', ruined(mat), same=True)

for style, name in (('tile', 'Terracotta roof - mossy, broken'), ('slate', 'Slate roof - mossy, broken'), ('teal', 'Teal roof - mossy, broken')):
    for kind, label, same in (('slope', 'front slope', False), ('hip', 'hip slope', False), ('corner', 'hip corner', True)):
        add(name, f'roof-{style}-{kind}-mossy', f'{label}, mossy', roof_piece(kind, style, ['roof-moss']), same=same)
        add(name, f'roof-{style}-{kind}-broken', f'{label}, tiles missing', roof_piece(kind, style, ['roof-broken']), same=same)

add('Extras', 'rubble', 'rubble', rubble, same=True)
add('Extras', 'chimney', 'chimney', chimney, same=True)
add('Extras', 'pinnacle', 'pinnacle', pinnacle, same=True)
add('Extras', 'spire-dark', 'spire, dark (2 levels)', spire('dark'), same=True)
add('Extras', 'spire-teal', 'spire, teal (2 levels)', spire('teal'), same=True)


def piece_rows(piece, orient, fine=True):
    solids, levels = piece['make'](orient)
    rows, _ = bd.render(solids, 1, 1, levels, fine=fine, scale=1, margin=0, extra_row=0)
    return rows, levels


def piece_id(piece, orient):
    return f"bld-{piece['id']}-{orient.lower()}"


# --- building with the kit --------------------------------------------------------------------
class Town:
    """Pieces placed on a grid: (x, y, level, kit id) where level 0 sits on the ground tile of the cell."""

    def __init__(self):
        self.pieces = []
        self.corners = set()          # cells where two walls show, which get the pieces that decorate both

    def put(self, x, y, k, pid):
        self.pieces.append((x, y, k, pid))

    def house(self, x0, y0, w, l, floors, mat='timber', roof='tile', ridge='x', door=1, brace=False):
        """A house of w x l cells (one of them 2 deep, along its ridge), `floors` storeys of two levels, a door on its left wall, windows above."""
        xm, ym = x0 + w - 1, y0 + l - 1
        h = floors * 2
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + l):
                on_r, on_l = x == xm, y == ym
                if not (on_r or on_l):
                    continue
                for lv in range(h):
                    upper = lv % 2 == 1
                    storey = lv // 2
                    i_l, i_r = x - x0, y - y0
                    if on_r and on_l:
                        name = 'corner-window' if upper else 'plain'
                        self.corners.add((x, y))
                        self.put(x, y, lv, f'{mat}-{name}-ne')
                    elif on_l:
                        if storey == 0 and not upper and i_l == door:
                            name = 'door-low'
                        elif storey == 0 and upper and i_l == door:
                            name = 'door-up'
                        elif upper and i_l % 2 == 0:
                            name = 'window'
                        else:
                            name = 'plain'
                        self.put(x, y, lv, f'{mat}-{name}-se')
                    else:
                        name = 'window' if upper and i_r % 2 == 1 else ('brace' if brace and mat == 'timber' and not upper else 'plain')
                        self.put(x, y, lv, f'{mat}-{name}-ne')
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + l):
                if ridge == 'x':
                    if y == y0 + l - 1:
                        self.put(x, y, h, f'roof-{roof}-slope-se')
                    elif y == y0 + l - 2:
                        self.put(x, y, h, f'roof-{roof}-back-se')
                elif x == x0 + w - 1:
                    self.put(x, y, h, f'roof-{roof}-slope-ne')
                elif x == x0 + w - 2:
                    self.put(x, y, h, f'roof-{roof}-back-ne')

    def tower(self, x0, y0, size, levels, mat='stone', roof=None, belfry=0, slits=True):
        """A square stone tower. A 1 x 1 one gets a spire; a 2 x 2 one a hip roof. `belfry` is how many top levels have arched openings."""
        xm, ym = x0 + size - 1, y0 + size - 1
        for x in range(x0, x0 + size):
            for y in range(y0, y0 + size):
                if not (x == xm or y == ym):
                    continue
                for lv in range(levels):
                    open_ = lv >= levels - belfry
                    slit = slits and lv % 3 == 1 and not open_
                    if x == xm and y == ym:
                        name = 'corner-open' if open_ else 'corner-slit' if slit else 'plain'
                        self.corners.add((x, y))
                        self.put(x, y, lv, f'stone-{name}-ne')
                    elif y == ym:
                        name = 'open' if open_ else 'slit' if slit and (x - x0) % 2 == 0 else 'plain'
                        if lv == 0 and size >= 2 and x - x0 == 0:
                            name = 'door-low'
                        if lv == 1 and size >= 2 and x - x0 == 0:
                            name = 'door-up'
                        self.put(x, y, lv, f'stone-{name}-se')
                    else:
                        name = 'open' if open_ else 'slit' if slit and (y - y0) % 2 == 0 else 'plain'
                        self.put(x, y, lv, f'stone-{name}-ne')
        if size == 1:
            self.put(x0, y0, levels, 'spire-dark-ne' if roof != 'teal' else 'spire-teal-ne')
        elif size == 2:
            self.put(x0 + 1, y0 + 1, levels, f'roof-{roof or "teal"}-corner-ne')
            self.put(x0 + 1, y0, levels, f'roof-{roof or "teal"}-hip-ne')
            self.put(x0, y0 + 1, levels, f'roof-{roof or "teal"}-hip-se')

    def weather(self, seed=1, amount=0.3, overgrown=0.5):
        """Age the town: swap some plain blocks for worn, mossy, holed or vine-covered ones, and some roof for mossy or broken. A cell is
        the same piece in every storey of a wall until the dice say otherwise, so the damage comes in runs, and vines climb from the ground."""
        import random
        rng = random.Random(seed)
        out = []
        for x, y, k, pid in self.pieces:
            mat = pid.split('-')[0]
            orient = pid[-2:]
            kind = pid[len(mat) + 1:-3]
            new = pid
            if mat in ('stone', 'timber') and kind == 'plain' and rng.random() < amount:
                corner = (x, y) in self.corners
                if rng.random() < overgrown:
                    if corner:
                        new = f'{mat}-corner-vines-{orient}'
                    else:
                        new = f'{mat}-' + (rng.choice(['vines', 'vines', 'vines-heavy']) if k < 2 else rng.choice(['vines-hang', 'vines-heavy', 'vines-hang'])) + f'-{orient}'
                else:
                    wear = ['worn', 'mossy', 'hole', 'worn'] if mat == 'stone' else ['peeled', 'hole', 'peeled']
                    new = f'{mat}-{rng.choice(wear)}-{orient}'
            elif pid.startswith('roof-') and any(pid.endswith(f'{kd}-{o}') for kd in ('slope', 'hip', 'corner') for o in ('ne', 'se')) and rng.random() < amount * 0.7:
                new = pid[:-3] + rng.choice(['-mossy', '-broken']) + pid[-3:]
            elif mat == 'window' or kind == 'window':
                if rng.random() < amount * overgrown:
                    new = f'{mat}-window-vines-{orient}'
            out.append((x, y, k, new))
        self.pieces = out

    def ruin(self, cells, mat='stone', rubble_at=()):
        """Break walls off along the top at the given (x, y, level) cells: whatever stood above them goes, the roof over those columns goes
        (the whole depth of the building there), and `rubble_at` cells (x, y) get a pile of rubble on the ground."""
        gone = set(cells)
        xs = {c[0] for c in gone}
        y_lo, y_hi = min(c[1] for c in gone) - 1, max(c[1] for c in gone)
        keep = []
        for p in self.pieces:
            x, y, k, pid = p
            above = any(x == c[0] and y == c[1] and k >= c[2] for c in gone)
            if above or (pid.startswith(('roof-', 'chimney')) and x in xs and y_lo <= y <= y_hi):
                continue
            keep.append(p)
        self.pieces = keep
        for x, y, k in gone:
            self.put(x, y, k, f'{mat}-ruined-ne')
        for x, y in rubble_at:
            self.put(x, y, 0, 'rubble-ne')

    def frame(self, gx, gy):
        """(width, height, ox, oy) of the picture of a gx x gy ground: the ground tile of cell (0, 0) has its top left at (ox - 16, oy)."""
        top_level = max((k + (2 if 'spire' in pid else 1) for _, _, k, pid in self.pieces), default=1)
        return 16 * (gx + gy) + 32, 8 * (gx + gy) + 16 * top_level + 64, 16 * gy + 16, 16 * top_level + 16

    def render(self, ground, gx, gy, rgb):
        """The whole scene: ground tiles (frames of role rows, or none), then every piece back to front."""
        from PIL import Image
        by_id = {}
        for piece in KIT:
            for orient in ORIENTS:
                by_id[piece_id(piece, orient)[len('bld-'):]] = (piece, orient)
        W, H, ox, oy = self.frame(gx, gy)
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

        def put_rows(rows, left, top):
            for y, line in enumerate(rows):
                for x, ch in enumerate(line):
                    if ch != '.' and 0 <= left + x < W and 0 <= top + y < H:
                        img.putpixel((left + x, top + y), rgb[ch] + (255,))

        for (x, y), rows in sorted(ground.items(), key=lambda kv: kv[0][0] + kv[0][1]):
            put_rows(rows, ox + 16 * (x - y) - 16, oy + 8 * (x + y))
        cache = {}
        for x, y, k, pid in sorted(self.pieces, key=lambda p: (p[0] + p[1], p[2])):
            piece, orient = by_id[pid]
            if pid not in cache:
                cache[pid] = piece_rows(piece, orient)
            rows, levels = cache[pid]
            put_rows(rows, ox + 16 * (x - y) - 16, oy + 8 * (x + y) - 16 * (k + levels))
        return img


# --- the assets: all grouped in the "Buildings" category, ids bld-*, and the folder sprites/assets/buildings/ ----------------------
CATEGORY = 'Buildings'
FOLDER = 'buildings'
CELL = 32
LEVEL = bd.LEVEL
SHEET_COLS = 8                                   # four pieces a row, each as its NE picture then its SE picture
GROUP_SHEETS = {                                 # a kit group -> the sheet its pieces are on
    'Stone wall': ('bld-stone-wall', 'Stone walls'),
    'Timber-framed wall': ('bld-timber-wall', 'Timber-framed walls'),
    'Terracotta roof': ('bld-roof-terracotta', 'Terracotta roof'),
    'Slate roof': ('bld-roof-slate', 'Slate roof'),
    'Teal roof': ('bld-roof-teal', 'Teal roof'),
    'Stone wall - worn, damaged, overgrown': ('bld-stone-wall-aged', 'Stone walls - worn, damaged, overgrown'),
    'Timber-framed wall - worn, damaged, overgrown': ('bld-timber-wall-aged', 'Timber-framed walls - worn, damaged, overgrown'),
    'Terracotta roof - mossy, broken': ('bld-roof-terracotta-aged', 'Terracotta roof - mossy, broken'),
    'Slate roof - mossy, broken': ('bld-roof-slate-aged', 'Slate roof - mossy, broken'),
    'Teal roof - mossy, broken': ('bld-roof-teal-aged', 'Teal roof - mossy, broken'),
    'Extras': ('bld-extras', 'Extras: chimney, pinnacle, rubble'),
}
SPIRES = ('bld-spires', 'Spires (two levels tall)')


def sheet_of(piece, levels):
    return SPIRES if levels == 2 else GROUP_SHEETS[piece['group']]


def sheets():
    """{sheet id: dict(label, h, levels, entries=[(piece, orient, rows)])} in kit order, with every piece drawn for NE then SE."""
    out = {}
    for piece in KIT:
        for orient in ORIENTS:
            rows, levels = piece_rows(piece, orient)
            sid, label = sheet_of(piece, levels)
            sh = out.setdefault(sid, dict(label=label, levels=levels, entries=[]))
            assert sh['levels'] == levels, f'{sid} mixes piece heights'
            sh['entries'].append((piece, orient, rows))
    return out


def build_assets():
    """The kit as assets: a sheet per group, each piece twice (NE then SE), 32 wide and 16 * levels + 16 tall, anchored at the middle of its base."""
    assets = []
    for sid, sh in sheets().items():
        n = len(sh['entries'])
        h = LEVEL * sh['levels'] + 16
        assets.append({
            'id': sid, 'label': f"Buildings - {sh['label']}", 'category': CATEGORY, 'folder': FOLDER,
            'kind': 'variants', 'place': 'ground',
            'names': [f"{p['label']} ({o})" for p, o, _ in sh['entries']],
            'w': CELL, 'h': h, 'cols': SHEET_COLS, 'rows': -(-n // SHEET_COLS), 'fps': 0,
            'anchor': {'x': CELL // 2, 'y': h - 8},
            'buildings': {'role': 'kit', 'pieces': [f"{p['id']}-{o.lower()}" for p, o, _ in sh['entries']]},
            'frames': [rows for _, _, rows in sh['entries']],
        })
    return assets


def write_package(folder, rgb=None):
    """Beside the sheets: buildings.json (every piece, where it is, and the rules in numbers) and an example street with its layout."""
    import json
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rgb = rgb or {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    pieces = {}
    sheet_info = {}
    for sid, sh in sheets().items():
        h = LEVEL * sh['levels'] + 16
        sheet_info[sid] = {'file': f'{sid}.png', 'label': sh['label'], 'cell': [CELL, h], 'cols': SHEET_COLS, 'levels': sh['levels']}
        for i, (p, o, _) in enumerate(sh['entries']):
            pieces[f"{p['id']}-{o.lower()}"] = {'sheet': sid, 'frame': i, 'col': i % SHEET_COLS, 'row': i // SHEET_COLS, 'levels': sh['levels'],
                                                'orient': o, 'label': p['label'], 'group': p['group'], 'sameInBoth': p['same']}
    town = build_city()
    gx, gy = 12, 10
    W, H, ox, oy = town.frame(gx, gy)
    town.render({}, gx, gy, rgb).save(folder / 'example-street.png')
    (folder / 'example-street.json').write_text(json.dumps({
        'about': 'The street in example-street.png: only the buildings, on a transparent background. Every piece is [x, y, level, id]: the cell, the level '
                 '(0 stands on the ground tile of the cell) and the piece id from buildings.json. cellOrigin is where the ground tile of cell (0, 0) has its top '
                 'left in the picture; draw each piece as the README says and you get the picture back pixel for pixel.',
        'ground': [gx, gy], 'size': [W, H], 'cellOrigin': [ox - 16, oy],
        'pieces': [list(p) for p in sorted(town.pieces, key=lambda p: (p[0] + p[1], p[2]))],
    }, indent=0))
    (folder / 'buildings.json').write_text(json.dumps({
        'about': 'How an app uses the building tiles in this folder. See README.md beside this file for the whole story.',
        'cell': CELL, 'level': LEVEL,
        'placement': 'a piece at cell (x, y), level k, whose ground tile has its top left at (gx, gy): draw its picture with its top left at '
                     '(gx, gy - 16 * (k + levels)), levels being 1 (a 32 x 32 picture) or 2 (a 32 x 48 one)',
        'groundTile': 'the cell\'s ground tile top left is (16 * (x - y), 8 * (x + y)) plus the map\'s own offset, as the terrain page draws it',
        'drawOrder': 'sort by x + y, then by level, and draw in that order, after the ground tiles',
        'storey': 2, 'sheetColumns': SHEET_COLS, 'frameOrder': 'in a sheet, each piece is its NE picture then its SE picture; the frame is col + row * columns',
        'orientation': {'NE': 'the feature or slope is on the wall or run that goes NE-SW (the right-hand wall as seen)',
                        'SE': 'the feature or slope is on the wall or run that goes NW-SE (the left-hand wall as seen)',
                        'NW and SW': 'flip the NE and SE pictures left to right, as for the characters'},
        'roof': {'rise': 'one level over one cell', 'endsMatch': {'tile': 'timber plaster', 'slate': 'stone', 'teal': 'stone'}},
        'sheets': sheet_info,
        'pieces': pieces,
    }, indent=0))


# --- previews -------------------------------------------------------------------------------
def ground_frames():
    import json
    s = (ROOT / 'assets' / 'data.js').read_text()
    data = json.loads(s[s.index('{'):s.rindex('}') + 1])
    by = {a['id']: a['frames'][0] for a in data['assets']}
    return by


def preview_kit(path, scale=3):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    groups = {}
    for p in KIT:
        groups.setdefault(p['group'], []).append(p)
    cw, ch = 32 * scale + 8, 48 * scale + 22
    per = 5                                   # pieces per row, each shown NE then SE
    rows_needed = sum(-(-len(v) // per) for v in groups.values())
    W = per * (2 * cw + 14) + 20
    H = rows_needed * ch + len(groups) * 26 + 20
    sheet = Image.new('RGBA', (W, H), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    y = 10
    for name, pieces in groups.items():
        d.text((12, y), name, fill=(255, 226, 150, 255))
        y += 18
        for i, p in enumerate(pieces):
            col, row = i % per, i // per
            for o, orient in enumerate(ORIENTS):
                rows, levels = piece_rows(p, orient)
                img = Image.new('RGBA', (32, 16 * levels + 16), (0, 0, 0, 0))
                for yy, line in enumerate(rows):
                    for xx, c in enumerate(line):
                        if c != '.':
                            img.putpixel((xx, yy), rgb[c] + (255,))
                img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
                x0 = 10 + col * (2 * cw + 14) + o * cw
                sheet.alpha_composite(img, (x0, y + row * ch + 14 + (48 * scale - img.height)))
                if o == 0:
                    d.text((x0, y + row * ch + 1), p['label'] + ('  (one picture)' if p['same'] else ''), fill=(235, 238, 245, 255))
                d.text((x0 + 2, y + row * ch + 13), orient, fill=(150, 160, 180, 255))
        y += -(-len(pieces) // per) * ch + 8
    sheet.save(path)


def build_city():
    t = Town()
    # the north side of the street: a row of timber houses, a chapel with its bell tower
    t.house(1, 1, 3, 2, 2, 'timber', 'tile', 'x', door=1, brace=True)
    t.house(4, 1, 2, 2, 3, 'timber', 'tile', 'x', door=0)
    t.house(6, 1, 4, 2, 1, 'stone', 'tile', 'x', door=2)
    t.tower(10, 1, 1, 7, belfry=2)
    t.put(2, 1, 4, 'chimney-ne')           # a chimney stands on the back slope, at the level the roof starts
    t.put(7, 1, 2, 'chimney-ne')
    # the south side: a slate warehouse, a taller house with its ridge the other way, and a stone tower with a teal roof
    t.house(1, 6, 3, 2, 1, 'stone', 'slate', 'x', door=1)
    t.house(5, 6, 2, 3, 2, 'timber', 'tile', 'y', door=1)
    t.tower(8, 6, 2, 6)
    t.put(5, 7, 4, 'chimney-ne')
    t.weather(seed=4, amount=0.38)
    t.ruin([(8, 2, 1), (9, 2, 1), (9, 1, 1)], rubble_at=[(8, 3), (9, 3)])        # the chapel's far end has fallen in
    for lv in (0, 1):
        t.put(7, 1, lv, 'stone-plain-ne')            # the roof that is left now ends here, so this wall, once hidden inside, closes it
    return t


def preview_city(path, scale=3):
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    frames = ground_frames()
    gx, gy = 12, 10
    ground = {}
    for x in range(gx):
        for y in range(gy):
            ground[(x, y)] = frames['ground-8-5'] if y in (4, 5) else frames['ground-0-0']
    img = build_city().render(ground, gx, gy, rgb)
    img.resize((img.width * scale, img.height * scale), __import__('PIL.Image', fromlist=['Image']).NEAREST).save(path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--kit', type=Path)
    parser.add_argument('--city', type=Path)
    parser.add_argument('--package', type=Path, help='write buildings.json and the example street into this folder')
    args = parser.parse_args()
    if args.kit:
        preview_kit(args.kit)
        print('wrote', args.kit, f'({len(KIT)} pieces, {2 * len(KIT)} tiles)')
    if args.city:
        preview_city(args.city)
        print('wrote', args.city)
    if args.package:
        write_package(args.package)
        print('wrote the package ->', args.package)


if __name__ == '__main__':
    main()
