#!/usr/bin/env python3
"""Check everything in the project against the conventions (CONVENTIONS.md, conventions.py).

    python3 tools/check_conventions.py          check, and exit 1 if anything is off
    python3 tools/check_conventions.py -q       only say what is wrong

What it looks at:
  - every base in poses/base.js: inside the cell, outlined, feet on the ground row, the right size,
    the right weight, and (for people) leaning into the movement like the original bases
  - the colour ramps of every generated creature: light to dark, real palette roles
  - the weapon strips in sprites/weapons: the right cell, and all sharing one swing
  - every generated person's strike hand: close enough to the weapons' grip that a weapon looks held

Run it after changing any pose, ramp, proportion or weapon, and before relying on the data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions as cv  # noqa: E402


def main():
    quiet = '-q' in sys.argv
    problems = []

    def section(title, found, count):
        if not quiet:
            print(f"{'ok  ' if not found else 'FAIL'} {title} ({count})")
        problems.extend(found)

    bases = cv.load_bases()
    for ch in bases['characters']:
        creator = cv.creator_of(ch['id'])
        airborne = getattr(creator, 'airborne', set())
        section(f"{ch['id']} ({cv.kind_of(ch['id'])})", cv.check_base(ch['id'], ch['frames'], airborne=airborne), f"{len(ch['frames'])} poses")
        section(f"{ch['id']} bow animation", cv.check_bow(ch['id'], ch['frames']), 'bow poses')

    emperor = cv.ROOT / 'sprites' / 'scorpion-emperor'
    if emperor.is_dir():
        found = cv.load_boss_frames(emperor, 'scorpion-emperor')
        section('scorpion-emperor (boss)', cv.check_boss('scorpion-emperor', found), f'{sum(len(v) for v in found.values())} frames')

    weapons = cv.ROOT / 'sprites' / 'weapons'
    if weapons.is_dir():
        section('weapons', cv.check_weapons(weapons), f"{len(list(weapons.glob('*.png')))} strips")
        for name in cv.CREATORS:
            creator = cv.creator_of(name)
            if getattr(creator, 'kind', '') == 'humanoid':
                section(f'{name} holds a weapon', cv.check_hand_path(creator, weapons), '8 attack frames')
    for name in cv.CREATORS:
        creator = cv.creator_of(name)
        section(f'{name} colour ramps', cv.check_ramps(creator.ramps, name), f'{len(creator.ramps)} materials')
        section(f'{name} eyes', cv.check_eyes(creator, name), 'tall slits')

    if problems:
        print(f'\n{len(problems)} problem{"s" if len(problems) != 1 else ""}:', file=sys.stderr)
        for p in problems:
            print('  ' + p, file=sys.stderr)
        sys.exit(1)
    if not quiet:
        print('\nEverything follows the conventions.')


if __name__ == '__main__':
    main()
