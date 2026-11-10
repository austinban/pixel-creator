# The All Tree

The victory screen's display piece: a massive, ancient tree being corrupted by the mushrooms. It is **one picture for one screen**, not a map object, in the **Victory Screen** category.

| File | What it is |
|---|---|
| `all-tree.png` | The loop: 12 frames, 8 across and 2 down, 10 a second. Each frame is 384 x 448 |
| `all-tree-still.png` | The same tree, one flat picture (384 x 448), for a screen that does not animate |
| `all-tree.json` | The cell, anchor, frame count and footprint, for the app to read |

**Size.** Its base is **10 x 10 ground tiles**: a 320 x 160 pixel diamond in the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level). It rises **20 levels (320 pixels)** and goes on up: the picture is **cropped by its top edge**, so the trunk and the great boughs run out of view.

**Anchor.** (192, 336): the middle of the base on the ground. Put it on the middle of a 10 x 10 patch of ground and the roots lie on it. The cell is 384 x 448, so there are 32 pixels of margin each side of the diamond and 112 below the anchor.

**The animation.** Everything loops on a period that divides 12, so frame 12 flows into frame 1. The bark and the silhouette hold still; the fungi, caps, vines, thorns and the glowing eyes in the hollow pulse brighter and darker in a slow wave that climbs from the roots, a few sparkles flash on the bark, spore motes drift up beside the canopy, and glowing drops form under the fungi, boughs and hanging vines, fall and splash. Play it from frame 1 at 10 a second, looping, with nearest-neighbour scaling.

**Using it.** Draw it once, behind the victory text and anything in front of it, as big as the screen allows in whole-number scales. It is a display piece: it blocks nothing and has no walkable top. Its roots and the corrupted ground in its base diamond are painted in, so it does not need a ground under it.

It comes from `tools/make_all_tree.py` (`--preview` shows it over its footprint, `--gif` the loop); do not edit the PNGs.

## The wide version

`all-tree-wide` (the loop) and `all-tree-wide-still` are the same corrupted tree on a **704 x 448** canvas, so the great boughs and their foliage are **not cut off** by the sides, as they are in the 384-wide picture. The anchor is **(352, 336)**, the middle of the wider canvas and of the same 10 x 10 base, so the trunk, roots and boughs sit in the same places relative to it, and the middle of the picture is the same as the narrow one (the narrow picture's column x is the wide one's x + 160). The top edge still crops the tree. The loop is 12 frames at 10 a second, 8 across and 2 down, in `all-tree-wide.png`; the still is `all-tree-wide-still.png`. The extra width is a small amount of extra sky with a few more drops, leaves or fairies on the sides. The corrupted and the autumn wide pictures share the same width, so they swap like the narrow ones.

Use the narrow picture where the screen is narrow or the cut-off sides do not matter, and the wide one where the tree should spread to its full width. They are all in `all-tree.json`.
