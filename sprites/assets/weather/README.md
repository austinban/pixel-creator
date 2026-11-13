# Weather and fog: looping screen overlays and rain decals

Nine **looping overlays** (category **Weather**) that the game lays over a whole battle, and three small **rain decals** (category **Decals**) that play where a drop lands. All made by `tools/make_weather.py`, in the shared palette, and all of it **opaque pixels**: softness comes from a dither of a smooth field in two or three tones, and from the game drawing the whole layer at an **opacity**. `weather.json` lists every file with the numbers below (its `scroll_px_per_second` is the scroll column). Nothing is placed on the map.

## The overlays

Each overlay is one **sheet** of frames, read left to right and then down, **8 frames to a row** (so a 12 frame sheet is 8 on the first row and 4 on the second). Every frame is **one tile**, and the tile **repeats seamlessly across the screen in both directions**, and the **last frame runs straight into the first** (the tests check both).

| File | Tile | Frames | fps | Blend | Opacity | Scroll (px/s, x y) | What it is |
|---|---|---|---|---|---|---|---|
| `weather-rain-light.png` | 128 x 128 | 8 | 12 | normal | 0.35 to 0.60 | none | a few short streaks falling down and to the left |
| `weather-rain-heavy.png` | 128 x 128 | 8 | 12 | normal | 0.50 to 0.85 | none | many longer streaks, the near ones two wide |
| `weather-rain-ripples.png` | 128 x 128 | 8 | 8 | normal | 0.45 to 0.90 | none | flat rings opening on the ground: **for the ground layer** |
| `weather-fog-light.png` | 128 x 128 | 12 | 6 | normal | 0.25 to 0.50 | 6, 2 | thin drifting banks (about a sixth of the tile) |
| `weather-fog-dense.png` | 128 x 128 | 12 | 6 | normal | 0.40 to 0.70 | 4, 1 | thick banks (about a third) |
| `weather-spore-haze.png` | 128 x 128 | 12 | 8 | **add** | 0.50 to 1.00 | -3, -2 | lime, mint and magenta spores over a faint green haze |
| `weather-embers.png` | 128 x 128 | 12 | 10 | **add** | 0.60 to 1.00 | none | embers and ash rising and swaying |
| `weather-petals.png` | 128 x 128 | 12 | 8 | normal | 0.80 to 1.00 | -8, 0 | petals and a few leaves falling and fluttering |
| `weather-mist-low.png` | **128 x 64** | 12 | 6 | normal | 0.30 to 0.60 | 5, 0 | flat bands of mist, thickest across the middle of the tile: for water and graves |

**Scroll** is a drift the **game** adds: move the repeating tile by that many **screen pixels a second** (x to the right, y down; use whole pixels a step). A **falling or rising** overlay (the rain, embers and petals) moves by its own frames and needs no scroll; the petals also drift sideways at 8 pixels a second. A **field** (fog, haze, mist) only billows in place in its frames, so without the scroll it would not travel. **Opacity** is the range to draw the whole layer at, from a thin day to a heavy one; set it from the weather's strength.

## Drawing one

- **In screen space, not the world.** Repeat the tile over the whole view (a tiled sprite, or a texture with repeat on) so it does not move when the camera does.
- **Above the map and its props and below the UI**, so it never greys the menus. The exception is `weather-rain-ripples`: it lies flat on the ground, so draw it **under units and props**, over the ground only.
- **Play the frames at `fps`**, looping, with whole-pixel steps. Do not smooth the pixels (`nearest`), or the dither turns to mush.
- **Opacity multiplies the dither.** The pixels are opaque, so the layer's alpha is what makes it soft: draw the whole layer at an opacity in the range above, never per pixel.
- **Blend `add`** is for light that should glow on a dark map (spore haze, embers; their roles are bright and saturated). A game with no additive blend can draw them `normal` at the high end of the range.
- A `128 x 64` tile (the low mist) repeats in the same way; it is a strip, so lay it as bands across the water or the graves, not over the whole view, unless you want a bank of mist.

```js
// a looping, repeating overlay: frame `f` of a sheet (8 to a row), tiled over the view and drifting by its scroll
function drawWeather(ctx, sheet, o, f, t, view) {
  const col = f % 8, row = Math.floor(f / 8);
  const [tw, th] = o.tile, dx = (o.scroll[0] * t) % tw, dy = (o.scroll[1] * t) % th;
  ctx.globalAlpha = o.opacity;                        // somewhere in o's range; the whole layer
  ctx.globalCompositeOperation = o.blend === 'add' ? 'lighter' : 'source-over';
  ctx.imageSmoothingEnabled = false;
  for (let y = -th + dy; y < view.h; y += th)
    for (let x = -tw + dx; x < view.w; x += tw)
      ctx.drawImage(sheet, col * tw, row * th, tw, th, Math.round(x), Math.round(y), tw, th);
}
```

## Which overlay goes with which set

The sets (`sprites/assets/sets/README.md`) say what a place looks like; weather says what it is doing. These suit them:

| Weather | Suits | Not for |
|---|---|---|
| `rain-light`, `rain-heavy`, `rain-ripples` | meadow, riverbank, highland, market town, fallen town and the marsh, on day and dusk maps | the corrupted sets look best with haze first; rain on top is fine at the low end |
| `mist-low` | riverbank, sunken marsh, gravemoor (water and graves) | an open battlefield: it reads as a bank, not weather |
| `fog-light`, `fog-dense` | dawn and dusk on any set; gravemoor and highland at night | a day map at full opacity: it greys the colours |
| `spore-haze` | **corrupted ground only**: spore hollow, sunken marsh, gravemoor | a plain-ground set (the colours are the corruption's) |
| `embers` | fallen town, gravemoor, any map with fire | a meadow |
| `petals` | meadow, riverbank, market town (day) | night maps and corrupted ground |

Only one of the **falling** kinds (rain, embers, petals) at a time, plus at most one **field** (fog, haze or mist) under it.

## The rain decals

Three small animations, **4 frames at 8 fps**, played **once** at the point a drop lands, on a tile the game picks at random (a handful a second in rain), then removed. They have no outline. Draw them on the ground, under units and props, on the cell's top face:

| File | Size | Anchor | For |
|---|---|---|---|
| `weather-ripple-water.png` | 32 x 16 | (16, 8) | two rings opening: on water |
| `weather-ripple-ground.png` | 32 x 16 | (16, 8) | one small ring: on dirt, stone and grass |
| `weather-splash.png` | 32 x 24 | (16, 16) | a ring and a crown of drops: on stone and anything hard |

The anchor is the point on the ground the decal is placed from (the middle of the tile's top face). The sheets are the frames in one row.

## Things to know

- The fog is soft **round banks**, not long wisps, and the light fog shows as distinct discs; use it at the higher end of its opacity, or lay `fog-dense` thin.
- The **embers and petals are single small specks**: they only read at an opacity of **0.8 or more**. The **light rain** is thin (about 1 percent of the tile) and faint below an opacity of about **0.4**.
- The splash's drops are single pixels, so they read as dots, not droplets; the water ripple's last frame is cut flat at the top and bottom by the tile's diamond.
- The 12 frame overlays move about **10 pixels a frame** (the embers and petals about 85 pixels a second at 8 fps): below about **6 fps** they look choppy.
- `Weather` is a new category (the Assets page lists categories from `assets/data.js`, so it appears by itself); `Decals` now holds the blood pool and these three.
- Everything is palette colours (`p q r` for the rain, fog and mist; the corruption's greens and magentas for the haze; embers `a b d g l p`; petals `A C c e f z`), so it recolours with the rest of the art.
