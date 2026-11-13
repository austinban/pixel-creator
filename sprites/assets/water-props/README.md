# Water props: docks, a rowboat, stepping stones, waterfalls, pads and reeds

25 pictures in category **Water props** (`tools/make_water_props.py`, shared renderer `tools/prop3d.py`), things that live on and beside the water, in the ground tiles' projection and palette, with a corrupted version of the docks, the waterfalls and the reeds. Each is one sprite covering its whole footprint. `water-props.json` lists every file with its footprint, whether it is walkable and how much of each cell is flat top.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**.
- **The drawing level: z = 0 in every picture is the surface of a water tile.** In the game the water sits **one height step** below the land (`BattleGrid.HEIGHT_STEP`, **8 pixels**, half a level), so the water's surface is 8 pixels under the neighbouring grass. Draw a water prop on the **water cell's top face** (the diamond of the water tile as drawn), not on the land.
- **Anchor: the middle of the footprint on that surface.** For a piece over several cells it is the middle of the bounding box; its x is always the picture's centre column. The anchor is in `assets/data.js` (`anchor`), and the pictures are `16 * (fx + fy)` plus a margin wide (8 to 18 pixels, more for the waterfall's spill, 32 for a decal).
- **Footprint:** `footprint.size` is [x cells, y cells] and `footprint.cells` the cells it stands on, counted `(i, j)` from the back corner (the top of the diamond), i running down-right and j down-left. Every piece here is a plain rectangle. Put the anchor on the ground point of the middle of those cells and draw; for a piece over many cells **sort it by its front-most cell** (the largest `i + j`) with the rest of the scenery.
- A `variants` or `animation` file is a **strip of frames side by side**, each exactly `w` x `h`, all with the same anchor: `stepping-1x1.png` is 150 x 38 (three variants), `waterfall-ne.png` is 360 x 38 (six frames).

## Walkable or not

The **docks and the stepping stones are walkable**: their flat top is **half a level (8 pixels, one game step) above the water's surface**, which is the height of the land beside the water, so a unit steps straight on from the shore with no ramp. `levels` is 0.5 on every walkable piece. `top_cover` gives, per cell `"i,j"`, the share of the cell's area (0 to 1) that is flat top: **0.75 for every dock cell, 0.77 to 0.80 for the stones**; a piece is only marked walkable when every cell has at least **0.6** (`walk_min`, the same rule as the rock kit). Treat each cell of a walkable piece as ground at the land's height (one step above the water). The sides are not walkable and a unit does not wade: the water around them is still water.

Everything else is **scenery**: the rowboat (its floor is half a level up and the deck is only dressing), the waterfalls (a one-cell cliff the water pours over, a level high), the pads and the reeds. None of these is walkable (`walkable: false`, no `top_cover`). Treat the waterfall as blocking its cell; the pads and the reeds are flat or tiny, so they are decor for a cell the map already says is water or shore (the records do not carry a `blocks` flag for this folder; that is the game's call).

## Pieces and files

| File | What | Footprint | Frames | Walkable |
|---|---|---|---|---|
| `dock-1x2.png`, `dock-2x1.png` | a plank pier on piles; 1 x 2 runs down-left, 2 x 1 down-right | 1 x 2, 2 x 1 | 1 | yes, 0.75 |
| `dock-1x3.png`, `dock-3x1.png` | the same, longer | 1 x 3, 3 x 1 | 1 | yes, 0.75 |
| `dock-*-corrupted.png` | a rotted pier grown over with mushrooms; same footprint and numbers | the same | 1 | yes, 0.75 |
| `rowboat-2x1.png`, `rowboat-1x2.png` | a rowboat moored at a post | 2 x 1, 1 x 2 | 1 | no |
| `stepping-1x1.png` | a flat-topped stone standing in the water, three variants A, B and C | 1 x 1 | 3 | yes, 0.80 |
| `stepping-2x1.png`, `stepping-1x2.png` | two stones in a row | 2 x 1, 1 x 2 | 1 | yes, 0.77 to 0.80 |
| `stepping-1x3.png`, `stepping-3x1.png` | three stones in a row | 1 x 3, 3 x 1 | 1 | yes, 0.77 to 0.80 |
| `waterfall-ne.png`, `waterfall-se.png` | a cliff cell that water pours over, facing NE or SE | 1 x 1 | 6 at 8 fps, loops | no |
| `waterfall-*-corrupted.png` | the same in the corrupted water's teal | 1 x 1 | 6 at 8 fps, loops | no |
| `lily-pads.png` | flat decals on the water: One, Two, Three and Cluster | 1 x 1 (32 x 16, anchor 16, 8) | 4 variants | no |
| `mushroom-pads.png` | the corrupted pads: One, Two, Three and Cluster | 1 x 1 (32 x 16, anchor 16, 8) | 4 variants | no |
| `reeds.png` | tufts for the shore: Tall, Thick and Short (32 x 32, anchor 16, 25) | 1 x 1 | 3 variants | no |
| `reeds-sway.png` | the reeds swaying, 4 frames at 4 fps, loops | 1 x 1 | 4 | no |
| `reeds-corrupted.png`, `reeds-corrupted-sway.png` | the same in the corrupted teal with magenta tips | 1 x 1 | 3, 4 | no |

## Using them

- **Docks:** lay one across a stretch of water from the shore, with the end that touches land on the cell beside the grass. The deck is the land's height, so a unit walks from the grass onto it. Pick the corrupted dock on a corrupted ground (and the plain one on a plain ground): the pair share every number, so one can replace the other in any map. Keep the cells of a dock (and any stepping stone) clear of other pieces.
- **Stepping stones** are a way across a pond that is one cell wide, or decoration in the shallows. Each stone is a cell and a full step; a row of three is three cells, not one.
- **Waterfalls** belong at the edge of a cliff where one water level meets another: place one on the cell beside the drop, facing the way the water goes, and play the strip at 8 fps in a loop. The water's own foam and ripples spill a little outside the 1 x 1 footprint (the picture is 60 wide), so draw it after the water tiles around it.
- **Pads and reeds** are decals. Draw lily pads on a water cell (mushroom pads on corrupted water) and reeds on a shore cell, where the land meets the water. Pick one of the variants at random per cell. The reeds sway 4 frames at 4 fps; leave the still `reeds` for cells that should not move.
- **Draw order:** all of these stand on the water or the shore, so draw them after the water and ground tiles and before units that stand in front of them.

## Things to know

- **The stepping stones are low stones, flush with the land:** half a level above the water, which is exactly the land beside it.
- The rowboat is blocky, with no oar, and its hull sides are dark. It is not walkable.
- The waterfall is one cell wide and small; its pool ripples spill outside its 1 x 1 footprint.
- The reeds are plain one-pixel stalks with no outline; the pads are small and flat.
- Everything is palette colours (roles only), so the pieces recolour with the rest of the art. The corrupted pieces use the corrupted water's teal (`s`, `D`, `q`) and mushrooms; the plain ones use the plain water's blues.
- The pieces are deterministic: the same code gives the same pictures every time.
