# Conventions

The rules every character, creature and weapon here follows, so new ones fit in with the old.
They were **measured from the original six bases** (cleric, fighter, mage, skeleton, zombie,
knight), not invented. The Human, Dog and Rat were then brought into line with them.

The same rules, as numbers and code, are in `tools/conventions.py`. Generating a character checks
them and refuses to write anything that breaks them. To check the whole project:

```bash
python3 tools/check_conventions.py
```

Run it after changing any pose, colour ramp, proportion or weapon.

## Floating creatures

A spirit or wisp has no feet, so it follows its own ground rules (kind `floater` in `BASE_KINDS`, `tools/conventions.py`):

- Its **lowest painted row** (the tail tip or a trailing wisp) is **28-31**, a little below the ground line at 27, and it stays in that band: across a walk the lowest row changes by at most **3**, so it bobs instead of sinking or lifting off. The game draws its shadow on the ground at row 27.
- It may stand **22-32 rows** tall, taller than a person (24-27), and at most **26 columns** wide, outline included. Standing, it is centred like everyone else (middle at 15-18).
- No lean, weight, walk-slide or hand-path checks apply; the outline, the cell margins and the palette still do.
- Anything not on the list is checked as a humanoid, so declare a floater in `BASE_KINDS`.

`tools/trace_guide.py` turns a picture of a pose guide (`tools/make_pose_guide.py`) back into sprites and trims them to these rules.

## The cell

- A character is drawn in a **32 × 32** cell. Painted pixels stay inside columns **1-30** and rows
  **0-31**.
- A **weapon** is drawn in a **48 × 48** cell, so a swing can pass the character's edge. The
  character sits in the middle of it, **8 pixels in** from every side.
- Every pose has the same frame counts: attack 4, walking 8, everything else 1, in both facings.

## Facings

- **NE** is the character seen from behind, going away from the camera.
- **SE** is the character seen from the front, coming toward it.
- Light comes from the **upper left, in front**. Do not move it.

## Standing on the ground

- The lowest painted pixel of a frame, outline included, is on **row 27**, even in the middle of a
  lunge. Walking may have a lifted foot one row up. Generation puts every frame there for you.
- Lying down (**dead**) sits lower: the lowest row is **29-31**.
- A frame can only leave the ground if the creature says so on purpose (a leap): `airborne`.

## Outline

- Every silhouette has a one-pixel outline in the **outline** colour. No painted pixel on the edge
  of a shape is left un-outlined.

## Size and weight

- A standing **person** is **24-27 rows** tall, top of the outline to the ground, with its middle
  at column **15-18**.
- A **creature** is wider and lower than a person: **at most 26 columns** wide, **at least 14 rows**
  tall.
- **Height by pose.** A flinch is hunched (21-24 rows), a slump is low (16-18), a cast has the arms
  thrown up (27-28), walking is 23-28, attack 22-27. See `HEIGHT` in `conventions.py`.
- **Weight.** A figure fills the cell. Painted pixels per frame, in the originals: attack 267-388,
  charging 274-380, damage 250-363, release 297-373, walking 258-394, weak 220-286, dead 225-312. A
  character with much less than this reads as floating. Get weight from a thicker body and limbs
  (`bulk` in `humanoid.py`), not from making the figure taller.

## Lean: characters lean into what they are doing

This is what makes the originals feel heavy. **Lean** is how far the head is from the feet across
the screen: the middle of the head (the top third) minus the middle of the feet (the bottom three
rows), in pixels, positive toward the right.

The average of the six originals, frame by frame (`LEAN` in `conventions.py`):

| pose | frame lean (px) |
|---|---|
| attack SE | −2.5, +3.5, +4.0, +4.0 |
| attack NE | −4.0, +0.5, +3.5, +3.5 |
| charging SE / NE | +3.0 / 0.0 |
| damage SE / NE | +3.5 / +1.0 |
| release SE / NE | +2.0 / −1.5 |
| weak SE / NE | +2.0 / +3.0 |
| walking SE | +2.0, +0.5, −0.5, +0.5, +2.0, +1.5, 0.0, +1.5 |
| walking NE | −1.0 (×5), 0.0 (×3) |

The shape of an **attack** is the lesson: the body goes **back** to wind up, then throws its weight
**forward** and **keeps it there** through the follow-through. It does not straighten up when the
arm finishes. A person must stay within **2.5 px** of these numbers (the originals themselves
differ by up to 4).

