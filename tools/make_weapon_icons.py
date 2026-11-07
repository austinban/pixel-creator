#!/usr/bin/env python3
"""Display icons for the weapons: one 32 x 32 image each, in the amulets' style, for the shop and any weapon list.

Which icon belongs to which weapon is by NAME, and the name is the weapon's id without its prefix and facing:

    weapon asset ids        weapon-iron-sword-ne, weapon-iron-sword-se       the NAME is  iron-sword
    its display icon        icon-weapon-iron-sword                           (category "Weapon icons")

Both ends say so in the data: the icon asset has 'icon_for': 'iron-sword' and each weapon asset has 'icon': 'icon-weapon-iron-sword'.
ICONS below is the one list. It has an entry for every weapon, and make_assets.py stops with a message if a weapon has no icon or an icon
names a weapon that is not there, so they cannot drift apart.

How each icon is drawn:
  - the melee weapons use the same parts as the sprites that are made by code (tools/make_melee.py WEAPONS), drawn large on the diagonal;
    the six hand-drawn ones (hatchet, iron axe, iron sword, scepter, wooden staff, wooden sword) have their parts written here, in
    HAND_DRAWN, and so does any weapon whose shape needs changing at this size (the kris)
  - the bows are drawn from the bow models' own numbers (tools/make_bow.py SPECS): size, curve, tips, colours

To add one: add the weapon (its strips, or a bow spec), then one line in ICONS. Preview all:

    python3 tools/make_weapon_icons.py --preview previews/weapon-icons.png
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
import make_bow  # noqa: E402
import make_melee as mm  # noqa: E402
from make_melee import part, rod, taper, swell, tone_of  # noqa: E402

CELL = 32
LIGHT = mm.LIGHT
FIT = 28                      # the weapon (before its outline) fits in this many pixels each way
ICON_RAMPS = dict(mm.RAMPS, gem=('y', 'i', 'h', 'u'), leaf=('r', 'A', 'B', 's'))


def icon_prefix(stem):
    return f'icon-weapon-{stem}'


# --- melee weapons: parts along a diagonal axis -------------------------------------------------
def head_up(t0, t1, reach, ramp):
    """A one-sided axe blade, out toward the upper left (the lit side)."""
    def shape(t):
        k = (t - t0) / (t1 - t0)
        return (-(0.9 + reach * math.sin(math.pi * k) ** 0.8), 0.8)
    return part(t0, t1, shape, ramp)


def orb(t_mid, radius, ramp):
    return part(t_mid - radius, t_mid + radius, lambda t: (-radius * math.sqrt(max(0.0, 1 - ((t - t_mid) / radius) ** 2)), radius * math.sqrt(max(0.0, 1 - ((t - t_mid) / radius) ** 2))), ramp)


# Parts written for the icons themselves: the six hand-drawn weapons (which have no parts), and a form that needs changing at this size.
HAND_DRAWN = {
    # the sprite's kris waves more: at this size that reads as a bolt of lightning, so the icon's blade has a gentler wave
    'kris': [rod(-1.8, 2.4, 1.1, 'leather'), mm.pommel(-2.0, 1.8), mm.guard(2.8, 4.2),
             part(3.2, 12.4, lambda t: (0.45 * math.sin((t - 3.2) * 1.0) - (2.6 * (1 - (t - 3.2) / 9.2) + 0.3) / 2,
                                         0.45 * math.sin((t - 3.2) * 1.0) + (2.6 * (1 - (t - 3.2) / 9.2) + 0.3) / 2), 'steel')],
}


def melee_parts(stem):
    if stem in HAND_DRAWN:
        return HAND_DRAWN[stem]
    return mm.WEAPONS[stem]['parts']


def draw_melee(stem):
    """The weapon's parts on a diagonal (grip lower left, tip upper right), as large as fits, with an outline."""
    parts = melee_parts(stem)
    angle = math.radians(-45)
    d = (math.cos(angle), math.sin(angle))
    n = (-d[1], d[0])
    tmin, tmax = min(p[0] for p in parts), max(p[1] for p in parts)
    mid = (tmin + tmax) / 2
    # the lit side is the one facing the light, as everywhere
    lit_positive = (n[0] * LIGHT[0] + n[1] * LIGHT[1]) > 0

    def sample(scale):
        mask = {}
        ox, oy = CELL / 2 - d[0] * mid * scale, CELL / 2 - d[1] * mid * scale
        for y in range(CELL):
            for x in range(CELL):
                rx, ry = x + 0.5 - ox, y + 0.5 - oy
                t, s = (rx * d[0] + ry * d[1]) / scale, (rx * n[0] + ry * n[1]) / scale
                for t0, t1, shape, ramp in parts:
                    if t0 <= t <= t1:
                        lo, hi = shape(t)
                        if lo - 0.1 <= s <= hi + 0.1:
                            u = min(1.0, max(0.0, (s - lo) / ((hi - lo) or 1)))
                            if lit_positive:
                                u = 1 - u
                            mask[(x, y)] = ICON_RAMPS[ramp][tone_of(u)]
        return mask

    scale = 3.4
    while True:
        mask = sample(scale)
        xs, ys = [p[0] for p in mask], [p[1] for p in mask]
        if max(xs) - min(xs) + 1 <= FIT and max(ys) - min(ys) + 1 <= FIT:
            break
        scale -= 0.1
    return finish(mask)


