#!/usr/bin/env python3
"""The flat (2D) version of the item pictures: 26 icons, 32 x 32, one per item that had no picture of its own (see the game's docs/pixel-creator-requests.md, section 5).

They are drawn the way the amulets and the equipment slot icons are (see make_amulets.py and make_slot_icons.py): a stack of shapes, each shaded from the light in the upper left in the shared
palette roles, with a one-pixel outline. Weapons lie on the diagonal with the point at the upper right, as the weapon icons do; armour and trinkets sit in the middle of the cell.

    weapons    recurve_bow  sling  worn_sword  worn_dagger  worn_bow  oak_staff  warding_staff  storm_staff
    armour     leather_jerkin  iron_mail  warden_plate  dragonscale_mail
    trinkets   swift_boots  windrunner_boots  warding_charm  vigor_ring  strength_band  sage_amulet  giants_belt  hawkeye_pendant  guardian_sigil
               sage_circlet  summit_crown  phoenix_heart  stormcaller_band  stone_idol

The ids are the game's (`<id>.png` in `assets/sprites/items/`), and each has the picture idea the game asked for. The palette has no true brown, so wood and leather are its orange, plum and grape.

The family that ships is the 3D version, make_item_icons3d.py, which has the same ids; this one is kept for comparison (and its ramps are shared).

    python3 tools/make_item_icons.py --preview previews/item-icons.png     all of them, enlarged, with their names
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import family, write_json  # noqa: E402
from make_amulets import CELL, RAMPS, Icon, diamond, disc, ellipse, heart, minus, poly, rect, ring, union  # noqa: E402
from make_slot_icons import bar  # noqa: E402

FOLDER = 'item-icons'
CATEGORY = 'Item icons'

RAMPS.update({
    'wood': ('b', 'a', 'g', 'w'),             # a warm wood: amber, orange, plum, grape
    'dark_wood': ('a', 'g', 'w', 'x'),
    'pale_wood': ('t', 'C', 'c', 'e'),
    'leather': ('c', 'a', 'e', 'g'),          # salmon, orange, coral, plum
    'rust': ('b', 'a', 'e', 'g'),
    'dull_steel': ('q', 'p', 'l', 'k'),
    'iron': ('p', 'l', 'k', 'w'),
    'dark_iron': ('l', 'k', 'w', 'x'),
    'pale': ('t', 't', 'r', 'q'),
    'teal': ('r', 'q', 's', 'D'),
    'violet': ('t', 'v', 'u', 'w'),
    'glow': ('t', 'r', 'o', 'n'),
    'flame': ('t', 'd', 'b', 'a'),
    'bronze': ('d', 'b', 'a', 'g'),
    'cream': ('t', 't', 'C', 'c'),
    'moss': ('z', 'A', 'B', 's'),
    'ember': ('d', 'b', 'a', 'e'),
})


class Pic(Icon):
    def cut(self, *pts):
        for x, y in pts:
            self.grid[y][x] = '.'
            self.solid.discard((x, y))

    def dots(self, pts, role):
        for x, y in pts:
            if 0 <= x < CELL and 0 <= y < CELL:
                self.dot(x, y, role)

    def stroke(self, pts, w, ramp, **kw):
        """A thick line through a list of points, each piece a bar."""
        for a, b in zip(pts, pts[1:]):
            self.layer(bar(a, b, w, w), ramp, **kw)

    def line(self, a, b, role):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 1
        for k in range(n + 1):
            t = k / n
            self.dot(int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t)), role)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# --- weapons ------------------------------------------------------------------------------
def recurve_bow():
    i = Pic()
    i.line((23, 3), (23, 28), 't')                                                   # a pale string
    top = [(24.5, 2.5), (21.5, 4.0), (18.5, 7.5), (16.5, 12.5), (16.0, 16.0)]
    i.stroke(top, 3.0, 'dark_wood', centre=(17, 15), radius=14)                      # the limbs, their tips curling back on themselves
    i.stroke([(p[0], 32 - p[1]) for p in reversed(top)], 3.0, 'dark_wood', centre=(17, 17), radius=14)
    i.layer(ellipse(23.4, 5.6, 1.6, 2.4), 'moss')                                    # a leaf tied at each tip
    i.layer(ellipse(23.4, 26.4, 1.6, 2.4), 'moss')
    i.layer(rect(15, 14, 18, 18), 'cord', flat=1)                                    # a wrapped grip
    return i.outline()


def sling():
    i = Pic()
    i.stroke([(15, 18), (9, 25), (6, 27)], 1.7, 'leather', centre=(10, 24), radius=8)       # the cord to the finger loop
    i.layer(ring(6, 27, 1.7, 3.2), 'leather')                                              # the finger loop
    i.stroke([(19, 14), (24, 9), (27, 6)], 1.5, 'leather', centre=(23, 10), radius=8)      # the cord with the knot
    i.layer(disc(27, 5.6, 1.7), 'leather')
    i.layer(ellipse(17.2, 17.4, 5.6, 4.2), 'leather', centre=(17, 17), radius=6)             # the pouch
    i.layer(disc(17.2, 17.0, 3.2), 'dull_steel')                                           # a round stone in it
    i.dot(16, 15, 'r')
    for x, y in ((24, 19), (26, 21), (27, 24), (11, 11), (9, 9), (13, 8)):                  # a faint swirl behind it
        i.dot(x, y, 'r')
    return i.outline()


def sword_parts(i, base, tip, width, grip_end, notches=(), rust=(), blade_ramp='dull_steel'):
    i.layer(bar(base, tip, width, 1.4), blade_ramp, centre=lerp(base, tip, 0.5), radius=12)
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    gx, gy = -uy, ux
    guard_a = (base[0] + gx * 4.4, base[1] + gy * 4.4)
    guard_b = (base[0] - gx * 4.4, base[1] - gy * 4.4)
    i.layer(bar(guard_a, guard_b, 2.2, 2.2), 'rust')                                       # a rusted crossguard
    i.layer(bar(base, grip_end, 2.6, 2.6), 'cream', centre=lerp(base, grip_end, 0.5), radius=6, flat=None)
    for k in (0.25, 0.5, 0.75):                                                            # tape wraps
        p = lerp(base, grip_end, k)
        i.dots([(int(p[0]), int(p[1])), (int(p[0]) + 1, int(p[1]))], 'e')
    i.layer(disc(grip_end[0], grip_end[1], 1.9), 'rust')
    i.cut(*notches)
    i.dots(rust, 'a')


def worn_sword():
    i = Pic()
    sword_parts(i, (10.5, 21.5), (25.5, 6.5), 5.2, (6, 26), notches=((17, 15), (20, 11), (22, 12)), rust=((14, 17), (15, 18), (19, 13), (21, 10), (17, 16), (23, 8)))
    return i.outline()


def worn_dagger():
    i = Pic()
    i.layer(bar((11, 20), (21, 11), 4.0, 1.6), 'dull_steel', centre=(16, 16), radius=9)       # a short blade...
    i.layer(bar((21, 11), (25, 11.5), 1.7, 1.0), 'dull_steel', flat=2)                        # ...with its tip bent over
    i.layer(bar((9, 18), (14, 23), 2.0, 2.0), 'rust')
    i.layer(bar((11, 21), (6, 26), 2.4, 2.4), 'leather', centre=(8, 24), radius=5)
    for p in ((9, 23), (8, 24), (7, 25)):                                                      # a frayed cord wrap, with loose ends
        i.dot(*p, 't')
    i.dots([(5, 24), (4, 27)], 'C')
    i.layer(disc(5.6, 26.4, 1.6), 'rust')
    i.cut((18, 14), (16, 16))
    i.dots([(14, 18), (19, 13)], 'a')
    return i.outline()


def worn_bow():
    i = Pic()
    i.line((21, 4), (21, 28), 'C')                                                             # a frayed string
    arc = [(20, 3.5), (15.5, 6.5), (13.5, 12), (13.5, 20), (15.5, 25.5), (20, 28.5)]
    i.stroke(arc, 3.2, 'wood', centre=(14, 16), radius=14)                                     # a plain shortbow
    i.layer(rect(12, 15, 15.5, 18), 'cord', flat=1)
    i.line((14, 7), (14, 11), 'x')                                                              # a crack along the upper limb
    i.dots([(13, 9), (15, 9)], 'g')
    for y in (21, 23, 25):                                                                     # the lower limb mended with twine: bands across it
        i.layer(rect(11.6, y, 16.8, y + 1.1), 'cream', flat=1)
        i.dot(12, y + 1, 'c')
    return i.outline()


def oak_staff():
    i = Pic()
    i.stroke([(6, 27), (12, 20), (18, 14), (24, 8)], 3.0, 'wood', centre=(15, 17), radius=14)   # a knotted branch
    for cx, cy, r in ((11, 21, 2.2), (18, 14.5, 2.0), (8, 25, 1.7)):
        i.layer(disc(cx, cy, r), 'wood')                                                       # knots
        i.dot(int(cx), int(cy), 'g')
    i.layer(ellipse(26, 6.4, 2.2, 3.4), 'moss')                                                # a green bud
    i.layer(ellipse(23.5, 4.4, 1.5, 2.4), 'moss')
    i.dots([(14, 18), (15, 17), (15, 18), (16, 16), (13, 19)], 'z')                              # lichen
    i.dots([(14, 17), (16, 17)], 'A')
    return i.outline()


def warding_staff():
    i = Pic()
    i.stroke([(5, 27), (11, 21), (17, 15), (21, 11)], 3.0, 'pale_wood', centre=(13, 19), radius=12)
    i.layer(ring(24, 8, 4.2, 6.0), 'silver')                                                   # an open hoop
    i.layer(poly([(24, 4.2), (27.2, 5.4), (27.2, 8.6), (24, 12.0), (20.8, 8.6), (20.8, 5.4)]), 'glow', flat=None)   # a shield of soft cyan light
    i.layer(poly([(24, 5.8), (26, 6.6), (26, 8.2), (24, 10.2), (22, 8.2), (22, 6.6)]), 'glow', flat=0)
    i.dot(22, 6, 't')
    return i.outline()


def storm_staff():
    i = Pic()
    i.stroke([(4, 28), (10, 22), (16, 16), (20, 12)], 3.0, 'dark_iron', centre=(12, 20), radius=12)
    for k in (0.15, 0.45):                                                                     # iron bands
        p = lerp((4, 28), (20, 12), k)
        i.layer(bar((p[0] - 1.9, p[1] - 1.9), (p[0] + 1.9, p[1] + 1.9), 2.4, 2.4), 'steel', flat=1)
    i.stroke([(20, 12), (19, 4.5)], 2.2, 'iron', centre=(19, 8), radius=5)                       # a fork: two prongs
    i.stroke([(20, 12), (28, 11)], 2.2, 'iron', centre=(24, 11), radius=5)
    i.layer(disc(23.5, 7.5, 3.4), 'glow', centre=(23.5, 7.5), radius=4)                          # a spark crackling between them
    i.layer(disc(23.5, 7.5, 1.7), 'cream', flat=0)
    i.line((26, 3), (24.6, 5.2), 't')
    i.line((29, 6), (27, 7), 'o')
    i.line((27, 11), (25.4, 9.4), 'o')
    i.line((21, 3), (22.6, 4.6), 'o')
    return i.outline()


# --- armour -------------------------------------------------------------------------------
def tunic(i, body_ramp, shoulders=True):
    """A shirt's shape: shoulders, short sleeves, a body down to the hem."""
    outline = [(11, 4), (16, 6), (21, 4), (28, 8), (27, 14), (23, 14.5), (23, 27), (9, 27), (9, 14.5), (5, 14), (4, 8)]
    i.layer(poly(outline), body_ramp, centre=(16, 15), radius=14)
    return outline


