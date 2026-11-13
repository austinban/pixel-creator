# Menu panel

A frame that replaces the plain dark box behind a screen's text. It matches the buttons (`../buttons/`): dark ink in a steel bevel with gold corner brackets, rounded corners, a slab under it for depth, and moss on the top edge, with **mushrooms** growing off the top corners and **vines** creeping along the frame and hanging into the panel. It is in category **UI** (`tools/make_panel.py`), made of **nine pieces that join** (a nine-slice) so it can be any size from 80 x 80 up. The top edge comes in **six pictures** that you mix at random so a long panel does not repeat. It has **no text**: draw your own over the fill.

## The pieces

```
TL  T  TR        T is any of six pictures: T, T2, T3, T4, T5, T6
L   C  R
BL  B  BR
```

| File | Piece | Picture size | Notes |
|---|---|---|---|
| `ui-panel-tl.png` | top left corner | 40 x 54 | the pink mushroom cluster; 14 rows of mushroom above the body, then 40 of body |
| `ui-panel-t.png` | top edge, **vines** | 64 x 54 | **wraps left to right**; five vines hanging in: the busy one |
| `ui-panel-t2.png` | top edge, **mossy** | 64 x 54 | extra moss on the steel and two short roots: the calm one |
| `ui-panel-t3.png` | top edge, **mushrooms** | 64 x 54 | four small pink and teal mushrooms on the edge |
| `ui-panel-t4.png` | top edge, **one vine** | 64 x 54 | one long vine, a short one, and a vine crawling along the steel |
| `ui-panel-t5.png` | top edge, **big caps** | 64 x 54 | two big cap mushrooms, pink and teal, and a sprout |
| `ui-panel-t6.png` | top edge, **glow-worms** | 64 x 54 | four thin teal threads with a bright bead on the end, and two tiny teal mushrooms |
| `ui-panel-tr.png` | top right corner | 40 x 54 | the glowing teal mushrooms |
| `ui-panel-l.png` | left edge | 40 x 64 | **wraps top to bottom** |
| `ui-panel-c.png` | fill | 64 x 64 | **wraps both ways** |
| `ui-panel-r.png` | right edge | 40 x 64 | **wraps top to bottom** |
| `ui-panel-bl.png` | bottom left corner | 40 x 44 | teal mushrooms inside the corner; 40 of body, then 4 of slab |
| `ui-panel-b.png` | bottom edge | 64 x 44 | **wraps left to right**; 40 of body, then 4 of slab |
| `ui-panel-br.png` | bottom right corner | 40 x 44 | a vine over the corner |
| `ui-panel.png` | ready-made | 320 x 138 | the whole panel at one size (body 320 x 120), for when you do not need another |

`panel.json` lists the same numbers, the six top edges (`top_edges`) and how often to pick each (`top_edge_weights`). Draw with nearest-neighbour scaling off (`imageSmoothingEnabled = false`) and at whole-pixel positions.

## What the numbers mean

- **The body** is the rectangle the panel covers, the old box's rectangle: `w` x `h`, both at least **80**. Corners are **40 x 40** of body (the `SLICE`).
- **Above the body** the top row has **14 extra rows** (`PAD`): the mushrooms rise over the edge. Draw the top row 14 rows above the body's top.
- **Below the body** the bottom row has **4 extra rows** (`SLAB`): the depth under the frame. The panel's whole picture is therefore `w` x (14 + `h` + 4).
- **Wrap.** The edges and the fill are 64 long and join themselves with no seam: draw as many as fit and **cut the last one short** (take its first columns or rows). The moss, drips and wear carry on across every join, so a long panel does not repeat in steps.
- **The six top edges join each other.** They share the moss hem and are identical in their first and last 4 columns, so any one can follow any other, in any order, with no seam. `test_families.py` checks every one.

## Choosing the top edges

Pick one of the six for each 64-wide run of the top edge, **at random, but the same every time the panel is drawn** (a pick that changes every frame flickers). Seed it with something that stays put: the panel's id or its position, and the run's number. Use the weights in `panel.json` so the busy picture comes up least:

| Piece | Weight |
|---|---|
| `t` vines | 0.12 |
| `t2` mossy | 0.28 |
| `t3` mushrooms | 0.20 |
| `t4` one vine | 0.15 |
| `t5` big caps | 0.13 |
| `t6` glow-worms | 0.12 |

And **do not repeat the same picture twice in a row**; if the pick matches the last one, pick again.

## Drawing one

