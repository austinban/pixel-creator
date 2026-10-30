# Pixel Creator

A small, dependency-free pixel art editor that runs from a single folder of
static files. Pick a grid size, pick a colour, fill in cells, export a PNG with
a transparent background.

## Running it

Open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 4321
```

Then visit http://localhost:4321.

## What it does

- **Canvas size** — any grid from 1×1 up to 128×128, plus 8/16/32/64 presets.
  Resizing keeps the pixels that still fit inside the new bounds.
- **Palette** — 16 starter colours, a colour picker, and *Add* to put a custom
  colour into the palette.
- **Tools** — pencil (`B`), eraser (`E`), flood fill (`G`), eyedropper (`I`).
- **Undo / redo** — `Cmd/Ctrl+Z` and `Cmd/Ctrl+Shift+Z`. A whole drag counts as
  one step.
- **Import** — load a PNG, GIF or WebP up to 128×128 at one image pixel per
  cell. The grid resizes to fit, transparent pixels stay empty, and the
  image's colours are added to the palette. Pixels that are at least half
  opaque become solid; the rest become empty.
- **Export** — PNG at 1×, 8×, 16× or 32× the grid. Cells you never touch are
  written as fully transparent pixels, and the export is drawn fresh rather
  than captured from the screen, so neither the grid lines nor the
  transparency checkerboard end up in the file.

## Characters

`characters.html` recolours a set of base poses into new characters. Pixels in
the base poses are colour *roles*, one per slot of the art's shared master
palette (orange, coral, magenta, indigo, teal...), and a character is a role ->
colour map, so one edit recolours every pose at once. Roles are named for the
colour, not what it paints: the cleric's dome and the fighter's hair come from
the same slots.

There can be several bases (cleric, fighter) on the same poses. Pick one with
**Base**; your colours carry over when you switch.

Poses are named `<action><facing>`, like the source files they come from
(`20240427cleric-attackNE.png` becomes `attackNE`). NE faces away from the
camera, SE toward it. Exports are named `<character>-<pose>.png`. Saved
character files record their base; files saved before roles followed the
palette still load.

The pose data is built from folders of sprite PNGs and is not stored in the
repo (`poses/` is git-ignored). Rebuild it with:

```bash
python3 tools/extract_poses.py cleric=path/to/cleric fighter=path/to/fighter
```

This needs Python 3 with Pillow. It stops on any pixel whose colour has no role
(add it to `ROLES` in the script), and re-renders every frame from its roles to
check it matches the source exactly.

## Layout

| File | What's in it |
| --- | --- |
| `index.html` | Markup for the panel and the canvas |
| `styles.css` | All styling |
| `app.js` | The editor: model, rendering, input, history, export |
| `characters.html`, `characters.js` | Recolour the base poses, save and export characters |
| `tools/extract_poses.py` | Builds `poses/base.js` from sprite PNGs |