def leather_jerkin():
    i = Pic()
    tunic(i, 'leather')
    i.layer(poly([(14, 4.8), (16, 7.5), (18, 4.8), (16, 5.5)]), 'leather', flat=3)             # the neck
    i.layer(rect(14.4, 8, 17.6, 26.8), 'leather', flat=2)                                      # the front, laced up
    for y in range(9, 26, 3):
        i.line((14, y), (18, y + 1), 'T' if False else 't')
        i.line((18, y), (14, y + 1), 't')
    i.layer(rect(5.5, 7.5, 11.5, 12.5), 'leather', flat=0)                                     # a patch on the shoulder
    for p in ((6, 8), (11, 8), (6, 12), (11, 12), (8, 8), (8, 12)):
        i.dot(*p, 'e')
    i.layer(rect(9, 25, 23, 26.8), 'leather', flat=3)                                          # the hem
    return i.outline()


def iron_mail():
    i = Pic()
    tunic(i, 'steel')
    for y in range(6, 27):                                                                     # links
        for x in range(5, 28):
            if i.grid[y][x] in 'rqp' and (x + y) % 3 == 0 and 5 < x < 27:
                i.grid[y][x] = 'l'
    i.layer(rect(9, 24, 23, 27), 'dark_iron', flat=1)                                          # a dark hem
    i.layer(rect(9, 24, 23, 25.3), 'dark_iron', flat=2)
    i.dot(10, 12, 't')                                                                         # one bright rivet
    i.dot(10, 11, 't')
    return i.outline()


