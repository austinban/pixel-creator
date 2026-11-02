"""A 3D preview of a creature or person, before it is turned into pixels.

Pixelating is slow and throws away detail, so a design is looked at first as the model it is: the same
ellipsoids, camera and light the sprites are made from, drawn smooth, large and in the real colours,
from several angles. Change the model until it looks right here, then make the sprites.

    python3 tools/make_ninja.py --model preview.png                  five views of the standing pose
    python3 tools/make_ninja.py --model preview.png --pose attack --frame 2
    python3 tools/make_ninja.py --model preview.png --views face,SE  just these views

The views: face (looking straight at the face), SE and NE (the two sprite facings), side, and back.
Colours go light to dark along each material's ramp as the surface turns from the light, and the
outline is the outline colour, so what you see here is what the pixel art will be shaded from.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import creature as cr  # noqa: E402
import extract_poses as ep  # noqa: E402

VIEWS = {              # name -> yaw in degrees. Forward is +x; -90 turns the face to the camera.
    'face': -90, 'SE': -45, 'side': 0, 'NE': 45, 'back': 90,
}
OUTLINE_RGB = tuple(int(ep.ROLES[0][4][i:i + 2], 16) for i in (0, 2, 4))
SUPER = 2              # drawn this much larger and shrunk, for smooth edges


def _rgb(role):
    hex_ = next(h for c, _, _, _, h in ep.ROLES if c == role)
    return np.array([int(hex_[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def _colour(ramp, shade):
    """The colour of a surface that catches `shade` of the light, along a ramp from lit to deep."""
    stops = np.array([1.0, 0.66, 0.43, 0.22])         # where lit, base, shade, deep sit
    pts = np.stack([_rgb(r) for r in ramp])
    s = np.clip(shade, 0.22, 1.0)
    out = np.zeros(shade.shape + (3,))
    for channel in range(3):
        out[..., channel] = np.interp(s, stops[::-1], pts[::-1, channel])
    return out


def render_view(parts, decals, ramps, yaw_deg, size=300, scale=1.0, eye=(0, 0, 0), fit_points=()):
    """One view as an RGBA image, `size` pixels square, the model fitted to it.

    `fit_points` are extra model points the picture must have room for, so a set of views of a
    changing model (an animation) can share one scale and position.
    """
    yaw = np.radians(yaw_deg)
    tilt = cr.TILT
    M = np.array([[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]])
    Ry = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    B = M @ Ry                                          # model space to camera space
    Bt = B.T
    direction = Bt @ np.array([0.0, 0.0, 1.0])
    light = np.array(cr.LIGHT)

    placed = []
    for q in parts:
        c = np.array(q['c']) * scale
        r = np.array(q['r']) * scale
        R = np.array(q['R'])
        placed.append((q, c, r, R, R.T))

    # Fit the model to the picture: the screen extent of every ellipsoid's bounding sphere.
    centres = np.array([B @ p[1] for p in placed] + [B @ (np.array(q) * scale) for q in fit_points])
    radii = np.array([p[2].max() for p in placed] + [0.0] * len(fit_points))
    lo = (centres[:, :2] - radii[:, None]).min(axis=0)
    hi = (centres[:, :2] + radii[:, None]).max(axis=0)
    span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.08
    px = size * SUPER / span                            # pixels per model unit
    mid = (lo + hi) / 2

    n = size * SUPER
    xs = (np.arange(n) - n / 2) / px + mid[0]           # camera x of each column
    ys = -(np.arange(n) - n / 2) / px + mid[1]          # camera y of each row (up is positive)
    X, Y = np.meshgrid(xs, ys)
    origin = Bt[:, 0][None, None, :] * X[..., None] + Bt[:, 1][None, None, :] * Y[..., None]

    best_t = np.full((n, n), -1e9)
    mat_id = np.full((n, n), -1)
    shade = np.zeros((n, n))
    part_id = np.full((n, n), -1)
    materials = sorted({p[0]['mat'] for p in placed})
    names = sorted({p[0]['part'] for p in placed})

    np.seterr(all='ignore')          # rays that miss produce huge numbers that are thrown away
    for q, c, r, R, Rt in placed:
        o = ((origin - c) @ Rt.T) / r
        d = (Rt @ direction) / r
        a = float(d @ d)
        b = o @ d
        cc = (o * o).sum(axis=-1) - 1.0
        disc = b * b - a * cc
        hit = disc >= 0
        t = np.where(hit, (-b + np.sqrt(np.where(hit, disc, 0))) / a, -1e9)
        nearer = hit & (t > best_t)
        if not nearer.any():
            continue
        u = o + t[..., None] * d
        nrm = (u / r) @ R.T
        nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
        nc = nrm @ B.T
        s = 0.22 + 0.78 * np.clip(nc @ light, 0.0, None)
        best_t = np.where(nearer, t, best_t)
        shade = np.where(nearer, s, shade)
        mat_id = np.where(nearer, materials.index(q['mat']), mat_id)
        part_id = np.where(nearer, names.index(q['part']), part_id)

    covered = mat_id >= 0
    img = np.zeros((n, n, 3))
    for i, m in enumerate(materials):
        sel = mat_id == i
        if sel.any():
            img[sel] = _colour(ramps[m], shade[sel])

    # Eyes: a dark dot where the head is in front, as in the sprite.
    for pt, shape in decals:
        cam = B @ (np.array(pt) * scale)
        col = int(round((cam[0] - mid[0]) * px + n / 2))
        row = int(round(-(cam[1] - mid[1]) * px + n / 2))
        if 0 <= row < n and 0 <= col < n and covered[row, col] and names[part_id[row, col]] == 'head' and best_t[row, col] - cam[2] < cr.EYE_REACH:
            rad = int(px * (0.55 if shape == 'open' else 0.4))
            yy, xx = np.ogrid[:n, :n]
            disc_mask = (yy - row) ** 2 + (xx - col) ** 2 <= rad * rad
            if shape != 'open':
                disc_mask = disc_mask & (np.abs(yy - row) <= max(1, rad // 3))
            img[disc_mask & covered] = _rgb(cr.EYE)

    # Outline round the silhouette.
    grown = covered.copy()
    for _ in range(max(2, int(px * 0.12))):
        grown = grown | np.roll(grown, 1, 0) | np.roll(grown, -1, 0) | np.roll(grown, 1, 1) | np.roll(grown, -1, 1)
    out = np.zeros((n, n, 4), dtype=np.uint8)
    out[..., :3] = np.where(covered[..., None], img, np.array(OUTLINE_RGB))
    out[..., 3] = np.where(grown, 255, 0)
    from PIL import Image
    return Image.fromarray(out, 'RGBA').resize((size, size), Image.LANCZOS)


def render_sheet(creature, pose, views=None, size=300):
    """The model of a pose from several views, side by side with their names."""
    from PIL import Image, ImageDraw
    names = views or list(VIEWS)
    cr.EYE_REACH = getattr(creature, 'eye_reach', 0.9)
    parts, decals = creature.place(pose)
    tiles = []
    for name in names:
        tiles.append(render_view(parts, decals, creature.ramps, VIEWS[name], size))
    sheet = Image.new('RGBA', (size * len(tiles), size + 18), (60, 64, 74, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (name, tile) in enumerate(zip(names, tiles)):
        sheet.alpha_composite(tile, (i * size, 18))
        draw.text((i * size + 6, 3), name, fill=(235, 238, 245, 255))
    return sheet


def pick_pose(creature, name='charging', frame=0, facing='SE'):
    frames = creature.poses.get(name + facing) or creature.poses[name]
    return frames[min(frame, len(frames) - 1)]
