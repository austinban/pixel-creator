"""Draw a creature for the character poses, from a small 3D model.

This is the shared machinery for making a new base character that is not a repaint of
the humanoid fighter. A creature is a handful of ellipsoids (body, head, legs, tail...).
Each is ray-cast from an isometric camera, flat-shaded into the shared palette's colour
roles, given a dark outline, and written as one PNG per pose in the same 32 x 32 cells and
frame counts as the other bases (see extract_poses.POSES). NE is the creature seen from
behind and SE from the front.

A new creature is a small module that describes its anatomy and poses and hands them to
`run`. See make_dog.py, which is the worked example:

    class Dog:
        name = 'dog'
        kind = 'creature'          # or 'humanoid': which size rules apply (see conventions.py)
        airborne = {('attack', 1)} # frames allowed to leave the ground; everything else stands on it
        ramps = {...}              # material -> four roles: lit, base, shade, deep
        stand = {...}              # a pose, only used to centre and ground the drawing
        poses = {'walking': [...], 'attack': [...], ...}   # action -> one pose per frame
                                   # ('attackSE': [...] overrides one facing)
        scale = 0.86               # shrink the model if frames touch the cell edge

        def place(self, pose):     # -> (parts, decals) already carried into the pose
            ...

    if __name__ == '__main__':
        run(Dog())

`parts` are made with `part(...)`; `bone` and `two_bone` lay a limb between two joints, and
the matrix helpers (rx, ry, rz, mm, mv) turn them. Everything is in model space: x forward,
y up, z to the creature's right, one unit a pixel, with the ground at y = 0.

    python3 tools/make_dog.py sprites/dog [--preview sheet.png]
    python3 tools/extract_poses.py --merge dog=sprites/dog

`run` also enforces the project's conventions (CONVENTIONS.md, conventions.py). Every frame is put
on the ground row the way the original bases are, then checked: inside the cell, outlined, the
right size, feet down, colour ramps light to dark. If anything is wrong it says what and writes
nothing, so a pose that breaks the rules cannot slip into the set. `--force` writes anyway.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventions  # noqa: E402
import extract_poses as ep  # noqa: E402

CELL = ep.CELL
SS = 2                        # subsamples per pixel, each way
LIGHT = (-0.45, 0.62, 0.64)   # in camera space: from the upper left, in front
TILT = math.radians(30)       # how far the camera looks down
YAW = {'SE': math.radians(-45), 'NE': math.radians(45)}
GROUND_ROW = 26               # lowest painted (not outline) row of a standing creature
OUTLINE, EYE = 'O', 'w'


# --- a little linear algebra ---------------------------------------------------------------
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def tr(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def deg(a):
    return math.radians(a)


I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


# --- building a creature -------------------------------------------------------------------
def part(c, r, mat, name, R=None):
    """An ellipsoid: centre, the three radii, its material, a name, and its orientation.

    Parts with the same name are one piece; where a nearer piece overlaps a different one,
    the edge falls into shadow, which is what separates a leg from the body.
    """
    return dict(c=c, r=r, R=R or I3, mat=mat, part=name)


def two_bone(hip, target, upper, lower, knee_forward):
    """Knee and foot for a limb reaching a target, in the side-on (x, y) plane."""
    hx, hy = hip[0], hip[1]
    dx, dy = target[0] - hx, target[1] - hy
    d = min(max(math.hypot(dx, dy), abs(upper - lower) + 0.05), upper + lower - 0.05)
    base = math.atan2(dy, dx)
    cos_a = (upper * upper + d * d - lower * lower) / (2 * upper * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    direction = base - a if knee_forward else base + a
    knee = (hx + upper * math.cos(direction), hy + upper * math.sin(direction))
    foot = (hx + d * math.cos(base), hy + d * math.sin(base))
    return knee, foot


def bone(a, b, z, radius, mat, name, grow=0.6):
    """An ellipsoid laid along the line from a to b, in the x-y plane at depth z."""
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    beta = math.atan2(b[1] - a[1], b[0] - a[0])
    return part((cx, cy, z), (radius, length / 2 + grow, radius * 0.95), mat, name, rz(beta - math.pi / 2))


# --- drawing -------------------------------------------------------------------------------
def render_frame(parts, decals, facing, origin, ramps, scale=1.0, decal_part='head'):
    """One 32 x 32 frame as role characters.

    `decals` are (point, shape) pairs, pixels laid on the drawing after it is made: eyes.
    The shape is 'open' for a dot, anything else for a short line (shut).
    """
    placed = [dict(q, c=tuple(x * scale for x in q['c']), r=tuple(x * scale for x in q['r'])) for q in parts]
    placed_decals = [(tuple(x * scale for x in pt), shape) for pt, shape in decals]

    # Camera: yaw to the facing, then tilt down. B takes a model point to camera space.
    B = mm([[1, 0, 0], [0, math.cos(TILT), -math.sin(TILT)], [0, math.sin(TILT), math.cos(TILT)]], ry(YAW[facing]))
    Bt = tr(B)
    direction = mv(Bt, (0, 0, 1))
    ox, oy = origin

    def project(pt):
        c = mv(B, pt)
        return ox + c[0], oy - c[1], c[2]

    prepared = [(q, tr(q['R']), q['r']) for q in placed]

    def cast(sx, sy):
        """The nearest ellipsoid along the ray through this screen point."""
        origin_m = mv(Bt, (sx - ox, oy - sy, 0.0))
        best = None
        for q, Rt, r in prepared:
            o = mv(Rt, sub(origin_m, q['c']))
            o = (o[0] / r[0], o[1] / r[1], o[2] / r[2])
            d = mv(Rt, direction)
            d = (d[0] / r[0], d[1] / r[1], d[2] / r[2])
            a = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
            b = o[0] * d[0] + o[1] * d[1] + o[2] * d[2]
            c = o[0] * o[0] + o[1] * o[1] + o[2] * o[2] - 1
            disc = b * b - a * c
            if disc < 0:
                continue
            t = (-b + math.sqrt(disc)) / a
            if best is None or t > best[0]:
                u = tuple(o[i] + t * d[i] for i in range(3))
                n = mv(q['R'], (u[0] / r[0], u[1] / r[1], u[2] / r[2]))
                m = math.sqrt(sum(x * x for x in n)) or 1
                nc = mv(B, tuple(x / m for x in n))
                shade = 0.22 + 0.78 * max(0.0, sum(nc[i] * LIGHT[i] for i in range(3)))
                best = (t, q['mat'], q['part'], shade)
        return best

    grid = [[None] * CELL for _ in range(CELL)]
    depth = [[-1e9] * CELL for _ in range(CELL)]
    for py in range(CELL):
        for px in range(CELL):
            hits = []
            for i in range(SS):
                for j in range(SS):
                    s = cast(px + (i + 0.5) / SS, py + (j + 0.5) / SS)
                    if s:
                        hits.append(s)
            if len(hits) * 2 >= SS * SS:
                top = max(hits)
                grid[py][px] = [top[1], top[2], top[3]]
                depth[py][px] = top[0]

    out = [['.'] * CELL for _ in range(CELL)]
    for y in range(CELL):
        for x in range(CELL):
            cell = grid[y][x]
            if not cell:
                continue
            mat, name, shade = cell
            level = 0 if shade > 0.80 else 1 if shade > 0.52 else 2 if shade > 0.34 else 3
            # Where a nearer part overlaps this one, the edge falls into shadow.
            for nx, ny in ((x - 1, y), (x, y - 1)):
                other = grid[ny][nx] if 0 <= nx < CELL and 0 <= ny < CELL else None
                if other and other[1] != name and depth[ny][nx] - depth[y][x] > 1.5 * scale:
                    level = 3
            out[y][x] = ramps[mat][level]

    # Eyes: a dot, or a short line when shut. Only where the head is actually in front.
    for pt, shape in placed_decals:
        sx, sy, dz = project(pt)
        px, py = int(sx), int(sy)
        if 0 <= px < CELL and 0 <= py < CELL and grid[py][px] and grid[py][px][1] == decal_part and depth[py][px] - dz < 0.9:
            if shape == 'open':
                out[py][px] = EYE
            else:
                for dx in (0, 1):
                    if px + dx < CELL and grid[py][px + dx]:
                        out[py][px + dx] = EYE

    # Outline: every empty cell that touches the creature.
    final = [row[:] for row in out]
    for y in range(CELL):
        for x in range(CELL):
            if out[y][x] != '.':
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < CELL and 0 <= ny < CELL and out[ny][nx] != '.':
                    final[y][x] = OUTLINE
                    break
    return [''.join(row) for row in final]


def project_point(pt, facing, origin, scale=1.0):
    """Where a model-space point lands in the 32 x 32 cell, in pixels (a pixel covers x to x + 1)."""
    B = mm([[1, 0, 0], [0, math.cos(TILT), -math.sin(TILT)], [0, math.sin(TILT), math.cos(TILT)]], ry(YAW[facing]))
    c = mv(B, tuple(x * scale for x in pt))
    return origin[0] + c[0], origin[1] - c[1]


def calibrate(creature, facing):
    """Where to put the origin so a standing creature is centred and its paws touch the ground row.

    A creature that is another one in different clothes can say `calibrate_like`, so both are drawn on
    exactly the same grid: a hood that changes the standing width by half a pixel should not move the
    whole body half a pixel and change how every frame samples.
    """
    creature = getattr(creature, 'calibrate_like', None) or creature
    ox, oy = CELL / 2, 24.0
    for _ in range(3):
        parts, decals = creature.place(creature.stand)
        rows = render_frame(parts, decals, facing, (ox, oy), creature.ramps, creature.scale)
        painted = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch not in '.' + OUTLINE]
        xs = [x for x, _ in painted]
        low = max(y for _, y in painted)
        ox += (CELL - 1) / 2 - (min(xs) + max(xs)) / 2
        oy += GROUND_ROW - low
    return ox, oy


def to_png(frames, cols, rows, path):
    from PIL import Image
    rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    img = Image.new('RGBA', (cols * CELL, rows * CELL), (0, 0, 0, 0))
    px = img.load()
    for index, lines in enumerate(frames):
        ox, oy = (index % cols) * CELL, (index // cols) * CELL
        for y, line in enumerate(lines):
            for x, ch in enumerate(line):
                if ch != '.':
                    px[ox + x, oy + y] = (*rgb[ch], 255)
    img.save(path)
    return img


def shift_rows(lines, dy):
    """A frame moved down by dy rows (up if negative); rows pushed off the edge are lost."""
    blank = '.' * CELL
    if dy >= 0:
        return [blank] * dy + lines[:CELL - dy]
    return lines[-dy:] + [blank] * -dy


def render_centred(parts, decals, facing, origin, ramps, scale):
    """A single-frame pose drawn centred in its cell, as the originals' are, whatever its lean did.

    The camera moves, not the pixels, so nothing is clipped at the edge on the way.
    """
    ox, oy = origin
    for _ in range(3):
        lines = render_frame(parts, decals, facing, (ox, oy), ramps, scale)
        xs = [x for line in lines for x, ch in enumerate(line) if ch != '.']
        if not xs:
            break
        miss = conventions.CENTRE_X - (min(xs) + max(xs) + 1) / 2
        if abs(miss) < 0.5:
            break
        ox += round(miss)
    return lines


def ground(lines, action, airborne):
    """Put a frame's feet on the ground row, as every original base does, even mid-lunge."""
    rows = [y for y, line in enumerate(lines) if line.strip('.')]
    if not rows:
        return lines
    target = sum(conventions.DEAD_ROWS) // 2 if action == 'dead' else conventions.GROUND_ROW
    return lines if airborne else shift_rows(lines, target - max(rows))


