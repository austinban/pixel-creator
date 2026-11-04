# Buildings

A kit of building tiles for the isometric ground: walls, doors, windows, roofs, towers and spires, worn and overgrown versions of them,
and a few extras. They are not finished buildings. They are one-cell pieces you **stack and set side by side** to make any house, tower or whole street.
Everything for them is in this folder and shares the `bld-` prefix. On the Assets page it is the **Buildings** category.

| File | What it is |
|---|---|
| `bld-stone-wall.png`, `bld-timber-wall.png` | Wall blocks: plain, windows, doors, arrow slits, belfry and gate arches, a battlement |
| `bld-stone-wall-aged.png`, `bld-timber-wall-aged.png` | The same walls worn, holed, mossy, overgrown with vines, or ruined |
| `bld-roof-terracotta.png`, `bld-roof-slate.png`, `bld-roof-teal.png` | Roof pieces: front slope, back slope, hip slope, hip corner |
| `bld-roof-*-aged.png` | The same roofs mossy, and with tiles missing |
| `bld-extras.png` | Chimney, pinnacle, rubble |
| `bld-spires.png` | Dark and teal spires, which are two levels tall |
| `buildings.json` | Every piece, which sheet and frame it is on, and the rules below in numbers: for the app to read |
| `example-street.png`, `example-street.json` | A street built only from these pieces (the buildings alone, on transparent), and the list of pieces that makes it |

## The grid

Everything lives on the same cells as the ground tiles. A **cell** is one ground tile; moving one cell along either grid axis moves the picture
**16 pixels across and 8 down**. A **level** is one piece's height: **16 pixels**. A piece is a 32 x 32 cube, the same size and projection as a ground tile.
A **storey** of a building is **two levels**, so a door is two pieces (a lower and an upper), and a window sits in the upper level of its storey.

Two axes: x runs down and to the right (SE), y down and to the left (SW), as the terrain page draws them. The camera sees the **right wall** (the one at the
largest x of a building), the **left wall** (the largest y) and the top.

### Placing a piece

A piece at cell `(x, y)` and level `k` (0 stands on the ground tile of that cell, 1 on the piece below it, and so on) is drawn with its **top left at**

```
left = gx
top  = gy - 16 * (k + levels)
```

where `(gx, gy)` is the top left of that cell's **ground tile** as you draw it (`16 * (x - y)` and `8 * (x + y)`, plus the map's own offset), and `levels` is
1 for the 32 x 32 pieces and 2 for the spires (32 x 48). Draw the whole ground first, then the pieces **sorted by `x + y`, then by level**, so a piece in front covers the
ones behind it:

```js
pieces.sort((a, b) => (a.x + a.y) - (b.x + b.y) || a.k - b.k);
for (const p of pieces) {
  const info = buildings.pieces[p.id];                       // from buildings.json
  const sheet = images[info.sheet], [cw, ch] = buildings.sheets[info.sheet].cell;
  const gx = mapOffsetX + 16 * (p.x - p.y), gy = mapOffsetY + 8 * (p.x + p.y);      // the cell's ground tile
  ctx.drawImage(sheet, info.col * cw, info.row * ch, cw, ch, gx, gy - 16 * (p.k + info.levels), cw, ch);
}
```

The pieces assume the ground under them is a **full-height cube tile** (a flat top at the standard height). The half-height and sloped tiles are not for building on.

## NE and SE

Every piece is drawn twice, like the characters and the bridge. In a sheet each piece is its **NE** picture followed by its **SE** picture (the frame is `col + row * 8`, and
`buildings.json` has the column and row for each id).

- **NE**: the feature (a window, a door, vines, a crack) is on the wall that runs NE-SW, which is the **right-hand wall** as the camera sees it. A roof slope or ridge that runs that way.
- **SE**: the feature is on the wall that runs NW-SE, the **left-hand wall**. A roof slope or ridge that runs that way.
- A piece that does not have a direction (a plain block, a corner, a spire, a chimney) is the **same picture** in both, so you can always ask for either.
- **NW and SW** are the NE and SE pictures **flipped left to right**, as for the characters. A flipped piece is a mirror image, so its lit and shaded walls swap: it will not match the light on the unflipped pieces beside it. Use NE and SE for everything the camera shows, and flips only where you must face the other way.

Ids are `NAME-ne` and `NAME-se`: `stone-window-ne`, `timber-door-low-se`, `roof-tile-slope-se`. `buildings.json` > `pieces` lists them all.

