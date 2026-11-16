#!/usr/bin/env python3
"""VARIANTS of the ranger (tools/make_ranger.py): a pure one and a corrupted one. Not new characters and not bases: the same slim body, poses, lean, walk and weapon hand as the ranger,
in a different palette, with a few small things added to the hood, the cloak and the shoulder (so the bow hand and the legs are never touched).

    ranger-pure        mint and cream hood and cloak, a cream tunic with amber, steel trousers, tan boots, lighter skin, cyan eyes; a leaf clasp, a gold circlet on the hood's edge, an even cloak hem
    ranger-corrupted   orchid and violet hood and cloak with a hot-pink edge, a dark tunic, pale sickly teal skin, hot-pink eyes and clasp; a ragged hem, two thorns on the hood's peak,
                       a mushroom on one shoulder

The ranger itself is unchanged (`sprites/ranger`). These are written to `sprites/variants/ranger-pure` and `sprites/variants/ranger-corrupted`, away from the bases, with a README.

    python3 tools/make_ranger_variants.py --preview previews/ranger-variants.png      (writes nothing else)
    python3 tools/make_ranger_variants.py --write                                      (sprites/variants/...)
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_ranger as mr  # noqa: E402
import make_slim  # noqa: E402
import creature as cr  # noqa: E402
from creature import mm, part, rx, rz  # noqa: E402
from humanoid import Humanoid  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'sprites' / 'variants'
HEAD_Y = mr.HEAD_Y

RAMPS = {
    'pure': {'hood': ('r', 'q', 's', 'k'), 'cloak': ('t', 'r', 'q', 's'), 'rim': ('t', 'r', 'q', 's'), 'clasp': ('d', 'b', 'a', 'e'), 'leaf': ('r', 'q', 's', 'D'),
             'crown': ('d', 'b', 'a', 'e'), 'shirt': ('t', 'C', 'b', 'a'), 'pants': ('p', 'l', 'k', 'w'), 'shoes': ('C', 'b', 'a', 'e'), 'skin': ('t', 'C', 'b', 'e')},
    'corrupted': {'hood': ('v', 'f', 'g', 'w'), 'cloak': ('f', 'u', 'w', 'x'), 'rim': ('j', 'i', 'h', 'w'), 'clasp': ('j', 'i', 'h', 'w'), 'thorn': ('t', 'f', 'g', 'x'),
                  'cap': ('j', 'i', 'h', 'w'), 'stem': ('t', 'C', 'p', 'l'), 'shirt': ('p', 'l', 'k', 'w'), 'pants': ('l', 'k', 'w', 'x'), 'shoes': ('f', 'g', 'w', 'x'),
                  'skin': ('r', 'q', 'p', 'l')},
}
EYES = {'pure': 'o', 'corrupted': 'j'}
LABEL = {'pure': 'Ranger (pure)', 'corrupted': 'Ranger (corrupted)'}


def circlet(j):
    """Gold beads across the brow, just outside the hood's edge."""
    R = j['head_R']
    out = []
    for i in range(7):
        a = math.radians(-70 + 140 * i / 6)
        out.append(part(j['head'](mr.RIM_X + 0.35, HEAD_Y + 0.2 + (mr.RIM_RADIUS + 0.2) * math.cos(a), (mr.RIM_RADIUS + 0.2) * math.sin(a)), (0.75, 0.75, 0.75), 'crown', 'crown', R))
    return out


def thorns(j):
    R = j['head_R']
    return [part(j['head'](-mr.HOOD_BACK - 0.8, HEAD_Y + 5.6, side * 1.5), (0.75, 2.2, 0.75), 'thorn', 'thorn' + str(n), mm(R, rx(side * 0.35)))
            for n, side in enumerate((-1, 1))]


def shoulder_mushroom(j):
    R = j['body_R']
    return [part(j['body'](-0.6, 14.4, 4.4), (0.7, 1.3, 0.7), 'stem', 'stem', R),
            part(j['body'](-0.6, 15.6, 4.4), (1.9, 0.95, 1.9), 'cap', 'cap', R),
            part(j['body'](-0.6, 14.8, 2.6), (1.0, 0.6, 1.0), 'cap', 'cap2', R)]


