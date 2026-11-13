# Bridges: stone arch, broken, rotted plank and corrupted, 3 and 5 cells long

14 bridges in category **Bridges** (`tools/make_bridges.py`, drawn by `tools/voxelkit.py`), in the ground tiles' projection and the stone palette. Each is **one sprite that covers its whole footprint**, one cell wide and 3 or 5 long, like the rocks and the buildings. `bridges.json` lists every file with its footprint, which cells can be walked and the axis it runs along. The older rickety `bridge` (four 32 x 40 frames, laid cell by cell: see `BRIDGES.md`) is **unchanged**; these are whole-span pieces you place once.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right, SE), a step along y **16 across and 8 down-left** (SW). One level of height is **16 pixels up**.
- `-Nx1` runs **along x** (SE, `footprint.size` is [N, 1]); `-1xN` runs **along y** (SW, [1, N]). N is 3 or 5. They are the same bridge turned, with the same size, anchor and cover. Cells are `(i, j)` from the back corner: `(0, 0)` .. `(N-1, 0)` for x, `(0, 0)` .. `(0, N-1)` for y.
- **Anchor: the middle of the bounding box on the ground** (the ground the bridge stands on, at its base). The picture is `16 * (fx + fy) + 12` wide, so a 3-cell bridge is 76 wide and a 5-cell one 108; the anchor's x is the picture's centre column and its y is the `anchor` in `assets/data.js` (the corrupted ones are 4 pixels taller for their mushrooms, so their anchor y is 4 more).
- **The deck is exactly 1 level (16 pixels) above the ground the bridge stands on.** Stand it on the floor of a gap that is one level below the banks (sunken water is exactly that: one step below the grass), and the deck meets the bank flush. On level ground it meets 1-level ledges. The ends are solid: the arch bridges have **abutments** (solid stone) at each end, and the plank bridges have a **stone sill** a quarter of a cell long at each end where the planks rest on the bank, with every plank kept at both ends (the missing and half planks are in the middle). So a unit steps from the bank straight onto the end cell.
- To place one with its back-corner cell at the map cell `(cx, cy)`: the bounding box's middle is the ground point of the cell `(cx + fx / 2, cy + fy / 2)`; put the anchor on it and draw. **Draw order:** it covers several cells, so sort it by its **front-most cell** (the largest `i + j`) with the other scenery and draw it after the ground (and the water) under it. Units crossing walk **on top of** the sprite: draw them after the bridge, at deck height (+16 pixels).

## Walkable or not

`walkable` is **true** when the deck is flat at 1 level over every one of its cells. `top_cover` gives, per cell `"i,j"`, the share of the cell's area (0 to 1) that is deck or planks; a bridge is `walkable` only when **every cell is at least 0.6** (`walk_min`, the same as the rocks). `walkable_cells` lists the cells that are at or over the threshold: for a whole bridge that is every cell, for a **broken** one it is the two ends.

- The **broken** bridges (`bridge-broken-5x1`, `-1x5`) are the 5-cell arch with the middle cell crumbled away: ragged stubs either side of an open gap with rubble at its foot. As a whole they are **not walkable** (`walkable: false`; the gap cell has a cover of 0.14), but the first two cells and the last two **can be walked** and are listed in `walkable_cells`. Use them as a broken crossing that has to be mended or crossed another way, or as two dead-end stubs.
- A unit **cannot enter the gap cell**. Treat it as the gap it looks like (a pit, water): impassable for walking, open for flying.
- The stone bridges have a **tall parapet along the back** and a **low kerb along the front**, because the camera looks at the front: a unit crossing is never hidden behind its own bridge. The plank bridges have a rope rail along the back only, like the older bridge.

## The bridges

