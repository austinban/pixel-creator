# Destructibles: barricades, barrels, walls, urns and a hay cart that break

Eight pieces in category **Destructibles** (`tools/make_destructibles.py`, shared renderer `tools/prop3d.py`), things on the battlefield that can be broken. Each comes in **three states** and has a **destruction animation** of its own: 16 files, every one a strip of frames side by side. They are in the ground tiles' projection and palette. `destructibles.json` lists every file with its footprint and the flags below.

## The geometry

- One ground cell is a **32 x 16 diamond**: a step along the grid axis x moves the picture **16 across and 8 down** (down-right), a step along y **16 across and 8 down-left**. One level of height is **16 pixels up**.
- **Anchor: the middle of the footprint on the ground**, the same in every state and every frame of a piece (`anchor` in `assets/data.js`). The picture is `16 * (fx + fy)` plus a margin wide (the room for flying chunks and the dust cloud), and the anchor's x is its centre column. **A piece's states and its strip are the same size with the same anchor, so you swap between them in place** with no offset.
- **Footprint:** `footprint.size` is [x cells, y cells] and `footprint.cells` the cells it stands on, counted `(i, j)` from the back corner, i running down-right and j down-left. For a piece over several cells, sort it by its front-most cell (the largest `i + j`) with the rest of the scenery.
- A file is a **strip**: `barrel-explosive.png` is 192 x 46 (three states of 64 x 46, left to right: Intact, Damaged, Destroyed) and `barrel-explosive-destroy.png` is 384 x 46 (six frames of 64 x 46).

## The pieces

| States file | Destruction strip | What | Footprint | Blocks while standing | Cover (levels) | Explosive |
|---|---|---|---|---|---|---|
| `barricade-1x1.png` | `barricade-1x1-destroy.png` | a wooden barricade | 1 x 1 | yes | 0.8 | no |
| `barricade-1x2.png` | `barricade-1x2-destroy.png` | a longer barricade | 1 x 2 | yes | 0.8 | no |
| `barrel-explosive.png` | `barrel-explosive-destroy.png` | a barrel with a fuse, it goes off | 1 x 1 | yes | 0.62 | **yes** |
| `barrel-stack.png` | `barrel-stack-destroy.png` | a stack of plain barrels | 1 x 1 | yes | 1.2 | no |
| `wall-1x1.png` | `wall-1x1-destroy.png` | a breakable stone wall | 1 x 1 | yes | 1.0 | no |
| `wall-1x2.png` | `wall-1x2-destroy.png` | a longer stone wall | 1 x 2 | yes | 1.0 | no |
| `urns.png` | `urns-destroy.png` | a cluster of clay urns | 1 x 1 | yes | 0.45 | no |
| `haycart.png` | `haycart-destroy.png` | a hay cart | 2 x 1 | yes | 0.75 | no |

## What the flags mean

Every record (in `assets/data.js` and `destructibles.json`) carries:

- **`blocks`**: while the piece is intact or damaged it occupies every cell of its footprint: nothing walks through it. True for all of them.
- **`blocks_when_destroyed`**: whether the wreck still blocks. **False for all**: a destroyed piece leaves low rubble that a unit walks over, so the cells open up.
- **`cover_levels`**: how high the piece stands, in levels of 16 pixels. More than half a level (more than 8 pixels) counts as cover for the line of sight; the urns (0.45) are the exception, low enough to shoot over. A wall is a full level, a stack of barrels 1.2.
- **`explosive`**: the piece goes off when destroyed. Only `barrel-explosive`.
- **`states`**: `["intact", "damaged", "destroyed"]`, the order of the frames in the states file (`names` says the same in words).
- None of them is walkable (`walkable: false`): they are things to get round, not stand on.

## Playing the destruction

1. **Standing:** draw the **Intact** frame (frame 0 of the states file). While it stands it blocks its footprint.
2. **Hurt:** when a piece is damaged but not yet broken (say, below half its health), swap to the **Damaged** frame (frame 1). It is the same size and anchor, so nothing jumps. The damaged state still blocks.
3. **Destroyed:** when its health runs out, **play the strip once** (`<id>-destroy.png`, 6 frames at 12 fps, about half a second), and do not loop it. Draw it where the piece stood. When it ends, **hold the Destroyed frame** (frame 2 of the states file) as the wreck from then on, and clear `blocks`: set the cells walkable.
4. The strip: frame 1 is the piece lit up (a flash, a fireball for the barrel), frame 2 it breaks into chunks, the chunks being the piece's own pixels thrown out along the ground's plane with a cloud of dust, frame 3 the chunks at the top of their arc, frame 4 they fall, frame 5 they land and the cloud thins, frame 6 is the wreck with a last wisp. Its last frame is nearly the Destroyed frame, so the hand-over is seamless.
5. **Explosive:** when an `explosive` piece is destroyed, it also hurts what is round it: the game decides the radius and the damage (the strip is only the picture: its fireball is drawn inside the piece's own cell and the room round it, and does not say how far the blast reaches). It can set off other explosive pieces; chain them one strip at a time, a short beat apart.

## Blocking rules

- A piece blocks **every cell of its footprint** while intact or damaged. A 1 x 2 wall is two cells; the hay cart is two.
- `cover_levels` over half a level is cover (a wall, a barricade, a stack of barrels): it blocks sight from behind it but a unit can stand beside it. The urns are not cover.
- The wreck never blocks (`blocks_when_destroyed` is false).
- The pieces sit on the **ground** (the land's top face), not in water.

## Things to know

- The destruction animation breaks the sprite into 4 x 4 pixel chunks of its own pixels, so it reads well on the barricade, the barrel and the cart, and noisy on the big stone walls.
- The damaged barricade is only slightly different from the intact one; the barrel and stack wrecks are rough, and the urns are tiny.
- The explosion uses fire colours (orange and yellow); everything else breaks into dust (bone, sand, grey stone). It is the body explosion's way in other colours, with no blood.
- Everything is palette colours (roles only), so the pieces recolour with the rest of the art, and the pieces are deterministic: the same code gives the same pictures every time.
