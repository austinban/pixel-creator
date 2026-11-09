#!/usr/bin/env python3
"""A leech: a fat, glossy, ringed worm of deep maroon, the lowest and simplest shape of the blood enemies.

A creature (see creature.py, make_puffball.py and make_mycelium_crawler.py): a chain of eight overlapping ellipsoids, plump in the middle and tapering at both ends, alternately deep maroon and a paler
coral so the body reads as rings, a paler belly along the underside, two cream eyespots, a round toothed sucker at the front (a pale lip round a dark throat with a ring of cream teeth) and a flat sucker
at the back. It has no legs. It walks like an inch-worm: the front stretches out, the back sucks on and the body arches as the rear is pulled up behind. The attack coils, lunges and clamps; the release is
reared up and swollen with the mouth wide; and when it dies it bursts, a flat ragged husk with blood spattered round it. All palette roles (no yellow), so it recolours like the rest.

    python3 tools/make_leech.py --model previews/leech-3d.png      look at the 3D model first
    python3 tools/make_leech.py sprites/leech [--preview sheet.png]
    python3 tools/extract_poses.py --merge leech=sprites/leech
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import deg, mm, part, run, ry, rz  # noqa: E402

RAMPS = {
    'body': ('e', 'h', 'w', 'x'),         # deep maroon: coral, magenta-dark, grape, eggplant
    'ring': ('c', 'e', 'h', 'w'),         # the paler rings: salmon, coral, magenta-dark, grape
    'belly': ('t', 'c', 'e', 'h'),        # the underside: cream, salmon, coral, magenta-dark
    'lip': ('c', 'e', 'h', 'w'),          # the sucker's rim
    'throat': ('g', 'w', 'x', 'x'),       # the dark inside of the mouth
    'tooth': ('t', 't', 'C', 'c'),
    'eye': ('t', 't', 'C', 'c'),
    'blood': ('j', 'i', 'h', 'w'),        # spatter: hot pink, magenta, magenta-dark, grape
}

SEGMENTS = 8
HEIGHT_OF_ARCH = 5.4           # how far the middle lifts when the body arches
HEIGHT_OF_RISE = 7.0           # how far the front lifts when the head is reared
FAT = 4.4                      # radius of the fattest segment, sideways
REST = 15.5


def radii_at(t, swell, flat):
    """Sideways and vertical radii of the segment at t (0 at the tail, 1 at the head)."""
    plump = 0.5 + 0.5 * math.sin(math.pi * (0.04 + 0.78 * t))
    r = FAT * plump * swell
    return r * (1.0 + 0.5 * flat), r * 0.86 * (1.0 - 0.7 * flat)


def spine(p):
    """Where each segment sits: a list of (x, y, slope angle, sideways radius, vertical radius, spacing)."""
    n = SEGMENTS
    length = p['len']
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = (t - 0.5) * length + p['fwd']
        rz_, ry_ = radii_at(t, p['swell'], p['flat'])
        lift = p['arch'] * HEIGHT_OF_ARCH * math.sin(math.pi * t) + p['rise'] * HEIGHT_OF_RISE * t ** 2.4
        pts.append([x, ry_ + lift + p['lift'], 0.0, rz_, ry_])
    for i in range(n):                               # each segment lies along the line to its neighbours
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        pts[i][2] = math.atan2(b[1] - a[1], b[0] - a[0])
    return pts, length / (n - 1)


def anatomy(p):
    pts, step = spine(p)
    parts = []
    for i, (x, y, ang, rzz, ryy) in enumerate(pts):
        R = rz(ang)
        along = max(step * 0.72, 0.9)
        parts.append(part((x, y, 0.0), (along, ryy, rzz), 'ring' if i % 2 else 'body', f'seg{i}', R))
        parts.append(part((x, y - ryy * 0.42, 0.0), (along * 0.96, ryy * 0.72, rzz * 1.03), 'belly', f'belly{i}', R))
    # the rear sucker, a flat disc at the tail
    x, y, ang, rzz, ryy = pts[0]
    parts.append(part((x - step * 0.55, y - ryy * 0.1, 0.0), (0.9, ryy * 0.82, rzz * 0.8), 'belly', 'tail', rz(ang)))
    # the front sucker: a pale rim round a dark throat, a ring of cream teeth
    x, y, ang, rzz, ryy = pts[-1]
    R = rz(ang)
    o = p['open']
    cx, cy = x + math.cos(ang) * step * 0.55, y + math.sin(ang) * step * 0.55
    rim = (1.2, ryy * (1.02 + 0.25 * o), rzz * (1.02 + 0.25 * o))
    parts.append(part((cx, cy, 0.0), rim, 'lip', 'lip', R))
    out = 0.8
    fwd = (math.cos(ang), math.sin(ang))
    throat_r = (0.6, ryy * (0.5 + 0.28 * o), rzz * (0.5 + 0.28 * o))
    parts.append(part((cx + fwd[0] * out, cy + fwd[1] * out, 0.0), throat_r, 'throat', 'throat', R))
    for k in range(7):                               # teeth around the throat's edge, in the plane of the rim
        a = 2 * math.pi * k / 7 + 0.3
        ty, tz = math.sin(a) * throat_r[1] * 1.12, math.cos(a) * throat_r[2] * 1.12
        # (ty, tz) are in the sucker's own frame, which is turned by ang about z
        px = cx + fwd[0] * (out + 0.55) - fwd[1] * ty
        py = cy + fwd[1] * (out + 0.55) + fwd[0] * ty
        parts.append(part((px, py, tz), (0.34, 0.34 + 0.08 * o, 0.3), 'tooth', 'tooth'))
    # two cream eyespots on the top of the head segment
    if p['eyes'] == 'open':
        for side in (-1, 1):
            ex, ey = x - 0.4, y + ryy * 0.86
            parts.append(part((ex, ey, side * rzz * 0.42), (0.6, 0.5, 0.6), 'eye', f'eye{side}', R))
    for k, (sx, sz, r) in enumerate(p['spatter']):
        parts.append(part((sx, r * 0.35, sz), (r, r * 0.35, r * 0.9), 'blood', f'blood{k}'))
    return parts


def place(p):
    g = mm(ry(deg(p['yaw'])), rz(deg(p['roll'])))
    placed = []
    for q in anatomy(p):
        placed.append(dict(q, c=tuple(sum(g[i][k] * q['c'][k] for k in range(3)) for i in range(3)), R=mm(g, q['R'])))
    return placed, []


BASE = dict(len=REST, fwd=0.0, arch=0.2, rise=0.0, lift=0.0, open=0.0, swell=1.0, flat=0.0, roll=0, yaw=0, eyes='open', spatter=())


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


LMIN, LMAX = 12.0, 19.0


def inch(k, n=8):
    """One frame of the inch-worm walk: four frames stretching with the tail stuck down, four pulling the tail up behind."""
    half = n // 2
    if k < half:
        u = k / half
        length = LMIN + (LMAX - LMIN) * u
        rear, front = 0.0, length
    else:
        u = (k - half) / half
        length = LMAX - (LMAX - LMIN) * u
        front, rear = LMAX, LMAX - length
    drift = (LMAX - LMIN) * k / n
    mid = (rear + front) / 2 - drift - LMIN / 2
    arch = ((LMAX - length) / (LMAX - LMIN)) ** 1.3
    return pose(len=length, fwd=mid, arch=0.12 + 0.88 * arch, rise=0.18 * math.sin(math.pi * k / half) if k < half else 0.0)


BURST = ((5.5, 4.0, 1.5), (-5.5, 5.5, 1.1), (9.0, -1.0, 1.0), (-9.0, -4.5, 1.3), (2.0, -6.0, 1.1), (-1.0, 7.5, 0.9), (12.0, 3.5, 0.8), (-12.5, 1.5, 0.7))


class Leech:
    name = 'leech'
    kind = 'creature'
    airborne = set()
    ramps = RAMPS
    scale = 1.0
    stand = pose()

    poses = {
        # rearing up to strike, front end lifted, mouth working
        'charging': [pose(len=11.0, arch=0.35, rise=1.5, open=0.4)],
        # coil, lunge, clamp, recover
        'attack': [
            pose(len=10.5, arch=1.0, rise=0.15, fwd=-1.0, open=0.0),
            pose(len=20.0, arch=0.0, rise=0.9, fwd=2.0, open=1.0),
            pose(len=19.0, arch=0.0, rise=0.15, fwd=3.0, open=0.55),
            pose(len=15.0, arch=0.3, rise=0.1, fwd=0.6, open=0.1),
        ],
        # reared right up, swollen, mouth wide: gorging
        'release': [pose(len=13.5, arch=0.1, rise=1.55, swell=1.22, open=1.0, fwd=-0.6)],
        # knocked back and curled in on itself
        'damage': [pose(len=10.5, arch=1.0, rise=0.0, fwd=-2.0, roll=8, swell=0.92, eyes='shut')],
        # worn out: long, low and slack
        'weak': [pose(len=17.0, arch=0.0, rise=0.0, swell=0.84, eyes='shut', open=0.1)],
        # burst: a flat, ragged husk with blood spattered round it
        'dead': [pose(len=17.5, arch=0.0, flat=1.0, swell=0.95, eyes='shut', spatter=BURST)],
        'walking': [inch(k) for k in range(8)],
    }

    @staticmethod
    def place(p):
        return place(p)


CREATURE = Leech()

if __name__ == '__main__':
    run(CREATURE)
