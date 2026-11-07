#!/usr/bin/env python3
"""Build the assets: things that aren't characters.

Each asset is painted in the same colour roles as the characters, so it recolours
the same way. The turn crystal is rendered from a small 3D model: an elongated
octahedron, flat-shaded, turning about its vertical axis and bobbing as it goes.
Four faces repeat every quarter turn, so the frames loop with no seam.

    python3 tools/make_assets.py [--png-dir DIR] [--force]

Writes assets/data.js. With --png-dir it also writes each asset's sheet as a PNG,
and every frame is checked to re-render identically from its roles.

Only what changed is rebuilt: each family of tools/registry.py is cached in .build-cache/ (see tools/buildcache.py) and a sheet is only rewritten when its pixels
changed. --force rebuilds everything.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buildcache  # noqa: E402
import extract_poses as ep  # noqa: E402
import make_corrupted_ground  # noqa: E402
import make_overlay  # noqa: E402
import make_weapon_icons  # noqa: E402
import make_weapons  # noqa: E402
import registry  # noqa: E402


def build_assets(weapons_dir=make_weapons.DEFAULT_DIR, force=False):
    """Every asset, in the registry's order. Each family comes from the cache unless its code or inputs changed. Returns (assets, {unit name: from the cache?})."""
    assets, cached = [], {}
    for unit in registry.UNITS:
        started = time.time()
        got, hit = buildcache.build(unit, weapons_dir, force)
        assets += got
        cached[unit.name] = hit
        print(f'{unit.name:13s} {"cached" if hit else f"built in {time.time() - started:.1f}s"}  ({len(got)} assets)')
    tag_overlay_shapes(assets)
    # Each weapon's display icon, linked both ways by the weapon's name (see make_weapon_icons.py): it fails the build if they do not match.
    problems = make_weapon_icons.link_icons(assets)
    if problems:
        sys.exit('weapon display icons:\n  ' + '\n  '.join(problems))
    return assets, cached


def tag_overlay_shapes(assets):
    """Say which overlay shape fits each ground tile, as an `overlay` index into the shaped overlays' variants.

    The shapes: 0 is a flat top on a full block, 1 a flat top 8 rows lower, and 2 onward the angled ones (the grass tile each was
    read from names it in tools/data/overlay_shapes.json). A tile with the same silhouette as an angled shape's grass tile uses
    that shape; any other tile uses one of the flat ones if its whole flat top fits inside it. A tile that fits none (stairs) has no
    `overlay` yet.
    """
    import json
    entries = json.loads(make_overlay.SHAPES_PATH.read_text())
    by_id = {a['id']: a for a in assets}
    silhouette = lambda a: tuple(''.join('#' if ch != '.' else '.' for ch in row) for row in a['frames'][0])
    angled = [silhouette(by_id[e['tile']]) for e in entries]
    flat = [[row for row in m] for m in (make_overlay.diamond_mask(0), make_overlay.diamond_mask(8))]
    for a in assets:
        if not a['id'].startswith('ground-') or a['category'] not in ('Grass', 'Dirt', 'Stone', 'Water', 'Crates', 'Stairs'):
            continue
        sil = silhouette(a)
        shape = next((2 + k for k, other in enumerate(angled) if other == sil), None)
        if shape is None:
            top = next(y for y, row in enumerate(sil) if '#' in row)
            for k, mask in enumerate(flat):
                if top == 8 * k and all(sil[y][x] == '#' for y in range(32) for x in range(32) if mask[y][x]):
                    shape = k
                    break
        if shape is None and a['category'] == 'Stairs':
            # Stairs climb like a ramp: the biggest angled shape that lies wholly inside the tile fits the flight of steps.
            masks = [[[ch == '#' for ch in row] for row in e['rows']] for e in entries]
            fits = [(sum(map(sum, m)), 2 + k) for k, m in enumerate(masks) if all(sil[y][x] == '#' for y in range(32) for x in range(32) if m[y][x])]
            shape = max(fits)[1] if fits else None
        if shape is not None:
            a['overlay'] = shape
    for a in assets:        # a corrupted tile has the original's shape, so the same overlay fits it
        if not a['id'].startswith('ground-corrupted-'):
            continue
        cell = a['id'][len('ground-corrupted-'):]
        if tuple(int(v) for v in cell.split('-')) in make_corrupted_ground.CLEAN_GRASS:      # a plain block is the (0, 0) block's shape
            cell = '%d-%d' % make_corrupted_ground.CLEAN_SOURCE
        if 'overlay' in by_id.get('ground-' + cell, {}):
            a['overlay'] = by_id['ground-' + cell]['overlay']


# The shape of assets/data.js, for the game that reads it: bump this when a key is renamed or the layout changes (not when assets are added).

# The shape of assets/data.js, for the game that reads it: bump this when a key is renamed or the layout changes (not when assets are added).
DATA_FORMAT = 1


def sheet_hash(asset, rgb):
    """What a sheet's pixels are, as a hash: its frames, layout and opacity, and the colours the roles mean."""
    body = json.dumps([asset['w'], asset['h'], asset['cols'], asset['rows'], asset.get('opacity', 1), asset['frames']], separators=(',', ':'))
    return hashlib.sha256((body + json.dumps(rgb, sort_keys=True)).encode()).hexdigest()


