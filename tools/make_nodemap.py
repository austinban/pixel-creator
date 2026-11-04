#!/usr/bin/env python3
"""Node-map tiles: a top-down branching island with water between, for a floor-choosing map like Slay the Spire's.

The map is a grid of cells, each LAND or WATER. Tiles are drawn on the CORNERS between four cells (a "dual grid"), so a tile's picture depends on
which of its four corner cells are land: 2 ** 4 = 16 tiles cover every shore, every path one cell wide, every blob, with no special cases.

    corner bits   TL = 1   TR = 2
                  BL = 4   BR = 8        tile 0 is open water (empty), tile 15 is all land

A tile is drawn from a smooth field: the four corners blended (bilinear), and land is where the field is over a half. That gives the round
corners and straight edges for free, and because the field is the same along the edge two tiles share, they always join. A narrow band of
the land's edge is a darker green bank, and a band of the water's edge is foam. Water itself is a separate layer under everything (an
animated tile, 4 frames), so a shore tile is transparent wherever it is open water.

    TILE = 16        the one number to change for bigger or smaller tiles (the textures repeat every TILE pixels)

    python3 tools/make_nodemap.py --preview previews/nodemap.png      the 16 tiles and a branching map made from them
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

TILE = 16
BANK = 0.085          # how much of the field, over a half, is the land's darker edge
FOAM = 0.16           # and under a half, the water's foam
TL, TR, BL, BR = 1, 2, 4, 8

# A skin is only colours and textures; the 16 tile shapes are the same for all of them.
BIOMES = {
    # green islands in a blue sea with white foam, the same greens and blues as the ground tiles
    'grass': dict(base='A', speck='z', tuft='B', bank='B', sea='n', glint='o', wave='m', foam_in='t', foam_out='r'),
    # an old chart: ochre land inked round its coast, on pale parchment sea
    'parchment': dict(base='b', speck='d', tuft='a', bank='g', sea='C', glint='t', wave='c', foam_in='t', foam_out='C'),
}


def hashed(x, y, salt=0):
    n = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF


def field(bits, x, y):
    """The land field at a pixel of a tile: its four corners blended, 0 to 1."""
    u, v = (x + 0.5) / TILE, (y + 0.5) / TILE
    return ((bits & TL > 0) * (1 - u) * (1 - v) + (bits & TR > 0) * u * (1 - v)
            + (bits & BL > 0) * (1 - u) * v + (bits & BR > 0) * u * v)


def land_pixel(x, y, biome):
    """The ground texture: repeats every TILE pixels, so any two tiles agree where they meet."""
    b = BIOMES[biome]
    h = hashed(x % TILE, y % TILE)
    if h % 29 == 0:
        return b['speck']
    if h % 13 == 0 and hashed((x + 1) % TILE, y % TILE) % 3:
        return b['tuft']
    return b['base']


def shore_tile(bits, biome='grass'):
    """One tile as TILE rows of roles; '.' where it is open water (the water layer shows through)."""
    rows = []
    b = BIOMES[biome]
    for y in range(TILE):
        row = ''
        for x in range(TILE):
            f = field(bits, x, y)
            if f > 0.5 + BANK:
                row += land_pixel(x, y, biome)
            elif f > 0.5:
                row += b['bank']
            elif f > 0.5 - FOAM:
                # foam: bright against the land, mint further out, and ragged at the outer edge
                depth = (0.5 - f) / FOAM
                if depth < 0.45:
                    row += b['foam_in']
                elif depth < 0.8 or hashed(x % TILE, y % TILE, 3) % 3:
                    row += b['foam_out']
                else:
                    row += '.'
            else:
                row += '.'
        rows.append(row)
    return rows


def water_tile(frame, biome='grass'):
    """Open water, 4 frames. The ripples slide along and wrap after 4, and repeat every TILE pixels, so water tiles join."""
    rows = []
    for y in range(TILE):
        row = ''
        for x in range(TILE):
            b = BIOMES[biome]
            ch = b['sea']
            if y % 4 == 1 and (x + 2 * frame + 2 * (y // 4)) % 8 in (0, 1):
                ch = b['glint']
            elif y % 4 == 3 and (x * 3 + 2 * frame + 5 * (y // 4)) % 16 in (0, 1, 2):
                ch = b['wave']
            row += ch
        rows.append(row)
    return rows


# --- a branching map -------------------------------------------------------------------------------
def make_layout(lanes=5, floors=8, paths=4, seed=7):
    """Slay-the-Spire style: paths climb from the bottom floor to the top one, one lane left, straight or right a floor, and never cross.
    Returns (nodes, edges) with a node as (floor, lane) and an edge as a pair of nodes on neighbouring floors."""
    rng = random.Random(seed)
    nodes, edges = set(), set()
    for lane in rng.sample(range(lanes), min(paths, lanes)):
        at = lane
        for floor in range(floors - 1):
            options = [l for l in (at - 1, at, at + 1) if 0 <= l < lanes]
            rng.shuffle(options)
            # a step sideways is skipped if the path beside it already steps the other way across it: that would cross
            options = [l for l in options if l == at or ((floor, l), (floor + 1, at)) not in edges]
            nxt = options[0] if options else at
            edges.add(((floor, at), (floor + 1, nxt)))
            nodes.update({(floor, at), (floor + 1, nxt)})
            at = nxt
    # the top floor is one place, the boss, where every path ends
    top = floors - 1
    boss = (top, lanes // 2)
    for (a, b) in list(edges):
        if b[0] == top:
            edges.discard((a, b))
            edges.add((a, boss))
    return {n for n in nodes if n[0] < top} | {boss}, edges


def land_cells(nodes, edges, lanes, floors, dx=9, dy=8, margin=8, seed=7, bridges=True, node_r=(2.6, 2.9, 3.2), path_r=0.78):
    rng = random.Random(seed + 1)
    width = (lanes - 1) * dx + 2 * margin
    height = (floors - 1) * dy + 2 * margin
    land = [[False] * width for _ in range(height)]
    centre = {}
    for (floor, lane) in nodes:
        jx, jy = rng.randint(-1, 1), rng.randint(-1, 1)
        centre[(floor, lane)] = (margin + lane * dx + jx, margin + (floors - 1 - floor) * dy + jy)

    def stamp(cx, cy, r):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if 0 <= x < width and 0 <= y < height and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    land[y][x] = True

    if bridges:
        for a, b in edges:
            (x0, y0), (x1, y1) = centre[a], centre[b]
            steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
            for i in range(steps + 1):
                stamp(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps, path_r)
    for n, (cx, cy) in centre.items():
        boss = n[0] == floors - 1
        stamp(cx, cy, 5.0 if boss else rng.choice(node_r))
    return land, centre


PEGS = {'green': ('z', 'A', 'B', 's'), 'blue': ('r', 'n', 'm', 'k'), 'red': ('c', 'j', 'i', 'h')}


PIN_W, PIN_H = 16, 24
PIN_TIP = (8, 20)           # the pin's point, which stands on the node's middle: the anchor


def pin_rows(ramp):
    """A map pin as PIN_H rows of PIN_W roles: a round head on a point, a bright spot on it, its shadow to one side, and an outline."""
    cx, cy = PIN_TIP
    head_r, head_y = 5.2, cy - 9.0
    mask = {}
    for y in range(PIN_H):
        for x in range(PIN_W):
            px, py = x + 0.5 - cx, y + 0.5
            t = (py - head_y) / (cy - head_y)
            in_head = math.hypot(px, py - head_y) <= head_r
            in_tail = 0.1 < t <= 1.0 and abs(px) <= head_r * 0.62 * (1 - t) + 0.3     # narrows from the head's width to nothing at the tip
            if in_head or in_tail:
                lit = (px * -0.55 + (py - head_y) * -0.83) / head_r
                mask[(x, y)] = PEGS[ramp][0 if lit > 0.5 else 1 if lit > -0.05 else 2 if lit > -0.6 else 3]
    mask[(cx - 2, int(head_y) - 2)] = 't'
    mask[(cx - 1, int(head_y) - 3)] = 't'
    shadow = {(x, y): 'g' for y in range(cy - 1, cy + 2) for x in range(cx - 3, cx + 7)
              if ((x + 0.5 - cx - 2) / 4.5) ** 2 + ((y + 0.5 - cy) / 1.6) ** 2 <= 1 and (x, y) not in mask}
    solid = set(mask)
    grid = [['.'] * PIN_W for _ in range(PIN_H)]
    for (x, y), ch in {**shadow, **mask}.items():
        grid[y][x] = ch
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in solid and 0 <= n[0] < PIN_W and 0 <= n[1] < PIN_H and grid[n[1]][n[0]] == '.':
                grid[n[1]][n[0]] = 'O'
    return [''.join(r) for r in grid]


def draw_peg(img, rgb, cx, cy, ramp):
    """Stand a pin on a node: its point at (cx, cy) in the picture."""
    for y, line in enumerate(pin_rows(ramp)):
        for x, ch in enumerate(line):
            px, py = cx - PIN_TIP[0] + x, cy - PIN_TIP[1] + y
            if ch != '.' and 0 <= px < img.width and 0 <= py < img.height:
                img.putpixel((px, py), rgb[ch] + (255,))


def draw_routes(img, rgb, edges, centre, dot='g', every=3):
    """Dotted routes from node to node, on the land and across the sea."""
    for a, b in edges:
        (x0, y0), (x1, y1) = centre[a], centre[b]
        x0, y0, x1, y1 = (x0 + 0.5) * TILE, (y0 + 0.5) * TILE, (x1 + 0.5) * TILE, (y1 + 0.5) * TILE
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for i in range(n + 1):
            if i % every in (0, 1):
                x, y = int(x0 + (x1 - x0) * i / n), int(y0 + (y1 - y0) * i / n)
                if 0 <= x < img.width and 0 <= y < img.height:
                    img.putpixel((x, y), rgb[dot] + (255,))


def render_map(land, biome='grass', frame=0, rgb=None):
    from PIL import Image
    height, width = len(land), len(land[0])
    img = Image.new('RGBA', (width * TILE, height * TILE), (0, 0, 0, 255))
    water = water_tile(frame, biome)

    def put(rows, ox, oy):
        for y, line in enumerate(rows):
            for x, ch in enumerate(line):
                if ch != '.' and 0 <= ox + x < img.width and 0 <= oy + y < img.height:
                    img.putpixel((ox + x, oy + y), rgb[ch] + (255,))

    for j in range(height + 1):
        for i in range(width + 1):
            put(water, i * TILE - TILE // 2, j * TILE - TILE // 2)
    cell = lambda x, y: 0 <= x < width and 0 <= y < height and land[y][x]
    for j in range(height + 1):
        for i in range(width + 1):
            bits = (TL * cell(i - 1, j - 1) + TR * cell(i, j - 1) + BL * cell(i - 1, j) + BR * cell(i, j))
            if bits:
                put(shore_tile(bits, biome), i * TILE - TILE // 2, j * TILE - TILE // 2)
    return img


# --- the assets: all grouped in the "Node map" category, ids nodemap-*, and the folder sprites/assets/nodemap/ ----------------------------
CATEGORY = 'Node map'
FOLDER = 'nodemap'
SKIN_LABELS = {'grass': 'Grass islands', 'parchment': 'Parchment chart'}
SEA_FRAMES = 4
SEA_FPS = 4
ROUTE = {'on': 2, 'off': 1, 'width': 1, 'role': 'g'}          # a dotted route: 2 pixels, a gap of 1, along the line between two nodes
# What the example map and the recommended layout use, in cells (a cell is TILE pixels square).
LAYOUT = {'laneSpacing': 9, 'floorSpacing': 8, 'margin': 8, 'nodeRadius': [2.6, 2.9, 3.2], 'bossRadius': 5.0, 'pathRadius': 0.78, 'jitter': 1}


def tile_name(bits):
    if bits == 0:
        return '0: open water (empty)'
    if bits == 15:
        return '15: all land'
    corners = [name for name, bit in (('top-left', TL), ('top-right', TR), ('bottom-left', BL), ('bottom-right', BR)) if bits & bit]
    return f'{bits}: land at ' + ', '.join(corners)


def build_assets():
    """The node map's assets. Per skin: a 16-tile shore sheet (the tile for corner bits n is frame n) and a 4-frame sea tile. Then the pins."""
    assets = []
    for biome, label in SKIN_LABELS.items():
        assets.append({
            'id': f'nodemap-{biome}-shore', 'label': f'Node map - {label} - shore tiles (16, by corner bits)', 'category': CATEGORY, 'folder': FOLDER,
            'kind': 'variants', 'place': 'none', 'names': [tile_name(b) for b in range(16)],
            'w': TILE, 'h': TILE, 'cols': 4, 'rows': 4, 'fps': 0, 'anchor': {'x': TILE // 2, 'y': TILE // 2},
            'nodemap': {'role': 'shore', 'skin': biome, 'bits': {'TL': TL, 'TR': TR, 'BL': BL, 'BR': BR}},
            'frames': [shore_tile(b, biome) for b in range(16)],
        })
        assets.append({
            'id': f'nodemap-{biome}-sea', 'label': f'Node map - {label} - sea (animated, tiles the whole map)', 'category': CATEGORY, 'folder': FOLDER,
            'kind': 'animation', 'place': 'none',
            'w': TILE, 'h': TILE, 'cols': SEA_FRAMES, 'rows': 1, 'fps': SEA_FPS, 'anchor': {'x': TILE // 2, 'y': TILE // 2},
            'nodemap': {'role': 'sea', 'skin': biome},
            'frames': [water_tile(f, biome) for f in range(SEA_FRAMES)],
        })
    assets.append({
        'id': 'nodemap-pins', 'label': 'Node map - pins (green, blue, red; the point is the anchor)', 'category': CATEGORY, 'folder': FOLDER,
        'kind': 'variants', 'place': 'none', 'names': ['Green pin', 'Blue pin', 'Red pin'],
        'w': PIN_W, 'h': PIN_H, 'cols': 3, 'rows': 1, 'fps': 0, 'anchor': {'x': PIN_TIP[0], 'y': PIN_TIP[1]},
        'nodemap': {'role': 'pin'},
        'frames': [pin_rows(r) for r in ('green', 'blue', 'red')],
    })
    return assets


def example(seed=7, lanes=5, floors=8):
    """The example map: its layout (floors, lanes, node and edge cells) and its land, for checking an app's own tile picking against."""
    nodes, edges = make_layout(lanes, floors, 4, seed)
    land, centre = land_cells(nodes, edges, lanes, floors, seed=seed, dx=LAYOUT['laneSpacing'], dy=LAYOUT['floorSpacing'], margin=LAYOUT['margin'])
    return nodes, edges, land, centre


def write_package(folder, seed=7):
    """Beside the sheets: nodemap.json (how to use them, in numbers) and an example map in each skin, with its layout."""
    import json
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    nodes, edges, land, centre = example(seed)
    for biome in BIOMES:
        img = render_map(land, biome, 0, rgb)
        draw_routes(img, rgb, edges, centre)
        for (floor, lane), (cx, cy) in centre.items():
            draw_peg(img, rgb, int((cx + 0.5) * TILE), int((cy + 0.5) * TILE), ('green', 'blue', 'red')[hashed(floor, lane) % 3])
        img.save(folder / f'example-{biome}.png')
    (folder / 'example-layout.json').write_text(json.dumps({
        'about': 'The map in example-grass.png and example-parchment.png (seed %d). Cells are TILE pixels square; (x, y) are cell coordinates, y down. '
                 'land is one string per row, # for land and . for water: draw it with the shore tiles to get the example back, pixel for pixel '
                 '(without the routes and pins).' % seed,
        'seed': seed, 'cell': TILE, 'width': len(land[0]), 'height': len(land),
        'nodes': [{'floor': f, 'lane': l, 'x': x, 'y': y, 'pin': ('green', 'blue', 'red')[hashed(f, l) % 3], 'boss': f == max(n[0] for n in nodes)}
                  for (f, l), (x, y) in sorted(centre.items())],
        'edges': [{'from': list(a), 'to': list(b)} for a, b in sorted(edges)],
        'land': [''.join('#' if c else '.' for c in row) for row in land],
    }, indent=1))
    (folder / 'nodemap.json').write_text(json.dumps({
        'about': 'How an app uses the node-map sheets in this folder. See README.md beside this file for the whole story.',
        'tile': TILE,
        'bits': {'TL': TL, 'TR': TR, 'BL': BL, 'BR': BR},
        'tileIndex': 'in a shore sheet, the tile for corner bits n is at column n % 4, row n // 4 (16 x 16 px); 0 is empty, 15 is all land',
        'tilePosition': 'the tile on the corner between cells (i-1, j-1), (i, j-1), (i-1, j) and (i, j) is drawn with its top left at (i * 16 - 8, j * 16 - 8)',
        'skins': {b: {'label': SKIN_LABELS[b], 'shore': f'nodemap-{b}-shore.png', 'sea': f'nodemap-{b}-sea.png',
                      'routeDot': {**ROUTE, 'hex': '#' + next(h for c, _, _, _, h in ep.ROLES if c == ROUTE['role'])}}
                  for b in BIOMES},
        'sea': {'frames': SEA_FRAMES, 'fps': SEA_FPS, 'size': TILE, 'note': 'every sea tile shows the same frame at the same time; it tiles the whole map, shore tiles go over it'},
        'pins': {'sheet': 'nodemap-pins.png', 'names': ['green', 'blue', 'red'], 'size': [PIN_W, PIN_H], 'anchor': list(PIN_TIP),
                 'note': 'put the anchor (the point) on the middle of the node: ((x + 0.5) * 16, (y + 0.5) * 16)'},
        'layout': LAYOUT,
        'drawOrder': ['sea (whole map)', 'shore tiles', 'routes (dotted)', 'pins', 'your node icons'],
    }, indent=1))


def preview(path, seed=7):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    scale = 5
    cell = TILE * scale
    sheet = Image.new('RGBA', (8 * (cell + 6), 4 * (cell + 18) + 20), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    for biome_i, biome in enumerate(BIOMES):
        for bits in range(16):
            col, row = bits % 8, biome_i * 2 + bits // 8
            tile = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 255))
            for y, line in enumerate(water_tile(0, biome)):
                for x, ch in enumerate(line):
                    tile.putpixel((x, y), rgb[ch] + (255,))
            for y, line in enumerate(shore_tile(bits, biome)):
                for x, ch in enumerate(line):
                    if ch != '.':
                        tile.putpixel((x, y), rgb[ch] + (255,))
            sheet.alpha_composite(tile.resize((cell, cell), Image.NEAREST), (col * (cell + 6), 18 + row * (cell + 18)))
            d.text((col * (cell + 6) + 2, row * (cell + 18) + 3), f'{biome} {bits:2d}', fill=(235, 238, 245, 255))
    sheet.save(path)
    lanes, floors = 5, 8
    nodes, edges = make_layout(lanes, floors, 4, seed)
    stem = str(path).replace('.png', '')
    # islands joined by land paths
    land, centre = land_cells(nodes, edges, lanes, floors, seed=seed)
    img = render_map(land, 'grass', 0, rgb)
    for (floor, lane), (cx, cy) in centre.items():
        draw_peg(img, rgb, int((cx + 0.5) * TILE), int((cy + 0.5) * TILE), ('green', 'blue', 'red')[hashed(floor, lane) % 3])
    img.save(stem + '-islands.png')
    # an old chart: the same islands joined by land, with the dotted routes drawn along them
    land2, centre2 = land_cells(nodes, edges, lanes, floors, seed=seed)
    img = render_map(land2, 'parchment', 0, rgb)
    draw_routes(img, rgb, edges, centre2)
    for (floor, lane), (cx, cy) in centre2.items():
        draw_peg(img, rgb, int((cx + 0.5) * TILE), int((cy + 0.5) * TILE), ('green', 'blue', 'red')[hashed(floor, lane) % 3])
    img.save(stem + '-parchment.png')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview, args.seed)
        print('wrote', args.preview, 'and the -islands and -parchment maps beside it')


if __name__ == '__main__':
    main()
