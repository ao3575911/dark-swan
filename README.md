# dark-swan

Decentralized identity and symbolic anonymization protocol. Unites Ed25519 cryptography, symbolic logic, and rotating pseudonyms — creating private, verifiable, and pseudonymous identities for creators, researchers, and autonomous agents.

> "Graceful anonymity through symbolic verification."

```python
from ds_protocol_core import DSIdentity

identity = DSIdentity("my-secret-seed")
print(identity.symbolic_id)              # short urlsafe ID derived from seed
print(identity.derive_ephemeral_handle()) # rotates daily: "ds_Xk3mPq"

sig = identity.sign_message("hello world")
identity.verify_message("hello world", sig)  # True
```

## Features

- **Ed25519 signing** — industry-standard elliptic curve signatures via `cryptography`
- **Symbolic identities** — compact, human-readable IDs derived from your seed
- **Rotating pseudonyms** — ephemeral handles that change daily, breaking linkability
- **Local registry** — commit and resolve identities via a SHA3-256-keyed JSON store
- **Zero-Knowledge proofs** *(planned — v0.2)*

## Install

```bash
git clone https://github.com/ao3575911/dark-swan.git
cd dark-swan
pip install cryptography
```

Requires Python ≥ 3.10. No other runtime dependencies.

## Usage

### Generate an identity

```python
from ds_protocol_core import DSIdentity

identity = DSIdentity("your-unique-seed-phrase")

# Stable symbolic ID (derived from seed hash)
print(identity.symbolic_id)

# Daily-rotating pseudonym (changes every 24h)
handle = identity.derive_ephemeral_handle()
print(handle)   # e.g. "ds_Xk3mPq"
```

### Sign and verify messages

```python
sig = identity.sign_message("publish this")
valid = identity.verify_message("publish this", sig)   # True
tampered = identity.verify_message("publish THIS", sig)  # False
```

### Registry — commit and resolve

```python
from ds_registry import DSRegistry

reg = DSRegistry("registry.json")
reg.commit(identity.symbolic_id, handle)

entry = reg.resolve(identity.symbolic_id)
print(entry["handle"])
```

### Full example

```bash
python examples/generate_identity.py
```

## Protocol design

See `docs/protocol_design.md` for architecture layers, the symbolic system, and registry logic.

The identity lifecycle:

```
seed → sha256 → Ed25519 private key → symbolic_id (8-byte urlsafe)
                                    ↓
                            ephemeral_handle (rotates daily via sha3-256)
```

## Roadmap

| Version | Feature |
|---------|---------|
| v0.1 (now) | Ed25519 identities, rotating handles, local registry |
| v0.2 | Zero-Knowledge symbolic proofs |
| v0.3 | IPFS-backed distributed registry |

## License

MIT — © 2025 Adam Grange (@beathovn)
