# Node map

Top-down tiles for a floor-choosing map, like Slay the Spire's: a branching set of islands with water between them, and a pin on every
node. Everything for it is in this folder and shares the `nodemap-` prefix. On the Assets page it is the **Node map** category.

| File | What it is |
|---|---|
| `nodemap-grass-shore.png` | 16 shore tiles, **Grass islands** skin (green land, white foam, blue sea) |
| `nodemap-grass-sea.png` | The sea for that skin: 4 animation frames of one 16 x 16 tile |
| `nodemap-parchment-shore.png` | 16 shore tiles, **Parchment chart** skin (ochre land, inked coast, pale sea) |
| `nodemap-parchment-sea.png` | The sea for that skin, 4 frames |
| `nodemap-pins.png` | Three map pins: green, blue, red (16 x 24) |
| `nodemap.json` | All the numbers below in one file, for the app to read |
| `example-grass.png`, `example-parchment.png` | A finished example map in each skin, with routes and pins |
| `example-layout.json` | The example's layout: its nodes, edges and land, so you can check your own drawing against it |

The two skins have the same 16 tiles in the same order, so changing skin is only changing which two files you load.

## How a map is built

The map is a grid of **cells**, each either **land** or **water**. A cell is 16 x 16 pixels. You do not draw a tile per cell. You draw a
tile on every **corner** where four cells meet, and which of the 16 tiles it is depends on which of those four cells are land. This is called
a dual grid, and it is why 16 tiles are enough for every coast, every path one cell wide, and every blob:

```
 corner cells around a tile        the tile number is the sum of the land corners

     (i-1, j-1) | (i, j-1)             top left     = 1
     -----------+----------           top right    = 2
     (i-1, j)   | (i, j)              bottom left  = 4
                                      bottom right = 8
```

So `0` is open water (the tile is empty), `15` is all land, `3` is land along the top, and so on. The tile numbered `n` is the **n-th frame** of
the shore sheet: column `n % 4`, row `n // 4`, 16 x 16 pixels each.

A tile on the corner between cells `(i-1, j-1)`, `(i, j-1)`, `(i-1, j)` and `(i, j)` is drawn with its top left at `(i * 16 - 8, j * 16 - 8)`,
half a tile up and left, because it sits on the corner and not on a cell. Keep a few cells of water all round the edge of the map, so the
tiles that hang off the edge are all `0` and draw nothing.

```js
// land(x, y) says whether a cell is land; it must say false outside the map.
// shore is the loaded shore sheet, sea the loaded sea sheet (4 frames side by side), frame the current sea frame 0..3.
for (let j = 0; j <= height; j++) {
  for (let i = 0; i <= width; i++) {
    ctx.drawImage(sea, frame * 16, 0, 16, 16, i * 16 - 8, j * 16 - 8, 16, 16);        // the sea under everything
  }
}
for (let j = 0; j <= height; j++) {
  for (let i = 0; i <= width; i++) {
    const n = (land(i - 1, j - 1) ? 1 : 0) | (land(i, j - 1) ? 2 : 0) | (land(i - 1, j) ? 4 : 0) | (land(i, j) ? 8 : 0);
    if (n) ctx.drawImage(shore, (n % 4) * 16, (n >> 2) * 16, 16, 16, i * 16 - 8, j * 16 - 8, 16, 16);
  }
}
```

`example-layout.json` has the example's `land` rows. Draw them this way and you should get `example-grass.png` back (without its routes and pins).
Turn smoothing off (`imageSmoothingEnabled = false`) and scale by whole numbers only.

## Layers, from the bottom

1. **Sea.** One tile, 4 frames, tiled over the whole map. Every sea tile shows the same frame at the same time; play the frames in order at
   **4 frames a second** and loop. It repeats every 16 pixels both ways, so there is no seam.
2. **Shore tiles.** Land with a darker edge, and foam (or the pale shallows, on parchment) on the water side. They are see-through wherever it is open
   water, so the sea shows. They do not animate.
3. **Routes.** Dotted lines from node to node: **2 pixels on, 1 off, 1 pixel wide**, in the skin's route colour (`nodemap.json` > `skins` > `routeDot`).
   Draw them from the middle of one node to the middle of the next, over the land and over any sea between.
4. **Pins.** Stand a pin on each node. Its **anchor is its point** (8, 20 in the 16 x 24 picture): put that on the node's middle,
   `((x + 0.5) * 16, (y + 0.5) * 16)` for a node in cell `(x, y)`. The three colours are only colours; what they mean is up to the app.
5. **Your own node icons** (fights, shops, rests, the boss) go on top. These assets do not include them.

## Making the layout

The shapes the assets were designed for, and what `tools/make_nodemap.py` does (a reference to port, in `make_layout`, `land_cells` and `example`):

- **Floors and lanes.** Floor 0 is at the bottom, the top floor is the boss. A map has some **lanes** across (5 in the example) and some **floors** up (8).
- **Paths.** Start a few paths on different lanes of floor 0 (4 in the example). Each floor a path goes up to the same lane or one to either side, at
  random. Two paths must never cross: do not let one step from lane `a` to `a + 1` if another already steps from `a + 1` to `a` on that floor. Every
  path ends at the one boss node on the top floor.
- **Cells.** Put node `(floor, lane)` at cell `x = margin + lane * 9`, `y = margin + (floors - 1 - floor) * 8`, moved by at most one cell in each direction
  at random so the map is not a grid. `margin` is 8. (`nodemap.json` > `layout` has all these numbers.)
- **Land.** Mark as land every cell within **2.6 to 3.2** cells of a node (**5.0** for the boss), and every cell within **0.78** of the straight
  line between two nodes joined by a path. That gives islands joined by land paths one or two cells wide. For the parchment look you can also draw the dotted
  routes along them. To have separate islands joined only by routes across the sea, leave out the paths' land.
- Then draw it as above. The cells have no other state; the tiles, the sea and the foam all come from the land cells alone.

## Making a new skin

A skin is only colours and textures: the 16 tile shapes are decided by a formula, the same for every skin. In `tools/make_nodemap.py`, add an entry to `BIOMES`
(its land, speck, tuft, bank, sea, glint, wave and foam roles) and to `SKIN_LABELS`, then run `python3 tools/make_assets.py --png-dir sprites/assets`.
Every skin follows the same rules: the texture repeats every 16 pixels (so neighbouring tiles agree), the shore is made from one continuous edge
(so tiles always join), and nothing else changes.

## Rebuilding these files

```bash
python3 tools/make_assets.py --png-dir sprites/assets      # writes this whole folder, and the Node map category on the Assets page
python3 tools/make_nodemap.py --preview previews/nodemap.png   # the 16 tiles of each skin, and a sample map
```

The sheets are generated by code, so change the code and rebuild instead of editing the PNGs.
