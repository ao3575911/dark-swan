"""ds_registry.py — Dark-Swan identity registry with GDk9 indexing.

Stores verified identity records keyed by canonical DID. Each record also
contains the 4-letter symbolic_id as a human-readable label. The public key is
stored so commits can be independently verified, and records are indexed by
digital root and symmetry class for GDk9-aware search.
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from ds_gdk9 import pubkey_to_symbolic_id, symbolic_id_profile
from ds_protocol_core import _verify_with_pubkey, pubkey_to_did


class DSRegistry:
    """Persistent registry of dark-swan identities.

    Storage format (registry.json):
    {
      "did:ds:<fingerprint>": {
        "did":          "did:ds:<fingerprint>",
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
            text = self.path.read_text().strip()
            if text:
                try:
                    self._db = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f'Registry file {str(self.path)!r} contains invalid JSON: {exc}'
                    ) from exc

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
        did = pubkey_to_did(pubkey_b64)

        existing_key, existing_rec = self._find_key_record(did)
        if existing_rec is None:
            existing_key, existing_rec = self._find_key_record(sid)
        if existing_rec is not None and not overwrite:
            raise ValueError(f'identity {did!r} / {sid!r} already registered')

        profile = symbolic_id_profile(sid)
        record = {
            'did': did,
            'symbolic_id': sid,
            'pubkey_b64': pubkey_b64,
            'handle': handle,
            'committed_at': int(time.time()),
            'profile': {
                'digital_root': profile['digital_root'],
                'dominant_class': profile['dominant_class'],
                'total_energy': profile['total_energy'],
                'class_counts': profile['class_counts'],
            },
        }
        if existing_key and existing_key != did:
            self._db.pop(existing_key, None)
        self._db[did] = record
        self._save()
        return record

    def update_handle(self, identity_ref: str, new_handle: str) -> None:
        """Update the handle for an existing record by DID or symbolic ID."""
        key, rec = self._find_key_record(identity_ref)
        if rec is None or key is None:
            raise KeyError(f'identity {identity_ref!r} not found')
        self._db[key]['handle'] = new_handle
        self._save()

    def remove(self, identity_ref: str) -> None:
        key, _ = self._find_key_record(identity_ref)
        if key is not None:
            self._db.pop(key, None)
        self._save()

    # ── Read ──────────────────────────────────────────────────────────────────

    def resolve(self, identity_ref: str) -> Optional[dict]:
        """Look up a record by DID or symbolic_id. Returns None if not found."""
        _, rec = self._find_key_record(identity_ref)
        return rec

    def resolve_by_did(self, did: str) -> Optional[dict]:
        """Look up a record by canonical DID."""
        return self.resolve(did)

    def resolve_by_handle(self, handle: str) -> Optional[dict]:
        """Look up by ephemeral handle (linear scan)."""
        for rec in self._db.values():
            if rec.get('handle') == handle:
                return rec
        return None

    # ── Search ────────────────────────────────────────────────────────────────

    def search_by_dr(self, dr: int) -> List[dict]:
        """Return all records whose symbolic_id has digital root *dr* (1-9)."""
        return [r for r in self._db.values() if r['profile']['digital_root'] == dr]

    def search_by_class(self, sym_class: str) -> List[dict]:
        """Return all records whose dominant symmetry class matches *sym_class*.

        *sym_class* is one of: ``idempotent``, ``biphasic``, ``involutive``,
        ``asymmetric``.
        """
        return [r for r in self._db.values() if r['profile']['dominant_class'] == sym_class]

    def search_by_energy_range(self, low: float, high: float) -> List[dict]:
        """Return records whose total_energy falls within [low, high]."""
        return [r for r in self._db.values() if low <= r['profile']['total_energy'] <= high]

    def all_records(self) -> List[dict]:
        return list(self._db.values())

    def count(self) -> int:
        return len(self._db)

    # ── Verification ─────────────────────────────────────────────────────────

    def verify_record(self, symbolic_id: str, msg: str, signature: str) -> bool:
        """Verify *signature* on *msg* against the stored public key."""
        rec = self.resolve(symbolic_id)
        if not rec:
            return False
        raw = base64.urlsafe_b64decode(rec['pubkey_b64'] + '==')
        return _verify_with_pubkey(raw, msg, signature)

    def verify_pubkey_matches(self, identity_ref: str, pubkey_b64: str) -> bool:
        """Confirm that *pubkey_b64* hashes to the supplied DID or symbolic ID."""
        import base64

        from ds_gdk9 import pubkey_to_symbolic_id as _p2s

        raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
        return identity_ref in {_p2s(raw), pubkey_to_did(pubkey_b64)}

    def _find_key_record(self, identity_ref: str) -> tuple[Optional[str], Optional[dict]]:
        """Return (storage_key, record) for DID or symbolic ID references."""
        if identity_ref in self._db:
            return identity_ref, self._db[identity_ref]
        for key, rec in self._db.items():
            if rec.get('did') == identity_ref or rec.get('symbolic_id') == identity_ref:
                return key, rec
        return None, None

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._db, indent=2, ensure_ascii=False))
