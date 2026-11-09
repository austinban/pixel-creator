#!/usr/bin/env python3
"""The blood mushroom: a boss on a 2 x 2 footprint, a tall, wet, gnarled toadstool that has grown through the things it fed on. Built like the scorpion emperor (see make_emperor.py and creature.py), drawn in the boss's 96 x 96 cell.

A swollen root base fills the four ground squares, in a pool of blood. A thick stem of pale pink flesh rises from it, with five things pushing out of it:
two human arms with hands that twitch; a pink-grey rat's head, snout out, low on the stem; two human legs dangling
from under the cap; and antlers growing up through the cap. A tall dome of a cap, dark crimson with a clean rounded lip and cream spots, crowns it, a skirt of blood red gills hangs under the rim
(teal-grey ridges among them), and blood drips from it into the pool.

It is stationary, like the stone totem (see make_stonetotem.py): it never walks. Its "walking" is an idle, a slow breath in which the cap pulses, the hands twitch, the legs sway and blood drips. "Attack" is a pulse:
gather, a burst of spores in a ring, tendrils lashing out of the base, settle. It has the same actions and frame counts as a boss (charging, a four-frame attack, release, damage, weak, dead and an eight-frame walk, both facings).

    python3 tools/make_blood_mushroom.py --model previews/blood-mushroom-3d.png      look at the 3D model first
    python3 tools/make_blood_mushroom.py sprites/blood-mushroom [--preview sheet.png]
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
from make_mushroom import surface_disc  # noqa: E402
from make_rockmonster import along  # noqa: E402
from make_scorpion import bone3  # noqa: E402

# Colour ramps by role: lit, base, shade, deep.
RAMPS = {
    'flesh': ('c', 'e', 'f', 'g'),           # wet pink flesh: salmon, coral, orchid, plum (darker than the skin, so the limbs show against it)
    'flesh_dark': ('e', 'f', 'g', 'x'),      # the swollen base and the roots: darker
    'vein': ('e', 'f', 'g', 'x'),
    'cap': ('e', 'i', 'h', 'x'),             # dark crimson (the palette has no pure red): coral, magenta, dark magenta, eggplant
    'cap_hi': ('j', 'i', 'h', 'x'),          # the ragged rim bumps: a little brighter
    'gill': ('i', 'h', 'x', 'x'),            # blood red gills
    'gill_teal': ('p', 'l', 'k', 'w'),       # sickly teal-grey ridges among them
    'spot': ('t', 't', 'C', 'c'),            # cream spots
    'blood': ('j', 'i', 'h', 'x'),           # wet blood: drips, drops and the pool
    'pool': ('h', 'x', 'x', 'x'),
    'skin': ('t', 'C', 'c', 'e'),            # human skin: pale, so it stands out from the flesh
    'hand': ('t', 't', 't', 'C'),            # the hands: lighter than the arms, so they stand out
    'hollow': ('w', 'x', 'x', 'x'),          # the dark inside a mouth, an eye socket
    'bone': ('t', 't', 'C', 'c'),            # antlers, teeth, nails
    'fur': ('t', 'c', 'f', 'g'),             # the rat's coat: pink-grey flesh, paler and greyer than the stem
    'pink': ('c', 'e', 'f', 'g'),            # the rat's nose, ears and tail
    'eye': ('j', 'j', 'i', 'h'),             # glowing red-pink
    'pale': ('t', 't', 'C', 'c'),            # everything flashed pale when it is hit
    'spore': ('t', 'r', 'q', 'p'),           # spores in a ring: pale, teal-tinged
    'tendril': ('e', 'f', 'g', 'x'),
}

PIVOT = (0.0, 0.0, 0.0)                      # it leans about the middle of its base
CAP_PIVOT = (0.0, 24.0, 0.0)                 # the cap tilts about the top of the stem
CAP_C = (0.0, 28.6, 0.0)                     # the cap's dome: tall, its top 7.6 above its middle
CAP_R = (10.0, 7.6, 10.0)
LIP_C = (0.0, 24.2, 0.0)                     # a wide lip round the foot of the dome, which makes the bell
LIP_R = (10.4, 2.2, 10.4)
RIM_Y = 22.1                                 # where the skirt of gills ends and the drips begin
SKIRT_R = 9.1
POOL_R = 12.2


def P(c, r, mat, name, R=None, grp='stem'):
    """A part, in a group (base, stem or cap) that moves together."""
    q = part(c, r, mat, name, R)
    q['grp'] = grp
    return q


def rod(a, b, radius, mat, name, grp, grow=0.3):
    q = bone3(a, b, radius, mat, name, grow)
    q['grp'] = grp
    return q


def unit(v):
    return normalise(v)


def hashed(a, b=0):
    """A fixed pseudo-random number in [0, 1) from two integers: the ragged rim and the drips are not random from run to run."""
    n = (a * 374761393 + b * 668265263 + 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


# --- the parts -----------------------------------------------------------------------------
def base_parts(p):
    out = [P((0.0, 1.7, 0.0), (9.4, 3.0, 9.4), 'flesh_dark', 'mound', grp='base')]
    for k, (a, r0, w, l) in enumerate(((0.5, 9.6, 1.0, 2.6), (2.1, 10.0, 0.8, 2.0), (3.6, 9.4, 1.1, 2.8), (5.2, 9.9, 0.7, 1.8))):      # a few small irregular stains at the foot, not a ring
        w, l = w * p['pool'], l * p['pool']
        out.append(P((r0 * math.cos(a), 0.2, r0 * math.sin(a)), (l, 0.25, w), 'pool', f'stain{k}', ry(-a - 0.6), 'base'))
    for k in range(7):                                                 # roots: swollen lumps spreading across the footprint
        a = 2 * math.pi * (k + 0.3 * hashed(k)) / 7
        r0 = 7.8 + 1.3 * hashed(k, 1)
        out.append(P((r0 * math.cos(a), 1.2, r0 * math.sin(a)), (3.8 + hashed(k, 2), 1.6, 2.1), 'flesh_dark', f'root{k}', ry(-a), 'base'))
    for k in range(4):                                                 # pale blisters on the mound
        a = 2 * math.pi * (k + 0.5) / 4 + 0.4
        out.append(P((6.4 * math.cos(a), 3.2, 6.4 * math.sin(a)), (1.5, 1.2, 1.5), 'flesh', f'blister{k}', grp='base'))
    t = p['tendrils']
    if t > 0:                                                          # lashing tendrils out of the base
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8 + 0.2
            d = (math.cos(a), 0.0, math.sin(a))
            length = 9.0 * t * (0.8 + 0.4 * hashed(k, 7))
            pts = [(6.0 * d[0], 1.5, 6.0 * d[2])]
            for step, (frac, rise) in enumerate(((0.45, 2.6), (0.8, 4.4), (1.0, 3.6))):
                pts.append((d[0] * (6.0 + length * frac), 1.5 + rise * t, d[2] * (6.0 + length * frac)))
            for s in range(3):
                out.append(rod(pts[s], pts[s + 1], 0.75 - 0.18 * s, 'tendril', f'tendril{k}_{s}', 'base'))
    return out


def stem_parts(p):
    out = [P((0.0, 5.0, 0.0), (4.8, 5.0, 4.8), 'flesh', 'stem0'),
           P((0.4, 11.5, -0.3), (3.9, 4.4, 3.8), 'flesh', 'stem1', rz(deg(-4))),
           P((-0.4, 18.0, 0.3), (3.4, 4.4, 3.4), 'flesh', 'stem2', rz(deg(5))),
           P((0.0, 23.0, 0.0), (3.2, 2.6, 3.2), 'flesh', 'stem3')]
    for k, (c, r, rot) in enumerate((((-3.6, 7.6, 2.2), (1.6, 1.3, 1.3), 20), ((3.0, 16.6, 2.4), (1.3, 1.4, 1.1), -15), ((-2.2, 14.4, -3.0), (1.2, 1.5, 1.1), 10),
                                     ((2.6, 8.0, -3.4), (1.5, 1.2, 1.3), -25))):          # gnarled knots in the flesh
        out.append(P(c, r, 'flesh_dark', f'knot{k}', rz(deg(rot))))
    for k, (a, b) in enumerate((((3.6, 18.6, 0.8), (4.0, 13.0, 1.6)), ((3.0, 19.6, -2.6), (3.4, 15.0, -3.0)), ((-3.2, 18.4, 1.6), (-3.6, 11.0, 2.4)))):
        out.append(rod(a, b, 0.32, 'vein', f'vein{k}', 'stem', grow=0.2))                 # veins down the flesh
    return out




def arm_parts(p, shoulder, out_dir, a1, a2, l1, l2, name, phase):
    """A human arm growing out of the stem: upper arm, forearm, a palm and five fingers that open and curl."""
    limp = p['limp']
    a1 = a1 + p['arm_lift'] * (1 - limp) + 6 * math.sin(phase + p['twitch']) - limp * (a1 + 55)
    a2 = a2 + p['arm_lift'] * 1.4 * (1 - limp) + 14 * math.sin(phase * 1.7 + p['twitch'] * 2) - limp * (a2 + 70)
    o = unit((out_dir[0], 0.0, out_dir[2]))
    d1 = unit((o[0] * math.cos(deg(a1)), math.sin(deg(a1)), o[2] * math.cos(deg(a1))))
    elbow = add(shoulder, tuple(l1 * v for v in d1))
    d2 = unit((o[0] * math.cos(deg(a2)), math.sin(deg(a2)), o[2] * math.cos(deg(a2))))
    wrist = add(elbow, tuple(l2 * v for v in d2))
    out = [rod(shoulder, elbow, 0.68, 'skin', f'{name}u', 'stem', grow=0.4), rod(elbow, wrist, 0.52, 'skin', f'{name}f', 'stem', grow=0.3)]
    palm = add(wrist, tuple(1.0 * v for v in d2))
    out.append(P(palm, (1.45, 0.5, 1.35), 'hand', f'{name}p', along(d2)))                # a broad palm, lighter than the arm
    side = unit((d2[2], 0.0, -d2[0]))                                  # across the hand, horizontal
    up = unit((side[1] * d2[2] - side[2] * d2[1], side[2] * d2[0] - side[0] * d2[2], side[0] * d2[1] - side[1] * d2[0]))
    spread, curl = p['fingers'], p['curl']
    for i in range(4):                                                 # four long fingers, splayed so each is its own shape
        off = (i - 1.5) * spread / 1.35
        o_i = math.sin(deg(off))
        d = unit(tuple(d2[k] * math.cos(deg(off)) + side[k] * o_i for k in range(3)))
        d = unit(tuple(d[k] - up[k] * curl * 0.9 for k in range(3)))
        length = (2.6, 3.4, 3.6, 2.9)[i]
        start = add(palm, tuple(0.9 * d2[k] + side[k] * (i - 1.5) * 0.62 for k in range(3)))
        tip = add(start, tuple(length * v for v in d))
        out.append(rod(start, tip, 0.34, 'hand', f'{name}g{i}', 'stem', grow=0.05))
        out.append(P(tip, (0.36, 0.36, 0.36), 'hand', f'{name}n{i}', None))               # a rounded tip to each finger
    # the thumb: out to the side and forward, apart from the fingers
    d = unit(tuple(d2[k] * 0.55 + side[k] * 0.85 - up[k] * curl * 0.5 for k in range(3)))
    start = add(palm, tuple(0.1 * d2[k] + side[k] * 1.25 for k in range(3)))
    out.append(rod(start, add(start, tuple(2.3 * v for v in d)), 0.4, 'hand', f'{name}th', 'stem', grow=0.05))
    return out


def rat_parts(p):
    """A rat's head pushing out of the lower stem, snout first."""
    u = unit((0.5, -0.12 + 0.015 * p['rat'], 0.85))
    side = unit((-u[2], 0.0, u[0]))
    up = unit((side[1] * u[2] - side[2] * u[1], side[2] * u[0] - side[0] * u[2], side[0] * u[1] - side[1] * u[0]))
    base = (2.2, 4.8, 3.6)

    def at(a, b=0.0, c=0.0):
        return tuple(base[k] + u[k] * a + up[k] * b + side[k] * c for k in range(3))

    out = [P(at(1.0), (2.8, 2.5, 2.5), 'fur', 'ratneck', along(u)),
           P(at(3.4), (3.6, 2.4, 2.3), 'fur', 'rathead', along(u)),
           P(at(6.4, -0.3), (2.7, 1.5, 1.4), 'fur', 'ratsnout', along(u)),
           P(at(8.8, -0.4), (0.95, 0.85, 0.9), 'blood', 'ratnose'),
           P(at(7.0, -1.7, 0.0), (1.4, 0.5, 1.2), 'pink', 'ratjaw', along(u))]
    for z in (-1, 1):
        out.append(P(at(2.8, 1.7, z * 1.3), (0.72, 0.65, 0.65), 'eye', f'rateye{z}'))
        out.append(P(at(2.0, 2.2, z * 2.2), (1.15, 1.5, 0.45), 'pink', f'ratear{z}', rz(deg(10))))
        out.append(P(at(7.0, -1.2, z * 0.36), (0.38, 0.95, 0.32), 'bone', f'rattooth{z}', rz(deg(-8))))
    return out


