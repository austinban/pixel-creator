"""A generic humanoid, for building characters from scratch with creature.py.

The knight, skeleton and zombie are paintings over the fighter's poses. This builds a person
instead: a torso, a big head, two arms and two legs, as ellipsoids, rendered by creature.py in
the same 32 x 32 cells, the same 14 poses and the same palette roles as every other base. Limbs
are solved with two-bone inverse kinematics, so a hand goes where the pose puts it and a foot
stays on the ground.

Making a character is a description, not new drawing code:

    from humanoid import Humanoid, run

    run(Humanoid('guard', ramps={'shirt': ('q', 'p', 'l', 'k'), ...}, hair='none',
                 accessories=my_helmet_and_spear))

then

    python3 tools/make_guard.py sprites/guard [--preview sheet.png]
    python3 tools/extract_poses.py --merge guard=sprites/guard

What can be changed, all optional:

    ramps        material -> four roles (lit, base, shade, deep). Materials: skin, hair, shirt,
                 pants, shoes, belt. Any other name is yours to use from `accessories`.
    hair         'short', 'long' or 'none'
    body         proportions, in pixels; see BODY for the names. `bulk` is how heavy it looks
    scale        shrink or grow the whole figure
    accessories  a function that adds parts (a hat, a cape, a staff). It is given the joints of
                 the pose so it can follow a hand or the head:

                     def accessories(j):
                         return [part(j['head'](0, 22, 0), (5, 1, 5), 'hat', 'hat')]   # on the head
                         # j['hand_R'] is the right hand's world position; j['body'](x, y, z)
                         # and j['head'](x, y, z) carry a point in the standing figure along;
                         # j['head_R'] is how the head is turned (give a part this as its
                         # orientation to make it turn with the head)

    calibrate_like  another build to draw on the same grid as (for a restyle of it)
    tweaks       pose id -> values to fix for this build (kept as they are; the tuners skip those poses)
    tuning       whose tuned numbers to use; defaults to its own name (see tune_lean.py, fit_hands.py)
    poses        replace or add poses by action name; each is a list of pose dicts (see POSE).
                 'attackSE' beside 'attack' gives that one facing its own frames. The default attack
                 is an overhand swing with the left hand, like the other bases

Everything is in model space: x forward, y up, z to the figure's right, one unit a pixel, with
the ground at y = 0.
"""
import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creature import add, bone, deg, mm, mv, part, run, rx, ry, rz, sub, two_bone  # noqa: E402,F401

DATA = Path(__file__).resolve().parent / 'data'


def tuned(name):
    """Numbers worked out by a tool and kept as data: see tune_lean.py and fit_hands.py."""
    path = DATA / name
    return json.loads(path.read_text()) if path.exists() else {}


# Colour ramps by role: lit, base, shade, deep. A generic person: blue tunic, dark trousers,
# brown hair and boots, a gold belt.
RAMPS = {
    'skin': ('C', 'b', 'e', 'f'),
    'hair': ('f', 'g', 'w', 'x'),
    'shirt': ('n', 'm', 'k', 'w'),
    'pants': ('p', 'l', 'k', 'w'),
    'shoes': ('f', 'g', 'w', 'x'),
    'belt': ('d', 'b', 'a', 'e'),
}

# Proportions, in pixels. A big head on a small body, like the other bases.
BODY = dict(
    leg_upper=3.4, leg_lower=3.6,          # hip to knee, knee to ankle
    arm_upper=3.5, arm_lower=3.7,          # shoulder to elbow, elbow to wrist (long, like the other bases')
    hip_y=7.4, hip_z=1.7,
    shoulder_y=13.4, shoulder_z=3.7,
    head_fwd=1.5,                          # the head sits ahead of the shoulders, as in the originals
    bulk=1.5,
    hand_mat='skin', neck_mat='skin',      # what the forearms, hands and neck are made of (gloves, a scarf...)
    foot_rx=1.7, foot_ry=1.0, foot_rz=1.7, foot_toe=0.5,   # short, small feet, like the originals'                             # how thick the body and limbs are; weight, without height
    head_y=18.6, head_rx=4.8, head_ry=4.6, head_rz=4.5,
)


