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
| `lookup <id\|handle>` | Resolve a symbolic ID or `ds-XXXX` handle |
| `search` | Filter registry by `--dr`, `--class`, or `--energy-range` |
| `profile <word>` | GDk9 symbolic breakdown of any 4-letter word |

**Global flags** (before the subcommand):

```
--registry FILE   Path to registry JSON  (default: registry.json)
--no-color        Disable ANSI output
--json            Also emit JSON alongside human output
```

---

## How symbolic IDs work

```
seed → Ed25519 keypair → SHA-256(public_key) → first 4 bytes → A-Z letters
```

The symbolic ID (`KLNI`, `FWEM`, …) is derived from the **public key only**.  
Anyone with your public key can independently verify your ID — no seed required.

Each letter carries GDk9 symmetry-class energy (idempotent / biphasic / involutive / asymmetric).  
The ID is indexed by digital root (1–9) and total SymPhi energy for registry search.

**Ephemeral handles** (`ds-XXXX`) rotate each UTC day:  
`SHA3-256(symbolic_id + epoch_day) → 4-letter word → ds-XXXX`

---

## Registry search

```bash
ds search --dr 7                        # all identities with digital root 7
ds search --class asymmetric            # dominant class filter
ds search --energy-range 10,50          # SymPhi energy band
ds search                               # list all
```

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
ds_cli.py            CLI — all 7 commands
tests/               76 unit tests
```

---

## License

MIT — © 2025 Adam Grange (@beathovn)
