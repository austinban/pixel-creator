#!/usr/bin/env python3
"""The facing marker: a yellow arrowhead lying on the ground, to show which way a character will face.

Four of them sit round the tile a character stands on, one for each diagonal. Only two are drawn,
NE and SE: NW and SW are those mirrored. The chosen one is yellow and the others are the same sprite
recoloured pale, so it is one asset that recolours like the rest, and it does not animate.

It follows the crystal's conventions: a small 3D model, flat-shaded in the shared palette's colour
roles, light from the upper left, a dark outline. The model is a flat arrowhead slab with a little
thickness, lying on the ground plane. Tiles are 32 x 16 diamonds, so a step of one tile along the NE
axis moves 16 right and 8 up, and along the SE axis 16 right and 8 down.

    python3 tools/make_facing.py --model previews/facing-3d.png    look at the 3D model first
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

TILE_HALF_W, TILE_HALF_H = 16, 8       # the tile diamond, in game pixels
# The arrowhead on the ground, in tile units. u runs along the NE axis (the tip points along +u), v along
# the SE axis. It measures about 0.55 of a tile each way, like the placeholder it replaces.
TIP = (0.30, 0.0)
BASE = ((-0.25, -0.28), (-0.25, 0.28))
THICKNESS = 1.5                         # game pixels, how thick the slab is
OFFSET = 0.78                           # how far from the tile's middle the marker sits, in tiles
LIGHT = (-1.0, -1.0)                    # towards the light on screen: the upper left

# Colour ramps, lit to deep. The chosen marker is yellow; the others are the same shape in pale.
YELLOW = ('t', 'd', 'b', 'a')           # cream, yellow, amber, orange
PALE = ('t', 'r', 'q', 'p')             # cream, mint, teal, steel
OUTLINE = 'O'
# The marker's own edge instead of the standard indigo: two tones of its own family, lighter on the
# edges facing the light (the top) and deeper on the ones turned away (the bottom).
EDGE = ('b', 'a')                       # amber above, orange below
PALE_EDGE = ('p', 'l')                  # steel above, lavender below


def rgb(role):
    hex_ = next(h for c, _, _, _, h in ep.ROLES if c == role)
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4))


def to_screen(u, v):
    """A point on the ground, in tile units, to screen pixels from the tile's middle."""
    return (TILE_HALF_W * (u + v), TILE_HALF_H * (v - u))


def outline_of(direction):
    """The arrowhead's corners on screen, relative to its own middle. NE points up-right, SE down-right."""
    pts = [TIP, *BASE]
    if direction == 'SE':                # turn it a quarter: the tip along +v
        pts = [(v, u) for u, v in pts]
    cu = sum(p[0] for p in pts) / 3
    cv = sum(p[1] for p in pts) / 3
    return [to_screen(u - cu, v - cv) for u, v in pts]


