#!/usr/bin/env python3
"""A body explosion: what happens when a corpse is destroyed. Six frames, generic: it is not any one creature, it is a burst of gore at the place the body lay.

It is drawn in the blood pool's own four colours (see make_blood_pool.py: a purple rim, a dark magenta body, a brighter wet magenta and a hot pink glint), with no outline, as a decal-like effect:

    1  the body bursts: a hot bright core
    2  the cloud swells and chunks and drops are thrown out in every direction
    3  the cloud is thinning and the chunks are at the top of their arc: with the second, the biggest frames
    4  the cloud breaks up, the chunks fall
    5  the chunks land and the drops splash on the ground
    6  only splatters on the ground and a few last drops

The cell is 48 x 48 and the anchor is (24, 34), the middle of the body on the ground: put it where the corpse is, on the tile's middle. The chunks fly on the ground's own isometric plane (a circle on the
ground is an ellipse twice as wide as tall), up and out and down, and the ones that land leave a splat where they land. Everything is deterministic.

    python3 tools/make_body_explosion.py --preview previews/body-explosion.png      the six frames over a grass tile and a corpse, enlarged, and a gif beside it
"""
import argparse
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family  # noqa: E402

CELL_W, CELL_H = 48, 48
ANCHOR = (24, 34)
FRAMES = 6
FPS = 12
RIM, BODY, WET, GLINT = 'u', 'h', 'i', 'j'          # the blood pool's: purple, dark magenta, magenta, hot pink
CATEGORY = 'Animations'
ID = 'body-explosion'
G = 5.2                                              # gravity on the chunks, in pixels a frame squared
CHUNKS = 16
DROPS = 30


def blob(grid, cx, cy, rx, ry, seed, hot, thin=0.0):
    """A ragged cloud of gore: an ellipse `rx` x `ry` at (cx, cy), shaded from a purple rim to a wet middle, with a hot glint core, and `thin` (0 to 1) of it eaten away."""
    rng = random.Random(f'explosion-blob-{seed}')
    noise = [rng.uniform(-0.18, 0.18) for _ in range(24)]
    for y in range(CELL_H):
        for x in range(CELL_W):
            dx, dy = (x + 0.5 - cx) / max(rx, 0.1), (y + 0.5 - cy) / max(ry, 0.1)
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            edge = 1.0 + noise[int((ang + math.pi) / (2 * math.pi) * 24) % 24] + 0.08 * math.sin(5 * ang + seed)
            if r > edge:
                continue
            if thin and rng.random() < thin * (0.35 + 0.65 * r / edge):
                continue
            depth = 1 - r / edge
            role = RIM if depth < 0.2 else WET if depth > 0.55 else BODY
            if hot and depth > 0.55 and r < 0.35 * edge:
                role = GLINT
            grid[y][x] = role


def chunk(grid, x, y, shape):
    for dy, row in enumerate(shape):
        for dx, ch in enumerate(row):
            if ch != '.' and 0 <= x + dx < CELL_W and 0 <= y + dy < CELL_H:
                grid[y + dy][x + dx] = ch


# gibs: bits of flesh, a few pixels across, lit from the upper left (a hot corner, a wet middle, a purple shadow)
SHAPES = [
    ['jii.', 'ihhu', '.huu'],
    ['.ij.', 'ihhh', 'hhuu', '.uu.'],
    ['ii.', 'ihh', 'huu'],
    ['.jh', 'ihh', 'hhu', '.u.'],
    ['jii', 'hhh', '.uu'],
]


def flights():
    """Each chunk and drop: where it goes on the ground (an angle and a speed), how hard it is thrown up, and its look. The same every time."""
    rng = random.Random('body-explosion-flights')
    out = []
    for k in range(CHUNKS):
        out.append(dict(kind='chunk', a=2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / CHUNKS, R=rng.uniform(15.0, 22.0), up=rng.uniform(6.5, 10.5), shape=SHAPES[k % len(SHAPES)]))
    for k in range(DROPS):
        out.append(dict(kind='drop', a=rng.uniform(0, 2 * math.pi), R=rng.uniform(9.0, 20.0), up=rng.uniform(5.5, 10.5), role=(WET, BODY, GLINT, WET)[k % 4]))
    return out


FLIGHTS = flights()


def position(f, t):
    """Where a flying piece is at time t (in frames, 0 at the burst): (screen x, screen y, height above the ground, landed?)."""
    r = f['R'] * (1 - math.exp(-1.4 * t))                              # thrown hard and slowing: out of the cloud at once, then coasting
    z = f['up'] * t - 0.5 * G * t * t
    landed = z <= 0 and t > 0.5
    if landed:                                                         # it stops where it came down
        tl = f['up'] * 2 / G
        r, z = f['R'] * (1 - math.exp(-1.4 * tl)), 0.0
    x = ANCHOR[0] + r * math.cos(f['a'])
    y = ANCHOR[1] + 0.5 * r * math.sin(f['a']) - max(z, 0.0)
    return x, y, z, landed


