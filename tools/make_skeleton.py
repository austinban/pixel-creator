#!/usr/bin/env python3
"""Paint a skeleton on the cleric's poses.

The cleric's silhouette is kept frame for frame, so the skeleton shares every
anchor and the ground line with the other bases. Its dome becomes a skull and
the rest becomes banded bone with dark gaps. Everything is painted from the
shared palette, so the output goes straight through extract_poses.py.

    python3 tools/make_skeleton.py path/to/cleric sprites/skeleton
"""
import argparse
import sys
from collections import deque
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

CELL = ep.CELL
BONE_HI, BONE, BONE_SHADE, GAP, EYE_GLOW = 't', 'C', 'p', 'k', 'z'
DOME = set('aef')  # orange, coral, orchid: the cleric's dome ramp
UPRIGHT_FACES = ('attackSE', 'chargingSE', 'releaseSE', 'walkingSE')
LYING = ('deadNE', 'deadSE')
RIB_ZONE = 0.58  # share of the body, from the top, that is ribcage
KNEE_AT = 0.82   # where the knee joint falls, as a share of the body

# Faces for the frames where the head is short, tilted or tucked into the body,
# placed by hand from the cleric's geometry. left/right are the first column of
# each 3-wide socket, rows give the top of the eyes, their height, the nose row
# and the teeth row, and teeth is the span of columns.
FACES = {
    'damageSE': dict(left=14, right=19, eye_top=10, eye_h=3, nose_y=13, teeth_y=14, teeth=(15, 20)),
    'deadSE': dict(left=17, right=21, eye_top=23, eye_h=3, nose_y=26, teeth_y=28, teeth=(18, 23)),
    'weakSE': dict(left=13, right=18, eye_top=14, eye_h=2, nose_y=None, teeth_y=16, teeth=(14, 17)),
}

TO_RGB = {char: tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4)) for char, _, _, _, hex_ in ep.ROLES}
FROM_RGB = {rgb: char for char, rgb in TO_RGB.items()}