| File | What | Footprint | Picture | Anchor | Levels | Walkable | Least cover |
|---|---|---|---|---|---|---|---|
| `bridge-arch-3x1.png` | Stone arch bridge, 3 cells, along x (SE) | 3 x 1 | 76 x 63 | (38, 45) | 1 | yes | 0.69 |
| `bridge-arch-1x3.png` | Stone arch bridge, 3 cells, along y (SW) | 1 x 3 | 76 x 63 | (38, 45) | 1 | yes | 0.69 |
| `bridge-arch-5x1.png` | Stone arch bridge, 5 cells, along x (SE) | 5 x 1 | 108 x 79 | (54, 53) | 1 | yes | 0.69 |
| `bridge-arch-1x5.png` | Stone arch bridge, 5 cells, along y (SW) | 1 x 5 | 108 x 79 | (54, 53) | 1 | yes | 0.69 |
| `bridge-broken-5x1.png` | Broken stone bridge, 5 cells, along x (SE) | 5 x 1 | 108 x 79 | (54, 53) | 1 | no (ends only) | 0.14 |
| `bridge-broken-1x5.png` | Broken stone bridge, 5 cells, along y (SW) | 1 x 5 | 108 x 79 | (54, 53) | 1 | no (ends only) | 0.14 |
| `bridge-plank-3x1.png` | Rotted plank bridge, 3 cells, along x (SE) | 3 x 1 | 76 x 63 | (38, 45) | 1 | yes | 0.93 |
| `bridge-plank-1x3.png` | Rotted plank bridge, 3 cells, along y (SW) | 1 x 3 | 76 x 63 | (38, 45) | 1 | yes | 0.93 |
| `bridge-plank-5x1.png` | Rotted plank bridge, 5 cells, along x (SE) | 5 x 1 | 108 x 79 | (54, 53) | 1 | yes | 0.70 |
| `bridge-plank-1x5.png` | Rotted plank bridge, 5 cells, along y (SW) | 1 x 5 | 108 x 79 | (54, 53) | 1 | yes | 0.70 |
| `bridge-corrupt-3x1.png` | Overgrown stone bridge, 3 cells, along x (SE) | 3 x 1 | 76 x 67 | (38, 49) | 1 | yes | 0.62 |
| `bridge-corrupt-1x3.png` | Overgrown stone bridge, 3 cells, along y (SW) | 1 x 3 | 76 x 67 | (38, 49) | 1 | yes | 0.62 |
| `bridge-corrupt-5x1.png` | Overgrown stone bridge, 5 cells, along x (SE) | 5 x 1 | 108 x 83 | (54, 57) | 1 | yes | 0.62 |
| `bridge-corrupt-1x5.png` | Overgrown stone bridge, 5 cells, along y (SW) | 1 x 5 | 108 x 83 | (54, 57) | 1 | yes | 0.62 |

**Kinds:** `arch` is a stone bridge on one arch (3 cells) or two arches and a pier (5 cells); `plank` is a rotted plank bridge on posts and beams, with planks missing and moss on the rest; `corrupt` is the arch bridge in plum and lavender stone grown over with vines and small mushrooms (use it on corrupted ground and over corrupted water, where the plain `bridge` and the stone bridge do not fit); `broken` is described above.

## Things to know

- The arch openings are low (the arch is 12 pixels tall under a 16 pixel deck), because the picture is cut at ground level; they read as a notch under the deck, not as a tall tunnel. The water or ground showing through the arch is whatever the map has under the bridge: draw the bridge over it.
- The corrupted bridge has the lowest cover (0.62) because of the mushrooms on the kerb and the parapet. It is still walkable. The plain stone bridge's ends are the thinnest (0.69).
- Rocks, bridges and stairs share one stone ramp (`r q p l k w`, with moss `z A B`), so a bridge sits against a rock ledge or a bank without a colour jump. Every picture is palette roles only and outlined on the outside; moss and mushrooms may sit over the outline.
- To join a bridge to the **stairs and ramps** (`sprites/assets/stairs/`), put the stair's high end against the first or last cell: its top is the same 1 level (16 pixels) as the deck.
- A bridge has **no front**: one picture each. The two axes are separate pieces. NE and SE do not apply.