def render_pixels(frame):
    grid = [['.'] * CELL_W for _ in range(CELL_H)]
    t = frame + 0.5 if frame else 0.35
    # the cloud: a hot bright core at the burst, swelling and rising, then thinning and breaking up
    sizes = [(9, 5, 0.0), (11, 7, 0.0), (12, 8, 0.25), (9, 5, 0.6), (6, 3, 0.85), (0, 0, 1.0)]
    rx, ry, thin = sizes[frame]
    if rx:
        blob(grid, ANCHOR[0], ANCHOR[1] - 2 - 2.2 * frame, rx, ry, frame, hot=frame < 3, thin=thin)
    # the ground splats of the chunks that have landed come first, so what is still flying is drawn over them
    flying = []
    for f in FLIGHTS:
        if frame == 0:
            continue
        x, y, z, landed = position(f, t)
        if landed:
            if f['kind'] == 'chunk':
                for dx, dy, role in ((0, 0, BODY), (-1, 0, RIM), (1, 0, RIM), (0, 1, RIM), (-2, 0, BODY) if f['R'] > 18 else (0, -1, WET)):
                    px, py = int(x) + dx, int(y) + dy
                    if 0 <= px < CELL_W and 0 <= py < CELL_H and grid[py][px] == '.':
                        grid[py][px] = role
            else:
                px, py = int(x), int(y)
                if 0 <= px < CELL_W and 0 <= py < CELL_H and grid[py][px] == '.':
                    grid[py][px] = f['role'] if f['role'] != GLINT else WET
        else:
            flying.append((z, x, y, f))
    for z, x, y, f in sorted(flying):                                  # the highest last, so it is in front
        px, py = int(round(x)), int(round(y))
        if f['kind'] == 'chunk':
            chunk(grid, px - 1, py - 1, f['shape'])
        elif 0 <= px < CELL_W and 0 <= py < CELL_H:
            grid[py][px] = f['role']
            if f['role'] != WET and 0 <= py + 1 < CELL_H and frame > 0 and grid[py + 1][px] == '.':
                grid[py + 1][px] = RIM                                   # a short tail on a fast drop
    return [''.join(row) for row in grid]


def build_assets():
    """One `body-explosion` asset: six frames at 12 a second on a 48 x 48 cell, anchored at (24, 34), the middle of the body on the ground."""
    make = family(CATEGORY, CELL_W, CELL_H, ANCHOR, place='ground')
    return [make(ID, 'Body explosion', 'animation', [render_pixels(f) for f in range(FRAMES)], fps=FPS)]


def preview(path, scale=6):
    from PIL import Image
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    root = Path(__file__).resolve().parent.parent
    ground = Image.open(root / 'sprites' / 'assets' / 'ground.png').convert('RGBA')
    grass = ground.crop((0, 0, 32, 32))
    dead = root / 'sprites' / 'slim' / 'slim-deadSE.png'
    sprite = Image.open(dead).convert('RGBA') if dead.exists() else None
    frames = []
    for f in range(FRAMES):
        im = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
        for y, row in enumerate(render_pixels(f)):
            for x, c in enumerate(row):
                if c != '.':
                    im.putpixel((x, y), rgb[c] + (255,))
        frames.append(im)
    cell_w, cell_h = 64, 64
    bg = (36, 38, 56, 255)
    strip = Image.new('RGBA', (FRAMES * cell_w, cell_h * 2), bg)
    for i, im in enumerate(frames):
        for row, show_body in enumerate((True, False)):
            ox, oy = i * cell_w + 8, row * cell_h + 8
            tile_x, tile_y = ox + ANCHOR[0] - 16, oy + ANCHOR[1] - 8                  # the tile's middle is under the anchor
            strip.alpha_composite(grass, (tile_x, tile_y))
            if row == 0 and sprite and i == 0:                                         # the corpse, on the first frame only: it is gone by the next
                strip.alpha_composite(sprite, (tile_x, tile_y + 8 - 26))
            strip.alpha_composite(im, (ox, oy))
    big = strip.resize((strip.width * scale // 2, strip.height * scale // 2), Image.NEAREST)
    big.save(path)
    gif = Path(path).with_suffix('.gif')
    stage = []
    for im in frames:
        f = Image.new('RGBA', (cell_w, cell_h), bg)
        f.alpha_composite(grass, (8 + ANCHOR[0] - 16, 8 + ANCHOR[1] - 8))
        f.alpha_composite(im, (8, 8))
        stage.append(f.resize((cell_w * scale, cell_h * scale), Image.NEAREST).convert('P', palette=Image.ADAPTIVE))
    stage[0].save(gif, save_all=True, append_images=stage[1:], duration=int(1000 / FPS * 2), loop=0, disposal=2)
    return gif


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='the six frames over a grass tile (with a corpse on the first), enlarged, and a gif beside it at half speed')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        gif = preview(args.preview)
        print('the body explosion, enlarged ->', args.preview, 'and', gif)


if __name__ == '__main__':
    main()
