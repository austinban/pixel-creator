# Animated water

The ground sheet's water tiles, moving: the **normal** set and the **corrupted** set, the open pieces and the eight edge pieces with foam, at both heights (level with the grass, and sunken). 36 animations, each **10 frames at 4 frames a second** (a loop of 2.5 seconds), in categories **Animated Water** and **Animated Corrupted Water**.

Each one is the same tile as in the ground sheet and keeps its **cell**: `water-COL-ROW` moves `ground-COL-ROW`, and `water-corrupted-COL-ROW` moves `ground-corrupted-COL-ROW`. So a map swaps a still water tile for its animation by cell and changes nothing else: same 32 x 32 size, same sides, same outline and silhouette, drawn where the still tile was drawn. Each is a sheet of 10 frames, 8 across and 2 down (frame 0 first), and `water.json` lists every tile, its foam sides and its height.

| What moves | How |
|---|---|
| The water on the top face | The ring and glint texture drifts one tile's width over the loop, and carries on over the tile's borders, so tiles still join and frame 10 leads back to frame 0. A few glints twinkle (cyan on the normal water, violet on the corrupted). |
| The foam on an edge piece | A bright crest runs along the shore, measured along the edge so it carries on from one tile to the next. |

The sides of the cube, the outline, the mushroom pads on the corrupted water and everything else stay still. Frame 0 of an open tile is the ground sheet's tile.

## Drawing it

Pick the tile as you do now (by the sides that touch land), draw frame `n` of it in the tile's place, and **start each tile a frame later than the one behind it**, so a slow wave runs across the water instead of every tile moving in step:

```js
const FRAMES = 10, FPS = 4, STEP = 1;                          // water.json has them
const frame = (Math.floor(time * FPS) + (x + y) * STEP) % FRAMES;     // x, y: the tile's cell on the map
ctx.drawImage(sheet, (frame % 8) * 32, Math.floor(frame / 8) * 32, 32, 32, gx, gy, 32, 32);
```

- **STEP 1** is the look to use: the wave runs towards the viewer and the rings and foam stay joined from tile to tile (a seam may shift by a pixel or two).
- **STEP 0** (all tiles on the same frame) is the calmest and joins perfectly; it is what to use if you want it still and cheap.
- **Do not start tiles on random frames**: the rings stop joining at every border and the lake looks like a patchwork, and the foam crests flicker instead of running along the shore.
- Every water tile must use the same `time`; only the `(x + y) * STEP` differs.

An edge piece is chosen as before: the tile whose foam sides best match the sides that touch land (the `foam` list in `water.json`; NW, NE, SW, SE are screen directions). The open tile has none. Sunken and level water are separate tiles; do not mix them in one lake.
