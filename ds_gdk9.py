"""ds_gdk9.py — GDk9 symbolic bridge for dark-swan identities.

Maps identity material (public key bytes) to GDk9 symbolic space:
  - symbolic_id : 4-letter uppercase word derived from SHA-256(pubkey)
  - digital_root: DR 1-9 of the A1Z26 letter sum
  - energy      : SymPhi rest-energy of the symbolic word
  - sym_class   : dominant symmetry class of the word

No gdk9 package dependency required — all relevant math is inlined here so
dark-swan works standalone.  If gdk9 is importable, richer DCG analysis is
available via `dcg_profile()`.
"""

from __future__ import annotations

import hashlib
import math
from typing import Dict, Optional

# ── Symmetry tables (mirrors gdk9/dcg.py) ────────────────────────────────────

_IDEMP = frozenset('AHIMOTUVWXY')
_BIPH = frozenset('BCDEK')
_INVOL = frozenset('NSZ')
_ASYM = frozenset('FGJLPQR')

_CLASS_ORDER = ('asymmetric', 'biphasic', 'idempotent', 'involutive')


def _sym_class(ch: str) -> Optional[str]:
    u = ch.upper()
    if u in _IDEMP:
        return 'idempotent'
    if u in _BIPH:
        return 'biphasic'
    if u in _INVOL:
        return 'involutive'
    if u in _ASYM:
        return 'asymmetric'
    return None


def _sym_energy(ch: str) -> float:
    u = ch.upper()
    if not u.isalpha():
        return 0.0
    pos = ord(u) - ord('A') + 1
    if u in _IDEMP:
        return float(pos)
    if u in _BIPH:
        return math.sin(pos)
    if u in _INVOL:
        return 1.0 / pos
    if u in _ASYM:
        return float(pos + 1)
    return 0.0


def _digital_root(n: int) -> int:
    if n <= 0:
        return 9
    r = n % 9
    return r if r != 0 else 9


# ── Core derivation ───────────────────────────────────────────────────────────


def bytes_to_word(data: bytes, length: int = 4) -> str:
    """Map *length* bytes of *data* to uppercase letters A-Z."""
    return ''.join(chr(ord('A') + b % 26) for b in data[:length])


def pubkey_to_symbolic_id(pubkey_raw: bytes) -> str:
    """Derive a 4-letter GDk9 symbolic ID from a raw Ed25519 public key.

    Derivation: SHA-256(pubkey_raw) → first 4 bytes → A-Z letters.
    Anyone with the public key can independently verify the symbolic_id.
    """
    h = hashlib.sha256(pubkey_raw).digest()
    return bytes_to_word(h, 4)


def symbolic_id_profile(word: str) -> Dict:
    """Return full GDk9 profile for a symbolic ID word."""
    letters = [ch for ch in word.upper() if ch.isalpha()]
    total_energy = sum(_sym_energy(ch) for ch in letters)
    a1z26_sum = sum(ord(ch) - ord('A') + 1 for ch in letters)
    dr = _digital_root(a1z26_sum)

    class_counts: Dict[str, int] = {}
    for ch in letters:
        c = _sym_class(ch)
        if c:
            class_counts[c] = class_counts.get(c, 0) + 1

    dominant_class = max(class_counts, key=class_counts.get) if class_counts else 'mixed'

    steps = []
    for ch in letters:
        steps.append(
            {
                'char': ch,
                'class': _sym_class(ch),
                'energy': _sym_energy(ch),
                'pos': ord(ch) - ord('A') + 1,
            }
        )

    return {
        'word': word.upper(),
        'total_energy': total_energy,
        'digital_root': dr,
        'dominant_class': dominant_class,
        'class_counts': class_counts,
        'steps': steps,
    }


# ── Optional rich analysis via gdk9 package ──────────────────────────────────


def dcg_profile(word: str) -> Optional[Dict]:
    """Return DCG word_path_info for *word* if gdk9 is installed, else None."""
    try:
        from gdk9.dcg import get_dcg

        g = get_dcg()
        info = g.word_path_info(word)
        return info
    except ImportError:
        return None


def homotopy_check(word_a: str, word_b: str, tol: float = 1.0) -> Optional[Dict]:
    """Check homotopy equivalence via gdk9 if available."""
    try:
        from gdk9.dcg import homotopy_equivalent

        equiv, detail = homotopy_equivalent(word_a, word_b, tol=tol)
        return detail
    except ImportError:
        return None


# ── Handle derivation ─────────────────────────────────────────────────────────


def derive_handle(symbolic_id: str, epoch_day: int) -> str:
    """Derive a daily-rotating ephemeral handle from symbolic_id + epoch_day.

    Format: ``ds-XXXX`` where XXXX is a 4-letter GDk9 word derived from
    SHA3-256(symbolic_id + epoch_day).  The handle rotates each UTC day.
    """
    material = (symbolic_id + str(epoch_day)).encode()
    h = hashlib.sha3_256(material).digest()
    return 'ds-' + bytes_to_word(h, 4)
