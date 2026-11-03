#!/usr/bin/env python3
"""Ropes: a coil of thick rope wound round a person in the charging pose, for a captive, and the animation of it being cut.

It is drawn in 2D, from the silhouette of the widest humanoid in the charging pose, from the shoulders to the feet. Each turn of the coil is a thick cord that bows down across the front of the body, like a
ring seen from above and a little in front, tilted a little as a spiral would be, with a lit top edge, a body of hemp and a dark underside.
There is one generic coil for everyone, cut to the widest of the humanoids, so it covers any of them and the figure shows between the turns.

Cutting: six frames. A pale slash flashes across the coils, they part along it, break into pieces that drop away with frayed ends, and
by the last frame there is almost nothing left.

    python3 tools/make_ropes.py --preview previews/ropes.png      the coils and the cut, over a few people
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

HEMP = {'lit': 'C', 'body': 'b', 'shade': 'a', 'deep': 'g', 'frayed': 't'}       # sand, amber, orange, plum, and cream for cut ends
THICK = 3                  # how many rows thick each cord is: heavy rope
PITCH = 4                  # rows from one turn to the next
SAG = 2.0                  # how far a turn bows down across the front
TILT = 1.4                 # how much a turn climbs from one side to the other, as a spiral does
CUT_FRAMES = 6
PIECES = 4                 # the pieces each turn breaks into when cut


def silhouette(rows):
    return [[ch != '.' for ch in row] for row in rows]


def coil_rows(mask):
    """Where the turns go: from just under the head to the feet, in rows. Found from the silhouette, whatever the person's size."""
    ys = [y for y, row in enumerate(mask) if any(row)]
    top, bottom = min(ys), max(ys)
    # the head is about ten rows tall (a big head on a small body), so the first turn goes just under the chin
    start = top + 11
    return start, bottom - 1


