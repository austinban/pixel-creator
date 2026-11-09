#!/usr/bin/env python3
"""The rat king: an elite creature, a great bloody heap of rats that has grown into one. Built like the rat (see make_rat.py and creature.py), but much bigger.

Elite means bigger than an ordinary creature and still on ONE ground tile: it is drawn in a 64 x 64 cell (twice a person's), taller and wider than the tile, with the middle
of its tile at ELITE_ANCHOR on the ground and its lowest row on ELITE_GROUND.

    a big bulbous rat for the body, with a LARGE rat face: a long snout, big buck teeth, a wet pink nose, whiskers, round pink ears and red glowing eyes
    five smaller rats fused into its flanks, rump and back: a head and shoulders each, with their own snouts, ears and eyes
    six long pink tails, knotted and curling up behind it, that sway as it moves
    blood: dark red on the fur, round the maw, on the claws, and a raw patch or two

It has the same actions as everyone else (charging, a four-frame attack, release, damage, weak, dead and an eight-frame walk, both facings).

    python3 tools/make_rat_king.py --model previews/rat-king-3d.png         look at the 3D model first
    python3 tools/make_rat_king.py sprites/rat-king [--preview sheet.png]
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402
import creature as cr  # noqa: E402
import extract_poses as ep  # noqa: E402
from creature import add, bone, deg, mm, mv, part, rx, ry, rz, sub, two_bone  # noqa: E402

ELITE_CELL = conventions.ELITE_CELL
ELITE_ANCHOR = conventions.ELITE_ANCHOR        # the middle of its one ground tile, on the ground
ELITE_GROUND = conventions.ELITE_GROUND        # the lowest painted row of a standing frame: the tile's bottom point is 8 rows below the anchor
CANVAS = 96                    # drawn on a bigger canvas, then put on the cell, so a reaching frame is not cut off on the way
SCALE = 1.42                   # pixels to a model unit

RAMPS = {
    'fur': ('p', 'l', 'k', 'w'),          # the king: steel, lavender, indigo, grape
    'furB': ('f', 'u', 'w', 'x'),         # the rats grown into it: mauve
    'furC': ('l', 'k', 'w', 'x'),         # and darker
    'pink': ('c', 'e', 'f', 'g'),         # ears, paws and tails
    'cream': ('t', 'C', 'c', 'e'),        # teeth and whiskers
    'nose': ('j', 'j', 'i', 'h'),         # a wet pink nose
    'eye': ('j', 'j', 'j', 'i'),          # glowing red
    'glint': ('t', 't', 'C', 'C'),        # the white dot in each eye
    'blood': ('h', 'x', 'x', 'x'),        # dark red, drying
    'raw': ('e', 'i', 'h', 'x'),          # raw red flesh
    'maw': ('i', 'h', 'x', 'x'),          # the dark red inside of the mouth
    'claw': ('c', 'e', 'h', 'x'),         # claws, rusted with blood
    'dark': ('w', 'x', 'x', 'x'),         # shut eyes
}

PIVOT = (0.0, 8.0, 0.0)
NECK = (6.0, 12.0, 0.0)
HINGE = (13.4, 9.6, 0.0)
UPPER, LOWER = 3.4, 4.2
HIPS = {'FL': (3.6, 6.0, -4.2), 'FR': (3.6, 6.0, 4.2), 'HL': (-4.6, 6.0, -4.6), 'HR': (-4.6, 6.0, 4.6)}
KNEE_FORWARD = {'FL': False, 'FR': False, 'HL': True, 'HR': True}

# The rats grown into it: (where its head is on the king, yaw, pitch, size, its fur, which side it is on).
MINIS = [
    ((2.6, 8.4, -7.0), -62, 4, 1.15, 'furB'),        # the left flank, looking out and forward
    ((-1.4, 9.6, 7.0), 70, -6, 1.25, 'furC'),         # the right flank, looking out
    ((-2.2, 15.6, 2.6), 14, 28, 1.0, 'furB'),         # up on the back, looking forward and up
    ((-6.8, 7.0, -6.2), -130, 6, 1.0, 'furC'),        # the left rump, looking back
    ((-7.8, 10.6, 5.2), 128, 12, 0.95, 'furB'),       # the right rump, looking back
]

# The tails: (where it starts, its heading, how it starts to rise, where it ends up, how far it wags, its phase, how many segments).
TAILS = [
    ((-10.2, 8.4, 0.0), 0, 4, 58, 26, 0.0, 7),
    ((-10.0, 7.2, 1.4), 30, 8, 66, 30, 1.3, 7),
    ((-10.0, 7.2, -1.4), -30, 8, 62, 30, 2.5, 7),
    ((-9.0, 7.0, 6.0), 64, 2, 40, 24, 3.6, 6),
    ((-9.2, 6.6, -6.0), -64, 2, 44, 24, 4.8, 6),
    ((-6.4, 14.0, -1.6), -128, 14, 72, 22, 5.9, 6),
]


def mini_rat(c, yaw, pitch, size, fur, n, p):
    """A smaller rat grown into the king: its head and shoulders, in the king's own frame."""
    wig = p['wig']
    yaw = yaw + 9 * math.sin(wig + n * 1.7)
    pitch = pitch + 7 * math.sin(wig * 1.0 + n * 0.9) + p['lunge']
    R = mm(ry(-deg(yaw)), rz(deg(pitch)))
    k = size

    def at(x, y, z):
        return add(c, mv(R, (x * k, y * k, z * k)))

    out = [
        part(at(-2.4, -1.2, 0), (3.6 * k, 3.0 * k, 2.8 * k), fur, f'm{n}body', R),
        part(at(0, 0, 0), (2.4 * k, 2.1 * k, 2.0 * k), fur, f'm{n}head', R),
        part(at(2.7, -0.5, 0), (2.1 * k, 1.25 * k, 1.25 * k), fur, f'm{n}head', R),
        part(at(4.5, -0.4, 0), (0.75 * k, 0.7 * k, 0.8 * k), 'nose', f'm{n}head', R),
    ]
    for side in (-1, 1):
        out.append(part(at(-0.5, 2.0, side * 1.5), (1.15 * k, 1.1 * k, 0.4 * k), 'pink', f'm{n}ear{side}', mm(R, rx(side * deg(24)))))
        if p['eyes'] == 'open':
            out.append(part(at(1.3, 0.75, side * 1.45), (0.62 * k, 0.72 * k, 0.5 * k), 'eye', f'm{n}eye{side}', R))
            out.append(part(at(1.75, 1.1, side * 1.3), (0.26 * k, 0.26 * k, 0.26 * k), 'glint', f'm{n}eye{side}', R))
        else:
            out.append(part(at(1.3, 0.75, side * 1.5), (0.7 * k, 0.2 * k, 0.5 * k), 'dark', f'm{n}eye{side}', R))
        out.append(part(at(3.9, -1.35, side * 0.4), (0.32 * k, 0.75 * k, 0.28 * k), 'cream', f'm{n}tooth{side}', R))
    if n in (0, 2):
        out.append(part(at(2.6, -1.3, 0), (1.5 * k, 0.5 * k, 0.9 * k), 'blood', f'm{n}maw', R))
    return out