def leg_parts(p, hip, sway, name, bend):
    """A human leg hanging limp from under the cap: thigh, shin and a foot, swinging a little."""
    out = []
    s1, s2 = deg(sway), deg(sway * 1.6 + bend)
    d1 = unit((0.35 * math.sin(s1), -math.cos(s1), 0.2 * math.sin(s1 + 1.0)))
    knee = add(hip, tuple(5.2 * v for v in d1))
    d2 = unit((0.6 * math.sin(s2) + 0.15, -math.cos(s2), 0.2 * math.sin(s2)))
    ankle = add(knee, tuple(5.2 * v for v in d2))
    out.append(rod(hip, knee, 1.5, 'skin', f'{name}t', 'cap', grow=0.4))
    out.append(rod(knee, ankle, 1.15, 'skin', f'{name}s', 'cap', grow=0.3))
    out.append(P(add(ankle, (0.9, -0.6, 0.0)), (2.0, 0.75, 1.0), 'skin', f'{name}foot', rz(deg(-12 - 20 * p['limp'])), 'cap'))
    return out


def cap_parts(p):
    out = [P(CAP_C, CAP_R, 'cap', 'cap', grp='cap'), P(LIP_C, LIP_R, 'cap', 'cap', grp='cap')]
    for k in range(48):                                                # the gill skirt under the lip: many overlapping slats of ONE piece, so it is a smooth skirt, with a teal-grey ridge every few
        a = 2 * math.pi * k / 48
        out.append(P((SKIRT_R * math.cos(a), 23.7, SKIRT_R * math.sin(a)), (0.7, 1.8, 1.0), 'gill_teal' if k % 8 == 4 else 'gill', 'gills', ry(-a), 'cap'))
    for k, (d, size) in enumerate((((0.6, 0.62, 0.3), 1.7), ((-0.4, 0.8, 0.45), 1.4), ((0.1, 0.78, -0.6), 1.6), ((-0.7, 0.55, -0.35), 1.2), ((0.78, 0.45, -0.4), 1.3), ((0.15, 0.97, 0.2), 1.0), ((-0.2, 0.5, 0.82), 1.1))):
        out.append(surface_disc(CAP_C[0], CAP_C[1], CAP_C[2], CAP_R, CAP_C, d, size, 'spot', f'spot{k}', 0.45))
        out[-1]['grp'] = 'cap'
    for a, pts, tines in ((-1.0, ((-0.4, 34.6, -3.0), (-1.2, 37.0, -4.4), (-0.8, 38.8, -5.6), (0.4, 39.8, -5.9)), ((1, (-3.0, 38.6, -5.2)), (2, (1.2, 40.8, -4.2)))),
                          (1.0, ((-0.2, 34.8, 3.4), (0.6, 36.8, 5.0), (0.2, 38.2, 6.4), (-0.9, 39.2, 6.8)), ((1, (2.4, 38.0, 6.4)), (2, (-2.2, 41.0, 5.4))))):
        for s in range(3):
            out.append(rod(pts[s], pts[s + 1], 0.78 - 0.14 * s, 'bone', f'antler{a}{s}', 'cap', grow=0.35))
        for idx, tip in tines:
            out.append(rod(pts[idx], tip, 0.5, 'bone', f'tine{a}{idx}', 'cap', grow=0.25))
    for k in range(10):                                                # blood dripping from the skirt
        a = 2 * math.pi * (k + 0.5 * hashed(k, 9)) / 10
        if 2.0 < a < 3.3:                                              # the legs hang here
            continue
        phase = (p['drip'] + 0.37 * k + 0.13 * hashed(k, 5)) % 1.0
        stretch = 1.0 + p['drip_len'] * (1.2 + 1.8 * math.sin(math.pi * phase))
        x, z = 9.0 * math.cos(a), 9.0 * math.sin(a)
        out.append(P((x, RIM_Y - stretch / 2, z), (0.4, stretch / 2 + 0.2, 0.4), 'blood', f'drip{k}', grp='cap'))
        if 0.45 < phase < 0.97 and not p['dead']:                       # a drop that has let go and is falling into the pool
            fall = (phase - 0.45) / 0.52
            y = RIM_Y - 1.5 - 20.0 * fall * fall
            if y > 0.8:
                out.append(P((x * 1.02, y, z * 1.02), (0.45, 0.65, 0.45), 'blood', f'drop{k}', grp='base'))
    return out


