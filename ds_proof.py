"""ds_proof.py — Dark-Swan Proof Cards.

A proof card is a signed, portable identity proof object that lets an identity
holder demonstrate control of a dark-swan identity without revealing their seed.

Wire format::

    {
      "type":       "dark-swan-proof",
      "did":        "did:ds:<fingerprint>",
      "symbol":     "UYRJ",
      "handle":     "ds-DENA",
      "claim":      "I control this identity",
      "context":    "github.com/ao3575911/dark-swan",
      "issued_at":  "2026-05-16T00:00:00Z",
      "expires_at": "2026-05-17T00:00:00Z",
      "pubkey":     "<base64url 44-char>",
      "signature":  "<base64url Ed25519 sig over canonical payload>"
    }

The signature covers the canonical JSON of all fields except ``signature``
itself, serialised with sorted keys and no extra whitespace.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Tuple

from ds_protocol_core import DSIdentity, pubkey_to_did, pubkey_to_id, verify_message

_TYPE = 'dark-swan-proof'
_DEFAULT_CONTEXT = 'github.com/ao3575911/dark-swan'
_DEFAULT_TTL_H = 24


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _canonical(proof: dict) -> str:
    """Canonical signing payload: all fields except 'signature', sorted keys."""
    payload = {k: v for k, v in proof.items() if k != 'signature'}
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def create_proof(
    identity: DSIdentity,
    claim: str,
    *,
    context: str = _DEFAULT_CONTEXT,
    ttl_hours: float = _DEFAULT_TTL_H,
) -> dict:
    """Create and sign a proof card for *identity*.

    Parameters
    ----------
    identity:
        The DSIdentity whose private key signs the proof.
    claim:
        Free-text claim string, e.g. ``"I built dark-swan"``.
    context:
        Optional context URI (default: this repository).
    ttl_hours:
        How many hours until the proof expires (default 24).

    Returns
    -------
    dict
        Complete signed proof object ready for serialisation.
    """
    now = time.time()
    proof: dict = {
        'type': _TYPE,
        'did': identity.did,
        'symbol': identity.symbolic_id,
        'handle': identity.ephemeral_handle(),
        'claim': claim,
        'context': context,
        'issued_at': _iso(now),
        'expires_at': _iso(now + ttl_hours * 3600),
        'pubkey': identity.public_key_b64(),
    }
    proof['signature'] = identity.sign(_canonical(proof))
    return proof


def verify_proof(proof: dict) -> Tuple[bool, str]:
    """Verify a proof card.

    Returns
    -------
    (valid, reason)
        ``valid`` is True only if the type, expiry, pubkey, and signature all
        check out.  ``reason`` is a human-readable status string.
    """
    if proof.get('type') != _TYPE:
        return False, f'unexpected type: {proof.get("type")!r}'

    try:
        expires = datetime.strptime(proof['expires_at'], '%Y-%m-%dT%H:%M:%SZ').replace(
            tzinfo=timezone.utc
        )
    except (KeyError, ValueError) as exc:
        return False, f'malformed expires_at: {exc}'

    if datetime.now(tz=timezone.utc) > expires:
        return False, f'proof expired at {proof["expires_at"]}'

    pubkey = proof.get('pubkey', '')
    sig = proof.get('signature', '')

    try:
        expected_did = pubkey_to_did(pubkey)
        expected_symbol = pubkey_to_id(pubkey)
    except Exception:
        return False, 'pubkey invalid'

    if proof.get('did') != expected_did:
        return False, 'DID does not match pubkey'
    if proof.get('symbol') != expected_symbol:
        return False, 'symbol does not match pubkey'

    payload = _canonical(proof)

    if not verify_message(pubkey, payload, sig):
        return False, 'signature invalid'

    return True, 'valid'


def load_proof(path: str) -> dict:
    """Load a proof card from a JSON file."""
    with open(path) as fh:
        return json.load(fh)


def save_proof(proof: dict, path: str) -> None:
    """Write a proof card to a JSON file."""
    with open(path, 'w') as fh:
        json.dump(proof, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
