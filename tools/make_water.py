#!/usr/bin/env python3
"""Animated water: the ground sheet's water tiles, moving. The normal set and the corrupted set, the open pieces and the edge pieces with foam.

Every tile keeps its sheet cell and its look: the cube, its two sides and the outline of its foam stay exactly where they are. Only two things move:
  * the water on the top face. The ring-and-glint texture drifts one tile's width (16 across, 8 down) over the loop, and because a map is the same
    tile over and over, the drift is taken on the *tiling* (a ring that leaves the diamond comes in at the opposite edge), so neighbouring tiles
    still join and the loop closes. A few glints twinkle on top (the same places on every tile, each with its own beat).
  * the foam on an edge piece. A bright crest runs along the shore, measured along the edge so it carries on from one tile to the next.
Frame 0 of an open tile is the sheet's tile, pixel for pixel. Palette roles only, nothing outside the original's silhouette.

    python3 tools/make_water.py --preview previews/water.png      the 18 tiles of each set, every frame; and previews/water.gif, a lake in each set at both heights
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402

FRAMES = 10
FPS = 4
DRIFT_X = [round(16 * f / FRAMES) for f in range(FRAMES)]       # (16, 8) over the loop, in whole pixels, so the loop closes
DRIFT_Y = [round(8 * f / FRAMES) for f in range(FRAMES)]
CELL = 32
FOLDER = 'water'
WAVE_STEP = 1            # frames each tile starts after the one behind it (x + y), the wave the game is told to use
FLUSH = {(0, 2): [], (3, 2): ['NE'], (2, 3): ['NW'], (4, 3): ['SE'], (3, 4): ['SW'],
         (2, 2): ['NW', 'NE'], (4, 2): ['NE', 'SE'], (2, 4): ['NW', 'SW'], (4, 4): ['SW', 'SE']}
SUNKEN = {(1, 2): [], (6, 2): ['NE'], (5, 3): ['NW'], (7, 3): ['SE'], (6, 4): ['SW'],
          (5, 2): ['NW', 'NE'], (7, 2): ['NE', 'SE'], (5, 4): ['NW', 'SW'], (7, 4): ['SW', 'SE']}
INTERIOR = {'flush': (0, 2), 'sunken': (1, 2)}
TOP_OFFSET = {'flush': 0, 'sunken': 8}               # a sunken tile's top face sits eight rows lower in its cell
SIDES = {'NW': (-1, 0), 'NE': (0, -1), 'SW': (0, 1), 'SE': (1, 0)}

THEMES = {
    # water: the roles the surface is drawn in; spark: the twinkle; foam: (dim, bright)
    'original': dict(prefix='ground', water='no', body='n', spark='o', foam=('r', 't'), label='Water', category='Animated Water'),
    'corrupted': dict(prefix='ground-corrupted', water='qs', body='q', spark='v', foam=('r', 'v'), label='Corrupted water', category='Animated Corrupted Water'),
}
SPARKS = [(11, 5, 0), (22, 6, 3), (7, 9, 5), (25, 10, 1), (16, 12, 6), (13, 3, 2)]    # local x, y on the top face, and the beat (0-7, doubled to a frame) each twinkles on


def in_top(x, y, fat=0.12):
    """Is (x, y), in the top face's own coordinates (the diamond is 32 x 16, rows 0-15), on the face? A little fat, as the art is."""
    return abs(x + 0.5 - 16) / 16 + abs(y + 0.5 - 8) / 8 <= 1.0 + fat + 1e-9


def reduce_to_face(x, y):
    """The same place in the tiling, on the face: neighbouring faces are a step of (16, 8) or (16, -8) away."""
    for n in range(0, 9):
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                if abs(i) + abs(j) != n:
                    continue
                X, Y = x - 16 * (i + j), y - 8 * (i - j)
                if in_top(X, Y):
                    return X, Y
    raise ValueError((x, y))


