# Corrupted terrain: mycelium veins, shelf fungus, spore vents and thorn walls

30 pieces in category **Corrupted Terrain** (`tools/make_corrupted_terrain.py`), for the corrupted ground (`ground-corrupted`): veins of mycelium that run across it, bracket fungus a unit can climb, a vent that breathes spores and walls of thorns that can be cut down. All are palette roles only (mycelium: `u i e o`; the standing pieces use the fungal ramp with the one-pixel `O` outline). `corrupted-terrain.json` lists the numbers below.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**. **x runs SE, y runs SW.**
- **Anchor: the middle of the piece's bounding box on the ground** (for a flat tile, the middle of the cell's top face). A piece over several cells is **one sprite covering them**; `footprint.cells` are the cells `(i, j)` it stands on, counted from the back corner (the top of the diamond), `i` down-right and `j` down-left. **Draw order:** sort a multi-cell piece by its front-most cell (the largest `i + j`), after the ground.
- A standing piece is `16 * (fx + fy) + 24` wide (12 pixels of room each side for a cap that overhangs). Every standing piece has the one-pixel outline; the mycelium tiles are flat marks and have none.

## Mycelium: veins that join

16 flat decals, each **32 x 16**, one ground tile, anchored at **(16, 8)**, the middle of the cell's top face. Draw them **on the ground, under everything else** (the same layer as the blood pool), one per cell. They are `place: ground` stills with no outline.

**The join rule.** A vein leaves a tile by **the middle of an edge**, at **the same place and the same width every time**. So any two tiles that both have a vein on their shared edge join, with no gap and no step. The four edges are named by the screen direction they face, and the tile's open edges are the veins it has; the middle pixel of each edge is in `corrupted-terrain.json` (`mycelium.edges`):

| Edge | Middle of the edge, in the tile | The neighbour across it | That neighbour's matching edge |
|---|---|---|---|
| `ne` | (24, 4) | cell (x, y - 1) | `sw` |
| `se` | (24, 12) | cell (x + 1, y) | `nw` |
| `sw` | (8, 12) | cell (x, y + 1) | `ne` |
| `nw` | (8, 4) | cell (x - 1, y) | `se` |

