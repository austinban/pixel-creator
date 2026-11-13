# Low structures: haybales, crate piles, stalls, sheds, carts and wagons

32 pieces in category **Low structures** (`tools/make_lowstructures.py`): things a unit can **climb onto and walk across** one or two levels up, and a few that give cover. Drawn in the ground tiles' projection like the rocks (`../rocks/`) and the ruins (`../ruins/`): **one sprite that covers its whole footprint**, anchored at the middle of its bounding box on the ground. `low-structures.json` lists every file with its footprint, the level of each cell and whether it is walkable.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**.
- A piece's footprint is a set of **cells (i, j)** counted from its bounding box's back corner (the top of the diamond): i runs down-right, j down-left. `footprint.size` is [x cells, y cells], `footprint.cells` the cells it stands on.
- **Anchor: the middle of the bounding box on the ground.** The picture is `16 * (fx + fy) + 12` wide, so a 1 x 1 is 44, a 1 x 2 or 2 x 1 is 60, a 2 x 2 or 3 x 1 is 76. The anchor's x is the picture's centre column; its y is the `anchor` in `assets/data.js`.
- To place a piece with its back-corner cell at the map cell `(cx, cy)`: put the anchor on the ground point of the cell `(cx + fx / 2, cy + fy / 2)` and draw. **Draw order:** sort a piece by its **front-most cell** (the largest `i + j`) and draw it after the ground.
- Every piece is **outlined on its outside**.

## Walkable: `cell_levels` and `top_cover`

`walkable` is **true** when the piece has a **flat top at a whole level** over every one of its cells. `cell_levels` gives the level of each cell `"i,j"` (**1 = 16 pixels up, 2 = 32 pixels**), and `top_cover` the share of the cell's area (0 to 1) that is flat top; a piece is marked walkable only when **every cell is at least 0.6** (`walk_min`). Treat each cell of a walkable piece as a ground cell at its own level: a unit stands at the middle of the cell, `level * 16` pixels up.

**Stepped stacks** (`*-stepped`) have a **tall cell (level 2) at the back and lower cells (level 1) in front**: a unit climbs from the ground onto a 1-level cell, then onto the 2-level one. The tall cell is always at the back (toward -x and -y), because a tall cell in front would hide the lower one and its flat top. Whether a unit can step up one level at a time, and how far it can drop, is the game's own rule; the stack is built so a one-level step gets a unit from the ground to the top.

The load on a **cart or wagon** is flat enough to stand on (75 percent flat top), at level 1.

## The pieces

