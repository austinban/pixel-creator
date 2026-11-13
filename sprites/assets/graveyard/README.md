# Graveyard and ritual set: gravestones, cairns, bones, altars, lanterns, iron and ritual circles

22 pieces in category **Graveyard** (`tools/make_graveyard.py`) for the Gravemoor map and any place of the dead: small 3D models in the ground's projection (the right face lit, light from the upper left) in the stone ramp with a little moss, bone and iron, plus glowing marks on the ground. All palette roles only; every standing piece has the one-pixel outline, the ritual circles (flat marks) have none. `graveyard.json` lists the numbers below.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**. **x runs SE, y runs SW.**
- **Anchor: the middle of the piece's bounding box on the ground.** `footprint.cells` are the cells `(i, j)` it stands on, counted from the back corner (the top of the diamond), `i` down-right and `j` down-left. A piece over several cells is one sprite covering them: sort it by its front-most cell (the largest `i + j`) and draw it after the ground.
- A standing piece is `16 * (fx + fy) + 20` wide (10 pixels of margin each side), so every 1 x 1 is 52 wide and a 2 x 1 is 68. Pieces have **no front**: one picture each, except the iron, which comes along x and along y.

## Standing pieces: they block

Every 1 x 1 standing piece has `blocks: true`: treat its cell as blocked. None is walkable. They are scenery for the cells they stand on, drawn after the ground and mycelium.

| File | What | Footprint | Blocks | Size | Anchor |
|---|---|---|---|---|---|
| `gravestone-round.png` | a round-topped gravestone | 1 x 1 | yes | 52 x 38 | (26, 30) |
| `gravestone-cross.png` | a cross | 1 x 1 | yes | 52 x 40 | (26, 32) |
| `gravestone-leaning.png` | a leaning stone | 1 x 1 | yes | 52 x 39 | (26, 31) |
| `gravestone-broken.png` | a broken stone, its top lying beside it | 1 x 1 | yes | 52 x 36 | (26, 28) |
| `cairn-tall.png` | a tall stack of stones | 1 x 1 | yes | 52 x 40 | (26, 32) |
| `cairn-small.png` | a small stack | 1 x 1 | yes | 52 x 31 | (26, 23) |
| `bones-skull.png` | a skull among bones | 1 x 1 | yes | 52 x 30 | (26, 22) |
| `bones-ribs.png` | a rib cage | 1 x 1 | yes | 52 x 32 | (26, 24) |
| `bones-scatter.png` | scattered bones | 1 x 1 | yes | 52 x 27 | (26, 19) |
| `obelisk.png` | a tall four-sided stone with glowing runes on the two faces the camera sees | 1 x 1 | yes | 52 x 68 | (26, 60) |
| `rune-plinth.png` | a plinth with a rune and a crystal | 1 x 1 | yes | 52 x 47 | (26, 39) |

## The rune altar: a stone table to stand on

A stone table with runes cut in its **flat top, one level up**. It is `walkable` and has `top_cover` per cell `"i,j"` (the share of the cell that is flat top; a piece is walkable when every cell has at least **0.6**). The 1 x 2 measures lower (0.75) than the 2 x 1 (0.88). It has no `blocks` flag: it is a step a unit can climb onto, so the game decides whether an altar stays open to stand on or is blocked as a shrine.

| File | Footprint | Levels | Flat top per cell | Size | Anchor |
|---|---|---|---|---|---|
| `rune-altar-2x1.png` | 2 x 1 | 1 | 0,0: 0.88, 1,0: 0.88 | 68 x 42 | (34, 34) |
| `rune-altar-1x2.png` | 1 x 2 | 1 | 0,0: 0.75, 0,1: 0.75 | 68 x 42 | (34, 34) |

## Spirit lanterns: a flicker you can loop

Two lanterns, each an **animation of 4 frames at 6 fps** that **loops** (the last frame leads into the first), with a halo of drifting glow. They have `light: true` (the glow is part of the picture, so the game does not need to add a light) and `blocks: true`. They are wider than the other pieces (60) to hold the halo, which is a dither of dots: it is low in contrast and best over plain ground.

| File | Size | Anchor |
|---|---|---|
| `spirit-lantern-post.png` | 60 x 57 | (30, 49) |
| `spirit-lantern-stone.png` | 60 x 41 | (30, 33) |

## Iron: a fence and a gate

A section of iron fence and a gate, each in two pictures: `runs_along: "x"` runs down-right along the grid's x axis, `"y"` down-left. They sit on one cell and join at the cell's edges, so a run of them across several cells makes a wall. Both **block** the cell. The gate has `opens: true`: the game may swap it for an open state or let units through; there is no open picture yet. The y pictures are not mirrors of the x ones.

| File | Runs along | Opens | Size | Anchor |
|---|---|---|---|---|
| `iron-fence-x.png` | x | no | 48 x 38 | (24, 30) |
| `iron-fence-y.png` | y | no | 48 x 38 | (24, 30) |
| `graveyard-gate-x.png` | x | yes | 48 x 46 | (24, 38) |
| `graveyard-gate-y.png` | y | yes | 48 x 46 | (24, 38) |

## Ritual circles: marks on the ground

Flat decals, **2 x 2, 3 x 3 and 4 x 4 cells**, a ring of runes and a star, glowing on the ground. Draw them **on the ground, under everything else** (the layer of the blood pool and the mycelium). Each is one sprite covering `n x n` cells, `decal: true`, no outline, anchored at the middle: its width is `32 n` and its height `16 n`. They do not block and are not walkable pieces: a unit stands on the ground below, and the game may give the circle a rule.

| File | Footprint | Size | Anchor |
|---|---|---|---|
| `ritual-circle-2.png` | 2 x 2 | 64 x 32 | (32, 16) |
| `ritual-circle-3.png` | 3 x 3 | 96 x 48 | (48, 24) |
| `ritual-circle-4.png` | 4 x 4 | 128 x 64 | (64, 32) |

## Things to know

- They fit the **corrupted** ground best (they were drawn for the Gravemoor moor), and read fine on plain ground.
- The iron fence is dark purple and low in contrast against dark ground; the gate reads better. The bones and gravestones are small, so their details are a few pixels each, and the skull is the hardest to read.
- The stone lantern's roof can read as horns or a hat, and the halo is noisy over a busy ground.
