# dark-swan

User-sovereign pseudonymous identity for builders who do not want identity owned by states, platforms, or vendors.  
Every identity has a canonical `did:ds:<fingerprint>` derived from its public key, plus a 4-letter symbolic short name — verifiable, portable, and daily-rotating.

> "Self-issued identity. Portable proofs. No permission layer."

---

## Install

```bash
pip install -e .
```

That's it. The `ds` command is now available globally.

**Dependencies:** `cryptography>=41` (standard Ed25519 + encrypted PEM key files). No other runtime deps.  
**Optional:** `gdk9` — install only if you want deeper symbolic/DCG path analysis in `ds profile`.

---

## Quick start

```bash
# Create a legacy deterministic identity
ds generate "your secret seed"

# Preferred: create a random encrypted key file
ds keygen --output identity.pem --passphrase "strong passphrase"
ds generate-key identity.pem --passphrase "strong passphrase"

# Sign a message
ds sign "your secret seed" "hello world"

# Verify a signature (no seed needed)
ds verify <pubkey_b64> "hello world" <signature>

# Register in local registry
ds publish "your secret seed"

# Look up by DID, symbolic short name, or handle
ds lookup FWEM
ds lookup ds-QVWK
```

---

## Commands

| Command | Description |
|---------|-------------|
| `generate <seed>` | Legacy deterministic seed identity — DID, symbolic short name, handle, symbolic profile |
| `keygen` | Create a random Ed25519 key file, encrypted by default |
| `generate-key <file>` | Show DID/profile info from a PEM key file |
| `sign <seed> <msg>` | Sign a message with legacy seed mode; outputs signature + pubkey |
| `sign-key <file> <msg>` | Sign a message with a key file |
| `verify <pubkey> <msg> <sig>` | Verify without a seed; re-derives symbolic ID |
| `publish <seed>` | Register legacy seed identity in the local registry |
| `publish-key <file>` | Register key-file identity in the local registry |
| `publish <seed> --overwrite` | Replace an existing registry record |
| `lookup <id\|handle>` | Resolve a symbolic ID or `ds-XXXX` handle |
| `search` | Filter registry by `--dr`, `--class`, or `--energy-range` |
| `profile <word>` | Symbolic breakdown of any 4-letter word |
| `proof create <seed>` | Create a signed portable proof card |
| `proof verify <file>` | Verify a proof card |
| `proof card <file>` | Display a formatted proof card |

**Global flags** (before the subcommand):

```
--registry FILE   Path to registry JSON  (default: registry.json)
--no-color        Disable ANSI output
--json            Also emit JSON alongside human output
```

---

## How identities work

```
seed
 └→ SHA-256(seed)
     └→ Ed25519 private key
         └→ public key  (32 bytes raw)
             └→ SHA-256(pubkey)
                 └→ first 4 bytes → A-Z  →  symbolic_id  e.g. KLNI
                                              │
                                    SHA3-256(id + epoch_day) → handle  ds-QVWK
```

The canonical DID is derived from the **public key only** using the first 16 bytes of `SHA-256(pubkey)` as 32 lowercase hex characters. The symbolic short name (`KLNI`, `FWEM`, …) is also derived from the public key and remains the human-readable short label. Anyone with your public key can independently verify both — no seed required.

**Ephemeral handles** (`ds-XXXX`) rotate each UTC day.

---

## Symbolic metrics

The 4-letter short name is not the canonical identity key — the DID is. The symbolic layer is an optional UX/indexing layer that makes identities easier to recognize, discuss, and search. Each letter carries a symmetry class that determines its energy contribution:

| Class | Color | Letters | Energy rule |
|-------|-------|---------|-------------|
| idempotent | cyan | A H I M O T U V W X Y | `pos` |
| biphasic | yellow | B C D E K | `sin(pos)` |
| involutive | magenta | N S Z | `1/pos` |
| asymmetric | red | F G J L P Q R | `pos + 1` |

**Digital root** (DR 1–9): A1Z26 letter sum reduced to a single digit (9 if divisible by 9).  
**SymPhi energy**: sum of each letter's energy value under its class rule.

Records can be indexed by DR and total energy for registry search. Keep this if you want human/memetic navigation; ignore it if you want a pure cryptographic DID workflow.

---

## Registry search

```bash
ds search --dr 7                        # all identities with digital root 7
ds search --class asymmetric            # dominant class filter
ds search --energy-range 10,50          # SymPhi energy band
ds search                               # list all
```

---

## Key files

For production-style identities, prefer random key files over human seed strings:

```bash
ds keygen --output identity.pem --passphrase "strong passphrase"
ds sign-key identity.pem "hello world" --passphrase "strong passphrase"
ds publish-key identity.pem --passphrase "strong passphrase"
ds proof create-key identity.pem --passphrase "strong passphrase" --claim "I control this identity"
```

`ds generate <seed>` remains available for deterministic demos and compatibility, but raw `SHA-256(seed)` is not recommended for high-value identities.

## Python API

```python
from ds_protocol_core import DSIdentity, verify_message, pubkey_to_id

# Generate an identity
identity = DSIdentity("your secret seed")
print(identity.symbolic_id)          # e.g. "KLNI"
print(identity.ephemeral_handle())   # e.g. "ds-QVWK" — rotates daily
print(identity.public_key_b64())     # base64url-encoded Ed25519 public key

# Sign a message
sig = identity.sign("hello world")

# Verify with only the public key (no seed needed)
pubkey = identity.public_key_b64()
ok = verify_message(pubkey, "hello world", sig)  # True
sid = pubkey_to_id(pubkey)                        # re-derives symbolic ID
```

See `examples/` for complete workflows including registry use.

---

## Proof cards

Create a portable, signed identity proof:

```bash
ds proof create "your secret seed" --claim "I built dark-swan"
# → proof.json

ds proof verify proof.json
# → ✓ valid

ds proof card proof.json
# → formatted proof display
```

A proof card is a signed JSON object containing your canonical DID, symbolic ID, handle, claim, expiry, public key, and Ed25519 signature. Verification checks the signature and confirms that DID + symbol match the embedded public key. Anyone can verify it with only the public key — no seed, no registry lookup required.

---

## Optional symbolic integration

Install `gdk9` alongside dark-swan only if you want:

- DCG path analysis in `ds profile`
- Homotopy equivalence checks between symbolic IDs
- Full SymPhi energy model

```bash
pip install -e ../gdk9   # or wherever your gdk9 lives
```

---

## Project layout

```
ds_gdk9.py           Symbolic metrics bridge (standalone, no gdk9 dep)
ds_protocol_core.py  DSIdentity — keypair, signing, symbolic ID derivation
ds_registry.py       Persistent JSON registry with GDk9-aware search
ds_proof.py          Proof cards — create, sign, and verify portable proofs
ds_cli.py            CLI — generate, sign, verify, publish, lookup, search, profile, proof
docs/
  protocol_design.md  Full protocol specification
  philosophy.md       Project purpose and design rationale
  roadmap.md          Planned milestones
examples/            Runnable Python examples
tests/               124 unit tests
```

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the full plan. Short version:

| Version | Theme |
|---------|-------|
| v0.2.1 | Hardening — registry fixes, CLI validation, proof cards, full CI |
| v0.3 | DID / fingerprint rollout, optional KDF, SQLite registry |
| v0.4 | Proof cards v2 — QR codes, claim chains |
| v0.5 | Decentralized registry / transparency log |

---

## License

MIT — © 2025 Adam Grange (@beathovn)
