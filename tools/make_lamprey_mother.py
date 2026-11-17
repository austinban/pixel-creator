#!/usr/bin/env python3
"""The Lamprey Mother: a boss on a 2 x 2 footprint, the blighted ruler of the sunken water and the thing the sirens are spawned from. Built like the blood mushroom (see make_blood_mushroom.py and creature.py),
drawn in the boss's 96 x 96 cell.

A huge lamprey rises out of the water in a long S: a thick teal-black body with a pale belly, a ridge of fuchsia fin down its back, and a second coil of the same body looping up out of the water beside it.
Where a fish's head would be there is only a funnel: a ring of magenta lip round a black throat, set with rings of cream teeth (the opposite of the siren's toothless gape), a small yellow eye on each side behind it.
A crown of mushrooms grows from the back of her head and along her spine, and seven glowing hot-pink gill slits run down each flank. Foam rings spread on the water round her.

She is stationary, like the stone totem and the blood mushroom: she never walks. Her "walking" is an idle, a slow sway of the body with the ring of teeth turning in the mouth. "Attack" is a strike:
rear back, lunge, bite down with the ring pulled tight, recoil. It has the same actions and frame counts as a boss (charging, a four-frame attack, release, damage, weak, dead and an eight-frame walk, both facings).

    python3 tools/make_lamprey_mother.py --model previews/lamprey-3d.png      look at the 3D model first
    python3 tools/make_lamprey_mother.py sprites/lamprey-mother --preview previews/lamprey-mother.png
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402
import creature as cr  # noqa: E402
import extract_poses as ep  # noqa: E402
from assetkit import normalise  # noqa: E402
from creature import add, deg, mm, mv, part, rx, ry, rz, sub  # noqa: E402
from make_blood_mushroom import hashed, shift_frame  # noqa: E402
from make_mushroom import surface_disc  # noqa: E402
from make_rockmonster import along  # noqa: E402

# Colour ramps by role: lit, base, shade, deep.
RAMPS = {
    'scale': ('q', 's', 'D', 'x'),           # teal, deep teal, abyss, eggplant: the back and flanks, as the siren's
    'belly': ('r', 'q', 'p', 'l'),           # mint, teal, steel, lavender: the pale belly
    'fin': ('y', 'y', 'u', 'w'),             # fuchsia, purple, grape: the fin ridge
    'lip': ('j', 'i', 'h', 'w'),             # the ring round the mouth: hot pink, magenta, dark magenta, grape
    'maw': ('w', 'x', 'x', 'x'),             # the throat: as dark as the palette goes
    'tooth': ('t', 't', 'C', 'c'),           # cream teeth
    'tongue': ('c', 'e', 'g', 'w'),          # a raw pink tongue in the middle of the ring
    'gill': ('j', 'j', 'i', 'h'),            # glowing hot pink
    'gill_dim': ('l', 'k', 'w', 'x'),        # the gills gone out
    'eye': ('d', 'd', 'b', 'a'),             # a small sick yellow eye
    'pupil': ('w', 'x', 'x', 'x'),
    'cap': ('v', 'f', 'g', 'x'),             # mushroom caps: violet, orchid, plum, eggplant
    'stalk': ('t', 'C', 'c', 'e'),           # their pale stalks
    'spot': ('t', 't', 'C', 'c'),            # cream spots
    'foam': ('r', 'q', 'p', 'l'),            # foam and ripples on the water: cream, mint, teal, steel
    'spray': ('t', 'r', 'q', 'p'),
    'pale': ('t', 't', 'C', 'c'),            # everything flashed pale when she is hit
}

BODY_STEPS = 17
COIL_STEPS = 11


def P(c, r, mat, name, R=None):
    return part(c, r, mat, name, R)


def catmull(pts, n):
    """n + 1 points along the smooth curve through pts (Catmull-Rom), evenly spaced in the curve's parameter."""
    out = []
    m = len(pts) - 1
    ext = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(n + 1):
        u = m * i / n
        k = min(int(u), m - 1)
        t = u - k
        p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
        out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(3)))
    return out


