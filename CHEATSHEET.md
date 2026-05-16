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
ds publish "my seed"           # register in registry.json
ds publish "my seed" --overwrite  # update existing record

ds lookup KLNI                 # by symbolic ID
ds lookup ds-QVWK              # by today's handle
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
