#!/usr/bin/env python3
"""Build the assets: things that aren't characters.

Each asset is painted in the same colour roles as the characters, so it recolours
the same way. The turn crystal is rendered from a small 3D model: an elongated
octahedron, flat-shaded, turning about its vertical axis and bobbing as it goes.
Four faces repeat every quarter turn, so the frames loop with no seam.

    python3 tools/make_assets.py [--png-dir DIR]

Writes assets/data.js. With --png-dir it also writes each asset's sheet as a PNG,
and every frame is checked to re-render identically from its roles.
"""
import argparse
import importlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
import make_facing  # noqa: E402
import make_arrow  # noqa: E402
import make_bow  # noqa: E402
import make_ground  # noqa: E402
import make_overlay  # noqa: E402
import make_fire  # noqa: E402
import make_ui  # noqa: E402
import make_aoe  # noqa: E402
import make_vine  # noqa: E402
import make_weapons  # noqa: E402

# Roles used, by palette character: spark, then the green ramp, then the outline.
SPARK, LIT, BASE, SHADE, DEEP, OUTLINE = 't', 'z', 'A', 'B', 's', 'O'

SHEET_COLS = 8  # frames per row in an asset's sheet
GROUND_ROW = 27  # the lowest painted row of a standing character: assets that sit on the ground end here too

# --- the turn crystal -------------------------------------------------------
CRYSTAL = dict(
    id='crystal', label='Turn crystal',
    w=32, h=32, frames=8, fps=8,   # a square cell like the characters', with room around the crystal
    half_height=10.0,   # apex to the middle
    radius=5.6,         # the middle's radius
    tilt=14,            # degrees the camera looks down
    bob=1,              # rows the whole crystal rises and falls
    light=(-0.45, 0.62, 0.64),
)