def norm(v):
    return normalise(v)


def spine(p):
    """The main body: points from the water up to the head, in this pose, and the head's centre and the way its mouth faces."""
    s, rear, lunge, drop = p['sway'], p['rear'], p['lunge'], p['drop']
    w = lambda i, a: a * math.sin(p['phase'] - i * 0.8)               # a wave running up the body
    ctrl = [(-3.0, -3.0, 0.0),
            (-4.6 + 0.4 * lunge * 0.0, 5.0, 1.6 + w(0, s)),
            (-2.6, 13.0, -1.8 + w(1, s)),
            (1.5 + 0.35 * lunge, 20.0 + 0.7 * rear + 0.2 * drop, 0.8 + w(2, s * 0.7)),
            (5.2 + 0.8 * lunge, 26.0 + rear + 0.5 * drop, w(3, s * 0.4)),
            (8.3 + lunge, 28.4 + rear + drop, 0.0)]
    head = ctrl[-1]
    return ctrl, head


def mouth_axis(p):
    t = deg(p['tilt'])
    m = (math.cos(t), -math.sin(t), 0.0)
    u1 = (0.0, 0.0, 1.0)
    u2 = (math.sin(t), math.cos(t), 0.0)
    return m, u1, u2


def radius_at(i, n):
    u = i / n
    return 4.0 + 1.9 * math.sin(math.pi * min(1.0, u * 1.25)) ** 0.7 - 0.8 * max(0.0, u - 0.8) * 5 * 0.0