Leaning is done with **sway**: the upper body (torso, head, arms) moves ahead of the hips while the
feet stay planted, which is how a figure puts its weight into a movement. Tipping the whole body
forward barely moves the head across the screen (about 0.1 px a degree) and quickly looks like
falling over, so do not reach for that. `tools/tune_lean.py` finds the sway that gives each frame
its lean, and the head sits a little ahead of the shoulders (`head_fwd`), as the originals' do.

## The walk

The originals all share one walk, and it is a **bob with sliding feet**, not a rock forward and back.
Over its eight frames (`WALK_*` in `conventions.py`):

- **The head stays put.** It moves at most about 1 px across the screen over the whole cycle
  (the originals: 0-0.8). The upper body does not swing forward and back.
- **The body bobs down and up twice** in the eight frames, a period of four, by 1-3 rows. A person's
  legs are straight when standing, so the bob goes *down* from there and back up.
- **The feet slide** along the ground (the middle of the feet moves 1.2-3.3 px) and barely lift:
  the lowest row is 26 on one frame at most, 27 on the rest.
- Because the head does not move, the **lean** in a walk comes from the feet sliding under it, and it is
  one steady weight shift for the whole walk, not a different one each frame.

Do not fix a walk by adding forward-and-back sway to the body, and do not let a foot swing up and
through the air.

## The attack

- It is an **overhand swing with the left hand**, in both facings.
- Frame 1: the arm is swung **back, behind the body**. Frame 2: it comes **up and over the head** in
  an arc. Frame 3: it strikes **forward and down** through chest height, with a lunge. Frame 4: a
  low **follow-through**. The other hand guards, then is thrown back for balance.
- The body turns into the swing and the arm is long, like the originals'.
- A weapon's four frames give the strike hand's path exactly, in the weapon cell. A person's hand
  has to be within **4.5 px** of the weapon's grip (the grip is an estimate, so a pixel of slack) on every frame, so a weapon placed in it looks
  held. `tools/fit_hands.py` finds those positions.

## Weapons

- A weapon is two strips, **NE** and **SE**, of **4 frames of 48 × 48** (192 × 48), named
  `NAME-attackNE.png` and `NAME-attackSE.png`.
- A frame shows the weapon where it is in that frame of the attack. All the weapons share one
  swing, so their paths agree frame by frame (within 6 px).
- **A weapon is drawn behind the character**, as it will be in the game. The hand and body cover
  its grip.
- Melee weapons can be drawn by code instead of by hand: `tools/make_melee.py` reads the shared swing back from the existing
  strips (each frame's middle, which way the sword points, how foreshortened it looks) and draws a weapon as a list of parts along its
  axis, with the grip at 0, so it is held at the grip and its middle is on the swing's path. Add one to `WEAPONS` there and run
  `python3 tools/make_melee.py --out sprites/weapons`.
- **Bows** are variants of the one bow model in `tools/make_bow.py` (`SPECS`: size, curve, tips, colours), all drawn with the same
  draw animation, as weapon assets `weapon-NAME-ne` and `-se`. Look at them in 3D first: `python3 tools/make_bow.py --variants previews/bows-3d.png`.
- **Every weapon has a display icon**: one 32 x 32 image in the amulets' style, in the "Weapon icons" category, for the shop and any list.
  It is tied to its weapon by **name**, the weapon's asset id without its prefix and facing (`weapon-iron-sword-ne` and `-se` are
  `iron-sword`; the icon is `icon-weapon-iron-sword`). The data says so at both ends: the icon has `icon_for: 'iron-sword'` and each of the weapon's
  assets has `icon: 'icon-weapon-iron-sword'`. `ICONS` in `tools/make_weapon_icons.py` is the one list, and the build stops, naming the weapon,
  if a weapon has no icon or an icon names a weapon that is not there. A new weapon is not finished until it has its line in `ICONS`.
- **Amulets** are shop images only: 32 x 32 pendants on a chain in the "Amulets" category, never worn or animated
  (`tools/make_amulets.py`; add one as a short function and list it in `AMULETS`).

## Weapon style

Weapons are slim and sharp, not blocky: thin shafts, **curved lens-shaped guards** and pommels instead of straight bars, blades that taper long to a point, slender heads, and bows with thin limbs. Their
materials are the spirit realm's: **dark twisted bark** for wood (orchid, plum, grape, eggplant), indigo for wraps, dull bronze for trim, corrupted magenta for gems, and the teal steel, bone and sapphire kept.
Every melee weapon, including the six that began as hand-drawn strips (the originals are kept in `sprites/weapons-original/`), is made from parts in `tools/make_melee.py` on the swing in
`tools/data/weapon_swing.json`, which is a fixed reference so remaking the weapons never moves the hand fits. The display icons (`make_weapon_icons.py`) and the bows (`make_bow.py`) use the same materials.

