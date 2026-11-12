# Pixel Creator

Working on the repo, or an agent working in it? Start with [AGENTS.md](AGENTS.md): the rules, the build and cache, how to add an asset family, and what the game reads.

A small, dependency-free pixel art editor that runs from a single folder of
static files. Pick a grid size, pick a colour, fill in cells, export a PNG with
a transparent background.

## Running it

Open `index.html` in a browser, or serve the folder:

```bash
python3 tools/serve.py
```

Then visit http://localhost:4321. (`tools/serve.py` tells the browser never to keep old copies of the files, so a
rebuilt asset shows on a normal reload. Each page also loads its scripts with a changing `?v=` on the address, so it
shows the newest copy even from a plain `python3 -m http.server` or by opening the file directly.)

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
and **Export for the game (ZIP, 1×)** is the same at true size with a `pixel-creator.json` saying what it is, and **Save to sprites/ (1×)** (Chromium) writes it straight into the repo's `sprites/` folder for the game's sync script. **Export all characters (ZIP)** does the same for every saved character, one
folder each. The pixel-size menu applies to the two ordinary exports.

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

On the Characters and Assets pages the address says what is on screen: the browse grid has no `?item=`, and an opened one is `?item=ID`
(`assets.html?item=base:crystal`). Clicking into something, or going back to the grid, is a step in the browser history, so **Back** returns to
what you had before and **Forward** goes on again, and a link to an item opens straight on it.

`assets.html` is for things that aren't characters. They are painted in the same
colour roles, so they recolour the same way, and each saved item has its own
colours, so you can keep a crystal per player. There are the same Duplicate, New
and Delete buttons, and exports as PNG sheets or ZIPs of every frame.

The **vine spell** is the first of the **Animations** category: a vine shoots up out of the ground,
swells and opens its leaves, hangs a frame, then slams straight back down in a burst of earth. It is 8
frames at 8 a second in a 32 × 48 cell (the vine is taller than a character), anchored at the middle
of its foot on the ground. It is made from a small 3D model in the bush and tree's greens; look at the
model first with `python3 tools/make_vine.py --model previews/vine-3d.png`. The frame list (`FRAMES` in
`tools/make_vine.py`) says what each frame does, so a frame can be added or held by editing one line.

The overlays also come **cut to the ground tiles' shapes**: each colour has a see-through and a solid set of 14 shapes (a flat top on a
full block, a flat top 8 rows lower, and the twelve ramps, stepped ramps and half blocks of Grass 3 to 8 and 15 to 20), 32 × 32 and lined up with
the tile, so an overlay is drawn where the tile is. Grass, dirt, stone, water, crates and stairs share these shapes, and every ground
tile has an `overlay` number in `assets/data.js` saying which one fits it. Each colour also has an **animated** solid set for hovering (a row for each shape and the eight breathing frames across, so a
hover plays one row), and its own overlays for the **bridge** decks, in the bridge's own 32 × 40 cell and in the order of its four sprites (see-through
and solid). The angled shapes are read from the ground sheet with
`tools/extract_overlay_shapes.py`, and `python3 tools/make_overlay.py --shapes previews/overlay-shapes.png` shows them over their tiles.

The **fire burst** is an area spell on five plots, one in the middle and one out in each direction: it
ignites at the middle, bursts out onto the four around it, burns at full strength and dies to embers
and smoke. It is 8 frames at 8 a second in an 80 × 56 cell, anchored on the middle plot, and is the template for other
area spells (`tools/make_aoe.py` has the shared footprint; see Area-of-effect spells in CONVENTIONS.md).
Preview it over five ground tiles with `python3 tools/make_fire.py --preview previews/fire-burst.png`.

The **healing spell** is pink rose petals that appear above a character and drift down over them and are gone by the last frame (nothing
touches the ground): 8 frames at 8 a second in a 32 × 48 cell (like the vine), anchored at the middle of the feet on the ground
(`tools/make_heal.py`; `--preview` shows the frames over a character).

The **tile overlays** are flat tones laid over a ground tile's top face (a 32 × 16 diamond): blue for choosing where
to move, plus yellow and red. They cover the whole tile but are **see-through** (an asset's `opacity` is applied when
it is drawn and in its PNG export), so they tone the grass underneath instead of hiding it. They are a single still frame
for now. Each also has a solid version for hovering, which animates (eight slow frames). They are in the **Overlays**
category, in colours already in the ground tiles' palette (`tools/make_overlay.py`).