def body_parts(p):
    ctrl, head = spine(p)
    pts = catmull(ctrl, BODY_STEPS)
    m, u1, u2 = mouth_axis(p)
    out = []
    glow = 'gill_dim' if p['dim'] else 'gill'
    for i in range(BODY_STEPS):
        a, b = pts[i], pts[i + 1]
        mid = tuple((a[k] + b[k]) / 2 for k in range(3))
        d = norm(sub(b, a))
        ln = math.sqrt(sum(v * v for v in sub(b, a)))
        r = 4.3 + 1.1 * math.sin(math.pi * (i + 0.5) / BODY_STEPS) - 0.5 * (i / BODY_STEPS) ** 2
        out.append(P(mid, (ln * 0.95 + 1.6, r, r), 'scale', 'body', along(d)))
        belly = (d[1], -d[0], 0.0)                                      # the belly side: forward as the body rises, down as it lies over
        bn = norm(belly)
        out.append(P(tuple(mid[k] + bn[k] * r * 0.62 for k in range(3)), (ln * 0.9 + 1.4, r * 0.5, r * 0.7), 'belly', 'belly', along(d)))
        if 2 <= i <= BODY_STEPS - 2:                                    # the fin ridge on the back
            back = (-bn[0], -bn[1], 0.0)
            tall = 2.6 + 1.2 * (1 if i % 2 else 0) - 0.05 * i
            out.append(P(tuple(mid[k] + back[k] * (r + tall * 0.35) for k in range(3)), (ln * 0.58 + 0.2, tall * 0.8, 0.38), 'fin', f'fin{i}', along(d)))
        if 6 <= i <= BODY_STEPS - 3 and i % 2 == 0:                                    # a pair of glowing gill slits each side, down the flank toward the head
            slit_c = tuple(mid[k] + bn[k] * r * 0.15 for k in range(3))
            for z in (-1, 1):
                c = (slit_c[0], slit_c[1], slit_c[2] + z * r * 0.93)
                out.append(P(c, (0.5, 1.8, 0.75), glow, f'gill{i}_{z}', along((-d[1], d[0], 0.0))))
    # the head and its funnel
    Hc = head
    out.append(P(add(Hc, tuple(m[k] * 0.4 for k in range(3))), (4.8, 4.9, 4.9), 'scale', 'body', along(m)))
    out.append(P(add(Hc, tuple(m[k] * 0.9 - u2[k] * 2.0 for k in range(3))), (4.0, 3.0, 4.2), 'belly', 'belly', along(m)))
    fl = p['flare']
    Lr = 5.2 * fl
    dist = 3.3
    for z in (-1, 1):                                                   # a small yellow eye each side, behind the ring
        ec = add(Hc, tuple(-m[k] * 0.2 + u2[k] * 2.4 + u1[k] * z * 4.3 for k in range(3)))
        out.append(P(ec, (0.95, 0.95, 0.95), 'eye', f'eye{z}'))
        out.append(P(add(ec, tuple(m[k] * 0.55 + u1[k] * z * 0.2 for k in range(3))), (0.4, 0.55, 0.45), 'pupil', f'pupil{z}'))
    n = 22
    for k in range(n):                                                  # the ring of lip, a swollen magenta ring
        a = 2 * math.pi * k / n
        radial = tuple(math.cos(a) * u1[j] + math.sin(a) * u2[j] for j in range(3))
        tang = tuple(-math.sin(a) * u1[j] + math.cos(a) * u2[j] for j in range(3))
        c = add(Hc, tuple(m[j] * dist + radial[j] * Lr for j in range(3)))
        out.append(P(c, (1.5, 1.25, 1.25), 'lip', 'lip', along(tang)))
    out.append(P(add(Hc, tuple(m[j] * (dist + 0.35) for j in range(3))), (0.7, 4.3 * fl, 4.3 * fl), 'maw', 'maw', along(m)))
    out.append(P(add(Hc, tuple(m[j] * (dist + 0.9) for j in range(3))), (0.6, 1.0, 1.0), 'tongue', 'tongue', along(m)))
    spin = p['spin']
    for ring, (count, r0, size, reach) in enumerate(((16, 3.9, 0.62, 1.7), (11, 2.55, 0.52, 1.5), (6, 1.35, 0.42, 1.3))):
        for k in range(count):
            a = 2 * math.pi * (k + spin * (1 if ring % 2 == 0 else -1)) / count + ring * 0.3
            radial = tuple(math.cos(a) * u1[j] + math.sin(a) * u2[j] for j in range(3))
            c = add(Hc, tuple(m[j] * (dist + 0.5 + 0.5 * reach * p['bite']) + radial[j] * r0 * fl * (1 - 0.18 * p['bite']) for j in range(3)))
            R = along(norm(tuple(m[j] * 1.0 - radial[j] * 0.35 for j in range(3))))
            out.append(P(c, (reach * 0.55 * (1 + 0.5 * p['bite']), size * 0.9, size * 0.8), 'tooth', f'tooth{ring}', R))
    # the crown: mushrooms growing from the back of the head and along the spine
    dorsal = tuple(-v for v in u2)
    back = tuple(-m[j] * 1.0 for j in range(3))
    for k, (up, bk, side, size, tall) in enumerate(((4.0, -1.2, 0.0, 3.4, 2.6), (3.6, -3.4, 2.8, 2.4, 2.0), (3.8, -3.0, -3.0, 2.7, 2.2), (2.4, -5.0, 0.2, 1.9, 1.6))):
        base = add(Hc, tuple(u2[j] * up * 0.9 + m[j] * bk + u1[j] * side for j in range(3)))
        top = add(base, tuple(u2[j] * tall for j in range(3)))
        out.append(P(tuple((base[j] + top[j]) / 2 for j in range(3)), (0.75, tall / 2 + 0.4, 0.75), 'stalk', f'stalk{k}', along(norm(sub(top, base)))))
        cap_c = add(top, tuple(u2[j] * size * 0.12 for j in range(3)))
        out.append(P(cap_c, (size, size * 0.52, size), 'cap', f'cap{k}', along((1, 0, 0))))
        for q, (dx, dz) in enumerate(((0.45, 0.2), (-0.35, 0.5), (0.1, -0.7))):
            out.append(P((cap_c[0] + dx * size * 0.9, cap_c[1] + size * 0.5, cap_c[2] + dz * size * 0.9), (size * 0.22, 0.2, size * 0.2), 'spot', f'spot{k}_{q}'))
    for k, i in enumerate((6, 9, 12)):                                  # small ones along the spine
        a, b = pts[i], pts[i + 1]
        mid = tuple((a[j] + b[j]) / 2 for j in range(3))
        d = norm(sub(b, a))
        bn = norm((d[1], -d[0], 0.0))
        r = 4.3 + 1.1 * math.sin(math.pi * (i + 0.5) / BODY_STEPS)
        base = tuple(mid[j] - bn[j] * r * 0.9 + (1.2 if j == 2 else 0) * (1 if k % 2 else -1) for j in range(3))
        top = tuple(base[j] - bn[j] * 1.8 for j in range(3))
        out.append(P(tuple((base[j] + top[j]) / 2 for j in range(3)), (0.6, 1.2, 0.6), 'stalk', f'sstalk{k}', along(norm(sub(top, base)))))
        out.append(P(tuple(top[j] - bn[j] * 0.2 for j in range(3)), (1.8, 0.95, 1.8), 'cap', f'scap{k}', along((1, 0, 0))))
    return out