# --- poses ---------------------------------------------------------------------------------
# A pose is a dict. Anything left out falls back to BASE.
#   pitch   lean of the whole body, degrees; positive leans back
#   roll    turn about the forward axis, degrees (lying on a side)
#   twist   turn of the whole body about the vertical, degrees, into or away from a swing
#   sway    weight shifted forward: the upper body moves this many pixels ahead of the hips (the
#           feet stay put). This is what leans a figure into its movement (see CONVENTIONS.md)
#   lift    body height; negative bends the knees
#   fwd     step forward, pixels
#   head_pitch, head_yaw   the head, about the neck
#   spread  how far the arms are held out from the body, pixels (clears the head when raised)
#   eyes    'open' or 'shut'
#   hands   {'L': (dx, dy), 'R': (dx, dy)}  where each hand goes, from its own shoulder
#   feet    {'L': (dx, lift), 'R': (dx, lift)}  where each foot goes: ahead of the hip, and how high
#   A hand or foot given four numbers (0, 0, a1, a2) is bent by raw angles instead; this is for
#   lying down.
BASE = dict(pitch=0, roll=0, twist=0, sway=0, lift=0, fwd=0, head_pitch=0, head_yaw=0, spread=0, eyes='open',
            hands={'L': (0.3, -5.6), 'R': (0.3, -5.6)}, feet={'L': (0, 0), 'R': (0, 0)})


def pose(**kw):
    p = copy.deepcopy(BASE)
    p.update(kw)
    return p


def walk(k, n=8):
    """One frame of the walk the originals share: the body bobs, the feet slide, the head stays put.

    The body goes down and up twice in the eight frames, a period of four. The feet slide back along
    the ground and swing forward barely off it, and the arms swing against the legs. The legs are straight
    when standing, so a walk starts slightly crouched and bobs between there and lower, which
    leaves room to rise and fall evenly. Nothing sways
    forward and back: the upper body does not move across the screen, so the lean (conventions.LEAN)
    is one steady weight shift for the whole walk, not a different one each frame.
    """
    phase = 2 * math.pi * k / n
    feet, hands = {}, {}
    for side, offset in (('L', 0.0), ('R', math.pi)):
        s = (phase + offset) % (2 * math.pi)
        if s < math.pi:                       # foot on the ground, sliding back
            dx, lift = 3.1 * (1 - 2 * s / math.pi), 0.0
        else:                                 # swinging forward, only just off the ground
            u = (s - math.pi) / math.pi
            dx, lift = -3.1 + 6.2 * u, 0.9 * math.sin(math.pi * u)      # barely off the ground
        feet[side] = (dx, lift)
        # the arm on the same side swings against the leg
        hands[side] = (0.3 - 0.6 * dx, -5.4 + 0.2 * abs(dx))
    return pose(feet=feet, hands=hands, lift=-2.0 + 1.0 * math.cos(2 * math.pi * k / 4), pitch=-3)


def mirrored(p):
    """The same pose with left and right swapped."""
    q = copy.deepcopy(p)
    q['hands'] = {'L': p['hands']['R'], 'R': p['hands']['L']}
    q['feet'] = {'L': p['feet']['R'], 'R': p['feet']['L']}
    return q