| File | What | Footprint (cells) | Picture | Levels | Walkable | Top level | Cover |
|---|---|---|---|---|---|---|---|
| `low-hay-1x1-h1.png` | Haybale stack 1 x 1, 1 high | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-hay-1x1-h2.png` | Haybale stack 1 x 1, 2 high | 1 x 1 (1) | 44 x 54 | 2 | yes | 2 | - |
| `low-hay-1x2-h1.png` | Haybale stack 1 x 2, 1 high | 1 x 2 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-hay-2x1-h1.png` | Haybale stack 2 x 1, 1 high | 2 x 1 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-hay-2x2-h1.png` | Haybale stack 2 x 2, 1 high | 2 x 2 (4) | 76 x 54 | 1 | yes | 1 | - |
| `low-hay-2x2-stepped.png` | Haybale stack 2 x 2, stepped | 2 x 2 (4) | 76 x 70 | 2 | yes | 1/2 | - |
| `low-hay-2x1-stepped.png` | Haybale stack 2 x 1, stepped | 2 x 1 (2) | 60 x 62 | 2 | yes | 1/2 | - |
| `low-hay-1x2-stepped.png` | Haybale stack 1 x 2, stepped | 1 x 2 (2) | 60 x 62 | 2 | yes | 1/2 | - |
| `low-hay-3x1-stepped.png` | Haybale stack 3 x 1, stepped | 3 x 1 (3) | 76 x 70 | 2 | yes | 1/2 | - |
| `low-crates-1x1-h1.png` | Crate pile 1 x 1, 1 high | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-crates-1x1-h2.png` | Crate pile 1 x 1, 2 high | 1 x 1 (1) | 44 x 54 | 2 | yes | 2 | - |
| `low-crates-2x1-stepped.png` | Crate pile 2 x 1, stepped | 2 x 1 (2) | 60 x 62 | 2 | yes | 1/2 | - |
| `low-crates-1x2-stepped.png` | Crate pile 1 x 2, stepped | 1 x 2 (2) | 60 x 62 | 2 | yes | 1/2 | - |
| `low-crates-2x2-stepped.png` | Crate pile 2 x 2, stepped | 2 x 2 (4) | 76 x 70 | 2 | yes | 1/2 | - |
| `low-crates-l-stepped.png` | Crate pile, L, stepped | 2 x 2 (3) | 76 x 70 | 2 | yes | 1/2 | - |
| `low-stall-1x1.png` | Market stall 1 x 1, canvas roof (walkable) | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-stall-1x1-cool.png` | Market stall 1 x 1, teal canvas roof (walkable) | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-stall-2x1.png` | Market stall 2 x 1, canvas roof (walkable) | 2 x 1 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-stall-1x2.png` | Market stall 1 x 2, canvas roof (walkable) | 1 x 2 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-stall-slope-1x1.png` | Market stall 1 x 1, sloping awning | 1 x 1 (1) | 44 x 38 | 1 | no | - | high |
| `low-stall-slope-2x1.png` | Market stall 2 x 1, sloping awning | 2 x 1 (2) | 60 x 46 | 1 | no | - | high |
| `low-shed-1x1-h1-se.png` | Shed 1 x 1, 1 high, open to the SE | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-shed-1x1-h1-sw.png` | Shed 1 x 1, 1 high, open to the SW | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-shed-1x1-h2-se.png` | Shed 1 x 1, 2 high, open to the SE | 1 x 1 (1) | 44 x 54 | 2 | yes | 2 | - |
| `low-shed-1x1-h2-sw.png` | Shed 1 x 1, 2 high, open to the SW | 1 x 1 (1) | 44 x 54 | 2 | yes | 2 | - |
| `low-shed-2x1-h1-sw.png` | Shed 2 x 1, 1 high, open to the SW | 2 x 1 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-shed-1x2-h1-se.png` | Shed 1 x 2, 1 high, open to the SE | 1 x 2 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-cart-hay.png` | Hay cart (along SE) | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-cart-crates.png` | Crate cart (along SW) | 1 x 1 (1) | 44 x 38 | 1 | yes | 1 | - |
| `low-wagon-2x1-hay.png` | Hay wagon 2 x 1 | 2 x 1 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-wagon-2x1-crates.png` | Crate wagon 2 x 1 | 2 x 1 (2) | 60 x 46 | 1 | yes | 1 | - |
| `low-wagon-1x2-hay.png` | Hay wagon 1 x 2 | 1 x 2 (2) | 60 x 46 | 1 | yes | 1 | - |

`hay` and `crates` are plain stacks (one level over every cell: `-h1` or `-h2` for a single cell, or `2x1`, `1x2`, `2x2` at level 1) and stepped ones. `stall-*` are market stalls with a flat canvas roof at level 1 (the roof is the walkable top); `stall-slope-*` have a **sloping awning** instead: not walkable, `cover: high`. `shed-*` are sheds with a flat plank roof and **one open alcove**, opening to the `se` or `sw`, at 1 or 2 levels. `cart-*` and `wagon-*` are loaded to a flat top.

## Cover and alcoves

- **Not walkable (`cover: high`)**: the two sloping stalls. Block their cells for walking and treat them like a 1-level wall for sight.
- **Alcoves:** a shed's open side is picture only. Whether a unit standing in that cell is covered, and from which direction, is the game's rule; the alcove opens to the `se` or `sw` (the end of the id) and the cell it is in is the shed's own footprint cell.
- **Roofs hide units.** The roof of a stall or shed is the walkable top, so a unit **on** it stands on top of a 1 or 2 level piece. A unit **in** an alcove or **under** an awning is hidden from the front by the roof, because the roof is drawn over it. The game's depth handling has to account for this: sort by the front-most cell as above, and draw a unit that is in or on a piece at that cell's ground point lifted by `level * 16` pixels, so the unit is sorted with its cell and not with the roof's front edge.

## Things to know

- Pieces have **no front**: one picture each, NE / SE do not apply, except the sheds, which come with the opening pointed `se` or `sw` (and the `2x1` shed only `sw`, the `1x2` shed only `se`).
- **The sheds and wagons look dark and plum**, and the crate and keg wood colours are guesses; the pieces do not match the ground sheet's own crates (`../ground.png`) exactly. Say if you want them brought closer.
- **A stall's interior is hidden by its roof** in this view: a unit under the awning cannot be seen from the front.
- Everything is palette colours, so a piece recolours with the rest of the art.