def coil_parts(p):
    """The second loop of the body, looping out of the water beside the first."""
    ctrl = [(-10.0, -3.0, 7.0), (-11.0, 5.0, 8.0), (-8.5, 13.5 + p['coil'], 9.5), (-3.5, 13.0 + p['coil'], 11.5), (-0.8, 5.0, 12.5), (1.0, -3.0, 13.0)]
    pts = catmull(ctrl, COIL_STEPS)
    out = []
    for i in range(COIL_STEPS):
        a, b = pts[i], pts[i + 1]
        mid = tuple((a[k] + b[k]) / 2 for k in range(3))
        d = norm(sub(b, a))
        ln = math.sqrt(sum(v * v for v in sub(b, a)))
        r = 3.7 - 0.7 * abs(i - COIL_STEPS / 2) / (COIL_STEPS / 2) * 0.0
        out.append(P(mid, (ln * 0.95 + 1.4, r, r), 'scale', 'coil', along(d)))
        bn = norm((d[1], -d[0], 0.0))
        out.append(P(tuple(mid[k] + bn[k] * r * 0.6 for k in range(3)), (ln * 0.9 + 1.2, r * 0.5, r * 0.7), 'belly', 'coilbelly', along(d)))
        if 1 <= i <= COIL_STEPS - 2:
            out.append(P(tuple(mid[k] - bn[k] * (r + 0.7) for k in range(3)), (ln * 0.58 + 0.2, 2.0, 0.34), 'fin', f'cfin{i}', along(d)))
    return out


def water_parts(p):
    out = []
    for ring, (r0, count, size) in enumerate(((7.6, 18, 1.0), (12.0, 26, 1.2), (16.0, 30, 1.0))):
        for k in range(count):
            if hashed(k, ring + 3) < 0.28:
                continue
            a = 2 * math.pi * (k + 0.3 * hashed(k, ring)) / count + p['ripple'] * ring * 0.2
            r = r0 + p['ripple'] * 0.6 + 0.5 * hashed(k, ring + 9)
            out.append(P((r * math.cos(a), 0.25, r * math.sin(a)), (size * 1.6, 0.22, size * 0.55), 'foam', f'foam{ring}', ry(-a)))
    for k, (c, s) in enumerate(p['drops']):
        out.append(P(c, (s, s * 1.3, s), 'spray', f'spray{k}'))
    if p['ring']:
        r0, y0 = p['ring']
        for k in range(20):
            a = 2 * math.pi * k / 20
            out.append(P((r0 * math.cos(a), y0, r0 * math.sin(a)), (1.0, 0.45, 1.0), 'spray', f'ring{k}'))
    return out


def anatomy(p):
    return body_parts(p) + coil_parts(p) + water_parts(p)


def place(p):
    flash = p['flash']
    placed = []
    for q in anatomy(p):
        mat = 'pale' if flash and q['mat'] in ('scale', 'belly', 'fin', 'lip', 'cap', 'tongue') else q['mat']
        placed.append(dict(q, mat=mat))
    return placed, []


