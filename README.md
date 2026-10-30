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

There can be several bases (cleric, fighter, mage, skeleton, zombie, knight) on the same poses. Pick one with
**Base**; your colours carry over when you switch.

Characters are saved in your browser as instances. **Duplicate** copies one (its
colours and its edits), **New** starts from the base's original colours, and
**Delete** removes one. Each has its own colours, so a copy can be recoloured
without touching the original.

**Edit in editor** opens the selected pose in the editor, at the pose's own size.
**Save to character** writes your changes back to that character as an edit, and
the pose card shows a dot. Pixels that still match one of the character's colours
are stored as that colour's role, so they follow later recolouring; pixels in
other colours stay as drawn. **Revert edits** puts the base pose back.

**Export full set (ZIP)** downloads every pose of the current character as PNGs,
and **Export all characters (ZIP)** does the same for every saved character, one
folder each. The pixel-size menu applies to both.

Poses are named `<action><facing>`, like the source files they come from
(`20240427cleric-attackNE.png` becomes `attackNE`). NE faces away from the
camera, SE toward it. Exports are named `<character>-<pose>.png`. Saved
character files record their base; files saved before roles followed the
palette still load.

The pose data is built from folders of sprite PNGs and is not stored in the
repo (`poses/` is git-ignored). Rebuild it with:

```bash
python3 tools/extract_poses.py cleric=path/to/cleric fighter=path/to/fighter mage=sprites/mage skeleton=sprites/skeleton zombie=sprites/zombie knight=sprites/knight
```

The skeleton is not drawn by hand: `tools/make_skeleton.py` repaints the cleric's
poses as bone (the dome becomes a skull, the body ribs and legs), keeping every
silhouette, so it shares anchors and the ground line with the other bases. Run
it first to produce `sprites/skeleton`:

```bash
python3 tools/make_skeleton.py path/to/cleric sprites/skeleton
```

The zombie works the same way on the fighter's poses (`tools/make_zombie.py`),
but it reshapes the silhouette: the hair is cut away to a bald green head with an
exposed skull wound and a stitched gash, the arm on the character's right is gone
(a torn sleeve and a bleeding stump), and the chest is torn open to the ribs.
Wounds and the stump follow the head and shoulders, so nothing flickers when a
walk cycle plays. The crouched `weak` frames keep their arms, which are folded
against the body.

```bash
python3 tools/make_zombie.py path/to/fighter sprites/zombie
```

The knight (`tools/make_knight.py`) is also built on the fighter's poses and
reshapes them too: the hair becomes a rounded steel helm with a crest, a gold
brow band and a dark visor, and the body is repainted as clean plate, with
breastplate bands and a gold belt, plated shoulders, and gauntlets and greaves.
No skin is left showing. The crest, breastplate, shoulders and knees are drawn on
the standing frames; the lying and crouched ones get the helm and plain plate.

```bash
python3 tools/make_knight.py path/to/fighter sprites/knight
```

Raw sprite PNGs can live in `sprites/`, which is also git-ignored. This needs
Python 3 with Pillow. It stops on any pixel whose colour has no role
(add it to `ROLES` in the script), and re-renders every frame from its roles to
check it matches the source exactly.

## Assets

`assets.html` is for things that aren't characters. They are painted in the same
colour roles, so they recolour the same way, and each saved item has its own
colours, so you can keep a crystal per player. There are the same Duplicate, New
and Delete buttons, and exports as PNG sheets or ZIPs of every frame.

The first asset is the **turn crystal**: a Sims-style marker for whose turn it is,
hovering above the active character and turning as it bobs. It is rendered from a
small 3D model (a stretched octahedron, flat-shaded) by `tools/make_assets.py`, so
the rotation is real, and it repeats every quarter turn, so it loops without a
seam. It is 8 frames at 8 a second, in a 32 × 32 cell, the same cell as the
characters, with at least 5 pixels clear on every side so nothing clips and there
is room for a glow later. Each asset names an **anchor**, the point where its tip
hangs at rest: put that point where you want the tip. **Over a character** shows
it placed that way, two rows above any head at rest, one to three as it bobs.

Unlike the characters, the asset data is generated from code, not from anyone's art,
so `assets/data.js` is committed. To change the crystal, edit `CRYSTAL` in
`tools/make_assets.py` (cell size, frames, size, tilt, bob) and run:

```bash
python3 tools/make_assets.py
```

Add `--png-dir sprites/assets` to also write each sheet as a PNG and check that it
re-reads identical. To add another asset, add a renderer beside the crystal.

## Layout

| File | What's in it |
| --- | --- |
| `index.html` | Markup for the panel and the canvas |
| `styles.css` | All styling |
| `app.js` | The editor: model, rendering, input, history, export, and saving a pose back to a character |
| `characters.html`, `characters.js` | Recolour the base poses, keep saved characters, export them |
| `assets.html`, `assets.js` | Recolour assets, keep saved copies, preview them over a character, export |
| `assets/data.js` | The built assets (committed; made by `tools/make_assets.py`) |
| `tools/make_assets.py` | Renders the turn crystal and writes `assets/data.js` |
| `colors.js`, `files.js` | Colour maths and download helpers shared by the pages |
| `zip.js` | A small ZIP writer for the export buttons |
| `tools/extract_poses.py` | Builds `poses/base.js` from sprite PNGs |
| `tools/make_skeleton.py` | Paints the skeleton base on the cleric's poses |
| `tools/make_zombie.py` | Paints the zombie base on the fighter's poses |
| `tools/make_knight.py` | Paints the armoured knight base on the fighter's poses |