def tail_parts(p):
    """The tails: long thin segments laid end to end from the rump and the rats on it, rising and curling and swaying as they go."""
    dp, wag, phase = p['tail']
    out = []
    for i, (root, yaw0, a1, a2, amp, ph, count) in enumerate(TAILS):
        pos = root
        step = 2.1
        for s in range(count):
            t = s / (count - 1)
            pitch = a1 + (a2 - a1) * t + dp
            yaw = yaw0 * (1 - 0.35 * t) + (amp * 0.5 + wag) * math.sin(math.pi * t + ph + phase)
            R = mm(ry(-deg(yaw)), rz(-deg(pitch)))
            d = mv(R, (-1.0, 0.0, 0.0))
            r = 0.95 - 0.09 * s
            out.append(part(add(pos, tuple(x * step / 2 for x in d)), (step / 2 + 0.45, r, r), 'pink', f'tail{i}', R))
            pos = add(pos, tuple(x * step for x in d))
    return out


def anatomy(p):
    body, head, jaw_parts = [], [], []
    # the big bulbous body: a rump, a heavy chest, a hump up on the shoulders
    body += [
        part((-3.8, 8.0, 0), (7.4, 7.0, 6.2), 'fur', 'body'),
        part((2.6, 9.0, 0), (6.4, 7.4, 5.8), 'fur', 'body'),
        part((-0.4, 12.4, 0), (5.4, 4.0, 4.4), 'fur', 'hump'),
        part((5.4, 6.2, 0), (2.6, 3.4, 2.6), 'furC', 'belly'),
        part((5.0, 11.8, 0), (3.4, 3.4, 3.4), 'fur', 'neck'),
        # blood on the king: a spattered shoulder, a dark stain down the chest, a raw patch on the back
        part((3.6, 11.4, 5.2), (1.3, 3.4, 0.7), 'blood', 'stain1', rx(deg(-28))),
        part((6.4, 8.0, 3.9), (1.0, 3.0, 0.6), 'blood', 'stain2', rx(deg(-30))),
        part((6.2, 8.6, -3.9), (1.2, 3.2, 0.6), 'blood', 'stain3', rx(deg(30))),
        part((-4.6, 13.8, 0.0), (2.6, 1.3, 3.4), 'raw', 'rawback'),
        part((-6.4, 9.0, 5.6), (2.0, 2.2, 0.9), 'raw', 'rawflank', rx(deg(-35))),
    ]
    # the head: big, round, long snout, a wet nose, buck teeth
    head += [
        part((10.2, 14.4, 0), (5.8, 5.2, 5.0), 'fur', 'head'),
        part((15.6, 12.6, 0), (4.8, 2.9, 2.9), 'furC', 'head'),
        part((20.2, 12.7, 0), (1.7, 1.5, 1.8), 'nose', 'head'),
        part((17.9, 10.4, 1.0), (0.8, 2.0, 0.65), 'cream', 'tooth', rz(deg(-8))),
        part((17.9, 10.4, -1.0), (0.8, 2.0, 0.65), 'cream', 'tooth', rz(deg(-8))),
        part((14.6, 10.5, 0), (4.4, 0.9, 2.4), 'blood', 'gums'),
    ]
    for side in (-1, 1):
        head.append(part((7.6, 19.2, side * 4.4), (3.0, 3.3, 0.85), 'pink', 'ear', mm(rz(-deg(p['ears'][1])), rx(side * deg(p['ears'][0])))))
        if p['eyes'] == 'open':
            head.append(part((13.4, 16.6, side * 3.7), (1.6, 1.9, 1.3), 'eye', 'eyeball'))
            head.append(part((14.45, 17.75, side * 4.3), (0.62, 0.62, 0.62), 'glint', 'eyeball'))      # a white dot, up and forward
        else:
            head.append(part((13.4, 16.6, side * 3.8), (1.7, 0.4, 1.3), 'dark', 'eyeball'))
        # whiskers: three long thin hairs each side, fanned out from the snout
        for k, (yaw, pitch) in enumerate(((14, 10), (34, 0), (54, -12))):
            R = mm(ry(-side * deg(yaw)), rz(deg(pitch)))
            base = (18.2, 12.4, side * 2.3)
            length = 5.2
            c = add(base, mv(R, (length * 0.5, 0.0, 0.0)))
            head.append(part(c, (length * 0.5 + 0.1, 0.55, 0.55), 'cream', f'whisker{side}{k}', R))
    # the lower jaw drops about its hinge: bloody inside, with teeth, and a tongue when it is open
    jaw = rz(-deg(p['mouth']))
    for c, r, mat, nm in (((16.6, 8.6, 0), (4.2, 1.5, 2.4), 'furC', 'jaw'), ((16.2, 9.6, 0), (3.8, 0.8, 2.0), 'maw', 'jawin'),
                          ((19.6, 9.6, 0.9), (0.45, 1.0, 0.35), 'cream', 'jawtooth'), ((19.6, 9.6, -0.9), (0.45, 1.0, 0.35), 'cream', 'jawtooth2')):
        jaw_parts.append(part(add(HINGE, mv(jaw, sub(c, HINGE))), r, mat, nm, jaw))
    if p['mouth'] > 14:
        jaw_parts.append(part(add(HINGE, mv(jaw, sub((16.0, 9.2, 0), HINGE))), (2.8, 0.6, 1.4), 'raw', 'tongue', jaw))
    return body, head, jaw_parts


