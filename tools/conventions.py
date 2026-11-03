"""The rules every character, creature and weapon here follows, and the checks for them.

CONVENTIONS.md explains the rules in words. This is the same rules as numbers and code, so they
can be checked instead of remembered. The numbers were measured from the original six bases (cleric,
fighter, mage, skeleton, zombie, knight), not invented; the Human, the Dog and the Rat were then
brought into line with them.

    python3 tools/check_conventions.py            check everything in the project
    python3 tools/make_dog.py sprites/dog         generation runs the frame checks itself and stops

A check returns a list of plain-English problems; an empty list means it passes.
"""
import importlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# --- the numbers ---------------------------------------------------------------------------
CELL = ep.CELL                   # a character's cell: 32 x 32
WEAPON_CELL = 48                 # a weapon's cell: 48 x 48, so a swing can pass the character's edge
WEAPON_PAD = (WEAPON_CELL - CELL) // 2   # the character sits 8 pixels in from each side of it
WEAPON_FRAMES = 4                # an attack has four frames, so a weapon strip is 4 cells wide

GROUND_ROW = 27                  # the lowest painted row (outline included) of a frame on the ground
GROUND_TOLERANCE = 1             # a foot lifting in a walk can be one row up
DEAD_ROWS = (29, 31)             # lying down, a character sits lower in the cell
X_RANGE = (1, 30)                # painted columns stay inside this
Y_RANGE = (0, 31)                # and painted rows inside this
STAND_HEIGHT = (24, 27)          # a standing humanoid, top of the outline to the ground, in rows
STAND_CENTRE_X = (15.0, 18.0)    # the middle of a standing figure, left to right
CENTRE_X = 16.5                  # where a single-frame pose is centred (the originals' are 16-17.5)
OPEN_EDGE_MAX = 1                # painted-but-not-outline pixels that may touch empty space
MIN_PIXELS = 100                 # a frame with less than this is probably empty or broken
CREATURE_MAX_WIDTH = 26          # a creature is wider and lower than a person, but fits the cell
CREATURE_MIN_HEIGHT = 14

# How close a weapon-holding hand has to be to the weapon's grip, in pixels, for the weapon to look
# held. The weapon path is measured from the strips themselves.
# A very heavy build cannot bring its strike hand all the way to the weapon's path in one frame, so it may miss by a little more. Listed here, with why.
HAND_TOLERANCE_BY_BUILD = {'earthbender': 5.6}      # bulk 1.6: his arms reach no further, but his body is wider
HAND_TOLERANCE = 4.5            # (the grip is itself an estimate, the weapon's drawn middle pulled back toward the body, so a pixel of slack)
WEAPON_SPREAD = 6.0              # how far one weapon's path may stray from the others'

# --- movement: lean and weight ---------------------------------------------------------------
# A character leans into what it is doing. "Lean" is how far the head is from the feet across the
# screen, in pixels: the middle of the head (the top third) minus the middle of the feet (the bottom
# three rows). Positive is toward the right of the screen. The numbers are the average of the six
# original bases, frame by frame. They tell the same story as the animation: in an attack the body
# goes back to wind up, then throws its weight forward and keeps it there through the follow-through
# instead of straightening up.
LEAN = {
    'attackNE': [-4.0, 0.5, 3.5, 3.5],
    'attackSE': [-2.5, 3.5, 4.0, 4.0],
    'chargingNE': [0.0],
    'chargingSE': [3.0],
    'damageNE': [1.0],
    'damageSE': [3.5],
    'releaseNE': [-1.5],
    'releaseSE': [2.0],
    'walkingNE': [-1.0, -1.0, -1.0, -1.0, -1.0, 0.0, 0.0, 0.0],
    'walkingSE': [2.0, 0.5, -0.5, 0.5, 2.0, 1.5, 0.0, 1.5],
    'weakNE': [3.0],
    'weakSE': [2.0],
}                               # lying down (dead) is not a lean, so it has none
LEAN_TOLERANCE = 2.5            # the originals differ from each other by up to 4; stay within this of their average
# "Weight": how much of the cell a figure fills, as painted pixels. A light figure reads as floating.
MASS = {                        # (fewest, most) painted pixels in a frame of this action
    'bow': (267, 388),     # the bow animation is held to the attack's numbers
    'attack': (267, 388), 'charging': (274, 380), 'damage': (250, 363), 'release': (297, 373),
    'walking': (258, 394), 'weak': (220, 286), 'dead': (225, 312),
}
# How tall a figure stands in each pose, in rows, top of the outline to the lowest pixel. A flinch is
# hunched, a slump is low, a cast has the arms thrown up. Measured from the originals.
HEIGHT = {'attack': (22, 27), 'bow': (22, 27), 'charging': (24, 26), 'damage': (21, 24), 'release': (27, 28),
          'walking': (23, 28), 'weak': (16, 18), 'dead': (16, 19)}