def normalise(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


# --- rocks ------------------------------------------------------------------
# A rock is a jittered, subdivided icosahedron with a flat base, flat-shaded. Stone
# is the cool ramp (steel, lavender, indigo) held to a narrow range so it reads as
# rock and not as a gem. Moss is small green speckle on the upward-facing surfaces.
STONE = ((0.84, 'q'), (0.62, 'p'), (0.44, 'l'), (0.30, 'k'), (0.0, 'w'))
MOSS = ((0.62, 'z'), (0.44, 'A'), (0.0, 'B'))
CRACK = 'w'
PHI = (1 + 5 ** 0.5) / 2
ICO_VERTS = [(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0), (0, -1, PHI), (0, 1, PHI),
             (0, -1, -PHI), (0, 1, -PHI), (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)]
ICO_FACES = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
             (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
             (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]


def subdivided_sphere():
    """The icosahedron with every face split in four, on the unit sphere."""
    verts = [normalise(v) for v in ICO_VERTS]
    midpoints = {}

    def mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in midpoints:
            verts.append(normalise(tuple((verts[i][c] + verts[j][c]) / 2 for c in range(3))))
            midpoints[key] = len(verts) - 1
        return midpoints[key]

    faces = []
    for a, b, c in ICO_FACES:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return verts, faces


SPHERE = subdivided_sphere()


class Lcg:
    """A tiny seeded random source, so the same seed always gives the same rock."""
    def __init__(self, seed):
        self.state = (seed * 2654435761) % 2 ** 32 or 1

    def next(self):
        self.state = (self.state * 1664525 + 1013904223) % 2 ** 32
        return self.state / 2 ** 32


ROCK = dict(
    id='rock', label='Rock barrier', w=32, h=32,
    tilt=28,          # degrees the camera looks down
    flat=0.5,         # how much of the bottom is cut away, so it sits on the ground
    light=(-0.45, 0.62, 0.64),
    variants=[
        dict(name='Boulder', moss=40, cracks=2, rocks=[dict(rx=11.5, ry=11.0, rz=9.0, jitter=0.16, seed=4, yaw=20, ox=0, oz=0)]),
        dict(name='Tall rock', moss=30, cracks=2, rocks=[dict(rx=8.0, ry=14.0, rz=7.0, jitter=0.16, seed=2, yaw=-25, ox=0, oz=0)]),
        dict(name='Twin rocks', moss=40, cracks=2, rocks=[dict(rx=7.6, ry=9.2, rz=7.0, jitter=0.16, seed=3, yaw=10, ox=-4.4, oz=-2),
                                                         dict(rx=4.8, ry=5.2, rz=4.6, jitter=0.18, seed=14, yaw=-30, ox=6.4, oz=3)]),
        dict(name='Slab', moss=25, cracks=2, rocks=[dict(rx=11.6, ry=5.6, rz=7.6, jitter=0.14, seed=5, yaw=8, ox=0, oz=0)]),
    ],
)


def tone(table, value):
    return next(char for floor, char in table if value > floor)


def hash2(x, y, seed):
    return ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) % 1000 / 1000


def render_rock_variant(spec, variant, seed_override=None):
    w, h = spec['w'], spec['h']
    tilt = math.radians(spec['tilt'])
    light = normalise(spec['light'])
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    sphere_verts, sphere_faces = SPHERE
    tris = []
    first_seed = None
    for index, rock in enumerate(variant['rocks']):
        seed = rock['seed'] if seed_override is None else seed_override + index * 17
        first_seed = seed if first_seed is None else first_seed
        rng = Lcg(seed)
        yaw = math.radians(rock['yaw'])
        verts = []
        for nx, ny, nz in sphere_verts:
            k = 1 + (rng.next() - 0.5) * 2 * rock['jitter']
            x, y, z = nx * rock['rx'] * k, ny * rock['ry'] * k, nz * rock['rz'] * k
            y = max(y, -spec['flat'] * rock['ry'])
            x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
            verts.append((x + rock['ox'], y, z + rock['oz']))
        centre = (rock['ox'], 0, rock['oz'])
        for fid, face in enumerate(sphere_faces):
            pts = [verts[i] for i in face]
            u = tuple(pts[1][i] - pts[0][i] for i in range(3))
            v2 = tuple(pts[2][i] - pts[0][i] for i in range(3))
            n = (u[1] * v2[2] - u[2] * v2[1], u[2] * v2[0] - u[0] * v2[2], u[0] * v2[1] - u[1] * v2[0])
            mid = tuple(sum(q[i] for q in pts) / 3 - centre[i] for i in range(3))
            if sum(n[i] * mid[i] for i in range(3)) < 0:
                n = tuple(-c for c in n)
            if not any(n):
                continue
            n = normalise(n)
            vn = (n[0], n[1] * cos_t - n[2] * sin_t, n[2] * cos_t + n[1] * sin_t)   # as the camera sees it
            if vn[2] <= 0:
                continue
            shade = 0.2 + 0.8 * max(0.0, sum(vn[i] * light[i] for i in range(3)))
            shade += (hash2(fid, index, seed) - 0.5) * 0.10      # a little grain between neighbouring facets
            screen = [(x, y * cos_t - z * sin_t, z * cos_t + y * sin_t) for x, y, z in pts]
            tris.append((screen, shade, n[1]))

    big = 80
    ox, oy = big / 2, big * 0.75
    cells = {}
    for py in range(big):
        for px in range(big):
            x, y = px + 0.5 - ox, oy - (py + 0.5)
            hit = [(max(q[2] for q in p), shade, up) for p, shade, up in tris if inside(p, x, y)]
            if hit:
                _, shade, up = max(hit)
                cells[(px, py)] = (shade, up)
    if not cells:
        return ['.' * w] * h
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    dx = round(w / 2 - (min(xs) + max(xs) + 1) / 2)
    dy = (GROUND_ROW - 1) - max(ys)          # the lowest body row sits just above the outline row
    grid = [['.'] * w for _ in range(h)]
    placed = {}
    for (px, py), (shade, up) in cells.items():
        qx, qy = px + dx, py + dy
        if not (0 <= qx < w and 0 <= qy < h):
            continue
        # Moss: speckle, in small clumps, on surfaces that face up.
        mossy = up > 0.5 and hash2(qx // 2, qy // 2, first_seed) * 100 < variant['moss'] * (up - 0.3) * 2.2
        grid[qy][qx] = tone(MOSS if mossy else STONE, shade)
        placed[(qx, qy)] = shade

    # Cracks: short runs down and to the right from near the top.
    rng = Lcg(first_seed * 7 + 1)
    top = min(y for _, y in placed)
    for _ in range(variant.get('cracks', 0)):
        cx_, cy_ = int(w / 2 + (rng.next() - 0.5) * 12), top + 2 + int(rng.next() * 5)
        for step in range(3 + int(rng.next() * 3)):
            for q in ((cx_ + step, cy_ + step), (cx_ + step + 1, cy_ + step)):
                if q in placed and grid[q[1]][q[0]] not in ('z', 'A', 'B'):
                    grid[q[1]][q[0]] = CRACK
    for (px, py) in placed:
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                nx, ny = px + ddx, py + ddy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == '.':
                    grid[ny][nx] = OUTLINE
    return [''.join(row) for row in grid]


def inside(p, x, y):
    """Whether the point (x, y) is inside the triangle p, ignoring depth."""
    (x0, y0, _), (x1, y1, _), (x2, y2, _) = p
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return False
    a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
    b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
    return a >= 0 and b >= 0 and 1 - a - b >= 0


def render_crystal(spec, frame):
    w, h = spec['w'], spec['h']
    theta = math.radians(frame * 90 / spec['frames'])
    tilt = math.radians(spec['tilt'])
    light = normalise(spec['light'])
    bob = round(math.sin(2 * math.pi * frame / spec['frames']) * spec['bob'])
    cx, cy = w / 2, h / 2

    def project(p):
        x, y, z = p
        x, z = x * math.cos(theta) + z * math.sin(theta), -x * math.sin(theta) + z * math.cos(theta)  # turn
        y, z = y * math.cos(tilt) - z * math.sin(tilt), z * math.cos(tilt) + y * math.sin(tilt)         # look down
        return (x, y, z)

    top, bottom = (0, spec['half_height'], 0), (0, -spec['half_height'], 0)
    ring = [(spec['radius'] * math.cos(a), 0, spec['radius'] * math.sin(a)) for a in (k * math.pi / 2 for k in range(4))]
    faces = []
    for k in range(4):
        a, b = ring[k], ring[(k + 1) % 4]
        faces.append((top, a, b))
        faces.append((bottom, b, a))

    visible = []
    for tri in faces:
        p = [project(v) for v in tri]
        u = tuple(p[1][i] - p[0][i] for i in range(3))
        v = tuple(p[2][i] - p[0][i] for i in range(3))
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        centre = tuple(sum(q[i] for q in p) / 3 for i in range(3))
        if sum(n[i] * centre[i] for i in range(3)) < 0:
            n = tuple(-c for c in n)        # point it away from the middle
        if n[2] <= 0:
            continue                         # facing away
        n = normalise(n)
        shade = 0.22 + 0.78 * max(0.0, sum(n[i] * light[i] for i in range(3)))
        visible.append((p, shade))

    grid = [['.'] * w for _ in range(h)]
    filled = {}
    for py in range(h):
        for px in range(w):
            x, y = px + 0.5 - cx, -(py + 0.5 - cy - bob)
            hit = [(max(q[2] for q in p), shade) for p, shade in visible if inside(p, x, y)]
            if hit:
                filled[(px, py)] = max(hit)[1]

    for (px, py), shade in filled.items():
        grid[py][px] = LIT if shade > 0.80 else BASE if shade > 0.52 else SHADE if shade > 0.34 else DEEP

    # A glint on the brightest face, up and to the left of its middle, never on the tip.
    if filled:
        brightest = max(filled.values())
        lit = [c for c, s in filled.items() if s == brightest]
        if len(lit) >= 6:
            mx = sum(c[0] for c in lit) / len(lit)
            my = sum(c[1] for c in lit) / len(lit)
            x, y = min(lit, key=lambda c: (c[0] - (mx - 1)) ** 2 + (c[1] - (my - 2)) ** 2)
            grid[y][x] = SPARK
            if (x, y + 1) in filled and filled[(x, y + 1)] == brightest:
                grid[y + 1][x] = SPARK

    for (px, py) in list(filled):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == '.':
                    grid[ny][nx] = OUTLINE
    return [''.join(row) for row in grid]


def sheet_layout(count):
    return min(count, SHEET_COLS), -(-count // SHEET_COLS)


def build_assets(weapons_dir=make_weapons.DEFAULT_DIR):
    crystal = CRYSTAL
    crystal_frames = [render_crystal(crystal, f) for f in range(crystal['frames'])]
    cols, rows = sheet_layout(len(crystal_frames))
    crystal_asset = {
        'id': crystal['id'], 'label': crystal['label'], 'category': 'Markers', 'kind': 'animation', 'place': 'above',
        'w': crystal['w'], 'h': crystal['h'], 'cols': cols, 'rows': rows, 'fps': crystal['fps'],
        # Where the tip hangs: the bottom edge of the lowest pixel, in the frame where it is at rest.
        'anchor': {'x': crystal['w'] // 2, 'y': 1 + max(y for y, row in enumerate(crystal_frames[0]) if row.strip('.'))},
        'frames': crystal_frames,
    }

    rock = ROCK
    rock_frames = [render_rock_variant(rock, v) for v in rock['variants']]
    cols, rows = sheet_layout(len(rock_frames))
    rock_asset = {
        'id': rock['id'], 'label': rock['label'], 'category': 'Nature', 'kind': 'variants', 'place': 'ground',
        'names': [v['name'] for v in rock['variants']],
        'w': rock['w'], 'h': rock['h'], 'cols': cols, 'rows': rows, 'fps': 0,
        # The middle of the base, on the ground row characters stand on.
        'anchor': {'x': rock['w'] // 2, 'y': GROUND_ROW + 1},
        'frames': rock_frames,
    }
    # The facing marker: a flat arrowhead on the ground, NE and SE. NW and SW are those mirrored.
    # Two colourways: yellow for the chosen direction, and pale blue for the others.
    facing_assets = []
    for id_, label, ramp, edge in (('facing', 'Facing marker (yellow)', make_facing.YELLOW, make_facing.EDGE),
                                   ('facing-pale', 'Facing marker (pale blue)', make_facing.PALE, make_facing.PALE_EDGE)):
        facing_assets.append({
            'id': id_, 'label': label, 'category': 'Markers', 'kind': 'variants', 'place': 'ground',
            'names': ['NE', 'SE'],
            'w': make_facing.CELL_W, 'h': make_facing.CELL_H, 'cols': 2, 'rows': 1, 'fps': 0,
            # The arrow's middle on the ground: mirrored left or right, it stays put.
            'anchor': {'x': make_facing.MIDDLE[0], 'y': make_facing.MIDDLE[1]},
            'frames': [make_facing.render_pixels(d, ramp, edge) for d in ('NE', 'SE')],
        })
    # The vine spell: shoots up out of the ground, swells, hangs a frame, and slams back down.
    vine_frames = [make_vine.render_pixels(f) for f in make_vine.FRAMES]
    cols, rows = sheet_layout(len(vine_frames))
    vine_asset = {
        'id': 'vine', 'label': 'Vine spell', 'category': 'Animations', 'kind': 'animation', 'place': 'ground',
        'w': make_vine.CELL_W, 'h': make_vine.CELL_H, 'cols': cols, 'rows': rows, 'fps': 8,
        # The middle of the vine's foot, on the ground.
        'anchor': {'x': make_vine.ANCHOR[0], 'y': make_vine.ANCHOR[1]},
        'frames': vine_frames,
    }
    # Tile overlays: flat animated highlights over a tile's top face; blue is for choosing where to move.
    overlay_assets = []
    for id_, label, colours in make_overlay.COLOURWAYS:
        overlay_assets.append({
            'id': id_, 'label': label, 'category': 'Overlays', 'kind': 'still', 'place': 'ground',
            'opacity': make_overlay.OPACITY,       # see-through: it tones the tile underneath
            'w': make_overlay.CELL_W, 'h': make_overlay.CELL_H, 'cols': 1, 'rows': 1, 'fps': 0,
            # The middle of the diamond, on the ground.
            'anchor': {'x': make_overlay.MIDDLE[0], 'y': make_overlay.MIDDLE[1]},
            'frames': [make_overlay.render_pixels(colours)],
        })
    # The solid overlays, for hovering: they cover the whole top face, in the same three colours.
    for id_, label, colours in make_overlay.SOLID_COLOURWAYS:
        solid_frames = [make_overlay.render_solid(f, colours) for f in range(make_overlay.FRAMES)]
        cols, rows = sheet_layout(len(solid_frames))
        overlay_assets.append({
            'id': id_, 'label': label, 'category': 'Overlays', 'kind': 'animation', 'place': 'ground',
            'w': make_overlay.CELL_W, 'h': make_overlay.CELL_H, 'cols': cols, 'rows': rows, 'fps': 3,
            'anchor': {'x': make_overlay.MIDDLE[0], 'y': make_overlay.MIDDLE[1]},
            'frames': solid_frames,
        })
    # The fire burst: an area spell on five plots (see make_aoe.py), the template for the others.
    fire_frames = [make_fire.render_pixels(f) for f in range(make_fire.FRAMES)]
    cols, rows = sheet_layout(len(fire_frames))
    fire_asset = {
        'id': 'fire-burst', 'label': 'Fire burst spell (five plots)', 'category': 'Animations', 'kind': 'animation', 'place': 'ground',
        'w': make_aoe.CELL_W, 'h': make_aoe.CELL_H, 'cols': cols, 'rows': rows, 'fps': 8,
        # The middle of the middle plot, on the ground.
        'anchor': {'x': make_aoe.MIDDLE[0], 'y': make_aoe.MIDDLE[1]},
        'frames': fire_frames,
    }
    # The dots for the UI: filled for a point left, empty for a point spent. Blue is the movement point; red is its twin.
    dot_assets = [{
        'id': id_, 'label': label, 'category': 'UI', 'kind': 'variants', 'place': 'none',
        'names': ['Filled', 'Empty'],
        'w': make_ui.DOT, 'h': make_ui.DOT, 'cols': 2, 'rows': 1, 'fps': 0,
        'anchor': {'x': make_ui.MIDDLE[0], 'y': make_ui.MIDDLE[1]},
        'frames': [make_ui.render_pixels('filled', colours), make_ui.render_pixels('empty', colours)],
    } for id_, label, colours in make_ui.COLOURWAYS]
    # The dots bursting as a point is spent: full to empty, played once.
    for id_, label, colours in make_ui.COLOURWAYS:
        burst_frames = [make_ui.render_burst(f, colours) for f in range(make_ui.BURST_FRAMES)]
        cols, rows = sheet_layout(len(burst_frames))
        dot_assets.append({
            'id': id_ + '-burst', 'label': label.replace(' (filled and empty)', '') + ' - burst (full to empty)', 'category': 'UI',
            'kind': 'animation', 'place': 'none',
            'w': make_ui.BURST, 'h': make_ui.BURST, 'cols': cols, 'rows': rows, 'fps': 14,
            'anchor': {'x': make_ui.BURST_MIDDLE[0], 'y': make_ui.BURST_MIDDLE[1]},
            'frames': burst_frames,
        })
    # The arrow, two ways to try: one frame flying to the right to rotate and mirror, and two frames
    # already angled the way the game's camera sees a NE and an SE flight.
    arrow_side = {
        'id': 'arrow', 'label': 'Arrow - single frame (rotate and mirror)', 'category': 'Weapons', 'kind': 'still', 'place': 'none',
        'w': make_arrow.CELL_W, 'h': make_arrow.SIDE['h'], 'cols': 1, 'rows': 1, 'fps': 0,
        'anchor': make_arrow.anchor('side'),
        'frames': [make_arrow.render_pixels('side')],
    }
    arrow_angled = {
        'id': 'arrow-iso', 'label': 'Arrow - two frames (NE and SE)', 'category': 'Weapons', 'kind': 'variants', 'place': 'none',
        'names': ['NE', 'SE'],
        'w': make_arrow.CELL_W, 'h': make_arrow.ANGLED['h'], 'cols': 2, 'rows': 1, 'fps': 0,
        'anchor': make_arrow.anchor('NE'),
        'frames': [make_arrow.render_pixels('NE'), make_arrow.render_pixels('SE')],
    }
    # The bow: the slim human's pull-and-release as an animation, and the bow itself as a weapon strip that
    # goes behind it. Built apart, so either can change; they are laid over each other frame by frame.
    bow_assets = []
    for who in ('human', 'slim', 'ninja', 'ranger', 'bones', 'paladin'):                          # every person built from the humanoid model
        creature = getattr(importlib.import_module(f'make_{who}'), 'CREATURE')
        bow = make_bow.build_frames(make_bow.with_bow(creature))
        for facing in ('NE', 'SE'):
            bow_assets.append({
                'id': f'bow-draw-{who}-{facing.lower()}', 'label': f'Bow draw {facing} ({who.capitalize()})', 'category': 'Animations',
                'kind': 'animation', 'place': 'none', 'w': 32, 'h': 32, 'cols': 4, 'rows': 1, 'fps': 4,
                'anchor': {'x': 16, 'y': GROUND_ROW + 1},
                'frames': bow['person'][facing],
            })
        if who == 'slim':       # the bow is drawn once, on the Slim, and shared: builds differ by under a pixel in the hand
            for facing in ('NE', 'SE'):
                bow_assets.append({
                    'id': f'weapon-bow-{facing.lower()}', 'label': f'Bow {facing}', 'category': 'Weapons', 'kind': 'animation',
                    'place': 'none', 'weapon': 'Bow', 'facing': facing, 'animation': 'bow-draw',
                    'w': make_bow.WEAPON_CELL, 'h': make_bow.WEAPON_CELL, 'cols': 4, 'rows': 1, 'fps': 4,
                    'anchor': {'x': make_bow.WEAPON_CELL // 2, 'y': make_bow.WEAPON_CELL},
                    'frames': bow['bow'][facing],
                })
    # The ground tileset is sliced from a PNG rather than rendered.
    # Weapon strips are read from PNGs too, if there are any.
    return [crystal_asset] + facing_assets + overlay_assets + dot_assets + [vine_asset, fire_asset, arrow_side, arrow_angled] + bow_assets + [rock_asset] + make_ground.build_ground_assets() + make_weapons.build_weapon_assets(weapons_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--png-dir', type=Path, help='also write each asset as a PNG sheet here, and check it')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'assets' / 'data.js')
    parser.add_argument('--weapons', type=Path, default=make_weapons.DEFAULT_DIR, help='folder of NAME-attackNE.png / NAME-attackSE.png weapon strips')
    args = parser.parse_args()

    assets = build_assets(args.weapons)
    data = {
        'groups': [{'id': i, 'label': l, 'hue': i not in ('outline', 'neutral')} for i, l in ep.GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ep.ROLES],
        # The order the browse view lists them in: by first appearance.
        'categories': list(dict.fromkeys(a['category'] for a in assets)),
        'assets': assets,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.ASSETS = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(f'wrote {len(assets)} asset(s) -> {args.out}')

    if args.png_dir:
        from PIL import Image
        to_rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
        args.png_dir.mkdir(parents=True, exist_ok=True)
        for asset in assets:
            sheet = Image.new('RGBA', (asset['w'] * asset['cols'], asset['h'] * asset['rows']), (0, 0, 0, 0))
            px = sheet.load()
            origin = lambda f: ((f % asset['cols']) * asset['w'], (f // asset['cols']) * asset['h'])
            for f, rows in enumerate(asset['frames']):
                ox, oy = origin(f)
                for y, row in enumerate(rows):
                    for x, ch in enumerate(row):
                        if ch != '.':
                            px[ox + x, oy + y] = (*to_rgb[ch], 255)
            path = args.png_dir / f'{asset["id"]}.png'
            sheet.save(path)
            # Re-read the PNG and compare every pixel with what the roles say it should be.
            back = Image.open(path).convert('RGBA').load()
            for f, rows in enumerate(asset['frames']):
                ox, oy = origin(f)
                for y, row in enumerate(rows):
                    for x, ch in enumerate(row):
                        want = (0, 0, 0, 0) if ch == '.' else (*to_rgb[ch], 255)
                        if back[ox + x, oy + y] != want:
                            sys.exit(f'{path}: round trip differs at frame {f} ({x}, {y})')
            print(f'{asset["id"]}: {len(asset["frames"])} frames written and re-read identical -> {path}')


if __name__ == '__main__':
    main()
