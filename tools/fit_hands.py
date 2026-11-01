#!/usr/bin/env python3
"""Fit a humanoid's attack so its strike hand carries the weapon along the weapons' path.

The weapon strips say where the weapon sits in each frame of the swing, in a 48 x 48 cell with
the 32 x 32 character in the middle. This finds, for each frame, where the strike hand has to go
so that it ends up there on screen, by solving the arm with the same inverse kinematics the poses
use, and prints the hand positions to put in the poses. A hand that cannot reach (the arm is only
so long) is as close as it can get, and the miss is reported.

    python3 tools/fit_hands.py [NAME] [sprites/weapons]          fit, write the data, show how close each frame is
    python3 tools/fit_hands.py [NAME] --check [sprites/weapons]  only show

NAME is a generated person (human, slim...); it defaults to human.

It averages every weapon in the folder: they share a hand path and differ only in the head. The
answer goes to data/NAME_hands.json, which humanoid.py applies over the hand-written poses.
Run tune_lean.py first: the hand has to be placed for the body's final lean. Frames are put on the
ground row when they are made, which moves them a pixel or two, so that is allowed for here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copy  # noqa: E402
import json  # noqa: E402

import creature  # noqa: E402
import make_weapons  # noqa: E402
import conventions  # noqa: E402
from humanoid import DATA, Humanoid  # noqa: E402

CELL = creature.CELL
GRIP = 3.5      # how far the hand is from the middle of the drawn weapon, toward the body


def weapon_path(folder):
    """Per facing, the middle of the weapon in each frame, in the character's cell."""
    from PIL import Image
    sums = {}
    for path in sorted(Path(folder).glob('*.png')):
        m = make_weapons.FILE.match(path.name)
        if not m:
            continue
        im = Image.open(path).convert('RGBA')
        cell = im.height
        pad = (cell - CELL) / 2
        px = im.load()
        points = []
        for f in range(make_weapons.FRAMES):
            pts = [(x - f * cell, y) for y in range(cell) for x in range(f * cell, f * cell + cell) if px[x, y][3] >= make_weapons.SOLID]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            centre = ((min(xs) + max(xs) + 1) / 2 - pad, (min(ys) + max(ys) + 1) / 2 - pad)
            # The hand holds the weapon at its handle, a few pixels back from the middle of what is
            # drawn (the head), toward the body.
            dx, dy = CELL / 2 - centre[0], CELL / 2 - centre[1]
            length = (dx * dx + dy * dy) ** 0.5 or 1
            points.append((centre[0] + GRIP * dx / length, centre[1] + GRIP * dy / length))
        sums.setdefault(m['facing'], []).append(points)
    return {facing: [(sum(p[f][0] for p in paths) / len(paths), sum(p[f][1] for p in paths) / len(paths))
                     for f in range(make_weapons.FRAMES)] for facing, paths in sums.items()}


def hand_on_screen(human, pose, facing, origin, side):
    human.place(pose)
    x, y, z = human.last_joints['hand_' + side]
    return creature.project_point((x, y, z), facing, origin, human.scale)


def ground_offset(human, pose, facing, origin):
    """How far a frame is moved down when it is put on the ground row, so the hand lands where it is drawn."""
    parts, decals = human.place(pose)
    lines = creature.render_frame(parts, decals, facing, origin, human.ramps, human.scale)
    rows = [y for y, line in enumerate(lines) if line.strip('.')]
    return conventions.GROUND_ROW - max(rows)


def fit(human, frames, facing, targets, side='L', reach=7.1, step=0.5, twists=range(-50, 51, 10)):
    """For each frame, the hand position (from its shoulder) and body twist that land closest to the target.

    A grid search over every spot the arm can reach and every twist, so a target out of reach just
    gets the nearest one instead of a wild answer. Done twice: the second time the frame's move to the
    ground row, which depends on the first answer, is allowed for.
    """
    origin = creature.calibrate(human, facing)
    n = int(reach / step)
    fitted = [copy.deepcopy(p) for p in frames]
    for _ in range(2):
        results = []
        for pose, target in zip(fitted, targets):
            shift = ground_offset(human, pose, facing, origin)
            pose = copy.deepcopy(pose)
            best = None
            for twist in twists:
                pose['twist'] = twist
                for i in range(-n, n + 1):
                    for j in range(-n, n + 1):
                        dx, dy = i * step, j * step
                        if dx * dx + dy * dy > reach * reach:
                            continue
                        pose['hands'][side] = (dx, dy)
                        p = hand_on_screen(human, pose, facing, origin, side)
                        miss = ((p[0] - target[0]) ** 2 + (p[1] + shift - target[1]) ** 2) ** 0.5
                        cost = miss + 0.04 * abs(twist)      # only turn as far as it needs to
                        if best is None or cost < best[0]:
                            best = (cost, dx, dy, twist, miss)
            pose['hands'][side] = (round(best[1], 2), round(best[2], 2))
            pose['twist'] = best[3]
            results.append((pose, best[4]))
        fitted = [p for p, _ in results]
    return results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check_only = '--check' in sys.argv
    name = next((a for a in args if a in conventions.CREATORS), 'human')
    rest = [a for a in args if a != name]
    folder = rest[0] if rest else make_weapons.DEFAULT_DIR
    paths = weapon_path(folder)
    human = conventions.creator_of(name)
    out = {}
    for facing in ('NE', 'SE'):
        frames = human.poses['attack' + facing]
        print(f'{facing}: weapon path (x, y) per frame: ' + ', '.join(f'({x:.1f}, {y:.1f})' for x, y in paths[facing]))
        if check_only:
            origin = creature.calibrate(human, facing)
            for i, (pose, target) in enumerate(zip(frames, paths[facing])):
                x, y = hand_on_screen(human, pose, facing, origin, 'L')
                y += ground_offset(human, pose, facing, origin)
                print(f"   frame {i + 1}: hand {pose['hands']['L']} twist {pose['twist']}  off {((x - target[0]) ** 2 + (y - target[1]) ** 2) ** 0.5:.1f}px")
            continue
        result = fit(human, frames, facing, paths[facing], 'L')
        print('   ' + '  '.join(f"{p['hands']['L']} twist {p['twist']} off {miss:.1f}px" for p, miss in result))
        out['attack' + facing] = [{'L': list(p['hands']['L']), 'twist': p['twist']} for p, _ in result]
    if not check_only:
        DATA.mkdir(exist_ok=True)
        (DATA / f'{name}_hands.json').write_text(json.dumps(out, indent=1) + '\n')
        print('wrote', DATA / f'{name}_hands.json')


if __name__ == '__main__':
    main()