def write_sheets(assets, png_dir, force=False):
    """Write each asset's sheet as a PNG and check it re-reads identically; a sheet whose pixels have not changed is left alone. Returns the manifest entries."""
    from PIL import Image
    to_rgb = {c: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for c, _, _, _, h in ep.ROLES}
    hashes_path = buildcache.CACHE / 'sheets.json'
    known = json.loads(hashes_path.read_text()) if hashes_path.exists() and not force else {}
    png_dir.mkdir(parents=True, exist_ok=True)
    # The ground tiles are cut from sprites/assets/ground.png and the weapons are strips in sprites/weapons, so they are not written again.
    written = [a for a in assets if not a['id'].startswith(('ground-', 'weapon-'))]
    manifest, rewritten = [], 0
    for asset in written:
        # An asset that belongs to a group (the node map) goes in that group's own folder inside the PNG folder.
        path = png_dir / asset.get('folder', '') / f'{asset["id"]}.png'
        digest = sheet_hash(asset, to_rgb)
        if not (path.exists() and known.get(str(path)) == digest):
            rewritten += 1
            # A see-through asset (a tile overlay) is written with its opacity in the alpha channel, ready to lay over a tile.
            alpha = round(255 * asset.get('opacity', 1))
            sheet = Image.new('RGBA', (asset['w'] * asset['cols'], asset['h'] * asset['rows']), (0, 0, 0, 0))
            px = sheet.load()
            origin = lambda f: ((f % asset['cols']) * asset['w'], (f // asset['cols']) * asset['h'])
            for f, rows in enumerate(asset['frames']):
                ox, oy = origin(f)
                for y, row in enumerate(rows):
                    for x, ch in enumerate(row):
                        if ch != '.':
                            px[ox + x, oy + y] = (*to_rgb[ch], alpha)
            path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(path)
            # Re-read the PNG and compare every pixel with what the roles say it should be.
            back = Image.open(path).convert('RGBA').load()
            for f, rows in enumerate(asset['frames']):
                ox, oy = origin(f)
                for y, row in enumerate(rows):
                    for x, ch in enumerate(row):
                        want = (0, 0, 0, 0) if ch == '.' else (*to_rgb[ch], alpha)
                        if back[ox + x, oy + y] != want:
                            sys.exit(f'{path}: round trip differs at frame {f} ({x}, {y})')
            print(f'{asset["id"]}: {len(asset["frames"])} frames written and re-read identical -> {path}')
        known[str(path)] = digest
        manifest.append({k: asset[k] for k in ('id', 'label', 'category', 'kind', 'place', 'w', 'h', 'cols', 'rows', 'fps', 'anchor') if k in asset}
                        | {'file': str(path.relative_to(png_dir)), 'frames': len(asset['frames'])}
                        | ({'names': asset['names']} if 'names' in asset else {}) | ({'opacity': asset['opacity']} if 'opacity' in asset else {}))
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    hashes_path.write_text(json.dumps(known, indent=0))
    print(f'{rewritten} sheet(s) written, {len(written) - rewritten} unchanged')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--png-dir', type=Path, help='also write each asset as a PNG sheet here, and check it')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'assets' / 'data.js')
    parser.add_argument('--weapons', type=Path, default=make_weapons.DEFAULT_DIR, help='folder of NAME-attackNE.png / NAME-attackSE.png weapon strips')
    parser.add_argument('--force', action='store_true', help='ignore the cache and rebuild everything')
    args = parser.parse_args()

    assets, cached = build_assets(args.weapons, args.force)
    data = {
        'format': DATA_FORMAT,
        'groups': [{'id': i, 'label': l, 'hue': i not in ('outline', 'neutral')} for i, l in ep.GROUPS],
        'roles': [{'char': c, 'id': i, 'label': l, 'group': g, 'hex': '#' + h} for c, i, l, g, h in ep.ROLES],
        # The order the browse view lists them in: by first appearance.
        'categories': list(dict.fromkeys(a['category'] for a in assets)),
        'assets': assets,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('window.ASSETS = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(f'wrote {len(assets)} asset(s) -> {args.out}')

    if args.png_dir:
        manifest = write_sheets(assets, args.png_dir, args.force)
        # Which overlay shape fits each ground tile, by the tile's place on ground.png, and where the shapes are in the overlay sheets.
        ground_overlays = {a['id'][len('ground-'):]: a['overlay'] for a in assets if a['id'].startswith('ground-') and 'overlay' in a}
        (args.png_dir / 'manifest.json').write_text(json.dumps({
            'about': 'Every asset sheet in this folder: frames run left to right, then down, in w x h cells (cols x rows). anchor is the point '
                     'that sits on the ground tile or the character; opacity (if any) is already in the PNG\'s alpha. groundOverlays says which frame '
                     'of the "-shapes" overlay sheets fits each ground tile of ground.png, by its column-row.',
            'assets': manifest,
            'groundOverlays': ground_overlays,
        }, indent=1))
        # A family that ships a folder writes its package (the JSON beside the sheets, and any examples) when it was rebuilt or the folder is missing.
        import importlib
        for unit in registry.UNITS:
            module = importlib.import_module(unit.module)
            if hasattr(module, 'write_package'):
                folder = args.png_dir / module.FOLDER
                if not cached[unit.name] or not folder.exists():
                    module.write_package(folder)
        print(f'{len(manifest)} sheets and manifest.json -> {args.png_dir}')


if __name__ == '__main__':
    main()
