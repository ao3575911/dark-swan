#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ds_protocol_core.py — Dark-Swan identity with GDk9 symbolic grounding.

DSIdentity derives its symbolic_id from SHA-256(public_key), making it
independently verifiable by anyone who holds the public key — no seed required.
"""

from __future__ import annotations

import base64
import hashlib
import time
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

from ds_gdk9 import derive_handle, pubkey_to_symbolic_id, symbolic_id_profile


class DSIdentity:
    """An Ed25519 identity with a GDk9-grounded symbolic ID.

    Parameters
    ----------
    seed:
        Arbitrary passphrase / secret string.  Deterministically produces the
        same keypair and symbolic_id each time.
    """

    def __init__(self, seed: str) -> None:
        self._seed_bytes = seed.encode()
        h = hashlib.sha256(self._seed_bytes).digest()
        self._init_from_private_key(ed25519.Ed25519PrivateKey.from_private_bytes(h))

    def _init_from_private_key(self, private_key: ed25519.Ed25519PrivateKey) -> None:
        self._key = private_key
        self._public = self._key.public_key()

        pubkey_raw = self._public.public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.symbolic_id = pubkey_to_symbolic_id(pubkey_raw)  # 4-letter GDk9 word
        self.did = pubkey_to_did_raw(pubkey_raw)  # canonical long-form DID
        self._pubkey_raw = pubkey_raw

    @classmethod
    def from_private_key(cls, private_key: ed25519.Ed25519PrivateKey) -> 'DSIdentity':
        """Construct an identity from an Ed25519 private key."""
        obj = cls.__new__(cls)
        obj._seed_bytes = b''
        obj._init_from_private_key(private_key)
        return obj

    @classmethod
    def generate_random(cls) -> 'DSIdentity':
        """Create a fresh random Ed25519 identity."""
        return cls.from_private_key(ed25519.Ed25519PrivateKey.generate())

    @classmethod
    def load_keyfile(cls, path: str, passphrase: Optional[str] = None) -> 'DSIdentity':
        """Load an identity from a PEM private-key file.

        Encrypted key files require *passphrase*.
        """
        password = passphrase.encode() if passphrase is not None else None
        with open(path, 'rb') as fh:
            key = load_pem_private_key(fh.read(), password=password)
        if not isinstance(key, ed25519.Ed25519PrivateKey):
            raise ValueError('key file does not contain an Ed25519 private key')
        return cls.from_private_key(key)

    # ── Public key export ─────────────────────────────────────────────────────

    def public_key_b64(self) -> str:
        """Base64url-encoded raw public key (32 bytes → 44 chars)."""
        return base64.urlsafe_b64encode(self._pubkey_raw).decode()

    def public_key_raw(self) -> bytes:
        return self._pubkey_raw

    def private_key_pem(self, passphrase: Optional[str] = None) -> bytes:
        """Return PKCS8 PEM private key bytes.

        If *passphrase* is provided, the PEM is encrypted using cryptography's
        best available password-based encryption.
        """
        enc = (
            BestAvailableEncryption(passphrase.encode())
            if passphrase is not None
            else NoEncryption()
        )
        return self._key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            enc,
        )

    def save_keyfile(self, path: str, passphrase: Optional[str] = None) -> None:
        """Write this identity's private key to *path* as PKCS8 PEM."""
        with open(path, 'wb') as fh:
            fh.write(self.private_key_pem(passphrase))

    # ── Handle derivation ─────────────────────────────────────────────────────

    def ephemeral_handle(self, epoch_day: Optional[int] = None) -> str:
        """Return today's (or a specific day's) ephemeral GDk9 handle.

        Format: ``ds-XXXX``.  Rotates each UTC day.
        """
        day = epoch_day if epoch_day is not None else int(time.time() // 86400)
        return derive_handle(self.symbolic_id, day)

    # ── Signing / verification ────────────────────────────────────────────────

    def sign(self, msg: str) -> str:
        """Return base64url-encoded Ed25519 signature over UTF-8 *msg*."""
        return base64.urlsafe_b64encode(self._key.sign(msg.encode())).decode()

    def verify(self, msg: str, signature: str) -> bool:
        """Verify *signature* against this identity's public key."""
        return _verify_with_pubkey(self._pubkey_raw, msg, signature)

    # ── GDk9 profile ─────────────────────────────────────────────────────────

    def profile(self) -> dict:
        """Return GDk9 symbolic profile of this identity's symbolic_id."""
        return symbolic_id_profile(self.symbolic_id)

    # ── Representation ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f'DSIdentity(symbolic_id={self.symbolic_id!r}, did={self.did!r})'


# ── Standalone verification (no DSIdentity instance needed) ──────────────────


def verify_message(pubkey_b64: str, msg: str, signature: str) -> bool:
    """Verify *msg* + *signature* given only a base64url-encoded public key.

    This is the verifier path: third parties can call this without access to
    the seed.
    """
    try:
        raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
        return _verify_with_pubkey(raw, msg, signature)
    except Exception:
        return False


def pubkey_to_id(pubkey_b64: str) -> str:
    """Re-derive the symbolic_id from a base64url public key (for verification)."""
    from ds_gdk9 import pubkey_to_symbolic_id

    raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
    return pubkey_to_symbolic_id(raw)


def pubkey_to_did_raw(pubkey_raw: bytes) -> str:
    """Derive the canonical Dark-Swan DID from raw public-key bytes.

    The DID uses the first 16 bytes of SHA-256(pubkey), encoded as 32 hex
    characters. The 4-letter symbolic ID remains a human-readable short label;
    this DID is the collision-resistant primary identity key.
    """
    fingerprint = hashlib.sha256(pubkey_raw).digest()[:16].hex()
    return f'did:ds:{fingerprint}'


def pubkey_to_did(pubkey_b64: str) -> str:
    """Re-derive the canonical DID from a base64url public key."""
    raw = base64.urlsafe_b64decode(pubkey_b64 + '==')
    return pubkey_to_did_raw(raw)


def _verify_with_pubkey(pubkey_raw: bytes, msg: str, signature: str) -> bool:
    try:
        pub = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_raw)
        pub.verify(base64.urlsafe_b64decode(signature + '=='), msg.encode())
        return True
    except Exception:
        return False
