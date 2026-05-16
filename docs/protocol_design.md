# Dark-Swan Protocol Design

## Overview

Dark-Swan is a deterministic, pseudonymous identity protocol built on Ed25519 key pairs and optional symbolic grounding. Every identity has a canonical long-form DID and an optional short symbolic label, both independently verifiable from the public key alone — no central authority, no registration, no seed exposure required for verification.

---

## 1. Identity Derivation

```
seed (string)
  └→ SHA-256(seed.encode('utf-8'))   → 32 bytes  [private key material]
      └→ Ed25519PrivateKey.from_private_bytes(...)
          └→ Ed25519PublicKey  (32 bytes raw)
```

**Known limitation:** SHA-256 seed mode is deterministic and convenient but not hardened — brute-force attacks on weak seed strings could recover the key. Dark-Swan now supports random Ed25519 key files stored as PKCS8 PEM, encrypted with `cryptography` when a passphrase is supplied. For high-value identities, prefer `ds keygen` + key-file commands over raw seed mode. An Argon2id/scrypt KDF mode for deterministic seeds remains planned.

---


## 2. Keyfile Mode

Preferred identity creation uses random Ed25519 keys:

```
ds keygen --output identity.pem --passphrase "..."
```

The key file is PKCS8 PEM. When `--passphrase` is supplied, it is encrypted using `cryptography`'s best available password-based PEM encryption. `--no-encrypt` is available for tests or throwaway demos but should not be used for valuable identities.

Key-file commands include `generate-key`, `sign-key`, `publish-key`, and `proof create-key`.

## 3. Canonical DID Derivation

```
Ed25519 public key (32 bytes raw)
  └→ SHA-256(pubkey_raw)             → 32 bytes
      └→ first 16 bytes              → 32 lowercase hex chars
          └→ "did:ds:" + hex32       e.g. did:ds:a3f9...d581
```

The DID is the primary identity key. It has a much larger collision-resistant namespace than the symbolic short name and should be used for registry keys, proof cards, and cross-system references.

## 4. Symbolic Short-Name Derivation

```
Ed25519 public key (32 bytes raw)
  └→ SHA-256(pubkey_raw)             → 32 bytes
      └→ first 4 bytes
          └→ each byte % 26          → letter index A-Z
              └→ 4-letter word       e.g. "KLNI"  (symbolic_id)
```

The symbolic short name is a human-memorable 4-letter word derived **only from the public key**. Anyone holding the public key can independently re-derive and verify the symbolic ID. No seed access is needed.

**Known limitation:** The symbolic ID space is 26⁴ = 456,976 unique values. Collision probability rises sharply once thousands of identities are registered. Symbolic short names are human-readable labels, not globally unique long-term identity keys. See §7 for the planned upgrade.

---

## 5. Handle Derivation

```
symbolic short name (string)  +  epoch_day (int, UTC)
  └→ SHA3-256((symbolic_id + str(epoch_day)).encode())
      └→ first 4 bytes → A-Z letters
          └→ "ds-" + 4-letter word    e.g. "ds-QVWK"  (ephemeral handle)
```

Handles rotate once per UTC day (`epoch_day = floor(unix_ts / 86400)`). A fresh handle is indistinguishable from any other valid handle to an observer who does not know the symbolic ID — but the mapping is deterministic for anyone who does.

**Known limitation:** If an observer discovers the symbolic ID, past and future handles are predictable. Handle rotation provides temporal unlinkability only against adversaries who cannot correlate the symbolic ID across days.

---

## 6. Signing and Verification

Dark-Swan uses raw Ed25519 signatures (RFC 8032).

**Signing** (seed holder only):
```
signature = Ed25519PrivateKey.sign(message.encode('utf-8'))
                              ↓ base64url-encoded string
```

**Verification** (anyone with the public key):
```
Ed25519PublicKey.verify(
    base64url_decode(signature),
    message.encode('utf-8')
)
```
A failed verification raises `cryptography.exceptions.InvalidSignature`; this is caught and returns `False`. Padding is handled by appending `==` before decoding (base64url without padding).

---

## 7. Registry Record Format

The local registry is a JSON file (`registry.json` by default) mapping `did → record`. The record also stores `symbolic_id` for short-label lookup and display.

```json
{
  "did:ds:a3f9c2b17e04d581ffeeddccbbaa9988": {
    "did":          "did:ds:a3f9c2b17e04d581ffeeddccbbaa9988",
    "symbolic_id":  "FWEM",
    "pubkey_b64":   "<base64url 44-char raw Ed25519 public key>",
    "handle":       "ds-XYZW",
    "committed_at": 1716000000,
    "profile": {
      "digital_root":   7,
      "dominant_class": "asymmetric",
      "total_energy":   42.04,
      "class_counts":   {"asymmetric": 2, "idempotent": 1, "biphasic": 1}
    }
  }
}
```

**Indexed fields** (searchable via `ds search`):

| Field | Type | Description |
|-------|------|-------------|
| `digital_root` | int 1–9 | A1Z26 letter sum → digital root |
| `dominant_class` | string | Plurality symmetry class of the 4 letters |
| `total_energy` | float | Sum of per-letter SymPhi energies |

**Symmetry classes:**

| Class | Letters | Energy rule |
|-------|---------|-------------|
| `idempotent` | A H I M O T U V W X Y | pos |
| `biphasic` | B C D E K | sin(pos) |
| `involutive` | N S Z | 1/pos |
| `asymmetric` | F G J L P Q R | pos + 1 |

---

## 8. Proof Cards

A proof card is a signed portable document asserting control of a dark-swan identity. Wire format (see `ds_proof.py`):

```json
{
  "type":       "dark-swan-proof",
  "did":        "did:ds:a3f9c2b17e04d581ffeeddccbbaa9988",
  "symbol":     "FWEM",
  "handle":     "ds-XYZW",
  "claim":      "I control this identity",
  "context":    "github.com/ao3575911/dark-swan",
  "issued_at":  "2026-05-16T00:00:00Z",
  "expires_at": "2026-05-17T00:00:00Z",
  "pubkey":     "<base64url>",
  "signature":  "<base64url Ed25519 sig>"
}
```

The `signature` covers a canonical JSON serialisation of all other fields (sorted keys, no extra whitespace). Verification requires only the `pubkey` field — no registry lookup. Verifiers also re-derive the DID and symbol from `pubkey` and reject proof cards whose identifiers do not match.

---

## 9. Known Limitations

| # | Issue | Severity | Planned fix |
|---|-------|----------|-------------|
| L1 | 4-letter symbolic short-name space (26⁴ = 456,976) has high collision risk at scale | Mitigated | Canonical DID fingerprints are now primary; keep symbol as display label |
| L2 | SHA-256(seed) legacy mode has no KDF or salt | Medium | Prefer random encrypted key files now; future: optional Argon2id/scrypt KDF for seed mode |
| L3 | Daily handles are predictable once symbolic_id is known | Medium | Accepted; by design for UX. Future: blinded tokens |
| L4 | Registry is local append-only JSON; no federation, no tamper evidence | Medium | v0.5: Merkle/transparency-log backend |
| L5 | `registry.json` is a flat file — no locking for concurrent writes | Low | v0.3: SQLite or locking wrapper |

---

## 10. DID / Fingerprint Status

Dark-Swan now derives canonical DIDs as:

```
did:ds:<hex32>
```

where `hex32` is the first 16 bytes of SHA-256(pubkey) as lowercase hex (32 chars). This gives 2¹²⁸ collision resistance for the canonical identifier. The 4-letter word is retained as the human-memorable short form; the DID is the primary key for registry records and proof cards.
