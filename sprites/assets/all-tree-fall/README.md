# The All Tree (autumn)

The victory screen's display piece in its **healthy** form: the same massive ancient tree as `all-tree`, with **no mushrooms and no corruption**, in yellow, orange and red autumn foliage, with natural green vines and a few small glowing fairies drifting round it. Category **Victory Screen**.

| File | What it is |
|---|---|
| `all-tree-fall.png` | The loop: 12 frames, 8 across and 2 down, 10 a second. Each frame is 384 x 448 |
| `all-tree-fall-still.png` | The same tree, one flat picture (384 x 448) |
| `all-tree-fall.json` | The cell, anchor, frame count and footprint, for the app to read |

**It is the same tree as `all-tree`:** the same cell (**384 x 448**), the same **anchor (192, 336)** (the middle of the **10 x 10 tile** base on the ground), and the trunk, roots, hollow and boughs are in **exactly the same places**, so a screen can swap one for the other (for example, the corrupted tree for a victory, the autumn tree for what is saved) without moving anything. The tree rises 20 levels and is cropped by the top edge, so it runs out of view.

**The animation.** Everything loops on a period that divides 12, so frame 12 flows into frame 1. The trunk holds still; the leaf clusters shimmer brighter and darker in a slow wave, some leaves drift down and sway, the fairies flit on looping paths in front of and behind the tree, and glowing halos pulse round them. Play it from frame 1 at 10 a second, looping, with nearest-neighbour scaling.

**Using it.** Draw it once as a display piece, in whole-number scales. It blocks nothing and has no walkable top. Its ground (green turf, soil and fallen leaves) is painted in, so it needs no ground under it.

It comes from `tools/make_all_tree_fall.py` (`--preview` shows it over its footprint, `--gif` the loop), which reuses the corrupted tree's model; do not edit the PNGs.
