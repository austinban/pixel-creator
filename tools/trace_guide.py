#!/usr/bin/env python3
"""Turn a picture of a pose and colour guide (tools/make_pose_guide.py) back into sprite sheets, whatever made the picture.

    python3 tools/trace_guide.py generated-guide.jpg spirit sprites/spirit

The picture does not have to be pixel-exact (an image generator redraws the guide at another size, a little blurred and shifted). The tool finds the
panels by their colour, cuts each frame into a 32 x 32 grid, takes the middle colour of every grid square, snaps it to the nearest palette role,
and drops the panel behind the figure (flood-filled from the frame's edge, so dark figure colours that match the panel stay). It writes
NAME-<pose><facing>.png in the layout of the guide: frames side by side, the walk in two rows of four.
The result is a first trace: look at it (--preview) and tidy what the picture got wrong before using it as a base.
"""
import argparse
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep

ORDER = [('walking', 4, 2), ('attack', 4, 1), ('bow', 4, 1), ('charging', 1, 1), ('release', 1, 1), ('damage', 1, 1), ('weak', 1, 1), ('dead', 1, 1)]
CELL = 32


def runs(v, th, min_len):
    out, s = [], None
    for i, x in enumerate(v):
        if x > th and s is None:
            s = i
        if x <= th and s is not None:
            if i - s >= min_len:
                out.append((s, i - 1))
            s = None
    if s is not None and len(v) - s >= min_len:
        out.append((s, len(v) - 1))
    return out


def find_panels(a):
    panel = np.array([50, 44, 84])
    m = np.abs(a.astype(int) - panel).sum(2) < 40
    cols = runs(m.sum(0), a.shape[0] * 0.15, 50)
    rows = runs(m.sum(1), a.shape[1] * 0.25, 40)
    return cols, rows


def trace_frame(a, x0, y0, size, palette, names):
    """One frame: the box (x0, y0, size, size) of the picture as 32 x 32 role letters."""
    step = size / CELL
    grid = [[None] * CELL for _ in range(CELL)]
    for j in range(CELL):
        for i in range(CELL):
            cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
            r = max(1, int(step * 0.3))
            box = a[int(cy - r):int(cy + r) + 1, int(cx - r):int(cx + r) + 1].reshape(-1, 3)
            c = np.median(box, axis=0)
            grid[j][i] = int(np.argmin(((palette - c) ** 2).sum(1)))
    return grid


def components(pts):
    """Groups of pixels touching each other, corners included."""
    left, out = set(pts), []
    while left:
        seed = left.pop()
        group, todo = {seed}, [seed]
        while todo:
            x, y = todo.pop()
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + d[0], y + d[1])
                if n in left:
                    left.discard(n)
                    group.add(n)
                    todo.append(n)
        out.append(group)
    return out


def tidy(figure, outline, single=False):
    """Clean one traced frame: drop the label text and edge speckle, keep a spark only if it is near the body, and close gaps in the outline."""
    if not figure:
        return figure
    groups = sorted(components(figure), key=len, reverse=True)
    body = groups[0]
    keep = set(body)
    for g in groups[1:]:
        xs, ys = [x for x, _ in g], [y for _, y in g]
        label = max(xs) < 12 and min(ys) >= 26                 # the NE / SE caption in the picture
        edge = min(xs) == 0 or max(xs) == CELL - 1 or min(ys) == 0 or max(ys) == CELL - 1
        near = min(abs(x - bx) + abs(y - by) for x, y in g for bx, by in body) <= 7
        if len(g) >= 3 and near and not label and not edge:
            keep |= g
        elif len(g) <= 2 and near and not label and not edge:     # a spark of one or two pixels
            keep |= g
    out = {k: v for k, v in figure.items() if k in keep}
    # wisps that stray far from the body are cut (a creature is at most 26 wide, outline included), then the frame is moved sideways to sit inside the cell
    # (columns 2-29, so an outline fits round it) and, for a single pose, to the middle
    cx = sum(x for x, _ in body) / len(body)
    out = {k: v for k, v in out.items() if abs(k[0] - cx) <= 11.5}
    lo, hi = min(x for x, _ in out), max(x for x, _ in out)
    shift = 0
    if single:
        shift = round(16.5 - (lo + hi + 1) / 2)
    shift += max(0, 2 - (lo + shift)) - max(0, (hi + shift) - 29)
    out = {(x + shift, y): v for (x, y), v in out.items()}
    # an outline pixel on any open side of anything that is not already outline, so the figure is outlined all round
    for (x, y) in list(out):
        if out[(x, y)] == outline:
            continue
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + d[0], y + d[1])
            if n not in out and 0 <= n[0] < CELL and 0 <= n[1] < CELL:
                out[n] = outline
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('image', type=Path)
    ap.add_argument('name')
    ap.add_argument('out', type=Path)
    ap.add_argument('--panel', default='322c54', help='the panel colour behind the figures, hex (the guide uses 322c54)')
    ap.add_argument('--raw', action='store_true', help='skip the tidying: keep every pixel the trace found')
    args = ap.parse_args()

    im = Image.open(args.image).convert('RGB')
    a = np.array(im)
    cols, rows = find_panels(a)
    if len(cols) != 2 or len(rows) != len(ORDER):
        sys.exit(f'expected 2 columns and {len(ORDER)} rows of panels, found {len(cols)} and {len(rows)}')
    letters = [c for c, *_ in ep.ROLES]
    palette = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for *_, h in ep.ROLES], dtype=float)
    outline = 0
    args.out.mkdir(parents=True, exist_ok=True)
    for (pose, nc, nr), (ry0, ry1) in zip(ORDER, rows):
        for facing, (cx0, cx1) in zip(('NE', 'SE'), cols):
            size = (cx1 - cx0 + 1) / 4          # a frame is a quarter of the panel's width
            sheet = Image.new('RGBA', (nc * CELL, nr * CELL), (0, 0, 0, 0))
            px = sheet.load()
            for f in range(nc * nr):
                fx, fy = cx0 + (f % nc) * size, ry0 + (f // nc) * size
                grid = trace_frame(a, fx, fy, size, palette, letters)
                # the panel is whatever touches the frame's edge and is panel-coloured
                pan = np.argmin(((palette - np.array([int(args.panel[i:i + 2], 16) for i in (0, 2, 4)])) ** 2).sum(1))
                for k in range(CELL):                  # the picture's edge shadow and the panel's border are not part of any figure
                    grid[0][k] = grid[CELL - 1][k] = grid[k][0] = grid[k][CELL - 1] = pan
                bg = [[False] * CELL for _ in range(CELL)]
                q = deque((x, y) for y in range(CELL) for x in range(CELL) if x in (0, CELL - 1) or y in (0, CELL - 1))
                while q:
                    x, y = q.popleft()
                    if not (0 <= x < CELL and 0 <= y < CELL) or bg[y][x]:
                        continue
                    if grid[y][x] == pan:
                        bg[y][x] = True
                        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
                figure = {(x, y): grid[y][x] for y in range(CELL) for x in range(CELL) if not bg[y][x]}
                if not args.raw:
                    figure = tidy(figure, letters.index('O'), nc * nr == 1)
                for (x, y), k in figure.items():
                    h = ep.ROLES[k][4]
                    px[(f % nc) * CELL + x, (f // nc) * CELL + y] = (*(int(h[i:i + 2], 16) for i in (0, 2, 4)), 255)
            sheet.save(args.out / f'{args.name}-{pose}{facing}.png')
    print(f'traced {len(ORDER) * 2} sheets -> {args.out}')


if __name__ == '__main__':
    main()
