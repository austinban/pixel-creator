#!/usr/bin/env python3
"""The terrain sets: which ground goes with which pieces, and what can be swapped for what.

Two layers, both data (nothing here draws anything):

    GROUPS    a group is a handful of pieces that are one kind of thing: the temperate trees, the natural slabs, the graveyard stones. It says its ROLE (what it does
              on a map), which GROUND it FITS (`plain`, `corrupted`, or `any`: the two ground sheets are cell for cell the same, so a piece that fits `any` is drawn on either),
              its STYLE (so a set stays cohesive: blocky pieces beside blocky ones) and a note.
    SETS      a set is a look for a whole map: one ground theme, a mix of surfaces, and weighted groups for each role. A set only lists groups that fit its ground, and
              the test checks that.

A group's pieces are named by `ids` (exact asset ids), `prefix` (every asset whose id starts with it) or `regex` (every id that matches it), found in assets/data.js. A group with `pending: True` has no
assets built yet (or not wired in); it is listed so the set is complete on paper, and it is skipped until it matches something.

    python3 tools/make_sets.py        writes assets/sets.js, sprites/assets/sets/sets.json and SETS.md from this file and assets/data.js
"""

# --- ground ---------------------------------------------------------------------------------------
GROUNDS = {
    'plain': dict(label='Plain', sheet='ground', note='The original ground: green turf, brown soil, blue water.'),
    'corrupted': dict(label='Corrupted', sheet='ground-corrupted', note='Teal turf, plum soil, dark teal water; the same layout as plain, cell for cell. (0, 0) carries mushrooms; use CLEAN_GRASS for everyday turf.'),
}
CLEAN_GRASS = [(4, 11), (5, 11), (6, 11)]                       # plain turf on the corrupted sheet (see AGENTS.md)
PLAIN_GRASS = [((0, 0), 10), ((9, 1), 2), ((8, 7), 1), ((10, 9), 1), ((10, 7), 1), ((9, 8), 1), ((8, 9), 1)]     # plain, a dirt patch, stepping stones

# --- roles ----------------------------------------------------------------------------------------
ROLES = {
    'scatter': 'one-cell scenery that fills a map: trees, bushes, small rocks, flowers, mushrooms. Blocks its cell (or not: see the group).',
    'platform': 'multi-cell pieces with a flat top at a whole level a unit can walk on (`walkable`, `top_cover` in the asset record).',
    'blocker': 'multi-cell scenery that blocks every cell of its footprint.',
    'crossing': 'a piece that spans water or a gap (a bridge) and joins land to land.',
    'cover': 'low, partial obstacles that give cover without blocking the way round (fences, crates, walls).',
    'structure': 'buildings and their ruins, one or many cells, placed by rule rather than scattered.',
    'decor': 'flat or tiny detail that changes the look and nothing else (decals, flowers).',
    'hazard': 'something that hurts or changes a unit that stands on it (traps, vents).',
    'connector': 'stairs and ramps that join one height to the next; they attach to a platform of the same number of levels (see their `connector` field).',
    'overlay': 'a screen-space weather layer drawn over the whole map (rain, fog, haze); see the weather README for blend, opacity and scroll.',
}

