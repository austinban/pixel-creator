# Text icons: gold, experience and fight difficulty

Five small icons for the game's text, each **16 x 16**, the size of a line of text, in category **UI** (`tools/make_hud_icons.py`). They are drawn in the shared palette with a one-pixel outline and lit from the upper left, like the rest of the UI art.

| File | What it is | Use it for |
|---|---|---|
| `icon-gold.png` | a little golden mushroom | gold: "Gold 120", prices, "Hire 140" |
| `icon-xp.png` | a four-point star of cyan light | experience points: "45 xp", the bar's label, a reward |
| `icon-skull-green.png` | a green skull | an **easy** fight |
| `icon-skull-yellow.png` | a yellow skull | an **even** fight |
| `icon-skull-red.png` | a red skull | a **hard** fight |

`hud-icons.json` lists the same files. Each file is one 16 x 16 picture, not a sheet, with nothing placed on the map.

## Putting one beside text

- **Draw at whole pixels, at the same scale as the rest of the UI,** with nearest-neighbour scaling (`imageSmoothingEnabled = false`). Do not scale the icon to the text: it is drawn for 16 pixels.
- **Line it up with the text:** centre the icon on the line's middle, or put its bottom row (row 15) on the baseline, whichever sits better with the font; the gold mushroom's stem and the skulls' teeth hang to the bottom rows. Leave **3 to 4 pixels** between the icon and the number.
- **Number first or icon first** is up to you; the icon's outline is dark, so it reads on the panel's dark fill and on the floor.

```js
// draw "120" with the gold icon in front of it, centred on the line at (x, y)
function drawAmount(ctx, icon, text, x, y) {
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(icon, x, y - 8);                       // 16 x 16, centred on the line
  ctx.fillText(text, x + 16 + 4, y);
}
```

## The skulls

- A skull fills **13 x 14** of its 16 x 16 cell, from (1, 1), so a row of them is **14 pixels apart** and a row of three is 40 wide.
- The **colour** says how hard the fight is: green easy, yellow even, red hard. Use the count as well if you like (1 to 3 skulls), all in the same colour for a fight.
- The three skulls are the same picture in three colours, so they swap without anything moving.
- The palette has no pure red: the red skull is coral, salmon and magenta, so it reads as a rose red. It is still clearly the hot one next to the yellow and the green.

## Things to know

- The icons are palette colours, so they recolour with the rest of the art.
- There is one gold icon and one experience icon. If another look is wanted (a coin, a gem, an orb) say so; they were drawn as options and left out.
