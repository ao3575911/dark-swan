# dark-swan

Cryptographic pseudonymous identity with symbolic grounding.  
Every identity is a 4-letter GDk9 word derived from its public key — verifiable, energy-indexed, and daily-rotating.

> "Graceful anonymity through symbolic verification."

---

## Install

```bash
pip install -e .
```

That's it. The `ds` command is now available globally.

**Dependencies:** `cryptography>=41` (standard Ed25519). No other runtime deps.  
**Optional:** `gdk9` — install for DCG path analysis in `ds profile`.

---

## Quick start

```bash
# Create an identity
ds generate "your secret seed"

# Sign a message
ds sign "your secret seed" "hello world"

# Verify a signature (no seed needed)
ds verify <pubkey_b64> "hello world" <signature>

# Register in local registry
ds publish "your secret seed"

# Look up by symbolic ID or handle
ds lookup FWEM
ds lookup ds-QVWK
```

---

## Commands

| Command | Description |
|---------|-------------|
| `generate <seed>` | Derive identity — symbolic ID, handle, GDk9 profile |
| `sign <seed> <msg>` | Sign a message; outputs signature + pubkey |
| `verify <pubkey> <msg> <sig>` | Verify without a seed; re-derives symbolic ID |
| `publish <seed>` | Register identity in the local registry |
| `publish <seed> --overwrite` | Replace an existing registry record |
| `lookup <id\|handle>` | Resolve a symbolic ID or `ds-XXXX` handle |
| `search` | Filter registry by `--dr`, `--class`, or `--energy-range` |
| `profile <word>` | GDk9 symbolic breakdown of any 4-letter word |
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

## How symbolic IDs work

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

The symbolic ID (`KLNI`, `FWEM`, …) is derived from the **public key only**.  
Anyone with your public key can independently verify your ID — no seed required.

**Ephemeral handles** (`ds-XXXX`) rotate each UTC day.

---

## Symmetry classes

Each letter in a symbolic ID carries a GDk9 symmetry class that determines its energy contribution:

| Class | Color | Letters | Energy rule |
|-------|-------|---------|-------------|
| idempotent | cyan | A H I M O T U V W X Y | `pos` |
| biphasic | yellow | B C D E K | `sin(pos)` |
| involutive | magenta | N S Z | `1/pos` |
| asymmetric | red | F G J L P Q R | `pos + 1` |

**Digital root** (DR 1–9): A1Z26 letter sum reduced to a single digit (9 if divisible by 9).  
**SymPhi energy**: sum of each letter's energy value under its class rule.

IDs are indexed by DR and total energy for registry search.

---

## Registry search

```bash
ds search --dr 7                        # all identities with digital root 7
ds search --class asymmetric            # dominant class filter
ds search --energy-range 10,50          # SymPhi energy band
ds search                               # list all
```

---

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

A proof card is a signed JSON object containing your DID, symbolic ID, handle, claim, expiry, public key, and Ed25519 signature. Anyone can verify it with only the public key — no seed, no registry lookup required.

---

## GDk9 integration

Install `gdk9` alongside dark-swan for:

- DCG path analysis in `ds profile`
- Homotopy equivalence checks between symbolic IDs
- Full SymPhi energy model

```bash
pip install -e ../gdk9   # or wherever your gdk9 lives
```

---

## Project layout

```
ds_gdk9.py           GDk9 symbolic bridge (standalone, no gdk9 dep)
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
| v0.3 | DID / fingerprint upgrade, optional KDF, SQLite registry |
| v0.4 | Proof cards v2 — QR codes, claim chains |
| v0.5 | Decentralized registry / transparency log |

---

## License

MIT — © 2025 Adam Grange (@beathovn)