# --- groups ---------------------------------------------------------------------------------------
# fits: plain, corrupted or any. style: what it looks like beside its neighbours (`natural` worn stone, `blocky` straight faces and courses, `timber`, `fungal`, `bone`, ...).
GROUPS = {
    'trees-temperate': dict(label='Temperate trees', role='scatter', fits='plain', style='natural', prefix=None,
                            ids=['tree-tall-pine', 'tree-spruce', 'tree-poplar', 'tree-tall-oak', 'tree-broad-oak', 'tree-birch', 'tree-small-pine'],
                            note='Healthy trees. In a corrupted set use the mushroom trees: they are the same trees gone wrong (the game flips between them on the title screen).'),
    'trees-dead': dict(label='Dead tree', role='scatter', fits='any', style='natural', ids=['tree-dead-tree'], note='Bare and grey; fits either ground.'),
    'bushes': dict(label='Bushes and hedges', role='scatter', fits='plain', style='natural', ids=['bush-berry-bush', 'bush-hedge']),
    'mushroom-trees': dict(label='Mushroom trees', role='scatter', fits='corrupted', style='fungal', prefix='fungus-',
                           note='The corrupted counterpart of the trees. `fungus-toadstool` is 2 x 2 and walkable (not used by the builder yet).'),
    'ground-props-plain': dict(label='Plain ground props', role='scatter', fits='plain', style='natural',
                               ids=['ground-0-3', 'ground-1-3', 'ground-0-4', 'ground-0-5', 'ground-1-5', 'ground-2-8', 'ground-4-8'],
                               note='From the ground sheet: bush, pine, two rocks, a stump and two flowers.'),
    'ground-props-corrupted': dict(label='Corrupted ground props', role='scatter', fits='corrupted', style='fungal',
                                   ids=['ground-corrupted-0-3', 'ground-corrupted-1-3', 'ground-corrupted-0-4', 'ground-corrupted-0-5', 'ground-corrupted-1-5'],
                                   note='The same cells on the corrupted sheet: blight bush, blight tree, blight rocks, spore stump.'),
    'logs': dict(label='Logs', role='cover', fits='any', style='timber', ids=['ground-0-6', 'ground-1-6', 'ground-0-7', 'ground-0-8', 'ground-1-8', 'ground-1-9']),
    'fences': dict(label='Fences', role='cover', fits='any', style='timber', ids=['ground-2-6', 'ground-3-6', 'ground-4-6', 'ground-2-7', 'ground-4-7', 'ground-3-8']),
    'crates': dict(label='Crates', role='cover', fits='any', style='timber', ids=['ground-2-5', 'ground-3-5', 'ground-4-5', 'ground-5-5', 'ground-6-5', 'ground-7-5']),
    'rocks-ledge': dict(label='Blocky ledges', role='platform', fits='any', style='blocky', prefix='rock-ledge-',
                        note='Walkable, flat topped, 1 or 2 levels, straight faces with courses of stone. Fits either ground; best beside buildings and walls.'),
    'rocks-slab': dict(label='Natural slabs', role='platform', fits='any', style='natural', prefix='rock-slab-',
                       note='Walkable, flat topped, 1 or 2 levels, worn stone. The natural twin of the ledges: swap one for the other and the footprint is the same.'),
    'rocks-crag': dict(label='Blocky crags', role='blocker', fits='any', style='blocky', prefix='rock-crag-', note='Not walkable. Broken peaks, one cell each.'),
    'rocks-stone': dict(label='Natural stones', role='blocker', fits='any', style='natural', prefix='rock-stone-',
                        note='Not walkable. Boulders, a standing stone, outcrops and scree. The natural twin of the crags.'),
    'bridge-plank': dict(label='Rickety bridge', role='crossing', fits='plain', style='timber', ids=['bridge'],
                         note='The original one-cell bridge frames, laid cell by cell over sunken water (see BRIDGES.md).'),
    'bridges-stone': dict(label='Stone arch bridges', role='crossing', fits='any', style='blocky', prefix='bridge-arch-',
                          note='3 and 5 cells, along either axis, a deck one level up. Walkable.'),
    'bridges-plank': dict(label='Plank bridges', role='crossing', fits='any', style='timber', prefix='bridge-plank-',
                          note='Rotted planks on posts, 3 and 5 cells, along either axis. Walkable.'),
    'bridges-corrupt': dict(label='Corrupted bridges', role='crossing', fits='corrupted', style='fungal', prefix='bridge-corrupt-',
                            note='Plum stone with vines and mushrooms, 3 and 5 cells. Walkable.'),
    'bridges-broken': dict(label='Broken bridges', role='crossing', fits='any', style='blocky', prefix='bridge-broken-',
                           note='A 5-cell arch bridge with a gap: the two ends are walkable, the middle is not. Scenery for a ruined crossing.'),
    'stairs': dict(label='Ground stairs', role='cover', fits='any', style='blocky', ids=['ground-0-1', 'ground-1-1'], note='Two stair cubes from the ground sheet.'),
    'stairs-new': dict(label='Stairs and ramps', role='connector', fits='any', style='blocky', prefix='stair-',
                       note='1 and 2 levels, stairs, ramps and ramps ending in a ledge, in four directions; the high end is flush with a ledge or slab of the same height.'),
    'stairs-scaffold': dict(label='Scaffold stairs and ramps', role='connector', fits='any', style='timber', prefix='scaffold-',
                            note='Wood plank twins of the stone stairs: the same 24 footprints, heights and directions, open timber frames. The stepped ones have no rail; the ramps do.'),
    'ruins-walls': dict(label='Ruined walls', role='cover', fits='any', style='blocky', regex=r'^ruin-(wall|corner|tee|arch)-(?!2x1|1x2)(?!.*-grown$).*',
                        note='Broken walls at half, one and two levels, corners, tees and arches: cover and line-of-sight blockers, never walkable. Each says `cover` low, high or full.'),
    'ruins-walls-grown': dict(label='Overgrown ruined walls', role='cover', fits='any', style='fungal', regex=r'^ruin-(wall|corner|tee|arch)-(?!2x1|1x2).*-grown$',
                              note='The same walls with vines, moss and mushrooms: for corrupted maps and old ruins.'),
    'ruins-walls-long': dict(label='Long ruined walls', role='blocker', fits='any', style='blocky', regex=r'^ruin-wall-(2x1|1x2)-.*', note='Two cells long, one or two levels: cover and sight blockers.'),
    'ruins-heaps': dict(label='Rubble heaps', role='blocker', fits='any', style='blocky', regex=r'^ruin-heap-(?!.*-grown$).*', note='Low rubble, 1 x 1 to 2 x 2 and L.'),
    'ruins-heaps-grown': dict(label='Overgrown rubble', role='blocker', fits='any', style='fungal', regex=r'^ruin-heap-.*-grown$'),
    'ruins-floors': dict(label='Foundation floors', role='platform', fits='any', style='blocky', regex=r'^ruin-floor-(?!.*-grown$).*', note='Half-level footings with flags missing; walkable.'),
    'ruins-floors-grown': dict(label='Overgrown floors', role='platform', fits='any', style='fungal', regex=r'^ruin-floor-.*-grown$', note='Walkable.'),
    'low-hay': dict(label='Haybales and crate piles', role='platform', fits='any', style='timber', regex=r'^low-(hay|crates)-.*',
                    note='1 or 2 levels, some stepped, walkable: climb them. Stepped pieces have the tall cell at the back.'),
    'low-stalls': dict(label='Stalls and sheds', role='platform', fits='any', style='timber', regex=r'^low-(stall|shed)-.*',
                       note='Flat roofs are walkable; the sloped awnings are not. Sheds have an open alcove: the roof hides a unit inside, so the game needs depth handling.'),
    'low-carts': dict(label='Carts and wagons', role='platform', fits='any', style='timber', regex=r'^low-(cart|wagon)-.*', note='Loaded to a flat top at 1 level; walkable.'),
    'mycelium': dict(label='Mycelium veins', role='decor', fits='corrupted', style='fungal', regex=r'^mycelium-.*', joins='mycelium',
                     note='Flat 32 x 16 vein tiles (end, straight, corner, tee, cross, node) that join at fixed edge midpoints: lay them as a network; see the corrupted-terrain README.'),
    'shelf-fungus': dict(label='Shelf fungus platforms', role='platform', fits='corrupted', style='fungal', prefix='shelf-',
                         note='Walkable, 1 and 2 levels, 1 x 1 to 2 x 2; two have a one-level cell as the way up.'),
    'spore-vents': dict(label='Spore vents', role='hazard', fits='corrupted', style='fungal', prefix='spore-vent', note='A looping puff; a hazard or a marker for the game to give an effect.'),
    'thorn-walls': dict(label='Thorn walls', role='blocker', fits='corrupted', style='fungal', regex=r'^thorn-wall-(?!.*broken).*',
                        note='Block their cells until destroyed; each has a `-broken` twin to swap to.'),
    'gravestones': dict(label='Gravestones', role='scatter', fits='any', style='bone', prefix='gravestone-'),
    'cairns-bones': dict(label='Cairns and bones', role='scatter', fits='any', style='bone', regex=r'^(cairn|bones)-.*'),
    'monuments': dict(label='Obelisk and plinth', role='scatter', fits='any', style='bone', regex=r'^(obelisk|rune-plinth)$', note='Glowing runes: a ritual place.'),
    'rune-altar': dict(label='Rune altar', role='platform', fits='any', style='bone', prefix='rune-altar-', note='Flat topped at level 1 and measures walkable; the game may want it to block.'),
    'spirit-lanterns': dict(label='Spirit lanterns', role='decor', fits='any', style='bone', prefix='spirit-lantern-', note='Animated glow.'),
    'iron-fences': dict(label='Iron fences and gates', role='cover', fits='any', style='iron', regex=r'^(iron-fence|graveyard-gate)-.*'),
    'ritual-circles': dict(label='Ritual circles', role='decor', fits='any', style='bone', prefix='ritual-circle-', flat=True, note='Flat ground decals, 2 x 2 to 4 x 4.'),
    'docks': dict(label='Docks', role='platform', fits='plain', style='timber', regex=r'^dock-(?!.*corrupted).*', note='Walkable, deck flush with land, over water. Placed by the game against a shore.'),
    'docks-corrupted': dict(label='Corrupted docks', role='platform', fits='corrupted', style='fungal', regex=r'^dock-.*corrupted$'),
    'rowboats': dict(label='Rowboats', role='blocker', fits='any', style='timber', prefix='rowboat-', on='water', note='On the water; not walkable.'),
    'stepping-stones': dict(label='Stepping stones', role='platform', fits='any', style='natural', prefix='stepping-', on='water', note='Walkable stones in water, 1 level above its surface.'),
    'waterfalls': dict(label='Waterfalls', role='decor', fits='plain', style='natural', regex=r'^waterfall-(ne|se)$', note='Animated; for a cliff edge. Placed by the game.'),
    'waterfalls-corrupted': dict(label='Corrupted waterfalls', role='decor', fits='corrupted', style='fungal', regex=r'^waterfall-(ne|se)-corrupted$'),
    'lily-pads': dict(label='Lily pads', role='decor', fits='plain', style='natural', ids=['lily-pads'], on='water', flat=True),
    'mushroom-pads': dict(label='Mushroom pads', role='decor', fits='corrupted', style='fungal', ids=['mushroom-pads'], on='water', flat=True),
    'reeds': dict(label='Reeds', role='decor', fits='plain', style='natural', regex=r'^reeds(-sway)?$', on='shore'),
    'reeds-corrupted': dict(label='Corrupted reeds', role='decor', fits='corrupted', style='fungal', regex=r'^reeds-corrupted(-sway)?$', on='shore'),
    'destructibles-small': dict(label='Small destructibles', role='cover', fits='any', style='timber', regex=r'^(barricade-1x1|barrel-explosive|barrel-stack|wall-1x1|urns)$',
                                note='One cell each, with intact, damaged and destroyed states and a `-destroy` animation. `barrel-explosive` explodes.'),
    'destructibles-long': dict(label='Long destructibles', role='blocker', fits='any', style='timber', regex=r'^(barricade-1x2|wall-1x2|haycart)$', note='The 1 x 2 barricade and wall, and the two-cell hay cart.'),
    'weather-rain': dict(label='Rain', role='overlay', fits='any', style='weather', regex=r'^weather-rain-(light|heavy)$'),
    'weather-fog': dict(label='Fog and mist', role='overlay', fits='any', style='weather', regex=r'^weather-(fog-light|fog-dense|mist-low)$'),
    'weather-haze': dict(label='Spore haze', role='overlay', fits='corrupted', style='weather', ids=['weather-spore-haze']),
    'weather-embers': dict(label='Embers', role='overlay', fits='any', style='weather', ids=['weather-embers']),
    'weather-petals': dict(label='Petals', role='overlay', fits='plain', style='weather', ids=['weather-petals']),
    'weather-ripples': dict(label='Rain ripples and splashes', role='decor', fits='any', style='weather', regex=r'^weather-(ripple|splash)-.*', note='Ground and water decals for rain; one shot.'),
    'traps': dict(label='Traps', role='hazard', fits='any', style='iron', prefix='trap-'),
    'chests': dict(label='Chests', role='decor', fits='any', style='timber', prefix='chest-'),
    'buildings': dict(label='Buildings', role='structure', fits='any', style='blocky', prefix='bld-',
                      note='The kit of walls and roofs; `-aged` pieces are the weathered versions that sit in a ruined or corrupted town.'),
}

