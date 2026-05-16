#!/usr/bin/env python3
"""ds_cli.py — Dark-Swan command-line interface.

Usage: ds [--registry FILE] [--json] [--no-color] <command> [args]

Commands
--------
  generate  — create a new identity from a seed passphrase
  sign      — sign a message with your identity
  verify    — verify a signature given a public key
  publish   — register identity in the local registry
  lookup    — resolve symbolic_id or handle in the registry
  search    — search registry by DR, class, or energy range
  profile   — display GDk9 symbolic profile of a word or identity
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import List, Optional, Sequence

from ds_gdk9 import symbolic_id_profile, derive_handle
from ds_protocol_core import DSIdentity, verify_message, pubkey_to_id
from ds_registry import DSRegistry


# ── ANSI engine ───────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

_CODES: dict[str, str] = {
    'bold':          '\033[1m',
    'dim':           '\033[2m',
    'reset':         '\033[0m',
    'red':           '\033[31m',
    'green':         '\033[32m',
    'yellow':        '\033[33m',
    'blue':          '\033[34m',
    'magenta':       '\033[35m',
    'cyan':          '\033[36m',
    'white':         '\033[37m',
    'bright_red':    '\033[91m',
    'bright_green':  '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue':   '\033[94m',
    'bright_white':  '\033[97m',
}

_DR_COL   = {1:'blue', 2:'blue', 3:'cyan', 4:'green', 5:'yellow',
             6:'magenta', 7:'red', 8:'bright_red', 9:'bright_white'}
_CLS_COL  = {'idempotent':'cyan', 'biphasic':'yellow',
             'involutive':'magenta', 'asymmetric':'red'}
_CLS_ABBR = {'idempotent':'ide', 'biphasic':'bip',
             'involutive':'inv', 'asymmetric':'asy'}


def _use_color() -> bool:
    return sys.stdout.isatty() and os.getenv('NO_COLOR') != '1'


def _c(text: str, color: Optional[str], en: bool = True) -> str:
    if not en or not color or color not in _CODES:
        return text
    return _CODES[color] + text + _CODES['reset']


def _strip(s: str) -> str:
    return _ANSI_RE.sub('', s)


def _vlen(s: str) -> int:
    return len(_strip(s))


def _vpad(s: str, width: int, align: str = 'l') -> str:
    diff = max(0, width - _vlen(s))
    if align == 'r':
        return ' ' * diff + s
    if align == 'c':
        lp = diff // 2
        return ' ' * lp + s + ' ' * (diff - lp)
    return s + ' ' * diff


# ── Box renderer ──────────────────────────────────────────────────────────────

class Box:
    """Unicode-bordered table with ANSI-aware column widths."""

    _TL='┌'; _TR='┐'; _BL='└'; _BR='┘'
    _TJ='┬'; _BJ='┴'; _LJ='├'; _RJ='┤'; _X='┼'
    _H='─';  _V='│'

    def __init__(self, headers: Sequence[str], *,
                 col_align: Optional[Sequence[str]] = None,
                 enabled: bool = True,
                 headless: bool = False) -> None:
        self._h        = list(headers)
        self._rows:    List[List[str]] = []
        self._aligns   = list(col_align or ['l'] * len(headers))
        self._divs:    set = set()
        self.enabled   = enabled
        self._headless = headless

    def row(self, cells: Sequence[str]) -> 'Box':
        self._rows.append(list(cells))
        return self

    def divider(self) -> 'Box':
        if self._rows:
            self._divs.add(len(self._rows) - 1)
        return self

    def render(self) -> str:
        en = self.enabled
        nc = len(self._h)
        widths = [_vlen(h) for h in self._h]
        for row in self._rows:
            for i in range(min(nc, len(row))):
                widths[i] = max(widths[i], _vlen(row[i]))

        def bd(s: str) -> str:
            return _c(s, 'dim', en) if en else s

        def hsep(left: str, mid: str, right: str) -> str:
            segs = (bd(self._H * (w + 2)) for w in widths)
            return bd(left) + bd(mid).join(segs) + bd(right)

        def render_row(cells: List[str]) -> str:
            parts: List[str] = []
            for i in range(nc):
                content = cells[i] if i < len(cells) else ''
                a = self._aligns[i] if i < len(self._aligns) else 'l'
                parts.append(' ' + _vpad(content, widths[i], a) + ' ')
            return bd(self._V) + bd(self._V).join(parts) + bd(self._V)

        lines: List[str] = []
        lines.append(hsep(self._TL, self._TJ, self._TR))
        if not self._headless:
            lines.append(render_row([_c(h, 'bold', en) for h in self._h]))
            lines.append(hsep(self._LJ, self._X, self._RJ))
        for i, row in enumerate(self._rows):
            lines.append(render_row(row))
            if i in self._divs and i < len(self._rows) - 1:
                lines.append(hsep(self._LJ, self._X, self._RJ))
        lines.append(hsep(self._BL, self._BJ, self._BR))
        return '\n'.join(lines)

    def __str__(self) -> str:
        return self.render()


def _section(title: str, width: int = 46, en: bool = True) -> str:
    label  = f' {title} '
    prefix = '── '
    fill   = max(0, width - len(prefix) - len(label))
    return (_c(prefix, 'dim', en) + _c(title, 'bold', en)
            + _c(' ' + '─' * fill, 'dim', en))


def _kv(key: str, val: str, en: bool = True) -> str:
    v = val if (en and _strip(val) != val) else _c(val, 'bright_white', en)
    return _c(key, 'dim', en) + '=' + v


def _die(msg: str, en: bool = True, code: int = 1) -> None:
    """Print a coloured error box to stderr and exit."""
    inner  = f'  ✗  {msg}  '        # 2 + 1 + 2 + msg + 2
    width  = len(inner)
    rule   = _c('─' * width, 'dim', en)
    print(_c('┌', 'dim', en) + rule + _c('┐', 'dim', en), file=sys.stderr)
    print(_c('│', 'dim', en)
          + '  ' + _c('✗', 'bright_red', en) + '  '
          + _c(msg, 'bright_red', en) + '  '
          + _c('│', 'dim', en), file=sys.stderr)
    print(_c('└', 'dim', en) + rule + _c('┘', 'dim', en), file=sys.stderr)
    sys.exit(code)


# ── Shared formatters ─────────────────────────────────────────────────────────

def _colored_word(word: str, steps: list, en: bool) -> str:
    """Each letter colored by its symmetry class."""
    return ' '.join(
        _c(s['char'], _CLS_COL.get(s['class'], 'white'), en)
        for s in steps
    )


def _fmt_dr(dr: int, en: bool) -> str:
    return _c(str(dr), _DR_COL.get(dr, 'white'), en)


def _fmt_energy(e: float, en: bool) -> str:
    return _c(f'{e:.4f}', 'cyan', en)


def _identity_card(sid: str, handle: str, pubkey_b64: str,
                   profile: dict, en: bool) -> str:
    """Bordered identity card used by generate and publish."""
    steps = profile['steps']
    dr    = profile['digital_root']
    ec    = profile['total_energy']
    dom   = profile['dominant_class']

    cw    = _colored_word(sid, steps, en)
    abbrs = '  '.join(
        _c(s['char'], _CLS_COL.get(s['class'], 'white'), en)
        + _c(f"[{_CLS_ABBR.get(s['class'], '?')}]", 'dim', en)
        for s in steps
    )

    box = Box(['', ''], col_align=['r', 'l'], enabled=en, headless=True)
    box.row([_c('id', 'dim', en),
             _c(sid, 'bold', en) + '  ' + cw])
    box.row([_c('handle', 'dim', en),
             _c(handle, 'cyan', en)])
    box.divider()
    box.row([_c('dr', 'dim', en),
             _fmt_dr(dr, en) + '  ' + _kv('energy', _fmt_energy(ec, en), en)])
    box.row([_c('class', 'dim', en),
             _c(dom, _CLS_COL.get(dom, 'white'), en)])
    box.divider()
    box.row([_c('letters', 'dim', en), abbrs])
    box.divider()
    box.row([_c('pubkey', 'dim', en),
             _c(pubkey_b64[:32], 'dim', en) + _c('…', 'dim', en)])
    return box.render()


def _registry_card(rec: dict, en: bool) -> str:
    """Bordered card for a registry record."""
    sid    = rec['symbolic_id']
    handle = rec['handle']
    p      = rec['profile']
    dr     = p['digital_root']
    dom    = p['dominant_class']
    ec     = p['total_energy']
    pk     = rec['pubkey_b64']

    profile = symbolic_id_profile(sid)

    box = Box(['', ''], col_align=['r', 'l'], enabled=en, headless=True)
    box.row([_c('id', 'dim', en),
             _c(sid, 'bold', en) + '  '
             + _colored_word(sid, profile['steps'], en)])
    box.row([_c('handle', 'dim', en), _c(handle, 'cyan', en)])
    box.divider()
    box.row([_c('dr', 'dim', en),
             _fmt_dr(dr, en) + '  ' + _kv('energy', _fmt_energy(ec, en), en)])
    box.row([_c('class', 'dim', en),
             _c(dom, _CLS_COL.get(dom, 'white'), en)])
    box.divider()
    box.row([_c('pubkey', 'dim', en),
             _c(pk[:32], 'dim', en) + _c('…', 'dim', en)])
    return box.render()


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_generate(args: argparse.Namespace, en: bool) -> None:
    identity = DSIdentity(args.seed)
    profile  = identity.profile()
    handle   = identity.ephemeral_handle()

    print(_section('dark-swan · generate', en=en))
    print(_identity_card(identity.symbolic_id, handle,
                         identity.public_key_b64(), profile, en))

    if args.json:
        print(json.dumps({
            'symbolic_id': identity.symbolic_id,
            'pubkey_b64':  identity.public_key_b64(),
            'handle':      handle,
            'profile':     profile,
        }, indent=2, ensure_ascii=False))


def cmd_sign(args: argparse.Namespace, en: bool) -> None:
    identity  = DSIdentity(args.seed)
    signature = identity.sign(args.message)

    print(_section('dark-swan · sign', en=en))
    box = Box(['', ''], col_align=['r', 'l'], enabled=en, headless=True)
    box.row([_c('id', 'dim', en),   _c(identity.symbolic_id, 'bold', en)])
    box.row([_c('msg', 'dim', en),  _c(args.message[:60], 'white', en)])
    box.divider()
    box.row([_c('pubkey', 'dim', en),
             _c(identity.public_key_b64()[:32], 'dim', en) + _c('…', 'dim', en)])
    box.row([_c('sig', 'dim', en),
             _c(signature[:48], 'dim', en) + _c('…', 'dim', en)])
    print(box.render())
    if args.json:
        print(json.dumps({'id': identity.symbolic_id,
                          'pubkey_b64': identity.public_key_b64(),
                          'signature': signature}, indent=2))


def cmd_verify(args: argparse.Namespace, en: bool) -> None:
    ok = verify_message(args.pubkey, args.message, args.signature)

    print(_section('dark-swan · verify', en=en))
    box = Box(['', ''], col_align=['r', 'l'], enabled=en, headless=True)
    mark = (_c('✓  valid', 'bright_green', en) if ok
            else _c('✗  invalid', 'bright_red', en))
    box.row([_c('result', 'dim', en), mark])
    if ok:
        box.divider()
        box.row([_c('id', 'dim', en),
                 _c(pubkey_to_id(args.pubkey), 'bold', en)])
        box.row([_c('msg', 'dim', en), _c(args.message[:60], 'white', en)])
    print(box.render())


def cmd_publish(args: argparse.Namespace, en: bool) -> None:
    reg      = DSRegistry(args.registry)
    identity = DSIdentity(args.seed)
    handle   = identity.ephemeral_handle()
    try:
        rec = reg.commit(identity.public_key_b64(), handle, overwrite=args.overwrite)
        print(_section('dark-swan · publish', en=en))
        print('  ' + _c('✓', 'bright_green', en) + '  '
              + _c('registered', 'dim', en))
        print(_registry_card(rec, en))
    except ValueError as e:
        _die(str(e), en)


def cmd_lookup(args: argparse.Namespace, en: bool) -> None:
    reg = DSRegistry(args.registry)
    rec = reg.resolve(args.query) or reg.resolve_by_handle(args.query)
    if not rec:
        _die(f'not found: {args.query!r}', en)
    print(_section(f'dark-swan · {args.query}', en=en))
    print(_registry_card(rec, en))


def cmd_search(args: argparse.Namespace, en: bool) -> None:
    reg = DSRegistry(args.registry)

    if args.dr is not None:
        results = reg.search_by_dr(args.dr)
        label   = f'dr={_fmt_dr(args.dr, en)}'
    elif args.sym_class:
        results = reg.search_by_class(args.sym_class)
        label   = f'class={_c(args.sym_class, _CLS_COL.get(args.sym_class, "white"), en)}'
    elif args.energy_range:
        lo, hi  = map(float, args.energy_range.split(','))
        results = reg.search_by_energy_range(lo, hi)
        label   = f'energy={_c(f"{lo}..{hi}", "cyan", en)}'
    else:
        results = reg.all_records()
        label   = _c('all', 'dim', en)

    n = len(results)
    print(_section(f'search  {label}  {_c(str(n), "bright_white", en)} result{"s" if n != 1 else ""}', en=en))
    for rec in results:
        print(_registry_card(rec, en))


def cmd_profile(args: argparse.Namespace, en: bool) -> None:
    word    = args.word.upper()
    profile = symbolic_id_profile(word)
    steps   = profile['steps']
    dr      = profile['digital_root']
    ec      = profile['total_energy']
    dom     = profile['dominant_class']

    print(_section(f'profile  {_c(word, "bold", en)}', en=en))

    box = Box(['', ''], col_align=['r', 'l'], enabled=en, headless=True)
    box.row([_c('word', 'dim', en),
             _c(word, 'bold', en) + '  ' + _colored_word(word, steps, en)])
    box.row([_c('dr', 'dim', en),
             _fmt_dr(dr, en) + '  ' + _kv('energy', _fmt_energy(ec, en), en)])
    box.row([_c('class', 'dim', en),
             _c(dom, _CLS_COL.get(dom, 'white'), en)])
    box.divider()
    for s in steps:
        cls  = s['class']
        abbr = _CLS_ABBR.get(cls, '?')
        box.row([
            _c(s['char'], _CLS_COL.get(cls, 'white'), en),
            _c(f'pos={s["pos"]:<2}', 'dim', en) + '  '
            + _kv('e', _c(f'{s["energy"]:>8.4f}', _CLS_COL.get(cls, "white"), en), en)
            + '  ' + _c(cls, _CLS_COL.get(cls, 'white'), en),
        ])
    print(box.render())

    # Optional DCG path (requires gdk9 installed)
    try:
        from ds_gdk9 import dcg_profile as _dcg
        dcg_info = _dcg(word)
        if dcg_info:
            print(_section('dcg path', en=en))
            dcg_steps = dcg_info.get('steps', [])
            chain = _c(' → ', 'dim', en).join(
                _c(s['char'], _CLS_COL.get(s['class'], 'white'), en)
                for s in dcg_steps
            )
            valid = dcg_info.get('is_valid_path', False)
            mark  = (_c('✓ valid path', 'bright_green', en) if valid
                     else _c('✗ broken path', 'bright_red', en))
            print('  ' + chain + '  ' + mark)
    except Exception:
        pass


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='ds',
        description='Dark-Swan identity CLI with GDk9 symbolic grounding',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('--registry', default='registry.json',
                   help='Path to registry JSON  (default: registry.json)')
    p.add_argument('--json',     action='store_true', help='Emit JSON alongside output')
    p.add_argument('--no-color', action='store_true', help='Disable ANSI colour')
    sub = p.add_subparsers(dest='command', required=True)

    g = sub.add_parser('generate', help='Create identity from seed')
    g.add_argument('seed', help='Secret seed passphrase')

    s = sub.add_parser('sign', help='Sign a message')
    s.add_argument('seed',    help='Secret seed passphrase')
    s.add_argument('message', help='Message to sign')

    v = sub.add_parser('verify', help='Verify a signature')
    v.add_argument('pubkey',    help='Base64url public key')
    v.add_argument('message',   help='Message that was signed')
    v.add_argument('signature', help='Base64url signature')

    pub = sub.add_parser('publish', help='Register identity in registry')
    pub.add_argument('seed', help='Secret seed passphrase')
    pub.add_argument('--overwrite', action='store_true',
                     help='Replace existing record if present')

    lk = sub.add_parser('lookup', help='Resolve symbolic_id or handle')
    lk.add_argument('query', help='symbolic_id (e.g. FWEM) or handle (ds-XYZW)')

    sr = sub.add_parser('search', help='Search registry')
    sr.add_argument('--dr',           type=int, help='Filter by digital root 1-9')
    sr.add_argument('--class',        dest='sym_class', help='Filter by symmetry class')
    sr.add_argument('--energy-range', dest='energy_range',
                    help='Energy range low,high  e.g. 10,50')

    pr = sub.add_parser('profile', help='Show GDk9 profile of a word')
    pr.add_argument('word', help='Word to profile  (e.g. FWEM)')

    return p


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    en     = _use_color() and not getattr(args, 'no_color', False)

    dispatch = {
        'generate': cmd_generate,
        'sign':     cmd_sign,
        'verify':   cmd_verify,
        'publish':  cmd_publish,
        'lookup':   cmd_lookup,
        'search':   cmd_search,
        'profile':  cmd_profile,
    }
    dispatch[args.command](args, en)


if __name__ == '__main__':
    main()