The **rickety bridge** spans a gap between two pieces of land, and is in the **Bridges** category as one asset with four
one-tile sprites (32 × 40, anchored on the middle of the land-level top face, so it sits where a ground tile would): a flat section
and the sloped start of a bridge, each running NE-SW or NW-SE. The deck hangs a few pixels below the land, and a slope joins
it to the land. The slopes going NW and SW are the NE and SE ones flipped left to right, so a bridge is built as land, slope,
flat sections, the flipped slope, land: a NE-SW bridge starts with the NE slope and ends with the flipped SE slope, and a NW-SE
one starts with the SE slope and ends with the flipped NE one. It has a rope rail along the back side only, so a character crossing it is never hidden by a front rail. The planks are uneven on
purpose, with a missing one, a frayed rope and a leaning post. `python3 tools/make_bridge.py --preview previews/bridge.png` shows a whole bridge each way over sunken water.
The terrain page lays one across the lake where land is close on both sides (tick "Bridge across the water"; it needs sunken water, now the default), and
`terrain.html?seed=7` opens a particular map.

The **mushroom trees** are six giant mushrooms for the corrupted lands, to stand where trees would, in the **Mushroom Trees** category (`tools/make_fungi.py`; `--preview` shows them over their footprints): a spotted
toadstool, a bell, a cluster of three, a puffball and a parasol on one tile each, and a **giant toadstool on four tiles (2 x 2) whose flat top is two levels up and can be walked on**. One picture each (they look the same from
every side), anchored at the middle of the footprint. They are one folder, `sprites/assets/mushroom-trees/`, with its own README and `mushroom-trees.json`.

