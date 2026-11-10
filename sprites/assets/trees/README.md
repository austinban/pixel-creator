# Trees

Ten more trees and bushes to stand beside the ground sheet's round bush and pine, in the **Trees** category, four of them tall (the sheet's pine is 64 px; these go up to about 128 px). Each is **one still picture**: a tree looks the same from every side, so there is no NE and SE (NW and SW are the picture flipped about the anchor, if you want variety). They are drawn in the ground tiles' own projection and the shared palette's roles, so they recolour with the rest of the game.

| File | What it is | Cell | Anchor | Height (levels) |
|---|---|---|---|---|
| `tree-tall-pine.png` | Tall pine | 48 x 125 | (24, 113) | 6.4 |
| `tree-spruce.png` | Spruce | 48 x 118 | (24, 106) | 6 |
| `tree-poplar.png` | Poplar | 48 x 123 | (24, 111) | 6.3 |
| `tree-tall-oak.png` | Tall oak | 64 x 128 | (32, 116) | 6.6 |
| `tree-broad-oak.png` | Broad oak | 64 x 78 | (32, 66) | 3.5 |
| `tree-birch.png` | Birch | 48 x 107 | (24, 95) | 5.3 |
| `tree-small-pine.png` | Small pine | 48 x 53 | (24, 41) | 1.9 |
| `tree-dead-tree.png` | Dead tree | 64 x 88 | (32, 76) | 4.1 |
| `bush-berry-bush.png` | Berry bush | 48 x 43 | (24, 31) | 1.3 |
| `bush-hedge.png` | Hedge | 64 x 38 | (32, 26) | 1 |
| `trees.json` | Every file, cell, anchor and height, for the app to read | | | |

## Placing one

The **anchor is the middle of its 1 x 1 footprint on the ground**: the middle of the ground tile, where a character stands. A tree is wider and taller than the tile, so draw it after the ground and in the same back-to-front pass as units and props: sort by the anchor's ground position (a tree in front of a unit hides its feet, a unit in front hides the trunk).

```js
const gx = mapOffsetX + 16 * (x - y), gy = mapOffsetY + 8 * (x + y);      // the ground tile's top left
ctx.drawImage(sheet, gx + 16 - ax, gy + 8 - ay);                           // the anchor (ax, ay) on the tile's middle (16, 8)
```

## What blocks

Every one **blocks its tile** (trunk, bush or hedge: nothing walks through, nothing stands on it). The crown is above head height for the tall ones, so it does not block anything else, but a unit behind a tall crown is hidden by it, so keep a unit's tile out of the crown's shadow if you want it visible, or fade the crown.

They come from `tools/make_trees.py` (`--preview` shows them enlarged beside the sheet's bush and pine); do not edit the PNGs.
