# Menu buttons

Reusable buttons for menus, drawn after the game's main menu: a dark bar in a steel bevel with gold corner brackets, rounded ends, a slab under it for depth, and moss, scratches and chips for wear. They are in category **UI** (`tools/make_buttons.py`), **33 sheets**: 3 colourways by 11 sizes (2 heights by 4 widths, and three small sizes of their own). A button has **no label**: draw your own text over the middle.

Each sheet is **three cells side by side, one per state**: `default`, `hovered`, `active`. A cell is the whole button at its size, so the sheet is three times as wide as a button.

| | Width | Standard (48 high) | Short (32 high) |
|---|---|---|---|
| `sm` | 128 | 128 x 48 | 128 x 32 |
| `md` | 192 | 192 x 48 | 192 x 32 |
| `lg` | 256 | 256 x 48 | 256 x 32 |
| `xl` | 384 | 384 x 48 | 384 x 32 |

Three more sizes of their own, for tight places:

| Size | Cell | Notes |
|---|---|---|
| `short-xs` | 48 x 32 | the short height at 48 wide (body 29 rows, slab 3) |
| `compact-sm` | 112 x 40 | a compact height (body 36 rows, slab 4) |
| `icon-sq` | 36 x 36 | a square for an icon (body 33 rows, slab 3); put the icon on the body |

Buttons under 80 wide are two half-caps that meet in the middle, so they have no repeating middle.

Files are `ui-button-COLOURWAY-HEIGHT-WIDTH.png`, for example `ui-button-red-short-xl.png`: colourway `primary`, `low` (low contrast) or `red`; height `std` or `short`; width `sm`, `md`, `lg` or `xl`. The three extras are `ui-button-COLOURWAY-short-xs`, `-compact-sm` and `-icon-sq`. `buttons.json` lists them with their cell sizes.

## The states

| State | Use it for |
|---|---|
| `default` | The button at rest |
| `hovered` | The pointer is over it, or it has keyboard focus (the bright row of the menu) |
| `active` | The chosen or current item, or the button while it is pressed: dark in a glow |

The wear is the same in all three, so swapping states changes colour and light and nothing jumps.

## The colourways

- **primary**: purple, lighting up blue, with gold brackets and green moss.
- **low**: the same button with its values squeezed together, a quiet one to sit behind a busy screen. The brackets are a dull plum and the moss a deep teal. The three states are close; the glow on `active` is muted.
- **red**: coral, magenta and plum in place of the purple and blue. The palette has no pure red, so it reads raspberry; hovered is a salmon-coral and active a hot magenta. Gold and moss stay.

## Drawing one

```js
const STATES = { default: 0, hovered: 1, active: 2 };
const w = 256, h = 48;                                              // the sheet's cell, from buttons.json
ctx.drawImage(sheet, STATES[state] * w, 0, w, h, x, y, w, h);       // then draw the label over it, centred on (x + w / 2, y + 22)
```

The body of a standard button is its top **44 rows** and the slab under it the last 4 (short: 29 and 3), so centre a label on the body, not on the whole cell. Pick the nearest size and do not stretch a button: the corners, brackets and moss are drawn for their height. For a width that is none of the four, use the next one up and clip it, or ask for another.
