# Ability animations

The animations for the abilities: bursts on the ground, rings round a unit, icons over a head, a vanish and appear shimmer, and surfaces that stay on the ground. Everything for them is in this
folder, on the Assets page it is the **Abilities** category, and **`abilities.json` is the table the game reads**: for every ability it says which sheet to play, where, and how. The ability names
and areas are the game's (`scripts/content/ability_kit.gd`); the existing `fire-burst`, `heal-petals` and `vine` stay as they are, and are not in this folder.

## How to play one

- A sheet is **one row of equal frames**, left to right. Play them in order at the sheet's frame rate. A sheet that **loops** repeats; any other plays **once** and is done (draw nothing after the last frame).
- Every sheet has an **anchor**, a point in its frame. Put the anchor on the thing the effect belongs to: **the middle of the ground tile** for a burst or a ground loop (a five-plot burst: the middle of the
  middle tile), **the unit's feet** for a ring or a vanish, and **the point just above the unit's head** for an icon. Draw it **over the ground and under the units that stand on it**, except icons, which go over everything.
- A ground tile is a 32 x 16 diamond. Moving one cell along x (down and right) moves the drawing **(16, 8)**; along y (down and left) **(-16, 8)**. `abilities.json` > `offsets` has the pixel offset of every cell in
  a radius-1 (5 cells) and radius-2 (13 cells) diamond, with its distance from the middle.
- **Five-plot sheets** (`burst-NAME`, 80 x 56) cover a radius-1 area in one picture: put the anchor on the aimed cell. **Tile sheets** (`burst-NAME-tile`) are one cell; place one on every cell of the area
  (radius 2 is 13 tiles, a wall is 3), and for a radius-2 burst start each tile one frame later for each step from the aimed cell, so it spreads outward.
