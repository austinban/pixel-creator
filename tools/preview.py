"""One preview for any family: a labelled contact sheet of the sheets you name, every frame, standing on a ground tile at its anchor,
at game scale and at 2x side by side. What a preview for approval looks like, the same for every family, from the files the game takes.

    python3 tools/preview.py trap-snare trap-snare-triggered          # by asset id (see sprites/assets/manifest.json)
    python3 tools/preview.py --grep item-                              # every asset whose id has this in it
    python3 tools/preview.py --grep sweep --out previews/sweeps.png --scale 3

Writes previews/<name>.png (previews/ is not committed) and prints the path. An asset placed on the ground or above it is drawn over
a tile with its anchor on the tile's middle; an icon (place "none") on a plain panel.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'sprites' / 'assets'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_poses as ep  # noqa: E402

BACKDROP = (34, 30, 52, 255)
PANEL = (52, 46, 78, 255)
LABEL = (230, 222, 200, 255)
DIM = (150, 140, 170, 255)
PAD = 6


def _hex(char):
    h = next(h for c, *_, h in ep.ROLES if c == char)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def tile(width=32):
    """A grass tile's top, in the ground's projection (twice as wide as deep), in the palette's greens with an outline."""
    depth = width // 2
    image = Image.new('RGBA', (width, depth + 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    diamond = [(width // 2, 0), (width - 1, depth // 2), (width // 2, depth), (0, depth // 2)]
    draw.polygon(diamond, fill=_hex('A'), outline=_hex('B'))
    return image


def load_manifest():
    return json.loads((ASSETS / 'manifest.json').read_text())['assets']


def frames_of(asset):
    sheet = Image.open(ASSETS / asset['file']).convert('RGBA')
    out = []
    for index in range(asset['frames']):
        x = (index % asset['cols']) * asset['w']
        y = (index // asset['cols']) * asset['h']
        out.append(sheet.crop((x, y, x + asset['w'], y + asset['h'])))
    return out


def cell_image(asset, frame):
    """One frame as the game would show it: on a tile with the anchor on the tile's middle, or on a panel for an icon."""
    w, h = asset['w'], asset['h']
    image = Image.new('RGBA', (w + 2 * PAD, h + 2 * PAD), PANEL if asset['place'] == 'none' else BACKDROP)
    if asset['place'] != 'none':
        ground = tile()
        ax, ay = asset['anchor']['x'] + PAD, asset['anchor']['y'] + PAD
        image.alpha_composite(ground, (ax - ground.width // 2, ay - ground.height // 2))
    image.alpha_composite(frame, (PAD, PAD))
    return image


def render(assets, scale):
    rows = []
    for asset in assets:
        cells = [cell_image(asset, f) for f in frames_of(asset)]
        small = Image.new('RGBA', (sum(c.width for c in cells), cells[0].height), BACKDROP)
        x = 0
        for c in cells:
            small.alpha_composite(c, (x, 0))
            x += c.width
        big = small.resize((small.width * scale, small.height * scale), Image.NEAREST)
        label_h = 16
        meta = f"{asset['id']}  {asset['w']}x{asset['h']}  {asset['frames']} frame(s)" + (f"  {asset['fps']} fps" if asset['fps'] else '') \
            + f"  anchor {asset['anchor']['x']},{asset['anchor']['y']}  {asset['place']}"
        text_w = int(ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(meta)) + 2 * PAD
        row = Image.new('RGBA', (max(small.width + big.width + 3 * PAD, text_w), big.height + label_h + PAD), BACKDROP)
        draw = ImageDraw.Draw(row)
        draw.text((PAD, 2), meta, fill=LABEL)
        row.alpha_composite(small, (PAD, label_h))
        row.alpha_composite(big, (small.width + 2 * PAD, label_h))
        draw.text((PAD, label_h + small.height + 1), '1x', fill=DIM)
        draw.text((small.width + 2 * PAD, label_h + big.height - 11), f'{scale}x', fill=DIM)
        rows.append(row)
    width = max(r.width for r in rows)
    out = Image.new('RGBA', (width, sum(r.height for r in rows)), BACKDROP)
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('ids', nargs='*', help='asset ids to show')
    parser.add_argument('--grep', help='also every asset whose id contains this')
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    manifest = load_manifest()
    by_id = {a['id']: a for a in manifest}
    chosen = [by_id[i] for i in args.ids if i in by_id]
    missing = [i for i in args.ids if i not in by_id]
    if args.grep:
        chosen += [a for a in manifest if args.grep in a['id'] and a not in chosen]
    if missing:
        print(f'not in the manifest: {", ".join(missing)}', file=sys.stderr)
    if not chosen:
        print('nothing to preview', file=sys.stderr)
        return 1
    out = args.out or ROOT / 'previews' / f"{(args.grep or chosen[0]['id']).strip('-')}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    render(chosen, args.scale).save(out)
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