# --- poses ---------------------------------------------------------------------------------
BASE = dict(sway=2.0, phase=0.0, rear=0.0, lunge=0.0, drop=0.0, tilt=18.0, flare=1.0, bite=0.0, spin=0.0, dim=False, flash=False, coil=0.0, ripple=0.0, drops=[], ring=None)


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def idle(k, n=8):
    """A slow sway: a wave runs up the body, the head nods, the ring of teeth turns by one tooth over the loop and the ripples drift."""
    ph = 2 * math.pi * k / n
    return pose(sway=2.6, phase=ph, rear=1.2 * math.sin(ph + 1.0), lunge=0.8 * math.sin(ph), tilt=18 + 5 * math.sin(ph + 0.6), flare=1.0 + 0.04 * math.sin(2 * ph),
                spin=k / n, coil=0.8 * math.sin(ph + 2.0), ripple=math.sin(ph))


SPRAY = [((-9.0, 14.0, 2.0), 0.55), ((10.0, 9.0, 5.0), 0.5), ((12.0, 3.0, -6.0), 0.45), ((-12.0, 5.0, -4.0), 0.5), ((6.0, 18.0, -8.0), 0.4)]

POSES = {
    # braced: reared up, the funnel flared wide, the gills blazing
    'charging': [pose(rear=3.0, lunge=-1.0, tilt=10, flare=1.18, sway=1.5, drops=SPRAY[:3], ripple=1.0)],
    # a strike: rear back, lunge down, bite with the ring pulled tight, recoil
    'attack': [
        pose(rear=4.0, lunge=-5.0, drop=2.0, tilt=-8, flare=1.05, sway=3.0, phase=1.0),
        pose(rear=-3.0, lunge=8.0, drop=-3.0, tilt=42, flare=1.2, bite=0.4, sway=3.5, phase=2.0, drops=SPRAY[1:3]),
        pose(rear=-8.0, lunge=12.0, drop=-9.0, tilt=62, flare=0.9, bite=1.0, sway=3.0, phase=3.0, drops=SPRAY, ripple=1.5),
        pose(rear=2.0, lunge=1.0, drop=0.0, tilt=22, flare=1.0, bite=0.3, sway=2.0, phase=4.0),
    ],
    # a great screech: reared high, the funnel flung wide, spray and a ring of spray thrown out
    'release': [pose(rear=3.0, lunge=-3.0, drop=1.0, tilt=-4, flare=1.35, sway=1.0, ring=(9.0, 4.0), drops=SPRAY, ripple=1.8)],
    # a flinch: flashed pale, hunched away, the funnel clenched
    'damage': [pose(flash=True, rear=-3.0, lunge=-6.0, drop=-3.0, tilt=36, flare=0.82, sway=4.0, phase=2.4, drops=SPRAY[:3])],
    # badly hurt: the head sags toward the water, the gills dim
    'weak': [pose(rear=-8.0, lunge=-2.0, drop=-6.0, tilt=52, flare=0.85, sway=1.0, dim=True, coil=-2.0)],
    # dead: the head down in the water, the body slumped, the glow out
    'dead': [pose(rear=-16.0, lunge=3.0, drop=-12.0, tilt=76, flare=0.8, sway=0.5, dim=True, coil=-5.0, ripple=0.6)],
    'walking': [idle(k) for k in range(8)],
}


# --- the boss's sprites --------------------------------------------------------------------
BOSS_CELL = conventions.BOSS_CELL
ANCHOR = conventions.BOSS_ANCHOR
GROUND = conventions.BOSS_GROUND
RENDER_SCALE = 1.65
RENDER_ORIGIN = (BOSS_CELL / 2, 70.0)
ACTIONS = [('charging', 1), ('attack', 4), ('release', 1), ('damage', 1), ('weak', 1), ('dead', 1), ('walking', 8)]
NAME = 'lamprey-mother'


def render_pose(p, facing, origin=None):
    parts, decals = place(p)
    return cr.render_frame(parts, decals, facing, origin or RENDER_ORIGIN, RAMPS, RENDER_SCALE)


