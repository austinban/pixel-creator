#!/usr/bin/env python3
"""The shared footprint for area-of-effect spells: five plots, one in the middle and one out in each direction.

Every area spell (fire burst, and the ones to come) is drawn on the same cell with the same plot positions,
so any of them can be dropped on a target tile and hits the same five plots. A plot is a ground tile's top
face, a diamond 32 wide and 16 tall (see terrain.js), and one grid step moves the drawing 16 across and 8 down.

    the four neighbours:    NW (-16, -8)    NE (+16, -8)
                            SW (-16, +8)    SE (+16, +8)       the middle plot is (0, 0)

The cell is CELL_W x CELL_H with the middle plot's centre, on the ground, at MIDDLE. There is room above for
the tallest effect, and below for the two near plots. Draw back to front (DEPTH_ORDER) so the effect on a near
plot overlaps a far one the way it would in the world.
"""
CELL_W, CELL_H = 80, 56
MIDDLE = (40, 38)                       # the middle of the middle plot, on the ground (the asset's anchor)

PLOTS = {'C': (0, 0), 'NW': (-16, -8), 'NE': (16, -8), 'SW': (-16, 8), 'SE': (16, 8)}
DEPTH_ORDER = ('NW', 'NE', 'C', 'SW', 'SE')      # far to near


def centre(plot):
    """Where a plot's middle is on the cell, on the ground."""
    dx, dy = PLOTS[plot]
    return MIDDLE[0] + dx, MIDDLE[1] + dy


def inside(plot, x, y, shrink=0.0):
    """Is a cell pixel inside a plot's diamond?"""
    cx, cy = centre(plot)
    return abs(x + 0.5 - cx) / 16 + abs(y + 0.5 - cy) / 8 <= 1.0 - shrink + 1e-9


def blank():
    return [['.'] * CELL_W for _ in range(CELL_H)]


def put(grid, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < CELL_W and 0 <= y < CELL_H and c != '.':
        grid[y][x] = c


def lines(grid):
    return [''.join(row) for row in grid]