def run(creature):
    """The command line for a creature: write its pose PNGs, and optionally a contact sheet."""
    parser = argparse.ArgumentParser(description=f'Draw the {creature.name}.')
    parser.add_argument('out', type=Path, nargs='?', help=f'folder for the pose PNGs, e.g. sprites/{creature.name}')
    parser.add_argument('--model', type=Path, help='write a 3D preview of the model here instead of making sprites (see preview3d.py)')
    parser.add_argument('--pose', default='charging', help='with --model: which pose (an action name), default charging')
    parser.add_argument('--frame', type=int, default=0, help='with --model: which frame of the pose')
    parser.add_argument('--views', help='with --model: comma-separated views from face, SE, side, NE, back')
    parser.add_argument('--preview', type=Path, help='also write one contact sheet of every pose here')
    parser.add_argument('--force', action='store_true', help='write the poses even if they break the conventions')
    args = parser.parse_args()

    if args.model:
        import preview3d
        views = args.views.split(',') if args.views else None
        sheet = preview3d.render_sheet(creature, preview3d.pick_pose(creature, args.pose, args.frame), views)
        sheet.save(args.model)
        print(f'3D preview of the {creature.name} ({args.pose}, frame {args.frame + 1}) -> {args.model}; no sprites were made')
        return
    if not args.out:
        parser.error('say where to write the sprites, or use --model to see the 3D model first')

    origins = {f: calibrate(creature, f) for f in ('NE', 'SE')}
    airborne = getattr(creature, 'airborne', set())
    kind = getattr(creature, 'kind', 'humanoid')
    built, problems = {}, conventions.check_ramps(creature.ramps, creature.name)
    for action, facing, cols, rows in ep.POSES:
        frames = []
        # A creature can give one facing its own frames, e.g. 'attackSE' beside 'attack'.
        for i, pose in enumerate(creature.poses.get(action + facing, creature.poses[action])):
            parts, decals = creature.place(pose)
            draw = render_centred if cols * rows == 1 else render_frame
            lines = draw(parts, decals, facing, origins[facing], creature.ramps, creature.scale)
            frames.append(ground(lines, action, (action, i) in airborne))
        if len(frames) != cols * rows:
            sys.exit(f'{action}{facing}: made {len(frames)} frames, the pose needs {cols * rows}')
        built[(action, facing, cols, rows)] = frames
    problems += conventions.check_base(creature.name, {f'{a}{f}': fr for (a, f, _, _), fr in built.items()}, kind, airborne)
    if problems and not args.force:
        print(f'{creature.name} breaks the conventions, so nothing was written (see CONVENTIONS.md; --force to write anyway):', file=sys.stderr)
        for p in problems:
            print('  ' + p, file=sys.stderr)
        sys.exit(1)
    args.out.mkdir(parents=True, exist_ok=True)
    sheets = [to_png(fr, cols, rows, args.out / f'{creature.name}-{a}{f}.png') for (a, f, cols, rows), fr in built.items()]
    print(f'wrote {len(sheets)} poses -> {args.out}' + (f' (with {len(problems)} problems, forced)' if problems else ''))

    if args.preview:
        from PIL import Image
        scale = 4
        width = max(i.width for i in sheets) * scale
        height = sum(i.height * scale + 4 for i in sheets)
        contact = Image.new('RGBA', (width, height), (60, 64, 74, 255))
        y = 0
        for img in sheets:
            contact.alpha_composite(img.resize((img.width * scale, img.height * scale), Image.NEAREST), (0, y))
            y += img.height * scale + 4
        contact.save(args.preview)
