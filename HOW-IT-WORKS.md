# How it all works

A map of this repo for whoever picks it up: what makes the art, how a piece gets from a Python generator to the game, the rules every piece follows, and how pieces are grouped into **sets** so a map feels like one place. The rules are in [CONVENTIONS.md](CONVENTIONS.md), what each page and asset is in [README.md](README.md), the sets in [SETS.md](SETS.md), the bridge rules in [BRIDGES.md](BRIDGES.md), and the standing rules for working here in [AGENTS.md](AGENTS.md).

## The pipeline

```
tools/make_*.py  ->  assets/data.js  +  sprites/assets/*.png   ->  the editor pages  and  the game
 (generators)        (every asset as    (sheets and folders)        (index, characters, assets, terrain)
                      rows of roles)
tools/sets.py    ->  assets/sets.js  +  sprites/assets/sets/sets.json  +  SETS.md
 (which pieces go together)
```

- **Everything is a generator.** A picture is never edited by hand: change the Python that draws it, rebuild, commit the result. Bases in the editor are read-only; the first edit makes a copy.
- **Colours are roles, not RGB.** Every pixel is a letter from the 31-role palette (`assets/data.js` lists them); the editor and the game turn letters into colours, so a palette change recolours everything (`tools/recolor.py`).
- **Previewed before wired in.** A new look is built as a generator with `--preview` (pictures in `previews/`, not committed), shown, and only then added to the registry, the tests and the docs.

```bash
python3 tools/make_assets.py --png-dir sprites/assets   # assets/data.js, every sheet, each folder's package (only what changed is rebuilt)
python3 tools/make_sets.py                              # assets/sets.js, sprites/assets/sets/sets.json, SETS.md
python3 -m unittest discover -s tools -p 'test_*.py'    # the tests
python3 tools/check_conventions.py                      # the character rules
python3 tools/serve.py                                  # then open http://localhost:4321 (index, characters, assets, terrain pages)
```

## One family, one module

An **asset family** is a module with `build_assets()` that returns asset records (`tools/assetkit.family(...)` makes them), and, if it ships a folder with a README, `FOLDER` and `write_package(folder)`. `tools/registry.py` lists the families in the order the Assets page shows them (`Unit(name, module, inputs=..., depends=...)`), `tools/buildcache.py` rebuilds only what changed (keyed on the code of the module and everything it imports, `tools/data/` and its inputs), and `tools/make_assets.py` writes the result. A generator must be **deterministic**: no unordered `set` choosing between equals, no random without a seed.

An asset record has `id`, `label`, `category`, `kind` (`still`, `animation` or `variants`), `place` (where the editor lets you put it), `w`, `h`, `frames` (rows of role letters), `anchor` (the point on the ground the picture is drawn from), and whatever the family adds (`footprint`, `walkable`, `levels`...).

## The ground and its geometry

This is the one projection everything on the map shares (`tools/buildings.py` draws with it, `terrain.js` lays tiles with it):

- A ground tile is a **32 x 32 cube**: a **32 x 16 diamond** on top and sides 16 tall. A step along either grid axis moves the picture **16 across and 8 down**: **x runs down-right (SE), y runs down-left (SW)**. One **level** of height is **16 pixels up**. The game's own height step is **8 pixels** (`BattleGrid.HEIGHT_STEP`, half a block), so a level is two steps; **sunken water is one step (8 px) below the land**, so water props are half a level above their surface and a bridge stands on the gap's floor, a level below the banks.
- Light is from the upper left; the right wall (+x) is lit, the left wall (+y) shaded, the top brightest. Pieces that share the ramp (steel, lavender, indigo, with moss) sit together.
- **Anchor:** the point on the ground the picture is placed from. For a single-cell prop it is the middle of the cell's top face. For a piece over many cells (a rock, a building, a boss) it is **the middle of the bounding box of its footprint on the ground**. Its picture is `16 * (fx + fy) + 2 * margin` wide.
- **Footprint:** `footprint.size` is `[x cells, y cells]` of the bounding box, `footprint.cells` the cells it stands on (an L has gaps), counted `(i, j)` from the back corner. A piece over several cells is **drawn when the map loop reaches its front-most cell** (the largest `i + j`), so it sits behind what is nearer and in front of what is further.
- **Walkable:** a piece is walkable when it has a **flat top at a whole level** over its cells. `levels` (1 or 2) says how high; `top_cover` says how much of each cell is flat; a piece is marked `walkable` only when every cell has at least **60 percent** flat top (`WALK_MIN` in `tools/make_rocks.py`, enforced by a test). Anything else with a footprint blocks every cell of it.