def anatomy(p):
    parts = base_parts(p) + stem_parts(p) + rat_parts(p) + cap_parts(p)
    parts += arm_parts(p, (2.6, 15.4, -1.8), (0.85, 0, -0.5), 6, 30, 5.8, 5.0, 'armA', 0.0)
    parts += arm_parts(p, (0.6, 11.4, 3.0), (0.35, 0, 0.94), 12, 38, 6.0, 5.2, 'armC', 4.2)
    parts += leg_parts(p, (-5.0, 22.9, 5.6), p['sway'] + 8, 'legA', 14 + 40 * p['limp'])
    parts += leg_parts(p, (-7.4, 22.9, 1.8), -p['sway'] * 0.8 - 4, 'legB', -8 + 50 * p['limp'])
    for k, (c, s) in enumerate(p['sparks']):
        parts.append(P(c, (s, s, s), 'spore', f'spark{k}', grp='base'))
    if p['ring']:
        r0, y0 = p['ring']
        for k in range(20):
            a = 2 * math.pi * k / 20
            parts.append(P((r0 * math.cos(a), y0, r0 * math.sin(a)), (1.0, 0.45, 1.0), 'spore', f'ring{k}', grp='base'))
    for k in range(p['streaks']):
        a = 2 * math.pi * (k + 0.5) / p['streaks']
        d = unit((math.cos(a), 0.45, math.sin(a)))
        length = 5.0
        c = tuple((0.0, 28.0, 0.0)[i] + d[i] * (length / 2 + 10.0) for i in range(3))
        parts.append(P(c, (length / 2, 0.38, 0.38), 'spore', f'streak{k}', along(d), 'base'))
    for k, (c, s) in enumerate(p['drops']):
        parts.append(P(c, (s, s * 1.3, s), 'blood', f'chip{k}', grp='base'))
    return parts