def warden_plate():
    i = Pic()
    breast = [(8, 5), (14, 6.5), (16, 8), (18, 6.5), (24, 5), (28, 9), (25, 15), (23, 24), (19, 28), (16, 29), (13, 28), (9, 24), (7, 15), (4, 9)]
    i.layer(poly(breast), 'stone', centre=(16, 16), radius=14)
    for a, b in (((9, 14), (23, 14)), ((10, 20), (22, 20))):                                    # slabs, split by dark seams
        i.line(a, b, 'k')
    i.line((16, 8), (16, 13), 'k')
    for y in (13, 14, 19, 20):                                                                 # iron straps round it
        pass
    i.layer(rect(7, 12.6, 25, 14.4), 'dark_iron', flat=1)
    i.layer(rect(8, 18.6, 24, 20.4), 'dark_iron', flat=1)
    i.dots([(9, 13), (23, 13), (10, 19), (22, 19)], 't')                                       # rivets
    i.dots([(8, 7), (9, 7), (9, 8), (22, 6), (23, 6)], 'A')                                      # moss
    i.dots([(9, 9), (10, 8), (24, 7)], 'z')
    i.layer(rect(14.4, 21.6, 17.6, 26.4), 'moss', flat=0)                                      # a carved rune, glowing green
    i.layer(rect(13, 23, 19, 24), 'moss', flat=0)
    i.dots([(16, 22), (16, 25)], 'r')
    return i.outline()