## Colour

- Everything is painted in the shared palette's colour **roles**, never in raw colours, so a
  character recolours with the hue sliders and swatches.
- The palette is moody on purpose, for a spirit realm with corrupted plants: deep indigo darks, muted mid-tones, and the cyan, violet and pink kept
  vivid as the only glows. **Changing the palette** means editing the hex values in `ROLES` (`tools/extract_poses.py`) with the old ones saved first in
  `LEGACY_HEX`, then `python3 tools/recolor.py` (swaps every sprite PNG's colours by role, no rebuilding from poses) and
  `python3 tools/make_assets.py --png-dir sprites/assets`. Keep each ramp's light-to-dark order. Roles are letters, so nothing else changes.
- A shaded material is a **ramp** of four roles, **light to dark**: lit, base, shade, deep. A ramp
  never gets lighter as it goes down.
- Shading has four steps, set by how the surface faces the light: lit, base, shade, deep. Where a
  nearer part overlaps another, the edge falls into the deep step. That is what separates a leg from
  a body.

## Proportions of a person

A big head on a small, thick body, like the originals (`BODY` in `humanoid.py`): legs 7 px, torso
about 8, head about 9; arms **long** (about 7 px, shoulder to wrist) so the strike can reach out; the
body **bulky** (`bulk` 1.5) so it carries weight; the head ahead of the shoulders (`head_fwd`);
**small feet**, about 3.4 px long (`foot_rx`), like the originals', since long feet make a walk look
like it is shuffling in flippers. Scale is 1.05. The **slim** build is `bulk` 1.0 with narrower
shoulders and hips.

## Area-of-effect spells

A spell that hits an area hits **five plots**: one in the middle and one out in each of the four directions.
Every such spell is drawn on the same cell, **80 x 56**, with the middle plot's centre, on the ground, at
(40, 38), which is the asset's anchor, so any of them can be dropped on a target tile and covers the same five
plots (`tools/make_aoe.py` has the geometry: a plot is a 32 x 16 diamond, and a neighbour sits 16 across and
8 up or down). Draw back to front (NW, NE, middle, SW, SE). **Eight frames**, in the Animations category: it
starts at the middle, spreads out to the four plots, peaks on all five, then dies away. Draw the effect as one
thing, with something linking the plots (the fire's low flames along the shared edges) and soft, rounded
bases instead of flat ones. The fire burst (`tools/make_fire.py`) is the worked example.

## Ability animations

The animations for abilities are their own group: category **Abilities**, folder `sprites/assets/abilities/`, five families that each share a cell size and a placement rule: **bursts** (ground, on the aimed
cell; a five-plot sheet on the 80 x 56 cell of the fire burst for radius 1, and a one-plot **tile** to place on every cell of any other shape), **rings** (round a unit's feet), **icons** (over a head, a pop-up that
plays once and a status icon that loops), **vanish and appear** (a shimmer; appear is vanish reversed) and **ground loops** (a tile per cell that loops). Every sheet is one row of equal frames with an anchor. The
folder's README.md and `abilities.json` are **generated** from `ABILITIES` in `tools/make_abilities.py`, which says for each ability which sheets it plays, where and how, so the game reads one table instead of guessing
from names. The rules the tests check: a burst starts small, grows and fades away; a ground loop that is meant to join its neighbours does (the same pattern repeats from plot to plot); a loop comes back to its first frame; every
sheet an ability names exists. A new ability is one entry in `ABILITIES`; a new colour or style is one entry in its family's module.

## The node map

A group of assets of its own: top-down, **16 x 16 tiles on a dual grid** (a tile for every corner of four land-or-water cells, 16 shapes), an animated sea
under them, and map pins. Everything is category **Node map**, ids `nodemap-*`, folder `sprites/assets/nodemap/`, and the rules for using it are in that
folder's README.md. A new skin changes only colours and textures (`BIOMES` in `tools/make_nodemap.py`); its 16 tiles keep their numbers (corner bits:
top left 1, top right 2, bottom left 4, bottom right 8), repeat their texture every 16 pixels, and join their neighbours, which the tests check.

## Traps

A trap lies flat on a ground tile and has two states: **placed** (one frame, the trap waiting) and **triggered** (an animation). They are category **Traps**, ids `trap-NAME` and
`trap-NAME-triggered`, folder `sprites/assets/traps/`, 32 x 32 frames anchored on the middle of the tile at (16, 24), and the rules for using them are in that folder's README.md. A
triggered animation plays once, at 10 frames a second, and **ends on the spent trap**, which is the picture to keep drawing. A new trap is an entry in `TRAPS` in `tools/make_traps.py`:
a placed state and a list of triggered frames, built from ellipsoids and looked at in 3D (`--model`) before it is drawn.

## The corrupted ground

A second ground set, `sprites/assets/ground-corrupted.png`, laid out **cell for cell like `ground.png`**: a tile has the same shape and the same column and row in both, so a map can swap one set for the other. Its assets
are ids `ground-corrupted-COL-ROW` in the categories **Corrupted Grass, Corrupted Dirt, Corrupted Stone, Corrupted Water** and **Corrupted Nature**, each with the original's label behind "Corrupted", and the same `overlay` shape
as the original. The crates, fences and stairs have no corrupted version. It is made, not hand-drawn: `tools/make_corrupted_ground.py` recolours the original by role (turf teal with lavender patches, soil plum and purple, water
a teal with violet foam and dark teal sides (the shaded side is a new role, `D` Abyss teal, `083a45`), wood bruised grey-purple) and then draws on the tiles that are full blocks: mushrooms on top, vines over the sides, thorns, and now and then a pair of glowing eyes in the dirt. Slopes and edge pieces
keep a clean outline. A tile never loses any of the original's outline and gains no more than 45 pixels past it (the tests check both). The bush, pine, stump, logs and rocks get the same treatment, and the two flowers are mushroom
clusters. Run `make_assets.py` and the sheet is remade first, so it follows the original and the palette.

**Plain grass.** The one full grass block at (0, 0) carries mushrooms, and a map that lays it on every grass tile repeats them. So three **plain** grass blocks, with no mushrooms, vines, thorns or eyes, sit in cells that are empty in both sheets: **(4, 11), (5, 11), (6, 11)**
(ids `ground-corrupted-4-11` ... `-6-11`, labels "Corrupted Grass, plain 1-3", category Corrupted Grass, the same shape and `overlay` as (0, 0)). Each has its own turf pattern. `CLEAN_GRASS` in `tools/make_corrupted_ground.py` is the list; the (0, 0) block keeps its mushrooms as the occasional accent.

## Treasure chests

Three chests on one ground tile, **common, rare and legendary**, each **NE and SE**, **shut** (`chest-RARITY-ne`, one frame) and **opening** (`chest-RARITY-ne-open`, an animation), category **Chests**, folder `sprites/assets/chests/`, 48 x 52 frames anchored at **(24, 40)**, the
middle of the tile on the ground (the cell is wider than a tile because the lid and light swing out). NE has the lock on the lit right-hand face and SE on the shaded left-hand one; NW and SW are flips. The opening is 8 frames at 10 a second, plays once, **starts as the shut chest and ends open**,
the picture to keep drawing. Rarity is size and richness: 24, 30 and 32 pixels wide, wood and iron, then mahogany and teal steel with a sapphire, then violet lacquer and gold with gems, and more treasure inside. They are generated: `tools/make_chest.py` is a small 3D model (hollow body, hinged lid, treasure) drawn in the
ground tiles' projection; `SPECS` is a rarity and `FRAMES` the opening. The folder's README.md says how to place and play them; the tests check the cell, the palette, the growth and the animation.

## The bazaar

The inside of a shop as one still: **`bazaar-shop`**, category **Buildings**, a single **256 x 256** image (`sprites/assets/bazaar-shop.png`) of a cut-away room floating in the air like the ground tiles: a 7 x 7 cell wooden floor
on a slab of the ground's clay with a rock hanging under it, two back walls, and the front and sides open to the camera. It is in the ground's projection (16 across, 8 down a cell) and anchored on the middle of the
floor, at (128, 148). Its wares are the game's own sprites (weapon icons, amulets, crystals and rocks, taken from `sprites/assets`) plus bottles, books and scrolls drawn in the generator, so a changed item shows in the
shop the next time it is built. `tools/make_bazaar.py` is the generator (`--preview` shows it enlarged); the tests keep it on the palette, 256 x 256 and clear of the image's edges.

## Buildings

The building tiles are one-cell, one-level **32 x 32 cubes** in the ground tiles' projection (16 across and 8 down a cell, 16 pixels a level, a storey of two levels), drawn in the quieter palette roles
so they do not fight the ground. Every piece with a direction is drawn **NE and SE** (the feature on the wall that runs NE-SW, or the one that runs NW-SE); a piece without one is the same picture
in both. Textures **repeat every 16 pixels** so stacked and neighbouring pieces line up. Everything is category **Buildings**, ids `bld-*`, folder `sprites/assets/buildings/`, and that folder's README.md says
how to use it. Add a piece with one `add(...)` line in `tools/make_buildings.py`; the tests check the sizes, NE and SE, and that the README's placement recipe redraws the example street.

## The bow animation

Every person has the bow animation: draw to the eyeline, release with a recoil, hold with the bow dropped
slightly (four frames, in both facings). It is made on the person's own model with a separate, swappable bow
(`tools/make_bow.py`), kept in the base set as the optional `bowNE` and `bowSE` poses, and shows up on the
assets page as a "bow draw" animation for them. The checker refuses a generated person without it, so
a new person is not finished until `python3 tools/make_bow.py --bases NAME` has been run. Someone who cannot
draw a bow (the one-armed zombie) is listed with a reason in `BOW_EXEMPT` in `conventions.py`. Animals
are not asked.

## Eyes

A person's open eyes are **tall, thin, vertical slits, 3 pixels tall**, like the original bases' and the
other creatures' black eyes, never single dots. Every person built on the humanoid model has them (`tall_eyes`,
on by default), and the checker refuses a build that turns them off. Shut eyes stay a short line. A build
may add whites beside the slit (`eye_white`) or bring the face out of a hood (`eye_reach`), but the slit
stays.

