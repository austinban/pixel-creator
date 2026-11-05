#!/usr/bin/env python3
"""A throw: a skeleton winds up with a bone in its hand, throws it, and follows through (four frames, like the bow draw).

The bone it throws is the projectile in make_bone.py (a spinning bone, and one shattering); here it is only the bone in the hand. The throw is a pose set like the bow draw: `throwNE` and `throwSE`,
four 32 x 32 frames each, on the people built from the 3D model.

    1  wind-up     leaning back, the body turned away from the target, the bone cocked behind the head, the other arm out ahead for balance
    2  throw       the body whips round and the arm comes over, the bone still in the hand at the top of the swing
    3  release     the arm out straight ahead, the weight thrown forward onto the front foot, the bone gone
    4  follow      the arm comes down across the body and the figure settles

    python3 tools/make_throw.py --preview previews/throw.png                 the four frames, both ways, enlarged
    python3 tools/make_throw.py --bases bones                                add the throw poses to this base's sprite folder
    python3 tools/extract_poses.py --merge bones=sprites/bones
"""
import argparse
import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_bones  # noqa: E402
import make_traps  # noqa: E402

from creature import part  # noqa: E402
from humanoid import pose as humanoid_pose  # noqa: E402

THROWING_HAND = 'R'
BONE_LENGTH = 8.0
BONE_RAMP = ('t', 't', 'C', 'b')              # warmer and brighter than the skeleton's own bone, so the bone in the hand stands out from the arm


def frames():
    return [
        # wind-up: leaning back, turned away, the bone cocked up behind the head
        humanoid_pose(pitch=8, lift=-0.5, twist=42, head_yaw=-30, head_pitch=-6, spread=1.0, sway=-1.5, flare=1.0, elbow_up=('R',),
                      hands={'L': (3.6, -1.0), 'R': (-3.0, 5.8)}, feet={'L': (2.6, 0), 'R': (-2.4, 0)}, bone=True),
        # throw: the body whips round, the arm comes over the top
        humanoid_pose(pitch=-4, lift=-0.7, twist=-18, head_yaw=-20, head_pitch=0, spread=1.4, sway=1.6, flare=0.6, elbow_up=('R',),
                      hands={'L': (-0.5, -3.6), 'R': (4.2, 6.2)}, feet={'L': (3.0, 0), 'R': (-2.6, 0)}, bone=True),
        # release: the arm out straight ahead, weight on the front foot, the bone gone
        humanoid_pose(pitch=-12, lift=-0.4, twist=-46, head_yaw=-30, head_pitch=2, spread=1.6, sway=3.0, fwd=1.0, flare=0.4,
                      hands={'L': (-1.5, -3.0), 'R': (5.4, 1.6)}, feet={'L': (3.2, 0), 'R': (-2.4, 1.2)}),
        # follow-through: the arm comes down across the body
        humanoid_pose(pitch=-8, lift=-0.5, twist=-34, head_yaw=-22, head_pitch=-3, spread=1.0, sway=1.8, fwd=0.4,
                      hands={'L': (-0.5, -4.2), 'R': (3.0, -3.6)}, feet={'L': (3.0, 0), 'R': (-1.6, 0)}),
    ]


def held_bone(j, p):
    """The bone in the throwing hand: along the forearm, past the fist, with a knob at each end."""
    if not p.get('bone') or ('arm_' + THROWING_HAND) not in j:
        return []
    shoulder, elbow, wrist = j['arm_' + THROWING_HAND]
    d = make_traps.norm(tuple(wrist[i] - elbow[i] for i in range(3)))
    centre = tuple(wrist[i] + d[i] * 1.6 for i in range(3))
    R = make_traps.along(d)
    parts = [part(centre, (BONE_LENGTH / 2, 0.7, 0.7), 'thrown', 'thrownbone', R)]
    for end in (-1, 1):
        for side in (-1, 1):
            c = tuple(centre[i] + d[i] * end * BONE_LENGTH / 2 for i in range(3))
            parts.append(part((c[0], c[1], c[2] + side * 0.65), (1.05, 1.05, 1.05), 'thrown', 'thrownbone'))
    return parts


def with_throw(creature):
    """The same person with the throw poses added, and a bone in the hand while it is held."""
    person = copy.copy(creature)
    person.poses = dict(creature.poses, throw=frames())
    person.ramps = dict(creature.ramps, thrown=BONE_RAMP)
    base_gear = creature.accessories
    person.accessories = lambda j, p: (base_gear(j, p) if base_gear else []) + held_bone(j, p)
    return person


def build_frames(person):
    """{facing: 4 frames of 32 x 32} as colour-role rows, each put on the ground row."""
    import conventions
    import creature as cr
    out = {}
    cr.TALL_EYES = person.tall_eyes
    for facing in ('NE', 'SE'):
        origin = cr.calibrate(person, facing)
        rows = []
        for pose_ in person.poses['throw']:
            parts, decals = person.place(pose_)
            lines = cr.render_frame(parts, decals, facing, origin, person.ramps, person.scale)
            ys = [y for y, line in enumerate(lines) if line.strip('.')]
            rows.append(cr.shift_rows(lines, conventions.GROUND_ROW - max(ys)))
        out[facing] = rows
    return out


def problems(who, built):
    import conventions
    return conventions.check_base(who, {f'throw{f}': fr for f, fr in built.items()}, 'humanoid')


def write_base_poses(who, creature):
    """Add NAME-throwNE.png and NAME-throwSE.png (4 frames of 32 x 32) to a base's sprite folder."""
    import creature as cr
    from PIL import Image
    built = build_frames(with_throw(creature))
    folder = Path(__file__).resolve().parent.parent / 'sprites' / who
    folder.mkdir(parents=True, exist_ok=True)
    found = problems(who, built)
    for p_ in found:
        print('  ' + p_)
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in cr.ep.ROLES}
    for facing, fr in built.items():
        img = Image.new('RGBA', (32 * len(fr), 32), (0, 0, 0, 0))
        px = img.load()
        for f, lines in enumerate(fr):
            for y, line in enumerate(lines):
                for x, ch in enumerate(line):
                    if ch != '.':
                        px[f * 32 + x, y] = (*rgb[ch], 255)
        img.save(folder / f'{who}-throw{facing}.png')
    return found


def preview(path, scale=6):
    from PIL import Image, ImageDraw
    import fx
    rgb = fx.rgb_of()
    built = build_frames(with_throw(make_bones.CREATURE))
    sheet = Image.new('RGB', (4 * 32 * scale, 2 * (32 * scale + 14)), (50, 44, 84))
    dr = ImageDraw.Draw(sheet)
    for row, facing in enumerate(('NE', 'SE')):
        for i, lines in enumerate(built[facing]):
            ox, oy = i * 32 * scale, row * (32 * scale + 14) + 14
            dr.text((ox + 4, oy - 12), f'{facing}  {("wind-up", "throw", "release", "follow")[i]}', fill=(240, 240, 240))
            for y, line in enumerate(lines):
                for x, ch in enumerate(line):
                    if ch != '.':
                        dr.rectangle([ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1], fill=rgb[ch])
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--bases', help='add the throw poses to these bases\' sprite folders, e.g. bones')
    args = parser.parse_args()
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview)
        print('wrote', args.preview)
    if args.bases:
        import importlib
        for who in args.bases.split(','):
            write_base_poses(who, getattr(importlib.import_module('make_' + who.replace('-', '_')), 'CREATURE'))
            print(f'{who}: throw poses -> sprites/{who}')


if __name__ == '__main__':
    main()
