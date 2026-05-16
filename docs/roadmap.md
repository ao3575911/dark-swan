# Dark-Swan Roadmap

## v0.2.1 — Hardening pass  *(released)*

- Fix empty / malformed registry file crash
- Tighten CLI validation (`--dr`, `--class`, `--energy-range`)
- CI now runs full pytest suite across Python 3.10 / 3.11 / 3.12
- Introduce Proof Cards (`ds proof create / verify / card`)
- Expand protocol design and philosophy docs

## v0.3 — DID / fingerprint upgrade  *(current)*

- [x] Add `did:ds:<hex32>` long-form identity key (first 16 bytes of SHA-256(pubkey) as hex)
- [x] Registry records carry both `symbolic_id` (4-letter short form) and `did` (long form)
- [x] Lookup by DID in `ds lookup`
- [x] Random Ed25519 key files with encrypted PEM storage
- [ ] Optional KDF hardening path: document and implement Argon2id seed stretching  
  (opt-in via `--kdf argon2` flag, backward-compatible)
- [ ] SQLite backend for registry with write locking

## v0.4 — Proof cards (full)

- QR code export (`ds proof card --qr`) via `qrcode[pil]` optional dependency
- Proof card schema v2: add `subject_did`, `attestation_type`, multi-claim support
- Proof chain: link proofs to form a verifiable claim graph
- `ds proof chain` — display linked proof chain for an identity

## v0.5 — Decentralized registry / transparency log

- Append-only registry with Merkle tree root published per epoch
- Peer-to-peer registry sync over HTTP (simple gossip, no consensus)
- Verifiable inclusion proofs: prove a record exists without downloading the full log
- Optional: publish roots to an existing transparency log (e.g. Sigstore Rekor)
- `ds registry export / import / verify-inclusion`