## Two grounds

`sprites/assets/ground.png` (the original, not ours, not committed) and `sprites/assets/ground-corrupted.png` (made from it by `tools/make_corrupted_ground.py`) are **cell for cell the same layout**. A map swaps one sheet for the other and finds each piece by its cell. So a table of cells (`grass`, `water`) names the same piece on either sheet: `ground-0-2` is water, `ground-corrupted-0-2` is dark teal water.

- Assets are `ground-COL-ROW` and `ground-corrupted-COL-ROW`.
- The corrupted block at **(0, 0)** carries mushrooms; **clean turf** is at **(4, 11), (5, 11), (6, 11)**. Use the clean ones for everyday grass and (0, 0) as an accent.
- Crates, fences and stairs have no corrupted version (their cells are empty in that sheet): they fit either ground because they are drawn from the plain sheet's cells.

## Sets: pieces that go together

A **set** is a look for a whole map, and the thing the terrain builder swaps. It is data in `tools/sets.py`:

- **Groups.** A group is a handful of pieces that are one kind of thing (the temperate trees, the natural slabs). It has a **role** (what it does on a map: `scatter`, `platform`, `blocker`, `crossing`, `cover`, `structure`, `decor`, `hazard`), a **ground it fits** (`plain`, `corrupted` or `any`) and a **style** (`natural`, `blocky`, `timber`, `fungal`...) so a set stays cohesive.
- **Sets.** A set picks a ground, a mix of grass cells, a default lake and bridge, and weighted groups for scatter and for multi-cell features. It may only list groups that fit its ground; a test checks that.
- **Twins.** Two groups that are two looks of the same job with the same footprints are **twins**: the blocky ledges and the natural slabs, the blocky crags and the natural stones, the temperate trees and the mushroom trees. Swap one for the other in any map and every rule still holds. [SETS.md](SETS.md) lists them, and what fits only one ground.
- **Fits `any`** means the piece is drawn on either ground with no variant. A piece that fits one ground only must not be put in a set on the other.

Run `python3 tools/make_sets.py` after changing a set or building assets. It checks every piece against `assets/data.js` and writes `assets/sets.js` (the terrain page), `sprites/assets/sets/sets.json` (for the game) and `SETS.md`.

**The terrain builder** (`terrain.html`, `terrain.js`) has a **Set** menu. Picking a set swaps the ground sheet, the grass mix, what is scattered, which rocks are placed and the lake and bridge defaults; **New map** remakes it from a seed. A link can name both: `terrain.html?set=gravemoor&seed=7`. Single-cell pieces are scattered with the set's density, off the shore; multi-cell pieces are planned first, each only where every cell of its footprint is clear land. The same seed in the same set always makes the same map.

**To add a set:** write it in `tools/sets.py` (groups that fit, one or two styles), rebuild, open the page, press **New map** a dozen times, and cut anything that looks like it belongs to another place. **To add a family to the sets:** add a group for it (its role, fit and style), name it in the sets it suits, and say its twin if it has one.

## What the game reads

The game pulls art with `tools/sync_sprites.py` in its own repo, one way; this repo never edits it. It reads the character, weapon and bow sheets by filename and size, the two ground sheets, and `assets/data.js` (including the ids named in AGENTS.md; the file has a top-level `"format"`, bumped when a key is renamed). New folders it can opt into are listed in its `tools/pixel_creator.json`. `sprites/assets/sets/sets.json` is for its map generator: it says which groups fit which ground and which pieces make a place feel like one place. Check you have not broken it with `python3 tools/sync_sprites.py --dry-run` from the game repo (`0 error(s)`).

## Tests

`test_conventions.py` (characters, walks, weapons), `test_abilities.py`, `test_ground.py`, `test_families.py` (every family, the registry and the cache), `test_handoff.py` (what the game reads, and the editor's Save to sprites/ guard), `test_sets.py` (every piece in a set exists and fits its ground, the generated files are up to date, the terrain script parses). A rule with no test protects nothing.

## Adding something new, in order

1. Write the generator in `tools/` with a `--preview`; show it.
2. Once approved: add a `Unit` to `tools/registry.py`, its tests, its README paragraph and its folder README.
3. Rebuild with `make_assets.py`, then `make_sets.py` if it belongs in a set.
4. Run the tests and `check_conventions.py`; run the game's `--dry-run`.
5. Commit and push only when asked; on `main`, branch first.