The **rat king** is the first **elite**: a creature bigger than an ordinary one that still stands on a single tile, drawn in a **64 x 64** cell (twice a person's; the boss is 96 x 96 on a 2 x 2 footprint). It is a great
bulbous rat with a large face and whiskers, five smaller rats fused into its flanks and six tails, in the **Elites** category (`tools/make_rat_king.py` makes the sprites, `tools/make_elite.py` the assets, `--model` shows it in 3D first).
It has a charging, a four-frame attack, release, damage, weak, dead and an eight-frame walk, in both facings, as `rat-king-ACTION-ne` and `-se`, anchored at (32, 52).

The **blood mushroom** is a boss for the corrupted lands, on a **2 x 2** footprint in a **96 x 96** cell (the same as the scorpion emperor): a tall crimson-domed mushroom with spots, a gill skirt and dripping blood, on a swollen
flesh stem, with reaching human arms and hands, a rat head, dangling legs and antlers growing out of it. It never walks, so, like the stone totem, the walk is its breathing idle and the attack a four-frame spore pulse; it has all
the actions, both facings, as `blood-mushroom-ACTION-ne` and `-se` in the **Bosses** category, anchored at (48, 72) (`tools/make_blood_mushroom.py` makes the sprites, `tools/make_boss.py` the assets).

The **All Tree** is the victory screen's display piece, in the **Victory Screen** category: a massive ancient tree being corrupted by the mushrooms, one **384 x 448** picture on a **10 x 10** tile base that rises 20 levels and runs off the top of the image
(`tools/make_all_tree.py`; `--preview` shows it over its footprint). `all-tree` is a 12-frame loop at 10 a second (a shimmer climbing the fungi, vines and eyes, and glowing drops that fall and splash); `all-tree-still` is the flat picture. They live in
`sprites/assets/all-tree/` with a README and `all-tree.json`.

Each All Tree also comes in a **wide** version (`all-tree-wide`, `all-tree-wide-still`, `all-tree-fall-wide`, `all-tree-fall-wide-still`): the same picture on a **704 x 448** canvas with the anchor at (352, 336), so the sides of the tree are not cut off. They are about 8 MB
of frames each pair, and make `assets/data.js` about 16 MB.

The **autumn All Tree** (`all-tree-fall` and `all-tree-fall-still`) is the same tree without the corruption: no mushrooms, yellow, orange and red foliage in clustered leaves, natural green vines, tumbling leaves and a few glowing fairies. Same cell, anchor and
boughs as the corrupted one (`tools/make_all_tree_fall.py` reuses its model), in `sprites/assets/all-tree-fall/`.

The **trees** are ten more trees and bushes to stand beside the ground sheet's bush and pine, in the **Trees** category (`tools/make_trees.py`; `--preview` shows them beside the originals): a tall pine, a spruce, a poplar, a tall oak (all about
100-128 px, taller than the sheet's 64 px pine), a broad oak, a birch, a small pine, a dead tree, a berry bush and a hedge. One picture each, anchored at the middle of the tile, blocking it. They are in `sprites/assets/trees/` with a README and `trees.json`.

The **animated water** moves all 36 water tiles of the ground sheet, normal and corrupted, open and edge pieces, level and sunken, in the **Animated Water** and **Animated Corrupted Water** categories (`tools/make_water.py`; `--preview` shows them, and `--wave 1` a lake with the wave):
10 frames at 4 a second, ids `water-COL-ROW` and `water-corrupted-COL-ROW` after the ground sheet's cell. The water drifts one tile's width over the loop and the foam crest runs along the shore; the cube, outline and silhouette do not change. The game starts each tile one frame after the one behind it (`(frame + (x + y)) % 10`) for a slow wave. They are in `sprites/assets/water/` with a README and `water.json`.

The **menu buttons** are reusable buttons in the **UI** category (`tools/make_buttons.py`; `--preview DIR` writes every sheet and a contact sheet): a purple bar in a steel bevel with gold corner brackets, rounded ends, a slab for depth and moss, scratches and chips
for wear. 33 sheets, `ui-button-COLOURWAY-HEIGHT-WIDTH`: colourways **primary**, **low** (low contrast) and **red**, heights **std** (48) and **short** (32), widths **sm** 128, **md** 192, **lg** 256 and **xl** 384, plus three small sizes of their own: **short-xs** 48 x 32, **compact-sm** 112 x 40 and **icon-sq** 36 x 36. Each sheet is three cells, the states
**default**, **hovered** and **active**. They have no label. They are in `sprites/assets/buttons/` with a README and `buttons.json`.

The **menu panel** replaces the plain dark box behind a screen's text, in the **UI** category (`tools/make_panel.py`; `--preview` shows it at two sizes beside a button, and its nine pieces): the buttons' steel bevel and gold brackets around a dark ink fill, with moss on the top edge,
pink and glowing teal mushrooms growing off the corners and vines crawling over the frame and hanging into the panel. It is a **nine-slice**, `ui-panel-tl`, `-t`, `-tr`, `-l`, `-c`, `-r`, `-bl`, `-b` and `-br` (corners 40 x 40 of body, the edges and the fill wrap at 64, so any size from 80 x 80 up),
plus `ui-panel`, a ready-made 320 x 120. The top edge has **six pictures** (`ui-panel-t`, `-t2` to `-t6`: vines, mossy, small mushrooms, one vine, big caps, glow-worms) that join in any order, for the game to mix at random. The top row has 14 rows of mushroom above the body and the bottom row 4 of slab. It has no text. They are in `sprites/assets/panel/` with a README that shows how to draw it and where to keep text, and `panel.json`.

The **blood pool** is a decal for a ground tile, in the **Decals** category (`tools/make_blood_pool.py`; `--preview` shows it over a grass tile, alone and under a dead character): six irregular pools, 32 x 16, on the tile's top face
and anchored at its middle (16, 8) like the tile overlays, so one goes where the tile is and a character's dead pose is drawn over it. A pool stays inside the diamond, has no outline, and is a dark rim, a deep red body and a wetter middle with a glint.

The **body explosion** is the burst of gore when a corpse is destroyed, in the **Animations** category (`tools/make_body_explosion.py`; `--preview` shows the frames over a grass tile and writes a gif): `body-explosion`, six frames at 12 a second on a 48 x 48 cell anchored at (24, 34), the middle of the body on the ground, in the blood pool's own four colours with no outline. A hot core bursts, a cloud swells and chunks and drops are thrown out along the ground's isometric plane, the cloud breaks up and the pieces fall, and the last frames are only the splatters where they landed. It is generic, the same burst for every body.

The **slot icons** are three 32 x 32 pictures in the **UI** category for the Weapon, Armor and Trinket slots (a sword, a breastplate, a gem ring), made by `tools/make_slot_icons.py`
(`--preview` shows them enlarged) and shipped in `sprites/assets/slot-icons/` with a README and `slot-icons.json`.

The **item pictures** are 26 inventory icons, 32 x 32, in the **Item icons** category (`tools/make_item_icons3d.py`; `--preview` shows them enlarged), for the items the game's `docs/pixel-creator-requests.md` lists as having no picture (weapons, armour and trinkets, ids `item-recurve_bow` to `item-stone_idol`). Each is a small 3D model rendered with the creatures' renderer (ellipsoids, rods and blocks, see `creature.py`) with its details painted over it; the weapons all lie at 45 degrees, rising to the right. A flat version of the same 26 is in `tools/make_item_icons.py` for comparison. They are in `sprites/assets/item-icons/` with a README, including the one-line copy into the game's `assets/sprites/items/`, and `item-icons.json`.

The **text icons** are five 16 x 16 pictures in the **UI** category for the game's text (`tools/make_hud_icons.py`; `--preview` shows them enlarged and at text size): `icon-gold` (a little golden mushroom), `icon-xp` (a four-point star of cyan light) and `icon-skull-green`, `-yellow` and `-red`, one skull in three colours for an easy, an even and a hard fight. They are in `sprites/assets/hud-icons/` with a README and `hud-icons.json`.

The **movement point dot** is a small UI element, 7 × 7 pixels, in the **UI** category: a filled dot (the move
blue, with a highlight) for each point left, and an empty one (the same shape as a dim socket) for each spent
(`tools/make_ui.py`; `--preview` shows a row of them). There is a red twin of it, with a plum socket for the empty one, and a yellow one for spirit, and each has a **burst**
animation (7 frames, in a 13 × 13 cell, played once) for the moment a point is spent: it swells, flashes, bursts into bits that fly out
and fade, and leaves the empty socket behind.

Each dot also has a **shell** for when a count has wrapped past ten (`ui-movement-dot-shell`, `ui-dot-red-shell`, `ui-dot-yellow-shell`): an 11 × 11 still ring in the dot's own colours, with a dark socket, drawn
behind the dot so it looks nested (one wrap only; it does not animate while idle). The anchors are both middles, so stacking them is a matter of putting the two anchors on the same point. Its own **break**
animation (`...-shell-break`, 8 frames at 14 fps, 19 × 19 cell, played once) swells and cracks, flashes, splits into eight pieces that fly out and crumble, and leaves nothing behind (the dot has its own burst).
`python3 tools/make_ui.py --shell previews/shell.png` shows them.

The **facing marker** is the yellow arrowhead that shows which way a character will face. It
lies flat on the ground and has two frames, NE and SE (20 × 14 cell, not animated); NW and SW are
those mirrored about the anchor, which is the arrow's middle on the ground. The unchosen ones are
the same sprite recoloured pale. Look at the model with
`python3 tools/make_facing.py --model previews/facing-3d.png`; the sprites come from the same
model in `tools/make_facing.py`.

The first asset is the **turn crystal**: a Sims-style marker for whose turn it is,
hovering above the active character and turning as it bobs. It is rendered from a
small 3D model (a stretched octahedron, flat-shaded) by `tools/make_crystal.py`, so
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
`tools/make_crystal.py` (cell size, frames, size, tilt, bob) and run:

```bash
python3 tools/make_assets.py
```

Add `--png-dir sprites/assets` to also write each asset as a PNG sheet (frames left to right, then down; a see-through overlay carries its
opacity in the alpha) and a `manifest.json` beside them (size, columns and rows, frame rate, anchor, variant names, and which
overlay shape fits each ground tile), and check that each sheet re-reads identical. The ground tiles and the weapons are not written again, since they are already
the ground sheet and the weapon strips. To add another asset, add a renderer beside the crystal and the rock. An asset says
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
| `tools/make_pose_guide.py`, `tools/trace_guide.py` | Draw a character's poses and palette on one page, and trace such a page (even one redrawn by an image generator) back into sprite sheets |
| `tools/recolor.py` | Moves every sprite PNG to a new palette by swapping colours (see Colour in CONVENTIONS.md) |
| `tools/make_skeleton.py` | Paints the skeleton base on the cleric's poses |
| `tools/make_zombie.py` | Paints the zombie base on the fighter's poses |
| `tools/make_knight.py` | Paints the armoured knight base on the fighter's poses |

## Node map

Top-down tiles for a Slay-the-Spire-style floor map: branching islands with water between, and pins on the nodes. It is its own group: the **Node map**
category on the Assets page, ids `nodemap-*`, and the folder `sprites/assets/nodemap/`, which has a **README.md for the app that uses it** (how to pick
tiles, the layers, the layout recipe), a `nodemap.json` with the numbers, and an example map with its layout. Two skins (Grass islands and Parchment chart)
share the same 16 tiles; `tools/make_nodemap.py` is the generator and the reference for making a layout.

## Traps

Caltrops and a bear trap, each placed (one frame) and triggered (an animation that ends on the spent trap). Their own group: the **Traps** category on the Assets page, ids `trap-*`,
and the folder `sprites/assets/traps/`, which has a **README.md for the app that uses it** and a `traps.json` with the numbers. `tools/make_traps.py` is the generator.

## The corrupted ground

The grass and water ground sets again, rotted: teal and purple turf and soil, a murky water, mushrooms, vines, thorns and the odd pair of eyes. `sprites/assets/ground-corrupted.png` has the same cells as `ground.png`
(categories **Corrupted Grass / Dirt / Stone / Water / Nature**, ids `ground-corrupted-COL-ROW`). `tools/make_corrupted_ground.py` makes it from the original (`--preview` shows the two side by side). Three plain grass blocks with no mushrooms are at cells (4, 11), (5, 11) and (6, 11), for everyday grass.

## Treasure chests

Common, rare and legendary treasure chests that stand on one ground tile, each in NE and SE, shut and opening (an 8-frame animation that plays once and ends on the open chest). Category **Chests**, ids `chest-RARITY-ne`, `chest-RARITY-ne-open` and so on,
in the folder `sprites/assets/chests/` (its **README.md** says how to place and play them). They grow in size and richness with rarity. `tools/make_chest.py --preview previews/chests.png` shows them enlarged.

## The bazaar

The inside of a shop as a single 256 x 256 image (`bazaar-shop`, category **Buildings**, `sprites/assets/bazaar-shop.png`): a floating, cut-away room with the game's own weapons, amulets, crystals and rocks on its walls,
counter and tables, anchored on the middle of its floor. `tools/make_bazaar.py` is the generator (`--preview` for an enlarged look).

## Ability animations

Forty-six animations for the abilities (bursts, rings, pop-up and status icons, vanish and appear, ground loops), in the **Abilities** category, ids `burst-*`, `ring-*`, `icon-*`, `vanish-*`, `appear-*`, `surface-*`,
in the folder `sprites/assets/abilities/`. That folder's **README.md** says which ability plays which sheet, where to put it and how, and **`abilities.json`** is the same table for the game to read (both generated by
`tools/make_abilities.py`). The families are `tools/make_burst.py`, `make_ring.py`, `make_icons.py`, `make_vanish.py` and `make_ground_fx.py`, sharing `tools/fx.py`; each has `--preview`.