def standard_poses():
    """The 14 poses every base needs, as action -> frames."""
    # An overhand swing with the left hand, in both facings, following the weapons' path: the arm
    # starts swung back behind the body, comes up and over the head in an arc, strikes forward and
    # down through chest height with a lunge, then follows through low. The right hand guards,
    # then is thrown back for balance. The left hand's positions and the body's turn into the swing
    # were found with tools/fit_hands.py, so the hand is where the weapon strips put the weapon.
    def swing(left, twist):
        frames = [
            pose(pitch=8, lift=-0.8, fwd=-1.2, head_pitch=2, spread=1.8,
                 hands={'L': left[0], 'R': (2.2, -2.2)}, feet={'L': (-2.2, 0), 'R': (1.6, 0)}),
            pose(pitch=12, lift=-0.6, fwd=-0.4, head_pitch=6, spread=3.2,
                 hands={'L': left[1], 'R': (1.8, -1.8)}, feet={'L': (-2.4, 0), 'R': (2.0, 0)}),
            pose(pitch=-12, lift=-0.9, fwd=4.4, head_pitch=-6, spread=0.8,
                 hands={'L': left[2], 'R': (-2.0, -3.2)}, feet={'L': (-3.4, 0), 'R': (3.2, 0)}),
            pose(pitch=-6, lift=-0.4, fwd=1.6, head_pitch=-2,
                 hands={'L': left[3], 'R': (0.4, -4.8)}, feet={'L': (-1.6, 0), 'R': (2.0, 0)}),
        ]
        for frame, t in zip(frames, twist):
            frame['twist'] = t
        return frames

    attack = swing([(-7.0, -1.0), (3.5, 3.0), (5.0, -5.0), (5.0, -5.0)], [0, 0, -40, -40])
    attack_se = swing([(-6.5, 2.5), (4.0, 5.5), (5.0, -5.0), (5.0, -5.0)], [10, 0, 0, -10])
    return {
        # gathering strength: a low wide stance, fists drawn in at the chest
        'charging': [pose(pitch=4, lift=-1.1, head_pitch=12,
                          hands={'L': (2.2, -1.8), 'R': (2.5, -1.3)}, feet={'L': (-1.4, 0), 'R': (2.0, 0)})],
        # an overhand swing with the left hand, in both facings (see `attack` above)
        'attack': attack,
        'attackSE': attack_se,
        # throwing power forward: both hands thrust out and up
        'release': [pose(pitch=9, lift=-0.4, head_pitch=8, spread=2.5,
                         hands={'L': (4.2, 1.2), 'R': (4.4, 1.9)}, feet={'L': (2.0, 0), 'R': (-2.0, 0)})],
        # a flinch: thrown back, head wrenched up and round, arms flung
        'damage': [pose(pitch=10, lift=-5.0, fwd=-1.8, head_pitch=6, head_yaw=14, eyes='shut',
                        hands={'L': (-2.8, -2.4), 'R': (-2.6, -1.0)}, feet={'L': (2.2, 0), 'R': (-2.4, 0)})],
        # worn out: knees bent, slumped forward, head hanging, arms dangling
        'weak': [pose(pitch=-55, lift=-7.2, head_pitch=-22, eyes='shut',
                      hands={'L': (0.9, -5.2), 'R': (0.5, -5.2)}, feet={'L': (0.8, 0), 'R': (-0.8, 0)})],
        # flat on the back, head behind, legs and arms out
        'dead': [pose(pitch=90, lift=-1.6, head_pitch=-6, eyes='shut',
                      hands={'L': (0, 0, 22, 6), 'R': (0, 0, -16, 4)}, feet={'L': (0, 0, 8, 2), 'R': (0, 0, -9, 3)})],
        'walking': [walk(k) for k in range(8)],
    }