def animate_tile(rows, interior, level, theme, frame):
    """One frame of one water tile: `rows` is the sheet's 32 rows of roles, `interior` the open tile at the same height."""
    t = THEMES[theme]
    off = TOP_OFFSET[level]
    water = t['water']
    shift_x, shift_y = DRIFT_X[frame], DRIFT_Y[frame]
    out = [list(r) for r in rows]
    foam = set(t['foam'])
    for y in range(off, off + 16):
        for x in range(CELL):
            ly = y - off
            if not in_top(x, ly):
                continue
            ch = rows[y][x]
            if ch in water and interior[y][x] != '.':
                if shift_x or shift_y:
                    X, Y = reduce_to_face(x - shift_x, ly - shift_y)
                    ch = interior[Y + off][X]
                if ch not in water:        # a bit of side showing at the rim: leave the sheet's pixel
                    ch = rows[y][x]
                out[y][x] = ch
                for sx, sy, beat in SPARKS:
                    if (x, ly) == (sx, sy) and (frame - beat) % FRAMES in (0, 1):
                        out[y][x] = t['spark']
            elif ch in foam:
                dx, dy = x + 0.5 - 16, ly + 0.5 - 8
                along = x + 2 * y if dx * dy < 0 else x - 2 * y            # measured along the edge the pixel is on
                out[y][x] = t['foam'][1] if (along - DRIFT_X[frame]) % 16 < 6 else t['foam'][0]
    return [''.join(r) for r in out]


def sheet_rows(theme):
    """{(col, row): the 32 rows of roles} for every cell of a theme's sheet that has a tile."""
    import make_ground
    if theme == 'original':
        assets = make_ground.build_ground_assets()
    else:
        import make_corrupted_ground
        make_corrupted_ground.ensure_sheet()
        assets = make_ground.build_ground_assets(make_ground.CORRUPTED)
    return {tuple(map(int, a['id'].split('-')[-2:])): a['frames'][0] for a in assets if a['w'] == CELL and a['h'] == CELL}


def tile_frames(theme, cell, level, cells=None):
    cells = cells or sheet_rows(theme)
    return [animate_tile(cells[cell], cells[INTERIOR[level]], level, theme, f) for f in range(FRAMES)]