# The generated people kneel when worn out (down on one knee, head bowed), which is taller than the
# originals' slump. Their own range, measured from their kneel; the originals keep theirs.
KNEEL_HEIGHT = (22, 26)
KNEELERS = {'human', 'slim', 'ninja', 'ranger', 'bones', 'undead', 'paladin', 'blossom', 'earthbender'}
HEIGHT_SLACK = {'release': 2}    # one row either side of the originals' range (two for a cast, which
HEIGHT_SLACK_DEFAULT = 1        # relies on arms thrown above the head that a shorter-armed figure cannot fully reach)
MASS_SLACK = 0.92               # a little under the lightest original is still allowed
# A person can be built slimmer on purpose. A slim build may carry up to 20% less than the lightest
# original, which is still well above the floaty look of a figure with no body to it. Builds are
# declared here so a slim character is a choice you can see, not a quiet loophole.
BUILDS = {'standard': 0.92, 'slim': 0.78, 'bony': 0.5,
          'maimed': 0.65,
          'delicate': 0.6}      # a fairy: slim, with little body and no heavy clothes      # a missing limb is less to paint
BASE_BUILDS = {'slim': 'slim', 'ninja': 'slim', 'ranger': 'slim', 'bones': 'bony', 'undead': 'maimed', 'paladin': 'standard', 'blossom': 'delicate', 'earthbender': 'standard'}

# --- the walk ----------------------------------------------------------------------------------
# The originals share one walk, and it is a bob with sliding feet, not a rock forward and back. Over
# its eight frames: the head stays at the same x (it moves 0-0.8 px, the body does not swing); the
# body goes down and up twice (a period of four frames), 1-3 rows; the feet slide along the ground
# (the middle of the feet moves 1.2-3.3 px) and barely lift, so the lowest row is 26 on one frame at
# most and 27 on the rest.
WALK_HEAD_SWAY_MAX = 1.2        # head x, most minus least, over the cycle
WALK_BOB = (1, 4)               # head-top y, most minus least (the originals are 1-3)
WALK_PERIOD = 4                 # frame k looks like frame k + 4,
WALK_PERIOD_TOLERANCE = 2       # to within this many rows (the fighter's own walk is two rows out)
WALK_SLIDE_MIN = 1.0            # the feet slide at least this far
WALK_FEET_REVERSALS_MAX = 3     # and smoothly: they change direction at most this often over the cycle
                                # (the originals: 2-3). More is a stutter, the feet jumping back and forth
WALK_LIFTED_MAX = 2             # frames where the lowest row is above the ground at all

# Colour ramps run light to dark.
RAMP_LENGTH = 4

# The original six are humanoid; anything else is declared here. Anything not listed is checked as
# a humanoid.
BASE_KINDS = {'dog': 'creature', 'rat': 'creature', 'scorpion': 'creature', 'mantis': 'creature', 'mantis-small': 'creature', 'scorpion-king': 'creature'}
# Which module describes how a generated base is built, so its poses can be checked at the source.
CREATORS = {'human': 'make_human', 'slim': 'make_slim', 'ninja': 'make_ninja', 'ranger': 'make_ranger', 'bones': 'make_bones', 'undead': 'make_undead', 'paladin': 'make_paladin', 'blossom': 'make_blossom', 'earthbender': 'make_earthbender', 'dog': 'make_dog', 'rat': 'make_rat', 'scorpion': 'make_scorpion', 'mantis': 'make_mantis', 'mantis-small': 'make_mantis_small', 'scorpion-king': 'make_scorpion_king'}

UPRIGHT = {'attack', 'charging', 'damage', 'release', 'walking', 'weak'}


def kind_of(base_id):
    return BASE_KINDS.get(base_id, 'humanoid')


# --- frame checks ----------------------------------------------------------------------------
def painted(lines):
    return [(x, y) for y, line in enumerate(lines) for x, c in enumerate(line) if c != '.']