def dragonscale_mail():
    i = Pic()
    tunic(i, 'teal')
    for row, y in enumerate(range(7, 27, 3)):                                                  # overlapping scales: rows of rounded caps
        for x in range(5 + (row % 2) * 2, 28, 4):
            if i.grid[y][x] != '.' and i.grid[y + 1][x] != '.':
                ember = (x + row) % 5 == 0
                for dx, dy, role in ((0, 0, 'a' if ember else 'q'), (1, 0, 'b' if ember else 'r'), (0, 1, 'e' if ember else 's'), (1, 1, 'a' if ember else 'p')):
                    if i.grid[y + dy][x + dx] != '.':
                        i.grid[y + dy][x + dx] = role
    for k, (x0, x1) in enumerate(((9, 12), (13, 16), (17, 20), (21, 24))):                     # a collar of spikes
        i.layer(poly([(x0, 5), (x1, 5), ((x0 + x1) / 2, 1.2)]), 'cream', flat=min(2, k % 3))
    for x, y in ((6, 3), (7, 1), (6, 0), (5, 2)):                                              # a little steam off the shoulder
        i.dot(x, y, 't')
    return i.outline()


# --- trinkets -----------------------------------------------------------------------------
def boot(i, ox, ramp, flip=False):
    pts = [(ox + 1, 5), (ox + 7, 5), (ox + 7.4, 15), (ox + 10, 16), (ox + 12.2, 18.2), (ox + 12.8, 21), (ox + 12, 24), (ox + 0.5, 24)]
    i.layer(poly(pts), ramp, centre=(ox + 6, 14), radius=11)
    i.layer(minus(rect(ox + 0.5, 23.2, ox + 12.6, 26.4), disc(ox + 12.6, 26.6, 1.6)), 'dark_iron', flat=1)       # the sole
    i.layer(rect(ox + 1, 5, ox + 7, 7), ramp, flat=3)                                          # the cuff
    i.layer(rect(ox + 8, 20.4, ox + 12.4, 21.4), ramp, flat=3)                                 # the toe cap seam


def swift_boots():
    i = Pic()
    boot(i, 3, 'teal')
    boot(i, 15, 'teal')
    for ox in (3, 15):                                                                          # a tiny wing at each ankle
        i.layer(poly([(ox + 7.4, 13), (ox + 13.2, 10.2), (ox + 11.6, 12.2), (ox + 14.2, 12.6), (ox + 11.2, 14.4), (ox + 12.6, 15.6), (ox + 7.4, 15.4)]), 'pale', centre=(ox + 10, 13), radius=5)
    return i.outline()


