# Rocks: ledges, crags, slabs and stones on 1 x 1 to 3 x 1 and L footprints

62 rocks in category **Nature** (`tools/make_rocks.py`), drawn in the ground tiles' projection and the stone palette (steel, lavender, indigo, a little moss). Each is **one sprite that covers its whole footprint**, so a rock on 4 cells is a single picture, like the boss and the buildings. `rocks.json` lists every file with its footprint, height and whether it is walkable.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**.
- A rock's footprint is a set of **cells (i, j)** counted from its bounding box's back corner (the top of the diamond): i runs down-right, j down-left. `footprint.size` is [x cells, y cells] of the bounding box, `footprint.cells` the cells it really stands on (an L has 3 or 4 of a box of 4 or 6).
- **Anchor: the middle of the bounding box on the ground.** The picture is `16 * (fx + fy) + 12` wide, so a 1 x 1 is 44 wide, a 2 x 2 is 76, a 1 x 3 is 76, and the anchor's x is the picture's centre column; its y is the `anchor` in `assets/data.js`.
- To place a rock with its back-corner cell at the map cell `(cx, cy)`: the bounding box's middle is the ground point of the cell `(cx + fx / 2, cy + fy / 2)`; put the anchor on it and draw. **Draw order:** a rock covers several cells, so sort it by its **front-most cell** (the largest `i + j`) with the rest of the scenery, and draw it after the ground.

## Walkable or not

`walkable` is **true** when the rock has a **flat top** at a whole level (1 or 2 levels = 16 or 32 pixels above the ground) over every one of its cells. `top_cover` gives, per cell `"i,j"`, the share of the cell's area (0 to 1) that is flat top; a rock is only marked walkable when **every cell is at least 0.6** (`walk_min`). Treat each cell of a walkable rock as a ground cell at height `levels`: a unit stands at the middle of the cell, `levels * 16` pixels up. The sides are cliff: not walkable.

Crags and stones are **never** walkable: they are scenery that blocks, so treat every cell of their footprint as blocked.

## The rocks

