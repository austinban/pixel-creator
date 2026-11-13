# Scaffold stairs: wood plank twins of the stone stairs

24 pieces in category **Stairs** (`tools/make_scaffold_stairs.py`): a timber scaffold for every stone stair, ramp and ledge ramp in `sprites/assets/stairs/`, with the **same footprint, height, direction, run and anchor x**, so a map can swap one for the other and every rule still holds. Each record carries its stone twin's id (`twin`, and `stone_twin` in `scaffold-stairs.json`).

They are open timber frames: plank treads (open between the steps) on a stringer under each side, posts down to the ground at the ends and at every cell boundary, and diagonal braces on the camera side. **The ground shows through**, which the solid stone stairs do not. The **ramps and ledge ramps have a rail along the back edge** (two rails on posts) so the treads stay in view; **the stepped stairs have none**.

- One ground cell is a **32 x 16 diamond**; a step along x moves the picture 16 across and 8 down (down-right), along y 16 across and 8 down-left. A level is **16 pixels** (two game height steps). Anchor: the middle of the footprint on the ground; the picture is `16 * (fx + fy) + 12` wide. A piece over several cells is drawn when you reach its front-most cell.
- **`up`** is the way up: `se` rises toward +x (down and to the right), `nw` toward -x, `sw` toward +y (down and to the left), `ne` toward -y. The low end is at the ground and the high end is exactly 1 or 2 levels up, flush with a rock ledge, a slab or a flat scaffold of that height. `connector` gives `kind` (`stair`, `ramp`, `ledge-ramp`), `rise_levels`, `run_cells` and `flat_cells`.
- **Walkable:** every piece is walkable over its whole footprint. `top_cover` is the share of each cell that is tread or ramp surface (the rail posts on the ramps are the only things that take any): 1.00 on the stepped stairs, 0.93 on the ramps and ledge ramps. Walk along the surface height: a stair rises 4 pixels a step, a ramp smoothly.
- Palette roles only (planks in the orange-brown roles, frame in plum), so they recolour with the rest of the art.

| File | What | Footprint | Levels | Up | Run + flat cells | Min top cover |
|---|---|---|---|---|---|---|
| `scaffold-h1-se.png` | Scaffold stairs, 1 up, rising toward SE | 2 x 1 | 1 | SE | 2 + 0 | 1.00 |
| `scaffold-h1-nw.png` | Scaffold stairs, 1 up, rising toward NW | 2 x 1 | 1 | NW | 2 + 0 | 1.00 |
| `scaffold-h1-sw.png` | Scaffold stairs, 1 up, rising toward SW | 1 x 2 | 1 | SW | 2 + 0 | 1.00 |
| `scaffold-h1-ne.png` | Scaffold stairs, 1 up, rising toward NE | 1 x 2 | 1 | NE | 2 + 0 | 1.00 |
| `scaffold-h2-se.png` | Scaffold stairs, 2 up, rising toward SE | 3 x 1 | 2 | SE | 3 + 0 | 1.00 |
| `scaffold-h2-nw.png` | Scaffold stairs, 2 up, rising toward NW | 3 x 1 | 2 | NW | 3 + 0 | 1.00 |
| `scaffold-h2-sw.png` | Scaffold stairs, 2 up, rising toward SW | 1 x 3 | 2 | SW | 3 + 0 | 1.00 |
| `scaffold-h2-ne.png` | Scaffold stairs, 2 up, rising toward NE | 1 x 3 | 2 | NE | 3 + 0 | 1.00 |
| `scaffold-ramp-h1-se.png` | Scaffold ramp, 1 up, rising toward SE | 2 x 1 | 1 | SE | 2 + 0 | 0.93 |
| `scaffold-ramp-h1-nw.png` | Scaffold ramp, 1 up, rising toward NW | 2 x 1 | 1 | NW | 2 + 0 | 0.93 |
| `scaffold-ramp-h1-sw.png` | Scaffold ramp, 1 up, rising toward SW | 1 x 2 | 1 | SW | 2 + 0 | 0.93 |
| `scaffold-ramp-h1-ne.png` | Scaffold ramp, 1 up, rising toward NE | 1 x 2 | 1 | NE | 2 + 0 | 0.93 |
| `scaffold-ramp-h2-se.png` | Scaffold ramp, 2 up, rising toward SE | 3 x 1 | 2 | SE | 3 + 0 | 0.93 |
| `scaffold-ramp-h2-nw.png` | Scaffold ramp, 2 up, rising toward NW | 3 x 1 | 2 | NW | 3 + 0 | 0.93 |
| `scaffold-ramp-h2-sw.png` | Scaffold ramp, 2 up, rising toward SW | 1 x 3 | 2 | SW | 3 + 0 | 0.93 |
| `scaffold-ramp-h2-ne.png` | Scaffold ramp, 2 up, rising toward NE | 1 x 3 | 2 | NE | 3 + 0 | 0.93 |
| `scaffold-ledge-ramp-h1-se.png` | Scaffold ledge with a ramp, 1 up, rising toward SE | 2 x 1 | 1 | SE | 1 + 1 | 0.93 |
| `scaffold-ledge-ramp-h1-nw.png` | Scaffold ledge with a ramp, 1 up, rising toward NW | 2 x 1 | 1 | NW | 1 + 1 | 0.93 |
| `scaffold-ledge-ramp-h1-sw.png` | Scaffold ledge with a ramp, 1 up, rising toward SW | 1 x 2 | 1 | SW | 1 + 1 | 0.93 |
| `scaffold-ledge-ramp-h1-ne.png` | Scaffold ledge with a ramp, 1 up, rising toward NE | 1 x 2 | 1 | NE | 1 + 1 | 0.93 |
| `scaffold-ledge-ramp-h2-se.png` | Scaffold ledge with a ramp, 2 up, rising toward SE | 3 x 1 | 2 | SE | 2 + 1 | 0.93 |
| `scaffold-ledge-ramp-h2-nw.png` | Scaffold ledge with a ramp, 2 up, rising toward NW | 3 x 1 | 2 | NW | 2 + 1 | 0.93 |
| `scaffold-ledge-ramp-h2-sw.png` | Scaffold ledge with a ramp, 2 up, rising toward SW | 1 x 3 | 2 | SW | 2 + 1 | 0.93 |
| `scaffold-ledge-ramp-h2-ne.png` | Scaffold ledge with a ramp, 2 up, rising toward NE | 1 x 3 | 2 | NE | 2 + 1 | 0.93 |

## Things to know

- The stepped stairs that rise **toward the camera** (`se` and `sw`) show their underside and posts more than their steps, as the stone ones show their front wall; the ones rising away read best.
- The braces are one pixel thick and low contrast at 1x.
- The twin of `scaffold-ramp-h1-se` is `stair-ramp-h1-se`, and so on: swap `scaffold-` for `stair-` (the stepped stone ones are `stair-h1-se`, the scaffold ones `scaffold-h1-se`).
