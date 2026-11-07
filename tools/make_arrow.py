#!/usr/bin/env python3
"""An arrow, to scale with the characters: a single frame to be rotated, mirrored and moved in play.

It is drawn flying to the right (side on), as a small 3D model like the vine and the characters: a thin
wooden shaft, a steel head, and three red fletching vanes round the tail. Painted in colour roles, so it
recolours. Model space: the arrow lies along x with its middle at the origin, one unit about one pixel.

    python3 tools/make_arrow.py --model previews/arrow-3d.png     look at the 3D model first
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import part, rx  # noqa: E402

RAMPS = {
    'shaft': ('b', 'a', 'e', 'g'),      # amber, orange, coral, plum: the wooden weapons' tones
    'head': ('t', 'q', 'p', 'l'),       # cream, teal, steel, lavender: the iron weapons' tones
    'vane': ('c', 'j', 'i', 'h'),       # salmon, hot-pink, magenta, dark magenta
}
LENGTH = 22.0                           # tip to tail, in game pixels: about as long as a character is tall
FLETCH_VANES = 3


def place():
    half = LENGTH / 2
    parts = [
        part((-0.8, 0, 0), (half - 1.8, 0.55, 0.55), 'shaft', 'shaft'),
        part((half - 3.4, 0, 0), (2.6, 1.45, 0.5), 'head', 'head'),            # the head: a leaf-shaped blade...
        part((half - 1.6, 0, 0), (2.4, 0.5, 0.3), 'head', 'head'),            # ...tapering to the point
        part((-half + 0.5, 0, 0), (0.7, 0.7, 0.7), 'shaft', 'nock'),
    ]
    for k in range(FLETCH_VANES):                                              # the vanes: flat, spread round the tail
        parts.append(part((-half + 3.4, 0, 0), (2.5, 1.6, 0.14), 'vane', f'vane{k}', rx(k * 2 * math.pi / FLETCH_VANES + 0.4)))
    return parts, []


# --- the pixel sprites ----------------------------------------------------------
CELL_W = 28
SIDE = dict(h=12, rows=(8, 20))         # flying to the right, side on
ANGLED = dict(h=16, rows=(6, 22))       # flying up-right (NE) and down-right (SE), as the game's camera sees it
MIDDLE_X = 14


def render_pixels(facing):
    """The arrow as rows of colour-role characters: 'side', 'NE' or 'SE'. Its middle is the cell's middle."""
    import creature as cr
    spec = SIDE if facing == 'side' else ANGLED
    parts, decals = place()
    old_cell, old_yaw = cr.CELL, dict(cr.YAW)
    cr.CELL = CELL_W
    cr.YAW['side'] = 0.0
    try:
        rows = cr.render_frame(parts, decals, facing, (MIDDLE_X, 14), RAMPS, 1.0)
    finally:
        cr.CELL = old_cell
        cr.YAW.clear()
        cr.YAW.update(old_yaw)
    lo, hi = spec['rows']
    return rows[lo:hi]


def anchor(facing):
    spec = SIDE if facing == 'side' else ANGLED
    return {'x': MIDDLE_X, 'y': 14 - spec['rows'][0]}


def render_sheet(size=420):
    from PIL import Image, ImageDraw
    import preview3d as pv
    parts, decals = place()
    fit = [(-LENGTH / 2 - 1, -1.6, -1.6), (LENGTH / 2 + 1, 1.6, 1.6)]
    names = ('side', 'SE', 'NE')
    sheet = Image.new('RGBA', (size * len(names), size // 2 + 20), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        tile = pv.render_view(parts, decals, RAMPS, pv.VIEWS[name], size, fit_points=fit)
        sheet.alpha_composite(tile.crop((0, size // 4, size, size // 4 + size // 2)), (i * size, 20))
        draw.text((i * size + 6, 4), f'{name}   (22 px long: a character is about 26 tall)', fill=(235, 238, 245, 255))
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', type=Path, required=True, help='write the 3D preview here')
    args = parser.parse_args()
    args.model.parent.mkdir(parents=True, exist_ok=True)
    render_sheet().save(args.model)
    print(f'3D preview of the arrow -> {args.model}; no sprite was made')

def build_assets():
    # The arrow, two ways to try: one frame flying to the right to rotate and mirror, and two frames
    # already angled the way the game's camera sees a NE and an SE flight.
    arrow_side = {
        'id': 'arrow', 'label': 'Arrow - single frame (rotate and mirror)', 'category': 'Weapons', 'kind': 'still', 'place': 'none',
        'w': CELL_W, 'h': SIDE['h'], 'cols': 1, 'rows': 1, 'fps': 0,
        'anchor': anchor('side'),
        'frames': [render_pixels('side')],
    }
    arrow_angled = {
        'id': 'arrow-iso', 'label': 'Arrow - two frames (NE and SE)', 'category': 'Weapons', 'kind': 'variants', 'place': 'none',
        'names': ['NE', 'SE'],
        'w': CELL_W, 'h': ANGLED['h'], 'cols': 2, 'rows': 1, 'fps': 0,
        'anchor': anchor('NE'),
        'frames': [render_pixels('NE'), render_pixels('SE')],
    }
    return [arrow_side, arrow_angled]


if __name__ == '__main__':
    main()