def check_frame(lines, action, kind='humanoid', airborne=False):
    """Problems with one 32 x 32 frame of a pose."""
    problems = []
    pts = painted(lines)
    if len(pts) < MIN_PIXELS:
        return [f'only {len(pts)} painted pixels']
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if min(xs) < X_RANGE[0] or max(xs) > X_RANGE[1]:
        problems.append(f'reaches column {min(xs) if min(xs) < X_RANGE[0] else max(xs)}; keep inside columns {X_RANGE[0]}-{X_RANGE[1]}')
    if min(ys) < Y_RANGE[0] or max(ys) > Y_RANGE[1]:
        problems.append(f'reaches row {min(ys) if min(ys) < Y_RANGE[0] else max(ys)}; keep inside rows {Y_RANGE[0]}-{Y_RANGE[1]}')

    # The silhouette is outlined: a painted pixel next to empty space must be the outline colour.
    open_edge = 0
    for x, y in pts:
        if lines[y][x] == ep.ROLES[0][0]:
            continue
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < CELL and 0 <= ny < CELL) or lines[ny][nx] == '.':
                open_edge += 1
                break
    if open_edge > OPEN_EDGE_MAX:
        problems.append(f'{open_edge} pixels on the edge are not outlined')

    low = max(ys)
    if action == 'dead':
        if not DEAD_ROWS[0] <= low <= DEAD_ROWS[1]:
            problems.append(f'lying down, the lowest row is {low}; it should be {DEAD_ROWS[0]}-{DEAD_ROWS[1]}')
    elif not airborne and not GROUND_ROW - GROUND_TOLERANCE <= low <= GROUND_ROW:
        problems.append(f'feet are on row {low}; the ground is row {GROUND_ROW}')
    return problems


def lean_of(lines):
    """How far the head is from the feet across the screen, in pixels (see LEAN)."""
    pts = painted(lines)
    ys = [p[1] for p in pts]
    top, low = min(ys), max(ys)
    height = low - top + 1
    head = [p for p in pts if p[1] < top + max(5, height * 0.30)]
    feet = [p for p in pts if p[1] > low - 3]
    return sum(p[0] for p in head) / len(head) - sum(p[0] for p in feet) / len(feet)


def check_movement(base_id, frames_by_pose):
    """Does a humanoid lean into its movement, and carry the weight of the originals?"""
    out = []
    for pose_id, frames in frames_by_pose.items():
        action = pose_id[:-2]
        for i, lines in enumerate(frames):
            ys = [p[1] for p in painted(lines)]
            height = max(ys) - min(ys) + 1
            h_lo, h_hi = KNEEL_HEIGHT if (action == 'weak' and base_id in KNEELERS) else HEIGHT[action]
            slack = HEIGHT_SLACK.get(action, HEIGHT_SLACK_DEFAULT)
            if not h_lo - slack <= height <= h_hi + slack:
                out.append(f'{base_id} {pose_id} frame {i + 1}: {height} rows tall; this pose is {h_lo}-{h_hi} for this build')
            mass = len(painted(lines))
            lo, hi = MASS[action]
            if mass < lo * BUILDS[BASE_BUILDS.get(base_id, 'standard')]:
                out.append(f'{base_id} {pose_id} frame {i + 1}: only {mass} painted pixels; the originals carry {lo}-{hi} (too light)')
            if pose_id in LEAN:
                want = LEAN[pose_id][i]
                got = lean_of(lines)
                if abs(got - want) > LEAN_TOLERANCE:
                    out.append(f'{base_id} {pose_id} frame {i + 1}: leans {got:+.1f}px, the originals average {want:+.1f}px '
                               f'(stay within {LEAN_TOLERANCE:g}); {"lean further into it" if (want - got) > 0 else "lean back more"}')
    return out


def walk_features(lines):
    pts = painted(lines)
    ys = [p[1] for p in pts]
    top, low = min(ys), max(ys)
    height = low - top + 1
    head = [p for p in pts if p[1] < top + max(5, height * 0.30)]
    feet = [p for p in pts if p[1] > low - 3]
    return top, low, sum(p[0] for p in head) / len(head), sum(p[0] for p in feet) / len(feet)


