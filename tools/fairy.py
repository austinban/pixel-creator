"""Parts shared by the fairies: wings, a skirt of petals or leaves, and pointed ears.

Each is a function that takes the joints of a pose (see humanoid.py), so it follows the body or the head, and gives back ellipsoids.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import deg, mm, part, rx, ry, rz  # noqa: E402

HEAD_Y = 18.6


def wings(j, upper=(0.3, 4.6, 3.1), lower=(0.3, 2.9, 2.0), spread=22, sweep=18, mat='wing', pair=2):
    """Wings on the back: a big upper wing and a smaller lower one on each side, tipped outward like a butterfly's.

    `pair` of 1 gives just the upper wings; the dragonfly's long thin pairs use different radii.
    """
    R = j['body_R']
    out = []
    for side in (-1, 1):
        # the upper wing: up and out from the shoulder blade
        out.append(part(j['body'](-3.3, 16.2, side * 3.4), upper, mat, 'wing' + str(side), mm(R, mm(rx(deg(-side * spread)), rz(deg(-sweep))))))
        if pair == 2:
            out.append(part(j['body'](-3.1, 12.6, side * 2.7), lower, mat, 'wingb' + str(side), mm(R, mm(rx(deg(-side * (spread + 8))), rz(deg(sweep))))))
    return out


def petal_skirt(j, count=9, radius=2.5, length=2.3, width=1.25, flare=30, mat='petal', y=7.7, drop=0):
    """A skirt of petals or leaves round the hips: each a thin ellipsoid hanging from the waist and flaring out."""
    R = j['body_R']
    out = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c = j['body'](radius * math.cos(t), y - drop, radius * math.sin(t))
        out.append(part(c, (0.38, length, width), mat, f'petal{i}', mm(R, mm(ry(-t), rz(deg(flare))))))
    return out


def pointed_ears(j, length=2.1, tilt=28):
    """Slim ears that point up and back from either side of the head."""
    HR = j['head_R']
    return [part(j['head'](-0.4, HEAD_Y + 1.0, side * 4.3), (0.5, length, 0.55), 'skin', 'ear' + str(side),
                 mm(HR, mm(rx(deg(side * 24)), rz(deg(tilt))))) for side in (-1, 1)]
