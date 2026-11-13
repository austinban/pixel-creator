# Settings controls: slider and toggle

A volume-style **slider** and an on/off **toggle**, in category **UI** (`tools/make_ui_controls.py`), to sit beside the buttons and the panel: the same dark steel bevel, a little moss on the top edge, a gold bead. All pieces are plain 1x PNGs; draw them at the same whole-number scale as the rest of the UI with nearest-neighbour scaling. `ui-controls.json` lists the numbers below.

## Slider

Three layers, back to front: the **track**, the **fill**, the **knob**.

| File | Size | What it is |
|---|---|---|
| `ui-slider-track-left.png` | 8 x 16 | the track's left end |
| `ui-slider-track-mid.png` | 32 x 16 | the middle; **it wraps**, so any number in a row join with no seam (cut the last one short) |
| `ui-slider-track-right.png` | 8 x 16 | the track's right end |
| `ui-slider-fill-left.png` | 8 x 16 | the fill's rounded left end |
| `ui-slider-fill-mid.png` | 32 x 16 | the fill's middle; it wraps too |
| `ui-slider-knob-default.png` | 24 x 24 | the knob |
| `ui-slider-knob-hovered.png` | 24 x 24 | cyan bead, lighter rim (mouse over, or focused) |
| `ui-slider-knob-pressed.png` | 24 x 24 | darker, bead glowing (being dragged) |

Build it for a track of width `W` (at least 16 + the knob):

1. Draw the track at `(x, y)`: left cap, as many middles as fill `W - 16` (the last one cut short), right cap.
2. Let `fx = (W - 24) * value + 12` for a value from 0 to 1 (the knob's centre). Draw the fill at the same `(x, y)`, **cut at `fx`**: the left cap, then middles until `fx` (the last one cut short). The fill is drawn on the track at the **same position**; its own 3-pixel inset leaves the track's frame showing.
3. Draw the knob with its centre at `(x + fx, y + 8)`, so it sits on the track's middle. It covers the fill's cut end, so the cut needs no end piece.

The knob is 24 high and the track 16, so the knob stands 4 pixels proud above and below. The hit area is the knob's 24 x 24 (or the whole track, as you like).

```js
// a slider of width W at (x, y), value 0..1; images are the loaded PNGs
function drawSlider(ctx, im, x, y, W, value, knobState) {
  ctx.imageSmoothingEnabled = false;
  const strip = (left, mid, right, to) => {                // right is null for the fill
    ctx.drawImage(left, x, y);
    for (let dx = 8; dx < to; dx += 32) {
      const w = Math.min(32, to - dx);
      ctx.drawImage(mid, 0, 0, w, 16, x + dx, y, w, 16);
    }
    if (right) ctx.drawImage(right, x + W - 8, y);
  };
  strip(im.trackLeft, im.trackMid, im.trackRight, W - 8);
  const fx = (W - 24) * value + 12;
  strip(im.fillLeft, im.fillMid, null, Math.max(8, fx));
  ctx.drawImage(im['knob' + knobState], x + fx - 12, y - 4);
}
```

## Toggle

Four whole pictures, each **44 x 22**, no layers to build:

| File | State |
|---|---|
| `ui-toggle-off.png` | off: a dark trough, the knob at the left with a dull plum bead |
| `ui-toggle-off-hovered.png` | off, with the mouse over it or focused: a lighter frame |
| `ui-toggle-on.png` | on: the lit blue trough, the knob at the right with a gold bead |
| `ui-toggle-on-hovered.png` | on, with the mouse over it or focused |

The knob does not move between them; swap the picture, or fade between two if you want it smooth. Put it at the right end of a row, like the one in the settings screen. The toggle has no pressed picture: use the hovered one while the button is down.

## Things to know

- Palette colours only, so they recolour with the rest of the art.
- The moss is in the same place in every state, so a swap does not make it jump.
- All the pieces are separate files, not sheets, with nothing placed on the map. The corners at each end of the track and the toggle are transparent.