def check_walk(base_id, frames_by_pose):
    """A humanoid walks the way the originals do: it bobs, its feet slide, its head stays put."""
    out = []
    for facing in ('NE', 'SE'):
        frames = frames_by_pose.get('walking' + facing)
        if not frames:
            continue
        tops, lows, heads, feet = zip(*(walk_features(f) for f in frames))
        name = f'{base_id} walking{facing}'
        sway = max(heads) - min(heads)
        if sway > WALK_HEAD_SWAY_MAX:
            out.append(f'{name}: the head moves {sway:.1f}px across the cycle; it should stay put (at most {WALK_HEAD_SWAY_MAX:g}), the body bobs instead of rocking')
        bob = max(tops) - min(tops)
        if not WALK_BOB[0] <= bob <= WALK_BOB[1]:
            out.append(f'{name}: the body bobs {bob} rows; the originals bob {WALK_BOB[0]}-{WALK_BOB[1] - 1}')
        n = len(frames)
        if any(abs(tops[k] - tops[(k + WALK_PERIOD) % n]) > WALK_PERIOD_TOLERANCE for k in range(n)):
            out.append(f'{name}: the bob should repeat every {WALK_PERIOD} frames (down, up, down, up in one cycle)')
        slide = max(feet) - min(feet)
        if slide < WALK_SLIDE_MIN:
            out.append(f'{name}: the feet slide only {slide:.1f}px; they should slide along the ground (at least {WALK_SLIDE_MIN:g})')
        diffs = [b - a for a, b in zip(feet, feet[1:]) if abs(b - a) >= 0.15]
        reversals = sum(1 for a, b in zip(diffs, diffs[1:]) if a * b < 0)
        if reversals > WALK_FEET_REVERSALS_MAX:
            out.append(f'{name}: the feet change direction {reversals} times, so the walk stutters; they should slide smoothly (at most {WALK_FEET_REVERSALS_MAX})')
        lifted = sum(1 for v in lows if v < GROUND_ROW)
        if lifted > WALK_LIFTED_MAX:
            out.append(f'{name}: the feet leave the ground on {lifted} frames; they slide, at most {WALK_LIFTED_MAX}')
    return out


def check_standing(lines, kind):
    """Size and place of a standing figure (the charging pose)."""
    pts = painted(lines)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    height = max(ys) - min(ys) + 1
    width = max(xs) - min(xs) + 1
    centre = (min(xs) + max(xs) + 1) / 2
    problems = []
    if kind == 'humanoid':
        if not STAND_HEIGHT[0] <= height <= STAND_HEIGHT[1]:
            problems.append(f'standing {height} rows tall; a person is {STAND_HEIGHT[0]}-{STAND_HEIGHT[1]}')
    else:
        if height < CREATURE_MIN_HEIGHT:
            problems.append(f'standing only {height} rows tall; a creature is at least {CREATURE_MIN_HEIGHT}')
        if width > CREATURE_MAX_WIDTH:
            problems.append(f'standing {width} columns wide; a creature is at most {CREATURE_MAX_WIDTH}')
    if not STAND_CENTRE_X[0] <= centre <= STAND_CENTRE_X[1]:
        problems.append(f'standing off centre (middle at {centre:g}); it should be {STAND_CENTRE_X[0]:g}-{STAND_CENTRE_X[1]:g}')
    return problems


# Every person has the bow animation: the draw, release and recoil (see make_bow.py), made on its own
# model and kept in the base set as optional poses. Someone who cannot draw a bow is listed here, with why.
BOW_EXEMPT = {'undead': 'has only one arm, so it cannot draw a bow'}


def check_bow(base_id, frames_by_pose):
    """A generated person has the bow animation, in both facings, unless it is exempt."""
    if base_id not in CREATORS or kind_of(base_id) != 'humanoid' or base_id in BOW_EXEMPT:
        return []
    return [f'{base_id} has no {pose}: every person has the bow animation (python3 tools/make_bow.py --bases {base_id})'
            for pose in ('bowNE', 'bowSE') if pose not in frames_by_pose]


# --- bosses -------------------------------------------------------------------------------------------
# A boss stands on four ground squares (a 2 x 2 footprint), so it is drawn in a 96 x 96 cell, three times a person's, with the middle of
# the footprint at BOSS_ANCHOR on the ground and its lowest row on BOSS_GROUND. It has the same actions as everyone else.
BOSS_CELL = 96
BOSS_ANCHOR = (48, 72)
BOSS_GROUND = 88
BOSS_FRAMES = {'charging': 1, 'attack': 4, 'release': 1, 'damage': 1, 'weak': 1, 'dead': 1, 'walking': 8}
BOSS_MIN_PIXELS = 1200