def finish(mask):
    """Centre the picture in the cell and put the one-pixel outline round it."""
    xs, ys = [p[0] for p in mask], [p[1] for p in mask]
    dx = int(round(CELL / 2 - (min(xs) + max(xs) + 1) / 2))
    dy = int(round(CELL / 2 - (min(ys) + max(ys) + 1) / 2))
    solid = {(x + dx, y + dy): ch for (x, y), ch in mask.items()}
    rows = [['.'] * CELL for _ in range(CELL)]
    for (x, y), ch in solid.items():
        rows[y][x] = ch
    for (x, y) in solid:
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ddx, y + ddy
            if 0 <= nx < CELL and 0 <= ny < CELL and (nx, ny) not in solid:
                rows[ny][nx] = 'O'
    return [''.join(r) for r in rows]


# --- bows: the model's own numbers, drawn flat -------------------------------------------------
ORIGINAL_BOW = dict(label='Bow', half=make_bow.BOW_HALF, bend=1.0, flare=0.0, radius=0.8, ramps={})


def draw_bow(spec):
    ramps = {**ICON_RAMPS, **make_bow.RAMPS, **spec.get('ramps', {})}
    tall = min(12.5 if spec.get('leaf') else 14.5, 4.0 + spec['half'] * 1.18)             # half the bow's height, in pixels
    depth = 3.0 + 3.6 * spec['bend']                         # how far the limbs bow back toward the string
    flare = spec.get('flare', 0.0) * 1.5
    thick = spec.get('radius', 1.0)
    cx, cy = 18.0, CELL / 2
    pts = []
    for i in range(0, 121):
        t = -1 + 2 * i / 120
        off = depth * t * t - flare * max(0.0, (abs(t) - 0.6) / 0.4) ** 2
        pts.append((t, cx - off + depth * 0.5, cy + t * tall, (1.45 - 0.7 * abs(t)) * thick))
    mask = {}
    for y in range(CELL):
        for x in range(CELL):
            best = min(pts, key=lambda p: (x + 0.5 - p[1]) ** 2 + (y + 0.5 - p[2]) ** 2)
            dist = math.hypot(x + 0.5 - best[1], y + 0.5 - best[2])
            if dist <= best[3] + 0.3:
                lit = ((x + 0.5 - best[1]) * LIGHT[0] + (y + 0.5 - best[2]) * LIGHT[1]) / (best[3] or 1)
                tone = 0 if lit > 0.35 else 1 if lit > -0.2 else 2 if lit > -0.65 else 3
                name = 'grip' if abs(best[0]) < 0.14 and 'grip' in spec.get('ramps', {}) else 'bow'
                mask[(x, y)] = ramps[name][tone]
    tips = (pts[0], pts[-1])
    if spec.get('leaf'):
        for tp, sign in ((tips[0], -1), (tips[1], 1)):
            for y in range(CELL):
                for x in range(CELL):
                    if (x + 0.5 - tp[1]) ** 2 / 2.0 + (y + 0.5 - (tp[2] + sign * 2.2)) ** 2 / 7.0 <= 1:
                        lit = ((x + 0.5 - tp[1]) * LIGHT[0] + (y + 0.5 - tp[2] - sign * 2.2) * LIGHT[1]) / 2.4
                        mask[(x, y)] = ramps['leaf'][0 if lit > 0.3 else 1 if lit > -0.3 else 2]
    if spec.get('gem'):
        for y in range(CELL):
            for x in range(CELL):
                if (x + 0.5 - (cx + depth * 0.5 + 1.3)) ** 2 + (y + 0.5 - cy) ** 2 <= 2.6:
                    lit = ((x + 0.5 - cx - depth * 0.5 - 1.3) * LIGHT[0] + (y + 0.5 - cy) * LIGHT[1]) / 1.6
                    mask[(x, y)] = ramps['gem'][0 if lit > 0.3 else 1 if lit > -0.3 else 2]
    # the string, a thin cream line from tip to tip
    (x0, y0), (x1, y1) = (tips[0][1], tips[0][2]), (tips[1][1], tips[1][2])
    steps = int(abs(y1 - y0) * 2)
    for i in range(steps + 1):
        px, py = int(x0 + (x1 - x0) * i / steps), int(y0 + (y1 - y0) * i / steps)
        if (px, py) not in mask:
            mask[(px, py)] = 't'
    return finish(mask)