- **Vanish and appear** are the same shimmer in two directions: `vanish-X` gathers the unit into a point (shrink the unit's own sprite to that point as it plays) and `appear-X` is the same frames reversed, so
  it grows back out. Play `vanish-X` where a unit leaves, `appear-X` where it arrives, and `vanish-X` again when a summon expires. Nothing needs playing backwards.
- **Dash** has an NE and an SE sheet. The NW and SW ones are those **flipped left to right**.
- **Ground loops** (mire, slick ground, fire wall) are one tile per cell and loop for as long as the effect lasts. The mire and the slick are drawn to **join** the next tile, so five of them are one surface. Start the fire wall's
  tiles on different frames so the flames do not move in step.

## Which ability plays what

Area is in cells, a diamond (steps along the two axes added together) round the aimed cell. `once` plays one time, `loop` repeats while the effect lasts.

### Bursts

| Ability | Area | Plays | On | How | Note |
|---|---|---|---|---|---|
| Crimson Bolt | 1 tile | `burst-crimson-tile` | aimed | once |  |
| Sanguine Burst | radius 1 | `burst-blood` | aimed | once | the five-plot sheet covers the whole area |
| Spore Cloud | radius 1 | `burst-spore` | aimed | once | the five-plot sheet covers the whole area |
| Static Surge | radius 2 | `burst-static-tile` | cells:radius2 | once | one tile on each of the 13 cells; start each a frame later for each step from the aimed cell |
| Downpour | radius 2 | `burst-rain-tile` | cells:radius2 | once | one tile on each of the 13 cells; start each a frame later for each step from the aimed cell |
| Quake | radius 1 | `burst-dust` | aimed | once | the five-plot sheet covers the whole area |
| Tremor (boss) | radius 2 | `burst-dust-tile` | cells:radius2 | once | one tile on each of the 13 cells; start each a frame later for each step from the aimed cell |
| Raise | 1 tile | `burst-dust-tile` | aimed | once | the game changes the terrain itself on the same frame as the dust peaks (frame 4) |
| Lower | 1 tile | `burst-dust-tile` | aimed | once | the game changes the terrain itself on the same frame as the dust peaks (frame 4) |
| Stone Wall | line of 3, 1 wide | `burst-dust-tile` | cells:line3 | once | one tile on each of the three cells |
| Shove | 1 tile | `burst-dust-small-tile` | target | once | a small puff where the unit was pushed from |

### Rings

| Ability | Area | Plays | On | How | Note |
|---|---|---|---|---|---|
| Rally | radius 2, centred on the caster | `ring-rally` | caster | once | the large ring spreads over the whole radius |
| Inspire | 1 tile | `ring-inspire` | target | once |  |
| Cleanse | 1 tile | `ring-cleanse` | target | once |  |
| Sever | 1 tile | `ring-sever` | target | once | the ring forms and breaks into pieces |
| Ward | 1 tile | `ring-ward-form` | target | once | when it is cast |
| Ward | 1 tile | `ring-ward-hold` | target | loop | while the ward stands, over the unit |
| Ward | 1 tile | `ring-ward-break` | target | once | when it absorbs a hit, in place of the hold; the same break as Sever |
| Climb | caster only | `ring-climb` | caster | once |  |
| Dash | caster only | `ring-dash-ne` | caster | once | when the dash goes up the screen (NE); NW is this sheet flipped left to right |
| Dash | caster only | `ring-dash-se` | caster | once | when the dash goes down the screen (SE); SW is this sheet flipped left to right |

### Icons over the head

| Ability | Area | Plays | On | How | Note |
|---|---|---|---|---|---|
| Mark | 1 tile | `icon-mark-pop` | target-head | once |  |
| Silence | 1 tile | `icon-silence-pop` | target-head | once |  |
| Stun | 1 tile | `icon-stun-pop` | target-head | once |  |
| Charm | 1 tile | `icon-charm-pop` | target-head | once |  |
| Confuse | 1 tile | `icon-confuse-pop` | target-head | once |  |

### Vanish and appear

| Ability | Area | Plays | On | How | Note |
|---|---|---|---|---|---|
| Blink | 1 tile | `vanish-violet` | start-cell | once | the unit shrinks to a point as it plays |
| Blink | 1 tile | `appear-violet` | end-cell | once | the unit grows back out |
| Swap | 2 tiles (both units) | `vanish-violet` | both-units-old-cell | once |  |
| Swap | 2 tiles (both units) | `appear-violet` | both-units-new-cell | once |  |
| Call Wolf | 1 tile | `appear-blue` | summon-cell | once | when it arrives |
| Call Wolf | 1 tile | `vanish-blue` | summon-cell | once | when it expires |
| Call Decoy | 1 tile | `appear-yellow` | summon-cell | once | when it arrives |
| Call Decoy | 1 tile | `vanish-yellow` | summon-cell | once | when it expires |
| Raise Guardian | 1 tile | `appear-stone` | summon-cell | once | when it arrives |
| Raise Guardian | 1 tile | `vanish-stone` | summon-cell | once | when it expires |

### Ground loops

| Ability | Area | Plays | On | How | Note |
|---|---|---|---|---|---|
| Mire | radius 1 | `surface-mire` | cells:radius1 | loop | one tile on each of the 5 cells; they join into one surface |
| Slick Ground | radius 1 | `surface-slick` | cells:radius1 | loop | one tile on each of the 5 cells; they join into one surface |
| Fire Wall | line of 3 | `surface-firewall` | cells:line3 | loop | one tile on each of the three cells, each started on a different frame so the flames do not move together |

### Statuses (looping icons)

A status that lasts shows its icon on the unit and loops it for as long as the status does.

| Status | Plays | On | Note |
|---|---|---|---|
| Mark | `icon-mark-loop` | unit-head |  |
| Silence | `icon-silence-loop` | unit-head |  |
| Stun | `icon-stun-loop` | unit-head |  |
| Charm | `icon-charm-loop` | unit-head |  |
| Confuse | `icon-confuse-loop` | unit-head |  |
| Soaked | `ring-status-soaked` | unit-feet |  |
| Shocked | `ring-status-shocked` | unit-feet |  |
| Spored | `ring-status-spored` | unit-feet |  |
| Rooted | `vine` | unit-feet | the existing vine animation, as it is |
| Snared | `vine` | unit-feet | the existing vine animation, as it is |
| Mired | `vine` | unit-feet | the existing vine animation, as it is |

### Reused, nothing new

| Ability | Plays | Note |
|---|---|---|
| Root | `vine` | the existing vine animation, as it is |
| Hook | `vine` | the existing vine recoloured grey, lashing out and pulling the target in; recolour by swapping roles z to q, A to p, B to l, s to k (the bud and the leaves go with them, the earth stays) |

## The sheets

| File | What it is | Frames @ fps | Cell | Anchor | Plays |
|---|---|---|---|---|---|
| `burst-blood.png` | Blood burst - five plots | 8 @ 8 | 80 x 56 | (40, 38) | once |
| `burst-blood-tile.png` | Blood burst - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-spore.png` | Spore cloud - five plots | 8 @ 8 | 80 x 56 | (40, 38) | once |
| `burst-spore-tile.png` | Spore cloud - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-static.png` | Static surge - five plots | 8 @ 8 | 80 x 56 | (40, 38) | once |
| `burst-static-tile.png` | Static surge - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-rain.png` | Downpour - five plots | 8 @ 8 | 80 x 56 | (40, 38) | once |
| `burst-rain-tile.png` | Downpour - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-dust.png` | Dust burst - five plots | 8 @ 8 | 80 x 56 | (40, 38) | once |
| `burst-dust-tile.png` | Dust burst - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-dust-small-tile.png` | Dust puff (small) - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `burst-crimson-tile.png` | Crimson bolt - one plot | 8 @ 8 | 32 x 56 | (16, 44) | once |
| `ring-rally.png` | Rally ring (gold, radius 2) | 8 @ 10 | 112 x 72 | (56, 52) | once |
| `ring-inspire.png` | Inspire ring (bright yellow) | 8 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-cleanse.png` | Cleanse ring (white-green) | 8 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-sever.png` | Sever (a white ring breaking) | 8 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-ward-form.png` | Ward - the bubble forming | 6 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-ward-hold.png` | Ward - the bubble holding (loops) | 6 @ 8 | 64 x 56 | (32, 40) | loops |
| `ring-ward-break.png` | Ward - the bubble breaking | 8 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-climb.png` | Climb (light blue rings rising) | 8 @ 10 | 64 x 56 | (32, 40) | once |
| `ring-status-soaked.png` | Soaked status (blue ring, loops) | 8 @ 8 | 64 x 56 | (32, 40) | loops |
| `ring-status-shocked.png` | Shocked status (yellow ring, loops) | 8 @ 8 | 64 x 56 | (32, 40) | loops |
| `ring-status-spored.png` | Spored status (green ring, loops) | 8 @ 8 | 64 x 56 | (32, 40) | loops |
| `ring-dash-ne.png` | Dash NE (speed lines; NW is this flipped) | 6 @ 12 | 64 x 56 | (32, 40) | once |
| `ring-dash-se.png` | Dash SE (speed lines; SW is this flipped) | 6 @ 12 | 64 x 56 | (32, 40) | once |
| `icon-mark-pop.png` | Mark (crosshair) - pop-up above the head (once) | 8 @ 10 | 24 x 32 | (12, 30) | once |
| `icon-mark-loop.png` | Mark (crosshair) - status icon (loops) | 6 @ 6 | 24 x 32 | (12, 30) | loops |
| `icon-silence-pop.png` | Silence (sealed lips) - pop-up above the head (once) | 8 @ 10 | 24 x 32 | (12, 30) | once |
| `icon-silence-loop.png` | Silence (sealed lips) - status icon (loops) | 6 @ 6 | 24 x 32 | (12, 30) | loops |
| `icon-stun-pop.png` | Stun (stars) - pop-up above the head (once) | 8 @ 10 | 24 x 32 | (12, 30) | once |
| `icon-stun-loop.png` | Stun (stars) - status icon (loops) | 6 @ 6 | 24 x 32 | (12, 30) | loops |
| `icon-charm-pop.png` | Charm (heart) - pop-up above the head (once) | 8 @ 10 | 24 x 32 | (12, 30) | once |
| `icon-charm-loop.png` | Charm (heart) - status icon (loops) | 6 @ 6 | 24 x 32 | (12, 30) | loops |
| `icon-confuse-pop.png` | Confuse (spiral) - pop-up above the head (once) | 8 @ 10 | 24 x 32 | (12, 30) | once |
| `icon-confuse-loop.png` | Confuse (spiral) - status icon (loops) | 6 @ 6 | 24 x 32 | (12, 30) | loops |
| `vanish-violet.png` | Vanish - Violet (blink, swap) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `appear-violet.png` | Appear - Violet (blink, swap) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `vanish-blue.png` | Vanish - Pale blue (call wolf) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `appear-blue.png` | Appear - Pale blue (call wolf) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `vanish-yellow.png` | Vanish - Yellow (call decoy) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `appear-yellow.png` | Appear - Yellow (call decoy) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `vanish-stone.png` | Vanish - Stone grey (raise guardian) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `appear-stone.png` | Appear - Stone grey (raise guardian) | 8 @ 12 | 48 x 56 | (24, 44) | once |
| `surface-mire.png` | Ground loop - Mire (brown-yellow mud) | 8 @ 8 | 32 x 56 | (16, 44) | loops |
| `surface-slick.png` | Ground loop - Slick ground (blue, wet) | 8 @ 8 | 32 x 56 | (16, 44) | loops |
| `surface-firewall.png` | Ground loop - Fire wall (flames, for a line of three) | 8 @ 8 | 32 x 56 | (16, 44) | loops |

## Making a new one

Each family is a small module (`tools/make_burst.py`, `make_ring.py`, `make_icons.py`, `make_vanish.py`, `make_ground_fx.py`, sharing `tools/fx.py`). A new colour or style of an existing family is one entry in that module; a new ability is one
entry in `ABILITIES` in `tools/make_abilities.py`, naming the sheets it plays. Then `python3 tools/make_assets.py --png-dir sprites/assets` rebuilds the sheets, `abilities.json` and this README, and the tests check that every sheet an ability
names exists. Preview a family with `--preview` (for example `python3 tools/make_burst.py --preview previews/bursts.png`). The sheets are generated by code, so change the code and rebuild instead of editing the PNGs.