def read_frames(path, cols, rows):
    image = Image.open(path).convert('RGBA')
    px = image.load()
    frames = []
    for index in range(cols * rows):
        ox, oy = (index % cols) * CELL, (index // cols) * CELL
        grid = [['.'] * CELL for _ in range(CELL)]
        for y in range(CELL):
            for x in range(CELL):
                r, g, b, a = px[ox + x, oy + y]
                if a:
                    grid[y][x] = FROM_RGB[(r, g, b)]
        frames.append(grid)
    return frames


def neighbours(x, y):
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def components(cells):
    seen, found = set(), []
    for start in cells:
        if start in seen:
            continue
        queue, part = deque([start]), set()
        seen.add(start)
        while queue:
            cell = queue.popleft()
            part.add(cell)
            for n in neighbours(*cell):
                if n in cells and n not in seen:
                    seen.add(n)
                    queue.append(n)
        found.append(part)
    return found


def with_holes(cells):
    """The cells plus any cell they fully enclose (the cleric's eye slits)."""
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    box = (min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1)
    outside, queue = set(), deque([(box[0], box[2])])
    outside.add((box[0], box[2]))
    while queue:
        x, y = queue.popleft()
        for n in neighbours(x, y):
            if box[0] <= n[0] <= box[1] and box[2] <= n[1] <= box[3] and n not in cells and n not in outside:
                outside.add(n)
                queue.append(n)
    return {(x, y) for x in range(box[0], box[1] + 1) for y in range(box[2], box[3] + 1) if (x, y) not in outside}


def upright_face(head):
    xs, ys = [c[0] for c in head], [c[1] for c in head]
    x0, x1, y1 = min(xs), max(xs), max(ys)
    cx = x0 + (x1 - x0 + 1) // 2 + 1  # a little toward the right: three-quarter view
    return dict(left=cx - 4, right=cx + 1, eye_top=y1 - 7, eye_h=3, nose_y=y1 - 3, teeth_y=y1 - 1, teeth=(cx - 3, cx + 3))


def draw_face(out, head, spec):
    def put(x, y, char):
        if (x, y) in head:
            out[y][x] = char

    for left in (spec['left'], spec['right']):
        for dy in range(spec['eye_h']):
            for dx in range(3):
                put(left + dx, spec['eye_top'] + dy, 'O')
        put(left + 1, spec['eye_top'] + spec['eye_h'] // 2, EYE_GLOW)
    if spec['nose_y'] is not None:
        mid = (spec['left'] + 2 + spec['right']) // 2
        put(mid, spec['nose_y'], GAP)
        put(mid + 1, spec['nose_y'], GAP)
    for i, x in enumerate(range(spec['teeth'][0], spec['teeth'][1] + 1)):
        put(x, spec['teeth_y'], 'O' if i % 2 == 0 else BONE_HI)


def paint(grid, pose_id):
    out = [row[:] for row in grid]
    solid = {(x, y) for y in range(CELL) for x in range(CELL) if grid[y][x] != '.'}
    dome = {(x, y) for (x, y) in solid if grid[y][x] in DOME}
    head = with_holes(max(components(dome), key=len)) if dome else set()

    # Skull: keep the dome's own light and shade.
    for x, y in head:
        out[y][x] = {'a': BONE_HI, 'f': BONE_SHADE}.get(grid[y][x], BONE)

    body = [(x, y) for (x, y) in solid if (x, y) not in head and grid[y][x] != 'O']
    if body:
        top = min(c[1] for c in body)
        height = max(c[1] for c in body) - top + 1
        pelvis = top + round(height * RIB_ZONE)
        knee = top + round(height * KNEE_AT)
        for x, y in body:
            if pose_id in LYING:
                band = x % 3  # bone bands run along the body, not down it
                out[y][x] = GAP if band == 0 else (BONE_HI if band == 1 else BONE)
            elif y < pelvis:
                band = (y - top) % 3  # ribs
                out[y][x] = GAP if band == 0 else (BONE_HI if band == 1 else BONE)
            elif y == pelvis or y == knee:
                out[y][x] = GAP  # pelvis and knee joints
            else:
                out[y][x] = BONE_HI if y == pelvis + 1 or y == knee + 1 else BONE

    # Light from the top left: bone edges facing right or down fall into shade.
    for x, y in body:
        if out[y][x] in (BONE_HI, BONE):
            right, below = grid[y][x + 1] if x + 1 < CELL else '.', grid[y + 1][x] if y + 1 < CELL else '.'
            if right in 'O.' or below in 'O.':
                out[y][x] = BONE_SHADE

    spec = FACES.get(pose_id)
    if head and spec is None and pose_id in UPRIGHT_FACES:
        spec = upright_face(head)
    if head and spec:
        draw_face(out, head, spec)
    return out


def write_sheet(path, frames, cols, rows):
    image = Image.new('RGBA', (cols * CELL, rows * CELL), (0, 0, 0, 0))
    px = image.load()
    for index, grid in enumerate(frames):
        ox, oy = (index % cols) * CELL, (index // cols) * CELL
        for y in range(CELL):
            for x in range(CELL):
                if grid[y][x] != '.':
                    px[ox + x, oy + y] = (*TO_RGB[grid[y][x]], 255)
    image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('cleric', type=Path, help='folder of the cleric pose PNGs')
    parser.add_argument('out', type=Path, help='folder to write skeleton-<pose>.png into')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for action, facing, cols, rows in ep.POSES:
        pose_id = action + facing
        frames = read_frames(ep.find_source(args.cleric, pose_id), cols, rows)
        write_sheet(args.out / f'skeleton-{pose_id}.png', [paint(g, pose_id) for g in frames], cols, rows)
    print(f'wrote {len(ep.POSES)} poses to {args.out}')


if __name__ == '__main__':
    main()