**To lay a network:** decide which cells are vein, and for each cell pick the piece whose open edges are exactly the neighbours that are vein (the cell's own `decal.edges` in `assets/data.js`, or the table below). A cell with one vein neighbour takes an **end**, two opposite ones a **straight**, two next to each other a **corner**, three a **tee** (named for the edge that is closed: `tee-no-se` has no vein on its `se` edge), four the **cross**. A lone cell takes a **node**.

| File | Open edges | What |
|---|---|---|
| `mycelium-end-ne.png` | ne | an end (a dead end) |
| `mycelium-end-se.png` | se | an end (a dead end) |
| `mycelium-end-sw.png` | sw | an end (a dead end) |
| `mycelium-end-nw.png` | nw | an end (a dead end) |
| `mycelium-straight-ne-sw.png` | ne, sw | a straight or a corner |
| `mycelium-straight-nw-se.png` | nw, se | a straight or a corner |
| `mycelium-corner-ne-se.png` | ne, se | a straight or a corner |
| `mycelium-corner-se-sw.png` | se, sw | a straight or a corner |
| `mycelium-corner-sw-nw.png` | sw, nw | a straight or a corner |
| `mycelium-corner-nw-ne.png` | nw, ne | a straight or a corner |
| `mycelium-tee-no-ne.png` | se, sw, nw | a tee |
| `mycelium-tee-no-se.png` | ne, sw, nw | a tee |
| `mycelium-tee-no-sw.png` | ne, se, nw | a tee |
| `mycelium-tee-no-nw.png` | ne, se, sw | a tee |
| `mycelium-cross.png` | ne, se, sw, nw | a cross |
| `mycelium-node.png` | none | a fruiting node, no veins |

Twigs and glowing spots inside a tile differ from tile to tile, but the vein at an edge does not, so you can repeat a piece freely. The veins are thin and low in contrast on the teal ground; they read best in a run of several cells, and the node (a fruiting body) reads on its own.

## Shelf fungus: a flat top to climb

Bracket fungus with a **flat top at a whole level** that a unit can stand on, like the rock ledges. `walkable` is true when every cell has at least **0.6** flat top (`top_cover`, per cell `"i,j"`, from 0 to 1); all of these are 0.91 or more. `cell_levels` is the height of the top of each cell in levels (16 pixels each; the picture is drawn for 12 pixels of cap overhang). Treat each cell of a walkable piece as ground that high: a unit stands at the middle of the cell, `levels * 16` pixels up. The sides (the stem and gills) are cliff.

A **stepped** piece (`-step`) has one cell a level lower than the rest, **always the front-most cell**, so the way up is in view: a unit steps from the ground to the one-level cell and from that to the two-level top.

| File | Footprint | Levels | Per cell | Min flat top | Size | Anchor |
|---|---|---|---|---|---|---|
| `shelf-1x1-h1.png` | 1 x 1 | 1 | 0,0: 1 | 0.94 | 56 x 38 | (28, 30) |
| `shelf-1x1-h2.png` | 1 x 1 | 2 | 0,0: 2 | 0.94 | 56 x 54 | (28, 46) |
| `shelf-1x2-h1.png` | 1 x 2 | 1 | 0,0: 1, 0,1: 1 | 0.91 | 72 x 42 | (36, 34) |
| `shelf-2x1-h1.png` | 2 x 1 | 1 | 0,0: 1, 1,0: 1 | 0.97 | 72 x 42 | (36, 34) |
| `shelf-2x2-h1.png` | 2 x 2 | 1 | 0,0: 1, 0,1: 1, 1,0: 1, 1,1: 1 | 0.98 | 88 x 46 | (44, 38) |
| `shelf-1x2-h2-step.png` | 1 x 2 | 2 | 0,0: 2, 0,1: 1 | 0.94 | 72 x 58 | (36, 50) |
| `shelf-2x2-h2-step.png` | 2 x 2 | 2 | 0,0: 2, 0,1: 2, 1,0: 2, 1,1: 1 | 0.97 | 88 x 62 | (44, 54) |

## The spore vent

`spore-vent.png` is a **32 x 48** animation of **6 frames at 8 fps**, in a row in the sheet, anchored at **(16, 40)** (the middle of its tile on the ground). It **loops**: the puff rises and fades, and the last frame leads into the first. `vent` says `{"loops": true, "blocks": false}`: it does not block, so a unit can stand on the tile. What the vent *does* (a poison, a slow, a spawn) is the game's rule. Draw it on its tile in the ground layer, after the mycelium and before units.

## Thorn walls: blocks that can be cut down

Each wall is **two pictures of the same wall**: the **intact** wall, which **blocks** every cell of its footprint, and the **broken** one (cut stubs and litter), which **does not** block. Both are `destroyable: true`. When the wall is destroyed (cut down, burnt or blown up), swap the picture and stop blocking. The two have the same width and anchor x, so the swap needs no shift; the broken one is shorter.

| File | Footprint | Blocks | Destroyable | Size | Anchor |
|---|---|---|---|---|---|
| `thorn-wall-1x1.png` | 1 x 1 | yes | yes | 48 x 44 | (24, 36) |
| `thorn-wall-1x1-broken.png` | 1 x 1 | no | yes | 48 x 33 | (24, 25) |
| `thorn-wall-1x2.png` | 1 x 2 | yes | yes | 64 x 48 | (32, 40) |
| `thorn-wall-1x2-broken.png` | 1 x 2 | no | yes | 64 x 37 | (32, 29) |
| `thorn-wall-2x1.png` | 2 x 1 | yes | yes | 64 x 48 | (32, 40) |
| `thorn-wall-2x1-broken.png` | 2 x 1 | no | yes | 64 x 37 | (32, 29) |

## Things to know

- The pieces recolour with the rest of the art (palette roles only). They are made for the **corrupted** ground.
- Thorns are sparse (a few pink dots on a tangle of green), and the shelf fungus reads like a pink mushroom more than a layered bracket; the spore puff reads as smoke. They are first versions.
- There is **no outline** on the mycelium, and no walkable flag: they are marks on the ground.
