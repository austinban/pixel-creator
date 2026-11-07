"""Shared by everything that makes assets: the sheet layout, the one way to write an asset record, and the one way to write a family's package file.

An asset family is a module with `build_assets()` that returns a list of asset records, and, if it ships a folder with a README, `write_package(folder)`.
tools/registry.py lists the families in the order the Assets page shows them, tools/buildcache.py rebuilds only the ones whose code or inputs changed, and
tools/make_assets.py writes the results.
"""
import json
import math
from pathlib import Path

SHEET_COLS = 8      # frames per row in an asset's sheet
GROUND_ROW = 27     # the lowest painted row of a standing character: assets that sit on the ground end here too


def sheet_layout(count):
    return min(count, SHEET_COLS), -(-count // SHEET_COLS)


def normalise(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def asset(id, label, category, kind, place, frames, w, h, anchor, *, fps=0, cols=None, rows=None, **extra):
    """One asset record. `kind` is still, animation or variants; `anchor` is (x, y) in the cell; cols and rows follow from the frame count unless given."""
    if cols is None:
        cols, rows = sheet_layout(len(frames))
    return dict(id=id, label=label, category=category, kind=kind, place=place, w=w, h=h, cols=cols, rows=rows, fps=fps,
                anchor={'x': anchor[0], 'y': anchor[1]}, frames=frames, **extra)


def family(category, w, h, anchor, place='ground', folder=None):
    """A maker of asset records that share a category, cell, anchor and placement (and a folder, if the family ships one): `make(id, label, kind, frames, fps=0, **extra)`."""
    def make(id, label, kind, frames, fps=0, **extra):
        if folder:
            extra['folder'] = folder
        return asset(id, label, category, kind, place, frames, w, h, anchor, fps=fps, **extra)
    return make


def write_json(folder, name, about, body):
    """The machine-readable half of a family's package (`NAME.json` beside the sheets): an `about` line, then the family's numbers."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps({'about': about, **body}, indent=1))


def inside(p, x, y):
    """Whether the point (x, y) is inside the triangle p, ignoring depth."""
    (x0, y0, _), (x1, y1, _), (x2, y2, _) = p
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return False
    a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
    b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
    return a >= 0 and b >= 0 and 1 - a - b >= 0