def build_frames(cache=None):
    import json
    raw = json.loads(Path(cache).read_text()) if cache and Path(cache).exists() else {}
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
    old = cr.CELL
    cr.CELL = BOSS_CELL
    cr.TALL_EYES, cr.EYE_WHITE, cr.EYE_COLOUR, cr.EYE_PUPIL, cr.EYE_REACH = False, None, None, None, 0.9
    out = {}
    try:
        for facing in ('NE', 'SE'):
            for action, count in [('standing', 1)] + ACTIONS:
                key = action + facing
                if key not in raw:
                    poses = [pose()] if action == 'standing' else POSES[action]
                    raw[key] = [render_pose(p, facing) for p in poses]
                    if cache:
                        Path(cache).write_text(json.dumps(raw))
        for facing in ('NE', 'SE'):
            rows = raw['standing' + facing][0]
            xs = [x for r in rows for x, ch in enumerate(r) if ch != '.']
            stand_dx = round(ANCHOR[0] - (min(xs) + max(xs) + 1) / 2)
            for action, count in ACTIONS:
                frames = []
                for rows in raw[action + facing]:
                    ys = [y for y, r in enumerate(rows) if r.strip('.')]
                    xs = [x for r in rows for x, ch in enumerate(r) if ch != '.']
                    dx = round(ANCHOR[0] - (min(xs) + max(xs) + 1) / 2) if action == 'dead' else stand_dx
                    frames.append(shift_frame(rows, dx, GROUND - max(ys)))
                out[action + facing] = frames
    finally:
        cr.CELL = old
    return out


def check(frames_by_pose):
    return conventions.check_ramps(RAMPS, NAME) + conventions.check_boss(NAME, frames_by_pose)


def write_sprites(folder, frames, preview=None):
    from PIL import Image
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    Path(folder).mkdir(parents=True, exist_ok=True)
    sheets = []
    for pose_id, fr in frames.items():
        img = Image.new('RGBA', (len(fr) * BOSS_CELL, BOSS_CELL), (0, 0, 0, 0))
        for i, rows in enumerate(fr):
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch != '.':
                        img.putpixel((i * BOSS_CELL + x, y), rgb[ch] + (255,))
        img.save(Path(folder) / f'{NAME}-{pose_id}.png')
        sheets.append((pose_id, img))
    if preview:
        scale = 2
        width = max(i.width for _, i in sheets) * scale
        height = sum(i.height * scale + 4 for _, i in sheets)
        contact = Image.new('RGBA', (width, height), (60, 64, 74, 255))
        y = 0
        for _, img in sheets:
            contact.alpha_composite(img.resize((img.width * scale, img.height * scale), Image.NEAREST), (0, y))
            y += img.height * scale + 4
        Path(preview).parent.mkdir(parents=True, exist_ok=True)
        contact.save(preview)


class LampreyMother:
    name = NAME
    kind = 'boss'
    airborne = set()
    ramps = RAMPS
    scale = 1.0
    stand = pose()
    tall_eyes = False
    poses = POSES

    @staticmethod
    def place(p):
        return place(p)


CREATURE = LampreyMother()


def main():
    parser = argparse.ArgumentParser(description='The Lamprey Mother, a 2 x 2 boss.')
    parser.add_argument('out', type=Path, nargs='?', help='folder for the sprite sheets, e.g. sprites/lamprey-mother')
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
        print(f'3D preview of the Lamprey Mother ({args.pose}, frame {args.frame + 1}) -> {args.model}; no sprites were made')
    elif args.out:
        frames = build_frames(Path(args.out) / 'raw.json')
        problems = check(frames)
        if problems and not args.force:
            print('the Lamprey Mother breaks the boss rules, so nothing was written (--force to write anyway):', file=sys.stderr)
            for q in problems:
                print('  ' + q, file=sys.stderr)
            sys.exit(1)
        write_sprites(args.out, frames, args.preview)
        print(f'wrote the sheets -> {args.out}' + (f' ({len(problems)} problems, forced)' if problems else ''))
    else:
        parser.error('say where to write the sprites, or use --model to see the 3D model first')


if __name__ == '__main__':
    main()