| File | What | Footprint | Style | Levels (tallest) | Walkable |
|---|---|---|---|---|---|
| `rock-ledge-1x1-h1.png` | Rock ledge 1 x 1, 1 high | 1 x 1 (1 cells) | block | 1 | yes |
| `rock-ledge-1x2-h1.png` | Rock ledge 1 x 2, 1 high | 1 x 2 (2 cells) | block | 1 | yes |
| `rock-ledge-2x1-h1.png` | Rock ledge 2 x 1, 1 high | 2 x 1 (2 cells) | block | 1 | yes |
| `rock-ledge-2x2-h1.png` | Rock ledge 2 x 2, 1 high | 2 x 2 (4 cells) | block | 1 | yes |
| `rock-ledge-1x1-h2.png` | Rock ledge 1 x 1, 2 high | 1 x 1 (1 cells) | block | 2 | yes |
| `rock-ledge-1x2-h2.png` | Rock ledge 1 x 2, 2 high | 1 x 2 (2 cells) | block | 2 | yes |
| `rock-ledge-2x1-h2.png` | Rock ledge 2 x 1, 2 high | 2 x 1 (2 cells) | block | 2 | yes |
| `rock-ledge-2x2-h2.png` | Rock ledge 2 x 2, 2 high | 2 x 2 (4 cells) | block | 2 | yes |
| `rock-ledge-1x3-h1.png` | Rock ledge 1 x 3, 1 high | 1 x 3 (3 cells) | block | 1 | yes |
| `rock-ledge-3x1-h1.png` | Rock ledge 3 x 1, 1 high | 3 x 1 (3 cells) | block | 1 | yes |
| `rock-ledge-1x3-h2.png` | Rock ledge 1 x 3, 2 high | 1 x 3 (3 cells) | block | 2 | yes |
| `rock-ledge-3x1-h2.png` | Rock ledge 3 x 1, 2 high | 3 x 1 (3 cells) | block | 2 | yes |
| `rock-ledge-l-n-h1.png` | Rock ledge, L (empty n), 1 high | 2 x 2 (3 cells) | block | 1 | yes |
| `rock-ledge-l-e-h1.png` | Rock ledge, L (empty e), 1 high | 2 x 2 (3 cells) | block | 1 | yes |
| `rock-ledge-l-s-h1.png` | Rock ledge, L (empty s), 1 high | 2 x 2 (3 cells) | block | 1 | yes |
| `rock-ledge-l-w-h1.png` | Rock ledge, L (empty w), 1 high | 2 x 2 (3 cells) | block | 1 | yes |
| `rock-ledge-l-n-h2.png` | Rock ledge, L (empty n), 2 high | 2 x 2 (3 cells) | block | 2 | yes |
| `rock-ledge-l-e-h2.png` | Rock ledge, L (empty e), 2 high | 2 x 2 (3 cells) | block | 2 | yes |
| `rock-ledge-l-s-h2.png` | Rock ledge, L (empty s), 2 high | 2 x 2 (3 cells) | block | 2 | yes |
| `rock-ledge-l-w-h2.png` | Rock ledge, L (empty w), 2 high | 2 x 2 (3 cells) | block | 2 | yes |
| `rock-ledge-l4-0-h1.png` | Rock ledge, long L (turn 0), 1 high | 2 x 3 (4 cells) | block | 1 | yes |
| `rock-ledge-l4-1-h1.png` | Rock ledge, long L (turn 1), 1 high | 3 x 2 (4 cells) | block | 1 | yes |
| `rock-ledge-l4-2-h1.png` | Rock ledge, long L (turn 2), 1 high | 2 x 3 (4 cells) | block | 1 | yes |
| `rock-ledge-l4-3-h1.png` | Rock ledge, long L (turn 3), 1 high | 3 x 2 (4 cells) | block | 1 | yes |
| `rock-crag-1x1-a.png` | Boulder | 1 x 1 (1 cells) | block | 0.75 | no |
| `rock-crag-1x1-b.png` | Crag | 1 x 1 (1 cells) | block | 1.7 | no |
| `rock-crag-1x1-c.png` | Tall crag | 1 x 1 (1 cells) | block | 2.6 | no |
| `rock-crag-1x2.png` | Crag ridge 1 x 2 | 1 x 2 (2 cells) | block | 2.2 | no |
| `rock-crag-2x1.png` | Crag ridge 2 x 1 | 2 x 1 (2 cells) | block | 2.2 | no |
| `rock-crag-2x2.png` | Massif 2 x 2 | 2 x 2 (4 cells) | block | 3.2 | no |
| `rock-crag-1x3.png` | Long ridge 1 x 3 | 1 x 3 (3 cells) | block | 1.9 | no |
| `rock-crag-3x1.png` | Long ridge 3 x 1 | 3 x 1 (3 cells) | block | 1.9 | no |
| `rock-crag-l-n.png` | Scree, L (empty n) | 2 x 2 (3 cells) | block | 1.5 | no |
| `rock-crag-l-e.png` | Scree, L (empty e) | 2 x 2 (3 cells) | block | 1.5 | no |
| `rock-crag-l-s.png` | Scree, L (empty s) | 2 x 2 (3 cells) | block | 1.5 | no |
| `rock-crag-l-w.png` | Scree, L (empty w) | 2 x 2 (3 cells) | block | 1.5 | no |
| `rock-slab-1x1-h1.png` | Worn slab 1 x 1, 1 high | 1 x 1 (1 cells) | natural | 1 | yes |
| `rock-slab-1x2-h1.png` | Worn slab 1 x 2, 1 high | 1 x 2 (2 cells) | natural | 1 | yes |
| `rock-slab-2x1-h1.png` | Worn slab 2 x 1, 1 high | 2 x 1 (2 cells) | natural | 1 | yes |
| `rock-slab-2x2-h1.png` | Worn slab 2 x 2, 1 high | 2 x 2 (4 cells) | natural | 1 | yes |
| `rock-slab-1x1-h2.png` | Worn slab 1 x 1, 2 high | 1 x 1 (1 cells) | natural | 2 | yes |
| `rock-slab-1x2-h2.png` | Worn slab 1 x 2, 2 high | 1 x 2 (2 cells) | natural | 2 | yes |
| `rock-slab-2x1-h2.png` | Worn slab 2 x 1, 2 high | 2 x 1 (2 cells) | natural | 2 | yes |
| `rock-slab-2x2-h2.png` | Worn slab 2 x 2, 2 high | 2 x 2 (4 cells) | natural | 2 | yes |
| `rock-slab-1x3-h1.png` | Worn slab 1 x 3, 1 high | 1 x 3 (3 cells) | natural | 1 | yes |
| `rock-slab-3x1-h1.png` | Worn slab 3 x 1, 1 high | 3 x 1 (3 cells) | natural | 1 | yes |
| `rock-slab-l-n-h1.png` | Worn slab, L (empty n), 1 high | 2 x 2 (3 cells) | natural | 1 | yes |
| `rock-slab-l-e-h1.png` | Worn slab, L (empty e), 1 high | 2 x 2 (3 cells) | natural | 1 | yes |
| `rock-slab-l-s-h1.png` | Worn slab, L (empty s), 1 high | 2 x 2 (3 cells) | natural | 1 | yes |
| `rock-slab-l-w-h1.png` | Worn slab, L (empty w), 1 high | 2 x 2 (3 cells) | natural | 1 | yes |
| `rock-stone-boulder.png` | Boulder | 1 x 1 (1 cells) | natural | 0.8 | no |
| `rock-stone-round.png` | Round stone | 1 x 1 (1 cells) | natural | 1.3 | no |
| `rock-stone-standing.png` | Standing stone | 1 x 1 (1 cells) | natural | 2.5 | no |
| `rock-stone-pair-1x2.png` | Stone pair 1 x 2 | 1 x 2 (2 cells) | natural | 1.4 | no |
| `rock-stone-pair-2x1.png` | Stone pair 2 x 1 | 2 x 1 (2 cells) | natural | 1.4 | no |
| `rock-stone-cluster.png` | Stone cluster 2 x 2 | 2 x 2 (4 cells) | natural | 2.0 | no |
| `rock-stone-outcrop-1x3.png` | Outcrop 1 x 3 | 1 x 3 (3 cells) | natural | 1.6 | no |
| `rock-stone-outcrop-3x1.png` | Outcrop 3 x 1 | 3 x 1 (3 cells) | natural | 1.6 | no |
| `rock-stone-scree-n.png` | Scree, L (empty n) | 2 x 2 (3 cells) | natural | 1.2 | no |
| `rock-stone-scree-e.png` | Scree, L (empty e) | 2 x 2 (3 cells) | natural | 1.2 | no |
| `rock-stone-scree-s.png` | Scree, L (empty s) | 2 x 2 (3 cells) | natural | 1.2 | no |
| `rock-stone-scree-w.png` | Scree, L (empty w) | 2 x 2 (3 cells) | natural | 1.2 | no |

**Kinds:** `ledge-*` and `slab-*` have flat tops; `crag-*` and `stone-*` do not. `block` style is straight faces with courses of stone; `natural` is worn, faceted stone that is widest at the ground and never undercuts. **L shapes** are named for the corner of their 2 x 2 box that is empty: `n` is the back corner of the diamond, `e` the right, `s` the front, `w` the left; the long L (`l4-0` to `l4-3`) is an arm of three cells with a foot of one, in four turns. The L has no mirror image.

## Things to know

- Rocks have **no front**: one picture each, NE / SE do not apply.
- Everything is palette colours (`r q p l k w` for the stone, `z A B` for moss, `O` for the outline), so a rock recolours with the rest of the art. The outline is on the outside only.
- The older `rock` asset (the 32 x 32 barrier) is unchanged.
