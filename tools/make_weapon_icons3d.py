#!/usr/bin/env python3
"""The weapon icons and the amulets again, made the way the new item pictures are (see make_item_icons3d.py): each a small 3D model ray-cast with the creatures' renderer, with its details painted over.

These are the 22 weapon display icons (make_weapon_icons.py) and the 8 amulets (make_amulets.py), the same names and ids, so a 3D version can stand in for a flat one. Weapons all lie on the 45 degree
diagonal rising to the upper right, bows too (an upright bow is turned onto it). The colours stay the old icons': teal steel blades, purple shafts, gold guards, so they sit beside what the game has.

    python3 tools/make_weapon_icons3d.py --preview previews/weapon-icons3d.png     the 22 weapons and the 8 amulets, enlarged, with their names
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_item_icons3d import (BOW_TURN, Bx, E, RAMPS, S, blade, chain, finish, line_px, paint, px_paint, render, ring, rod, rotp)  # noqa: E402

CELL = 32
RAMPS.update({
    'steel_t': ('r', 'q', 'p', 'l'),           # the old icons' teal steel
    'shaft': ('l', 'k', 'w', 'x'),             # their purple shafts
    'gold_t': ('d', 'b', 'a', 'g'),
    'bonec': ('t', 'C', 'c', 'e'),
    'crystal': ('t', 'r', 'o', 'n'),
    'green_gem': ('r', 'z', 'A', 'B'),
    'purple_orb': ('v', 'u', 'w', 'x'),
})


class Parts(list):
    """The parts of a model, and the ridges to paint along its blades afterwards."""
    def __init__(self, *a):
        super().__init__(*a)
        self.ridges = []


def done(parts):
    """Render a model, paint the light ridge down each blade, and finish."""
    g = render(parts)
    for t0, t1, ramp in getattr(parts, 'ridges', ()):
        line_px(g, (int(16 + t0), int(16 - t0)), (int(16 + t1), int(16 - t1)), RAMPS[ramp][0])
    return finish(g)


def leaf(parts, t0, t1, half, ramp, name='blade'):
    """A blade as a long lens (so it shades across its width) on the diagonal from t0 to t1, with a light ridge down it."""
    c = (t0 + t1) / 2
    length = (t1 - t0) * math.sqrt(2)
    parts.append(E(c, c, 0, length / 2 + 0.9, half, 1.7, ramp, name, 45))
    if hasattr(parts, 'ridges'):
        parts.ridges.append((t0 + 1.0, t1 - 2.2, ramp))


def D(t):
    """The point t along the 45 degree diagonal through the middle."""
    return (t, t)


def hilt(parts, t0, t1=None, grip='shaft', pommel='gold_t'):
    parts.append(rod(D(t0), D(t1 if t1 is not None else t0 - 5), 1.4, grip, 'grip'))
    parts.append(S(*D((t1 if t1 is not None else t0 - 5) - 0.8), 0.2, 1.9, pommel, 'pommel'))


def guard(parts, t, half=3.8, ramp='gold_t'):
    parts.append(Bx(t, t, 0.5, half, 1.2, 1.5, ramp, 'guard', 135))


def sword(parts, base, tip, half=2.3, ramp='steel_t', guard_half=3.8):
    leaf(parts, base, tip, half, ramp)
    guard(parts, base - 0.6, guard_half)
    hilt(parts, base - 1.0, base - 6.0)


def axe(parts, haft0, haft1, head_t, head_len, head_half, ramp='steel_t'):
    """A haft on the diagonal and a head on its top, swept out along the other diagonal."""
    parts.append(rod(D(haft0), D(haft1), 1.3, 'shaft', 'haft'))
    cu, cv = head_t - 0.8, head_t - 0.8
    parts.append(E(cu, cv, 0.3, head_half, head_len, 1.6, ramp, 'head', 45))
    parts.append(E(cu - head_len * 0.5, cv + head_len * 0.5, 0.5, head_half * 0.55, head_len * 0.78, 1.2, ramp, 'edge', 45))
    parts.append(S(*D(head_t - 3.4), 0.6, 1.6, 'gold_t', 'collar'))


# --- weapons ------------------------------------------------------------------------------
def hatchet():
    parts = Parts()
    axe(parts, -12, 7, 8.5, 5.0, 2.2)
    return done(parts)


def iron_axe():
    parts = Parts()
    axe(parts, -12, 8, 8.8, 5.6, 2.6)
    paint(g := render(parts), [(5, 11), (6, 12)], 't')
    return finish(g)


def iron_sword():
    parts = Parts()
    sword(parts, -3, 12.5)
    return done(parts)


def scepter():
    parts = [rod(D(-12), D(5), 1.2, 'shaft', 'shaft'), S(*D(7.6), 1.0, 4.4, 'green_gem', 'gem'), E(*D(4.4), 0.6, 2.2, 1.1, 1.3, 'gold_t', 'mount', 135), E(*D(3.0), 0.6, 1.6, 1.0, 1.2, 'gold_t', 'collar', 135)]
    g = render(parts)
    return finish(g)


def wooden_staff():
    parts = [rod(D(-12), D(8), 1.35, 'shaft', 'shaft'), E(*D(9.4), 0.6, 2.6, 3.2, 2.4, 'purple_orb', 'knob', 45)]
    return done(parts)


def wooden_sword():
    parts = Parts()
    sword(parts, -3, 11.5, 2.2, 'wood', 3.4)
    return done(parts)


def dagger():
    parts = Parts()
    sword(parts, -3, 8.5, 1.9, 'steel_t', 3.2)
    return done(parts)


def stiletto():
    parts = Parts()
    leaf(parts, -4, 11, 1.25, 'steel_t')
    guard(parts, -4.8, 2.6)
    hilt(parts, -5.4, -9.4)
    return done(parts)


def kris():
    parts = Parts()
    pts = [(-3, -3), (-0.8, 0.2), (2.0, 1.2), (3.6, 4.6), (6.4, 5.6), (8.2, 9.2), (10.8, 10.2)]       # a wavy blade
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        parts.append(rod(a, b, 2.1 - 0.17 * i, 'steel_t', f'blade{i}', 0.0, grow=0.6))
    guard(parts, -4.0, 3.0)
    hilt(parts, -4.6, -8.6)
    return done(parts)


def bone_dagger():
    parts = Parts()
    pts = [(-3, -3), (1.0, 1.4), (5.0, 5.8), (8.4, 10.6), (9.8, 13.4)]                                     # a curved bone blade
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        parts.append(rod(a, b, 2.5 - 0.5 * i, 'bonec', f'blade{i}', 0.0, grow=0.9))
    parts.append(rod(D(-3.8), D(-9), 1.5, 'cord', 'grip'))
    parts.append(S(*D(-9.6), 0.2, 1.8, 'bonec', 'pommel'))
    return done(parts)


def greatsword():
    parts = Parts()
    sword(parts, -2, 14, 3.1, 'steel_t', 5.0)
    return done(parts)


def scimitar():
    parts = Parts()
    pts = [(-3, -3), (0.4, 0.2), (4.2, 2.4), (8.0, 4.0), (11.6, 4.6)]                                      # a blade that curves over
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        parts.append(rod(a, b, 2.6 - 0.45 * i, 'steel_t', f'blade{i}', 0.0, grow=0.6))
    guard(parts, -4.0, 3.4)
    hilt(parts, -4.6, -9.0)
    return done(parts)


def battle_axe():
    parts = Parts()
    axe(parts, -12, 8, 9.0, 6.8, 3.0)
    parts.append(Bx(2.0, 2.0, 0.4, 0.9, 2.4, 1.3, 'gold_t', 'band', 45))
    return done(parts)


def war_hammer():
    parts = [rod(D(-12), D(8), 1.35, 'shaft', 'haft'), E(*D(8.4), 0.4, 4.2, 3.0, 2.8, 'steel_t', 'head', 45), E(*D(8.4), 0.4, 1.4, 4.8, 2.1, 'steel_t', 'peen', 45),
             S(*D(5.0), 0.6, 1.6, 'gold_t', 'collar')]
    return done(parts)


def spiked_mace():
    parts = [rod(D(-12), D(5.6), 1.35, 'shaft', 'haft'), S(*D(9.4), 0.4, 4.4, 'steel_t', 'ball')]
    for k, a in enumerate(range(0, 360, 45)):                                                                     # spikes all round it
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        c = D(9.4)
        parts.append(rod((c[0] + ux * 3.4, c[1] + uy * 3.4), (c[0] + ux * 6.9, c[1] + uy * 6.9), 0.9, 'steel_t', f'spike{k}', 0.6))
    return done(parts)


def spear():
    parts = [rod(D(-12.5), D(8), 1.1, 'shaft', 'shaft'), E(*D(11.6), 0.5, 4.4, 2.0, 1.2, 'steel_t', 'head', 45)]
    return done(parts)


def crystal_staff():
    parts = [rod(D(-12), D(7.4), 1.2, 'shaft', 'shaft'), E(*D(11.0), 0.8, 4.2, 2.2, 2.0, 'crystal', 'crystal', 45), E(*D(8.2), 0.4, 1.8, 1.0, 1.2, 'gold_t', 'claw', 135)]
    g = render(parts)
    paint(g, [(7.5, 9.5)], 't')
    return finish(g)


# --- bows: drawn upright, then turned onto the diagonal ----------------------------------------
def bow(top, string_x, grip_half, limb_r, ramp, tips=None):
    T = lambda p: rotp(p, BOW_TURN)
    parts = chain([T(p) for p in top], limb_r, ramp, 'limbT') + chain([T((a, -b)) for a, b in reversed(top)], limb_r, ramp, 'limbB')
    parts.append(rod(T((string_x, top[0][1])), T((string_x, -top[0][1])), 0.4, 'cream', 'string', -1.5))
    gu, gv = T((top[-1][0], 0))
    parts.append(E(gu, gv, 0.5, 1.5, grip_half, 1.8, 'gold_t', 'grip', BOW_TURN))
    if tips:
        for k, (p, rot) in enumerate(tips):
            tu, tv = T(p)
            parts.append(E(tu, tv, 0.8, 1.1, 2.2, 0.7, 'moss', f'tip{k}', rot + BOW_TURN))
    return parts


def plain_bow():
    return finish(render(bow([(5.5, 13), (0.5, 9.5), (-2.0, 4.0), (-2.6, 0.0)], 6.0, 2.4, 1.3, 'pale_wood')))


def longbow():
    return finish(render(bow([(3.0, 15), (-0.2, 10), (-1.6, 4.0), (-1.9, 0.0)], 3.2, 2.2, 1.1, 'dark_wood')))


def shortbow():
    return finish(render(bow([(5.8, 10.5), (1.0, 7.5), (-2.4, 3.0), (-3.0, 0.0)], 6.4, 2.0, 1.4, 'wood')))


def recurve():
    return finish(render(bow([(7.5, 13.5), (4.0, 11.5), (0.0, 7.0), (-2.2, 2.0), (-2.6, 0.0)], 7.5, 2.6, 1.3, 'dark_wood')))


def elven():
    parts = bow([(5.0, 14.5), (1.0, 11.0), (-2.2, 5.0), (-3.0, 0.0)], 5.6, 2.4, 1.0, 'moss', tips=[((6.2, 14.6), 25), ((6.2, -14.6), -25)])
    g = render(parts)
    return finish(g)


# --- amulets ------------------------------------------------------------------------------
def amulet(parts, bail_v=9.4, ramp='gold'):
    parts += chain([(-11, 15), (-5, 11), (0, bail_v)], 0.7, ramp, 'chainL') + chain([(11, 15), (5, 11), (0, bail_v)], 0.7, ramp, 'chainR') + [S(0, bail_v - 0.4, 0.6, 1.6, ramp, 'bail')]
    return parts


def ruby_heart():
    parts = amulet([], 9.4)
    parts += [S(-4.2, -1.4, 0, 5.4, 'gold', 'lobeL'), S(4.2, -1.4, 0, 5.4, 'gold', 'lobeR'), Bx(0, -6.8, 0, 6.6, 6.6, 3.4, 'gold', 'point', 45),
              S(-3.6, -1.4, 2.2, 3.5, 'ruby', 'rubyL'), S(3.6, -1.4, 2.2, 3.5, 'ruby', 'rubyR'), Bx(0, -5.8, 2.2, 4.2, 4.2, 2.0, 'ruby', 'rubyP', 45)]
    g = render(parts)
    paint(g, [(-4.5, 0.4), (-3.5, 0.9)], 't')
    return finish(g)


def sapphire():
    parts = amulet([], 9.4, 'silver') + ring(0, -4.4, 8.4, 8.4, 1.2, 32, 'silver', 'setting', 1.0) + [S(0, -4.4, 0, 7.8, 'sapphire', 'orb'), S(-1.8, -2.2, 6.0, 2.0, 'glow', 'shine')]
    g = render(parts)
    paint(g, [(-3, -1.8), (-2, -1.2)], 't')
    return finish(g)


def emerald():
    parts = amulet([], 9.4) + [Bx(0, -4.8, 0, 9.0, 9.0, 3.0, 'gold', 'setting', 45), Bx(0, -4.8, 1.8, 6.6, 6.6, 2.4, 'emerald', 'gem', 45), Bx(0, -4.8, 3.2, 3.6, 3.6, 1.6, 'emerald', 'facet', 45)]
    g = render(parts)
    paint(g, [(-3, -2.4)], 't')
    return finish(g)


def sunstone():
    parts = amulet([], 9.4)
    for k in range(8):
        a = k * math.pi / 4
        parts.append(rod((7.0 * math.cos(a), -5.4 + 7.0 * math.sin(a)), (12.0 * math.cos(a), -5.4 + 12.0 * math.sin(a)), 1.4, 'gold', f'ray{k}', 0.2, grow=0.4))
    parts += [S(0, -5.4, 0.6, 7.2, 'gold', 'disc'), S(0, -5.4, 2.4, 5.0, 'topaz', 'stone'), S(0, -5.4, 4.0, 2.6, 'topaz', 'core')]
    g = render(parts)
    paint(g, [(-2, -3)], 't')
    return finish(g)


def moon():
    parts = amulet([], 9.4, 'silver')
    arc = [(-1.0 + 8.4 * math.cos(math.radians(a)), -4.4 + 8.4 * math.sin(math.radians(a))) for a in range(80, 281, 20)]     # a crescent: a curved line of spheres thicker in the middle
    for i, p in enumerate(arc):
        t = i / (len(arc) - 1)
        parts.append(S(p[0], p[1], 0, 1.2 + 3.0 * math.sin(math.pi * t) ** 0.8, 'silver', 'moon'))
    parts += [S(6.6, -7.0, 1.0, 1.7, 'gold', 'star')]
    g = render(parts)
    return finish(g)


def bone_talisman():
    parts = amulet([], 9.4, 'cord')
    parts += [E(0, -3.2, 0, 8.2, 7.6, 5.0, 'bone', 'cranium'), Bx(0, -10.2, 0.6, 4.6, 2.2, 3.2, 'bone', 'jaw'),
              E(-3.2, -3.0, 4.2, 2.1, 2.5, 1.6, 'hole', 'eyeL'), E(3.2, -3.0, 4.2, 2.1, 2.5, 1.6, 'hole', 'eyeR'), Bx(0, -6.2, 4.4, 0.9, 1.4, 1.0, 'hole', 'nose', 0)]
    g = render(parts)
    for u in (-3, -1, 1, 3):                                                                  # teeth
        paint(g, [(u, -9.6), (u, -10.6)], 't')
    return finish(g)


def rose():
    parts = amulet([], 9.4)
    parts += [E(-5.6, -8.4, 0, 4.6, 2.0, 1.6, 'leaf', 'leafL', 20), E(5.6, -8.4, 0, 4.6, 2.0, 1.6, 'leaf', 'leafR', -20), S(0, -4.0, 0, 7.4, 'rose', 'bloom')]
    for k, (u, v, r) in enumerate(((-2.6, -2.0, 3.0), (2.8, -3.0, 2.8), (0, -5.6, 3.0), (-3.0, -5.8, 2.4), (1.2, -1.0, 2.2))):      # petals curling in
        parts.append(S(u, v, 3.0 + 0.4 * k, r, 'rose', f'petal{k}'))
    parts.append(Bx(0, -11.4, 0, 2.0, 2.4, 1.2, 'leaf', 'sepal', 45))
    g = render(parts)
    paint(g, [(-3, -1)], 't')
    return finish(g)


def rune_stone():
    parts = amulet([], 9.4, 'steel')
    for k, ang in enumerate((0, 60, 120)):                                                    # a hexagon from three blocks
        parts.append(Bx(0, -4.6, 0.2 * k, 8.4, 4.9, 3.6, 'stone', 'hex', ang))
    g = render(parts)
    for (u0, v0, u1, v1) in ((0, 1, 0, -10), (-3, -1, 0, -1), (0, -4, 3, -4), (-3, -7, 0, -7)):               # a carved rune
        line_px(g, (int(16 + u0), int(16 - v0)), (int(16 + u1), int(16 - v1)), 'd')
    return finish(g)


WEAPONS = [
    ('hatchet', 'Hatchet', hatchet), ('iron-axe', 'Iron axe', iron_axe), ('iron-sword', 'Iron sword', iron_sword), ('scepter', 'Scepter', scepter), ('wooden-staff', 'Wooden staff', wooden_staff),
    ('wooden-sword', 'Wooden sword', wooden_sword), ('dagger', 'Dagger', dagger), ('stiletto', 'Stiletto', stiletto), ('kris', 'Kris', kris), ('bone-dagger', 'Bone dagger', bone_dagger),
    ('greatsword', 'Greatsword', greatsword), ('scimitar', 'Scimitar', scimitar), ('battle-axe', 'Battle axe', battle_axe), ('war-hammer', 'War hammer', war_hammer), ('spiked-mace', 'Spiked mace', spiked_mace),
    ('spear', 'Spear', spear), ('crystal-staff', 'Crystal staff', crystal_staff), ('bow', 'Bow', plain_bow), ('longbow', 'Longbow', longbow), ('shortbow', 'Shortbow', shortbow), ('recurve', 'Recurve bow', recurve),
    ('elven', 'Elven bow', elven),
]
AMULETS = [('ruby-heart', 'Ruby heart', ruby_heart), ('sapphire', 'Sapphire', sapphire), ('emerald', 'Emerald', emerald), ('sunstone', 'Sunstone', sunstone), ('moon', 'Moon', moon),
           ('skull', 'Bone skull', bone_talisman), ('rose', 'Rose', rose), ('rune-stone', 'Rune stone', rune_stone)]
ALL = WEAPONS + AMULETS


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    cols = 8
    cw, ch = CELL * scale + 12, CELL * scale + 24
    sheet = Image.new('RGBA', (cols * cw + 12, ((len(ALL) + cols - 1) // cols) * ch + 12), (44, 40, 76, 255))
    d = ImageDraw.Draw(sheet)
    for k, (id, label, make_icon) in enumerate(ALL):
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
    parser.add_argument('--preview', type=Path, help='the weapons and the amulets, enlarged, with their names')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('the 3D weapon icons and amulets, enlarged ->', args.preview)


if __name__ == '__main__':
    main()