def check_boss(boss_id, frames_by_pose):
    """Every problem in a boss's frames (96 x 96 role rows), keyed like a base's: 'attackNE', 'walkingSE'..."""
    out = []
    for action, count in BOSS_FRAMES.items():
        for facing in ('NE', 'SE'):
            frames = frames_by_pose.get(action + facing)
            if frames is None:
                out.append(f'{boss_id} has no {action}{facing}: a boss has every action, in both facings')
                continue
            if len(frames) != count:
                out.append(f'{boss_id} {action}{facing}: {len(frames)} frames, a {action} has {count}')
            for i, lines in enumerate(frames):
                pts = painted(lines)
                name = f'{boss_id} {action}{facing} frame {i + 1}'
                if len(pts) < BOSS_MIN_PIXELS:
                    out.append(f'{name}: only {len(pts)} painted pixels')
                    continue
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if min(xs) < 1 or max(xs) > BOSS_CELL - 2 or min(ys) < 1 or max(ys) > BOSS_CELL - 2:
                    out.append(f'{name}: reaches the edge of the cell (columns {min(xs)}-{max(xs)}, rows {min(ys)}-{max(ys)})')
                if action != 'dead' and not BOSS_GROUND - 1 <= max(ys) <= BOSS_GROUND:
                    out.append(f'{name}: feet are on row {max(ys)}; the boss\'s ground is row {BOSS_GROUND}')
                open_edge = sum(1 for x, y in pts if lines[y][x] != ep.ROLES[0][0]
                                and any(not (0 <= x + dx < BOSS_CELL and 0 <= y + dy < BOSS_CELL) or lines[y + dy][x + dx] == '.'
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
                if open_edge > 4 * OPEN_EDGE_MAX:
                    out.append(f'{name}: {open_edge} pixels on the edge are not outlined')
    return out


def load_boss_frames(folder, boss_id):
    """A boss's sheets (NAME-actionFACING.png, frames side by side) as role rows, read back from the PNGs."""
    from PIL import Image
    to_role = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)): c for c, _, _, _, h in ep.ROLES}
    frames = {}
    for action in BOSS_FRAMES:
        for facing in ('NE', 'SE'):
            path = Path(folder) / f'{boss_id}-{action}{facing}.png'
            if not path.exists():
                continue
            img = Image.open(path).convert('RGBA')
            px = img.load()
            out = []
            for f in range(img.width // BOSS_CELL):
                out.append([''.join(to_role.get(px[f * BOSS_CELL + x, y][:3], '?') if px[f * BOSS_CELL + x, y][3] else '.'
                                    for x in range(BOSS_CELL)) for y in range(BOSS_CELL)])
            frames[action + facing] = out
    return frames


def check_base(base_id, frames_by_pose, kind=None, airborne=()):
    """Every problem in one base's poses, as 'pose frame N: problem' lines.

    `airborne` is a set of (action, frame index) that are allowed to leave the ground, such as a
    leap. Nothing else is.
    """
    kind = kind or kind_of(base_id)
    out = []
    for pose_id, frames in frames_by_pose.items():
        action = pose_id[:-2]
        for i, lines in enumerate(frames):
            for problem in check_frame(lines, action, kind, (action, i) in airborne):
                out.append(f'{base_id} {pose_id} frame {i + 1}: {problem}')
        if action == 'charging':
            for problem in check_standing(frames[0], kind):
                out.append(f'{base_id} {pose_id}: {problem}')
    if kind == 'humanoid':
        out += check_movement(base_id, frames_by_pose)
        out += check_walk(base_id, frames_by_pose)
    return out


# --- colour ramps ----------------------------------------------------------------------------
def luminance(char):
    hex_ = next(h for c, _, _, _, h in ep.ROLES if c == char)
    r, g, b = (int(hex_[i:i + 2], 16) for i in (0, 2, 4))
    return 0.299 * r + 0.587 * g + 0.114 * b


def check_eyes(creature, owner=''):
    """A person's open eyes are tall, thin, vertical slits (3 pixels tall), never dots (see CONVENTIONS.md)."""
    if getattr(creature, 'kind', 'humanoid') == 'humanoid' and not getattr(creature, 'tall_eyes', False):
        return [f'{owner} has dot eyes; every person has tall vertical slit eyes, 3 pixels tall (set tall_eyes, the default for a Humanoid)']
    return []


def check_ramps(ramps, owner=''):
    """A ramp is four palette roles, lit to deep, never getting lighter."""
    out = []
    known = {c for c, *_ in ep.ROLES}
    for material, ramp in ramps.items():
        if len(ramp) != RAMP_LENGTH:
            out.append(f'{owner} {material}: a ramp has {RAMP_LENGTH} roles (lit, base, shade, deep), not {len(ramp)}')
            continue
        if any(c not in known for c in ramp):
            out.append(f'{owner} {material}: {ramp} uses a role that is not in the palette')
            continue
        lum = [luminance(c) for c in ramp]
        if any(a < b for a, b in zip(lum, lum[1:])) or lum[0] <= lum[-1]:
            out.append(f'{owner} {material}: {ramp} must go from light to dark, but is {[round(v) for v in lum]}')
    return [p.strip() for p in out]


# --- weapons ---------------------------------------------------------------------------------
def weapon_paths(folder):
    """{weapon: {facing: [(x, y) middle of the weapon in each frame, in the character's cell]}}."""
    from PIL import Image
    found = {}
    for path in sorted(Path(folder).glob('*.png')):
        m = re.match(r'^(?P<name>.+?)-?attack(?P<facing>NE|SE)\.png$', path.name)
        if not m:
            continue
        im = Image.open(path).convert('RGBA')
        px = im.load()
        cell = im.height
        pad = (cell - CELL) / 2
        frames = []
        for f in range(WEAPON_FRAMES):
            pts = [(x - f * cell, y) for y in range(cell) for x in range(f * cell, f * cell + cell) if px[x, y][3] >= 128]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            frames.append(((min(xs) + max(xs) + 1) / 2 - pad, (min(ys) + max(ys) + 1) / 2 - pad))
        found.setdefault(m['name'], {})[m['facing']] = (path, im.size, frames)
    return found


def check_weapons(folder):
    out = []
    folder = Path(folder)
    if not folder.is_dir():
        return out
    found = weapon_paths(folder)
    for name, facings in found.items():
        for facing in ('NE', 'SE'):
            if facing not in facings:
                out.append(f'weapon {name}: no {facing} strip')
                continue
            path, size, _ = facings[facing]
            if size != (WEAPON_FRAMES * WEAPON_CELL, WEAPON_CELL):
                out.append(f'weapon {name} {facing}: {size[0]}x{size[1]}; a strip is {WEAPON_FRAMES * WEAPON_CELL}x{WEAPON_CELL}')
    # Weapons share a swing, so their paths should agree frame by frame.
    for facing in ('NE', 'SE'):
        paths = [f[facing][2] for f in found.values() if facing in f and f[facing][1] == (WEAPON_FRAMES * WEAPON_CELL, WEAPON_CELL)]
        if len(paths) < 2:
            continue
        for k in range(WEAPON_FRAMES):
            mx = sum(p[k][0] for p in paths) / len(paths)
            my = sum(p[k][1] for p in paths) / len(paths)
            for name, f in found.items():
                if facing in f and f[facing][1] == (WEAPON_FRAMES * WEAPON_CELL, WEAPON_CELL):
                    x, y = f[facing][2][k]
                    if ((x - mx) ** 2 + (y - my) ** 2) ** 0.5 > WEAPON_SPREAD:
                        out.append(f'weapon {name} {facing} frame {k + 1}: strays from the other weapons\' swing')
    return out


# --- generated characters --------------------------------------------------------------------
def creator_of(base_id):
    """The object a generated base is built from, or None for the original sprites."""
    name = CREATORS.get(base_id)
    if not name:
        return None
    return getattr(importlib.import_module(name), 'CREATURE')


def check_hand_path(creature, weapons_dir):
    """A humanoid's strike hand follows the weapons' swing, so a weapon in it looks held."""
    if not Path(weapons_dir).is_dir():
        return []
    import fit_hands
    paths = fit_hands.weapon_path(weapons_dir)
    out = []
    for facing in ('NE', 'SE'):
        if facing not in paths:
            continue
        frames = creature.poses.get('attack' + facing, creature.poses['attack'])
        import creature as creature_module
        origin = creature_module.calibrate(creature, facing)
        for i, (pose, target) in enumerate(zip(frames, paths[facing])):
            x, y = fit_hands.hand_on_screen(creature, pose, facing, origin, 'L')
            y += fit_hands.ground_offset(creature, pose, facing, origin)
            miss = ((x - target[0]) ** 2 + (y - target[1]) ** 2) ** 0.5
            limit = HAND_TOLERANCE_BY_BUILD.get(creature.name, HAND_TOLERANCE)
            if miss > limit:
                out.append(f'{creature.name} attack{facing} frame {i + 1}: the hand is {miss:.1f}px from the weapon (limit {limit:g})')
    return out


def load_bases(path=None):
    path = Path(path or ROOT / 'poses' / 'base.js')
    return json.loads(path.read_text()[len('window.BASE_POSES = '):].rstrip().rstrip(';'))
