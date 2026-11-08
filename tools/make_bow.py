#!/usr/bin/env python3
"""A bow: the Slim human's pull-and-release animation, with a bow in hand (see make_slim.py).

Four frames in both facings, like the attack, and held to the same conventions: the left hand is the
strike hand (here it holds the bow out ahead), the body turns into the movement and leans with it, and
the figure stands on the ground row. The frames:

    1  ready      undrawn, leaning in and looking down: the bow held low and forward, the string slack, an arrow nocked
    2  draw       the bow raised in an arc to the eyeline, the string pulled back to the cheek
    3  release    the string let go: the drawing hand flies back and the body recoils
    4  hold       the bow stays out, dropped a little, the drawing hand relaxing

    python3 tools/make_bow.py --model previews/bow-3d.png      look at the 3D model first

Model space is the humanoid's: x forward, y up, z to the figure's right, one unit about a pixel.
"""
import argparse
import importlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402
from creature import part  # noqa: E402
from humanoid import Humanoid, pose  # noqa: E402
from assetkit import GROUND_ROW  # noqa: E402

BOW_HALF = 8.6                   # grip to tip, in pixels: a bow about as tall as the figure's head and shoulders and more
ARROW_LENGTH = 10.5
RAMPS = {
    'bow': ('f', 'g', 'w', 'x'),          # twisted dark bark, like the other wooden weapons
    'string': ('t', 'r', 'q', 'p'),       # a pale spectral thread, bright enough to read against the dark limbs
    'arrow': ('f', 'g', 'w', 'x'),
    'head': ('t', 'q', 'p', 'l'),
    'vane': ('c', 'j', 'i', 'h'),
}


# The bows. Each is the same bow model with its own size, curve, tips and colours; `bend` scales how far the limbs curve back, `flare` how far the
# tips whip forward again (a recurve), `radius` how thick the limbs are. `grip` and `leaf` add a wrapped grip, a gem and leaf-shaped tips.
SPECS = {
    'longbow': dict(label='Longbow', half=11.6, bend=0.62, flare=0.0, radius=0.7,
                    ramps={'bow': ('g', 'w', 'x', 'x'), 'grip': ('l', 'k', 'w', 'x')}),
    'shortbow': dict(label='Shortbow', half=6.0, bend=1.5, flare=0.0, radius=0.9,
                     ramps={'bow': ('t', 'C', 'c', 'e'), 'grip': ('l', 'k', 'w', 'x')}),         # a bone bow
    'recurve': dict(label='Recurve bow', half=8.8, bend=1.0, flare=3.4, radius=0.8,
                    ramps={'bow': ('f', 'g', 'w', 'x'), 'grip': ('b', 'a', 'g', 'w')}),
    'elven': dict(label='Elven bow', half=10.2, bend=0.9, flare=2.2, radius=0.72, gem=True, leaf=True,
                  ramps={'bow': ('r', 'q', 'p', 'l'), 'grip': ('l', 'k', 'w', 'x'), 'gem': ('y', 'i', 'h', 'u'), 'leaf': ('r', 'A', 'B', 's')}),
}
ACTIVE = {}                      # the bow being drawn, one of SPECS (empty for the original)