## Making a building

**Walls.** Fill the cells along the two walls the camera can see. A cell at the largest x shows its **right wall**: use the **NE** piece for it. A cell at the largest y shows its
**left wall**: use the **SE** piece. The front corner shows both: use a `corner-` piece (`stone-corner-window`, `stone-corner-open`, `stone-corner-slit`, `timber-corner-window`, or
`-corner-vines`), or any plain block. The cells inside and behind are never seen and need no pieces. Stack a storey as two levels.

**Doors.** A door is `NAME-door-low` (level 0) with `NAME-door-up` (level 1, with the arch) above it, on the same wall. A gateway through a thick wall is `stone-gate` (one level).

**Windows.** `NAME-window` in the upper level of a storey, in the cells you want them. `NAME-window-vines` is the same with vines round it.

**Roofs.** Put the roof on top of the walls, at level `2 * storeys`. A roof is **two cells deep**, with the ridge between them, and rises one level over one cell:

- a ridge along the x axis (runs NW-SE, the front slope faces the left wall): the front row of cells is `roof-STYLE-slope-se`, the row behind it `roof-STYLE-back-se`
- a ridge along the y axis (runs NE-SW, the front slope faces the right wall): the front column is `roof-STYLE-slope-ne`, the column behind it `roof-STYLE-back-ne`
- the **back slope** is mostly hidden: it is there for the gable end that shows at the end of the ridge
- a **hip roof** over a square: the front corner is `roof-STYLE-corner`, the cell beside it on the right `roof-STYLE-hip-ne`, the cell beside it on the left `roof-STYLE-hip-se`; the cell behind is never seen
- a gable end shows at the end of the ridge, so put a wall block under it there (timber plaster under terracotta, stone under slate and teal: they match)
- `STYLE` is `tile` (terracotta), `slate` or `teal`

**Towers and spires.** A tower is stone wall pieces stacked as high as you like. A 1 x 1 tower takes `spire-dark` or `spire-teal` (two levels) on top, and `pinnacle` can stand at its corners.
A 2 x 2 tower takes a hip roof. Belfry arches are `stone-open` and `stone-corner-open`; arrow slits are `stone-slit` and `stone-corner-slit`.

**Extras.** A `chimney` stands on the back slope of a roof, at the level the roof starts. `rubble` goes on the ground in front of anything that has fallen.

## Breaking up the sameness

The worn, holed, mossy, vine-covered and ruined pieces are drop-in replacements for the plain ones. Use them to age a building:

- swap some plain blocks for **worn**, **mossy**, **hole** (or **peeled** on timber), keeping them in runs and patches, not evenly
- **vines** grow up from the ground (`NAME-vines`, `-corner-vines`) and **hang** from above (`NAME-vines-hang`); `NAME-vines-heavy` covers a block; the vine stems line up between a block and the one above it, so a vine rises through a stack
- **ruined** is a wall broken off along its top: nothing goes above it, and the roof above is taken away too
- roofs: `-mossy` and `-broken` versions of the slope, hip and corner pieces
- the kit's `Town.weather()` and `Town.ruin()` in `tools/make_buildings.py` do exactly this and are a reference to port

## The example street

`example-street.png` is a street made only of these pieces (no ground in it, so the ground tiles are not repeated here). `example-street.json` is the list of pieces
`[x, y, level, id]` that makes it, with `cellOrigin`, the top left of the ground tile of cell (0, 0) in the picture. Draw the list the way this README says over a transparent
picture and you get `example-street.png` back, pixel for pixel. That makes it the check for your own drawing code.

## Colour

The pieces are painted in the shared palette's roles, like everything else. They use the **quieter** roles on purpose (cream, sand, steel, lavender, plum, grape, deep teal) so they do not fight the
brighter ground, and recolour with the hue sliders as the ground does.

## Rebuilding these files

```bash
python3 tools/make_assets.py --png-dir sprites/assets        # writes this whole folder, and the Buildings category on the Assets page
python3 tools/make_buildings.py --kit previews/building-kit.png --city previews/building-city.png      # look at the kit and a street
```

The sheets are generated by code (`tools/buildings.py` is the renderer and `tools/make_buildings.py` the kit), so change the code and rebuild instead of editing the PNGs.
A new piece is one `add(...)` line in `make_buildings.py`; textures repeat every 16 pixels so it will line up with its neighbours.
