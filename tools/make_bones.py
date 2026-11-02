#!/usr/bin/env python3
"""A skeleton: the Slim build, stripped to the bone (see make_slim.py and humanoid.py).

The same proportions and poses as the Slim, so the lean, the walk and the weapon hand come with it, but
with almost nothing to it: thin limbs, a narrow dark chest with a cage of ribs round it and a spine
behind, a bare skull with deep eye sockets and a loose jaw. Everything is palette roles, so it recolours
like the rest. (The original skeleton is a different, hand-made character; this one is built like
the other people so it can use their poses, the bow animation and the weapons.)

    python3 tools/make_bones.py --model previews/bones-3d.png        look at the 3D model first
    python3 tools/make_bones.py sprites/bones [--preview sheet.png]
    python3 tools/extract_poses.py --merge bones=sprites/bones
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_slim  # noqa: E402

import math  # noqa: E402

from creature import deg, mm, mv, part, rx, ry, rz  # noqa: E402
from humanoid import Humanoid, run  # noqa: E402

HEAD_Y = 18.6                    # the middle of the head, from BODY in humanoid.py
BULK = 0.5                       # how thick the limbs and body are (the Slim is 1.0)
RIBS = 4                         # how many ribs show
BONE = ('t', 'C', 'p', 'k')      # lit, base, shade, deep: pale bone down to a blue-grey shadow


def gear(j, pose):
    """The rib cage, the spine, the jaw and the eye sockets. All follow the body or the head."""
    R, HR = j['body_R'], j['head_R']
    parts = []
    for i in range(RIBS):                                # a ring round the dark chest, narrower towards the top
        y = 9.8 + 1.0 * i
        width = 3.0 - 0.28 * i
        parts.append(part(j['body'](0.0, y, 0.0), (width, 0.36, width * 0.82), 'bone', 'torso', R))
    parts.append(part(j['body'](-1.4, 11.4, 0.0), (0.55, 3.6, 0.6), 'bone', 'torso', R))    # the spine
    parts.append(part(j['body'](0.0, 14.4, 0.0), (0.45, 0.45, 2.6), 'bone', 'torso', R))    # the collar bone
    parts.append(part(j['head'](1.8, HEAD_Y - 3.5, 0.0), (3.0, 1.2, 3.2), 'jaw', 'head', HR))    # the jaw
    for side in (-1, 1):                                  # deep tall sockets
        parts.append(part(j['head'](4.0, HEAD_Y + 0.3, side * 1.95), (0.9, 1.7, 1.0), 'socket', 'head', HR))
    return parts


def long_bone(c, length, spin, name, thick=0.5):
    """A long bone lying on the ground: a thin shaft with a double knob at each end, like a real bone.

    `c` is where its middle is, `spin` how many degrees it is turned about the vertical. Every piece shares
    one name, so the bone is drawn as one thing.
    """
    a = deg(spin)
    along = (math.cos(a), 0.0, -math.sin(a))               # the way the shaft runs
    across = (math.sin(a), 0.0, math.cos(a))               # the way the two lobes of a knob sit apart
    R = ry(a)
    knob = thick * 1.45
    y = knob * 0.85
    parts = [part((c[0], y, c[2]), (length / 2, thick * 0.8, thick * 0.8), 'bone', name, R)]
    for end in (-1, 1):
        for lobe in (-1, 1):
            at = tuple(c[k] + along[k] * end * length / 2 + across[k] * lobe * knob * 0.62 for k in (0, 1, 2))
            parts.append(part((at[0], y, at[2]), (knob * 0.95, knob * 0.9, knob * 0.9), 'bone', name, R))
    return parts


def rib(c, radius, spin, name, lift=0.0):
    """One rib: an arc of small pieces laid on the ground, open at the back."""
    parts = []
    for k in range(7):
        t = deg(-75 + 25 * k)
        local = (radius * math.cos(t), 0.0, radius * math.sin(t) * 0.85)
        at = mv(ry(deg(spin)), local)
        facing = math.atan2(-math.cos(t), -math.sin(t)) + deg(spin)
        parts.append(part((c[0] + at[0], 0.5 + lift, c[2] + at[2]), (0.75, 0.42, 0.42), 'bone', name, ry(facing)))
    return parts


def pelvis(c, spin):
    """The pelvis: two broad wings tipped towards each other, a sacrum between them."""
    parts = []
    for side in (-1, 1):
        at = mv(ry(deg(spin)), (0.0, 0.0, side * 1.5))
        parts.append(part((c[0] + at[0], 1.0, c[2] + at[2]), (1.5, 1.7, 0.5), 'bone', 'pelvis',
                          mm(ry(deg(spin)), rx(deg(-side * 38)))))
    at = mv(ry(deg(spin)), (-0.9, 0.0, 0.0))
    parts.append(part((c[0] + at[0], 0.8, c[2] + at[2]), (0.8, 0.9, 0.8), 'bone', 'pelvis', ry(deg(spin))))
    return parts


def pile(pose):
    """He has broken apart: a skull on its side, a loose jaw, a heap of ribs, and bones strewn about.

    Used for the dead pose only (see the tweaks below). Everything is laid on the ground, y = 0.
    """
    parts = []
    R_skull = mm(ry(deg(-30)), mm(rx(deg(35)), rz(deg(-12))))        # on its side, face turned up and away
    skull = (2.0, 3.6, -1.6)
    parts.append(part(skull, (4.8, 4.6, 4.5), 'bone', 'head', R_skull))
    for side in (-1, 1):                                                # the sockets, on the face
        off = mv(R_skull, (4.0, 0.3, side * 1.95))
        parts.append(part(tuple(skull[i] + off[i] for i in range(3)), (0.9, 1.7, 1.0), 'socket', 'head', R_skull))
    parts.append(part((-3.6, 1.0, 2.6), (3.0, 1.2, 3.2), 'jaw', 'jaw', mm(ry(deg(40)), rz(deg(14)))))   # the jaw, loose
    parts += rib((-3.0, 0, -4.2), 2.6, 10, 'rib0') + rib((-2.6, 0, -4.0), 2.2, 25, 'rib1', 0.5) + rib((-2.2, 0, -3.8), 1.8, 40, 'rib2', 1.0)
    parts += pelvis((4.2, 0, 2.8), 25)
    parts += long_bone((5.2, 0, -1.2), 7.0, 80, 'femurL', 0.55)         # two thigh bones
    parts += long_bone((1.5, 0, 5.4), 7.0, 15, 'femurR', 0.55)
    parts += long_bone((-1.0, 0, -5.8), 7.0, -10, 'tibia', 0.45)         # a shin
    parts += long_bone((-5.0, 0, 4.8), 5.6, 140, 'humerus', 0.42)        # an arm bone
    parts.append(part((-3.4, 0.8, -7.4), (1.8, 0.8, 1.0), 'bone', 'foot', ry(deg(70))))           # and a foot
    return parts, []


CREATURE = Humanoid(
    'bones',
    ramps={
        'skin': BONE, 'pants': BONE, 'shoes': BONE, 'belt': BONE, 'bone': BONE,
        'shirt': ('w', 'x', 'x', 'x'),           # the chest is a dark gap behind the ribs
        'jaw': ('C', 'p', 'k', 'w'),
        'socket': ('k', 'w', 'x', 'x'),
    },
    body=dict(make_slim.CREATURE.body, bulk=BULK, shoulder_z=2.7, hip_z=1.1, sleeve_mat='bone', ears=False),
    scale=1.16,                                  # a little taller than the Slim: a bare skull has no hair to add height
    # a flinch crouches less, or this thin figure ends up shorter than the damage pose should be
    tweaks={'damageSE': {'lift': -3.4, 'sway': 3.5}, 'damageNE': {'lift': -3.4},
            'deadNE': {'pile': True}, 'deadSE': {'pile': True},
            # his taller skull leaves less room above, so the jump is a little lower there
            'releaseNE': {'lift': -0.4, 'head_pitch': -12}},
    hair='none',                                 # a bare skull
    accessories=gear,
    calibrate_like=make_slim.CREATURE,           # drawn on the Slim's grid, so the walk samples identically
)

CREATURE.pile = pile

if __name__ == '__main__':
    run(CREATURE)
