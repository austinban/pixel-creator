# Working in pixel-creator

A static HTML/JS pixel-art editor (open `index.html`, `characters.html`, `assets.html`, `terrain.html` from any static server) plus the Python generators in `tools/` that make
the art. The game (iso-fft-like, a Godot tactics game) pulls the art out with its own script; this repo is the source of truth and nothing here depends on the game.
Look at [CONVENTIONS.md](CONVENTIONS.md) for the rules the art follows and [README.md](README.md) for what each page and asset set is.

## Standing rules

- **Bases never change in the editor.** A base (a character base, an asset) is read-only; the first edit makes a saved copy.
- **A new look is previewed and approved before it is wired in.** Build the generator with a `--preview`, show it, and only add it to the registry, the tests and the docs once it is approved.
- **Follow CONVENTIONS.md.** `python3 tools/check_conventions.py` and the tests enforce it; a rule with no test protects nothing.
- Commit and push only when asked. On `main`, branch first (GitHub rejects pushes to `main`). Commit messages say what and why, and end with the `Co-Authored-By` line the earlier commits use.
- Generated files are generated: change the generator in `tools/`, rebuild, and commit the result. Do not edit `assets/data.js`, `sprites/assets/*.png` or `poses/base.js` by hand.

## How the art is made

```bash
python3 tools/make_assets.py --png-dir sprites/assets     # assets/data.js, every sheet, each folder's package; only what changed is rebuilt
python3 tools/make_assets.py --png-dir sprites/assets --force   # rebuild everything (the bows alone take about two and a half minutes)
python3 tools/recolor.py                                  # after a palette change: recolours the PNGs by role and refreshes poses/base.js
python3 -m unittest discover -s tools -p 'test_*.py'      # the tests (about 20 seconds)
python3 tools/check_conventions.py                        # the character rules
```

**One family, one module.** Every module that makes assets has `build_assets()`, which returns a list of asset records, and, if it ships a folder with a README, `FOLDER` and `write_package(folder)`.
`tools/assetkit.py` has what they share: `family(category, w, h, anchor, ...)` makes records with the right keys, `write_json` writes the package file, and `sheet_layout`, `GROUND_ROW`,
`normalise` and `inside` are the helpers more than one family used. Look at `make_chest.py` or `make_traps.py` for the shape.

**The registry** (`tools/registry.py`) lists the families in the order the Assets page shows them. To add one: write the module, add a `Unit(...)` line (say what files it reads in `inputs`, any module it loads
by name in `depends`, any file it must leave behind in `outputs`), and write its tests in `tools/test_families.py` (or its own `test_*.py`). `tools/make_assets.py` does the rest: `data.js`, the sheets, the manifest and the package.

**The cache** (`tools/buildcache.py`, in `.build-cache/`, not committed) keeps each unit's assets, keyed on the code of its module and everything it imports, `tools/data/`, and its `inputs`. Change a family and only it rebuilds;
change a shared helper and everything that imports it rebuilds. A sheet PNG is only rewritten when its pixels changed. A generator must be **deterministic**: no unordered `set` choosing between equals (sort first), no random without a seed.
Tests get assets through `buildcache.assets_of(name)`, so a test run does not redraw what it did not touch.

**Tests** are split by what they protect: `test_conventions.py` (characters, walks, weapons, the bow), `test_abilities.py`, `test_ground.py`, `test_families.py` (chests, bazaar, traps, node map, buildings, registry and cache),
`test_handoff.py` (what the game reads, and the editor's Save to sprites/ guard, which runs `tools/test_save.js` in node).

## Ground themes

`sprites/assets/ground.png` is the original ground sheet (512 x 416, 32 x 32 cells; it is not ours, so it is not committed). `sprites/assets/ground-corrupted.png` is the second theme, **cell for cell the same layout**, made by
`tools/make_corrupted_ground.py` from the original by recolouring roles (teal turf, plum and purple soil, dark teal water) and drawing mushrooms, vines, thorns and eyes on the full blocks. A map swaps one sheet for the other and finds each piece by its cell.

- Assets are `ground-COL-ROW` and `ground-corrupted-COL-ROW`, with the same `overlay` shape.
- The block at **(0, 0)** of the corrupted sheet carries mushrooms. **Plain grass with no decoration is at (4, 11), (5, 11) and (6, 11)** (`CLEAN_GRASS`), three turf patterns on the same cube, for everyday grass.
- The crates, fences and stairs have no corrupted version; their cells are empty in that sheet. Do not put anything in a cell that is used in the original.
- The shaded side of the corrupted water is the palette role `D` (Abyss teal).

## What the game reads

The game pulls art with `tools/sync_sprites.py` in its own repo, one way. What it reads and must stay put: the character, weapon and bow sheets by filename and size, `sprites/assets/ground.png` and `ground-corrupted.png`, and
`assets/data.js`, including the ids `crystal`, `rock`, `facing`, `facing-pale`, `weapon-bow-ne`, `weapon-bow-se`, `arrow-iso` and `arrow` (`test_handoff.py` checks them). **`assets/data.js` has a top-level `"format"` number**
(`DATA_FORMAT` in `tools/make_assets.py`, now 1): bump it when a key is renamed or the layout changes, not when assets are added, so the game can notice by itself. The facing marker is a 20 x 14 cell, two frames, anchored at (10, 8):
tell the game's side before changing either. The palette has 31 roles (`D` Abyss teal) and the roles list is in `data.js`, so a role added or renamed is a change to tell them about. Check you have not broken the game's side from its repo with
`python3 tools/sync_sprites.py --dry-run`; it writes nothing and should end with `0 error(s)`.

Two ways to get an edited character to the game without a hand-made ZIP, on the Characters page: **Export for the game (ZIP, 1x)** is always true size and has a `pixel-creator.json`
(`{"format": 1, "kind": "character", "set": ..., "base": ..., "scale": 1, "cell": [32, 32]}`) beside the PNGs, and **Save to sprites/ (1x)** (Chromium only) writes the PNGs and the same manifest straight to `sprites/<set>/`
using the File System Access API (`sprites-save.js`), asking for the repo's `sprites/` folder once and remembering it. It refuses a set that would replace a generated one: a name that is a base, a folder with no `pixel-creator.json` of ours, or `assets` and `weapons`.
The manifest is not a sprite, so a reader of `sprites/<set>/` skips it.

## Known loose ends

- "Save to sprites/" has only been tested against in-memory folders; try it once in Chrome.
- The weapon, asset and ZIP manifests (`kind: "weapon"` or `"asset"`) are not written yet; only characters.
