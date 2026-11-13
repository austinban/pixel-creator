#!/usr/bin/env python3
"""A stone totem: a tall, square-cut carved pillar, a stationary magical idol that stands on its tile and never walks.

A creature, not a person (see creature.py and make_mushroom.py), but an object more than a creature: weathered grey-teal stone in stacked square blocks with flat faces and sharp edges (see `block`), a moai-like carved face (a heavy brow ridge over deep-set slit eyes, a long nose,
thin lips, a jutting chin, long ears), arms carved down the torso with the hands on the belly, on the FRONT only, moss on its shoulders, rune lines that glow gold, and a crystal floating in a hollow at the top. No arms, no legs, no weapon. It is kin to the rock monsters
(the same stone colours) but plainer.

    NE  seen from behind: no face, but the runes go all the way round
    SE  seen from the front, with the face

"Walking" is its idle: a slow breath in which the crystal brightens and dims, the runes flicker and one pebble drifts up and falls. "Attack" is a pulse: gather, flare, a ring of light, settle.

    python3 tools/make_stonetotem.py --model previews/stonetotem-3d.png      look at the 3D model first
    python3 tools/make_stonetotem.py sprites/stone-totem [--preview sheet.png]
    python3 tools/extract_poses.py --merge stone-totem=sprites/stone-totem
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assetkit import normalise  # noqa: E402
from creature import add, deg, mm, mv, part, run, rx, ry, rz, sub  # noqa: E402
from make_rockmonster import along  # noqa: E402

RAMPS = {
    'stone': ('q', 'p', 'l', 'k'),           # teal, steel, lavender, indigo: the rock monsters' stone
    'dark': ('p', 'l', 'k', 'w'),            # carved rings, the brow and the hollow's rim
    'pale': ('t', 't', 'r', 'q'),            # the stone flashed pale when it is hit
    'moss': ('z', 'A', 'B', 's'),
    'hollow': ('w', 'x', 'x', 'x'),
    'crack': ('w', 'w', 'x', 'x'),
    'rune_hi': ('d', 'd', 'b', 'b'),         # a rune at full glow: yellow, amber
    'rune_mid': ('b', 'b', 'a', 'a'),        # amber, orange
    'rune_off': ('k', 'k', 'w', 'w'),        # a rune gone dark
    'crystal_lo': ('b', 'a', 'g', 'w'),
    'crystal_mid': ('d', 'b', 'a', 'g'),
    'crystal_hi': ('t', 'd', 'b', 'a'),
    'crystal_flare': ('t', 't', 't', 'd'),   # white-gold
    'crystal_dead': ('l', 'k', 'w', 'x'),    # dull and dark
    'light': ('t', 't', 'd', 'd'),           # rings, sparks and streaks of light
}

# the blocks, bottom to top: (centre, half-sizes): square-cut, a slim shaft on a wide plinth, and taller than it was
BASE = ((0.0, 0.9, 0.0), (4.7, 0.9, 4.7))         # a rough platform
LOWER = ((0.0, 5.2, 0.0), (3.4, 3.4, 3.6))        # the long shaft
RIM = ((0.0, 10.9, 0.0), (3.8, 2.2, 3.5))         # the shoulders: a wider, darker tier
UPPER = ((0.0, 17.6, 0.0), (3.2, 4.5, 2.8))       # the head: a tall slab, deeper than it is wide
CAP = ((0.0, 22.8, 0.0), (2.4, 0.5, 2.0))         # the topknot, a flat block that holds the crystal
PIVOT = (0.0, 1.0, 0.0)             # it leans about its base, which never moves
CRYSTAL_Y = 25.1


TURN = {'base': 6, 'lower': -3, 'rim': 4, 'head': -2}          # each tier is turned a little, as hand-cut stone is


def block(c, r, mat, name, R=None):
    """A square-edged block: `part` with flat faces."""
    return part(c, r, mat, name, R, box=True)
# the runes: (azimuth, elevation, block, size, turn): where on a block they sit, and how the bar is turned. Azimuth 0 is the front (the face is on the upper block, so its front has none).
# (the runes sit on the torso and the sides and back of the head; the face is left bare)
RUNES = [
    (0, 18, 'lower', 0.62, 90), (0, -22, 'lower', 0.5, 0), (-24, -2, 'lower', 0.5, 90), (26, 2, 'lower', 0.5, 45),
    (62, 8, 'lower', 0.6, 90), (88, -14, 'lower', 0.5, 0), (116, 14, 'lower', 0.55, 90), (-64, 10, 'lower', 0.6, 90),
    (-94, -16, 'lower', 0.5, 0), (-120, 12, 'lower', 0.55, 45), (150, -4, 'lower', 0.6, 90), (180, 16, 'lower', 0.6, 90),
    (178, -26, 'lower', 0.5, 0), (-150, 4, 'lower', 0.55, 90), (60, 20, 'upper', 0.5, 90), (-60, 18, 'upper', 0.5, 0),
    (118, 10, 'upper', 0.55, 90), (-118, 12, 'upper', 0.55, 45), (180, 14, 'upper', 0.6, 90), (150, -8, 'upper', 0.5, 0), (-150, -6, 'upper', 0.5, 90),
]
FLICKER = [  # which runes are lit in each idle frame
    {0, 2, 3, 5, 7, 8, 11, 12, 14, 16, 19}, {1, 2, 4, 5, 7, 9, 11, 13, 15, 16, 18, 20}, {0, 2, 3, 6, 8, 9, 11, 12, 14, 17, 19, 20}, {1, 3, 4, 6, 7, 10, 12, 13, 15, 17, 18},
    {0, 2, 4, 5, 8, 10, 11, 13, 14, 16, 19}, {1, 3, 5, 6, 8, 9, 12, 13, 15, 16, 20}, {0, 2, 3, 6, 7, 10, 11, 12, 14, 18, 19}, {1, 4, 5, 7, 9, 10, 13, 15, 17, 18, 20},
]


def rune_direction(az, el):
    a, e = deg(az), deg(el)
    return (math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a))


def runes_for(p):
    """The glyph discs, lit or dark: `runes` is 'hi', 'mid', 'off', or a set of the rune numbers that are lit."""
    state = p['runes']
    out = []
    for k, (az, el, which, size, turn) in enumerate(RUNES):
        if state == 'off':
            mat = 'rune_off'
        elif isinstance(state, set):
            mat = 'rune_mid' if k in state else 'rune_off'
        else:
            mat = 'rune_' + state
        centre, radii = LOWER if which == 'lower' else UPPER
        d = rune_direction(az, el)
        # where the line from the middle of the block leaves it, and which face that is
        t = min(radii[i] / abs(d[i]) for i in range(3) if abs(d[i]) > 1e-9)
        face = min((i for i in range(3) if abs(d[i]) > 1e-9), key=lambda i: radii[i] / abs(d[i]))
        pt = tuple(centre[i] + d[i] * t for i in range(3))
        long, short = size * 0.75, size * 0.2
        tangents = [i for i in range(3) if i != face]                         # a bar lying flat on that face: long one way, thin the other
        sizes = [0.0] * 3
        sizes[face] = 0.22
        sizes[tangents[0]], sizes[tangents[1]] = (long, short) if turn == 90 else (short, long) if turn == 0 else (size * 0.55, size * 0.4)
        out.append(block(pt, tuple(sizes), mat, 'rune%d' % k))
    return out


def anatomy(p):
    """The totem standing, in the standing frame: the stone, the runes, the crystal and any light."""
    stone = 'pale' if p['flash'] else 'stone'
    dark = 'pale' if p['flash'] else 'dark'
    parts = [
        block(BASE[0], BASE[1], stone, 'base', ry(deg(TURN['base']))),
        block(LOWER[0], LOWER[1], stone, 'lower', ry(deg(TURN['lower']))),
        block(RIM[0], RIM[1], dark, 'rim', ry(deg(TURN['rim']))),
        block((4.4, 0.6, 3.2), (0.9, 0.6, 0.8), stone, 'rubble0', ry(deg(25))),        # fallen stones at the foot
        block((-3.0, 0.5, -5.0), (1.1, 0.5, 0.9), dark, 'rubble1', ry(deg(-20))),
        block((-5.2, 0.4, 2.6), (0.7, 0.4, 0.7), stone, 'rubble2', ry(deg(40))),
    ]
    if p['broken']:                                    # the top knocked off: a lower, slanting stump
        parts += [block((-0.5, 15.6, 0.0), (3.2, 3.8, 2.8), stone, 'head', rz(deg(-9))), block((0.4, 19.4, 0.9), (2.2, 0.8, 1.9), 'crack', 'break', rz(deg(-18)))]
    else:
        parts += [
            block(UPPER[0], UPPER[1], stone, 'head', mm(rz(deg(2)), ry(deg(TURN['head'])))),
            block((3.45, 20.0, 0.0), (0.8, 0.6, 3.0), dark, 'brow'),                    # a heavy brow ridge, wider than the face
            block((3.15, 18.7, -1.4), (0.25, 0.6, 0.85), 'hollow', 'head'),             # the eye sockets
            block((3.15, 18.7, 1.4), (0.25, 0.6, 0.85), 'hollow', 'head'),
            block((3.55, 16.6, 0.0), (0.7, 2.6, 0.8), stone, 'nose'),                   # a long nose
            block((3.4, 12.8, 0.0), (0.5, 0.9, 1.5), stone, 'chin'),                    # a jutting chin
            block((0.0, 16.6, 3.0), (1.0, 2.8, 0.35), stone, 'ear', ry(deg(-6))),       # long ears: the silhouette is wider here
            block((0.0, 15.8, -3.0), (0.9, 2.3, 0.3), stone, 'ear', ry(deg(8))),
            block(CAP[0], CAP[1], dark, 'cap', ry(deg(10))),
            block((0.0, 23.35, 0.0), (1.5, 0.12, 1.2), 'hollow', 'hollow'),
        ]
    parts += [
        part((-2.6, 1.9, 4.3), (1.7, 0.6, 1.4), 'moss', 'moss0', rx(deg(-25))),
        part((4.0, 1.8, -3.9), (1.4, 0.55, 1.2), 'moss', 'moss1', rx(deg(20))),
        part((-0.4, 13.2, 3.5), (1.3, 0.45, 0.6), 'moss', 'moss2'),
        part((0.5, 20.8, 1.2), (0.9, 0.35, 0.8), 'moss', 'moss3'),
        part((-3.2, 8.0, 1.5), (0.5, 1.8, 0.8), 'moss', 'moss4'),                   # a streak down the side of the shaft
    ]
    parts += runes_for(p)
    # cracks down the front of the stone
    if p['cracks']:
        for k, (c, r, rot) in enumerate((((3.5, 6.6, -1.5), (0.2, 2.2, 0.3), -8), ((3.5, 2.8, 1.8), (0.2, 1.2, 0.3), 12), ((3.4, 21.4, -1.6), (0.2, 1.5, 0.3), 8), ((-3.5, 5.0, 2.4), (0.2, 2.4, 0.3), -10))):
            parts.append(block(c, r, 'crack', 'crack%d' % k, rz(deg(rot))))
    # the crystal, floating over the hollow, and the pebble that drifts
    if p['crystal']:
        parts.append(part((0.0, CRYSTAL_Y + p['bob'], 0.0), (1.05, 1.65 * p['crystal_size'], 1.05), 'crystal_' + p['crystal'], 'crystal'))
    if p['pebble'] is not None:
        parts.append(block((5.9, 6.0 + p['pebble'], 1.8), (0.55, 0.5, 0.55), stone, 'pebble', rz(0.5)))
    # light: a ring leaving the body, sparks, streaks, chips
    if p['ring']:
        r0, y0 = p['ring']
        for k in range(18):
            a = 2 * math.pi * k / 18
            parts.append(part((r0 * math.cos(a), y0, r0 * math.sin(a)), (1.0, 0.35, 1.0), 'light', 'ring%d' % k))
    for k, (x, y, z, s) in enumerate(p['sparks']):
        parts.append(part((x, y, z), (s, s, s), 'light', 'spark%d' % k))
    for k in range(p['streaks']):
        a = 2 * math.pi * (k + 0.5) / p['streaks']
        d = normalise((math.cos(a), 0.55, math.sin(a)))
        length = 3.0
        c = tuple((0.0, CRYSTAL_Y, 0.0)[i] + d[i] * (length / 2 + 2.3) for i in range(3))
        parts.append(part(c, (length / 2, 0.3, 0.3), 'light', 'streak%d' % k, along(d)))
    for k, (x, y, z, s) in enumerate(p['chips']):
        parts.append(block((x, y, z), (s, s * 0.8, s), stone, 'chip%d' % k, rz(k * 0.8)))
    return parts


def pile(p):
    """Destroyed: a low heap of broken stone, with the dull dark shard of the crystal on top."""
    out = []
    for k, (c, r, rot, mat) in enumerate((
            ((0.0, 1.2, 0.0), (5.0, 1.3, 4.6), 0, 'stone'), ((-2.4, 2.2, 1.6), (2.8, 1.5, 2.3), -18, 'dark'), ((2.2, 2.0, -1.6), (2.7, 1.4, 2.4), 22, 'stone'),
            ((0.3, 3.1, 0.2), (2.4, 1.3, 2.2), 8, 'dark'), ((-3.7, 1.0, -2.8), (1.7, 0.9, 1.5), 30, 'stone'), ((3.9, 0.9, 2.9), (1.6, 0.9, 1.4), -25, 'dark'),
            ((-0.6, 4.2, -0.8), (1.5, 1.0, 1.4), -12, 'stone'))):
        out.append(block(c, r, mat, 'rock%d' % k, rz(deg(rot))))
    out.append(part((-1.2, 3.0, 3.4), (1.4, 0.55, 1.1), 'moss', 'moss0', rx(deg(-30))))
    out.append(part((0.9, 5.0, 0.6), (0.9, 1.35, 0.8), 'crystal_dead', 'shard', rz(deg(24))))
    k = 1.15                                            # the heap is drawn larger than the standing totem's blocks: it has less to show at the smaller scale
    return [dict(q, c=tuple(x * k for x in q['c']), r=tuple(x * k for x in q['r'])) for q in out]


def place(p):
    """The totem in a pose: parts carried to where the pose puts them."""
    if p['dead']:
        return pile(p), []
    s = p['squash']
    sx, sy = 1 + 0.08 * s, 1 - 0.1 * s
    g = mm(rx(deg(p['roll'])), rz(deg(p['lean'])))
    shift = (p['fwd'], 0.0, 0.0)

    def carry(pt):
        return add(add(PIVOT, mv(g, sub(pt, PIVOT))), shift)

    placed = []
    for q in anatomy(p):
        c, r = q['c'], q['r']
        if q['part'] not in ('crystal', 'pebble') and not q['part'].startswith(('ring', 'spark', 'streak', 'chip')):
            c, r = (c[0] * sx, c[1] * sy, c[2] * sx), (r[0] * sx, r[1] * sy, r[2] * sx)
        placed.append(dict(q, c=carry(c), R=mm(g, q['R']), r=r))
    decals = []
    if p['eyes']:
        for side in (-1, 1):
            decals.append((carry((3.4 * sx, 18.7 * sy, side * 1.4 * sx)), 'shut'))
    return placed, decals


# --- poses -------------------------------------------------------------------------------
BASE_POSE = dict(lean=0, roll=0, fwd=0, squash=0.0, runes='mid', crystal='mid', crystal_size=1.0, bob=0.0, flash=False, broken=False, cracks=False, eyes=True,
                 pebble=None, ring=None, sparks=[], streaks=0, chips=[], dead=False)


def pose(**kw):
    p = dict(BASE_POSE)
    p.update(kw)
    return p


def idle(k, n=8):
    """A slow breath: the crystal brightens and dims, the runes flicker, one pebble drifts up and falls. The stone barely moves."""
    t = math.sin(2 * math.pi * k / n)
    crystal = 'hi' if t > 0.55 else 'mid' if t > -0.45 else 'lo'
    rise = math.sin(math.pi * k / (n - 1))
    return pose(crystal=crystal, bob=0.45 * t, crystal_size=1.0 + 0.08 * t, runes=FLICKER[k], pebble=4.6 * rise if k < n - 1 else None, squash=-0.06 * t)


class StoneTotem:
    name = 'stone-totem'
    kind = 'creature'
    ramps = RAMPS
    scale = 0.9
    eye_colour = 'd'                    # gold slit eyes
    eye_reach = 1.6
    stand = pose()

    poses = {
        # charged up: every rune lit, the crystal bright, a few sparks round the top
        'charging': [pose(runes='hi', crystal='hi', bob=0.5, sparks=[(2.6, 26.4, 1.6, 0.35), (-2.4, 27.0, -1.0, 0.3), (1.0, 27.4, -2.2, 0.3), (-1.4, 25.6, 2.5, 0.3), (3.0, 24.4, -1.2, 0.3)])],
        # a pulse: gather (the runes dim, it sinks a little), the crystal flares, a ring of light leaves the body, settle
        'attack': [
            pose(runes='off', crystal='lo', squash=1.0, crystal_size=0.85, bob=-0.5),
            pose(runes='hi', crystal='flare', crystal_size=1.35, bob=0.9, squash=-0.4, sparks=[(0.0, 27.2, 0.0, 0.45)]),
            pose(runes='hi', crystal='flare', crystal_size=1.1, bob=0.6, ring=(7.5, 9.0), streaks=0),
            pose(runes='mid', crystal='mid', squash=0.3, bob=0.0),
        ],
        # the burst: the crystal at its brightest, leaning back, light streaking out
        'release': [pose(runes='hi', crystal='flare', crystal_size=1.3, bob=0.3, lean=5, streaks=8, sparks=[(0.0, 27.8, 0.0, 0.4)])],
        # hit: flashed pale, the runes dark, chips flying, tilted away from the blow
        'damage': [pose(runes='off', crystal='lo', flash=True, lean=4, fwd=-0.4, eyes=False, chips=[(5.2, 17.5, 3.2, 0.65), (-4.4, 19.0, -2.6, 0.55), (6.0, 8.0, -1.8, 0.5), (-5.2, 6.5, 3.0, 0.45)])],
        # badly damaged: cracked all down the front, the top broken off, the crystal dim
        'weak': [pose(runes='off', crystal='lo', crystal_size=0.8, broken=True, cracks=True, lean=-3, bob=-1.3)],
        # destroyed: a low pile with the dull dark shard
        'dead': [pose(dead=True)],
        'walking': [idle(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = StoneTotem()

if __name__ == '__main__':
    run(CREATURE)