def place(p):
    body, head, jaw_parts = anatomy(p)
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)
    h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_head(pt):
        return on_body(add(NECK, mv(h, sub(pt, NECK))))

    placed = []
    extras = []
    for n, (c, yaw, pitch, size, fur) in enumerate(MINIS):
        extras += mini_rat(c, yaw, pitch, size, fur, n, p)
    for q in body + tail_parts(p) + extras:
        placed.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in head + jaw_parts:
        placed.append(dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))))

    for name, hip in HIPS.items():
        hip_w = on_body(hip)
        spec = p['feet'].get(name, (0.0, 0.0))
        if len(spec) == 2:
            knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), UPPER, LOWER, KNEE_FORWARD[name])
            toe = (foot[0] + 0.9, foot[1] + 0.8)
        else:
            a1, a2 = deg(spec[2]), deg(spec[3])
            knee = (hip[0] + UPPER * math.sin(a1), hip[1] - UPPER * math.cos(a1))
            foot = (knee[0] + LOWER * math.sin(a1 + a2), knee[1] - LOWER * math.cos(a1 + a2))
            toe = (foot[0] + 0.9, foot[1] + 0.8)
            knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
        z = hip_w[2]
        hind = name.startswith('H')
        placed.append(bone(hip_w[:2], knee, z, 2.6 if hind else 2.2, 'fur', 'leg' + name))
        placed.append(bone(knee, foot, z, 1.8, 'fur', 'leg' + name, grow=0.4))
        placed.append(part((toe[0], toe[1], z), (2.4, 1.1, 2.0), 'pink', 'leg' + name))
        for dz in (-0.9, 0.0, 0.9):                                   # the claws, bloody
            placed.append(part((toe[0] + 2.0, toe[1] - 0.1, z + dz), (0.9, 0.35, 0.35), 'claw', 'claw' + name))
    return placed, []


