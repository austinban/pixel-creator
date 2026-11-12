#!/usr/bin/env python3
"""The item pictures again, made another way: each is built as a small 3D model (ellipsoids, rods and blocks), ray-cast with the same renderer the creatures use (creature.py) so it has real form,
light from the upper left and a shadow where one piece lies over another, and then the details (laces, chain links, scales, stitches, runes) are painted over the render in pixels.

The model is made in screen space: `u` to the right, `v` up and `w` towards the viewer, one unit a pixel, the middle of the icon at (0, 0), and the renderer's downward camera tilt is undone, so
each piece faces the viewer as it is drawn and only the light and the depth between pieces are 3D. The 2D versions are in make_item_icons.py; this file has the same 26 ids, so the two can be
compared on a sheet and one chosen. Palette roles only, a one-pixel outline, 32 x 32.

    python3 tools/make_item_icons3d.py --preview previews/item-icons3d.png     all of them, enlarged, with their names
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import creature as cr  # noqa: E402
from creature import deg, mm, mv, part, rz, tr  # noqa: E402
from assetkit import family, write_json  # noqa: E402
from make_amulets import RAMPS as AMULET_RAMPS  # noqa: E402
from make_item_icons import RAMPS, ITEMS as ITEMS_2D  # noqa: E402,F401  (the ramps it adds to the amulets')

CELL = 32
FOLDER = 'item-icons'
CATEGORY = 'Item icons'
B = [[1, 0, 0], [0, math.cos(cr.TILT), -math.sin(cr.TILT)], [0, math.sin(cr.TILT), math.cos(cr.TILT)]]
BT = tr(B)
cr.YAW['icon'] = 0.0
EXTRA = {
    'hole': ('w', 'x', 'x', 'x'),
    'cloud': ('t', 't', 'r', 'q'),
    'wing': ('t', 't', 'r', 'q'),
    'seam': ('p', 'l', 'k', 'w'),
}
RAMPS.update(EXTRA)


# --- building -----------------------------------------------------------------------------
def at(u, v, w=0.0):
    """A point in screen space, as a model point."""
    return mv(BT, (u, v, w))


def E(u, v, w, ru, rv, rw, mat, name, rot=0.0):
    """An ellipsoid facing the viewer, half-sizes ru (across), rv (up), rw (towards the viewer), turned `rot` degrees in the picture."""
    return part(at(u, v, w), (ru, rv, rw), mat, name, mm(BT, rz(deg(rot))))


def Bx(u, v, w, ru, rv, rw, mat, name, rot=0.0):
    """A block, the same way."""
    return part(at(u, v, w), (ru, rv, rw), mat, name, mm(BT, rz(deg(rot))), box=True)


def S(u, v, w, r, mat, name):
    return E(u, v, w, r, r, r, mat, name)


def rod(a, b, r, mat, name, w=0.0, grow=0.0, flat=1.0):
    """A thick line from (u, v) a to b, as an ellipsoid along it."""
    cu, cv = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return E(cu, cv, w, L / 2 + grow, r, r * flat, mat, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def chain(points, r, mat, name, w=0.0):
    """Rods end to end along a bent line."""
    return [rod(a, b, r, mat, f'{name}{i}', w, grow=r * 0.6) for i, (a, b) in enumerate(zip(points, points[1:]))]


def ring(cu, cv, Ru, Rv, r, n, mat, name, w=0.0):
    """A torus facing the viewer, as a ring of spheres (all one piece, so no seams between them)."""
    return [E(cu + Ru * math.cos(2 * math.pi * k / n), cv + Rv * math.sin(2 * math.pi * k / n), w, r, r, r, mat, name) for k in range(n)]


def render(parts, scale=1.0):
    return [list(row) for row in cr.render_frame(parts, [], 'icon', (16, 16), RAMPS, scale)]


# --- painting over the render -------------------------------------------------------------
def pix(u, v):
    return int(math.floor(16 + u)), int(math.floor(16 - v))


def paint(g, pts, role, only_inside=True):
    for u, v in pts:
        x, y = pix(u, v)
        if 0 <= x < CELL and 0 <= y < CELL and (not only_inside or g[y][x] not in '.O'):
            g[y][x] = role


def px_paint(g, pts, role, only_inside=True):
    """Paint at pixel positions, not screen-space ones."""
    for x, y in pts:
        if 0 <= x < CELL and 0 <= y < CELL and (not only_inside or g[y][x] not in '.O'):
            g[y][x] = role


def line_px(g, a, b, role, only_inside=True):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 1
    px_paint(g, [(int(round(a[0] + (b[0] - a[0]) * k / n)), int(round(a[1] + (b[1] - a[1]) * k / n))) for k in range(n + 1)], role, only_inside)


def darker(g, ramp_name, roles=None, every=None):
    """Step each painted pixel (selected by `every(x, y)`) one tone darker in its ramp, for a texture."""
    ramp = RAMPS[ramp_name]
    for y in range(CELL):
        for x in range(CELL):
            c = g[y][x]
            if c in ramp and (every is None or every(x, y)):
                i = ramp.index(c)
                if i + 1 < len(ramp):
                    g[y][x] = ramp[i + 1]


def lighter(g, ramp_name, every=None):
    ramp = RAMPS[ramp_name]
    for y in range(CELL):
        for x in range(CELL):
            c = g[y][x]
            if c in ramp and (every is None or every(x, y)):
                i = ramp.index(c)
                if i > 0:
                    g[y][x] = ramp[i - 1]


def finish(g):
    """Rows of roles, with the outline made good again round anything painted over the render (a spark, a sparkle, a loose cord end)."""
    out = [row[:] for row in g]
    for y in range(CELL):
        for x in range(CELL):
            if g[y][x] in '.O':
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < CELL and 0 <= ny < CELL and g[ny][nx] == '.':
                    out[ny][nx] = 'O'
    return [''.join(r) for r in out]


# --- weapons ------------------------------------------------------------------------------
def recurve_bow():
    top = [(7.5, 13.5), (4.0, 11.5), (0.0, 7.0), (-2.2, 2.0), (-2.6, 0.0)]
    T = lambda p: rotp(p, BOW_TURN)
    parts = chain([T(p) for p in top], 1.35, 'dark_wood', 'limbT') + chain([T((a, -b)) for a, b in reversed(top)], 1.35, 'dark_wood', 'limbB')
    gu, gv = T((-2.6, 0.0))
    lu, lv = T((8.6, 12.4))
    mu, mv_ = T((8.6, -12.4))
    parts += [rod(T((7.5, 13.5)), T((7.5, -13.5)), 0.4, 'cream', 'string', -1.5),
              E(gu, gv, 0.5, 1.7, 3.0, 2.0, 'cord', 'grip', BOW_TURN),
              E(lu, lv, 0.8, 1.2, 2.3, 0.7, 'moss', 'leafT', 25 + BOW_TURN), E(mu, mv_, 0.8, 1.2, 2.3, 0.7, 'moss', 'leafB', -25 + BOW_TURN)]
    return finish(render(parts))


def sling():
    parts = [E(0.5, -0.5, 0, 6.0, 3.8, 2.6, 'leather', 'pouch', 35), S(0.8, -0.3, 1.8, 2.8, 'dull_steel', 'stone'),
             rod((-3.5, -3.5), (-9, -9.5), 0.9, 'leather', 'cordA'), rod((4.2, 3.0), (9.5, 8.5), 0.8, 'leather', 'cordB'),
             S(10.2, 9.2, 0, 1.5, 'leather', 'knot')] + ring(-10.5, -11, 2.4, 2.4, 0.9, 12, 'leather', 'loop')
    g = render(parts)
    px_paint(g, [(14, 14), (15, 13), (11, 9), (9, 8), (8, 11), (22, 20), (24, 21), (25, 18), (21, 23)], 'r', only_inside=False)
    return finish(g)


def rotp(p, angle):
    """A point turned `angle` degrees about the middle of the icon (positive is anticlockwise)."""
    a = math.radians(angle)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


BOW_TURN = -45        # a bow is drawn upright, then turned so its tips lie along the same 45 degree slope as every blade and staff, up to the right


def blade(parts, a, b, half, name, ramp, thin=0.9):
    cu, cv = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    parts.append(Bx(cu, cv, 0, L / 2, half, thin, ramp, name, ang))
    parts.append(E(b[0], b[1], 0, half * 1.35, half * 0.85, thin * 0.8, ramp, name + 'tip', ang))


def worn_sword():
    parts = []
    blade(parts, (-5, -5), (11, 11), 2.2, 'blade', 'dull_steel')
    parts += [Bx(-6.2, -6.2, 0.4, 3.9, 1.2, 1.5, 'rust', 'guard', 135), rod((-6.5, -6.5), (-11.5, -11.5), 1.4, 'cream', 'grip'), S(-12.4, -12.4, 0, 1.9, 'rust', 'pommel')]
    g = render(parts)
    for x, y in ((18, 12), (20, 9), (22, 10)):                                         # notches in the edge
        g[y][x] = '.'
    px_paint(g, [(15, 16), (14, 17), (19, 12), (21, 9), (17, 15), (23, 7), (13, 18)], 'a')
    for k in (0.3, 0.55, 0.8):                                                         # tape wraps
        u, v = -6.5 - 5 * k, -6.5 - 5 * k
        paint(g, [(u, v + 1.2), (u + 1, v + 0.5)], 'e')
    return finish(g)


def worn_dagger():
    parts = []
    blade(parts, (-3, -3), (7, 7), 1.9, 'blade', 'dull_steel')
    parts += [rod((7, 7), (11, 7.4), 1.0, 'dull_steel', 'bent'), Bx(-4, -4, 0.4, 3.3, 1.1, 1.4, 'rust', 'guard', 135),
              rod((-4.5, -4.5), (-9.5, -9.5), 1.4, 'leather', 'grip'), S(-10.4, -10.4, 0, 1.7, 'rust', 'pommel')]
    g = render(parts)
    paint(g, [(-6, -5.4), (-7, -6.4), (-8, -7.4), (-6, -7), (-8, -9)], 't')
    px_paint(g, [(7, 24), (6, 27)], 'C', only_inside=False)
    px_paint(g, [(14, 18), (12, 20)], 'a')
    return finish(g)


def worn_bow():
    arc = [(5.5, 13), (0.5, 9.5), (-2.0, 4.0), (-2.5, -1.0), (-1.0, -7.5), (2.5, -11.5), (6.0, -13.0)]
    T = lambda p: rotp(p, BOW_TURN)
    gu, gv = T((-2.3, 0.5))
    parts = chain([T(p) for p in arc], 1.45, 'wood', 'limb') + [rod(T((6.5, 13)), T((6.5, -13)), 0.4, 'cream', 'string', -1.5), E(gu, gv, 0.5, 1.7, 2.6, 2.0, 'cord', 'grip', BOW_TURN)]
    g = render(parts)
    cu, cv = T((-0.5, 8.5))
    line_px(g, (int(16 + cu), int(16 - cv) - 1), (int(16 + cu) + 2, int(16 - cv) + 2), 'x')       # a crack along the upper limb
    px_paint(g, [(int(16 + cu), int(16 - cv))], 'g')
    for v in (-6.5, -8.5, -10.5):                                                              # twine across the mended limb
        a, b = T((-3.0, v)), T((2.4, v))
        line_px(g, (int(16 + a[0]), int(16 - a[1])), (int(16 + b[0]), int(16 - b[1])), 't')
    return finish(g)


def oak_staff():
    parts = [rod((-10.5, -11), (10, 9), 1.7, 'wood', 'shaft'), S(-3, -3.5, 1.6, 1.9, 'wood', 'knot1'), S(3.6, 2, 1.4, 1.7, 'wood', 'knot2'),
             S(-8, -8, 1.2, 1.5, 'wood', 'knot3'), E(11.4, 11, 0.6, 2.3, 3.4, 1.6, 'moss', 'bud', 20), E(8.4, 12.6, 0.4, 1.5, 2.5, 1.2, 'moss', 'bud2', -35)]
    g = render(parts)
    paint(g, [(-1, -1.5), (0, -0.5), (0.5, -1.5), (1, 0), (-1.5, -2.5)], 'z')
    paint(g, [(0, -1), (1.5, 0)], 'A')
    return finish(g)


def warding_staff():
    parts = [rod((-10.5, -11), (5, 4.5), 1.6, 'pale_wood', 'shaft')] + ring(8.5, 8.5, 4.4, 4.4, 0.95, 18, 'silver', 'hoop') + \
            [E(8.5, 8.5, 0.5, 2.7, 3.2, 1.0, 'glow', 'shield')]
    g = render(parts)
    paint(g, [(7.5, 10), (8, 11)], 't')
    return finish(g)


def storm_staff():
    parts = [rod((-11, -11.5), (4.5, 4), 1.6, 'dark_iron', 'shaft'), E(-6.5, -7, 1.5, 1.4, 1.9, 1.0, 'steel', 'band1', 45), E(-1.5, -2, 1.5, 1.4, 1.9, 1.0, 'steel', 'band2', 45),
             rod((4.5, 4), (3.5, 11.5), 1.1, 'iron', 'prongA'), rod((4.5, 4), (12.5, 5.5), 1.1, 'iron', 'prongB'), S(8.2, 8.2, 1.4, 3.1, 'glow', 'spark'), S(8.2, 8.2, 3.0, 1.6, 'cream', 'core')]
    g = render(parts)
    line_px(g, (22, 4), (24, 6), 't', False)
    line_px(g, (27, 8), (25, 9), 'o', False)
    line_px(g, (21, 13), (23, 11), 'o', False)
    line_px(g, (18, 6), (20, 8), 'o', False)
    return finish(g)


# --- armour -------------------------------------------------------------------------------
def tunic(mat, hem, sleeves=True, collar=True):
    parts = [E(0, -2, 0, 7.2, 8.8, 4.2, mat, 'body'), E(0, 7.0, 0, 8.8, 3.4, 3.8, mat, 'shoulders'), E(0, -10.0, 0.4, 8.0, 2.4, 4.4, hem, 'hem'), E(0, 10.2, 1.4, 2.9, 1.3, 2.4, 'hole', 'neck')]
    if sleeves:
        parts += [E(9.8, 5.0, 0, 3.8, 4.9, 3.3, mat, 'sleeveR', -14), E(-9.8, 5.0, 0, 3.8, 4.9, 3.3, mat, 'sleeveL', 14)]
    return parts


def leather_jerkin():
    parts = [E(0, -1.5, 0, 7.8, 9.8, 4.4, 'leather', 'body'), E(-6.2, 8.0, 0.6, 3.0, 3.6, 2.8, 'leather', 'strapL', 12), E(6.2, 8.0, 0.6, 3.0, 3.6, 2.8, 'leather', 'strapR', -12),
             E(0, -10.6, 0.5, 8.6, 2.2, 4.6, 'rust', 'hem'), E(0, 9.6, 1.6, 3.4, 2.0, 2.4, 'hole', 'neck'), E(-9.4, 3.0, -0.6, 2.6, 6.0, 2.4, 'rust', 'sideL', 6), E(9.4, 3.0, -0.6, 2.6, 6.0, 2.4, 'rust', 'sideR', -6)]
    g = render(parts)
    for k, v in enumerate(range(8, -9, -3)):                                              # laces criss-crossing down the front
        paint(g, [(-1.4, v), (-0.5, v - 0.6), (0.5, v - 1.4), (1.4, v - 2)], 't')
        paint(g, [(1.4, v), (0.5, v - 0.6), (-0.5, v - 1.4), (-1.4, v - 2)], 't')
    paint(g, [(0, v) for v in range(8, -11)], 'e')
    for u in range(-6, -1):                                                                # a patched shoulder
        for v in (6, 7, 8):
            paint(g, [(u - 1.5, v + 1)], 'c' if (u + v) % 2 else 'b')
    paint(g, [(-7.5, 9), (-3.5, 9), (-7.5, 6), (-3.5, 6)], 'e')
    return finish(g)


def iron_mail():
    g = render(tunic('steel', 'dark_iron'))
    darker(g, 'steel', every=lambda x, y: (x + 2 * (y % 2)) % 4 == 0)                    # links
    lighter(g, 'steel', every=lambda x, y: (x + 2 * (y % 2)) % 4 == 2 and y % 3 == 0)
    paint(g, [(-6.5, 3), (-6.5, 2)], 't')                                                  # one bright rivet
    return finish(g)


def warden_plate():
    parts = [E(0, -1, 0, 9.4, 11, 4.6, 'stone', 'breast'), E(-9.4, 7.8, 0.8, 4.0, 3.2, 3.4, 'stone', 'padL', 20), E(9.4, 7.8, 0.8, 4.0, 3.2, 3.4, 'stone', 'padR', -20),
             Bx(0, 1.6, 1.8, 10.6, 1.0, 1.6, 'dark_iron', 'strap1'), Bx(0, -5.4, 1.8, 9.6, 1.0, 1.6, 'dark_iron', 'strap2'),
             E(0, 10.4, 1.4, 2.8, 1.2, 2.2, 'hole', 'neck')]
    g = render(parts)
    paint(g, [(0, v) for v in range(4, 10)], 'k')
    for u, v in ((-9, 2), (9, 2), (-8, -5), (8, -5)):
        paint(g, [(u, v)], 't')
    paint(g, [(-8, 9), (-7, 9), (-7, 8), (7, 10), (8, 9)], 'A')
    paint(g, [(-6, 7), (-5, 8), (9.5, 8)], 'z')
    paint(g, [(0, v) for v in range(-8, -2)] + [(-2, -5), (2, -5), (-1, -4), (1, -6)], 'z')
    paint(g, [(0, -7), (0, -3)], 'r')
    return finish(g)


def dragonscale_mail():
    parts = tunic('teal', 'dark_iron')
    for k, (u, v) in enumerate(((-5.4, 11.4), (-2.8, 12.4), (0, 12.8), (2.8, 12.4), (5.4, 11.4))):          # a collar of spikes
        parts.append(E(u, v, 1.0, 0.8, 2.4, 0.8, 'cream', f'spike{k}', -u * 4))
    g = render(parts)
    for y in range(CELL):
        for x in range(CELL):
            c = g[y][x]
            if c in 'rqsD':
                off = (y // 3 % 2) * 2
                sx, sy, idx = (x + off) % 4, y % 3, (x + off) // 4 + 5 * (y // 3)
                ember = (idx * 7 + y // 3) % 9 == 0
                ramp = RAMPS['teal']
                i = ramp.index(c)
                if ember:
                    g[y][x] = 'b' if sy == 0 else 'e' if sy == 2 else 'a'
                elif sy == 2 or (sy == 1 and sx == 0):
                    g[y][x] = ramp[min(3, i + 1)]
                elif sy == 0 and sx in (1, 2):
                    g[y][x] = ramp[max(0, i - 1)]
    px_paint(g, [(5, 3), (6, 2), (5, 1), (7, 1)], 't', only_inside=False)                   # steam off the shoulder
    return finish(g)


# --- trinkets -----------------------------------------------------------------------------
def boot(cx, mat, cuff, tag):
    return [E(cx - 0.8, 2.6, 0, 3.4, 7.2, 3.2, mat, 'shaft' + tag), E(cx - 0.8, 9.9, 0.3, 4.2, 1.7, 3.8, cuff, 'cuff' + tag), E(cx + 2.2, -6.6, 0.4, 6.4, 3.2, 3.2, mat, 'foot' + tag),
            E(cx + 7.2, -7.2, 0.5, 2.7, 2.4, 2.8, 'dull_steel', 'toe' + tag), E(cx - 2.4, -8.0, 0.4, 2.0, 2.2, 3.0, 'dark_iron', 'heel' + tag), E(cx + 2.4, -9.8, 0.2, 7.8, 1.2, 3.4, 'dark_iron', 'sole' + tag)]


def swift_boots():
    parts = boot(-7, 'teal', 'teal', 'a') + boot(5, 'teal', 'teal', 'b')
    for cx, tag in ((-7, 'a'), (5, 'b')):                                                 # a tiny wing at each ankle
        parts += [E(cx - 4.2, 4.0, 1.2, 1.4, 2.0, 0.8, 'wing', 'wb' + tag, 20)]
        for k, ang in enumerate((150, 165, 180)):
            a = math.radians(ang)
            parts.append(rod((cx - 4.4, 4.2 - k * 0.6), (cx - 4.4 + 7.2 * math.cos(a), 4.2 - k * 0.6 + 7.2 * math.sin(a) + 1), 0.95, 'wing', f'f{k}{tag}', 1.2))
    g = render(parts)
    for cx in (-7, 5):
        paint(g, [(cx - 0.8, v) for v in (6, 3, 0)], 't')                                    # laces
        paint(g, [(cx + 6.2, -6.4), (cx + 7.0, -6.0)], 't')
    return finish(g)


def windrunner_boots():
    parts = boot(-7, 'pale', 'pale', 'a') + boot(5, 'pale', 'pale', 'b')
    for cx, tag in ((-7, 'a'), (5, 'b')):                                                 # clouds at the heels
        parts += [S(cx - 4.4, -10.0, 1.0, 2.6, 'cloud', 'c1' + tag), S(cx - 7.2, -9.4, 0.4, 2.0, 'cloud', 'c2' + tag), S(cx - 2.2, -11.4, 1.6, 1.9, 'cloud', 'c3' + tag)]
    g = render(parts)
    for cx in (-7, 5):                                                                    # a spiral of wind round each shaft
        for k in range(12):
            t = k / 11
            u, v = cx - 0.8 - 3.2 + 6.4 * t, 9 - 13 * t + 1.6 * math.sin(t * 9)
            paint(g, [(u, v)], 'o')
            paint(g, [(u + 1, v - 1)], 'n')
    return finish(g)


def warding_charm():
    parts = chain([(-9, 15), (-4, 10.5), (0, 8.5)], 0.7, 'cord', 'chainL') + chain([(9, 15), (4, 10.5), (0, 8.5)], 0.7, 'cord', 'chainR') + [S(0, 8.2, 0.6, 1.6, 'cord', 'bail')]
    parts += [Bx(0, 2.4, 0, 7.4, 4.2, 2.6, 'steel', 'top'), Bx(0, -2.4, 0, 5.2, 5.2, 2.6, 'steel', 'tip', 45),
              Bx(0, 2.4, 1.6, 5.2, 2.8, 1.4, 'glow', 'glowtop'), Bx(0, -1.8, 1.6, 3.6, 3.6, 1.4, 'glow', 'glowtip', 45)]
    g = render(parts)
    paint(g, [(-3, 4), (-2, 4)], 't')
    return finish(g)


def vigor_ring():
    parts = ring(0, -4.4, 7.4, 7.0, 1.9, 28, 'gold', 'band') + [E(0, 5.6, 0.6, 5.4, 2.3, 3.0, 'gold', 'setting'),
                                                                E(-2.1, 9.4, 1.4, 3.1, 3.2, 2.3, 'ruby', 'lobeL'), E(2.1, 9.4, 1.4, 3.1, 3.2, 2.3, 'ruby', 'lobeR'), E(0, 7.0, 1.4, 3.6, 3.2, 2.3, 'ruby', 'point', 45)]
    g = render(parts)
    paint(g, [(-3, 11), (-2, 11.5)], 't')
    return finish(g)


def strength_band():
    parts = ring(0, 0, 10.8, 8.4, 2.6, 34, 'leather', 'band', 0) + [Bx(0, 8.4, 2.6, 6.6, 3.0, 1.0, 'steel', 'plate')] + [S(u, 8.4, 3.6, 0.9, 'steel', f'stud{u}') for u in (-4, 0, 4)]
    g = render(parts)
    for u in range(-9, 10, 2):                                                            # orange stitching along both edges of the band
        paint(g, [(u, 8.4 - 4.2 * (abs(u) / 10) ** 2 - 4.0)], 'b')
        paint(g, [(u, -8.0 + 3.6 * (abs(u) / 10) ** 2)], 'b')
    return finish(g)


def sage_amulet():
    parts = chain([(-11, 15), (-5, 11), (0, 9.6)], 0.7, 'gold', 'chainL') + chain([(11, 15), (5, 11), (0, 9.6)], 0.7, 'gold', 'chainR') + [S(0, 9.2, 0.6, 1.6, 'gold', 'bail')]
    parts += ring(0, -3.4, 8.8, 8.8, 1.1, 32, 'gold', 'setting', 1.4) + [S(0, -3.4, 0, 8.4, 'violet', 'orb')]
    g = render(parts)
    eye = [(u, 0.0) for u in range(-7, 8)]
    for u in range(-7, 8):                                                                # a half-open eye
        top = 3.4 * (1 - (u / 7.0) ** 2) ** 0.5
        for v in range(int(-3.2 * (1 - (u / 7.0) ** 2) ** 0.5) - 1, int(top) + 1):
            paint(g, [(u, v - 3.4)], 'x' if v > 1 else 't', only_inside=True)
    paint(g, [(u, v - 3.4) for u in (-1, 0, 1) for v in (-3, -2, -1)], 'v')
    paint(g, [(0, -4.6), (0, -5.4)], 'x')
    return finish(g)


def giants_belt():
    parts = [Bx(0, 0, 0, 15.8, 4.6, 2.2, 'leather', 'belt')] + [S(u, 0, 2.6, 0.7, 'rust', f'hole{u}') for u in (-13, -9, 9, 13)]
    parts += [E(0, 0, 2.6, 8.6, 10.6, 4.8, 'stone', 'boulder'), E(-3, 3.6, 5.6, 3.4, 3.4, 2.0, 'stone', 'facet1'), E(3.6, -3, 5.8, 3.0, 3.4, 1.8, 'stone', 'facet2'), Bx(0.4, -3, 7.2, 1.0, 9.0, 0.8, 'steel', 'prong')]
    g = render(parts)
    paint(g, [(-3.5, 6), (-2.5, 7), (-4, 5)], 'r')
    paint(g, [(4, 5), (5, 3), (3, 7)], 'A')
    return finish(g)


def hawkeye_pendant():
    parts = chain([(-11, 15), (-5, 11), (0, 9.4)], 0.7, 'gold', 'chainL') + chain([(11, 15), (5, 11), (0, 9.4)], 0.7, 'gold', 'chainR') + [S(0, 9.0, 0.6, 1.6, 'gold', 'bail')]
    parts += [E(0, 1.4, 0, 11.4, 6.4, 2.8, 'gold', 'eye'), E(0, 1.4, 1.8, 8.6, 4.4, 1.4, 'cream', 'white'), S(0, 1.4, 2.8, 3.1, 'topaz', 'iris'), S(0, 1.4, 4.2, 1.4, 'hole', 'pupil'),
              rod((0.5, -5.6), (1.8, -14.5), 1.5, 'rust', 'feather', 0.4)]
    g = render(parts)
    paint(g, [(-1, 2.5)], 't')
    line_px(g, (16, 21), (17, 29), 'd')
    px_paint(g, [(14, 24), (14, 26), (19, 24), (19, 27)], 'a')
    return finish(g)


def guardian_sigil():
    parts = [E(0, 0, 0, 13.4, 13.4, 3.0, 'bronze', 'plaque')] + ring(0, 0, 12.0, 12.0, 1.1, 40, 'bronze', 'rim', 1.6)
    parts += [Bx(0, 1.8, 2.0, 5.6, 3.6, 1.4, 'bronze', 'shieldtop'), Bx(0, -2.6, 2.0, 4.0, 4.0, 1.4, 'bronze', 'shieldtip', 45), S(0, 8.6, 2.2, 1.9, 'gold', 'sun')]
    g = render(parts)
    line_px(g, (16, 16), (16, 25), 'a', True)
    line_px(g, (11, 17), (21, 17), 'a', True)
    for k in range(8):
        a = k * math.pi / 4
        paint(g, [(3.7 * math.cos(a), 8.6 + 3.7 * math.sin(a))], 'd')
    return finish(g)


def sage_circlet():
    parts = ring(0, -6.6, 11.8, 5.0, 1.15, 40, 'silver', 'band', 0) + [E(0, -1.6, 1.0, 2.0, 2.4, 1.2, 'silver', 'front', 45),
                                                                       E(0, 8.4, 0.6, 3.8, 5.8, 3.0, 'violet', 'gem', 0), E(0, 8.4, 1.6, 1.8, 3.4, 1.6, 'violet', 'facet')]
    g = render(parts)
    paint(g, [(-1, 10), (-1, 11)], 't')
    px_paint(g, [(5, 8), (6, 7), (6, 9), (7, 8), (27, 11), (26, 10), (26, 12), (25, 11)], 'v', only_inside=False)
    return finish(g)


def summit_crown():
    peaks = [(-11.5, -1.0, 6.0), (-6, 2.0, 8.4), (0, 5.5, 10.4), (6, 2.0, 8.4), (11.5, -1.0, 6.0)]
    parts = [E(0, -8.4, 0, 13.4, 3.8, 4.6, 'gold', 'band')]
    for k, (u, v, h) in enumerate(peaks):
        parts.append(E(u, v, 0.4 + 0.2 * (k % 2), 3.2, h, 2.8, 'steel', f'peak{k}', 0))
        parts.append(E(u, v + h - 3.0, 1.0, 2.2, 2.6, 2.0, 'pale', f'snow{k}'))
    parts.append(S(0, -8.4, 4.0, 2.6, 'sapphire', 'gem'))
    g = render(parts)
    paint(g, [(-1, -7), (-1, -6)], 't')
    return finish(g)


def phoenix_heart():
    parts = [S(-4.2, 3.4, 0, 5.6, 'ember', 'lobeL'), S(4.2, 3.4, 0, 5.6, 'ember', 'lobeR'), Bx(0, -1.2, 0, 6.9, 6.9, 4.0, 'ember', 'point', 45),
             S(-3.2, 3.8, 2.6, 3.4, 'flame', 'glowL'), S(3.2, 3.8, 2.6, 3.4, 'flame', 'glowR'), Bx(0, -0.6, 2.6, 4.4, 4.4, 2.0, 'flame', 'glowM', 45), S(0, 1.4, 4.0, 2.0, 'cream', 'core')]
    for k, u in enumerate((-9.6, -5, 0, 5, 9.6)):                                         # a small cage of gold flame round it
        parts.append(rod((u * 1.0, 10.5 - abs(u) * 0.45), (u * 0.62, -10.6 + abs(u) * 0.35), 0.7, 'gold', f'bar{k}', 4.6))
    parts.append(E(0, 11.2, 3.0, 9.0, 1.1, 2.4, 'gold', 'cap'))
    for k, (a, b) in enumerate((((7, 9), (10, 12.5)), ((10, 12.5), (12.5, 15)), ((12.5, 15), (11, 12.5)))):
        parts.append(rod(a, b, 1.5 - 0.35 * k, 'flame', f'feather{k}', 1.0))
    return finish(render(parts))


def stormcaller_band():
    parts = ring(0, -5.6, 9.8, 8.0, 2.0, 32, 'dark_iron', 'band') + [E(0, 7.0, 0.6, 7.6, 7.2, 3.0, 'dark_iron', 'setting'), S(0, 7.0, 2.2, 5.6, 'sapphire', 'gem'),
                                                                        E(-1.6, 7.2, 4.6, 3.6, 2.0, 1.4, 'steel', 'cloud1'), E(1.8, 8.4, 4.6, 2.8, 1.8, 1.4, 'steel', 'cloud2')]
    g = render(parts)
    line_px(g, (15, 7), (14, 9), 'd')
    line_px(g, (14, 9), (16, 9), 'd')
    line_px(g, (16, 9), (15, 11), 'd')
    paint(g, [(-3.5, 10.4)], 't')
    return finish(g)


def stone_idol():
    parts = [E(0, -1.0, 0, 9.4, 12.6, 6.0, 'stone', 'body'), Bx(0, -12.4, 0.4, 10.2, 2.0, 5.6, 'iron', 'base'),
             Bx(-4.6, 4.6, 5.4, 4.0, 0.8, 1.0, 'dark_iron', 'browL', -16), Bx(4.6, 4.6, 5.4, 4.0, 0.8, 1.0, 'dark_iron', 'browR', 16),
             Bx(-3.4, 2.0, 5.4, 1.7, 1.5, 0.8, 'flame', 'eyeL'), Bx(3.4, 2.0, 5.4, 1.7, 1.5, 0.8, 'flame', 'eyeR'),
             E(0, 11.2, 1.0, 5.4, 2.2, 3.4, 'moss', 'mossTop'), E(-8.2, 6.0, 2.0, 2.2, 2.0, 2.0, 'moss', 'mossL')]
    g = render(parts)
    paint(g, [(-3.4, 2.6), (3.4, 2.6)], 't')
    line_px(g, (13, 23), (15, 21), 'x')
    line_px(g, (15, 21), (18, 21), 'x')
    line_px(g, (18, 21), (20, 23), 'x')
    return finish(g)


ITEMS = [
    ('recurve_bow', 'Recurve Bow', recurve_bow), ('sling', 'Sling', sling), ('worn_sword', 'Worn Sword', worn_sword), ('worn_dagger', 'Worn Dagger', worn_dagger),
    ('worn_bow', 'Worn Bow', worn_bow), ('oak_staff', 'Oak Staff', oak_staff), ('warding_staff', 'Warding Staff', warding_staff), ('storm_staff', 'Storm Staff', storm_staff),
    ('leather_jerkin', 'Leather Jerkin', leather_jerkin), ('iron_mail', 'Iron Mail', iron_mail), ('warden_plate', "Warden's Plate", warden_plate), ('dragonscale_mail', 'Dragonscale Mail', dragonscale_mail),
    ('swift_boots', 'Swift Boots', swift_boots), ('windrunner_boots', 'Windrunner Boots', windrunner_boots), ('warding_charm', 'Warding Charm', warding_charm), ('vigor_ring', 'Ring of Vigor', vigor_ring),
    ('strength_band', 'Strength Band', strength_band), ('sage_amulet', 'Sage Amulet', sage_amulet), ('giants_belt', "Giant's Belt", giants_belt), ('hawkeye_pendant', 'Hawkeye Pendant', hawkeye_pendant),
    ('guardian_sigil', 'Guardian Sigil', guardian_sigil), ('sage_circlet', "Sage's Circlet", sage_circlet), ('summit_crown', 'Crown of the Summit', summit_crown), ('phoenix_heart', 'Phoenix Heart', phoenix_heart),
    ('stormcaller_band', 'Stormcaller Band', stormcaller_band), ('stone_idol', 'Stone Idol', stone_idol),
]


def build_assets():
    """One 32 x 32 still per item, `item-ID`, in category Item icons, anchored at the middle; nothing is placed on the map."""
    make = family(CATEGORY, CELL, CELL, (CELL // 2, CELL // 2), place='none', folder=FOLDER)
    return [make('item-' + id, label, 'still', [icon()]) for id, label, icon in ITEMS]


def write_package(folder):
    """Beside the sheets: item-icons.json, which file is which item and what the game calls it."""
    write_json(folder, 'item-icons.json', 'The item pictures in this folder, named as the game names them. See README.md beside this file.',
               {'cell': [CELL, CELL], 'items': {id: {'label': label, 'file': f'item-{id}.png', 'game_file': f'{id}.png'} for id, label, _ in ITEMS}})


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    cols = 7
    cw, ch = CELL * scale + 12, CELL * scale + 24
    n = len(ITEMS)
    sheet = Image.new('RGBA', (cols * cw + 12, ((n + cols - 1) // cols) * ch + 12), (44, 40, 76, 255))
    d = ImageDraw.Draw(sheet)
    for k, (id, label, make_icon) in enumerate(ITEMS):
        cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        for y, line in enumerate(make_icon()):
            for x, c in enumerate(line):
                if c != '.':
                    cell.putpixel((x, y), rgb[c] + (255,))
        ox, oy = 12 + (k % cols) * cw, 12 + (k // cols) * ch
        sheet.alpha_composite(cell.resize((CELL * scale, CELL * scale), Image.NEAREST), (ox, oy + 14))
        d.text((ox, oy), label, fill=(235, 238, 245, 255))
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path, help='every item, enlarged, with its name')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the 3D item icons, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