def place(p):
    """The boss in a pose: parts carried to where the pose puts them."""
    sx, sy = 1 + 0.045 * p['squash'], (1 - 0.055 * p['squash']) * (1 - p['sag'])
    pitch, roll = p['cap']
    Rcap = mm(rx(deg(roll)), rz(deg(pitch)))
    cs = p['cap_scale']
    g = mm(rx(deg(0)), rz(deg(p['lean'])))
    shift = (p['fwd'], 0.0, 0.0)
    pivot_y = CAP_PIVOT[1] * sy

    def carry(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    flash = p['flash']
    placed = []
    for q in anatomy(p):
        c, r, R = q['c'], q['r'], q['R']
        grp = q['grp']
        mat = 'pale' if flash and q['mat'] in ('flesh', 'flesh_dark', 'cap', 'cap_hi', 'skin', 'hand', 'fur') else q['mat']
        if grp in ('stem', 'cap'):
            c, r = (c[0] * sx, c[1] * sy, c[2] * sx), (r[0] * sx, r[1] * sy, r[2] * sx)
        if grp == 'cap':
            rel = (c[0] * cs, c[1] - pivot_y, c[2] * cs)
            rel = mv(Rcap, rel)
            c = (rel[0], rel[1] + pivot_y + p['cap_lift'], rel[2])
            r = (r[0] * cs, r[1], r[2] * cs)
            R = mm(Rcap, R)
        placed.append(dict(q, c=carry(c), r=r, R=mm(g, R), mat=mat))
    decals = []                                     # no face: the stem is smooth flesh where it was
    return placed, decals


# --- poses ---------------------------------------------------------------------------------
BASE = dict(lean=0, fwd=0, squash=0.0, sag=0.0, cap=(0, 0), cap_lift=0.0, cap_scale=1.0, fingers=24, curl=0.25, arm_lift=0, twitch=0.0, mouth=0.4,
            drip=0.0, drip_len=1.0, sway=0, flash=False, eyes='open', limp=0.0, tendrils=0.0, ring=None, streaks=0, sparks=[], drops=[], rat=0, pool=1.0, dead=False)


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def idle(k, n=8):
    """A slow breath: the cap pulses, the hands twitch, the legs sway, the mouth works and blood drips (the drips come round exactly once)."""
    ph = 2 * math.pi * k / n
    t = math.sin(ph)
    return pose(squash=-0.7 * t, cap_scale=1.0 + 0.022 * t, cap_lift=0.3 * t, cap=(1.2 * math.sin(ph + 1.0), 0.8 * math.sin(ph + 2.0)), twitch=ph, fingers=24 + 8 * math.sin(2 * ph),
                curl=0.25 + 0.15 * math.sin(ph + 0.5), sway=6 * math.sin(ph), mouth=0.4 + 0.25 * math.sin(ph + 0.8), drip=k / n, rat=2 * math.sin(ph + 2.0))


SPARKS = [((-9.0, 33.0, 3.0), 0.5), ((8.0, 35.0, -4.0), 0.45), ((12.0, 26.0, 5.0), 0.4), ((-11.0, 27.0, -4.0), 0.45), ((-4.0, 43.0, 1.0), 0.4), ((-2.0, 14.0, 8.5), 0.4)]
DROPS = [((9.0, 16.0, 4.0), 0.7), ((-7.0, 19.0, -6.0), 0.6), ((6.5, 10.0, -8.0), 0.6), ((-9.0, 9.0, 3.0), 0.5)]

POSES = {
    # braced: the cap swollen, the hands open, spores rising round the cap
    'charging': [pose(squash=-0.6, cap_scale=1.04, cap_lift=0.5, arm_lift=8, fingers=36, curl=0.0, mouth=0.7, sparks=SPARKS, drip=0.2, drip_len=1.4)],
    # a pulse: gather (it sinks, the hands curl), burst (a ring of spores, the mouth wide), the tendrils lash, settle
    'attack': [
        pose(squash=1.2, cap_scale=0.96, cap_lift=-0.5, cap=(-6, 0), arm_lift=-18, fingers=10, curl=0.9, mouth=0.0, drip=0.1),
        pose(squash=-1.0, cap_scale=1.08, cap_lift=1.4, cap=(5, 0), arm_lift=26, fingers=52, curl=0.0, mouth=1.0, ring=(8.0, 5.0), tendrils=0.5, sparks=SPARKS, drip=0.5),
        pose(squash=-0.6, cap_scale=1.06, cap_lift=1.0, cap=(9, 3), arm_lift=18, fingers=56, curl=0.0, mouth=1.0, ring=(13.0, 4.0), tendrils=1.0, drip=0.7, drip_len=1.6),
        pose(squash=0.3, cap_scale=1.0, arm_lift=-4, fingers=24, curl=0.3, mouth=0.4, tendrils=0.35, drip=0.9),
    ],
    # a great roar: the cap thrown up, the mouth wide, the arms flung out, spores streaking out
    'release': [pose(squash=-1.2, cap_scale=1.1, cap_lift=1.0, cap=(-7, 0), arm_lift=34, fingers=60, curl=0.0, mouth=1.0, eyes='open', streaks=10, ring=(7.0, 10.0), drip=0.3, drip_len=1.8)],
    # a flinch: flashed pale, hunched away from the blow, the hands recoiling, drops flying
    'damage': [pose(flash=True, lean=4, fwd=-0.5, squash=1.0, cap_scale=0.97, cap=(8, 3), arm_lift=-30, fingers=12, curl=0.9, mouth=0.9, eyes='shut', sway=-14, drops=DROPS, drip_len=1.6)],
    # badly hurt: the cap sagging and tilted, the limbs limp, blood running
    'weak': [pose(sag=0.14, squash=0.8, cap_lift=-1.6, cap=(11, 6), cap_scale=0.98, limp=0.6, fingers=10, curl=0.8, mouth=0.2, eyes='shut', sway=10, drip_len=2.0, drip=0.5, pool=1.08, rat=-6)],
    # dead: collapsed, the cap slumped on the base, the limbs hanging, a spreading pool
    'dead': [pose(sag=0.46, squash=0.6, cap_lift=-2.5, cap=(16, 8), cap_scale=1.0, limp=1.0, fingers=8, curl=1.0, mouth=0.9, eyes='shut', drip_len=0.4, pool=1.1, rat=-10, dead=True)],
    'walking': [idle(k) for k in range(8)],
}


# --- the boss's sprites --------------------------------------------------------------------
BOSS_CELL = conventions.BOSS_CELL
ANCHOR = conventions.BOSS_ANCHOR       # the middle of the 2 x 2 footprint, on the ground
GROUND = conventions.BOSS_GROUND       # the lowest painted row of a standing frame
RENDER_SCALE = 1.8                     # pixels to a model unit: the tall cap and the roar (the highest frame is 85 rows) must fit the cell
RENDER_ORIGIN = (BOSS_CELL / 2, 80.0)          # low in the cell, so the tall cap and antlers are not cut off at the top while drawing; the frame is then put on the ground row
ACTIONS = [('charging', 1), ('attack', 4), ('release', 1), ('damage', 1), ('weak', 1), ('dead', 1), ('walking', 8)]


def render_pose(p, facing, origin=None):
    parts, decals = place(p)
    return cr.render_frame(parts, decals, facing, origin or RENDER_ORIGIN, RAMPS, RENDER_SCALE)


def shift_frame(rows, dx, dy):
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


def build_frames(cache=None):
    """Every action's frames in both facings on a 96 x 96 cell with the base on the ground row. `cache` (a JSON file) keeps the raw drawings: change a pose or the model and delete it."""
    import json
    raw = json.loads(Path(cache).read_text()) if cache and Path(cache).exists() else {}
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
    old = cr.CELL
    cr.CELL = BOSS_CELL
    cr.TALL_EYES, cr.EYE_WHITE, cr.EYE_COLOUR, cr.EYE_PUPIL, cr.EYE_REACH = True, 't', 'j', None, 1.4
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
    return conventions.check_ramps(RAMPS, 'blood-mushroom') + conventions.check_boss('blood-mushroom', frames_by_pose)


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
        img.save(Path(folder) / f'blood-mushroom-{pose_id}.png')
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
        contact.save(preview)


class BloodMushroom:
    name = 'blood-mushroom'
    kind = 'boss'
    airborne = set()
    ramps = RAMPS
    scale = 1.0
    stand = pose()
    tall_eyes = True
    eye_white = 't'
    eye_colour = 'j'
    eye_reach = 1.4
    poses = POSES

    @staticmethod
    def place(p):
        return place(p)


CREATURE = BloodMushroom()


def main():
    parser = argparse.ArgumentParser(description='The blood mushroom, a 2 x 2 boss.')
    parser.add_argument('out', type=Path, nargs='?', help='folder for the sprite sheets, e.g. sprites/blood-mushroom')
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
        print(f'3D preview of the blood mushroom ({args.pose}, frame {args.frame + 1}) -> {args.model}; no sprites were made')
    elif args.out:
        frames = build_frames(Path(args.out) / 'raw.json')
        problems = check(frames)
        if problems and not args.force:
            print('the blood mushroom breaks the boss rules, so nothing was written (--force to write anyway):', file=sys.stderr)
            for q in problems:
                print('  ' + q, file=sys.stderr)
            sys.exit(1)
        write_sprites(args.out, frames, args.preview)
        print(f'wrote the sheets -> {args.out}' + (f' ({len(problems)} problems, forced)' if problems else ''))
    else:
        parser.error('say where to write the sprites, or use --model to see the 3D model first')


if __name__ == '__main__':
    main()
