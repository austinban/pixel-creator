# Bridges

How the rickety bridge works and the rules for laying it: which piece goes where, in what order, facing which way. The art is made by `tools/make_bridge.py`; the working example of the rules is `makeBridge()` in `terrain.js` (try it on `terrain.html`, "Bridge across the water").

## What a bridge is

A bridge spans a straight run of **water** between two pieces of **land**. It is drawn **on the water cells**, not on the land: the land at each end stays an ordinary ground tile, and the bridge's first and last cell are slopes that join it to a deck hanging a few pixels lower.

It is **one asset**, `bridge` (category **Bridges**), with **four frames**, each a **32 x 40** cell:

| Frame | Name | What it is |
|---|---|---|
| 0 | Flat NE-SW | A flat section running along the NE-SW axis |
| 1 | Flat NW-SE | A flat section running along the NW-SE axis |
| 2 | Slope down NE | A slope: **high at the SW edge** (land level), **low at the NE edge** (deck level) |
| 3 | Slope down SE | A slope: **high at the NW edge** (land level), **low at the SE edge** (deck level) |

The slopes going **NW** and **SW** are not drawn: they are frames 2 and 3 **flipped left to right**, the way the facing marker's are.

**Anchor:** (16, 18), the middle of the land-level top face, on the ground. A bridge sprite is drawn where a ground tile would be: put the anchor on the cell's top-face centre, so the sprite's top is 18 pixels above it.

## The pieces, in order

A bridge is **land, slope, flat, flat, ... flat, slope, land**, laid cell by cell from one shore to the other. Pick the axis it runs along, then use this table. The "high" edge of every slope must touch the land; the "low" edge must meet the flat deck (or the other slope).

**A NE-SW bridge** (it runs along the grid's y axis; y grows toward the SW):

| Position | Frame | Flipped? | High edge (touches land) |
|---|---|---|---|
| NE end (the first cell, smallest y) | 3, Slope down SE | **Yes** | NE |
| every cell between | 0, Flat NE-SW | no | |
| SW end (the last cell, largest y) | 2, Slope down NE | no | SW |

**A NW-SE bridge** (it runs along the grid's x axis; x grows toward the SE):

| Position | Frame | Flipped? | High edge (touches land) |
|---|---|---|---|
| NW end (the first cell, smallest x) | 3, Slope down SE | no | NW |
| every cell between | 1, Flat NW-SE | no | |
| SE end (the last cell, largest x) | 2, Slope down NE | **Yes** | SE |

Read it the other way round and it is the same bridge: starting from the SW, a NE-SW bridge begins with the NE slope and ends with the flipped SE slope.

A bridge of **two** cells is two slopes and no flat pieces. Never put a flat piece at an end, and never use a slope anywhere but an end.

## Orientation rules

1. **The slope's high edge is always on the land side.** Frame 2 is high at the SW; frame 3 is high at the NW. Flipping swaps the side: frame 2 flipped is high at the SE, frame 3 flipped is high at the NE. If a slope looks like a ramp up out of the water, it is on the wrong end.
2. **A flat piece's axis matches the bridge's.** Frame 0 for NE-SW, frame 1 for NW-SE. Never flip a flat piece (the NW-SE flat is its own picture, not a mirror of the NE-SW one).
3. **Only flip slopes, and only the end piece that needs it** (the table above). Flipping is a left-to-right mirror of the whole 32-wide cell.
4. **One axis per bridge.** A bridge never turns a corner; if it has to, it is two bridges with land between them.
5. **The rail is always on the back side.** The art puts one rope rail on the side away from the viewer: the **NW** side of a NE-SW bridge and the **NE** side of a NW-SE bridge. The flips keep it there (a flipped slope's rail ends up on the matching side), so a correct bridge has one continuous rail. There is deliberately **no front rail**, so a character crossing is never hidden behind one.

## Where a bridge can go

These are the rules `terrain.js` follows, and the game should too:

- **Water only, and sunken water only.** The deck hangs 6 pixels below the land (`SINK`), so the water must sit that far below the land too.
- **A straight run of water cells, with land at both ends**, along one grid axis.
- **Length 2 to 7 cells** of water. Fewer is no bridge (nothing to span); more is too long for the sprites' sag and for play.
- **Land at both ends at the same height** as the sprite expects (a land-level top face).
- **Inside the map**, not on its edge row or column (the generator starts at 1 and stops before the last).
- Choose the **shortest** run if there are several (the terrain page picks one of the shortest at random).

## Drawing order

- Draw the map **back to front** (the cells furthest from the viewer first, by `x + y`).
- A bridge cell is drawn **right after its own water tile, in the same cell**, and before any cell in front of it. Do not draw all the bridges after the whole map: the pieces would cover things that should stand in front of them.
- Inside one sprite the order is already fixed: the back rail, then the planks (back to front), then the beam under the deck. You only place the frame.
- A **unit crossing the bridge** is drawn after that bridge cell and before the cells in front of it, like any unit. Because there is no front rail, nothing from the bridge covers it.

## Standing on it

- The deck is the strip of planks down the middle of the cell (`deck_mask(axis, kind)` in `tools/make_bridge.py` is the walkable shape; flip it with the sprite).
- A unit's feet are **lower than on land**: a flat piece's deck is **6 pixels** below the land level. On a slope the deck falls from land level at the high edge to 6 pixels down at the low edge, so a unit at the middle of a slope stands 3 pixels down.
- The bridge cells are the only walkable cells of the span; the water on either side is not.

## Highlights (overlays)

Each highlight colour has bridge overlays too, **in the bridge's own 32 x 40 cell and in the order of the four sprites** (see-through and solid): `overlay-move-bridge`, `overlay-move-solid-bridge`, and the red and yellow ones. Use the **same frame number and the same flip** as the piece underneath, so the highlight lies on the deck.

## What to expect

- The planks are uneven **on purpose** (crooked, a missing one, a frayed rope, a leaning post). Each frame is drawn once with its own fixed seed, so **every flat piece in a run is the same picture**: a long bridge repeats its missing plank and frayed rope. If that shows, make a second flat variant rather than varying the sprite at draw time.
- Changing the bridge art changes frames only. The frame order above and the 32 x 40 cell with the (16, 18) anchor are what the game relies on, so tell the game's side before changing either.

## Quick check

For any laid bridge, all of these should be true:

1. Both ends are land cells; every cell of the span is water.
2. It runs along one axis, 2 to 7 cells long.
3. The first and last cells are slopes, the cells between are flats of the bridge's own axis.
4. Each slope's high edge touches land, and its low edge meets the deck.
5. Only the two end slopes may be flipped (see the tables), and no flat is flipped.
6. The rail is on the NW side (NE-SW) or the NE side (NW-SE) the whole way along.
7. Each bridge cell is drawn straight after its own water tile, in the back-to-front pass.
