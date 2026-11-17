# Building decks: flat roofs and balconies

84 pieces in category **Buildings** (`tools/make_building_decks.py`), in the **building kit's own format** (`../buildings/`, `tools/buildings.py`): each is a one-cell, one-level piece, **32 x 32**, anchored at the middle of its base at **(16, 24)**, so they stack and sit beside the wall, door, window and roof pieces. `building-decks.json` lists every group and piece with its kind and the sides it has a rail or parapet on.

x runs down and to the right (SE), y down and to the left (SW), as everywhere. Unlike the kit's windows and doors, a deck piece has **no NE and SE twin**: it is the same picture on every wall, and its sides are named for the world axes (`+x`, `-x`, `+y`, `-y`).

## The groups

Each is one `variants` asset (`bld-flat-roof-stone`, `bld-balcony-timber`...), one picture per piece.

| Group | Pieces | For |
|---|---|---|
| `bld-flat-roof-stone` | 10 | stone walls: coursed stone |
| `bld-flat-roof-timber` | 10 | timber-framed walls: a plum plank deck with a plaster parapet and a beam on top |
| `bld-flat-roof-tile`, `-slate`, `-teal` | 10 each | houses with those roofs: the kit's roof tile laid flat |
| `bld-flat-roof-plank` | 10 | warm planks, like the docks, bridges and scaffolds |
| `bld-balcony-stone` | 7 | stone walls: a slab on corbels with a stone balustrade |
| `bld-balcony-timber` | 7 | timber-framed walls: a plum floor and fascia with plaster panels between plum posts |
| `bld-balcony-plank` | 7 | a warm plank deck with a plank rail |
| `bld-supports` | 3 | `post-plank`, `post-timber` and `pillar-stone`, one level tall, to stand under a balcony |

**Flat roofs** are `deck` (no parapet), `hatch` (a trapdoor), `edge-px`, `edge-nx`, `edge-py`, `edge-ny` (a parapet along one side) and `corner-px-py`, `corner-nx-ny`, `corner-px-ny`, `corner-nx-py` (along two). **Balconies** are named for where the rail is: `alcove-x` (wall on the -x side, rail on the other three), `alcove-y`, `run-x` and `run-y` (a rail on the front only, so they join in a row), `run-start-x` and `run-start-y` (a run's first piece) and `corner`.

## Height and walking

- The walkable top is **`deck_top` = 0.5 level (8 pixels, one game step) above the piece's base**. A parapet or rail stands above it (a parapet to about 0.82 level) and does not block the walk, but it is the edge a unit stops at.
- **A flat roof** goes on top of a storey: put its piece at the level of the top of the wall below, so its deck is half a level above. Use `deck` inside, edges and corners round the outside, and `hatch` where a stair comes up.
- **A balcony** goes on the wall that faces out at a **storey floor**, one cell out from the wall, with `bld-supports` under it for the stone and plank kinds. Put the piece at the storey's floor level. A timber balcony on a timber house and a stone one on a stone house match; the plank ones go with either.
- All of them are walkable (`walkable: true`, `levels: 1`), apart from the supports.

## Using them

Draw a piece at its cell the way the kit's walls are drawn: anchor on the middle of the cell's top face on the ground, sorted by the cell's `i + j` and by level with the other building pieces. `tools/make_building_decks.py --preview` shows every piece and four small houses (stone, timber-framed, and two mixes).
