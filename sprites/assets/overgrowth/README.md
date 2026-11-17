# Overgrowth map

Tiles, pieces and flowers for a floor-choosing map, like Slay the Spire's, set in a purple void: floating mossy islands joined by vine bridges, and a **flower on every node**. It has no
water and no roads. It is the second look for the same job as the water-and-islands `nodemap-*` set, and does not replace it. Everything here shares the `overgrowth-` prefix, and on the Assets page it
is the **Overgrowth map** category. `tools/make_overgrowth.py` makes it, and is also the **floor generator**.

| File | What it is |
|---|---|
| `overgrowth-ground.png` | 16 x 5 tiles of 16 x 16: column = corner bits (0 is empty), row = cliff style 0-4 |
| `overgrowth-full.png` | 6 variants of the all-land tile (bits 15), with something in the middle |
| `overgrowth-spill.png` | The same grid: the rest of a cliff that ran past the bottom of its tile (drawn **under** the ground layer) |
| `overgrowth-void.png` | The void: 256 x 256, seamless, repeated across the whole map |
| `overgrowth-tone-patch.png`, `-moss-patch.png`, `-mushroom-*.png`, `-crystal-*.png`, `-rock.png`, `-fern.png`, `-bush.png`, `-tendril.png`, `-wisp.png`, `-vine-hang.png`, `-moss-drape.png` | Loose pieces to lay over the ground (each sheet's cell size and anchor are in `manifest.json` and `overgrowth.json`) |
| `overgrowth-node-KIND-STATE.png` | The 8 node flowers (battle, event, elite, shop, rest, treasure, mystery, boss) in 4 states: idle, hover, click, used |
| `overgrowth-path-default.png`, `-off.png`, `-used.png` | The route pieces in their three states |
| `overgrowth.json` | All the numbers below in one file, for the app to read |
| `example-PRESET.json`, `example-climb.png`, `example-tall.png` | Four finished floors (`climb`, `tall`, `wide`, `tangle`) as layout files, and two of them drawn |

## A floor is a layout file

`example-climb.json` is the whole recipe for one floor, and `make_overgrowth.py --layout out.json --seed N --preset NAME` makes another (same seed and preset, same floor). It has:

- `land`: one string per row of **cells** (16 x 16 pixels), `#` is land, `.` is void. `cells` is the width and height, `size` the pixels.
- `nodes`: `floor` and `lane`, the `kind`, the cell `x`, `y`, and `px`, `py`: the pixel the flower's **anchor** goes on.
- `edges`: from node to node (`[floor, lane]`), with the route's two ends in pixels (`x0, y0` to `x1, y1`) and `n`, the number of pixel steps along it.
- `tiles`: three grids of strings, one character per **corner** `(i, j)` with `0 <= i <= width` and `0 <= j <= height`: `bits` (a hex digit, 0-f), `style` (0-4) and `full` (the variant of the full tile).
- `pieces`: the loose pieces, in the order to draw them: `layer` (`tone`, `patch`, `decor`, `hang`), `id` (the sheet, without `overgrowth-`), `frame`, and `x`, `y`, the pixel the sprite's anchor goes on.

## Drawing it, from the bottom

1. **Void**: repeat `overgrowth-void.png` over the whole map.
2. **Spill**: for every corner tile with `bits` 1-14, draw the spill tile (column `bits`, row `style`) with its top left at `(i * 16 - 8, (j + 1) * 16 - 8)`: one row **down**.
3. **Ground**: for every corner tile with `bits` other than 0, draw the ground tile (column `bits`, row `style`) with its top left at `(i * 16 - 8, j * 16 - 8)`. When `bits` is 15, draw the variant `full` of `overgrowth-full.png` instead.
4. **Pieces**, in order: `tone`, `patch`, `decor`, `hang`. Put each sprite's anchor on `(x, y)`. The `wisp` is an animation (6 fps); the others are one frame, picked by `frame`.
5. **Routes**: along each edge, one point per pixel step: `(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)` for `k = 0..n` (floor each). Draw them in the state the node says, see below.
6. **Nodes**: the flower for the node's `kind` and state, with its anchor on `(px, py)`. Draw the nodes from the top of the map down.

Turn smoothing off and scale by whole numbers only. The dual grid (a tile for every corner between four cells, picked by which are land) is the same as the node map's: TL 1, TR 2, BL 4, BR 8.

## States

A node is one of **idle** (default; loops), **hover** (loops), **click** (plays once, then idle, or used), or **used**. The numbers are in `overgrowth.json`.

| State | Frames | fps | Notes |
|---|---|---|---|
| idle | 4 | 4 | loops, a slight sway |
| hover | 4 | 8 | loops, lifted and blazing, motes of light circling the clearing |
| click | 6 | 12 | **plays once**: squash, spring up, a ring of light and sparks bursts out |
| used | 1 | - | faded to ash: the node is done |

Each flower stands in a dark clearing ringed in its own colour, so it stands out from the moss. Cells are 40 x 40 with the anchor at (20, 30), except the **boss** (the summit), 56 x 56 at (28, 46).

A **route** has three states, and the app decides which applies. A way you have taken is **used**, the ways open from where you are are **default**, and the rest are **off**:

| State | What it looks like |
|---|---|
| default | 3 x 3 amber dots every 8 pixels, a bright pulse runs along them (4 frames, 6 fps; dot number `n` shows phase `(n + frame) % 4` of `overgrowth-path-default`) |
| off | a small dark unlit dot every 9 pixels (`overgrowth-path-off`) |
| used | a solid mint line, 2 pixels wide with a dark outline (`overgrowth-path-used`: a step, a bright step on every 5th pixel, and the sparkle on every 20th, moving 5 pixels a frame, 4 frames, 4 fps) |

## Ground, in short

- **Ground** is a dual grid: a 16 x 16 tile on every corner between four cells. Tile edges always agree, so any two tiles join.
- **Cliffs** hang under every south edge, in 5 styles. Every style ends the same at its left and right sides, so a tile joins any style next to it. A cliff that runs past the bottom of its tile continues in the **spill** tile.
- **Variety**: the `full` tiles differ only in their middle; the `tone` and `patch` pieces lay big soft patches of lighter and deeper moss and small patches over the open ground, and only where they fit inside an island, so they never hang over an edge.
