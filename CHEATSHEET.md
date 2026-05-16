# dark-swan cheatsheet

## Install

```bash
pip install -e .          # installs `ds` command globally
```

---

## Identity

```bash
ds generate "my seed"
# ── dark-swan · generate ─────────────────────
# id=KLNI  handle=ds-QVWK  dr=1  energy=21.07

ds profile FWEM           # GDk9 profile of any word
```

---

## Sign / Verify

```bash
# Sign
ds sign "my seed" "the message"
# → sig=<base64>  pubkey=<base64>

# Verify (no seed needed)
ds verify <pubkey> "the message" <sig>
# → ✓ valid   id=KLNI
```

---

## Registry

```bash
ds publish "my seed"                  # register in registry.json
ds publish "my seed" --overwrite      # update existing record

ds lookup KLNI                        # by symbolic ID
ds lookup ds-QVWK                     # by today's handle
```

---

## Search

```bash
ds search                          # all records
ds search --dr 7                   # digital root = 7
ds search --class asymmetric       # dominant class
ds search --energy-range 10,50     # SymPhi energy band
```

---

## Proof cards

```bash
ds proof create "my seed" --claim "I built dark-swan"
# → proof.json  (valid 24 h, signed with Ed25519)

ds proof verify proof.json
# → ✓ valid

ds proof card proof.json
# → formatted display
```

---

## Global flags  (always before the subcommand)

```bash
ds --registry /path/to/reg.json <cmd>
ds --no-color <cmd>
ds --json <cmd>
```

---

## Symmetry classes & colors

| Class | Color | Letters | Energy rule |
|-------|-------|---------|-------------|
| idempotent | cyan | A H I M O T U V W X Y | pos |
| biphasic | yellow | B C D E K | sin(pos) |
| involutive | magenta | N S Z | 1/pos |
| asymmetric | red | F G J L P Q R | pos+1 |

Digital root: A1Z26 letter sum → 1–9 (9 if divisible by 9)

---

## Derivation chain

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

## Proof card wire format

```json
{
  "type":       "dark-swan-proof",
  "did":        "did:ds:KLNI",
  "symbol":     "KLNI",
  "handle":     "ds-QVWK",
  "claim":      "I control this identity",
  "context":    "github.com/ao3575911/dark-swan",
  "issued_at":  "2026-05-16T00:00:00Z",
  "expires_at": "2026-05-17T00:00:00Z",
  "pubkey":     "<base64url 44-char>",
  "signature":  "<base64url Ed25519 sig>"
}
```

Signature covers all fields except `signature` itself (canonical JSON, sorted keys).
