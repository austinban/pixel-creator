# Terrain sets, for the game's map generator

`sets.json` (beside this file) says **which pieces belong together**, so a generated map feels like one place instead of a random mix. It is optional: nothing else in `sprites/assets/` depends on it, and nothing the game reads today has changed. It is made by `tools/make_sets.py` from `tools/sets.py`; do not edit it. The same data, as tables for people, is in `SETS.md` at the repo's root, and `HOW-IT-WORKS.md` explains the whole project.

## What is in it

```
format       1; bumped if a key is renamed or the layout changes
grounds      plain and corrupted: the ground sheet name (`ground`, `ground-corrupted`)
roles        what each kind of piece does on a map (scatter, platform, blocker, crossing, cover, structure, decor, hazard)
groups       a group of pieces that are one kind of thing: {label, role, fits, style, ids, twin, note}
sets         the looks: `meadow`, `highland`, `riverbank`, `market-town`, `fallen-town`, `spore-hollow`, `gravemoor`, `sunken-marsh`
```

A **group**'s `ids` are asset ids from `assets/data.js` (a prefix group lists every match, so a new rock is picked up with no change here). Its `fits` is `plain`, `corrupted` or `any`; its `style` (`natural`, `blocky`, `timber`, `fungal`...) is what keeps a set cohesive; its `twin` is the group that is the same job in another look.

A **set** is: `ground` (which sheet), `time` (a time of day that suits it), `blurb`, `grass` (cells with weights; `id` is the full asset id on that sheet), `lake` (0 none, 1 pond, 2 lake, 3 big), `level` (`sunken` or `flush` water), `bridge` (a group id or null), and these layers:

| Layer | What | How to use it |
|---|---|---|
| `scatter` | one-cell pieces on land: `density` 0 to 1 of cells, weighted groups | per land cell off the shore, roll the density, pick a group by weight, then a piece |
| `features` | multi-cell pieces on land: `per100` per 100 cells | place each where **every cell of its `footprint.cells`** is clear land, off the shore and off other pieces |
| `water` | pieces placed **in** the water (stepping stones, boats): `per100` per 100 water cells | every footprint cell must be water |
| `decals` | flat pieces: `{group, on: land / water / shore, per100}`. A group with `joins: "mycelium"` is a vein network | draw after the ground and before anything that stands |
| `connectors` | stairs and ramps | attach to a platform of the same height (see their `connector` field); the game decides where |
| `structures` | groups placed by the game's own rules (the buildings kit, docks) | not scattered |
| `weather` | `chance`, and weighted overlay groups | one per map at most; draw tiled over the map; blend, opacity and scroll are in each overlay's record |

## Heights

The game's height step is **8 pixels** (`BattleGrid.HEIGHT_STEP`, half a block); this project's **level is 16 pixels**, two steps. Rocks, ledges, slabs and stairs are 1 or 2 levels (2 or 4 steps); ruin floors and the water props are half a level (one step). **Sunken water is one step (8 pixels) below the land.** So:

- A **water prop** (`surface: "water"`: docks, stepping stones, boats, pads) is drawn **on the water's surface**, 8 pixels below the land's top face: put its anchor on the water cell's top face as drawn. Its walkable top is half a level above the surface, which is exactly the land's height.
- A **bridge** (`bridges-*`) stands on the **floor of the gap, one level (16 pixels) below the banks**, so its deck (one level above that) meets the bank. Place it over exactly the water cells it crosses (its footprint is 3 or 5 cells); both ends need land.
- Everything else stands on the top face of its cell.

## Using it

1. **Pick a set** for the battle (by encounter, node or at random). Draw the map on its `ground` sheet and lay the surfaces as you do now; draw grass from the set's `grass` cells, by weight. The corrupted sheet has the same layout as the plain one, cell for cell, so water and stone keep their cells and only the sheet changes. Use the corrupted clean turf cells in `grass`, not the mushroom block, for everyday grass.
2. **Draw in three passes:** the ground first, back to front; then the flat decals; then everything that stands, back to front. A piece over several cells is drawn when you reach its **front-most cell** (the largest `i + j`).
3. **Weights** are spread over a group's pieces, so a group of seven is no likelier than a group of two. Pieces of kind `variants` are several looks of one piece: pick a frame at random. A piece that is `walkable: true` has a flat top at `levels` levels; anything else with a footprint blocks every cell of it. `destructibles` have states and a `-destroy` animation; the `-broken` thorn walls are what a thorn wall becomes.
4. **Keep a set to itself.** A set only lists groups that fit its ground, so you can draw any of its pieces without a check. If you mix sets, mix the **twins** (a blocky ledge for a natural slab, a mushroom tree for a tree): they have the same footprints and rules. Do not put a piece that `fits` one ground on the other.

The editor's terrain page (`terrain.html`, the **Set** menu) does exactly this in `terrain.js` (`plan`, `makeSpan`, `planVeins`, `drawPlan`, `pickWeather`): read it as a worked example. The same seed in the same set always gives the same map.

## The sets

- **Meadow** (`meadow`, plain ground, day): Green rolling country: oaks and pines, bushes and flowers, worn slabs to climb, boulders and haystacks in the grass, a pond with lily pads and stepping stones, a plank bridge, petals on the wind.
- **Highland** (`highland`, plain ground, day): Cold, stony heights: pines and spruce, broken crags and straight-faced ledges with stairs up to them, a pond high in the rocks, a stone arch bridge, fog in the valleys.
- **Riverbank** (`riverbank`, plain ground, day): A big lake with docks, a stone bridge and reeds: oaks and birches on the banks, boulders on the shore, rowboats and stepping stones on the water.
- **Market town** (`market-town`, plain ground, day): A town square: stalls and carts, haybales and crate piles to climb, fences and crates, barrels and barricades you can break, a few trees, and the buildings kit.
- **Fallen town** (`fallen-town`, plain ground, dusk): The same town after something went wrong: ruined walls and rubble to hide behind, broken foundations and overgrown stumps of buildings, dead trees, broken fences and logs, embers in the air.
- **Spore hollow** (`spore-hollow`, corrupted ground, dusk): The healthy meadow, corrupted: teal turf, mushroom trees and shelf fungus to climb, veins of mycelium across the ground, spore vents and thorn walls, natural stones swallowed by moss, spore haze.
- **Gravemoor** (`gravemoor`, corrupted ground, night): A moor of graves under mist: gravestones and cairns, bones, an obelisk and a rune altar around a ritual circle, spirit lanterns, iron fences and gates, dead trees and broken crags.
- **Sunken marsh** (`sunken-marsh`, corrupted ground, dusk): A drowned corrupted lowland: dark water with mushroom pads, mushroom trees on the banks, rotten docks and a corrupted bridge, stones standing in the shallows, haze over it all.
