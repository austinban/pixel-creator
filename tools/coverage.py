"""What the game has that has no art here, and what art here the game does not use: both ways, against the game's own list.

The game writes its ids (abilities, statuses, items, traps, classes, the places an effect can go) to tools/game_ids.json in its repo
(`godot --headless --path . --script res://tools/export_ids.gd` there), and its plans for which ability plays which sheet to
assets/data/ability_fx.json. This reads both from GAME_DIR (default ~/GodotProjects/iso-fft-like).

    python3 tools/coverage.py            # the report
    GAME_DIR=/path/to/game python3 tools/coverage.py

tools/test_handoff.py fails on the hard breaks (a trap the game lays with no picture, a place an effect is put that the game does not
know); the rest is a report of what is still to draw.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'sprites' / 'assets'


def game_dir():
    return Path(os.path.expanduser(os.environ.get('GAME_DIR', '~/GodotProjects/iso-fft-like')))


def load_game():
    """(ids, plans) from the game, or (None, None) when it is not there."""
    ids_path = game_dir() / 'tools' / 'game_ids.json'
    plans_path = game_dir() / 'assets' / 'data' / 'ability_fx.json'
    if not ids_path.is_file():
        return None, None
    plans = json.loads(plans_path.read_text()) if plans_path.is_file() else {}
    return json.loads(ids_path.read_text()), plans


def our_sheets():
    path = ASSETS / 'abilities' / 'abilities.json'
    return json.loads(path.read_text()).get('sheets', {}) if path.is_file() else {}


def report(ids, plans):
    """{heading: [lines]} for everything that does not match."""
    sheets = our_sheets()
    out = {}
    out['abilities with no animation'] = sorted(
        id for id, a in ids['abilities'].items() if not a['animated'] and not a['passive'] and not a['item'] and not a.get('blow'))
    out['statuses with no picture'] = sorted(id for id, s in ids['statuses'].items() if not s['picture'])
    out['items with no icon of their own'] = sorted(id for id, i in ids['items'].items() if not i['own_icon'])
    out['traps the game lays with no picture'] = sorted(t for t in ids['traps'] if not (ASSETS / 'traps' / f'trap-{t}.png').is_file())
    used = set()
    for effects in plans.get('abilities', {}).values():
        for e in effects:
            # One drawn for two screen directions is two sheets, -ne and -se.
            used.update({e['sheet'] + '-ne', e['sheet'] + '-se'} if e['at'] == 'caster-facing' else {e['sheet']})
    for status in plans.get('statuses', {}).values():
        used.add(status['sheet'])
    out['sheets here the game plays nowhere'] = sorted(s for s in sheets if s not in used)
    out['plans naming a sheet that is not here'] = sorted(s for s in used if s not in sheets and s not in ('vine', 'vine-grey'))
    known = set(ids.get('placements', []))
    ours = json.loads((ASSETS / 'abilities' / 'abilities.json').read_text()) if (ASSETS / 'abilities' / 'abilities.json').is_file() else {}
    places = {e['at'] for row in ours.get('abilities', {}).values() for e in row.get('effects', [])}
    places |= {row['at'] for row in ours.get('statuses', {}).values()}
    out['places used here the game does not know'] = sorted(p for p in places if p not in known)
    return out


def main():
    ids, plans = load_game()
    if ids is None:
        print(f'No tools/game_ids.json in {game_dir()}: set GAME_DIR, or run tools/export_ids.gd in the game.')
        return 1
    for heading, lines in report(ids, plans).items():
        print(f'{heading} ({len(lines)}):')
        for line in lines:
            print(f'  {line}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
