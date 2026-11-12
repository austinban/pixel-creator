# Item pictures

26 inventory icons for the items the game listed in `docs/pixel-creator-requests.md` (section 5) that had no picture of their own. Each is **32 x 32**, in category **Item icons**, drawn in the shared palette with a one-pixel outline and lit from the upper left, like the amulets and the slot icons. They are made by `tools/make_item_icons3d.py`: each is a small 3D model, rendered with the creatures' renderer, with the details painted over it.

## Using them

Each file is one 32 x 32 picture, not a sheet. They are named `item-<id>.png` here, where `<id>` is the game's item id; the game wants them as **`<id>.png` in `assets/sprites/items/`**, so drop each in with the `item-` taken off. `item-icons.json` lists every item with its label, this file's name and the game's.

```bash
# from the pixel-creator repo, into the game's folder (it writes nothing else)
for f in sprites/assets/item-icons/item-*.png; do b=$(basename "$f"); cp "$f" ~/GodotProjects/iso-fft-like/assets/sprites/items/"${b#item-}"; done
```

| Group | Items (the game's ids) |
|---|---|
| Weapons | `recurve_bow` `sling` `worn_sword` `worn_dagger` `worn_bow` `oak_staff` `warding_staff` `storm_staff` |
| Armour | `leather_jerkin` `iron_mail` `warden_plate` `dragonscale_mail` |
| Trinkets | `swift_boots` `windrunner_boots` `warding_charm` `vigor_ring` `strength_band` `sage_amulet` `giants_belt` `hawkeye_pendant` `guardian_sigil` `sage_circlet` `summit_crown` `phoenix_heart` `stormcaller_band` `stone_idol` |

## How they are drawn

- **Weapons all lie on the same diagonal**, 45 degrees, rising to the upper right, to fill the cell: blades, staves, the sling and the bows (a bow is turned to sit on the slope, its string below it).
- **Armour and trinkets sit in the middle** of the cell, facing the viewer.
- The palette has no true brown, so wood and leather are its orange, plum and grape; there is no pure red either.
- The icons are palette colours, so they recolour with the rest of the art.

## Things to know

- A flat (2D) version of the same 26 also exists in the repo (`tools/make_item_icons.py`), kept for comparison; only the 3D set is shipped here.
- Three of them are weaker than the rest at this size and could be redrawn if they read badly in the game: `warding_charm`, `guardian_sigil` (flat shields) and `sage_amulet` (the eye is small).