```js
// x, y, w, h: the BODY, the rectangle the old black box was. w and h at least 80.
// p.tl, p.tr, p.l, p.c, p.r, p.bl, p.b, p.br, and p.tops = [t, t2, t3, t4, t5, t6]: the images of ui-panel-PIECE.png.
// seed: any number that stays the same for this panel (its id hashed, say), so its top edge does not change from frame to frame.
const SLICE = 40, WRAP = 64, PAD = 14;
const TOP_WEIGHTS = [0.12, 0.28, 0.20, 0.15, 0.13, 0.12];            // t, t2 ... t6 (also in panel.json)

function rng(seed) {                                                // a small repeatable random number generator (mulberry32)
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function pickTops(runs, seed) {                                     // which top edge each run uses: weighted, never the same twice in a row
  const next = rng(seed), picks = [];
  for (let i = 0; i < runs; i++) {
    let k;
    do {
      let x = next(); k = TOP_WEIGHTS.length - 1;
      for (let j = 0; j < TOP_WEIGHTS.length; j++) { if (x < TOP_WEIGHTS[j]) { k = j; break; } x -= TOP_WEIGHTS[j]; }
    } while (i > 0 && k === picks[i - 1]);
    picks.push(k);
  }
  return picks;
}

function drawPanel(ctx, p, x, y, w, h, seed = 1) {
  ctx.imageSmoothingEnabled = false;
  const iw = w - 2 * SLICE, ih = h - 2 * SLICE;
  const run = (img, n, vertical, dx, dy) => {                        // an edge or the fill, repeated, the last one cut short
    for (let k = 0; k < n; k += WRAP) {
      const cut = Math.min(WRAP, n - k);
      vertical ? ctx.drawImage(img, 0, 0, img.width, cut, dx, dy + k, img.width, cut)
               : ctx.drawImage(img, 0, 0, cut, img.height, dx + k, dy, cut, img.height);
    }
  };
  // top row: PAD rows above the body; each run of the top edge is one of the six pictures
  ctx.drawImage(p.tl, x, y - PAD);
  const picks = pickTops(Math.ceil(iw / WRAP), seed);
  picks.forEach((k, i) => {
    const cut = Math.min(WRAP, iw - i * WRAP), img = p.tops[k];
    ctx.drawImage(img, 0, 0, cut, img.height, x + SLICE + i * WRAP, y - PAD, cut, img.height);
  });
  ctx.drawImage(p.tr, x + w - SLICE, y - PAD);
  // middle: the left and right edges, and the fill between them (wrapping both ways)
  run(p.l, ih, true, x, y + SLICE);
  run(p.r, ih, true, x + w - SLICE, y + SLICE);
  for (let k = 0; k < ih; k += WRAP) {
    const cut = Math.min(WRAP, ih - k);
    for (let j = 0; j < iw; j += WRAP) {
      const cw = Math.min(WRAP, iw - j);
      ctx.drawImage(p.c, 0, 0, cw, cut, x + SLICE + j, y + SLICE + k, cw, cut);
    }
  }
  // bottom row: starts SLICE rows above the body's bottom; its last 4 rows are the slab
  ctx.drawImage(p.bl, x, y + h - SLICE);
  run(p.b, iw, false, x + SLICE, y + h - SLICE);
  ctx.drawImage(p.br, x + w - SLICE, y + h - SLICE);
}
```

Work out `pickTops` once when the panel is made (or when its size changes) and keep the result, rather than every frame. In an engine with nine-patch nodes (Godot's `NinePatchRect`) the top and bottom rows are taller than the corners of the middle, and the top edge is six pictures, so use separate sprites or textures placed as above rather than one patch texture.

## Where to put text

The fill is a flat dark eggplant with a few grape flecks, darker near the frame, so light text reads on all of it. Keep text clear of the decorations:

- **Left and right:** inset **10** from the body's edge (the steel is 5 thick plus its outline, and the gold brackets reach 18 along each edge at the corners).
- **Top:** the vines and threads hang into the panel from the top edge, down to **28** rows (the long vine in `t4`; the others are shorter), thin and in a few places. Inset text **12** for a quiet look, or **30** to keep it fully clear; a vine crossing a letter is part of the look and not a bug.
- **Bottom:** inset **10**. Keep the **bottom left 34 x 18** free: there is a cluster of glowing mushrooms there.
- **Top edge:** the mushrooms sit above the body (in the PAD) and on its top edge, so they only overlap content if you draw something there.

## Things to know

- The fill is **opaque**. If you want the screen to show through, draw the panel and then your own tinted overlay, or ask for a translucent variant.
- There is **one colourway** (the purple, like the primary buttons). More (low contrast, red) can be made the way the buttons' were.
- The pieces are drawn for their size: do not scale them. For a size other than the pieces make, change `w` and `h`.
- The corners are fixed: mushrooms on the **top corners and the bottom left**, a vine on the **top left and bottom right**. Only the top edge varies. To show a panel without mushrooms (a small panel under a button, say) ask for a plain set.
- A panel under about 200 wide has only a run or two of top edge, so it will look the same every time for the same seed. Change the seed to change it.