# --- the figure ----------------------------------------------------------------------------
class Humanoid:
    def __init__(self, name, ramps=None, hair='short', body=None, scale=None, accessories=None, poses=None, tuning=None, tweaks=None, calibrate_like=None):
        self.name = name
        self.calibrate_like = calibrate_like   # draw on another build's grid (see creature.calibrate)
        self.tweaks = tweaks or {}         # pose id -> values to fix for this build, e.g. {'weakNE': {'pitch': -48}}
        self.tuning = tuning or name       # whose lean and hand numbers to use (data/NAME_lean.json, NAME_hands.json)
        self.kind = 'humanoid'
        self.airborne = set()
        self.ramps = dict(RAMPS, **(ramps or {}))
        self.hair = hair
        self.body = dict(BODY, **(body or {}))
        self.scale = scale if scale is not None else 1.05
        self.accessories = accessories
        self.poses = dict(standard_poses(), **(poses or {}))
        self.poses.setdefault('attackNE', self.poses['attack'])
        self.stand = pose()
        if not poses:
            self.apply_tuning()
        for pose_id, changes in self.tweaks.items():      # a build's own answers win over the tuned ones
            frames = copy.deepcopy(self.poses.get(pose_id, self.poses[pose_id[:-2]]))
            for frame in frames:
                frame.update(changes)
            self.poses[pose_id] = frames

    def apply_tuning(self):
        """Lay the tool-made numbers over the hand-written poses.

        data/NAME_lean.json: each frame's sway, so the figure leans into its movement the
        way the original bases do (conventions.LEAN). data/NAME_hands.json: where the strike
        hand and the body's turn have to be so the weapon is in the hand (fit_hands.py).
        """
        # A build with no numbers of its own yet borrows the standard Human's until it is tuned.
        key = self.tuning if (DATA / f'{self.tuning}_lean.json').exists() else 'human'
        for pose_id, sways in tuned(f'{key}_lean.json').items():
            frames = copy.deepcopy(self.poses.get(pose_id, self.poses[pose_id[:-2]]))
            for frame, sway in zip(frames, sways):
                frame['sway'] = sway
            self.poses[pose_id] = frames
        hands_key = self.tuning if (DATA / f'{self.tuning}_hands.json').exists() else 'human'
        for pose_id, fits in tuned(f'{hands_key}_hands.json').items():
            frames = copy.deepcopy(self.poses[pose_id])
            for frame, fit in zip(frames, fits):
                frame['hands'] = dict(frame['hands'], L=tuple(fit['L']))
                frame['twist'] = fit['twist']
            self.poses[pose_id] = frames

    # Standing-figure parts, grouped by what moves together.
    def anatomy(self, p):
        b = self.body
        k = b['bulk']
        torso = [
            part((0, 11.3, 0), (3.8 * k, 3.7, 3.0 * k), 'shirt', 'torso'),
            part((0, 8.2, 0), (3.4 * k, 2.0, 2.8 * k), 'pants', 'pelvis'),
            part((0, 9.5, 0), (3.55 * k, 0.6, 2.95 * k), 'belt', 'torso'),
            part((0.3, b['shoulder_y'] + 1.2, 0), (1.6, 1.3, 1.5), b['neck_mat'], 'neck'),
        ]
        hy = b['head_y']
        head = [
            part((0, hy, 0), (b['head_rx'], b['head_ry'], b['head_rz']), 'skin', 'head'),
            part((-0.1, hy - 0.2, b['head_rz'] - 0.2), (1.0, 1.5, 0.7), 'skin', 'ear'),
            part((-0.1, hy - 0.2, -b['head_rz'] + 0.2), (1.0, 1.5, 0.7), 'skin', 'ear'),
        ]
        if self.hair != 'none':
            # A shell a little bigger than the skull and set back, so it covers the top, back and
            # sides completely, and a fringe across the forehead for the hairline. Only the face
            # is left bare. (A smaller cap lets the skin show through as bald patches.)
            head.append(part((-1.4, hy + 0.9, 0), (b['head_rx'] - 0.2, b['head_ry'] + 0.1, b['head_rz'] + 0.3), 'hair', 'hair'))
            head.append(part((2.4, hy + 2.9, 0), (2.4, 1.7, b['head_rz'] - 0.9), 'hair', 'hair'))
        if self.hair == 'long':
            head.append(part((-3.3, hy - 2.4, 0), (1.9, 4.4, b['head_rz'] - 0.6), 'hair', 'hair'))
        decals = [((b['head_rx'] - 0.4, hy + 0.1, side * 1.95), p['eyes']) for side in (-1, 1)]
        return torso, head, decals

    def place(self, p):
        b = self.body
        torso, head, decals = self.anatomy(p)
        pivot = (0.0, b['hip_y'] + 0.8, 0.0)         # the body turns about the hips
        neck = (0.3, b['shoulder_y'] + 1.4, 0.0)     # the head turns about the neck
        g = mm(ry(deg(p['twist'])), mm(rx(deg(p['roll'])), rz(deg(p['pitch']))))
        shift = (p['fwd'], p['lift'], 0.0)
        h = mm(ry(deg(p['head_yaw'])), rz(deg(p['head_pitch'])))

        def on_body(pt):
            # The upper body sways forward over the hips; the feet do not move.
            t = max(0.0, (pt[1] - pivot[1]) / (b['head_y'] - pivot[1]))
            pt = (pt[0] + p['sway'] * t, pt[1], pt[2])
            return add(add(pivot, mv(g, sub(pt, pivot))), shift)

        def on_head(pt):
            return on_body(add(add(neck, mv(h, sub(pt, neck))), (b['head_fwd'], 0.0, 0.0)))

        placed = [dict(q, c=on_body(q['c']), R=mm(g, q['R'])) for q in torso]
        placed += [dict(q, c=on_head(q['c']), R=mm(g, mm(h, q['R']))) for q in head]

        joints = {'body': lambda x, y, z: on_body((x, y, z)), 'head': lambda x, y, z: on_head((x, y, z)),
                  'head_R': mm(g, h)}        # how the head is turned, so a mask or hat can turn with it

        # Legs: a hip, a knee that bends forward, an ankle on the ground, and a shoe.
        for side, z in (('L', -1), ('R', 1)):
            hip = (0.0, b['hip_y'], z * b['hip_z'])
            hip_w = on_body(hip)
            spec = p['feet'][side]
            if len(spec) == 2:
                knee, foot = two_bone(hip_w, (hip[0] + spec[0], spec[1]), b['leg_upper'], b['leg_lower'], True)
                toe = (foot[0] + b['foot_toe'], foot[1] + 0.9)
            else:
                a1, a2 = deg(spec[2]), deg(spec[3])
                knee = (hip[0] + b['leg_upper'] * math.sin(a1), hip[1] - b['leg_upper'] * math.cos(a1))
                foot = (knee[0] + b['leg_lower'] * math.sin(a1 + a2), knee[1] - b['leg_lower'] * math.cos(a1 + a2))
                toe = (foot[0] + b['foot_toe'], foot[1] + 0.9)
                knee, foot, toe = [on_body((k[0], k[1], hip[2]))[:2] for k in (knee, foot, toe)]
            placed.append(bone(hip_w[:2], knee, hip_w[2], 1.75 * b['bulk'], 'pants', 'leg' + side))
            placed.append(bone(knee, foot, hip_w[2], 1.5 * b['bulk'], 'pants', 'leg' + side, grow=0.4))
            placed.append(part((toe[0], toe[1], hip_w[2]), (b['foot_rx'], b['foot_ry'], b['foot_rz']), 'shoes', 'leg' + side))

        # Arms: a shoulder, an elbow that bends back, a wrist, and a hand. Sleeves are short.
        hands_w = {}
        for side, z in (('L', -1), ('R', 1)):
            shoulder = (0.0, b['shoulder_y'], z * b['shoulder_z'])
            sh_w = on_body(shoulder)
            spec = p['hands'][side]
            if len(spec) == 2:
                elbow, wrist = two_bone(sh_w, (sh_w[0] + spec[0], sh_w[1] + spec[1]), b['arm_upper'], b['arm_lower'], False)
            else:
                a1, a2 = deg(spec[2]), deg(spec[3])
                elbow = (shoulder[0] + b['arm_upper'] * math.sin(a1), shoulder[1] - b['arm_upper'] * math.cos(a1))
                wrist = (elbow[0] + b['arm_lower'] * math.sin(a1 + a2), elbow[1] - b['arm_lower'] * math.cos(a1 + a2))
                elbow, wrist = [on_body((k[0], k[1], shoulder[2]))[:2] for k in (elbow, wrist)]
            arm_z = sh_w[2] + z * p['spread']
            placed.append(bone(sh_w[:2], elbow, arm_z, 1.45 * b['bulk'], 'shirt', 'arm' + side))
            placed.append(bone(elbow, wrist, arm_z, 1.15 * b['bulk'], b['hand_mat'], 'arm' + side, grow=0.3))
            placed.append(part((wrist[0], wrist[1] - 0.2, arm_z), (1.2 * b['bulk'], 1.2 * b['bulk'], 1.1 * b['bulk']), b['hand_mat'], 'arm' + side))
            hands_w[side] = (wrist[0], wrist[1], arm_z)
        joints['hand_L'], joints['hand_R'] = hands_w['L'], hands_w['R']
        self.last_joints = joints          # so a tool can ask where the hands ended up

        if self.accessories:
            placed += self.accessories(joints, p)
        return placed, [(on_head(pt), shape) for pt, shape in decals]