def gear(kind):
    def build(j, pose):
        R = j['body_R']
        parts = mr.hood(j)
        parts.append(part(j['body'](-0.4, 13.5, 0), (2.4, 1.4, 4.9), 'cloak', 'cloak', R))
        if kind == 'pure':
            parts += [part(j['body'](3.0, 13.6, 0.55), (1.5, 0.6, 0.8), 'leaf', 'leaf', mm(R, rx(0.5))), part(j['body'](3.0, 13.6, -0.55), (1.5, 0.6, 0.8), 'leaf', 'leaf2', mm(R, rx(-0.5)))]
            parts += circlet(j)
        else:
            parts += [part(j['body'](3.0, 13.6, 0), (0.9, 0.9, 0.9), 'clasp', 'clasp', R)]
            parts += thorns(j) + shoulder_mushroom(j)
        if pose['pitch'] >= 80:
            return parts
        if kind == 'pure':
            pieces = mr.CAPE_PIECES if pose['pitch'] > -30 else 3
            lengths = [0] * pieces
        else:
            pieces = 3 if pose['pitch'] > -30 else 2                    # shorter: it ends in a ragged edge
            lengths = [0, 0, 0][:pieces]
        for i in range(pieces):
            y = 11.8 - i * 1.0
            spread = 4.0 + 0.3 * i
            parts.append(part(j['body'](-3.6 - 0.12 * i, y, 0), (1.15, 2.5, spread), 'cloak', 'cloak', R))
        if kind == 'corrupted' and pose['pitch'] <= 80:
            # the torn edge: three uneven tatters hanging below the cloak
            for n, (z, drop) in enumerate(((-3.0, 2.2), (0.2, 3.2), (3.0, 1.6))):
                parts.append(part(j['body'](-3.9, 9.0 - drop / 2, z), (0.9, 1.0 + drop / 2, 1.0), 'cloak', 'tatter' + str(n), R))
        return parts
    return build


def creature(kind):
    c = Humanoid(f'ranger-{kind}', ramps=RAMPS[kind], hair='none', body=make_slim.CREATURE.body, calibrate_like=make_slim.CREATURE, accessories=gear(kind), tuning='ranger')
    c.eye_colour = EYES[kind]
    return c


def write(kind, folder):
    import extract_poses as ep  # noqa: F401
    c = creature(kind)
    folder.mkdir(parents=True, exist_ok=True)
    sys.argv = ['make_ranger_variants', str(folder)]
    cr.run(c)


README = """# Variants

Colour-and-detail variants of a base character. Each is the same body, poses, lean, walk and weapon hand as its base, so it swaps in anywhere the base stands (same 14 sheets, same sizes);
what differs is the palette and a few small additions that never touch the weapon hand or legs. A variant is not a base: it is made by its own generator, and the base it comes from is unchanged.

| Folder | From | What changes |
| --- | --- | --- |
| `ranger-pure/` | `ranger` | Mint and cream hood and cloak, cream tunic with amber, steel trousers, tan boots, lighter skin, cyan eyes; a leaf clasp, a gold circlet on the hood's edge, an even cloak hem |
| `ranger-corrupted/` | `ranger` | Violet and orchid hood and cloak with a hot-pink edge, dark tunic, pale sickly teal skin, hot-pink eyes and clasp; a ragged shorter cloak, two thorns on the hood, a mushroom on one shoulder |

Made by `tools/make_ranger_variants.py` (`--preview` shows them beside the ranger, `--write` writes these folders). Palette roles only, like everything else.
"""


def preview(path):
    import tempfile
    from PIL import Image, ImageDraw
    names = ['ranger', 'pure', 'corrupted']
    files = ['chargingSE', 'chargingNE', 'attackSE', 'attackNE', 'weakSE', 'walkingSE']
    S = 6
    with tempfile.TemporaryDirectory() as tmp:
        dirs = {'ranger': ROOT / 'sprites' / 'ranger'}
        for k in ('pure', 'corrupted'):
            dirs[k] = Path(tmp) / k
            write(k, dirs[k])
        ims = {(n, f): Image.open(dirs[n] / f'ranger{"-" + n if n != "ranger" else ""}-{f}.png').convert('RGBA') if n == 'x' else Image.open(next(dirs[n].glob(f'*-{f}.png'))).convert('RGBA') for n in names for f in files}
    W = {f: ims[('ranger', f)].width for f in files}
    H = max(i.height for i in ims.values())
    pad = 10
    sheet = Image.new('RGBA', (sum(W[f] * S + pad for f in files) + pad, (H * S + 24) * 3 + pad), (47, 26, 69, 255))
    d = ImageDraw.Draw(sheet)
    for r, n in enumerate(names):
        x, y = pad, r * (H * S + 24) + pad
        d.text((x, y), n, fill=(230, 220, 200, 255))
        for f in files:
            im = ims[(n, f)]
            sheet.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, y + 14))
            x += W[f] * S + pad
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
        print('the ranger and its two variants ->', args.preview)
    if args.write:
        for k in ('pure', 'corrupted'):
            write(k, OUT / f'ranger-{k}')
        (OUT / 'README.md').write_text(README)


if __name__ == '__main__':
    main()
