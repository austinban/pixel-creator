# Slot icons

Three icons for the equipment slots, 32 x 32 each, in the **UI** category, drawn in the amulets' style (the shared palette, lit from the upper left, a one-pixel outline). Each is **one still picture**, not placed on the map.

| File | Slot | What it is |
|---|---|---|
| `slot-weapon.png` | Weapon | A sword on the diagonal: silver blade, gold crossguard, cord grip, gold pommel |
| `slot-armor.png` | Armor | A breastplate with pauldrons: steel plates trimmed in gold, rivets |
| `slot-trinket.png` | Trinket | A gold ring with a cyan gem |
| `slot-icons.json` | | Every file and cell, for the app to read |

The anchor is the middle of the cell (16, 16). Draw them at whole-number scale with nearest-neighbour filtering, and use the same icon for filled and empty slots (dim it in the UI for empty).
They come from `tools/make_slot_icons.py` (`--preview` shows them enlarged); do not edit the PNGs.