def unit(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def segment(a, b, radius, mat, name, grow=0.5):
    """An ellipsoid laid along the 3D line from a to b."""
    d = tuple(b[i] - a[i] for i in range(3))
    length = math.sqrt(sum(c * c for c in d))
    ey = unit(d)
    helper = (1.0, 0.0, 0.0) if abs(ey[0]) < 0.9 else (0.0, 0.0, 1.0)
    ex = unit((ey[1] * helper[2] - ey[2] * helper[1], ey[2] * helper[0] - ey[0] * helper[2], ey[0] * helper[1] - ey[1] * helper[0]))
    ez = (ey[1] * ex[2] - ey[2] * ex[1], ey[2] * ex[0] - ey[0] * ex[2], ey[0] * ex[1] - ey[1] * ex[0])
    R = [[ex[i], ey[i], ez[i]] for i in range(3)]          # columns are the ellipsoid's own axes
    mid = tuple((a[i] + b[i]) / 2 for i in range(3))
    return part(mid, (radius, length / 2 + grow, radius), mat, name, R)


def bow(j, p):
    """The bow in the left hand, strung to the right. `draw` is how far the string is pulled."""
    grip = j['hand_L']
    nock_hand = j['hand_R']
    along = unit((grip[0] - nock_hand[0], 0.0, grip[2] - nock_hand[2]))       # the way it is aimed, level
    back = (-along[0], 0.0, -along[2])
    pull = p.get('draw', 0.0)
    half = ACTIVE.get('half', BOW_HALF)
    bend = p.get('bend', 1.0 + 2.6 * pull) * ACTIVE.get('bend', 1.0)         # how far the tips curve back
    flare = ACTIVE.get('flare', 0.0)
    thick = ACTIVE.get('radius', 0.8)
    parts = []
    # the limbs: an arc from tip to tip through the grip, belly to the front
    count = 9
    arc = []
    for i in range(count + 1):
        t = -1 + 2 * i / count
        off = bend * t * t - flare * max(0.0, (abs(t) - 0.6) / 0.4) ** 2        # a recurve's tips whip forward again
        arc.append(tuple(grip[k] + (0.0, t * half, 0.0)[k] + back[k] * off for k in range(3)))
    for i in range(count):
        t = -1 + 2 * (i + 0.5) / count
        radius = (0.95 - 0.45 * abs(t) + (0.35 if abs(t) < 0.12 else 0)) * thick
        parts.append(segment(arc[i], arc[i + 1], radius, 'grip' if 'grip' in ACTIVE.get('ramps', {}) and abs(t) < 0.16 else 'bow', 'bow', grow=0.9))
    tips = (arc[0], arc[-1])
    if ACTIVE.get('gem'):
        parts.append(part((grip[0] - along[0] * 0.9, grip[1] + 0.2, grip[2] - along[2] * 0.9), (0.9, 0.9, 0.9), 'gem', 'gem'))
    if ACTIVE.get('leaf'):
        for tip, sign in ((arc[0], -1), (arc[-1], 1)):
            beyond = (tip[0], tip[1] + sign * 2.4, tip[2])
            parts.append(segment(tip, beyond, 0.9, 'leaf', 'leaf', grow=0.5))
    mid_tips = tuple((tips[0][k] + tips[1][k]) / 2 for k in range(3))
    # the string: tip to the nock and nock to the other tip (straight if it is not held)
    nock = tuple(nock_hand[k] + (0.0, 0.2, 0.0)[k] for k in range(3)) if p.get('held', True) else mid_tips
    for a, b in ((tips[0], nock), (nock, tips[1])):
        parts.append(segment(a, b, 0.32, 'string', 'string', grow=0.2))
    if p.get('arrow', False):
        tip = tuple(nock[k] + along[k] * ARROW_LENGTH for k in range(3))
        parts.append(segment(nock, tip, 0.35, 'arrow', 'arrow', grow=0.2))
        head_a = tuple(nock[k] + along[k] * (ARROW_LENGTH - 1.2) for k in range(3))
        parts.append(segment(head_a, tuple(tip[k] + along[k] * 0.9 for k in range(3)), 0.65, 'head', 'head', grow=0.3))
    return parts


# The four frames, one set of numbers for both facings to begin with. The body is turned side-on
# (twist) so the left shoulder points where the bow is aimed, and the head turns back to look along it.
def frames():
    return [
        # undrawn, leaning into it, looking down: the bow out low and forward, the string slack, the other hand reaching for it
        pose(pitch=-3, lift=-0.7, twist=-62, head_yaw=60, head_pitch=-22, spread=0.8, sway=1.8,
             hands={'L': (4.8, -1.8), 'R': (3.4, -1.6)}, feet={'L': (3.0, 0), 'R': (-2.6, 0)}, draw=0.0, bend=1.0, held=False, arrow=True),
        # raised in an arc to the eyeline, the string drawn back to the cheek
        pose(pitch=3, lift=-0.9, twist=-66, head_yaw=60, head_pitch=2, spread=1.5, sway=-0.2,
             hands={'L': (4.6, 4.6), 'R': (0.6, 4.0)}, feet={'L': (3.2, 0), 'R': (-2.8, 0)}, draw=1.0, arrow=True),
        # let go: the drawing hand flies back, the body recoils, the bow stays up
        pose(pitch=9, lift=-0.5, twist=-58, head_yaw=56, head_pitch=3, spread=1.8, sway=-1.8, fwd=-0.9,
             hands={'L': (5.0, 4.4), 'R': (-2.4, 4.2)}, feet={'L': (3.0, 0), 'R': (-3.2, 0)}, draw=0.0, bend=0.5, held=False),
        # the bow holds out, dropped a little, the other hand coming down
        pose(pitch=3, lift=-0.7, twist=-60, head_yaw=58, head_pitch=0, spread=1.2, sway=0.2,
             hands={'L': (5.0, 2.9), 'R': (0.3, 0.2)}, feet={'L': (3.0, 0), 'R': (-2.6, 0)}, draw=0.0, bend=1.0, held=False),
    ]


CREATURE = Humanoid('slim', ramps=dict(make_slim.CREATURE.ramps, **RAMPS), body=make_slim.CREATURE.body,
                    accessories=bow, poses={'bow': frames()})
def with_bow(creature):
    """The same person (clothes, hair, build, grid) with the bow poses added, and nothing in the hands."""
    import copy
    person = copy.copy(creature)
    person.poses = dict(creature.poses, bow=frames())
    return person


# The slim human alone, for the animation asset and for drawing the bow: the same poses, nothing in the hands.
PERSON = with_bow(make_slim.CREATURE)
WEAPON_CELL = 48


def build_frames(person=None, spec=None):
    """{'person': {facing: 4 frames of 32 x 32}, 'bow': {facing: 4 frames of 48 x 48}} as colour-role rows.

    The bow is drawn on its own in the weapon cell, with the person's grid inside it 8 pixels in, so laid
    over the person's matching frame (behind them) it is in their hands. Each frame is moved to the ground
    row for the person, and the bow moves with it.
    """
    import creature as cr
    import conventions
    out = {'person': {}, 'bow': {}}
    person = person or PERSON
    ACTIVE.clear()
    ACTIVE.update(SPECS[spec] if spec else {})
    ramps = dict(RAMPS, **ACTIVE.get('ramps', {}))
    cr.TALL_EYES = person.tall_eyes             # the same eyes as the person's own sprites
    for facing in ('NE', 'SE'):
        origin = cr.calibrate(person, facing)
        people, bows = [], []
        for pose_ in person.poses['bow']:
            parts, decals = person.place(pose_)
            lines = cr.render_frame(parts, decals, facing, origin, person.ramps, person.scale)
            rows = [y for y, line in enumerate(lines) if line.strip('.')]
            dy = conventions.GROUND_ROW - max(rows)
            people.append(cr.shift_rows(lines, dy))
            bow_parts = bow(person.last_joints, pose_)                # (place() just set the joints the bow follows)
            old = cr.CELL
            cr.CELL = WEAPON_CELL
            try:
                bows.append(cr.render_frame(bow_parts, [], facing, (origin[0] + 8, origin[1] + 8 + dy), ramps, person.scale))
            finally:
                cr.CELL = old
        out['person'][facing], out['bow'][facing] = people, bows
    ACTIVE.clear()
    return out


def problems(person):
    """The conventions checked on the person's frames, as an attack: ground, outline, weight, height."""
    import conventions
    return conventions.check_base('slim', {f'bow{f}': frames for f, frames in person.items()}, 'humanoid')



def render_sheet(size=330):
    from PIL import Image, ImageDraw
    import preview3d as pv
    placed = [CREATURE.place(f)[0] for f in CREATURE.poses['bow']]
    fit = []
    for parts in placed:
        for q in parts:
            r = max(q['r'])
            fit += [(q['c'][0] + dx * r, q['c'][1] + dy * r, q['c'][2] + dz * r) for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    names = ('undrawn', 'draw', 'release', 'hold')
    sheet = Image.new('RGBA', (size * 4, size * 2 + 40), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for row, view in enumerate(('SE', 'NE')):
        for i, (f, parts) in enumerate(zip(CREATURE.poses['bow'], placed)):
            _, decals = CREATURE.place(f)
            tile = pv.render_view(parts, decals, CREATURE.ramps, pv.VIEWS[view], size, fit_points=fit)
            sheet.alpha_composite(tile, (i * size, 20 + row * (size + 20)))
            draw.text((i * size + 6, 5 + row * (size + 20)), f'{view}  {i + 1} {names[i]}', fill=(235, 238, 245, 255))
    return sheet


def render_variants(size=300):
    """The four new bows in 3D: undrawn, drawn and held, from the SE and the NE, each with the person's hands on it."""
    from PIL import Image, ImageDraw
    import preview3d as pv
    names = list(SPECS)
    frames_ = (1, 3)               # draw, hold
    sheet = Image.new('RGBA', (size * len(names), (size + 20) * 2 * len(frames_)), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for col, name in enumerate(names):
        ACTIVE.clear()
        ACTIVE.update(SPECS[name])
        import copy
        person = copy.copy(CREATURE)                 # the model that carries the bow
        person.ramps = dict(CREATURE.ramps, **SPECS[name]['ramps'])
        placed = [person.place(person.poses['bow'][f])[0] for f in frames_]
        fit = []
        for parts in placed:
            for q in parts:
                r = max(q['r'])
                fit += [(q['c'][0] + dx * r, q['c'][1] + dy * r, q['c'][2] + dz * r) for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
        row = 0
        for view in ('SE', 'NE'):
            for f, parts in zip(frames_, placed):
                _, decals = person.place(person.poses['bow'][f])
                tile = pv.render_view(parts, decals, person.ramps, pv.VIEWS[view], size, fit_points=fit)
                sheet.alpha_composite(tile, (col * size, 20 + row * (size + 20)))
                draw.text((col * size + 6, 5 + row * (size + 20)), f"{SPECS[name]['label']}  {view}  {'draw' if f == 1 else 'hold'}", fill=(235, 238, 245, 255))
                row += 1
    ACTIVE.clear()
    return sheet


def write_sprites(out, built):
    from PIL import Image
    import creature as cr
    out.mkdir(parents=True, exist_ok=True)
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in cr.ep.ROLES}
    for kind, cell in (('person', 32), ('bow', WEAPON_CELL)):
        for facing, frames in built[kind].items():
            img = Image.new('RGBA', (cell * len(frames), cell), (0, 0, 0, 0))
            px = img.load()
            for f, lines in enumerate(frames):
                for y, line in enumerate(lines):
                    for x, ch in enumerate(line):
                        if ch != '.':
                            px[f * cell + x, y] = (*rgb[ch], 255)
            name = f'slim-bow{facing}.png' if kind == 'person' else f'bow-bow{facing}.png'
            img.save(out / name)


def write_base_poses(who, creature):
    """Add NAME-bowNE.png and NAME-bowSE.png (4 frames of 32 x 32) to a base's sprite folder."""
    import creature as cr
    built = build_frames(with_bow(creature))
    folder = Path(__file__).resolve().parent.parent / 'sprites' / who
    folder.mkdir(parents=True, exist_ok=True)
    problems_ = problems(built['person'])
    for p_ in problems_:
        print('  ' + p_)
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in cr.ep.ROLES}
    from PIL import Image
    for facing, frames in built['person'].items():
        img = Image.new('RGBA', (32 * len(frames), 32), (0, 0, 0, 0))
        px = img.load()
        for f, lines in enumerate(frames):
            for y, line in enumerate(lines):
                for x, ch in enumerate(line):
                    if ch != '.':
                        px[f * 32 + x, y] = (*rgb[ch], 255)
        img.save(folder / f'{who}-bow{facing}.png')
    return problems_


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, help='write the 3D preview of the four frames here instead of making sprites')
    parser.add_argument('--bases', help='add the bow poses to these bases\' sprite folders, e.g. human,slim,ninja')
    parser.add_argument('--variants', type=Path, help='write the 3D preview of the new bows here')
    parser.add_argument('--out', type=Path, help='write the sprites (the person and the bow strips) here, e.g. previews/bow')
    args = parser.parse_args()
    if args.model:
        args.model.parent.mkdir(parents=True, exist_ok=True)
        render_sheet().save(args.model)
        print(f'3D preview of the bow animation -> {args.model}; no sprites were made')
        return
    if args.variants:
        args.variants.parent.mkdir(parents=True, exist_ok=True)
        render_variants().save(args.variants)
        print(f'3D preview of the new bows -> {args.variants}; no sprites were made')
        return
    if args.bases:
        import importlib
        for who in args.bases.split(','):
            write_base_poses(who, getattr(importlib.import_module('make_' + who.replace('-', '_')), 'CREATURE'))
            print(f'{who}: bow poses -> sprites/{who}')
        return
    if not args.out:
        parser.error('say --out for the sprites, or --model to see the 3D model first')
    built = build_frames()
    for p in problems(built['person']):
        print('  ' + p)
    write_sprites(args.out, built)
    print(f'wrote the person and the bow -> {args.out}')

# Every person built from the humanoid model, each a module make_<name>: the bow draw is made for all of them.
PEOPLE = ('human', 'slim', 'human-sleek', 'slim-sleek', 'ninja', 'ranger', 'verdant', 'fey', 'golden-mushroom', 'bones', 'paladin', 'blossom', 'earthbender')


def build_assets():
    # The bow: the slim human's pull-and-release as an animation, and the bow itself as a weapon strip that
    # goes behind it. Built apart, so either can change; they are laid over each other frame by frame.
    bow_assets = []
    for who in PEOPLE:
        creature = getattr(importlib.import_module('make_' + who.replace('-', '_')), 'CREATURE')
        bow = build_frames(with_bow(creature))
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
                    'w': WEAPON_CELL, 'h': WEAPON_CELL, 'cols': 4, 'rows': 1, 'fps': 4,
                    'anchor': {'x': WEAPON_CELL // 2, 'y': WEAPON_CELL},
                    'frames': bow['bow'][facing],
                })
            # The other bows: the same model with its own size, curve, tips and colours, drawn with the same animation.
            for spec_id, spec in SPECS.items():
                other = build_frames(with_bow(creature), spec=spec_id)
                for facing in ('NE', 'SE'):
                    bow_assets.append({
                        'id': f'weapon-{spec_id}-{facing.lower()}', 'label': f"{spec['label']} {facing}", 'category': 'Weapons', 'kind': 'animation',
                        'place': 'none', 'weapon': spec['label'], 'facing': facing, 'animation': 'bow-draw',
                        'w': WEAPON_CELL, 'h': WEAPON_CELL, 'cols': 4, 'rows': 1, 'fps': 4,
                        'anchor': {'x': WEAPON_CELL // 2, 'y': WEAPON_CELL},
                        'frames': other['bow'][facing],
                    })
    return bow_assets


if __name__ == '__main__':
    main()