def build_assets():
    """Ids `water-COL-ROW` and `water-corrupted-COL-ROW`, the cell of the sheet tile each one moves: FRAMES frames at FPS, in the order of the loop."""
    out = []
    for theme, t in THEMES.items():
        cells = sheet_rows(theme)
        make = family(t['category'], CELL, CELL, (CELL // 2, CELL), place='none', folder=FOLDER)
        for level, table in (('flush', FLUSH), ('sunken', SUNKEN)):
            for cell, sides in table.items():
                if cell not in cells:
                    continue
                label = f"{t['label']}, {level}" + (f", foam {'+'.join(sides)}" if sides else ', open')
                out.append(make(('water-corrupted-' if theme == 'corrupted' else 'water-') + f'{cell[0]}-{cell[1]}', label, 'animation',
                                tile_frames(theme, cell, level, cells), fps=FPS, names=[f'Frame {i + 1}' for i in range(FRAMES)],
                                water={'cell': list(cell), 'level': level, 'foam': sides, 'theme': theme}))
    return out


def write_package(folder):
    """Beside the sheets: water.json, the loop and the wave in numbers and every tile with its foam sides (README.md says how to lay them)."""
    tiles = {}
    for a in build_assets():
        tiles[a['id']] = dict(a['water'], file=f"{a['id']}.png", label=a['label'])
    write_json(folder, 'water.json', 'The animated water in this folder. See README.md beside this file for the whole story.',
               {'frames': FRAMES, 'fps': FPS, 'cell': [CELL, CELL], 'wave': {'step': WAVE_STEP, 'along': 'x + y', 'start': f'(frame + (x + y) * {WAVE_STEP}) % {FRAMES}'}, 'tiles': tiles})


# ---------- preview ----------

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


def lake(n=9):
    """A lake with a ragged shore, the same for every scene: True where there is water."""
    def h(x, y):
        return ((x * 73856093) ^ (y * 19349663) ^ 0x5bd1) % 1000 / 1000
    return [[1 <= x < n - 1 and 1 <= y < n - 1 and ((x - 4) ** 2 + (y - 4) ** 2 < 6.2 + 5 * h(x, y) or (x, y) in ((6, 3), (6, 4), (5, 6), (2, 4))) and (x, y) not in ((1, 1), (7, 7))
             for x in range(n)] for y in range(n)]


def pick_tile(table, want):
    best, score = [], 9
    for cell, sides in table.items():
        miss = sum((s in want) != (s in sides) for s in SIDES)
        if miss < score:
            best, score = [cell], miss
        elif miss == score:
            best.append(cell)
    return best[0]


def scene(theme, level, frame, rgb, cache, n=9, head=40, desync=None):
    """One lake as terrain.js lays it out, at frame `frame`."""
    from PIL import Image
    import make_ground
    water = lake(n)
    cells = cache.setdefault(theme, sheet_rows(theme))
    land_cell = (0, 0) if theme == 'original' else (4, 11)
    land = _image(cells[land_cell], rgb)
    table = FLUSH if level == 'flush' else SUNKEN
    art = Image.new('RGBA', (n * 32, n * 16 + 32 + head), (34, 36, 54, 255))
    for d in range(2 * n - 1):
        for x in range(n):
            y = d - x
            if not 0 <= y < n:
                continue
            sx, sy = (x - y) * 16 + (n - 1) * 16, (x + y) * 8 + head
            if water[y][x]:
                want = [s for s, (dx, dy) in SIDES.items() if not (0 <= x + dx < n and 0 <= y + dy < n and water[y + dy][x + dx]) and 0 <= x + dx < n and 0 <= y + dy < n]
                cell = pick_tile(table, want)
                key = (theme, cell, level)
                if key not in cache:
                    cache[key] = [_image(f, rgb) for f in tile_frames(theme, cell, level, cells)]
                start = desync(x, y) if desync else 0                      # the frame each tile starts on
                art.alpha_composite(cache[key][(frame + start) % FRAMES], (sx, sy))
            else:
                art.alpha_composite(land, (sx, sy))
    return art


def preview(path, scale=3, desync=None, tag='random'):
    from PIL import Image, ImageDraw
    rgb = _rgb()
    path = Path(path)
    # 1. every tile, every frame: rows of FRAMES for each of the 18 tiles, per theme
    sheets = []
    for theme in THEMES:
        cells = sheet_rows(theme)
        tiles = [(c, 'flush') for c in FLUSH] + [(c, 'sunken') for c in SUNKEN]
        im = Image.new('RGBA', (FRAMES * 34 + 2, len(tiles) * 34 + 2), (34, 36, 54, 255))
        for r, (cell, level) in enumerate(tiles):
            for f, rows in enumerate(tile_frames(theme, cell, level, cells)):
                im.alpha_composite(_image(rows, rgb), (f * 34 + 2, r * 34 + 2))
        sheets.append(im)
    both = Image.new('RGBA', (sheets[0].width * 2 + 8, sheets[0].height), (34, 36, 54, 255))
    both.alpha_composite(sheets[0], (0, 0))
    both.alpha_composite(sheets[1], (sheets[0].width + 8, 0))
    both = both.resize((both.width * 2, both.height * 2), Image.NEAREST)
    both.save(path)
    # 2. the scenes: a lake in each set at each height, animated
    cache = {}
    frames = []
    for f in range(FRAMES):
        panels = [scene(t, lv, f, rgb, cache, desync=desync) for lv in ('flush', 'sunken') for t in THEMES]
        w, h = panels[0].size
        canvas = Image.new('RGBA', (w * 2, h * 2), (34, 36, 54, 255))
        for i, p in enumerate(panels):
            canvas.alpha_composite(p, ((i % 2) * w, (i // 2) * h))
        frames.append(canvas.resize((canvas.width * scale, canvas.height * scale), Image.NEAREST))
    if desync:
        path = path.with_name(path.stem + f'-{tag}.png')
    gif = path.with_suffix('.gif')
    frames[0].convert('RGB').save(gif, save_all=True, append_images=[f.convert('RGB') for f in frames[1:]], duration=int(1000 / FPS), loop=0)
    frames[0].save(path.with_name(path.stem + '-scene-0.png'))
    frames[3].save(path.with_name(path.stem + '-scene-3.png'))
    return gif


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--desync', action='store_true', help='in the lake scenes, start every tile on its own frame (writes NAME-random.gif)')
    parser.add_argument('--wave', type=float, help='in the lake scenes, start each tile this many frames later than the one behind it, along the map (writes NAME-wave.gif)')
    parser.add_argument('--preview', type=Path, help='a PNG of every tile and frame, plus a GIF (and two stills) of a lake in each set at each height')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        if args.wave is not None:
            gif = preview(args.preview, desync=lambda x, y: round((x + y) * args.wave) % FRAMES, tag='wave')
        else:
            gif = preview(args.preview, desync=(lambda x, y: ((x * 73856093) ^ (y * 19349663) ^ 0x2f1) % FRAMES) if args.desync else None)
        print('every tile and frame ->', args.preview, '\nthe lakes, animated ->', gif)


if __name__ == '__main__':
    main()
