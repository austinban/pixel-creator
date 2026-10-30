#!/usr/bin/env python3
"""Paint a zombie on the fighter's poses.

The zombie starts from the fighter's frames and keeps its anchors and ground
line, but it is not the fighter in green: the hair is gone (the head is a bald
dome with an exposed skull patch and a stitched gash), the arm on the character's
right is missing and ends in a ragged, bleeding stump, and the chest is torn open
to the ribs. The skin is sickly green, the eyes are hollowed, and the clothes are
dull rags. Everything is painted from the shared palette, so the output goes
straight through extract_poses.py.

    python3 tools/make_zombie.py path/to/fighter sprites/zombie
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402
import make_skeleton as ms  # noqa: E402

CELL = ep.CELL
N8 = tuple((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
HAIR, SKIN, EYE = set('hij'), set('be'), 'd'

# fighter role -> zombie role, by palette character.
REPAINT = {
    'b': 'A', 'e': 'B',                                    # skin: green, emerald on the shaded side
    'r': 'p', 'q': 'l', 'n': 'l', 'p': 'l',                # light clothes, steel to lavender
    'm': 'k', 'l': 'k', 'k': 'w',                          # dark clothes, indigo to grape
    't': 'A', 'o': 'h',                                    # bright flecks become torn flesh and blood
    'g': 'x', 'f': 'h',                                    # plum rags; the orchid sash goes bloody
}
HIGHLIGHT, BASE, SHADE = 'z', 'A', 'B'  # lime, green, emerald
BLOOD, FRESH_BLOOD, BONE, BONE_SHADE = 'h', 'j', 't', 'C'

# The arm on the character's right: left of the screen facing us, right facing away.
MISSING_SIDE = {'SE': 'left', 'NE': 'right'}
ARM_ROWS = 7  # rows below the head that count as shoulder-to-hip
SLEEVE_CAP = 2  # shoulder rows that keep a short torn sleeve
STUMP_ROWS = 4  # how far down the cut the stump bleeds

# Poses where the upright rule finds the arm; the lying frames are cut by hand
# (x0, y0, x1, y1, inclusive), and the crouched ones keep their arms folded away.
UPRIGHT = ('attack', 'charging', 'release', 'walking', 'damage')
CUTS = {
    'deadSE': [(5, 17, 11, 21)],
    'deadNE': [(22, 20, 26, 22), (24, 19, 26, 19)],
}

SCALP_PATCH = (  # a jagged wound with the skull showing, and a drip; '.' leaves the cell alone
    '.hhh.',
    'hCCCh',
    'hCtCh',
    '.hCh.',
    '..h..',
)
GASH = (  # a stitched cut
    'O.O.',
    'hhhh',
    '.O.O',
)
CHEST = (  # torn open to the ribs
    'hhhh',
    'CCCh',
    'hhhh',
    'CCCh',
)


def components8(cells):
    seen, found = set(), []
    for start in cells:
        if start in seen:
            continue
        stack, part = [start], set()
        seen.add(start)
        while stack:
            x, y = stack.pop()
            part.add((x, y))
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n in cells and n not in seen:
                    seen.add(n)
                    stack.append(n)
        found.append(part)
    return found


def opening(mask, radius=2):
    """Erode then dilate: thin spikes narrower than the radius disappear."""
    offsets = [(dx, dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1) if dx * dx + dy * dy <= radius * radius + 1]
    core = {(x, y) for (x, y) in mask if all((x + dx, y + dy) in mask for dx, dy in offsets)}
    return {(x + dx, y + dy) for (x, y) in core for dx, dy in offsets}


def stamp(out, template, x0, y0, allowed):
    for dy, row in enumerate(template):
        for dx, char in enumerate(row):
            if char != '.' and (x0 + dx, y0 + dy) in allowed:
                out[y0 + dy][x0 + dx] = char


def head_cells(grid):
    solid = {(x, y) for y in range(CELL) for x in range(CELL) if grid[y][x] != '.'}
    hair = {c for c in solid if grid[c[1]][c[0]] in HAIR}
    if not hair:
        return set(), set()
    mass = max(components8(hair), key=len)
    reach = max(y for _, y in mass) + 8
    skin = {c for c in solid if grid[c[1]][c[0]] in SKIN | {EYE} and c[1] <= reach}
    face, frontier = set(), {c for c in skin if any((c[0] + dx, c[1] + dy) in mass for dx, dy in N8)}
    while frontier:
        cell = frontier.pop()
        face.add(cell)
        frontier |= {(cell[0] + dx, cell[1] + dy) for dx, dy in N8 if (cell[0] + dx, cell[1] + dy) in skin} - face
    return mass, mass | face


def paint(grid, pose_id):
    facing = pose_id[-2:]
    out = [[REPAINT.get(c, c) for c in row] for row in grid]
    solid_rows = [y for y in range(CELL) if any(c != '.' for c in grid[y])]
    top, bottom = min(solid_rows), max(solid_rows)
    face_limit = top + (bottom - top) * 0.45
    removed = set()

    # Below the face, coral is the sash unless it shades a hand: the sash becomes a bloody rag.
    for y in range(CELL):
        for x in range(CELL):
            if grid[y][x] == 'e' and y >= face_limit:
                beside = [grid[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < CELL and 0 <= y + dy < CELL]
                out[y][x] = SHADE if 'b' in beside else BLOOD

    # Hollow the eyes: skin touching a yellow eye or the dark eye slit goes dark green.
    for y in range(CELL):
        for x in range(CELL):
            if y < face_limit and (grid[y][x] == EYE or (grid[y][x] == 'O' and grid[y][x - 1] in SKIN and grid[y][x + 1] in SKIN)):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < CELL and 0 <= y + dy < CELL and grid[y + dy][x + dx] in SKIN:
                        out[y + dy][x + dx] = SHADE

    # No hair: the spikes are cut away and what is left of the mass is bare scalp.
    mass, head = head_cells(grid)
    if mass:
        rounded = opening(head)
        for cell in mass - rounded:
            removed.add(cell)
        scalp = mass & rounded
        kept = (head - removed)
        for x, y in scalp:
            if (x, y - 1) not in kept or (x - 1, y) not in kept:
                out[y][x] = HIGHLIGHT
            elif (x + 1, y) not in kept or (x, y + 1) not in kept:
                out[y][x] = SHADE
            else:
                out[y][x] = BASE
    else:
        kept = set()

    # The missing arm.
    head_bottom, centre, stump_limit = None, None, None
    if kept:
        hx = [c[0] for c in kept]
        head_bottom = max(c[1] for c in kept)
        torso = sorted(x for y in range(head_bottom + 2, min(CELL, head_bottom + 6)) for x in range(CELL)
                       if grid[y][x] not in '.O')
        centre = torso[len(torso) // 2] if torso else (min(hx) + max(hx)) // 2
        stump_limit = head_bottom + STUMP_ROWS
    if pose_id in CUTS:
        for x0, y0, x1, y1 in CUTS[pose_id]:
            removed |= {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if grid[y][x] != '.'}
        stump_limit = None
    elif kept and pose_id.startswith(UPRIGHT):
        left = MISSING_SIDE[facing] == 'left'
        for y in range(head_bottom + 1, min(CELL, head_bottom + 1 + ARM_ROWS)):
            reach = 3 if y > head_bottom + SLEEVE_CAP else 5  # a short torn sleeve stays at the shoulder
            for x in range(CELL):
                if grid[y][x] != '.' and ((left and x < centre - reach) or (not left and x > centre + reach)):
                    removed.add((x, y))

    # Whatever the cuts left floating is dropped with them.
    remaining = {(x, y) for y in range(CELL) for x in range(CELL) if grid[y][x] != '.' and (x, y) not in removed}
    if remaining:
        main = max(components8(remaining), key=len)
        removed |= remaining - main

    apply_cuts(out, grid, removed)
    interior = {(x, y) for y in range(CELL) for x in range(CELL) if out[y][x] not in '.O'}

    # Stump: the cut edge bleeds, with a spur of bone.
    cut = sorted(c for c in interior if any((c[0] + dx, c[1] + dy) in removed for dx, dy in N8) and c not in kept
                 and (stump_limit is None or c[1] <= stump_limit))
    for x, y in cut:
        out[y][x] = BLOOD
    if cut:
        x, y = cut[len(cut) // 2]
        out[y][x] = BONE

    if kept:
        hx0, hy0 = min(c[0] for c in kept), min(c[1] for c in kept)
        hx1 = max(c[0] for c in kept)
        stamp(out, SCALP_PATCH, hx0 + 2, hy0 + 1, kept)
        stamp(out, GASH, hx1 - 5, hy0 + 5, kept)
        stamp(out, CHEST, centre - 1, head_bottom + 2, interior - kept)
    return out


def apply_cuts(out, original, removed):
    """Delete the removed cells and redraw the outline around the edit."""
    for x, y in removed:
        out[y][x] = '.'
    dirty = {(x + dx, y + dy) for x, y in removed for dx in range(-2, 3) for dy in range(-2, 3)}
    solid = {(x, y) for y in range(CELL) for x in range(CELL) if out[y][x] not in '.O'}
    for x, y in dirty:
        if 0 <= x < CELL and 0 <= y < CELL and (x, y) not in solid:
            out[y][x] = 'O' if any((x + dx, y + dy) in solid for dx, dy in N8) else '.'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('fighter', type=Path, help='folder of the fighter pose PNGs')
    parser.add_argument('out', type=Path, help='folder to write zombie-<pose>.png into')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for action, facing, cols, rows in ep.POSES:
        pose_id = action + facing
        frames = ms.read_frames(ep.find_source(args.fighter, pose_id), cols, rows)
        ms.write_sheet(args.out / f'zombie-{pose_id}.png', [paint(g, pose_id) for g in frames], cols, rows)
    print(f'wrote {len(ep.POSES)} poses to {args.out}')


if __name__ == '__main__':
    main()