## Buildings

A kit of building tiles to build houses, towers and whole streets from: 33 pieces plus 36 worn, damaged and overgrown versions, each drawn twice (NE and SE), 32 x 32 like the ground tiles
(two spires are 32 x 48). They are one-cell, one-level pieces you stack and set side by side, in the **Buildings** category, ids `bld-*`, and the folder `sprites/assets/buildings/`, which has a
**README.md for the app that uses it** (placement, NE and SE, how to make walls, doors, roofs and towers), a `buildings.json` with every piece and the rules in numbers, and an example street with its piece list.
`tools/buildings.py` is the renderer and `tools/make_buildings.py` the kit and a `Town` helper that builds with it.

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

Eleven more melee weapons (dagger, stiletto, kris, bone dagger, greatsword, scimitar, battle axe, war hammer, spiked mace, spear and
crystal staff) are drawn by `tools/make_melee.py` along the same swing and written into that folder: `python3 tools/make_melee.py --out sprites/weapons`.
The bows are the one 3D bow model in several shapes (`tools/make_bow.py`: longbow, shortbow, recurve, elven), and the **Amulets** category holds eight
shop pendants (`tools/make_amulets.py`), images only. The amulets and every weapon's display icon are small 3D models, ray-cast with the creatures' renderer and finished with painted details (`tools/make_weapon_icons3d.py`), with the weapons, bows included, on the same 45 degree diagonal.

Every weapon also has a 32 x 32 **display icon** (category "Weapon icons", `tools/make_weapon_icons.py`), tied to it by name: the weapon's assets are
`weapon-NAME-ne` and `-se`, its icon is `icon-weapon-NAME`, and each side carries the other's id (`icon` on the weapon, `icon_for` on the icon). The
`ICONS` list there is the one place to add one, and the asset build fails if a weapon and its icon do not match.

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