def windrunner_boots():
    i = Pic()
    boot(i, 3, 'pale')
    boot(i, 15, 'pale')
    for ox in (3, 15):
        for k, (x, y) in enumerate(((1, 10), (3, 11.5), (5, 13), (7, 12), (9, 10.5))):         # a spiral of wind lines round the shaft
            i.dot(int(ox + x), int(y), 'o')
            i.dot(int(ox + x) + 1, int(y) + 1, 'n')
        i.dots([(ox + 2, 15), (ox + 4, 16), (ox + 6, 15)], 'o')
    for cx, cy, r in ((3, 27, 2.4), (6.4, 28, 2.0), (15, 27, 2.4), (18.4, 28, 2.0)):          # little clouds at the heels
        i.layer(disc(cx, cy, r), 'pale', centre=(cx, cy), radius=r)
    return i.outline()


def warding_charm():
    i = Pic()
    i.chain(((6, 1), (26, 1)), (16, 9), 'cord')
    i.layer(ring(16, 10, 0.9, 2.1), 'cord')
    shield = [(16, 12), (24, 14), (24, 21), (16, 29), (8, 21), (8, 14)]
    i.layer(poly(shield), 'steel', centre=(16, 20), radius=10)
    i.layer(poly([(16, 14.4), (21.8, 16), (21.8, 20.4), (16, 26.4), (10.2, 20.4), (10.2, 16)]), 'glow', centre=(16, 20), radius=8)
    i.layer(poly([(16, 17), (19.4, 18), (19.4, 20.4), (16, 23.6), (12.6, 20.4), (12.6, 18)]), 'glow', flat=0)
    i.dot(13, 17, 't')
    return i.outline()


def vigor_ring():
    i = Pic()
    i.layer(minus(ellipse(16, 21, 9.8, 8.4), ellipse(16, 21.8, 5.8, 4.8)), 'ember', centre=(16, 21), radius=10)     # a red-gold band
    i.layer(minus(ellipse(16, 21, 9.8, 8.4), ellipse(16, 21.8, 7.8, 6.6)), 'gold', centre=(16, 21), radius=10, flat=None)
    i.layer(poly([(11, 13.5), (21, 13.5), (23, 10.5), (9, 10.5)]), 'gold', flat=2)             # the setting
    i.layer(heart(16, 9.6, 5.2), 'ruby')
    i.dot(13, 7, 't')
    return i.outline()


def strength_band():
    i = Pic()
    band = minus(ellipse(16, 16, 13, 10.5), ellipse(16, 16, 9.6, 7.4))
    i.layer(band, 'leather', centre=(16, 16), radius=13)
    for x in range(5, 28, 2):                                                                   # orange stitching along both edges
        for y, role in ((6 + int(round(abs(x - 16) * 0.16)), 'b'), (26 - int(round(abs(x - 16) * 0.18)), 'b')):
            if i.grid[y][x] != '.':
                i.dot(x, y, role)
    i.layer(rect(10, 4.6, 22, 9.6), 'steel')                                                    # an iron stud plate
    for x in (12, 16, 20):
        i.dot(x, 7, 't')
    return i.outline()


def sage_amulet():
    i = Pic()
    i.chain(((5, 1), (27, 1)), (16, 8))
    i.layer(ring(16, 9, 0.9, 2.2), 'gold')
    i.layer(ring(16, 20, 8.2, 10.6), 'gold', centre=(16, 20), radius=10)                         # a thin gold setting
    i.layer(disc(16, 20, 8.4), 'violet', centre=(16, 20), radius=9)                              # a purple orb
    i.layer(poly([(9.4, 20), (12.5, 16.6), (16, 15.4), (19.5, 16.6), (22.6, 20), (19.5, 23.4), (16, 24.6), (12.5, 23.4)]), 'cream', flat=0)   # a half-open eye
    i.layer(minus(poly([(9.4, 20), (12.5, 16.6), (16, 15.4), (19.5, 16.6), (22.6, 20), (9.4, 20)]), rect(0, 19.4, 32, 21)), 'violet', flat=3)    # the upper lid
    i.layer(disc(16, 21.6, 2.4), 'violet', flat=2)
    i.dot(16, 22, 'x')
    return i.outline()