# --- the list: the one place a weapon and its icon are tied together ------------------------------
# (the weapon's NAME, shown as its label, how to draw it)
ICONS = [
    ('hatchet', 'Hatchet', lambda: draw_melee('hatchet')),
    ('iron-axe', 'Iron axe', lambda: draw_melee('iron-axe')),
    ('iron-sword', 'Iron sword', lambda: draw_melee('iron-sword')),
    ('scepter', 'Scepter', lambda: draw_melee('scepter')),
    ('wooden-staff', 'Wooden staff', lambda: draw_melee('wooden-staff')),
    ('wooden-sword', 'Wooden sword', lambda: draw_melee('wooden-sword')),
    ('dagger', 'Dagger', lambda: draw_melee('dagger')),
    ('stiletto', 'Stiletto', lambda: draw_melee('stiletto')),
    ('kris', 'Kris', lambda: draw_melee('kris')),
    ('bone-dagger', 'Bone dagger', lambda: draw_melee('bone-dagger')),
    ('greatsword', 'Greatsword', lambda: draw_melee('greatsword')),
    ('scimitar', 'Scimitar', lambda: draw_melee('scimitar')),
    ('battle-axe', 'Battle axe', lambda: draw_melee('battle-axe')),
    ('war-hammer', 'War hammer', lambda: draw_melee('war-hammer')),
    ('spiked-mace', 'Spiked mace', lambda: draw_melee('spiked-mace')),
    ('spear', 'Spear', lambda: draw_melee('spear')),
    ('crystal-staff', 'Crystal staff', lambda: draw_melee('crystal-staff')),
    ('bow', 'Bow', lambda: draw_bow(ORIGINAL_BOW)),
    ('longbow', 'Longbow', lambda: draw_bow(make_bow.SPECS['longbow'])),
    ('shortbow', 'Shortbow', lambda: draw_bow(make_bow.SPECS['shortbow'])),
    ('recurve', 'Recurve bow', lambda: draw_bow(make_bow.SPECS['recurve'])),
    ('elven', 'Elven bow', lambda: draw_bow(make_bow.SPECS['elven'])),
]


def weapon_name(asset_id):
    """'weapon-iron-sword-ne' -> 'iron-sword' (None if it is not a weapon strip's id)."""
    if not asset_id.startswith('weapon-') or asset_id[-3:] not in ('-ne', '-se'):
        return None
    return asset_id[len('weapon-'):-3]


def build_icon_assets():
    assets = []
    for name, label, draw in ICONS:
        assets.append({
            'id': icon_prefix(name), 'label': f'{label} (display icon)', 'category': 'Weapon icons', 'kind': 'still', 'place': 'none',
            'icon_for': name,                                  # the weapon's NAME: its assets are weapon-NAME-ne and weapon-NAME-se
            'w': CELL, 'h': CELL, 'cols': 1, 'rows': 1, 'fps': 0,
            'anchor': {'x': CELL // 2, 'y': CELL // 2},
            'frames': [draw()],
        })
    return assets


def link_icons(assets):
    """Mark each weapon asset with its icon's id, and stop if a weapon has no icon or an icon has no weapon. Returns the problems."""
    problems = []
    icons = {a['icon_for']: a['id'] for a in assets if 'icon_for' in a}
    weapons = {}
    for a in assets:
        name = weapon_name(a['id']) if a.get('weapon') else None
        if name:
            weapons.setdefault(name, []).append(a)
    for name, group in weapons.items():
        if name not in icons:
            problems.append(f'weapon "{name}" has no display icon: add ({name!r}, label, drawing) to ICONS in tools/make_weapon_icons.py')
        for a in group:
            if name in icons:
                a['icon'] = icons[name]
    for name in icons:
        if name not in weapons:
            problems.append(f'display icon "{icons[name]}" is for a weapon called "{name}", and there is no such weapon')
    return problems


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    per_row = 6
    rows = -(-len(ICONS) // per_row)
    w = CELL * scale + 8
    sheet = Image.new('RGBA', (per_row * w, rows * (CELL * scale + 22)), (60, 64, 74, 255))
    d = ImageDraw.Draw(sheet)
    for k, (name, label, draw) in enumerate(ICONS):
        x0, y0 = (k % per_row) * w, (k // per_row) * (CELL * scale + 22)
        cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        for y, line in enumerate(draw()):
            for x, ch in enumerate(line):
                if ch != '.':
                    cell.putpixel((x, y), rgb[ch] + (255,))
        sheet.alpha_composite(cell.resize((CELL * scale, CELL * scale), Image.NEAREST), (x0 + 4, y0 + 18))
        d.text((x0 + 6, y0 + 3), label, fill=(235, 238, 245, 255))
    sheet.save(path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
