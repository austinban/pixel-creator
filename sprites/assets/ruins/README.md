# Ruins: broken walls, arches, rubble and foundations

61 pieces in category **Ruins** (`tools/make_ruins.py`), drawn in the ground tiles' projection and the stone palette (steel, lavender, indigo), for the town sets that have gone wrong and for any corrupted map that needs something to hide behind. Each is **one sprite that covers its whole footprint**, like the rocks (`../rocks/`), the boss and the buildings. `ruins.json` lists every file with its footprint, height, cover and whether it is walkable.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**.
- A piece's footprint is a set of **cells (i, j)** counted from its bounding box's back corner (the top of the diamond): i runs down-right, j down-left. `footprint.size` is [x cells, y cells] of the bounding box, `footprint.cells` the cells it really stands on (an L has 3 of a box of 4).
- **Anchor: the middle of the bounding box on the ground.** The picture is `16 * (fx + fy) + 12` wide, so a 1 x 1 is 44 wide, a 1 x 2 or 2 x 1 is 60, a 2 x 2 is 76. The anchor's x is the picture's centre column; its y is the `anchor` in `assets/data.js`.
- To place a piece with its back-corner cell at the map cell `(cx, cy)`: the bounding box's middle is the ground point of the cell `(cx + fx / 2, cy + fy / 2)`; put the anchor on it and draw. **Draw order:** sort a piece by its **front-most cell** (the largest `i + j`) with the rest of the scenery, and draw it after the ground.
- Every piece is **outlined on its outside**. Moss and leaves on the overgrown pieces may sit over the outline.

## What each kind is

| Kind | Pieces | Walkable | `cover` |
|---|---|---|---|
| `wall` | broken walls along x and along y at 0.5, 1 and 2 levels (1 x 1), and long walls 2 x 1 and 1 x 2 at 1 and 2 | no | low, high or full by height |
| `corner` | two walls meeting, four turns (`se-sw`, `se-ne`, `nw-sw`, `nw-ne`), 1 and 2 levels | no | high or full |
| `tee` | a wall with a stub, four directions, 1 level | no | high |
| `arch` | a standing arch along x or along y | no | full |
| `heap` | rubble: 1 x 1, 1 x 2, 2 x 1, 2 x 2 and four L (`n`, `e`, `s`, `w`) | no | low |
| `floor` | a bare foundation: 1 x 1, 1 x 2, 2 x 1, 2 x 2 and four L, a few flags missing | **yes, at half a level** | - |

21 of the pieces have an **overgrown** twin with the id `<base>-grown` (`ruin-wall-x-h1-grown`...): vines, moss and small mushrooms, for the corrupted maps. They are the 1- and 2-level walls, the 2-level corners, two tees, both arches, three heaps and four floors. A twin has **exactly the same footprint, kind, cover and walkability** as its base (the tests check it), so the game can swap one for the other by id; it is a little taller, by up to about 0.2 level of vine and mushroom on top.

**L shapes** are named for the corner of their 2 x 2 box that is empty: `n` is the back corner of the diamond, `e` the right, `s` the front, `w` the left. The L has no mirror image.

## Sight and blocking: the `cover` field

Every piece that is not walkable has `cover`, which says how tall a blocker it is. The right-hand column is a **suggestion** for the game's own rules, not something this repo enforces:

| `cover` | Heights | Treat it as |
|---|---|---|
| `low` | under 1 level (a 0.5 wall, any heap) | **half cover**: it blocks movement through its cells, but a unit behind it can be seen over it and shot over it. Does not block line of sight. |
| `high` | 1 level up to under 1.75 (the 1-level walls, corners and tees) | **cover**: blocks movement, and blocks line of sight for a target behind it at the same ground level; a taller unit or one on higher ground sees over it. |
| `full` | 1.75 levels and up (the 2-level walls and corners, the arches) | **full blocker**: blocks movement and line of sight (this is the same as a tree or a rock crag). |

**Every cell of a non-walkable piece's footprint is blocked for walking**, an L's empty corner excepted. The game already knows its own sight heights (`Sight`): map `levels` to it, or use `cover` as the simple answer. A **floor** is not a blocker: it is a footing, not a wall.

## Walkable floors

