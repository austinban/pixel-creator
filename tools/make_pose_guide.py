#!/usr/bin/env python3
"""A pose and colour guide for one character: every pose in both facings on one page, with the full palette under it.

    python3 tools/make_pose_guide.py sprites/human previews/human-guide.png

The sprites are read from NAME-<pose><facing>.png in the folder (frames side by side, as the game uses them) and shown at 4x. The palette is the
current ROLES; the roles this character actually uses are marked with a white corner so you can see its colours at a glance.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep

SCALE = 4
ORDER = ['walking', 'attack', 'bow', 'charging', 'release', 'damage', 'weak', 'dead']
PAGE, PANEL, INK, DIM = (22, 18, 40), (50, 44, 84), (236, 230, 244), (160, 154, 190)


def font(size):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/SFNS.ttf', '/Library/Fonts/Arial.ttf'):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('folder', type=Path)
    ap.add_argument('out', type=Path)
    a = ap.parse_args()
    name = a.folder.name
    h = lambda x: tuple(int(x[i:i + 2], 16) for i in (0, 2, 4))
    pngs = {}
    for p in sorted(a.folder.glob(f'{name}-*.png')):
        stem = p.stem[len(name) + 1:]
        pngs[(stem[:-2], stem[-2:])] = Image.open(p).convert('RGBA')
    actions = [x for x in ORDER if any(k[0] == x for k in pngs)] + sorted({k[0] for k in pngs} - set(ORDER))
    used = set()
    for im in pngs.values():
        for r, g, b, al in im.getdata():
            if al:
                used.add(ep.COLOUR_TO_ROLE.get((r, g, b)))

    pad, gap, label = 24, 16, 22
    colw = max(im.width for im in pngs.values()) * SCALE
    width = pad * 2 + colw * 2 + gap
    rows = [(act, max(pngs[k].height for k in pngs if k[0] == act) * SCALE) for act in actions]
    pose_h = sum(rh + label + gap for _, rh in rows)
    cols, sw, sh = 6, (width - pad * 2 - 10 * 5) // 6, 58
    pal_rows = -(-len(ep.ROLES) // cols)
    height = pad + 40 + pose_h + 36 + pal_rows * (sh + 10) + pad
    page = Image.new('RGB', (width, height), PAGE)
    d = ImageDraw.Draw(page)
    d.text((pad, pad - 4), f'{name.capitalize()}: poses and colours', font=font(26), fill=INK)
    y = pad + 40
    for act, rh in rows:
        d.text((pad, y), act, font=font(15), fill=DIM)
        y += label
        for n, facing in enumerate(('NE', 'SE')):
            x = pad + n * (colw + gap)
            im = pngs.get((act, facing))
            d.rectangle([x, y, x + colw - 1, y + rh - 1], fill=PANEL)
            if im:
                big = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
                page.paste(big, (x, y), big)
            d.text((x + 6, y + rh - 18), facing, font=font(12), fill=DIM)
        y += rh + gap
    d.text((pad, y), f'Palette ({len(ep.ROLES)} roles; a white corner marks the ones {name} uses)', font=font(15), fill=DIM)
    y += 26
    for n, (c, rid, lab, grp, hx) in enumerate(ep.ROLES):
        x, yy = pad + (n % cols) * (sw + 10), y + (n // cols) * (sh + 10)
        d.rectangle([x, yy, x + sw - 1, yy + sh - 1], fill=h(hx), outline=(90, 84, 130))
        lum = 0.299 * h(hx)[0] + 0.587 * h(hx)[1] + 0.114 * h(hx)[2]
        ink = (20, 16, 36) if lum > 140 else (240, 236, 246)
        d.text((x + 6, yy + 5), f'{c}  {lab}', font=font(12), fill=ink)
        d.text((x + 6, yy + sh - 19), '#' + hx, font=font(12), fill=ink)
        if c in used:
            d.polygon([(x + sw - 14, yy), (x + sw - 1, yy), (x + sw - 1, yy + 13)], fill=(255, 255, 255))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    page.save(a.out)
    print(f'{len(pngs)} sprite sheets, {len(used - {None})} of {len(ep.ROLES)} roles used -> {a.out} ({width} x {height})')


if __name__ == '__main__':
    main()