# --- poses ---------------------------------------------------------------------------------
BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, head_pitch=0, head_yaw=0, mouth=5, ears=(18, 8), tail=(0, 0, 0),
            feet={}, eyes='open', wig=0.0, lunge=0.0)


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def lumber(k, n=8):
    """A heavy, rolling walk: short strides, the whole heap swaying and the rats on it nodding, the tails swinging."""
    phase = 2 * math.pi * k / n
    feet = {}
    for name, offset in (('FL', 0), ('HR', 0), ('FR', math.pi), ('HL', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:
            dx, lift = 2.2 * (1 - 2 * s / math.pi), 0.0
        else:
            u = (s - math.pi) / math.pi
            dx, lift = -2.2 + 4.4 * u, 1.8 * math.sin(math.pi * u)
        feet[name] = (dx, lift)
    return pose(feet=feet, lift=0.4 * math.cos(2 * phase) - 0.1, body_pitch=2.0 * math.sin(2 * phase),
                head_pitch=-2.5 * math.sin(2 * phase), tail=(0, 8, phase), mouth=6 + 3 * math.sin(phase), wig=phase)


STAND = pose()
POSES = {
    'charging': [pose(body_pitch=-4, lift=-0.8, head_pitch=10, mouth=10, ears=(22, 4), tail=(6, 6, 0.6), wig=0.5,
                      feet={'FL': (1.4, 0), 'FR': (1.4, 0), 'HL': (-0.8, 0), 'HR': (-0.8, 0)})],
    # rears up, then slams down maul-ing
    'attack': [
        pose(body_pitch=10, lift=0.4, fwd=-1.6, head_pitch=14, mouth=18, ears=(26, 18), tail=(14, 8, 1.0), wig=1.0, lunge=-10,
             feet={'FL': (0.4, 2.4), 'FR': (0.6, 2.8), 'HL': (-1.0, 0), 'HR': (-1.0, 0)}),
        pose(body_pitch=24, lift=1.8, fwd=-2.4, head_pitch=24, mouth=42, ears=(30, 26), tail=(26, 6, 2.0), wig=2.0, lunge=-18,
             feet={'FL': (2.0, 6.0), 'FR': (2.6, 6.6), 'HL': (-1.2, 0), 'HR': (-1.2, 0)}),
        pose(body_pitch=-12, lift=0.2, fwd=3.6, head_pitch=-22, mouth=44, ears=(30, 30), tail=(-8, 10, 3.0), wig=3.0, lunge=22,
             feet={'FL': (3.0, 0.8), 'FR': (3.6, 0.4), 'HL': (-1.2, 0), 'HR': (-1.0, 0)}),
        pose(body_pitch=2, lift=0.1, fwd=0.9, head_pitch=2, mouth=10, tail=(0, 8, 4.0), wig=4.0, lunge=6,
             feet={'FL': (0.8, 0), 'FR': (1.2, 0), 'HL': (-0.8, 0), 'HR': (-1.0, 0)}),
    ],
    # reared up to squeal, every rat shrieking
    'release': [pose(body_pitch=20, lift=1.0, head_pitch=16, mouth=44, ears=(14, 26), eyes='shut', tail=(30, 14, 1.8), wig=1.6, lunge=-16,
                     feet={'FL': (2.0, 5.0), 'FR': (2.4, 5.6), 'HL': (-1.2, 0), 'HR': (-1.2, 0)})],
    'damage': [pose(body_pitch=7, fwd=-1.8, head_pitch=20, head_yaw=16, mouth=22, ears=(48, 40), eyes='shut', tail=(-6, 16, 2.2), wig=2.6, lunge=14,
                    feet={'FL': (1.6, 0), 'FR': (1.4, 0), 'HL': (-1.6, 0), 'HR': (-1.4, 0)})],
    'weak': [pose(body_pitch=-3, lift=-2.6, head_pitch=-26, mouth=4, ears=(58, 4), eyes='shut', tail=(-30, 2, 0.4), wig=0.2, lunge=16,
                  feet={'FL': (0.6, 0), 'FR': (0.6, 0), 'HL': (-0.4, 0), 'HR': (-0.4, 0)})],
    # a collapsed heap on its side, the tails splayed
    'dead': [pose(roll=-90, lift=-3.0, head_pitch=-10, mouth=20, ears=(50, 14), eyes='shut', tail=(-36, 28, 0.3), wig=0.0, lunge=10,
                  feet={'FL': (0, 0, 24, -6), 'FR': (0, 0, 14, -4), 'HL': (0, 0, -22, 8), 'HR': (0, 0, -14, 5)})],
    'walking': [lumber(k) for k in range(8)],
}


class RatKing:
    name = 'rat-king'
    kind = 'elite'
    airborne = set()
    ramps = RAMPS
    scale = 1.0
    stand = STAND
    poses = POSES

    @staticmethod
    def place(p):
        return place(p)


CREATURE = RatKing()


# --- the sprites -----------------------------------------------------------------------------
def shift_into_cell(rows, dx, dy):
    """A frame from the big canvas moved by whole pixels into the elite cell; what is pushed off the edge is lost."""
    blank = '.' * ELITE_CELL
    out = []
    for y in range(ELITE_CELL):
        sy = y - dy
        if 0 <= sy < len(rows):
            row = ''.join(rows[sy][x - dx] if 0 <= x - dx < len(rows[sy]) else '.' for x in range(ELITE_CELL))
        else:
            row = blank
        out.append(row)
    return out


def draw(p, facing, origin):
    parts, decals = place(p)
    return cr.render_frame(parts, decals, facing, origin, RAMPS, SCALE)


def build_frames():
    """Every action's frames in both facings, in the 64 x 64 cell with the feet on the ground row."""
    old = cr.CELL
    cr.CELL = CANVAS
    cr.TALL_EYES, cr.EYE_WHITE, cr.EYE_COLOUR, cr.EYE_PUPIL = False, None, None, None
    origin = (CANVAS / 2, 72.0)
    out = {}
    try:
        for facing in ('NE', 'SE'):
            stand = draw(STAND, facing, origin)
            xs = [x for r in stand for x, ch in enumerate(r) if ch != '.']
            stand_dx = round(ELITE_ANCHOR[0] - (min(xs) + max(xs) + 1) / 2)
            for action, (_, _) in {a: (c, r) for a, f, c, r in ep.POSES if f == facing}.items():
                frames = []
                for p in POSES[action]:
                    rows = draw(p, facing, origin)
                    ys = [y for y, r in enumerate(rows) if r.strip('.')]
                    xs = [x for r in rows for x, ch in enumerate(r) if ch != '.']
                    dx = round(ELITE_ANCHOR[0] - (min(xs) + max(xs) + 1) / 2) if action == 'dead' else stand_dx
                    target = ELITE_GROUND - 3 if action == 'dead' else ELITE_GROUND
                    frames.append(shift_into_cell(rows, dx, target - max(ys)))
                out[action + facing] = frames
    finally:
        cr.CELL = old
    return out


def check_elite(frames_by_pose):
    """Problems with the elite's frames: the colour ramps, then size, the cell margin, the outline and the ground row (conventions.check_elite)."""
    return conventions.check_ramps(RAMPS, 'rat-king') + conventions.check_elite('rat-king', frames_by_pose)


def write_sprites(folder, frames, preview=None):
    from PIL import Image
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    Path(folder).mkdir(parents=True, exist_ok=True)
    sheets = []
    for action, facing, cols, rows in ep.POSES:
        fr = frames[action + facing]
        img = Image.new('RGBA', (cols * ELITE_CELL, rows * ELITE_CELL), (0, 0, 0, 0))
        for index, lines in enumerate(fr):
            ox, oy = (index % cols) * ELITE_CELL, (index // cols) * ELITE_CELL
            for y, line in enumerate(lines):
                for x, ch in enumerate(line):
                    if ch != '.':
                        img.putpixel((ox + x, oy + y), rgb[ch] + (255,))
        img.save(Path(folder) / f'rat-king-{action}{facing}.png')
        sheets.append(img)
    if preview:
        scale = 3
        width = max(i.width for i in sheets) * scale
        height = sum(i.height * scale + 4 for i in sheets)
        contact = Image.new('RGBA', (width, height), (60, 64, 74, 255))
        y = 0
        for img in sheets:
            contact.alpha_composite(img.resize((img.width * scale, img.height * scale), Image.NEAREST), (0, y))
            y += img.height * scale + 4
        contact.save(preview)


def main():
    parser = argparse.ArgumentParser(description='The rat king, an elite creature.')
    parser.add_argument('out', type=Path, nargs='?', help='folder for the sprite sheets, e.g. sprites/rat-king')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--pose', default='charging')
    parser.add_argument('--frame', type=int, default=0)
    parser.add_argument('--views')
    parser.add_argument('--preview', type=Path, help='also write one contact sheet of every pose here')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.model:
        import preview3d
        views = args.views.split(',') if args.views else None
        args.model.parent.mkdir(parents=True, exist_ok=True)
        preview3d.render_sheet(CREATURE, preview3d.pick_pose(CREATURE, args.pose, args.frame), views).save(args.model)
        print(f'3D preview of the rat king ({args.pose}, frame {args.frame + 1}) -> {args.model}; no sprites were made')
    elif args.out:
        frames = build_frames()
        problems = check_elite(frames)
        if problems and not args.force:
            print('the rat king breaks the elite rules, so nothing was written (--force to write anyway):', file=sys.stderr)
            for q in problems:
                print('  ' + q, file=sys.stderr)
            sys.exit(1)
        write_sprites(args.out, frames, args.preview)
        print(f'wrote the sheets -> {args.out}' + (f' (with {len(problems)} problems, forced)' if problems else ''))
    else:
        parser.error('say where to write the sprites, or use --model to see the 3D model first')


if __name__ == '__main__':
    main()
