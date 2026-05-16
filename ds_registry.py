"""ds_registry.py — Dark-Swan identity registry with GDk9 indexing.

Stores verified identity records keyed by symbolic_id.  Each record contains
the public key so commits can be independently verified, and records are
indexed by digital root and symmetry class for GDk9-aware search.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from ds_gdk9 import pubkey_to_symbolic_id, symbolic_id_profile
from ds_protocol_core import _verify_with_pubkey

import base64


class DSRegistry:
    """Persistent registry of dark-swan identities.

    Storage format (registry.json):
    {
      "<symbolic_id>": {
        "symbolic_id":  "FWEM",
        "pubkey_b64":   "<base64url 44-char>",
        "handle":       "ds-XYZW",
        "committed_at": <unix_ts>,
        "profile": { "digital_root": 7, "dominant_class": "asymmetric", ... }
      },
      ...
    }
    """

    def __init__(self, db_path: str = 'registry.json') -> None:
        self.path = Path(db_path)
        self._db: Dict[str, dict] = {}
        if self.path.exists():
            self._db = json.loads(self.path.read_text())

    # ── Write ─────────────────────────────────────────────────────────────────

    def commit(
        self,
        pubkey_b64: str,
        handle: str,
        *,
        overwrite: bool = False,
    ) -> dict:
        """Register a new identity by its public key.

        The symbolic_id is derived from *pubkey_b64* — the caller does not
        supply it directly, which prevents squatting.

        Raises ``ValueError`` if the symbolic_id already exists and
        *overwrite* is False.
        """
        raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
        sid = pubkey_to_symbolic_id(raw)

        if sid in self._db and not overwrite:
            raise ValueError(f'symbolic_id {sid!r} already registered')

        profile = symbolic_id_profile(sid)
        record = {
            'symbolic_id':  sid,
            'pubkey_b64':   pubkey_b64,
            'handle':       handle,
            'committed_at': int(time.time()),
            'profile': {
                'digital_root':   profile['digital_root'],
                'dominant_class': profile['dominant_class'],
                'total_energy':   profile['total_energy'],
                'class_counts':   profile['class_counts'],
            },
        }
        self._db[sid] = record
        self._save()
        return record

    def update_handle(self, symbolic_id: str, new_handle: str) -> None:
        """Update the handle for an existing record (e.g. daily rotation)."""
        if symbolic_id not in self._db:
            raise KeyError(f'symbolic_id {symbolic_id!r} not found')
        self._db[symbolic_id]['handle'] = new_handle
        self._save()

    def remove(self, symbolic_id: str) -> None:
        self._db.pop(symbolic_id, None)
        self._save()

    # ── Read ──────────────────────────────────────────────────────────────────

    def resolve(self, symbolic_id: str) -> Optional[dict]:
        """Look up a record by symbolic_id.  Returns None if not found."""
        return self._db.get(symbolic_id)

    def resolve_by_handle(self, handle: str) -> Optional[dict]:
        """Look up by ephemeral handle (linear scan)."""
        for rec in self._db.values():
            if rec.get('handle') == handle:
                return rec
        return None

    # ── Search ────────────────────────────────────────────────────────────────

    def search_by_dr(self, dr: int) -> List[dict]:
        """Return all records whose symbolic_id has digital root *dr* (1-9)."""
        return [r for r in self._db.values()
                if r['profile']['digital_root'] == dr]

    def search_by_class(self, sym_class: str) -> List[dict]:
        """Return all records whose dominant symmetry class matches *sym_class*.

        *sym_class* is one of: ``idempotent``, ``biphasic``, ``involutive``,
        ``asymmetric``.
        """
        return [r for r in self._db.values()
                if r['profile']['dominant_class'] == sym_class]

    def search_by_energy_range(self, low: float, high: float) -> List[dict]:
        """Return records whose total_energy falls within [low, high]."""
        return [r for r in self._db.values()
                if low <= r['profile']['total_energy'] <= high]

    def all_records(self) -> List[dict]:
        return list(self._db.values())

    def count(self) -> int:
        return len(self._db)

    # ── Verification ─────────────────────────────────────────────────────────

    def verify_record(self, symbolic_id: str, msg: str, signature: str) -> bool:
        """Verify *signature* on *msg* against the stored public key."""
        rec = self._db.get(symbolic_id)
        if not rec:
            return False
        raw = base64.urlsafe_b64decode(rec['pubkey_b64'] + '==')
        return _verify_with_pubkey(raw, msg, signature)

    def verify_pubkey_matches(self, symbolic_id: str, pubkey_b64: str) -> bool:
        """Confirm that *pubkey_b64* hashes to *symbolic_id*."""
        from ds_gdk9 import pubkey_to_symbolic_id as _p2s
        import base64
        raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
        return _p2s(raw) == symbolic_id

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._db, indent=2, ensure_ascii=False))
