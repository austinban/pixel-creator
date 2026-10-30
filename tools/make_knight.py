#!/usr/bin/env python3
"""Paint a knight in full plate on the fighter's poses.

The fighter's anchors and ground line are kept. The hair becomes a rounded helm
with a visor slit and a red crest, the face is covered, the torso gets breastplate
bands and a gold belt, the shoulders get plated, and the hands and legs become
gauntlets and greaves. Everything is painted from the shared palette, so the
output goes straight through extract_poses.py.

    python3 tools/make_knight.py path/to/fighter sprites/knight
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
import make_skeleton as ms  # noqa: E402
import make_zombie as mz  # noqa: E402

CELL = ep.CELL
N8 = mz.N8
SKIN = set('be')

# Metal, light to dark: spark, lit plate, plate, shaded plate, deep shade, seam.
SPARK, LIGHT, STEEL, SHADE, DEEP, SEAM = 't', 'q', 'p', 'l', 'k', 'w'
GOLD, GOLD_DARK = 'd', 'b'
CREST, CREST_LIGHT, CREST_DARK = 'i', 'j', 'h'
UPRIGHT = mz.UPRIGHT

FACE_ROWS = 0.45  # share of the figure, from the top, that is head


def shade_plate(out, cells, outside, base, lit=LIGHT, dark=SHADE):
    """Light from the top left: edges toward it catch the light, edges away fall into shade."""
    for x, y in cells:
        if outside(x, y - 1) or outside(x - 1, y):
            out[y][x] = lit
        elif outside(x + 1, y) or outside(x, y + 1):
            out[y][x] = dark
        else:
            out[y][x] = base


def reshape(out, removed, added):
    """Apply the cuts and additions, and redraw the outline around them."""
    for x, y in removed:
        out[y][x] = '.'
    dirty = {(x + dx, y + dy) for x, y in removed | added for dx in range(-2, 3) for dy in range(-2, 3)}
    solid = {(x, y) for y in range(CELL) for x in range(CELL) if out[y][x] not in '.O'}
    for x, y in dirty:
        if 0 <= x < CELL and 0 <= y < CELL and (x, y) not in solid:
            out[y][x] = 'O' if any((x + dx, y + dy) in solid for dx, dy in N8) else '.'


def paint(grid, pose_id):
    out = [row[:] for row in grid]
    upright = pose_id.startswith(UPRIGHT)
    removed, added = set(), set()

    solid = {(x, y) for y in range(CELL) for x in range(CELL) if grid[y][x] != '.'}
    mass, head = mz.head_cells(grid)
    kept = set()
    holes = set()
    if mass:
        removed |= mass - mz.opening(head)
        kept = head - removed
        holes = ms.with_holes(kept) - kept                             # the fighter's own eye slit: part of the face guard now
    figure = solid - removed
    inside = {c for c in figure if grid[c[1]][c[0]] != 'O'} | holes    # painted cells, outline left out
    outside = lambda x, y: (x, y) not in inside

    # The body first, as clean plate: steel with lit and shaded edges.
    body = inside - kept
    shade_plate(out, body, outside, STEEL)

    if kept:
        kept_all = kept | holes
        face = {c for c in kept_all if grid[c[1]][c[0]] in SKIN | {'d', 'O'}}
        crown = kept - face
        shade_plate(out, crown, outside, LIGHT, lit=SPARK, dark=STEEL)    # the helm: brightest metal
        shade_plate(out, face, outside, SHADE, lit=STEEL, dark=DEEP)      # the face guard: much darker, so the visor reads

        hx0, hx1 = min(c[0] for c in kept), max(c[0] for c in kept)
        hy0, hy1 = min(c[1] for c in kept), max(c[1] for c in kept)
        cx = (hx0 + hx1) // 2

        # A ridge down the crown.
        for y in range(hy0 + 1, hy1):
            if (cx, y) in crown:
                out[y][cx] = SPARK if y == hy0 + 1 else LIGHT

        if face and facing_forward(pose_id):
            rows = sorted(y for y in {c[1] for c in face} if sum(1 for c in face if c[1] == y) >= 3)
            top = rows[0] if rows else min(c[1] for c in face)
            block = {c for c in face if top <= c[1] <= top + 4}
            fx0, fx1 = min(c[0] for c in block), max(c[0] for c in block)
            eye_row = top + 1
            for x in range(fx0, fx1 + 1):
                if (x, top) in kept_all:
                    out[top][x] = GOLD                                 # brow trim, across the whole helm
                if fx0 < x < fx1 and (x, eye_row) in kept_all:
                    out[eye_row][x] = SEAM                             # visor slit
            for x in (fx0 + 2, fx1 - 2):
                if (x, eye_row) in face:
                    out[eye_row][x] = SPARK                            # a glint in each eye
            for x in (fx0, fx1):
                for y in range(eye_row, top + 5):
                    if (x, y) in face:
                        out[y][x] = DEEP                               # cheek guards
            for dy in (2, 3):
                if (cx, top + dy) in face:
                    out[top + dy][cx] = SEAM if dy == 2 else DEEP      # breathing vents
        elif face:
            for x, y in face:  # from behind: the back of the helm and the gorget
                out[y][x] = DEEP if (x + y) % 2 else SHADE

        # A crest along the top, kept inside the cell.
        if upright and hy0 - 3 >= 1:
            for dy, (a, b, tone) in enumerate(((cx - 2, cx + 2, CREST), (cx - 1, cx + 1, CREST_LIGHT))):
                for x in range(a, b + 1):
                    out[hy0 - 1 - dy][x] = tone
                    added.add((x, hy0 - 1 - dy))

    # Breastplate, belt, pauldrons and knees on the frames that stand up.
    if kept and upright:
        hb = max(c[1] for c in kept)
        torso = sorted(x for y in range(hb + 2, min(CELL, hb + 6)) for x in range(CELL) if (x, y) in body)
        centre = torso[len(torso) // 2] if torso else cx
        for x, y in body:
            row, across = y - hb, x - centre
            if abs(across) <= 3 and 1 <= row <= 6:                  # the breastplate
                out[y][x] = LIGHT if row in (1, 2, 4) else STEEL
                if row in (3, 5) or across == 0:
                    out[y][x] = DEEP
                if row == 6:
                    out[y][x] = GOLD
                if row == 2 and across == -2:
                    out[y][x] = SPARK
            elif 3 < abs(across) <= 7 and 1 <= row <= 3:            # the pauldron
                out[y][x] = LIGHT if row <= 2 else GOLD
                if row == 1 and across in (-4, 4):
                    out[y][x] = SPARK
            elif 3 < abs(across) <= 9 and row in (5, 6):            # the elbow joint
                out[y][x] = DEEP
        legs = [y for _, y in body if y - hb > 7]
        if legs:
            knee = min(legs) + (max(legs) - min(legs)) // 2
            for x, y in body:
                if y == knee:
                    out[y][x] = SPARK
                elif y == knee + 1:
                    out[y][x] = DEEP

    reshape(out, removed, added)
    return out


def facing_forward(pose_id):
    return pose_id.endswith('SE')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('fighter', type=Path, help='folder of the fighter pose PNGs')
    parser.add_argument('out', type=Path, help='folder to write knight-<pose>.png into')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for action, facing, cols, rows in ep.POSES:
        pose_id = action + facing
        frames = ms.read_frames(ep.find_source(args.fighter, pose_id), cols, rows)
        ms.write_sheet(args.out / f'knight-{pose_id}.png', [paint(g, pose_id) for g in frames], cols, rows)
    print(f'wrote {len(ep.POSES)} poses to {args.out}')


if __name__ == '__main__':
    main()