def giants_belt():
    i = Pic()
    i.layer(rect(1, 12, 31, 20), 'leather', centre=(16, 16), radius=16)                         # a thick belt
    i.layer(rect(1, 12, 31, 13.4), 'leather', flat=0)
    for x in range(3, 31, 4):
        i.dot(x, 16, 'e')                                                                       # stitched holes
    i.layer(poly([(10, 7), (14, 4.5), (20, 5), (24, 8), (25, 17), (23, 25), (17, 28), (11, 26), (8, 19)]), 'stone', centre=(16, 16), radius=12)   # a buckle like a boulder
    i.layer(poly([(12, 9.5), (16, 7.8), (21, 8.6), (22.6, 16), (20.6, 23), (16, 25), (12, 23), (10.4, 17)]), 'stone', centre=(16, 16), radius=9, flat=1)
    i.layer(rect(14.6, 14, 17.6, 25), 'steel', flat=2)                                          # the prong
    i.dots([(12, 11), (13, 10)], 'r')
    i.dots([(19, 12), (20, 14)], 'A')
    return i.outline()


def hawkeye_pendant():
    i = Pic()
    i.chain(((5, 1), (27, 1)), (16, 8))
    i.layer(ring(16, 9, 0.9, 2.2), 'gold')
    eye = [(5, 17), (10, 13), (16, 11.6), (22, 13), (27, 17), (22, 21), (16, 22.6), (10, 21)]
    i.layer(poly(eye), 'gold', centre=(16, 17), radius=12)                                      # a golden eye
    i.layer(poly([(8, 17), (11.4, 14.4), (16, 13.6), (20.6, 14.4), (24, 17), (20.6, 19.6), (16, 20.4), (11.4, 19.6)]), 'cream', flat=1)
    i.layer(disc(16, 17, 3.0), 'topaz', centre=(16, 17), radius=3)
    i.layer(disc(16, 17, 1.4), 'hole', flat=0)
    i.dot(15, 16, 't')
    i.layer(poly([(16, 22.4), (19.4, 25), (20, 31), (16.6, 29), (14.8, 24)]), 'rust', centre=(17, 27), radius=5)    # a hawk's feather
    i.line((16, 23), (17.6, 29.4), 'd')
    return i.outline()


def guardian_sigil():
    i = Pic()
    i.layer(disc(16, 16, 13.4), 'bronze', centre=(16, 16), radius=14)                           # a round bronze plaque
    i.layer(ring(16, 16, 11.0, 12.0), 'bronze', flat=3)
    i.layer(poly([(16, 12.4), (23, 14), (23, 20.4), (16, 28), (9, 20.4), (9, 14)]), 'bronze', flat=3)             # a shield, stamped in: dark rim
    i.layer(poly([(16, 14), (21.4, 15.4), (21.4, 19.8), (16, 25.8), (10.6, 19.8), (10.6, 15.4)]), 'bronze', centre=(16, 20), radius=8, flat=0)
    i.line((16, 14.4), (16, 24.6), 'a')                                                          # a line down the middle of the shield
    i.line((11, 18), (21, 18), 'a')
    i.layer(disc(16, 7.6, 1.9), 'gold', flat=0)                                                  # a small sun above it
    for k in range(8):
        a = k * math.pi / 4
        i.dot(int(16 + math.cos(a) * 3.7), int(7.6 + math.sin(a) * 3.7), 'd')
    return i.outline()


def sage_circlet():
    i = Pic()
    band = minus(ellipse(16, 23, 12.6, 6.4), ellipse(16, 23.2, 10.2, 4.2))
    i.layer(band, 'silver', centre=(16, 23), radius=12.6)                                       # a thin silver circlet, seen a little from above
    i.layer(poly([(16, 15.2), (18.2, 17.4), (16, 19.6), (13.8, 17.4)]), 'silver', flat=1)       # a point at the front
    i.layer(diamond(16, 8.4, 4.4, 5.6), 'violet', centre=(16, 8.4), radius=6)                    # a gem floating just above it
    i.layer(poly([(16, 4.4), (19, 8.4), (16, 12.4), (13, 8.4)]), 'violet', flat=None)
    i.dots([(14, 6), (15, 5)], 't')
    i.dots([(5, 8), (6, 7), (6, 9), (7, 8), (27, 11), (26, 10), (26, 12), (25, 11)], 'v')       # sparkles
    return i.outline()