def edge_light(points):
    """For each edge of the arrowhead, how much it faces the light: 1 is square on, 0 is edge on or away."""
    out = []
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    for a, b in zip(points, points[1:] + points[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        nx, ny = ey, -ex                                  # a normal; make it point outwards
        if nx * ((a[0] + b[0]) / 2 - cx) + ny * ((a[1] + b[1]) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        length = math.hypot(nx, ny) or 1
        out.append(max(0.0, (nx * LIGHT[0] + ny * LIGHT[1]) / (length * math.hypot(*LIGHT))))
    return out


def render_smooth(direction, ramp=YELLOW, ppu=14):
    """The 3D model drawn large and smooth: `ppu` image pixels to one game pixel.

    Returns the picture and where the arrow's own middle, on the ground, is in it.
    """
    from PIL import Image, ImageDraw
    pts = outline_of(direction)
    pad = 5
    w = int((max(p[0] for p in pts) - min(p[0] for p in pts) + 2 * pad) * ppu)
    h = int((max(p[1] for p in pts) - min(p[1] for p in pts) + THICKNESS + 2 * pad) * ppu)
    ox = -min(p[0] for p in pts) + pad
    oy = -min(p[1] for p in pts) + pad + THICKNESS
    ss = 3                                                 # drawn three times larger and shrunk, for smooth edges
    img = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def at(point, lift=0.0):
        return ((point[0] + ox) * ppu * ss, (point[1] + oy - lift) * ppu * ss)

    ink = rgb(OUTLINE) + (255,)
    n = len(pts)
    bottom = [at(p) for p in pts]
    top = [at(p, THICKNESS) for p in pts]
    # the outline: every wall and the top, each swollen a little, drawn first so it shows all round
    swell = int(0.55 * ppu * ss)

    def inked(shape):
        d.polygon(shape, fill=ink)
        d.line(shape + [shape[0]], fill=ink, width=2 * swell, joint='curve')    # centred on the edge, so it grows outward
    inked(top)
    for i in range(n):
        j = (i + 1) % n
        inked([bottom[i], bottom[j], top[j], top[i]])
    # the walls that face the viewer, lit or in shade by which way they face
    cy = sum(p[1] for p in pts) / n
    cx = sum(p[0] for p in pts) / n
    lights = edge_light(pts)
    for i in range(n):
        j = (i + 1) % n
        ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
        nx, ny = ey, -ex
        if nx * ((pts[i][0] + pts[j][0]) / 2 - cx) + ny * ((pts[i][1] + pts[j][1]) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        if ny <= 0:
            continue                                       # a wall on the far side: hidden
        colour = rgb(ramp[2] if lights[i] > 0.35 else ramp[3]) + (255,)
        d.polygon([bottom[i], bottom[j], top[j], top[i]], fill=colour)
    # the top face, with a bright rim on the edges that face the light and a darker one on the rest
    d.polygon(top, fill=rgb(ramp[1]) + (255,))
    rim = int(0.5 * ppu * ss)
    for i in range(n):
        j = (i + 1) % n
        colour = rgb(ramp[0] if lights[i] > 0.35 else ramp[2]) + (255,)
        d.line([top[i], top[j]], fill=colour, width=rim)
    return img.resize((w, h), Image.LANCZOS), (ox * ppu, oy * ppu)


# --- the pixel sprite ---------------------------------------------------------
CELL_W, CELL_H = 20, 14                 # a small tight cell: the arrow is about 16 x 10 with its outline
MIDDLE = (CELL_W // 2, 8)               # where the arrow's middle on the ground sits in the cell (a pixel corner)
SAMPLES = 8                             # sub-samples per pixel side when turning the model into pixels
RIM = 0.55                              # width of the bright rim, in game pixels


def render_pixels(direction, ramp=YELLOW, outline=EDGE):
    """The model as game pixels: rows of colour-role characters, outline included.

    The same walls, top and rim as the smooth model, drawn flat in the roles' own colours and
    sampled per pixel: a pixel takes the role that covers most of it.
    """
    from PIL import Image, ImageDraw
    ss = SAMPLES
    pts = outline_of(direction)
    n = len(pts)
    img = Image.new('RGB', (CELL_W * ss, CELL_H * ss), (0, 0, 0))
    d = ImageDraw.Draw(img)

    def at(point, lift=0.0):
        return ((point[0] + MIDDLE[0]) * ss, (point[1] + MIDDLE[1] - lift) * ss)

    bottom = [at(p) for p in pts]
    top = [at(p, THICKNESS) for p in pts]
    lights = edge_light(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    for i in range(n):
        j = (i + 1) % n
        ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
        nx, ny = ey, -ex
        if nx * ((pts[i][0] + pts[j][0]) / 2 - cx) + ny * ((pts[i][1] + pts[j][1]) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        if ny <= 0:
            continue
        d.polygon([bottom[i], bottom[j], top[j], top[i]], fill=rgb(ramp[2] if lights[i] > 0.35 else ramp[3]))
    d.polygon(top, fill=rgb(ramp[1]))
    for i in range(n):
        j = (i + 1) % n
        d.line([top[i], top[j]], fill=rgb(ramp[0] if lights[i] > 0.35 else ramp[2]), width=max(1, int(RIM * ss)))

    roles = {rgb(c): c for c in ramp}
    px = img.load()
    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    for y in range(CELL_H):
        for x in range(CELL_W):
            count = {}
            for sy in range(ss):
                for sx in range(ss):
                    colour = px[x * ss + sx, y * ss + sy]
                    if colour in roles:
                        count[roles[colour]] = count.get(roles[colour], 0) + 1
            if sum(count.values()) * 2 >= ss * ss:                       # at least half covered
                grid[y][x] = max(count, key=count.get)
    lit_edge, dark_edge = outline
    filled = [(y, x) for y in range(CELL_H) for x in range(CELL_W) if grid[y][x] != '.']
    edge = {}
    for y, x in filled:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < CELL_H and 0 <= nx < CELL_W and grid[ny][nx] == '.':
                    edge.setdefault((ny, nx), []).append((dy, dx))
    for (ny, nx), toward in edge.items():
        # (dy, dx) points from the picture out to this pixel: an edge above or to the left of the picture faces the light
        dy = sum(t[0] for t in toward)
        dx = sum(t[1] for t in toward)
        grid[ny][nx] = lit_edge if (dy < 0 or (dy == 0 and dx < 0)) else dark_edge
    return [''.join(row) for row in grid]


def render_sheet(ppu=14):
    """The model, big, NE and SE, and then to scale round a tile, as it will sit in the game."""
    from PIL import Image, ImageDraw
    ne, _ = render_smooth('NE', ppu=ppu)
    se, _ = render_smooth('SE', ppu=ppu)
    scale = 8                                            # the tile mock-up: image pixels per game pixel
    tile_w, tile_h = 80, 56
    mock = Image.new('RGBA', (tile_w * scale, tile_h * scale), (58, 190, 52, 255))
    md = ImageDraw.Draw(mock)
    cx, cy = tile_w * scale / 2, tile_h * scale / 2 + 6 * scale
    diamond = [(cx - TILE_HALF_W * scale, cy), (cx, cy - TILE_HALF_H * scale), (cx + TILE_HALF_W * scale, cy), (cx, cy + TILE_HALF_H * scale)]
    md.polygon(diamond, fill=(235, 230, 120, 255))
    # a stand-in for the character's feet, so the size of the marker can be judged against something
    md.ellipse([cx - 5 * scale, cy - 14 * scale, cx + 5 * scale, cy + 2 * scale], fill=(70, 30, 100, 255))
    # NE and SE are drawn; SW is SE mirrored, and NW is NE mirrored. NE is the chosen one here.
    spots = {'NE': (OFFSET, 0, 'NE', YELLOW, False), 'SE': (0, OFFSET, 'SE', PALE, False),
             'SW': (-OFFSET, 0, 'SE', PALE, True), 'NW': (0, -OFFSET, 'NE', PALE, True)}
    for name, (u, v, sprite, ramp, mirrored) in spots.items():
        tile = render_smooth(sprite, ramp, ppu=scale)
        img, (hx, hy) = tile
        if mirrored:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
            hx = img.width - hx
        sx, sy = to_screen(u, v)
        mock.alpha_composite(img, (int(cx + sx * scale - hx), int(cy + sy * scale - hy)))
    pad = 24
    tall = max(ne.height, se.height, mock.height)
    sheet = Image.new('RGBA', (ne.width + se.width + mock.width + pad * 4, tall + 30), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    x = pad
    for label, img in (('NE (3D, large)', ne), ('SE (3D, large)', se), ('to scale on a tile; NW and SW are mirrors', mock)):
        sheet.alpha_composite(img, (x, 24))
        draw.text((x, 6), label, fill=(235, 238, 245, 255))
        x += img.width + pad
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, required=True, help='write the 3D preview here')
    args = parser.parse_args()
    args.model.parent.mkdir(parents=True, exist_ok=True)
    render_sheet().save(args.model)
    print(f'3D preview of the facing marker -> {args.model}; no sprite was made')


if __name__ == '__main__':
    main()
