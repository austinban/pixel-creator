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

## Conventions

Everything here follows one set of rules for cell sizes, facings, standing on the ground, outlines,
size and weight, how characters lean into a movement, the attack swing, weapons and colour ramps.
They were measured from the original bases. Read [CONVENTIONS.md](CONVENTIONS.md) before making a
new character, creature or weapon, and check the whole project with:

```bash
python3 tools/check_conventions.py
```

Generating a character runs the same checks and stops, writing nothing, if a frame breaks one.
Design in 3D first: `python3 tools/make_NAME.py --model previews/NAME-3d.png` shows the model from five
angles in seconds, before any sprites are made.
The checker has its own tests: `python3 -m unittest discover -s tools -p 'test_*.py'`.

## Characters

`characters.html` recolours a set of base poses into new characters. Pixels in
the base poses are colour *roles*, one per slot of the art's shared master
palette (orange, coral, magenta, indigo, teal...), and a character is a role ->
colour map, so one edit recolours every pose at once. Roles are named for the
colour, not what it paints: the cleric's dome and the fighter's hair come from
the same slots.

There can be several bases (cleric, fighter, mage, skeleton, zombie, knight) on the same poses. Pick one with
**Base**; your colours carry over when you switch.

Bases never change. They sit at the top of the picker as read-only entries, and
the first time you change anything on one (a colour, Randomize, or saving an
edited pose) the change goes into a new saved copy, which becomes the selection.
Copies save themselves as you edit, and you can keep as many as you like.
**Duplicate** copies a copy (its colours and edits), **New** starts a copy from
the base's original colours, and **Delete** removes a copy. The Assets page works
the same way, including **Edit in editor** (all frames of an asset, one at a time)
and **Revert edits**.

**Browse assets** opens a picture of every asset, grouped by category (Grass, Dirt,
Stone, Water, Crates, Nature, Fences, Stairs, Markers) with a search box. Click one
to open it; your own copies get a group of their own. The ground tiles are sliced
from `sprites/assets/ground.png` (a sheet of 32 × 32 cells) by `tools/make_ground.py`,
which `tools/make_assets.py` runs, so rebuild with `python3 tools/make_assets.py`.
Each pixel maps to the shared palette. Three colours in the sheet (a brighter green
and two highlights) snap to their nearest palette colour, and the faint see-through
shadow sprites are left out, because assets are solid colour only. New kinds of item should reuse `copies.js` and the editor's
hand-off (`store`, `baseField`, `unitId`, `returnUrl`) rather than add their own flow.

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

The second asset is the **rock barrier**, a piece of terrain you can't walk through.
It is a set of four **variants**, not an animation (a boulder, a tall rock, a pair,
and a low slab), so the page lets you click one instead of playing it. Each rock is
a jittered, subdivided mesh with a flat base, flat-shaded in cool stone with moss
speckled on the upward-facing surfaces, so it recolours through the same sliders.
It is built to the characters' scale: the same 32 × 32 cell, and the lowest painted
row is row 27, the same row a standing character's feet end on, so a rock and a
character placed in the same cell share a ground line. **With a character** shows
them side by side on that line. Each variant keeps at least 3 pixels clear of the
cell edge.

Unlike the characters, the asset data is generated from code, not from anyone's art,
so `assets/data.js` is committed. To change the crystal, edit `CRYSTAL` in
`tools/make_assets.py` (cell size, frames, size, tilt, bob) and run:

```bash
python3 tools/make_assets.py
```

Add `--png-dir sprites/assets` to also write each sheet as a PNG and check that it
re-reads identical. To add another asset, add a renderer beside the crystal and the rock. An asset says
whether it is an `animation` or a set of `variants`, and whether it sits `above` a
character or `ground`ed beside one.

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

## Terrain

`terrain.html` lays the ground tiles out as an isometric map: grass with trees,
bushes, rocks and flowers scattered over it, and a lake. The lake's edge tiles are
chosen so the white foam sits on the sides that touch land, and the grass is a mix
of plain cubes, cubes with a dirt patch and cubes with stepping stones. **New map**
makes another; a seed makes the same map again. Water can sit level with the grass
or sunken below it, and **Export map PNG** saves it with a transparent background.
It uses the tiles' original colours and reads `assets/data.js`.

## Creatures

A base that isn't a repaint of the humanoid fighter, like the dog and the rat, is built from a small
3D model: ellipsoids for the body parts, rendered from an isometric camera into the
shared palette and written as the usual 14 poses. `tools/creature.py` is the shared
renderer, `tools/make_dog.py` is the worked example to copy for the next creature, and
`tools/make_rat.py` shows a smaller one with its own proportions and a long tail.

```bash
python3 tools/make_dog.py sprites/dog --preview dog.png
python3 tools/extract_poses.py --merge dog=sprites/dog
python3 tools/make_rat.py sprites/rat
python3 tools/extract_poses.py --merge rat=sprites/rat
```

`--merge` adds the creature to the existing `poses/base.js` and leaves the other bases as
they are, so it works without every base's sprite folder.

## Humanoids

A person is built the same way, from `tools/humanoid.py`: a torso, a big head, two arms and
two legs as ellipsoids, with the arms and legs solved so hands go where a pose puts them and
feet stay on the ground. It comes with all 14 poses, so a character is only a description.
`tools/make_human.py` is the generic person; copy it and change the name, colours, hair,
proportions or add accessories (a hat that follows the head, a staff that follows a hand).
`tools/make_slim.py` is a second build of the same person with a lighter body: one script, with its
own tuned numbers, and it passes the same checks (with a declared allowance for less weight).
`tools/make_ninja.py` is the Slim restyled: the same body, so it borrows the Slim's tuned numbers,
with a dark gi, red sash, hood, face mask and headband added through the builder's accessories hook.
It is a model for dressing up any build without redrawing poses.

```bash
python3 tools/make_human.py sprites/human --preview human.png
python3 tools/extract_poses.py --merge human=sprites/human
```

The options and how to add accessories are at the top of `tools/humanoid.py`.

## Weapons

Weapons are assets in a **Weapons** category, read from strips in `sprites/weapons/` (ignored by
git like the other source art):

```
sprites/weapons/20240429weapons-IronAxeattackNE.png     4 frames of 48 x 48, side by side (192 x 48)
sprites/weapons/20240429weapons-IronAxeattackSE.png
```

(`iron-axe-attackNE.png` works too.) A weapon cell is 48 x 48, bigger than a character's 32 x 32,
so a swing can reach past the character's edge; the character sits in the middle of it, 8 pixels in
from each side. Each frame has the weapon where it sits in that frame of an attack, so laying it
behind the character's frame puts it in the hand. Rebuild the assets after adding strips:

```bash
python3 tools/make_assets.py
```

Each strip becomes an asset ("Iron axe NE", "Iron axe SE") that recolours and can be copied and
edited like any other. On the Characters page, **Weapon overlay** draws the chosen weapon behind the
attack poses frame by frame, as it sits in the game. The **Frame** buttons (or `←` `→`, `A` `D`) step through by hand, and
Play runs it. A weapon copy you have made on the Assets page appears in the same menu, in its own
colours; for the facing it has no strip for, the original weapon is used.

When you are viewing a weapon on the Assets page, **Preview with character animation** draws it behind a
character's matching attack (or one of your copies of a character), one frame at a time, in step with
the weapon's own frames and in its own colours.

To make a humanoid's attack hold the weapon properly, `python3 tools/fit_hands.py` finds where the
strike hand has to go in each frame so it ends up at the weapon's grip, and prints the positions
for the attack poses in `humanoid.py`.
