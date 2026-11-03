#!/usr/bin/env python3
"""The scorpion emperor: a final boss, a man's body rising from the front of a giant scorpion (see make_scorpion.py and creature.py).

Four ground squares across, so it is drawn in a bigger cell (BOSS_CELL) on a 2 x 2 footprint instead of a single tile's. It is
built from the same kind of parts as the other scorpions: a long armoured body of dark plates, a huge tail curling over the back to
a barbed stinger, two great pincers, and eight thick, spiked legs. Where the scorpion's head would be, a human torso rises:
bare-chested, long-haired, one arm raised and the other held out, with a gold-bronze shoulder guard and bracers. It has the same
poses and animations as the others: charging, a four-frame attack, release, damage, weak, dead and an eight-frame walk, in both
facings.

    python3 tools/make_emperor.py --model previews/emperor-3d.png        look at the 3D model first
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, deg, mm, mv, part, rx, ry, rz, sub  # noqa: E402
from make_scorpion import bone3  # noqa: E402

RAMPS = {
    'shell': ('f', 'g', 'x', 'w'),       # the carapace: dark orchid-brown down to near black
    'plate': ('e', 'f', 'g', 'x'),       # lighter ridges of armour along it
    'claw': ('e', 'f', 'g', 'x'),
    'leg': ('f', 'g', 'x', 'w'),
    'bone': ('t', 'C', 'c', 'e'),        # the barbs and spikes: pale, like bone
    'skin': ('C', 'b', 'e', 'f'),        # the man's skin
    'hair': ('k', 'w', 'x', 'x'),        # long black hair
    'bronze': ('b', 'a', 'f', 'g'),      # the bracers: darker bronze
    'mouth': ('w', 'x', 'x', 'x'),       # the dark of his open mouth
    'ring': ('t', 't', 't', 'C'),        # a ring of white round each eye
    'gold': ('t', 'd', 'b', 'a'),        # the pauldrons: bright gold
}

PIVOT = (0.0, 3.0, 0.0)
LEG_X = (4.2, 1.2, -2.0, -5.0)
TAIL_ROOT = (-11.6, 7.0, 0.0)
TAIL_SEGMENTS = 9
TAIL_STEP = 2.4
BODY_SCALE = 0.8        # the scorpion's size, against the first sketch
MAN_SCALE = 1.2         # and the man's


def body_parts():
    out = []
    # the cephalothorax: a broad shield, with ridges of lighter armour across it
    out.append(part((3.0, 3.1, 0), (5.0, 2.4, 3.9), 'shell', 'carapace'))
    out.append(part((3.0, 4.3, 0), (4.2, 1.0, 3.1), 'plate', 'carapace'))
    # the abdomen: three long plates, each with a ridge, tapering back and curving up, each one higher and tipped further than
    # the last, so the body rises into the tail
    for i, (x, rr, rise, tilt) in enumerate(((-2.4, (3.9, 2.5, 3.3), 0.4, 5), (-6.3, (3.8, 2.3, 2.9), 1.6, 15), (-9.6, (3.1, 2.0, 2.3), 3.3, 28))):
        R = rz(deg(tilt))
        out.append(part((x, 3.1 - 0.1 * i + rise, 0), rr, 'shell', f'segment{i}', R))
        out.append(part((x + 0.1, 4.6 - 0.2 * i + rise + 0.2 * i, 0), (rr[0] * 0.85, 0.7, rr[2] * 0.55), 'plate', f'ridge{i}', R))
    return out


def tail_parts(p):
    """A huge, thick tail curling up and over the back, narrowing to a barbed stinger with a long hooked barb."""
    a1, a2, sway = p['tail']
    step = TAIL_STEP * p['stretch']
    out, pos = [], TAIL_ROOT
    for i in range(TAIL_SEGMENTS):
        t = i / (TAIL_SEGMENTS - 1)
        pitch = a1 + (a2 - a1) * t
        R = mm(ry(deg(sway * math.sin(math.pi * t))), rz(-deg(pitch)))
        d = mv(R, (-1.0, 0.0, 0.0))
        radius = 1.75 - 0.1 * i
        out.append(part(add(pos, tuple(x * step / 2 for x in d)), (step / 2 + 0.6, radius, radius), 'shell', 'tail', R))
        out.append(part(add(add(pos, tuple(x * step / 2 for x in d)), (0.0, radius * 0.8, 0.0)), (0.45, 0.45, radius * 0.5), 'bone', f'tailspike{i}', R))
        pos = add(pos, tuple(x * step for x in d))
        last = (R, d)
    R, d = last
    bulb = add(pos, tuple(x * 1.3 for x in d))
    out.append(part(bulb, (1.6, 1.3, 1.3), 'shell', 'tail', R))
    for k in range(5):                                    # spikes round the stinger's base
        a = 2 * math.pi * k / 5
        out.append(part(add(bulb, (0.0, 1.1 * math.cos(a), 1.1 * math.sin(a))), (0.3, 0.75, 0.3), 'bone', f'barbspike{k}', mm(R, rx(a))))
    barb = add(bulb, tuple(x * 2.4 for x in d))
    out.append(part(barb, (2.0, 0.55, 0.55), 'bone', 'barb', mm(R, rz(deg(-34)))))
    out.append(part(add(barb, tuple(x * 1.6 for x in d)), (1.1, 0.35, 0.35), 'bone', 'barb', mm(R, rz(deg(-62)))))
    return out


def pincers(on_body, p):
    """Two great pincers: a thick arm of two bones, a heavy palm and two long toothed fingers that open."""
    reach, spread, opening = p['claws']
    out = []
    for side, z in (('L', -1), ('R', 1)):
        shoulder = (6.4, 2.6, z * 2.8)
        elbow = (9.6 + reach * 0.5, 3.0 + (1.6 if side == 'R' else 0) * 0, z * (6.6 + spread))
        wrist = (12.8 + reach, 2.8, z * (5.4 + spread * 0.5))
        s, e, w = on_body(shoulder), on_body(elbow), on_body(wrist)
        out.append(bone3(s, e, 1.5, 'claw', 'arm' + side))
        out.append(bone3(e, w, 1.35, 'claw', 'arm' + side))
        out.append(part(add(w, (0.4, 0.0, 0.0)), (2.4, 1.7, 2.0), 'claw', 'arm' + side))
        for sign in (-1, 1):
            R = ry(deg(10 + opening) * sign * z)
            tip = mv(R, (3.4, 0.0, 0.0))
            out.append(part(add(w, (tip[0] + 1.0, tip[1] + 0.1, tip[2])), (3.0, 0.9, 1.05), 'claw', 'pincer' + side + str(sign), R))
    return out


def torso_parts(p, on_body, on_chest):
    """The man's body: waist, chest, head with long hair, a bronze shoulder guard, and two arms ending in claws."""
    out = []
    out.append(part(on_body((3.6, 5.6, 0)), (2.2, 2.1, 2.0), 'skin', 'waist'))
    out.append(part(on_chest((3.6, 8.7, 0)), (2.6, 2.9, 3.1), 'skin', 'chest'))
    out.append(part(on_chest((4.5, 9.6, 0)), (1.2, 1.5, 2.4), 'skin', 'pecs'))
    out.append(part(on_chest((3.5, 11.3, 0)), (0.9, 0.8, 1.0), 'skin', 'neck'))
    head = on_chest((4.0, 13.2, 0))
    out.append(part(head, (1.9, 2.1, 1.8), 'skin', 'head'))
    out.append(part(add(head, (-1.6, -2.2, 0)), (1.3, 4.0, 1.9), 'hair', 'hair'))               # long hair down the back
    out.append(part(add(head, (-0.3, 1.2, 0)), (1.9, 1.2, 1.9), 'hair', 'hair'))
    for z in (-1, 1):
        out.append(part(on_chest((5.35, 13.4, z * 0.85)), (0.45, 1.05, 0.62), 'ring', 'head'))
    # fangs: two long pale points hanging from his upper lip, with a dark mouth between them
    out.append(part(on_chest((5.5, 12.15, 0.0)), (0.5, 0.32, 0.95), 'mouth', 'mouth'))
    for z in (-1, 1):
        out.append(part(on_chest((5.55, 11.85, z * 0.62)), (0.3, 0.95, 0.28), 'bone', 'fang' + str(z), rz(deg(-8))))
    # the pauldrons, big curved plates of gold on each shoulder
    for z in (-1, 1):
        out.append(part(on_chest((3.4, 11.4, z * 3.7)), (2.0, 0.8, 1.3), 'gold', 'pauldron' + str(z), rx(deg(-z * 24))))
        out.append(part(on_chest((3.4, 10.7, z * 4.2)), (1.6, 0.5, 1.0), 'gold', 'pauldronb' + str(z), rx(deg(-z * 32))))
    # the arms: (upper-arm angle, forearm angle) for each: a ready stance, the elbows down and the forearms up in front
    for side, z in (('L', -1), ('R', 1)):
        up, fore = p['arms'][0 if side == 'L' else 1]
        sh = on_chest((3.6, 11.0, z * 3.2))
        d1 = (math.cos(deg(up)) * 0.6, math.sin(deg(up)), z * math.cos(deg(up)) * 0.8)
        elbow = (sh[0] + 3.0 * d1[0], sh[1] + 3.0 * d1[1], sh[2] + 3.0 * d1[2])
        d2 = (math.cos(deg(fore)) * 0.9, math.sin(deg(fore)), z * math.cos(deg(fore)) * 0.4)
        wrist = (elbow[0] + 2.9 * d2[0], elbow[1] + 2.9 * d2[1], elbow[2] + 2.9 * d2[2])
        out.append(bone3(sh, elbow, 1.05, 'skin', 'uarm' + side))
        out.append(bone3(elbow, wrist, 0.9, 'skin', 'farm' + side, grow=0.4))
        out.append(bone3(add(elbow, tuple(0.55 * (wrist[i] - elbow[i]) for i in range(3))), wrist, 1.0, 'bronze', 'bracer' + side, grow=0.1))
        # the arm ends in a claw, like the great pincers and the same colour: a palm and two fingers that open
        n = math.sqrt(sum(v * v for v in d2))
        fwd = tuple(v / n for v in d2)
        out.append(part(add(wrist, tuple(0.5 * v for v in fwd)), (1.05, 0.95, 0.9), 'claw', 'palm' + side))
        side_dir = (0.0, 0.0, 1.0)
        for sign in (-1, 1):
            base = add(wrist, tuple(0.9 * v + sign * 0.4 * w for v, w in zip(fwd, side_dir)))
            tip = add(wrist, tuple(2.9 * v + sign * 0.35 * w for v, w in zip(fwd, side_dir)))
            out.append(bone3(base, tip, 0.42, 'claw', f'finger{side}{sign}', grow=0.35))
    return out


