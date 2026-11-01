#!/usr/bin/env python3
"""Set each frame's sway so a humanoid leans into its movement like the original bases.

conventions.LEAN is the average lean of the six original characters, frame by frame: head over
feet, in pixels. Sway shifts the upper body ahead of the hips while the feet stay planted, which is
how a figure puts its weight into a movement. This finds, by rendering and looking, the sway that gives
each frame of a humanoid its lean, and writes the result to data/humanoid_lean.json, which humanoid.py
applies over the hand-written poses.

    python3 tools/tune_lean.py [NAME]            tune, write the data, and show how close each frame is
    python3 tools/tune_lean.py [NAME] --check    only show, change nothing
    python3 tools/tune_lean.py [NAME] --only walking   tune just the poses starting with this; the rest keep their numbers

NAME is a generated person (human, slim...); it defaults to human. Each has its own numbers in
data/NAME_lean.json, so tuning one build never disturbs another.

Run fit_hands.py afterwards: the strike hand has to be placed for the body's final pose.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402
import creature  # noqa: E402
from humanoid import DATA, Humanoid  # noqa: E402


def lean_at(human, pose, facing, origin, sway):
    pose = copy.deepcopy(pose)
    pose['sway'] = sway
    parts, decals = human.place(pose)
    return conventions.lean_of(creature.render_frame(parts, decals, facing, origin, human.ramps, human.scale))


def tune_frame(human, pose, facing, origin, target):
    """The sway whose lean is the target. Lean follows sway almost in a straight line, so a few tries do it."""
    a, b = 0.0, 4.0
    la, lb = lean_at(human, pose, facing, origin, a), lean_at(human, pose, facing, origin, b)
    best = (abs(la - target), a, la)
    for _ in range(3):
        if abs(lb - la) < 1e-6:
            break
        c = a + (target - la) * (b - a) / (lb - la)
        c = max(-8.0, min(14.0, c))
        lc = lean_at(human, pose, facing, origin, c)
        if abs(lc - target) < best[0]:
            best = (abs(lc - target), c, lc)
        a, la, b, lb = b, lb, c, lc
    return round(best[1] * 4) / 4, best[2]


def tune_walk(human, frames, facing, origin, targets):
    """One sway for the whole walk: the head must not swing, so the lean comes from the feet sliding."""
    def mean_lean(sway):
        return sum(lean_at(human, p, facing, origin, sway) for p in frames) / len(frames)
    target = sum(targets) / len(targets)
    a, b = 0.0, 4.0
    la, lb = mean_lean(a), mean_lean(b)
    sway = a + (target - la) * (b - a) / (lb - la) if abs(lb - la) > 1e-6 else 0.0
    return round(max(-8.0, min(14.0, sway)) * 4) / 4


def main():
    check_only = '--check' in sys.argv
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''
    names = [a for a in sys.argv[1:] if not a.startswith('--') and a != only]
    name = names[0] if names else 'human'
    human = conventions.creator_of(name)
    path = DATA / f'{name}_lean.json'
    result = json.loads(path.read_text()) if (only and path.exists()) else {}
    for pose_id, targets in conventions.LEAN.items():
        if not pose_id.startswith(only):
            continue
        if pose_id in getattr(human, 'tweaks', {}):
            print(f'{pose_id:11s} fixed by the build, left as it is')
            result[pose_id] = [f['sway'] for f in human.poses[pose_id]]
            continue
        facing = pose_id[-2:]
        origin = creature.calibrate(human, facing)
        frames = human.poses.get(pose_id, human.poses[pose_id[:-2]])
        sways = []
        if pose_id.startswith('walking') and not check_only:
            one = tune_walk(human, frames, facing, origin, targets)
            frames = [dict(p, sway=one) for p in frames]
        for i, (pose, target) in enumerate(zip(frames, targets)):
            if check_only or pose_id.startswith('walking'):
                sway, got = pose['sway'], lean_at(human, pose, facing, origin, pose['sway'])
            else:
                sway, got = tune_frame(human, pose, facing, origin, target)
            sways.append(sway)
            print(f'{pose_id:11s} frame {i + 1}: sway {sway:+5.2f}  lean {got:+5.1f}  (the originals {target:+4.1f})')
        result[pose_id] = sways
    if not check_only:
        DATA.mkdir(exist_ok=True)
        path.write_text(json.dumps(result, indent=1) + '\n')
        print('wrote', path)


if __name__ == '__main__':
    main()