## Builds

A person can be built **slim** instead of the standard heavy build, on purpose. A slim build keeps
the same head, limbs and reach (so every pose and the weapon hand carry over) but has less bulk
through the body, and may carry up to **20% less** weight than the lightest original (the standard
build: 8% less). Builds are declared in `BUILDS` and `BASE_BUILDS` in `conventions.py`, so a slim
character is a choice you can see, not a loophole. A figure lighter than that reads as floating.

### The sleek build and the four humans

There are four generic people: **Human** and **Slim** (the first two, unchanged) and **Human (sleek)** and **Slim (sleek)**, which are narrower and less blocky (bulk 1.1 and 0.75 against 1.5 and 1.0, narrower
shoulders and hips and a slightly narrower head) and a little larger overall, in the spirit realm's colours: ashen skin, and violet or teal hair. The sleek build is declared in `BUILDS` (it may carry
less weight, 0.6 of the lightest original), and a build can say its own `scale` in its body. The sleek people have their own tuned numbers (`tools/data/human-sleek_*.json`, `slim-sleek_*.json`).

## Look at the 3D model before making sprites

Making the pixel sprites is slow, and it throws away detail, so a design is judged first as the model it
is: the same ellipsoids, camera and light, drawn smooth, large and in the real colours, from five
angles (face, SE, side, NE, back). Every creator takes `--model`:

```bash
python3 tools/make_NAME.py --model previews/NAME-3d.png                       the standing pose
python3 tools/make_NAME.py --model previews/NAME-3d.png --pose attack --frame 2
```

It takes about three seconds and makes no sprites. Change the model until it looks right there, show it
to whoever is approving the design, and only then generate the sprites. The face view is the one to
check for anything worn on the head.

## Making something new

1. **A person**: copy `tools/make_human.py` and change the name, colours, hair or add accessories.
   The poses, lean, weight and weapon hand come with it. The lean and hand numbers
   (`tools/data/humanoid_lean.json`, `humanoid_hands.json`) were tuned for the standard build; if you
   change the proportions a lot, re-run `tools/tune_lean.py NAME` then `tools/fit_hands.py NAME`.
   Each person has numbers of their own (`tools/data/NAME_*.json`), so tuning one never changes
   another. `tune_lean.py NAME --only walking` tunes one pose and leaves the others exactly as they
   are: use it when only one pose needs work. Add a new person to `CREATORS` in `conventions.py`.
2. **A creature**: copy `tools/make_dog.py` (four legs) or `tools/make_rat.py`, and change the
   anatomy and poses.
3. **A weapon**: draw the two strips and put them in `sprites/weapons/`, then
   `python3 tools/make_assets.py`.
4. Look at it in 3D first (above), and get it approved. Then generate, merge, and check:

```bash
python3 tools/make_NAME.py sprites/NAME
python3 tools/make_bow.py --bases NAME            # every person has the bow animation
python3 tools/extract_poses.py --merge NAME=sprites/NAME
python3 tools/check_conventions.py
```

If generation reports a problem it says which rule and which frame, and writes nothing.

The checker itself is tested (each rule is shown a good frame and a broken one):

```bash
python3 -m unittest discover -s tools -p 'test_*.py'
```

## Changing a convention

If the rules turn out to be wrong, do not just edit a pose to dodge a check. Re-measure from the
originals, change the number in `tools/conventions.py` **and** this file together, and re-run
`check_conventions.py` so everything is held to the new rule.

## What the game reads

Moved to [AGENTS.md](AGENTS.md#what-the-game-reads), with the rest of how the repo is worked on.