def place(p):
    g = mm(rx(deg(p['roll'])), rz(deg(p['body_pitch'])))
    shift = (p['fwd'], p['lift'], 0.0)

    def on_body(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    def on_chest(pt):
        # the man leans: his chest sways forward and back over his waist
        lean = deg(p['torso_lean'])
        pivot = (3.6, 6.4, 0.0)
        r = mv(rz(lean), sub(pt, pivot))
        return on_body(add(pivot, r))

    scorpion = []
    for q in body_parts():
        scorpion.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    for q in tail_parts(p):
        scorpion.append(dict(q, c=on_body(q['c']), R=mm(g, q['R'])))
    scorpion += pincers(on_body, p)
    man = torso_parts(p, on_body, on_chest)
    placed = []
    # eight thick spiked legs, four pairs: a hip on the side, a high knee, a second joint, and a long pointed foot
    for k, x in enumerate(LEG_X):
        for side, z in (('L', -1), ('R', 1)):
            name = f'{side}{k + 1}'
            hip = on_body((x, 2.8, z * 3.3))
            dx, lift = p['feet'].get(name, (0.0, 0.0))
            foot = (hip[0] + dx + 0.4, 0.5 + lift, hip[2] + z * 7.0)
            knee = (hip[0] + dx * 0.3 + 0.5, 7.0 + lift * 0.4, hip[2] + z * 2.6)
            ankle = (hip[0] + dx * 0.7, 3.2 + lift * 0.8, hip[2] + z * 5.2)
            if p['curl']:
                c = p['curl']
                knee = on_body((x + 0.6, 6.5 + 1.0 * c, z * 6.0))
                ankle = on_body((x - 0.4, 5.8 + 2.0 * c, z * 7.0))
                foot = on_body((x - 1.0 * c, 4.0 + 3.0 * c, z * (8.0 - 2.0 * c)))
            out_r = 1.0 - 0.02 * k
            scorpion.append(bone3(hip, knee, out_r, 'leg', 'leg' + name, grow=0.5))
            scorpion.append(bone3(knee, ankle, out_r * 0.85, 'leg', 'leg' + name, grow=0.5))
            scorpion.append(bone3(ankle, foot, out_r * 0.7, 'bone', 'leg' + name, grow=0.5))
    # The man is drawn bigger and the scorpion smaller than the first sketch: the scorpion shrinks about the ground, and the man
    # grows about his waist, which stays on the scorpion's back.
    base = on_body((3.6, 4.8, 0.0))
    base_small = tuple(v * BODY_SCALE for v in base)
    for q in scorpion:
        placed.append(dict(q, c=tuple(v * BODY_SCALE for v in q['c']), r=tuple(v * BODY_SCALE for v in q['r'])))
    for q in man:
        placed.append(dict(q, c=tuple(base_small[i] + (q['c'][i] - base[i]) * MAN_SCALE for i in range(3)), r=tuple(v * MAN_SCALE for v in q['r'])))
    decals = []
    for z in (-1, 1):
        e = on_chest((5.6, 13.4, z * 0.8))
        decals.append((tuple(base_small[i] + (e[i] - base[i]) * MAN_SCALE for i in range(3)), p['eyes']))
    return placed, decals


BASE = dict(body_pitch=0, roll=0, fwd=0, lift=0, torso_lean=0, curl=0, stretch=1.0, tail=(70, 150, 0), claws=(0.0, 0.0, 14),
            arms=((-48, 30), (-42, 38)), feet={}, eyes='open')


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


# --- the boss's sprites -------------------------------------------------------------------
# A boss stands on four ground squares (a 2 x 2 footprint: a diamond 64 wide and 32 tall), so it is drawn in a 96 x 96 cell, three times
# the width and height of a person's, with the middle of the footprint at ANCHOR on the ground. The same poses as everyone else: charging,
# a four-frame attack, release, damage, weak, dead and an eight-frame walk, each in NE and SE.
BOSS_CELL = 96
ANCHOR = (48, 72)              # the middle of the 2 x 2 footprint, on the ground
GROUND = 88                    # the lowest painted row of a standing frame: the footprint's bottom point is 16 rows below the anchor
RENDER_SCALE = 2.6             # pixels to a model unit, so the legs span the footprint
FEET_ALL = {f'{s}{k}': (0.0, 0.0) for s in 'LR' for k in range(1, 5)}
ACTIONS = [('charging', 1), ('attack', 4), ('release', 1), ('damage', 1), ('weak', 1), ('dead', 1), ('walking', 8)]


def walk(k, n=8):
    """Eight legs in two sets of four, alternating, the body barely rising, the man swaying and the tail rocking."""
    phase = 2 * math.pi * k / n
    feet = {}
    for ki in range(4):
        for side, off in (('L', 0.0 if ki % 2 == 0 else math.pi), ('R', math.pi if ki % 2 == 0 else 0.0)):
            u = (phase + off) % (2 * math.pi)
            if u < math.pi:
                dx, lift = 2.2 * (1 - 2 * u / math.pi), 0.0
            else:
                w = (u - math.pi) / math.pi
                dx, lift = -2.2 + 4.4 * w, 1.6 * math.sin(math.pi * w)
            feet[f'{side}{ki + 1}'] = (dx, lift)
    return pose(feet=feet, lift=0.35 * math.cos(2 * phase), body_pitch=1.4 * math.sin(2 * phase), torso_lean=2.5 * math.sin(2 * phase),
                tail=(70, 150 + 6 * math.sin(2 * phase), 5 * math.sin(phase)), claws=(0.4 * math.sin(phase), 0.0, 14 + 5 * math.sin(phase)))


POSES = {
    # braced and ready
    'charging': [pose()],
    # coiled back with the tail drawn up tight, then the strike: the body surges, the tail stretches forward and the claws snap
    'attack': [
        pose(body_pitch=-4, fwd=-1.6, torso_lean=8, tail=(78, 128, 0), stretch=0.85, claws=(-0.8, 1.2, 36), arms=((-60, 55), (-55, 60))),
        pose(body_pitch=4, fwd=1.2, torso_lean=-8, tail=(60, 160, 0), stretch=1.2, claws=(1.2, 0.2, 28), arms=((-30, 10), (-26, 14))),
        pose(body_pitch=-7, fwd=2.8, torso_lean=-20, tail=(50, 150, 0), stretch=1.45, claws=(1.6, 0.0, 5), arms=((8, -4), (10, 0)),
             feet={'L4': (-0.6, 2.0), 'R4': (-0.6, 2.0), 'L3': (-0.4, 0.9), 'R3': (-0.4, 0.9)}),
        pose(body_pitch=1, fwd=0.8, torso_lean=-4, tail=(70, 150, 0), stretch=1.1, claws=(0.5, 0.2, 18), arms=((-40, 30), (-38, 34))),
    ],
    # reared up, claws and arms flung wide
    'release': [pose(body_pitch=16, lift=0.8, torso_lean=14, tail=(80, 175, 0), claws=(0.8, 2.4, 46), arms=((50, 20), (46, 24)), eyes='shut', feet=FEET_ALL)],
    # a flinch: thrown back, the man doubled over, the tail whipped
    'damage': [pose(body_pitch=12, fwd=-1.8, torso_lean=-26, tail=(62, 118, 8), claws=(-0.4, 1.6, 34), arms=((-80, 70), (-76, 74)), eyes='shut')],
    # worn out: low, the man slumped, the tail drooping
    'weak': [pose(body_pitch=-2, lift=-1.6, torso_lean=-34, tail=(52, 118, 4), claws=(-0.8, 0.4, 8), arms=((-85, 80), (-82, 84)), eyes='shut', feet=FEET_ALL)],
    # fallen on its side, the legs curled
    'dead': [pose(roll=120, lift=-0.8, torso_lean=-40, curl=1.0, tail=(-4, 24, 6), claws=(-0.8, 0.6, 8), arms=((-70, 70), (-66, 74)), eyes='shut')],
    'walking': [walk(k) for k in range(8)],
}


RENDER_ORIGIN = (BOSS_CELL / 2, 72.0)      # where the model's origin lands while drawing; frames are then shifted onto the ground


# A few frames reach further than the rest and would be cut off at the edge of the cell while drawing, so they are drawn from another
# origin and shifted back afterwards: (action, frame index) -> the origin to draw from.
ORIGIN_OVERRIDE = {('attack', 2): (36.0, 72.0), ('dead', 0): (48.0, 52.0), ('weak', 0): (48.0, 76.0)}


def render_pose(p, facing, scale=RENDER_SCALE, origin=None):
    """One frame of the boss at its own scale, as 96 x 96 rows of role characters, before it is put on the ground."""
    import creature as cr
    parts, decals = place(p)
    return cr.render_frame(parts, decals, facing, origin or RENDER_ORIGIN, RAMPS, scale)


def build_frames(cache=None):
    """Every action's frames in both facings, drawn on a 96 x 96 cell with the feet on the ground row.

    Drawing is the slow part, so `cache` (a JSON file) keeps the raw drawings: change how they are put on the ground and it takes a
    second; change a pose or the model and delete the file.
    """
    import json
    import creature as cr
    raw = json.loads(Path(cache).read_text()) if cache and Path(cache).exists() else {}
    old = cr.CELL
    cr.CELL = BOSS_CELL
    cr.TALL_EYES, cr.EYE_WHITE, cr.EYE_COLOUR, cr.EYE_PUPIL, cr.EYE_REACH = True, 't', 'j', None, 0.9
    try:
        out = {}
        for facing in ('NE', 'SE'):
            for action, count in [('standing', 1)] + ACTIONS:
                key = action + facing
                if key not in raw:
                    poses = [pose()] if action == 'standing' else POSES[action]
                    raw[key] = [render_pose(p, facing, origin=ORIGIN_OVERRIDE.get((action, i))) for i, p in enumerate(poses)]
                    if cache:
                        Path(cache).write_text(json.dumps(raw))
        for facing in ('NE', 'SE'):
            rows = raw['standing' + facing][0]
            xs = [x for r in rows for x, ch in enumerate(r) if ch != '.']
            stand_dx = round(ANCHOR[0] - (min(xs) + max(xs) + 1) / 2)       # the same sideways shift for every frame, so a lunge shows
            for action, count in ACTIONS:
                frames = []
                for index, rows in enumerate(raw[action + facing]):
                    ys = [y for y, r in enumerate(rows) if r.strip('.')]
                    xs = [x for r in rows for x, ch in enumerate(r) if ch != '.']
                    origin_x = ORIGIN_OVERRIDE.get((action, index), RENDER_ORIGIN)[0]
                    dx = round(ANCHOR[0] - (min(xs) + max(xs) + 1) / 2) if action == 'dead' else stand_dx + round(RENDER_ORIGIN[0] - origin_x)
                    frames.append(shift_frame(rows, dx, GROUND - max(ys)))      # every frame stands on the ground row, even mid-lunge
                out[action + facing] = frames
    finally:
        cr.CELL = old
    return out


def shift_frame(rows, dx, dy):
    """A frame moved by whole pixels; what is pushed off the edge is lost."""
    n = BOSS_CELL
    blank = '.' * n
    moved = []
    for y in range(n):
        src = y - dy
        row = rows[src] if 0 <= src < n else blank
        if dx > 0:
            row = '.' * dx + row[:n - dx]
        elif dx < 0:
            row = row[-dx:] + '.' * -dx
        moved.append(row)
    return moved


def write_sprites(folder, cache=None):
    """The sheets, one PNG per action and facing: the frames side by side, 96 pixels each."""
    from PIL import Image
    import extract_poses as ep
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    Path(folder).mkdir(parents=True, exist_ok=True)
    for pose_id, frames in build_frames(cache).items():
        img = Image.new('RGBA', (len(frames) * BOSS_CELL, BOSS_CELL), (0, 0, 0, 0))
        for i, rows in enumerate(frames):
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch != '.':
                        img.putpixel((i * BOSS_CELL + x, y), rgb[ch] + (255,))
        img.save(Path(folder) / f'scorpion-emperor-{pose_id}.png')


class Emperor:
    name = 'scorpion-emperor'
    kind = 'boss'
    airborne = set()
    ramps = RAMPS
    scale = 1.0
    stand = pose()
    tall_eyes = True
    eye_white = 't'                      # and for the sprites, white either side of each slit
    eye_colour = 'j'                     # red eyes (the palette's hot pink: there is no pure red)
    poses = {}

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Emperor()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The scorpion emperor.')
    parser.add_argument('out', type=Path, nargs='?', help='folder for the sprite sheets, e.g. sprites/scorpion-emperor')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--pose', default='charging')
    parser.add_argument('--frame', type=int, default=0)
    parser.add_argument('--views')
    args = parser.parse_args()
    if args.model:
        import preview3d
        CREATURE.poses = {k: v for k, v in POSES.items()}
        views = args.views.split(',') if args.views else None
        preview3d.render_sheet(CREATURE, preview3d.pick_pose(CREATURE, args.pose, args.frame), views).save(args.model)
        print('3D preview ->', args.model)
    elif args.out:
        write_sprites(args.out, Path(args.out) / 'raw.json')
        print('wrote the sheets ->', args.out)