# --- sets -----------------------------------------------------------------------------------------
# grass: [(cell, weight)] on the set's ground; lake: the default (0 none, 1 pond, 2 lake, 3 big lake); level: sunken or flush; bridge: a group id or None.
# Layers, each {groups: {group: weight}, ...}:
#   scatter    one-cell pieces on land (density: share of cells)                  features   multi-cell pieces on land (per100: per 100 cells), each where every cell is clear
#   water      pieces placed in the water (per100 water cells)                    decals     flat pieces: on land, water or shore (per100 cells of that kind; `mycelium` is laid as a joined network)
#   connectors stairs and ramps the game attaches to platforms                    structures groups placed by the game's own rules (buildings, docks)
#   weather    screen overlays: `chance` of each being used on a map, groups weighted
SETS = {
    'meadow': dict(
        label='Meadow', ground='plain', time='day',
        blurb='Green rolling country: oaks and pines, bushes and flowers, worn slabs to climb, boulders and haystacks in the grass, a pond with lily pads and stepping stones, a plank bridge, petals on the wind.',
        grass=PLAIN_GRASS, lake=1, level='sunken', bridge='bridges-plank',
        scatter=dict(density=0.22, groups={'trees-temperate': 3, 'bushes': 3, 'ground-props-plain': 4}),
        features=dict(per100=3.0, groups={'rocks-slab': 3, 'rocks-stone': 3, 'low-hay': 1}),
        water=dict(per100=8.0, groups={'stepping-stones': 3}),
        decals=[dict(group='lily-pads', on='water', per100=18), dict(group='reeds', on='shore', per100=30)],
        connectors=['stairs-scaffold'],
        weather=dict(chance=0.3, groups={'weather-petals': 2, 'weather-rain': 1}),
    ),
    'highland': dict(
        label='Highland', ground='plain', time='day',
        blurb='Cold, stony heights: pines and spruce, broken crags and straight-faced ledges with stairs up to them, a pond high in the rocks, a stone arch bridge, fog in the valleys.',
        grass=[((0, 0), 6), ((9, 1), 3), ((8, 7), 2), ((10, 9), 2), ((10, 7), 2), ((9, 8), 1), ((8, 9), 1)], lake=1, level='sunken', bridge='bridges-stone',
        scatter=dict(density=0.16, groups={'trees-temperate': 3, 'ground-props-plain': 4, 'trees-dead': 1}),
        features=dict(per100=5.0, groups={'rocks-ledge': 3, 'rocks-crag': 3, 'rocks-slab': 1}),
        water=dict(per100=6.0, groups={'stepping-stones': 3}),
        decals=[dict(group='reeds', on='shore', per100=20)],
        connectors=['stairs-new'],
        weather=dict(chance=0.5, groups={'weather-fog': 3, 'weather-rain': 1}),
    ),
    'riverbank': dict(
        label='Riverbank', ground='plain', time='day',
        blurb='A big lake with docks, a stone bridge and reeds: oaks and birches on the banks, boulders on the shore, rowboats and stepping stones on the water.',
        grass=PLAIN_GRASS, lake=3, level='sunken', bridge='bridges-stone',
        scatter=dict(density=0.18, groups={'trees-temperate': 3, 'bushes': 4, 'ground-props-plain': 2}),
        features=dict(per100=2.0, groups={'rocks-slab': 2, 'rocks-stone': 3}),
        water=dict(per100=7.0, groups={'stepping-stones': 3, 'rowboats': 1}),
        decals=[dict(group='lily-pads', on='water', per100=22), dict(group='reeds', on='shore', per100=40)],
        connectors=['stairs-scaffold'],
        structures=['docks'],
        weather=dict(chance=0.35, groups={'weather-fog': 2, 'weather-rain': 2}),
    ),
    'market-town': dict(
        label='Market town', ground='plain', time='day',
        blurb='A town square: stalls and carts, haybales and crate piles to climb, fences and crates, barrels and barricades you can break, a few trees, and the buildings kit.',
        grass=[((0, 0), 12), ((9, 1), 4)], lake=0, level='flush', bridge=None,
        scatter=dict(density=0.13, groups={'fences': 3, 'crates': 3, 'bushes': 2, 'trees-temperate': 1, 'destructibles-small': 3}),
        features=dict(per100=3.5, groups={'low-stalls': 3, 'low-hay': 3, 'low-carts': 2, 'rocks-ledge': 2, 'destructibles-long': 1}),
        connectors=['stairs-new', 'stairs-scaffold'],
        structures=['buildings'],
        weather=dict(chance=0.2, groups={'weather-rain': 1}),
    ),
    'fallen-town': dict(
        label='Fallen town', ground='plain', time='dusk',
        blurb='The same town after something went wrong: ruined walls and rubble to hide behind, broken foundations and overgrown stumps of buildings, dead trees, broken fences and logs, embers in the air.',
        grass=[((0, 0), 8), ((9, 1), 6), ((8, 7), 2)], lake=0, level='flush', bridge=None,
        scatter=dict(density=0.15, groups={'trees-dead': 3, 'fences': 2, 'crates': 2, 'logs': 2, 'ground-props-plain': 1, 'ruins-walls': 4, 'ruins-walls-grown': 1, 'destructibles-small': 2}),
        features=dict(per100=4.5, groups={'ruins-heaps': 3, 'ruins-walls-long': 2, 'ruins-floors': 2, 'ruins-floors-grown': 1, 'ruins-heaps-grown': 1, 'rocks-crag': 1, 'low-hay': 1, 'destructibles-long': 1}),
        connectors=['stairs-scaffold'],
        structures=['buildings'],
        weather=dict(chance=0.6, groups={'weather-embers': 3, 'weather-fog': 1}),
    ),
    'spore-hollow': dict(
        label='Spore hollow', ground='corrupted', time='dusk',
        blurb='The healthy meadow, corrupted: teal turf, mushroom trees and shelf fungus to climb, veins of mycelium across the ground, spore vents and thorn walls, natural stones swallowed by moss, spore haze.',
        grass=[(c, 4) for c in CLEAN_GRASS] + [((0, 0), 1)], lake=1, level='sunken', bridge='bridges-corrupt',
        scatter=dict(density=0.22, groups={'mushroom-trees': 5, 'ground-props-corrupted': 4, 'trees-dead': 1, 'spore-vents': 1}),
        features=dict(per100=3.5, groups={'shelf-fungus': 3, 'rocks-slab': 1, 'rocks-stone': 2, 'thorn-walls': 2, 'ruins-heaps-grown': 1}),
        water=dict(per100=6.0, groups={'stepping-stones': 2}),
        decals=[dict(group='mycelium', on='land', per100=8), dict(group='mushroom-pads', on='water', per100=20), dict(group='reeds-corrupted', on='shore', per100=30)],
        weather=dict(chance=0.7, groups={'weather-haze': 3, 'weather-fog': 1}),
    ),
    'gravemoor': dict(
        label='Gravemoor', ground='corrupted', time='night',
        blurb='A moor of graves under mist: gravestones and cairns, bones, an obelisk and a rune altar around a ritual circle, spirit lanterns, iron fences and gates, dead trees and broken crags.',
        grass=[(c, 4) for c in CLEAN_GRASS], lake=0, level='flush', bridge=None,
        scatter=dict(density=0.15, groups={'gravestones': 4, 'cairns-bones': 3, 'trees-dead': 3, 'ground-props-corrupted': 1, 'iron-fences': 2, 'monuments': 1, 'spirit-lanterns': 1}),
        features=dict(per100=3.5, groups={'rocks-crag': 2, 'rocks-stone': 2, 'rune-altar': 1, 'thorn-walls': 1, 'ruins-heaps-grown': 1}),
        decals=[dict(group='ritual-circles', on='land', per100=1.5), dict(group='mycelium', on='land', per100=3)],
        weather=dict(chance=0.8, groups={'weather-fog': 3, 'weather-rain': 1}),
    ),
    'sunken-marsh': dict(
        label='Sunken marsh', ground='corrupted', time='dusk',
        blurb='A drowned corrupted lowland: dark water with mushroom pads, mushroom trees on the banks, rotten docks and a corrupted bridge, stones standing in the shallows, haze over it all.',
        grass=[(c, 4) for c in CLEAN_GRASS], lake=3, level='sunken', bridge='bridges-corrupt',
        scatter=dict(density=0.20, groups={'mushroom-trees': 5, 'ground-props-corrupted': 3, 'logs': 1}),
        features=dict(per100=2.5, groups={'rocks-stone': 3, 'rocks-slab': 1, 'shelf-fungus': 1, 'thorn-walls': 1}),
        water=dict(per100=8.0, groups={'stepping-stones': 3}),
        decals=[dict(group='mushroom-pads', on='water', per100=24), dict(group='reeds-corrupted', on='shore', per100=45), dict(group='mycelium', on='land', per100=5)],
        connectors=['stairs-scaffold'],
        structures=['docks-corrupted'],
        weather=dict(chance=0.8, groups={'weather-haze': 3, 'weather-fog': 2}),
    ),
}

# Groups that are two looks of the same thing: same role, same footprints, so a map can swap one for the other and keep every rule. (Symmetric.)
TWINS = [('stairs-new', 'stairs-scaffold'), ('rocks-ledge', 'rocks-slab'), ('rocks-crag', 'rocks-stone'), ('trees-temperate', 'mushroom-trees'), ('ground-props-plain', 'ground-props-corrupted')]


def fits(group, ground):
    return GROUPS[group]['fits'] in ('any', ground)


def resolve(group, data):
    """The asset ids of a group, from assets/data.js (a dict {id: asset}). Exact ids that do not exist are dropped, a prefix finds every one."""
    g = GROUPS[group]
    import re
    found = [i for i in g.get('ids', []) if i in data]
    if g.get('prefix'):
        found += sorted(i for i in data if i.startswith(g['prefix']) and i not in found)
    if g.get('regex'):
        found += sorted(i for i in data if re.match(g['regex'], i) and i not in found)
    return found