`floor-*` pieces are **walkable at half a level**: `cell_levels` is 0.5 for each cell (the rock kit's ledges are whole levels; this is a deliberate exception, a foundation you step up onto). `top_cover` is the share of each cell that is flat footing (0.70 to 1.00); a piece is `walkable` only when **every cell is at least 0.6** (`walk_min`), and the tests enforce that. Treat a floor cell as ground half a level up (8 pixels).

## The pieces

| File | What | Footprint (cells) | Picture | Levels | Walkable | Top level | Cover |
|---|---|---|---|---|---|---|---|
| `ruin-wall-x-h05.png` | Broken wall along x, 0.5 high | 1 x 1 (1) | 44 x 30 | 0.5 | no | - | low |
| `ruin-wall-y-h05.png` | Broken wall along y, 0.5 high | 1 x 1 (1) | 44 x 30 | 0.5 | no | - | low |
| `ruin-wall-x-h1.png` | Broken wall along x, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-wall-y-h1.png` | Broken wall along y, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-wall-x-h2.png` | Broken wall along x, 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-wall-y-h2.png` | Broken wall along y, 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-wall-2x1-h1.png` | Long broken wall 2 x 1, 1 high | 2 x 1 (2) | 60 x 46 | 1 | no | - | high |
| `ruin-wall-1x2-h1.png` | Long broken wall 1 x 2, 1 high | 1 x 2 (2) | 60 x 46 | 1 | no | - | high |
| `ruin-wall-2x1-h2.png` | Long broken wall 2 x 1, 2 high | 2 x 1 (2) | 60 x 62 | 2 | no | - | full |
| `ruin-wall-1x2-h2.png` | Long broken wall 1 x 2, 2 high | 1 x 2 (2) | 60 x 62 | 2 | no | - | full |
| `ruin-corner-se-sw-h1.png` | Broken corner (se-sw), 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-corner-se-ne-h1.png` | Broken corner (se-ne), 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-corner-nw-sw-h1.png` | Broken corner (nw-sw), 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-corner-nw-ne-h1.png` | Broken corner (nw-ne), 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-corner-se-sw-h2.png` | Broken corner (se-sw), 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-corner-se-ne-h2.png` | Broken corner (se-ne), 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-corner-nw-sw-h2.png` | Broken corner (nw-sw), 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-corner-nw-ne-h2.png` | Broken corner (nw-ne), 2 high | 1 x 1 (1) | 44 x 54 | 2 | no | - | full |
| `ruin-tee-se-h1.png` | Broken tee, stub se, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-tee-sw-h1.png` | Broken tee, stub sw, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-tee-nw-h1.png` | Broken tee, stub nw, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-tee-ne-h1.png` | Broken tee, stub ne, 1 high | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `ruin-arch-x.png` | Broken arch, wall along x | 1 x 1 (1) | 44 x 50 | 1.75 | no | - | full |
| `ruin-arch-y.png` | Broken arch, wall along y | 1 x 1 (1) | 44 x 50 | 1.75 | no | - | full |
| `ruin-heap-1x1.png` | Heap of fallen stone 1x1 | 1 x 1 (1) | 44 x 31 | 0.56 | no | - | low |
| `ruin-heap-1x2.png` | Heap of fallen stone 1x2 | 1 x 2 (2) | 60 x 40 | 0.62 | no | - | low |
| `ruin-heap-2x1.png` | Heap of fallen stone 2x1 | 2 x 1 (2) | 60 x 39 | 0.56 | no | - | low |
| `ruin-heap-2x2.png` | Heap of fallen stone 2x2 | 2 x 2 (4) | 76 x 50 | 0.75 | no | - | low |
| `ruin-heap-l-n.png` | Heap of fallen stone l-n | 2 x 2 (3) | 76 x 49 | 0.69 | no | - | low |
| `ruin-heap-l-e.png` | Heap of fallen stone l-e | 2 x 2 (3) | 76 x 48 | 0.62 | no | - | low |
| `ruin-heap-l-s.png` | Heap of fallen stone l-s | 2 x 2 (3) | 76 x 47 | 0.56 | no | - | low |
| `ruin-heap-l-w.png` | Heap of fallen stone l-w | 2 x 2 (3) | 76 x 48 | 0.62 | no | - | low |
| `ruin-floor-1x1.png` | Foundation floor 1x1 | 1 x 1 (1) | 44 x 30 | 0.5 | yes | 0.5 | - |
| `ruin-floor-1x2.png` | Foundation floor 1x2 | 1 x 2 (2) | 60 x 42 | 0.72 | yes | 0.5 | - |
| `ruin-floor-2x1.png` | Foundation floor 2x1 | 2 x 1 (2) | 60 x 42 | 0.72 | yes | 0.5 | - |
| `ruin-floor-2x2.png` | Foundation floor 2x2 | 2 x 2 (4) | 76 x 50 | 0.72 | yes | 0.5 | - |
| `ruin-floor-l-n.png` | Foundation floor l-n | 2 x 2 (3) | 76 x 46 | 0.5 | yes | 0.5 | - |
| `ruin-floor-l-e.png` | Foundation floor l-e | 2 x 2 (3) | 76 x 50 | 0.72 | yes | 0.5 | - |
| `ruin-floor-l-s.png` | Foundation floor l-s | 2 x 2 (3) | 76 x 50 | 0.72 | yes | 0.5 | - |
| `ruin-floor-l-w.png` | Foundation floor l-w | 2 x 2 (3) | 76 x 50 | 0.72 | yes | 0.5 | - |
| `ruin-wall-x-h2-grown.png` | Broken wall along x, 2 high, overgrown | 1 x 1 (1) | 44 x 56 | 2.11 | no | - | full |
| `ruin-wall-y-h2-grown.png` | Broken wall along y, 2 high, overgrown | 1 x 1 (1) | 44 x 57 | 2.17 | no | - | full |
| `ruin-wall-x-h1-grown.png` | Broken wall along x, 1 high, overgrown | 1 x 1 (1) | 44 x 40 | 1.11 | no | - | high |
| `ruin-wall-y-h1-grown.png` | Broken wall along y, 1 high, overgrown | 1 x 1 (1) | 44 x 40 | 1.11 | no | - | high |
| `ruin-wall-2x1-h2-grown.png` | Long broken wall 2 x 1, 2 high, overgrown | 2 x 1 (2) | 60 x 64 | 2.11 | no | - | full |
| `ruin-wall-1x2-h2-grown.png` | Long broken wall 1 x 2, 2 high, overgrown | 1 x 2 (2) | 60 x 64 | 2.11 | no | - | full |
| `ruin-corner-se-sw-h2-grown.png` | Broken corner (se-sw), 2 high, overgrown | 1 x 1 (1) | 44 x 56 | 2.11 | no | - | full |
| `ruin-corner-se-ne-h2-grown.png` | Broken corner (se-ne), 2 high, overgrown | 1 x 1 (1) | 44 x 56 | 2.11 | no | - | full |
| `ruin-corner-nw-sw-h2-grown.png` | Broken corner (nw-sw), 2 high, overgrown | 1 x 1 (1) | 44 x 57 | 2.17 | no | - | full |
| `ruin-corner-nw-ne-h2-grown.png` | Broken corner (nw-ne), 2 high, overgrown | 1 x 1 (1) | 44 x 57 | 2.17 | no | - | full |
| `ruin-tee-se-h1-grown.png` | Broken tee, stub se, 1 high, overgrown | 1 x 1 (1) | 44 x 41 | 1.18 | no | - | high |
| `ruin-tee-sw-h1-grown.png` | Broken tee, stub sw, 1 high, overgrown | 1 x 1 (1) | 44 x 41 | 1.18 | no | - | high |
| `ruin-arch-x-grown.png` | Broken arch, wall along x, overgrown | 1 x 1 (1) | 44 x 52 | 1.86 | no | - | full |
| `ruin-arch-y-grown.png` | Broken arch, wall along y, overgrown | 1 x 1 (1) | 44 x 52 | 1.86 | no | - | full |
| `ruin-heap-1x1-grown.png` | Heap of fallen stone 1x1, overgrown | 1 x 1 (1) | 44 x 35 | 0.8 | no | - | low |
| `ruin-heap-2x2-grown.png` | Heap of fallen stone 2x2, overgrown | 2 x 2 (4) | 76 x 51 | 0.8 | no | - | low |
| `ruin-heap-1x2-grown.png` | Heap of fallen stone 1x2, overgrown | 1 x 2 (2) | 60 x 44 | 0.86 | no | - | low |
| `ruin-floor-2x2-grown.png` | Foundation floor 2x2, overgrown | 2 x 2 (4) | 76 x 53 | 0.9 | yes | 0.5 | - |
| `ruin-floor-1x1-grown.png` | Foundation floor 1x1, overgrown | 1 x 1 (1) | 44 x 34 | 0.72 | yes | 0.5 | - |
| `ruin-floor-2x1-grown.png` | Foundation floor 2x1, overgrown | 2 x 1 (2) | 60 x 44 | 0.83 | yes | 0.5 | - |
| `ruin-floor-l-n-grown.png` | Foundation floor l-n, overgrown | 2 x 2 (3) | 76 x 53 | 0.9 | yes | 0.5 | - |

## Things to know

- Pieces have **no front**: one picture each, NE / SE do not apply. Walls and arches come as an `x` and a `y` picture instead (`x` runs down-right, `y` down-left); a corner or tee names the two or three directions it opens (`se`, `sw`, `ne`, `nw`).
- **The arches barely read as openings** from this angle; they look like two piers with a notch. A unit does not walk through one: treat the arch cell as blocked.
- **Thin walls:** the half-thick walls at 2 levels look like pillars. They are meant to be seen in runs of several cells.
- **Mushrooms on the overgrown pieces** are 2 to 4 pixels wide and may disappear at the game's scale.
- Everything is palette colours, so a ruin recolours with the rest of the art.