def summit_crown():
    i = Pic()
    peaks = [(3, 22), (3, 12), (8, 17), (11, 8), (16, 15), (21, 4), (26, 14), (29, 9), (29, 22)]
    i.layer(poly(peaks), 'steel', centre=(16, 14), radius=15)                                    # a jagged crown of peaks
    for pts in (((11, 8), (13.3, 11.4), (8.7, 11.4)), ((21, 4), (24.2, 9.4), (17.8, 9.4)), ((29, 9), (30.4, 12), (27, 12)), ((3, 12), (4.4, 15), (1.6, 15))):
        i.layer(poly(list(pts)), 'pale', flat=0)                                                  # snow on the tops
    i.layer(rect(3, 21, 29, 26), 'gold', centre=(16, 23), radius=14)                              # the band
    i.layer(disc(16, 23.4, 2.6), 'sapphire')                                                     # a bright blue gem at the centre
    i.dots([(15, 22), (16, 21)], 't')
    return i.outline()


def phoenix_heart():
    i = Pic()
    i.layer(heart(16, 18.6, 10.6), 'ember', centre=(16, 18), radius=12)                           # an ember heart
    i.layer(heart(16, 19.0, 7.4), 'flame', centre=(16, 18), radius=8)
    i.layer(heart(16, 19.6, 3.8), 'cream', flat=0)
    for x in (10, 16, 22):                                                                         # a small cage of gold flame round it
        i.line((x, 9.5), (x + (x - 16) * 0.1, 27.4), 'b')
    i.line((9.6, 12.4), (22.4, 12.4), 'b')
    i.layer(minus(ellipse(16, 27.2, 8.4, 2.2), ellipse(16, 26.2, 6, 1.1)), 'gold', flat=1)
    i.layer(poly([(24, 10), (28, 5), (30, 1.6), (29, 7), (27, 11), (25, 12.4)]), 'flame', centre=(27, 8), radius=6)      # a feather of fire
    i.layer(poly([(27, 9), (28.6, 5.6), (29, 4), (28.6, 8)]), 'flame', flat=0)
    return i.outline()


def stormcaller_band():
    i = Pic()
    i.layer(minus(ellipse(16, 21, 10, 8.4), ellipse(16, 22, 6.4, 5.2)), 'dark_iron', centre=(16, 21), radius=10)
    i.layer(disc(16, 9, 7.4), 'dark_iron', centre=(16, 9), radius=8)                              # the setting
    i.layer(disc(16, 9, 5.8), 'sapphire', centre=(16, 9), radius=6, flat=3)                       # the gem: a stormy dark blue
    i.layer(ellipse(14.4, 8.6, 3.6, 2.0), 'steel', centre=(14.4, 8.6), radius=3.6)                # a storm cloud in it
    i.layer(ellipse(17.8, 7.4, 2.8, 1.8), 'steel', flat=1)
    i.line((16, 9.6), (15, 11.4), 'd')                                                             # a tiny bolt
    i.line((15, 11.4), (17, 11.8), 'd')
    i.line((17, 11.8), (16, 13), 'd')
    i.dot(12, 6, 't')
    return i.outline()


def stone_idol():
    i = Pic()
    body = [(8, 27), (7, 15), (9, 8), (12, 4.5), (20, 4.5), (23, 8), (25, 15), (24, 27)]
    i.layer(poly(body), 'stone', centre=(16, 16), radius=14)                                        # a squat carved idol
    i.layer(rect(7, 25, 25, 28), 'iron', flat=1)
    i.layer(poly([(9, 11), (15, 13.2), (15, 14.6), (9, 12.6)]), 'dark_iron', flat=1)                # a grumpy brow, slanting in
    i.layer(poly([(23, 11), (17, 13.2), (17, 14.6), (23, 12.6)]), 'dark_iron', flat=1)
    i.layer(rect(11.2, 14.6, 14.2, 17.4), 'flame', flat=0)                                           # two faintly glowing eyes
    i.layer(rect(17.8, 14.6, 20.8, 17.4), 'flame', flat=0)
    i.dots([(12, 15), (18, 15)], 't')
    i.line((12, 22.4), (14, 21), 'x')                                                                # a frown
    i.line((14, 21), (18, 21), 'x')
    i.line((18, 21), (20, 22.4), 'x')
    i.layer(ellipse(15, 5.4, 4.6, 1.8), 'moss')                                                      # moss on its head and one shoulder
    i.dots([(9, 9), (8, 10), (9, 10), (22, 8), (23, 9)], 'A')
    return i.outline()


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
        print('the item icons, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
