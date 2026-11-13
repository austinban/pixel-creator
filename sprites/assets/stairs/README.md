# Stairs and ramps: up 1 or 2 levels, four ways, flush with a ledge

24 pieces in category **Stairs** (`tools/make_stairs.py`, drawn by `tools/voxelkit.py`), in the ground tiles' projection and the rock ledges' stone, that carry a unit up to a ledge. Each is **one sprite that covers its whole footprint**: 2 or 3 cells (a ledge-ramp is 2 or 3 as well, with its own flat cell). `stairs.json` lists every file with its footprint, the way up and the rise. The two stair cubes on the ground sheet (`ground-0-1`, `ground-1-1`) are **unchanged**.

## The three kinds

- **stair**: a run of stone steps. Up **one level** over 2 cells (4 steps of 4 pixels), up **two levels** over 3 cells (8 steps of 4 pixels). Files `stair-h1-*`, `stair-h2-*`.
- **ramp**: the same runs as a smooth stone slope. Files `stair-ramp-h1-*`, `stair-ramp-h2-*`.
- **ledge-ramp**: a ramp that ends in a **ledge cell** with a flat top at the top height, so it joins the rock ledges as one piece: 1 level = a ramp cell then a ledge cell (2 cells); 2 levels = two ramp cells then a ledge cell (3 cells). Files `stair-ledge-ramp-h1-*`, `stair-ledge-ramp-h2-*`. It is steeper than the stairs (1 cell per level, against 2 for the stairs), so use it where space is short.

Each comes **up toward** each of the four sides: **SE** (up toward +x, down and to the right), **NW** (up toward -x), **SW** (up toward +y, down and to the left) and **NE** (up toward -y). The name ends in the way up.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along x moves the picture **16 across and 8 down** (SE), a step along y **16 across and 8 down-left** (SW). One level is **16 pixels up**.
- A piece rising toward **SE or NW** runs along x (`footprint.size` is [N, 1]); one rising toward **SW or NE** runs along y ([1, N]). N = `run_cells + flat_cells`. Cells are `(i, j)` from the back corner. The **low end** is at the ground of the footprint (height 0); the **high end** is exactly `levels` levels (16 or 32 pixels) up. For **SE** the high end is at the last cell along x (`i = N - 1`), for **NW** at `i = 0`, for **SW** at the last cell along y (`j = N - 1`), for **NE** at `j = 0`.
- **Anchor: the middle of the bounding box on the ground.** The picture is `16 * (fx + fy) + 12` wide (60 for a 2-cell piece, 76 for a 3-cell one). The anchor's x is the picture's centre column.
- To place one with its back-corner cell at the map cell `(cx, cy)`: the bounding box's middle is the ground point of the cell `(cx + fx / 2, cy + fy / 2)`; put the anchor on it and draw. **Draw order:** sort by its **front-most cell** (the largest `i + j`) with the other scenery, after the ground.

## Joining a ledge

The **high end is flush with a ledge of the same height**: put a rock ledge (`rock-ledge-*`, `rock-slab-*`, `levels` 1 or 2) on the cell **beyond** the high end, and the top of the last step or the ramp's end meets its flat top with no gap. A **ledge-ramp** already has its own ledge cell at the top: continue from it. The cell at the **low end** is plain ground at height 0.

For movement: the whole footprint is **walkable** (`walkable: true`, every cell `top_cover` 1.0). Treat it as a connector: a unit enters at the low end and leaves at the high end (or the other way), and its height follows the surface along the run: in whole 4-pixel steps for a stair, smoothly for a ramp, and flat on a ledge-ramp's last cell. Moving **sideways** off a stair onto its neighbours is the game's call (a ledge or rock beside it is higher; ground beside it is lower).

## The pieces

| File | Kind | Up toward | Footprint | Run + flat cells | Levels | Picture | Anchor |
|---|---|---|---|---|---|---|---|
| `stair-h1-se.png` | stair | SE | 2 x 1 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-h1-nw.png` | stair | NW | 2 x 1 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-h1-sw.png` | stair | SW | 1 x 2 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-h1-ne.png` | stair | NE | 1 x 2 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-h2-se.png` | stair | SE | 3 x 1 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-h2-nw.png` | stair | NW | 3 x 1 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-h2-sw.png` | stair | SW | 1 x 3 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-h2-ne.png` | stair | NE | 1 x 3 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-ramp-h1-se.png` | ramp | SE | 2 x 1 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-ramp-h1-nw.png` | ramp | NW | 2 x 1 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-ramp-h1-sw.png` | ramp | SW | 1 x 2 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-ramp-h1-ne.png` | ramp | NE | 1 x 2 | 2 + 0 | 1 | 60 x 46 | (30, 32) |
| `stair-ramp-h2-se.png` | ramp | SE | 3 x 1 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-ramp-h2-nw.png` | ramp | NW | 3 x 1 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-ramp-h2-sw.png` | ramp | SW | 1 x 3 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-ramp-h2-ne.png` | ramp | NE | 1 x 3 | 3 + 0 | 2 | 76 x 70 | (38, 52) |
| `stair-ledge-ramp-h1-se.png` | ledge-ramp | SE | 2 x 1 | 1 + 1 | 1 | 60 x 46 | (30, 32) |
| `stair-ledge-ramp-h1-nw.png` | ledge-ramp | NW | 2 x 1 | 1 + 1 | 1 | 60 x 46 | (30, 32) |
| `stair-ledge-ramp-h1-sw.png` | ledge-ramp | SW | 1 x 2 | 1 + 1 | 1 | 60 x 46 | (30, 32) |
| `stair-ledge-ramp-h1-ne.png` | ledge-ramp | NE | 1 x 2 | 1 + 1 | 1 | 60 x 46 | (30, 32) |
| `stair-ledge-ramp-h2-se.png` | ledge-ramp | SE | 3 x 1 | 2 + 1 | 2 | 76 x 70 | (38, 52) |
| `stair-ledge-ramp-h2-nw.png` | ledge-ramp | NW | 3 x 1 | 2 + 1 | 2 | 76 x 70 | (38, 52) |
| `stair-ledge-ramp-h2-sw.png` | ledge-ramp | SW | 1 x 3 | 2 + 1 | 2 | 76 x 70 | (38, 52) |
| `stair-ledge-ramp-h2-ne.png` | ledge-ramp | NE | 1 x 3 | 2 + 1 | 2 | 76 x 70 | (38, 52) |

Every record has a `connector`: `{kind, up, rise_levels, run_cells, flat_cells}` (also in `stairs.json`), so a map generator can pick a piece by the height and the way up without reading the name.

## Things to know

- The pieces that rise **toward the camera** (SE and SW) mostly show their tall front wall, so the steps or the ramp surface are hard to see; that is the projection. The NW and NE ones, which rise away from the camera, read best. Draw a unit on a stair or ramp after it at the right height and the climb reads.
- The ramps show a pinstripe from 1-pixel risers. The ledge-ramps are steeper than the stairs (1:1 against 1:2).
- Stone and courses are the buildings'; they do not match the rock ledges' strata exactly. Moss may sit over the outline.
- Palette roles only (`r q p l k w`, moss `z A B`, outline `O`), outlined on the outside, so a piece recolours with the rest of the art. Each piece is one picture with **no front** variant.
