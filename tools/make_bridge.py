#!/usr/bin/env python3
"""A rickety wooden bridge to span a gap between two pieces of land, with a rope rail along the back side only (so characters
walking it are never hidden behind a front rail).

Four sprites, each one tile, drawn on the same 32 wide cell as the ground tiles (a tile's top face is a diamond
32 wide and 16 tall; see terrain.js):

    bridge-flat-NE     a flat section running along the NE-SW axis
    bridge-flat-SE     a flat section running along the NW-SE axis
    bridge-slope-NE    the start of a bridge: it runs down from the land's height to the deck, going NE
    bridge-slope-SE    the same, going SE

The deck is a few pixels lower than the land (it sags over the gap, like the sunken water), and a slope joins the land to
it. The slopes going NW and SW are those two flipped left to right, like the facing marker, so a bridge is built:

    land, slope, flat, flat, ... flat, flipped slope, land

along either axis: a NE-SW bridge starts with the NE slope and ends with the flipped SE slope; a NW-SE bridge starts with
the SE slope and ends with the flipped NE slope. The anchor is the middle of the land-level top face, on the ground, so a
bridge tile sits where a ground tile would.

It is built the way the sprites are everywhere: planks, posts and rope laid out in a small 3D space and drawn in the palette's
own colours (the wood of the logs and crates), with the outline colour round it. The planks are uneven on purpose: crooked,
different lengths, a missing one, a frayed rope, a leaning post.

    python3 tools/make_bridge.py --preview previews/bridge.png
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

W, H = 32, 40
YC = 18                                  # the middle of the land-level top face, from the top of the cell
ANCHOR = (16, YC)
SINK = 6                                 # how far below the land the deck hangs
WOOD = dict(lit='a', base='e', shade='f', deep='g')     # orange, coral, orchid, plum: the logs' and crates' wood
ROPE = ('C', 'b', 'c')                   # sand, amber, salmon
PLANKS = 6                               # to a tile
DECK = 0.33                              # half the deck's width, as a fraction of a tile
RAIL = 0.37                              # where the rails stand
POST = 5                                 # how high the posts and rails are, in pixels
THICK = 2.3                              # how thick the deck is, in pixels


def project(a, b, h):
    """Tile coordinates to cell pixels: a runs SE, b runs NE, h is height in pixels."""
    return 16 + 16 * (a + b), YC + 8 * (a - b) - h


class Canvas:
    def __init__(self):
        self.grid = [['.'] * W for _ in range(H)]

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            self.grid[y][x] = c

    def polygon(self, pts, c):
        """Fill a polygon, the pixels whose middle is inside it."""
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y + 0.5 < max(y0, y1):
                    xs.append(x0 + (x1 - x0) * (y + 0.5 - y0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k] + 0.5), int(xs[k + 1] + 0.5)):
                    self.put(x, y, c)

    def line(self, p, q, c):
        (x0, y0), (x1, y1) = p, q
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def outline(self, c='O'):
        out = [row[:] for row in self.grid]
        for y in range(H):
            for x in range(W):
                if self.grid[y][x] == '.' and any(0 <= x + dx < W and 0 <= y + dy < H and self.grid[y + dy][x + dx] != '.'
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out[y][x] = c
        self.grid = out

    def lines(self):
        return [''.join(row) for row in self.grid]


def render_pixels(axis, kind):
    """One sprite: axis 'NE' or 'SE' is the way the bridge runs, kind 'flat' or 'slope'."""
    rng = random.Random(f'{axis}-{kind}')
    cv = Canvas()
    ne = axis == 'NE'

    def at(t, w, h):
        """A point by travel (t, -0.5 to 0.5, going NE or SE), across (w) and height (pixels)."""
        return project(w, t, h) if ne else project(t, w, h)

    def deck_h(t):
        return -SINK if kind == 'flat' else -SINK * (t + 0.5)

    far, near = (-1, 1) if ne else (1, -1)           # which side of the deck is behind and which in front
    seen = near                                      # the side of the deck whose edge shows

    def rail(side):
        w = RAIL * side
        tops = [(t, deck_h(t) + POST) for t in (-0.44, 0.0, 0.44)]
        lean = {0: 0.0, 1: rng.choice((-0.9, 0.9)), 2: 0.0}
        gap = rng.random() < 0.7 and kind == 'flat' and side == far          # a frayed rope on the far rail
        # the posts: a column two pixels wide, lit on the left and shaded on the right
        for i, (t, top) in enumerate(tops):
            x0, y0 = at(t, w, deck_h(t) - 1)
            x1, y1 = at(t, w, top)
            x1 += lean[i] * (1 if side == near else -1)
            cv.polygon([(x0 - 1, y0), (x0 + 1, y0), (x1 + 1, y1), (x1 - 1, y1)], WOOD['base'])
            cv.line((x0 - 1, y0), (x1 - 1, y1), WOOD['lit'])
            cv.line((x0, y0), (x1, y1), WOOD['base'])
            cv.put(x1, y1 - 1, ROPE[1])
        # two ropes along the posts, sagging between them
        for level, sag in ((1.0, 1.4),):
            prev = None
            for k in range(0, 41):
                u = k / 40
                t = -0.44 + 0.88 * u
                if gap and level == 1.0 and 0.50 < u < 0.64:
                    prev = None
                    continue
                top = deck_h(t) + POST * level + (0 if level == 1.0 else -0.5)
                x, y = at(t, w, top)
                y += sag * 4 * u * (1 - u)
                if prev:
                    cv.line(prev, (x, y), ROPE[0] if level == 1.0 else ROPE[1])
                prev = (x, y)

    rail(far)

    # the deck: planks laid across, each a little different
    order = list(range(PLANKS))
    if ne:
        order.reverse()                                  # nearer planks are drawn last
    missing = rng.randrange(1, PLANKS - 1) if kind == 'flat' else None
    for k in order:
        if k == missing:
            continue
        t0 = -0.5 + k / PLANKS + rng.uniform(0.0, 0.012)
        t1 = -0.5 + (k + 1) / PLANKS - rng.uniform(0.02, 0.05)
        w0, w1 = -DECK + rng.uniform(-0.05, 0.02), DECK + rng.uniform(-0.02, 0.05)
        tone = rng.choice((WOOD['lit'], WOOD['lit'], WOOD['base'], WOOD['base'], WOOD['base'], WOOD['shade']))
        top = [at(t0, w0, deck_h(t0)), at(t1, w0, deck_h(t1)), at(t1, w1, deck_h(t1)), at(t0, w1, deck_h(t0))]
        wedge = w1 if seen > 0 else w0                        # the long edge facing us, with the plank's thickness under it
        edge = [at(t0, wedge, deck_h(t0)), at(t1, wedge, deck_h(t1)), at(t1, wedge, deck_h(t1) - THICK), at(t0, wedge, deck_h(t0) - THICK)]
        cv.polygon(edge, WOOD['shade'] if tone != WOOD['shade'] else WOOD['deep'])
        cv.polygon(top, tone)
        # a knot, or a nail, now and then
        if rng.random() < 0.3:
            cv.put(*at((t0 + t1) / 2, rng.choice((w0, w1)) * 0.7, deck_h((t0 + t1) / 2)), WOOD['deep'])

    # the beam under the deck on the side we see, and a few frayed ropes hanging from it
    beam_w = DECK * seen
    p0, p1 = at(-0.5, beam_w, deck_h(-0.5) - THICK), at(0.5, beam_w, deck_h(0.5) - THICK)
    q0, q1 = at(-0.5, beam_w, deck_h(-0.5) - THICK - 1.4), at(0.5, beam_w, deck_h(0.5) - THICK - 1.4)
    cv.polygon([p0, p1, q1, q0], WOOD['deep'])
    for t in (-0.2, 0.3):
        x, y = at(t, beam_w, deck_h(t) - THICK - 1.4)
        for d in range(rng.randrange(2, 5)):
            cv.put(x, y + d, ROPE[1] if d % 2 == 0 else WOOD['deep'])

    # No rail on the near side: a character walking along the bridge would be drawn behind it. Only the back rail stands.
    cv.outline('O')
    return cv.lines()


def deck_mask(axis, kind):
    """The walkable deck of a bridge sprite as a W x H mask: the strip of planks, from one edge of the tile to the other."""
    ne = axis == 'NE'
    drop = lambda t: -SINK if kind == 'flat' else -SINK * (t + 0.5)

    def at(t, w, h):
        return project(w, t, h) if ne else project(t, w, h)
    corners = [at(-0.5, -DECK, drop(-0.5)), at(0.5, -DECK, drop(0.5)), at(0.5, DECK, drop(0.5)), at(-0.5, DECK, drop(-0.5))]
    cv = Canvas()
    cv.polygon(corners, '#')
    return [[cv.grid[y][x] == '#' for x in range(W)] for y in range(H)]


SPRITES = [
    ('bridge-flat-ne', 'Bridge - flat, NE-SW', 'NE', 'flat'),
    ('bridge-flat-se', 'Bridge - flat, NW-SE', 'SE', 'flat'),
    ('bridge-slope-ne', 'Bridge - slope down to the NE', 'NE', 'slope'),
    ('bridge-slope-se', 'Bridge - slope down to the SE', 'SE', 'slope'),
]


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    sheet_img = Image.open(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / 'ground.png').convert('RGBA')
    cell = lambda c, r: sheet_img.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    grass, water = cell(0, 0), cell(1, 2)

    def sprite(axis, kind, flip=False):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for y, line in enumerate(render_pixels(axis, kind)):
            for x, c in enumerate(line):
                if c != '.':
                    im.putpixel((x, y), rgb[c] + (255,))
        return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im

    scale = 5
    out = Image.new('RGBA', (170 * scale, 135 * scale), (36, 38, 56, 255))

    def build(axis):
        """Land, a slope, flat sections, the flipped slope, land: along one axis, over sunken water."""
        scene = Image.new('RGBA', (170, 135), (0, 0, 0, 0))
        n = 6
        for s_ in range(n):
            dx, dy = (16, -8) if axis == 'NE' else (16, 8)
            x0, y0 = (8, 62) if axis == 'NE' else (8, 14)
            x, y = x0 + dx * s_, y0 + dy * s_
            land = s_ in (0, n - 1)
            scene.alpha_composite(grass if land else water, (x, y))
            if not land:
                if s_ == 1:
                    sp = sprite(axis, 'slope')                      # the start: NE slope for a NE-SW bridge, SE slope for a NW-SE one
                elif s_ == n - 2:
                    sp = sprite('SE' if axis == 'NE' else 'NE', 'slope', flip=True)   # the end: the other slope, flipped
                else:
                    sp = sprite(axis, 'flat')
                scene.alpha_composite(sp, (x, y + 8 - YC))
        return scene
    for i, axis in enumerate(('NE', 'SE')):
        scene = build(axis)
        out.alpha_composite(scene.resize((scene.width * scale, scene.height * scale), Image.NEAREST), (0, 0)) if i == 0 else None
    # one panel per axis, side by side
    panel_w = 132
    out = Image.new('RGBA', (2 * panel_w * scale + 10, 85 * scale), (36, 38, 56, 255))
    for i, axis in enumerate(('NE', 'SE')):
        scene = build(axis).crop((0, 0, panel_w, 85))
        out.alpha_composite(scene.resize((panel_w * scale, 85 * scale), Image.NEAREST), (i * (panel_w * scale + 10), 0))
    if args.preview:
        out.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