def render_coils(mask, phase=0):
    """The turns of rope as {(x, y): (turn, piece, tone)} for a silhouette, before any cutting."""
    start, end = coil_rows(mask)
    cells = {}
    turn = 0
    y0 = start
    while y0 <= end:
        # this turn's extent across the body, from the silhouette at its middle row
        mid = min(31, y0 + THICK // 2 + 2)
        xs = [x for x in range(32) if mask[mid][x]] or [x for x in range(32) if mask[min(31, mid + 2)][x]]
        if xs:
            left, right = min(xs), max(xs)
            cx, hw = (left + right) / 2, max(1.0, (right - left) / 2)
            for x in range(left, right + 1):
                u = (x - cx) / hw
                centre = y0 + SAG * (1 - u * u) + TILT * u
                for dy in range(-THICK // 2 - 1, THICK // 2 + 2):
                    y = int(round(centre)) + dy
                    if not (0 <= y < 32 and mask[y][x]):
                        continue
                    top = dy == -THICK // 2 - 1 + 1
                    bottom_ = dy == THICK // 2 + 1 - 1
                    if dy < -THICK // 2 or dy > THICK // 2:
                        continue
                    tone = 'lit' if dy == -(THICK // 2) else 'deep' if dy == THICK // 2 else 'body'
                    # the twist of the strands: a darker notch every few pixels, slanting with the spiral
                    if tone == 'body' and (x + turn * 2 + dy + phase) % 4 == 0:
                        tone = 'shade'
                    piece = min(PIECES - 1, int((x - left) / ((right - left + 1) / PIECES)))
                    cells[(x, y)] = (turn, piece, tone)
        y0 += PITCH
        turn += 1
    return cells


def render_bound(mask):
    """The coiled rope on a silhouette as 32 rows."""
    grid = [['.'] * 32 for _ in range(32)]
    for (x, y), (turn, piece, tone) in render_coils(mask).items():
        grid[y][x] = HEMP[tone]
    # a knot, and a loose end hanging from the front of the waist
    cells = render_coils(mask)
    return [''.join(r) for r in grid]


def render_cut(mask, frame):
    """One frame of the rope being cut. frame 0 is the rope tied; the last is nearly nothing."""
    coils = render_coils(mask)
    if frame == 0:
        return render_bound(mask)
    start, end = coil_rows(mask)
    grid = [['.'] * 32 for _ in range(32)]
    cx, cy = 16, (start + end) / 2
    # the slash is a diagonal line through the middle of the body, from the upper right to the lower left
    def along(x, y):
        return (x - cx) * 0.55 + (y - cy)          # zero on the slash, positive below-right of it
    for (x, y), (turn, piece, tone) in coils.items():
        side = along(x, y)
        ch = HEMP[tone]
        if frame == 1:                              # the flash: the cord at the cut turns pale
            if abs(side) < 1.5:
                ch = HEMP['frayed']
            ny, nx = y, x
        elif frame == 2:                            # they part along the cut, and the ends are frayed
            sign = 1 if side > 0 else -1
            ny, nx = y + sign, x + sign
            if abs(side) < 2.4:
                ch = HEMP['frayed'] if tone != 'deep' else HEMP['shade']
        else:
            # the pieces break loose and fall, each at its own pace, the lower ones faster, drifting out to the side
            fall = {3: 3, 4: 8, 5: 16}[frame]
            speed = 0.8 + 0.35 * piece + 0.2 * (turn % 3)
            sway = (piece - (PIECES - 1) / 2) * (frame - 2) * 0.9
            ny, nx = int(round(y + fall * speed)), int(round(x + sway))
            if abs(side) < 2.4:
                ch = HEMP['frayed'] if tone == 'lit' else ch
        if 0 <= ny < 32 and 0 <= nx < 32:
            grid[ny][nx] = ch
    # the last frame keeps only a stray fibre or two
    if frame == CUT_FRAMES - 1:
        keep = [[False] * 32 for _ in range(32)]
        count = 0
        for y in range(31, -1, -1):
            for x in range(32):
                if grid[y][x] != '.' and (x * 7 + y * 3) % 11 == 0 and count < 6:
                    keep[y][x] = True
                    count += 1
        grid = [[grid[y][x] if keep[y][x] else '.' for x in range(32)] for y in range(32)]
    return [''.join(r) for r in grid]


def character_masks():
    """The silhouette of every humanoid's charging pose in both facings, from the base set: {id: {facing: 32 rows of bool}}."""
    import json
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / 'poses' / 'base.js').read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
    out = {}
    for c in data['characters']:
        if c.get('kind', 'humanoid') != 'humanoid':
            continue
        out[c['id']] = {'label': c['label'], **{f: silhouette(c['frames']['charging' + f][0]) for f in ('NE', 'SE')}}
    return out


def widest(masks, facing):
    """The id of the humanoid with the widest charging silhouette in a facing (ties go to the larger one): the one generic ropes are cut to."""
    return max(masks, key=lambda w: (max(sum(row) for row in masks[w][facing]), sum(map(sum, masks[w][facing]))))


def main():
    import argparse
    import extract_poses as ep
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    import json
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / 'poses' / 'base.js').read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
    frames_of = {c['id']: c['frames'] for c in data['characters']}
    masks = character_masks()
    who = [w for w in ('human', 'slim', 'paladin', 'earthbender', 'blossom', 'fighter') if w in masks]
    scale = 6
    sheet = Image.new('RGBA', (CUT_FRAMES * 33 * scale, len(who) * 2 * 33 * scale), (60, 64, 74, 255))

    def draw(rows, x0, y0, base=None):
        cell = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        if base:
            for y, line in enumerate(base):
                for x, ch in enumerate(line):
                    if ch != '.':
                        cell.putpixel((x, y), rgb[ch] + (255,))
        for y, line in enumerate(rows):
            for x, ch in enumerate(line):
                if ch != '.':
                    cell.putpixel((x, y), rgb[ch] + (255,))
        sheet.alpha_composite(cell.resize((32 * scale, 32 * scale), Image.NEAREST), (x0, y0))

    generic = {facing: masks[widest(masks, facing)][facing] for facing in ('SE', 'NE')}
    print('widest:', {f: widest(masks, f) for f in ('SE', 'NE')})
    for r, name in enumerate(who):
        for f_i, facing in enumerate(('SE', 'NE')):
            for i in range(CUT_FRAMES):
                draw(render_cut(generic[facing], i), i * 33 * scale, (r * 2 + f_i) * 33 * scale, frames_of[name]['charging' + facing][0])
    if args.preview:
        sheet.save(args.preview)
        print('wrote', args.preview)


if __name__ == '__main__':
    main()
