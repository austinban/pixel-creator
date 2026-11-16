#!/usr/bin/env python3
"""The ability animations as one group: which sheet each ability uses, and where and how to play it.

The pictures are drawn by the family modules (make_burst.py, make_ring.py, make_icons.py, make_vanish.py, make_ground_fx.py, with fx.py their drawing helpers). This file ties them to the abilities
in the game's ability kit (scripts/content/ability_kit.gd there is the source of truth for names and areas): ABILITIES says, for every ability, its area and what to play where. From it `write_package`
writes `abilities.json` (for the game to read) and `README.md` (for people), so the table, the JSON and the README cannot disagree, and the tests check every sheet an ability names exists.

    python3 tools/make_assets.py --png-dir sprites/assets        writes sprites/assets/abilities/ (the sheets, abilities.json and README.md)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_burst  # noqa: E402
import make_ground_fx  # noqa: E402
import make_icons  # noqa: E402
import make_hits  # noqa: E402
import make_impact  # noqa: E402
import make_ring  # noqa: E402
import make_vanish  # noqa: E402

FOLDER = 'abilities'
CATEGORY = 'Abilities'

# What an effect is placed on. 'aimed' is the cell the ability was aimed at, 'target' the unit there, 'caster' the unit using it.
# 'cells:radius1' and 'cells:radius2' mean every cell within that many steps of the aimed cell (a diamond, counted in cells: 5 and 13); 'cells:line3' is the three cells of a wall.
def fx_(sheet, at, how, note=''):
    return dict(sheet=sheet, at=at, how=how, **({'note': note} if note else {}))


ABILITIES = {
    # --- bursts: ground effects on the aimed cell -------------------------------------------------------
    'crimson-bolt': dict(label='Crimson Bolt', area='1 tile', family='burst', effects=[fx_('burst-crimson-tile', 'aimed', 'once')]),
    'sanguine-burst': dict(label='Sanguine Burst', area='radius 1', family='burst', effects=[fx_('burst-blood', 'aimed', 'once', 'the five-plot sheet covers the whole area')]),
    'spore-cloud': dict(label='Spore Cloud', area='radius 1', family='burst', effects=[fx_('burst-spore', 'aimed', 'once', 'the five-plot sheet covers the whole area')]),
    'static-surge': dict(label='Static Surge', area='radius 2', family='burst', effects=[fx_('burst-static-tile', 'cells:radius2', 'once', 'one tile on each of the 13 cells; start each a frame later for each step from the aimed cell')]),
    'downpour': dict(label='Downpour', area='radius 2', family='burst', effects=[fx_('burst-rain-tile', 'cells:radius2', 'once', 'one tile on each of the 13 cells; start each a frame later for each step from the aimed cell')]),
    'quake': dict(label='Quake', area='radius 1', family='burst', effects=[fx_('burst-dust', 'aimed', 'once', 'the five-plot sheet covers the whole area')]),
    'tremor': dict(label='Tremor (boss)', area='radius 2', family='burst', effects=[fx_('burst-dust-tile', 'cells:radius2', 'once', 'one tile on each of the 13 cells; start each a frame later for each step from the aimed cell')]),
    'raise': dict(label='Raise', area='1 tile', family='burst', effects=[fx_('burst-dust-tile', 'aimed', 'once', 'the game changes the terrain itself on the same frame as the dust peaks (frame 4)')]),
    'lower': dict(label='Lower', area='1 tile', family='burst', effects=[fx_('burst-dust-tile', 'aimed', 'once', 'the game changes the terrain itself on the same frame as the dust peaks (frame 4)')]),
    'stone-wall': dict(label='Stone Wall', area='line of 3, 1 wide', family='burst', effects=[fx_('burst-dust-tile', 'cells:line3', 'once', 'one tile on each of the three cells')]),
    'shove': dict(label='Shove', area='1 tile', family='burst', effects=[fx_('burst-dust-small-tile', 'target', 'once', 'a small puff where the unit was pushed from')]),
    # --- ring pulses: effects on or round a unit --------------------------------------------------------
    'rally': dict(label='Rally', area='radius 2, centred on the caster', family='ring', effects=[fx_('ring-rally', 'caster', 'once', 'the large ring spreads over the whole radius')]),
    'inspire': dict(label='Inspire', area='1 tile', family='ring', effects=[fx_('ring-inspire', 'target', 'once')]),
    'cleanse': dict(label='Cleanse', area='1 tile', family='ring', effects=[fx_('ring-cleanse', 'target', 'once')]),
    'sever': dict(label='Sever', area='1 tile', family='ring', effects=[fx_('ring-sever', 'target', 'once', 'the ring forms and breaks into pieces')]),
    'ward': dict(label='Ward', area='1 tile', family='ring', effects=[
        fx_('ring-ward-form', 'target', 'once', 'when it is cast'),
        fx_('ring-ward-hold', 'target', 'loop', 'while the ward stands, over the unit'),
        fx_('ring-ward-break', 'target', 'once', 'when it absorbs a hit, in place of the hold; the same break as Sever')]),
    'climb': dict(label='Climb', area='caster only', family='ring', effects=[fx_('ring-climb', 'caster', 'once')]),
    'dash': dict(label='Dash', area='caster only', family='ring', effects=[
        fx_('ring-dash-ne', 'caster', 'once', 'when the dash goes up the screen (NE); NW is this sheet flipped left to right'),
        fx_('ring-dash-se', 'caster', 'once', 'when the dash goes down the screen (SE); SW is this sheet flipped left to right')]),
    # --- pop-up icons over the head ---------------------------------------------------------------------
    'mark': dict(label='Mark', area='1 tile', family='icon', effects=[fx_('icon-mark-pop', 'target-head', 'once')]),
    'silence': dict(label='Silence', area='1 tile', family='icon', effects=[fx_('icon-silence-pop', 'target-head', 'once')]),
    'stun': dict(label='Stun', area='1 tile', family='icon', effects=[fx_('icon-stun-pop', 'target-head', 'once')]),
    'charm': dict(label='Charm', area='1 tile', family='icon', effects=[fx_('icon-charm-pop', 'target-head', 'once')]),
    'confuse': dict(label='Confuse', area='1 tile', family='icon', effects=[fx_('icon-confuse-pop', 'target-head', 'once')]),
    # --- vanish and appear ------------------------------------------------------------------------------
    'blink': dict(label='Blink', area='1 tile', family='vanish', effects=[fx_('vanish-violet', 'start-cell', 'once', 'the unit shrinks to a point as it plays'), fx_('appear-violet', 'end-cell', 'once', 'the unit grows back out')]),
    'swap': dict(label='Swap', area='2 tiles (both units)', family='vanish', effects=[fx_('vanish-violet', 'both-units-old-cell', 'once'), fx_('appear-violet', 'both-units-new-cell', 'once')]),
    'call-wolf': dict(label='Call Wolf', area='1 tile', family='vanish', effects=[fx_('appear-blue', 'summon-cell', 'once', 'when it arrives'), fx_('vanish-blue', 'summon-cell', 'once', 'when it expires')]),
    'call-decoy': dict(label='Call Decoy', area='1 tile', family='vanish', effects=[fx_('appear-yellow', 'summon-cell', 'once', 'when it arrives'), fx_('vanish-yellow', 'summon-cell', 'once', 'when it expires')]),
    'raise-guardian': dict(label='Raise Guardian', area='1 tile', family='vanish', effects=[fx_('appear-stone', 'summon-cell', 'once', 'when it arrives'), fx_('vanish-stone', 'summon-cell', 'once', 'when it expires')]),
    # --- ground loops: surfaces that last several rounds ------------------------------------------------
    'mire': dict(label='Mire', area='radius 1', family='ground', effects=[fx_('surface-mire', 'cells:radius1', 'loop', 'one tile on each of the 5 cells; they join into one surface')]),
    'slick-ground': dict(label='Slick Ground', area='radius 1', family='ground', effects=[fx_('surface-slick', 'cells:radius1', 'loop', 'one tile on each of the 5 cells; they join into one surface')]),
    'fire-wall': dict(label='Fire Wall', area='line of 3', family='ground', effects=[fx_('surface-firewall', 'cells:line3', 'loop', 'one tile on each of the three cells, each started on a different frame so the flames do not move together')]),
    'thornwall': dict(label='Thornwall', area='line of 3', family='ground', effects=[fx_('surface-thorns', 'cells:line3', 'loop', 'one tile on each of the three cells for as long as the thorns stand; start each on a different frame')]),
    # --- impacts (make_impact.py): what used to borrow the vine, the fire burst or the petals -------------
    'use-fire-bomb': dict(label='Fire Bomb (supply)', area='radius 1, thrown 2 tiles', family='burst', effects=[fx_('burst-explosion', 'aimed', 'once', 'the five-plot sheet covers the whole area')]),
    'use-blast-charge': dict(label='Blast Charge (supply)', area='radius 1, thrown 2 tiles', family='burst', effects=[fx_('burst-explosion', 'aimed', 'once', 'the five-plot sheet covers the whole area')]),
    'grasp': dict(label='Grasp (Zombie)', area='1 tile, adjacent', family='burst', effects=[fx_('burst-grasp-tile', 'target', 'once', 'hands clawing out of the ground at the target')]),
    'mind-spore': dict(label='Mind Spore', area='1 tile', family='burst', effects=[fx_('burst-mindspore-tile', 'target', 'once')]),
    'dominion': dict(label='Dominion', area='1 tile', family='burst', effects=[fx_('burst-mindspore-tile', 'target', 'once')]),
    'sap': dict(label='Sap', area='1 tile', family='burst', effects=[fx_('burst-mindspore-tile', 'target', 'once')]),
    'use-healing-draught': dict(label='Healing Draught (supply)', area='1 tile, adjacent', family='burst', effects=[fx_('burst-potion-tile', 'target', 'once')]),
    'use-greater-draught': dict(label='Greater Draught (supply)', area='1 tile, adjacent', family='burst', effects=[fx_('burst-potion-tile', 'target', 'once')]),
    'use-grand-elixir': dict(label='Grand Elixir (supply)', area='1 tile, adjacent', family='burst', effects=[fx_('burst-elixir-tile', 'target', 'once')]),
    'bark': dict(label='Bark', area='cone, 3 deep', family='burst', effects=[fx_('burst-wave-tile', 'cells:line', 'once', 'one tile on each cell of the cone, nearest the caster first, so it fans out')]),
    'scythe-sweep': dict(label='Scythe Sweep (Mantis)', area='cone: the cell in front and the three beyond', family='sweep', effects=[
        fx_('sweep-scythe', 'caster-facing', 'once', 'one stroke over the whole cone, at the attacker\'s feet: `sweep-scythe-ne` when it faces up the screen, `-se` down it; NW and SW are those flipped left to right')]),
    # --- the same art, put to work where there was none ----------------------------------------------
    'spore-burst': dict(label='Spore Burst (Puffball)', area='radius 1', family='burst', effects=[fx_('burst-spore', 'aimed', 'once')]),
    'spore-shot': dict(label='Spore Shot (Blood Mushroom)', area='1 tile', family='burst', effects=[fx_('burst-spore-tile', 'target', 'once')]),
    'totem-blast': dict(label='Totem Blast', area='radius 3 foes', family='burst', effects=[fx_('burst-static-tile', 'target', 'once', 'on each foe it burns')]),
    'use-cleansing-salve': dict(label='Cleansing Salve (supply)', area='1 tile, adjacent', family='ring', effects=[fx_('ring-cleanse', 'target', 'once')]),
    'use-revive-tonic': dict(label='Revive Tonic (supply)', area='1 fallen ally, adjacent', family='ring', effects=[fx_('ring-inspire', 'aimed', 'once')]),
    'warning-shot': dict(label='Warning Shot', area='1 tile', family='icon', effects=[fx_('icon-mark-pop', 'target-head', 'once')]),
    'disengage': dict(label='Disengage', area='caster only', family='ring', effects=[fx_('ring-dash', 'caster-facing', 'once', 'Dash\'s ring, the way the caster faces')]),
    'snare': dict(label='Snare', area='1 tile', family='burst', effects=[fx_('burst-dust-small-tile', 'aimed', 'once', 'a puff as the trap is set')]),
    'bear-trap': dict(label='Bear Trap', area='1 tile', family='burst', effects=[fx_('burst-dust-small-tile', 'aimed', 'once', 'a puff as the trap is set')]),
    'spike-pit': dict(label='Spike Pit', area='1 tile', family='burst', effects=[fx_('burst-dust-small-tile', 'aimed', 'once', 'a puff as the trap is set')]),
    'trapmaster': dict(label='Trapmaster', area='1 tile', family='burst', effects=[fx_('burst-dust-small-tile', 'aimed', 'once', 'a puff as the trap is set')]),
    'caltrops': dict(label='Caltrops', area='line of 3', family='burst', effects=[fx_('burst-dust-small-tile', 'cells:line3', 'once', 'a puff on each cell as the traps are set')]),
    'use-caltrop-pouch': dict(label='Caltrop Pouch (supply)', area='line of 3', family='burst', effects=[fx_('burst-dust-small-tile', 'cells:line3', 'once', 'a puff on each cell as the traps are set')]),
    # --- hits (make_hits.py): a flash on whoever a shot struck -------------------------------------------
    'headshot': dict(label='Headshot', area='1 tile', family='burst', effects=[fx_('burst-crit-tile', 'target', 'once', 'a crit star on the one struck')]),
    'called-shot': dict(label='Called Shot', area='1 tile', family='burst', effects=[fx_('burst-impact-tile', 'target', 'once', 'a heavy blow')]),
    'piercing-shot': dict(label='Piercing Shot', area='1 tile', family='burst', effects=[fx_('burst-streak-tile', 'target', 'once', 'a streak passing through')]),
    'hamstring': dict(label='Hamstring', area='1 tile', family='burst', effects=[fx_('burst-nick-tile', 'target', 'once', 'a nick low on the legs')]),
    'deadeye': dict(label='Deadeye', area='caster only', family='icon', effects=[fx_('icon-sight-pop', 'target-head', 'once', 'over the caster, who is the one it lands on')]),
    'minefield': dict(label='Minefield', area='radius 1', family='burst', effects=[fx_('burst-dust-small-tile', 'cells:radius1', 'once', 'a puff on each cell as the mines are set')]),
}

# Looping status icons. The ones with their own art are here; the others reuse what exists.
STATUSES = {
    'mark': fx_('icon-mark-loop', 'unit-head', 'loop'), 'silence': fx_('icon-silence-loop', 'unit-head', 'loop'), 'stun': fx_('icon-stun-loop', 'unit-head', 'loop'),
    'charm': fx_('icon-charm-loop', 'unit-head', 'loop'), 'confuse': fx_('icon-confuse-loop', 'unit-head', 'loop'),
    'soaked': fx_('ring-status-soaked', 'unit-feet', 'loop'), 'shocked': fx_('ring-status-shocked', 'unit-feet', 'loop'), 'spored': fx_('ring-status-spored', 'unit-feet', 'loop'),
    'rooted': fx_('vine', 'unit-feet', 'existing', 'the existing vine animation, as it is'), 'snared': fx_('vine', 'unit-feet', 'existing', 'the existing vine animation, as it is'),
    'mired': fx_('vine', 'unit-feet', 'existing', 'the existing vine animation, as it is'),
    'crippled': fx_('icon-cripple-loop', 'unit-head', 'loop'), 'trapped': fx_('icon-jaw-loop', 'unit-head', 'loop'), 'deadeye': fx_('icon-sight-loop', 'unit-head', 'loop'),
}

# Nothing new is drawn for these.
REUSED = {
    'root': dict(label='Root', effects=[fx_('vine', 'target-feet', 'existing', 'the existing vine animation, as it is')]),
    'hook': dict(label='Hook', effects=[fx_('vine', 'target-feet', 'existing',
                                           'the existing vine recoloured grey, lashing out and pulling the target in; recolour by swapping roles z to q, A to p, B to l, s to k (the bud and the leaves go with them, the earth stays)')],
                 recolour={'z': 'q', 'A': 'p', 'B': 'l', 's': 'k'}),
}

# How cells sit on the screen: moving one cell along x (SE) moves the drawing (16, 8), along y (SW) moves it (-16, 8): the same as the ground tiles and the buildings.
def offsets(radius):
    return [dict(dx=i, dy=j, px=16 * (i - j), py=8 * (i + j), distance=abs(i) + abs(j))
            for i in range(-radius, radius + 1) for j in range(-radius, radius + 1) if abs(i) + abs(j) <= radius]


FAMILIES = [make_burst, make_ring, make_icons, make_vanish, make_ground_fx, make_impact, make_hits]


def build_assets():
    assets = []
    for module in FAMILIES:
        assets += module.build_assets()
    return assets


def sheet_info(asset):
    return dict(file=f'{asset["id"]}.png', frames=asset['cols'] * asset['rows'], cell=[asset['w'], asset['h']], fps=asset['fps'], loops=bool(asset['fx'].get('loops')),
                anchor=[asset['anchor']['x'], asset['anchor']['y']], label=asset['label'])


def write_package(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    assets = build_assets()
    sheets = {a['id']: sheet_info(a) for a in assets}
    data = {
        'about': 'The ability animations in this folder, and which ability plays which. See README.md beside this file. The ability names and areas come from scripts/content/ability_kit.gd in the game.',
        'frameRule': 'every sheet is one row of equal frames, left to right; play them in order at `fps`; `loops` sheets repeat, the others play once and are done',
        'cellStep': [16, 8],
        'offsets': {'radius1': offsets(1), 'radius2': offsets(2)},
        'tileDelay': 'for a radius-2 burst made of tiles, start each tile (distance from the aimed cell) frames after the middle one, at 1 frame a step',
        'sheets': sheets,
        'abilities': ABILITIES,
        'statuses': STATUSES,
        'reused': REUSED,
    }
    (folder / 'abilities.json').write_text(json.dumps(data, indent=1))
    (folder / 'README.md').write_text(readme(sheets))


def readme(sheets):
    def sheet_row(name):
        s = sheets[name]
        return f'| `{s["file"]}` | {s["label"]} | {s["frames"]} @ {s["fps"]} | {s["cell"][0]} x {s["cell"][1]} | ({s["anchor"][0]}, {s["anchor"][1]}) | {"loops" if s["loops"] else "once"} |'

    lines = ['# Ability animations', '',
             'The animations for the abilities: bursts on the ground, rings round a unit, icons over a head, a vanish and appear shimmer, and surfaces that stay on the ground. Everything for them is in this',
             'folder, on the Assets page it is the **Abilities** category, and **`abilities.json` is the table the game reads**: for every ability it says which sheet to play, where, and how. The ability names',
             'and areas are the game\'s (`scripts/content/ability_kit.gd`); the existing `fire-burst`, `heal-petals` and `vine` stay as they are, and are not in this folder.', '',
             '## How to play one', '',
             '- A sheet is **one row of equal frames**, left to right. Play them in order at the sheet\'s frame rate. A sheet that **loops** repeats; any other plays **once** and is done (draw nothing after the last frame).',
             '- Every sheet has an **anchor**, a point in its frame. Put the anchor on the thing the effect belongs to: **the middle of the ground tile** for a burst or a ground loop (a five-plot burst: the middle of the',
             '  middle tile), **the unit\'s feet** for a ring or a vanish, and **the point just above the unit\'s head** for an icon. Draw it **over the ground and under the units that stand on it**, except icons, which go over everything.',
             '- A ground tile is a 32 x 16 diamond. Moving one cell along x (down and right) moves the drawing **(16, 8)**; along y (down and left) **(-16, 8)**. `abilities.json` > `offsets` has the pixel offset of every cell in',
             '  a radius-1 (5 cells) and radius-2 (13 cells) diamond, with its distance from the middle.',
             '- **Five-plot sheets** (`burst-NAME`, 80 x 56) cover a radius-1 area in one picture: put the anchor on the aimed cell. **Tile sheets** (`burst-NAME-tile`) are one cell; place one on every cell of the area',
             '  (radius 2 is 13 tiles, a wall is 3), and for a radius-2 burst start each tile one frame later for each step from the aimed cell, so it spreads outward.',
             '- **Vanish and appear** are the same shimmer in two directions: `vanish-X` gathers the unit into a point (shrink the unit\'s own sprite to that point as it plays) and `appear-X` is the same frames reversed, so',
             '  it grows back out. Play `vanish-X` where a unit leaves, `appear-X` where it arrives, and `vanish-X` again when a summon expires. Nothing needs playing backwards.',
             '- **Dash** has an NE and an SE sheet. The NW and SW ones are those **flipped left to right**.',
             '- **Ground loops** (mire, slick ground, fire wall) are one tile per cell and loop for as long as the effect lasts. The mire and the slick are drawn to **join** the next tile, so five of them are one surface. Start the fire wall\'s',
             '  tiles on different frames so the flames do not move in step.', '']
    families = {'burst': 'Bursts', 'sweep': 'Sweeps', 'ring': 'Rings', 'icon': 'Icons over the head', 'vanish': 'Vanish and appear', 'ground': 'Ground loops'}
    lines += ['## Which ability plays what', '', 'Area is in cells, a diamond (steps along the two axes added together) round the aimed cell. `once` plays one time, `loop` repeats while the effect lasts.', '']
    for fam, title in families.items():
        lines += [f'### {title}', '', '| Ability | Area | Plays | On | How | Note |', '|---|---|---|---|---|---|']
        for key, a in ABILITIES.items():
            if a['family'] != fam:
                continue
            for e in a['effects']:
                lines.append(f'| {a["label"]} | {a["area"]} | `{e["sheet"]}` | {e["at"]} | {e["how"]} | {e.get("note", "")} |')
        lines.append('')
    lines += ['### Statuses (looping icons)', '', 'A status that lasts shows its icon on the unit and loops it for as long as the status does.', '', '| Status | Plays | On | Note |', '|---|---|---|---|']
    for key, e in STATUSES.items():
        lines.append(f'| {key.capitalize()} | `{e["sheet"]}` | {e["at"]} | {e.get("note", "")} |')
    lines += ['', '### Reused, nothing new', '', '| Ability | Plays | Note |', '|---|---|---|']
    for key, r in REUSED.items():
        for e in r['effects']:
            lines.append(f'| {r["label"]} | `{e["sheet"]}` | {e["note"]} |')
    lines += ['', '## The sheets', '', '| File | What it is | Frames @ fps | Cell | Anchor | Plays |', '|---|---|---|---|---|---|']
    lines += [sheet_row(n) for n in sheets]
    lines += ['', '## Making a new one', '',
              'Each family is a small module (`tools/make_burst.py`, `make_ring.py`, `make_icons.py`, `make_vanish.py`, `make_ground_fx.py`, sharing `tools/fx.py`). A new colour or style of an existing family is one entry in that module; a new ability is one',
              'entry in `ABILITIES` in `tools/make_abilities.py`, naming the sheets it plays. Then `python3 tools/make_assets.py --png-dir sprites/assets` rebuilds the sheets, `abilities.json` and this README, and the tests check that every sheet an ability',
              'names exists. Preview a family with `--preview` (for example `python3 tools/make_burst.py --preview previews/bursts.png`). The sheets are generated by code, so change the code and rebuild instead of editing the PNGs.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    write_package(Path(__file__).resolve().parent.parent / 'sprites' / 'assets' / FOLDER)
    print('wrote', FOLDER)
