# Mushroom trees

Six giant mushrooms for the corrupted lands, to stand where trees would. On the Assets page they are the **Mushroom Trees** category. Each is **one still picture** (a mushroom looks the same from every side, so there is no NE and SE; NW and SW are the picture flipped about the anchor, if you want variety).

| File | What it is | Footprint | Cell | Anchor |
|---|---|---|---|---|
| `fungus-spotted.png` | Spotted toadstool: plum cap, cream spots, a ring on a pale stem | 1 x 1 | 48 x 79 | (24, 67) |
| `fungus-bell.png` | Bell mushroom: slender, deep teal, glowing pores | 1 x 1 | 48 x 83 | (24, 71) |
| `fungus-cluster.png` | Three small purple toadstools together (the lowest, a bush) | 1 x 1 | 48 x 58 | (24, 46) |
| `fungus-puffball.png` | Pale round puffball, plum warts, glowing pores | 1 x 1 | 48 x 48 | (24, 36) |
| `fungus-parasol.png` | Very tall thin stem under a wide flat violet cap, like a canopy | 1 x 1 | 48 x 79 | (24, 67) |
| `fungus-toadstool.png` | **Giant toadstool, walkable**: wide, low, hot pink with cream spots | **2 x 2** | 96 x 80 | (48, 60) |
| `mushroom-trees.json` | Every file, cell, anchor, footprint and the walkable top, for the app to read | | | |

Drawn in the ground tiles' own projection (16 across and 8 down a cell, 16 pixels a level) and the shared palette's colour roles, so it recolours with the rest of the game.

## Placing one

The **anchor is the middle of the footprint on the ground**. For a 1 x 1 that is the middle of its ground tile, where a character stands; for the giant toadstool it is the point where the four tiles meet.
Draw it after the ground and, like a tree, in front of anything behind it and behind anything in front (sort by the anchor's ground position).

```js
const gx = mapOffsetX + 16 * (x - y), gy = mapOffsetY + 8 * (x + y);           // the ground tile's top left (for the 2 x 2, the top-left tile of the four)
ctx.drawImage(sheet, gx + 16 - ax, gy + 8 - ay);                                // a 1 x 1: the anchor (ax, ay) on the tile's middle (16, 8)
// the 2 x 2: the anchor goes on the corner the four tiles share, which is (gx + 32, gy + 16) from the top-left tile's top-left
ctx.drawImage(sheet, gx + 32 - 48, gy + 16 - 60);
```

## What blocks and what can be walked on

The five 1 x 1 mushrooms are obstacles: they block their tile, like a tree or a rock. The **giant toadstool** covers a 2 x 2 block of tiles and **its flat top can be walked on**: it is `walkableTop`
in the json, **level 2** (32 pixels up). Treat its four tiles as a platform two levels above the ground (an ordinary raised tile, reached by stairs, a ramp or a jump); a character standing on it is drawn with its
anchor 32 pixels above the ground point of the tile it stands on, and in front of the toadstool's picture. Underneath, the stem is out of the way, so nothing walks there.

`python3 tools/make_fungi.py --preview previews/fungi.png` shows all six enlarged over their footprints.
