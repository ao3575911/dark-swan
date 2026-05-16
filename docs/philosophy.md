# Dark-Swan Philosophy

> "Self-issued identity. Portable proofs. No permission layer."

---

## Why this project exists

Identity on the internet is being pulled into two bad futures.

On one side: state and platform digital-ID systems that convert access, speech, payments, and reputation into permissioned infrastructure. Your identity is issued by someone else, revoked by someone else, and correlated across contexts by default.

On the other side: the fully anonymous throwaway account — no accountability, no continuity, no verifiable history. Nothing stops a bad actor from creating a thousand such accounts. Nothing stops a conversation from being astroturfed.

Dark-Swan is built from the opposite angle: identity as self-issued infrastructure, not administrative control.

It gives you a **persistent pseudonymous identity** — stable enough to build reputation, verifiable enough that others can confirm continuity, and anonymous enough that no legal name, phone number, platform account, or government credential is required.

---

## The core idea: keys, not permission

Your identity is derived from a keypair, not from a database entry. There is no issuer, approval queue, phone-number gate, compliance vendor, or central list required for verification.

```
random/private key → public key → DID fingerprint + symbolic short name
```

The DID is the canonical identity. The symbolic short name (`KLNI`, `FWEM`, …) is a 4-letter word derived from your public key. Anyone can verify that a given public key produces a given symbolic ID — independently, without contacting any server. If you sign a message with your key, anyone who holds your public key can confirm it was you, with no third party involved.

---

## Symbolic layer: useful, not mandatory

Dark-Swan uses a canonical DID fingerprint for serious identity work. The 4-letter symbolic name and its energy/class metrics are an optional human layer on top.

Keep the symbolic metrics if you want identity to be memorable, searchable, and community-native. Remove or ignore them if you want a minimal cryptographic DID system. They are not security assumptions. They are UX and culture.

---

## Ephemeral handles and temporal unlinkability

Your symbolic ID is stable. Your handle (`ds-QVWK`) rotates every UTC day.

If someone only knows your handle, they cannot tell whether you were online yesterday or last week — unless they already know your symbolic short name. This gives a layer of temporal unlinkability for observers who do not have prior context. It is not perfect anonymity. It is **graceful anonymity**: meaningful protection without making the system unusable.

---

## Portable proofs

Signing a message proves you hold a private key. But a raw signature is context-free — it requires the verifier to know what was signed, hold your public key, and do the verification themselves.

A proof card packages all of that into a single portable document: your DID, your symbolic short name, your current handle, a free-text claim, an expiry, your public key, and an Ed25519 signature over the whole thing. Anyone can verify it with zero infrastructure — no registry lookup, no server, no seed. It is sovereignty made portable.

This is the lightest possible unit of verifiable trust: a single JSON file that can be attached to an email, posted in a forum, or embedded in another document, and that stands on its own.

---

## What this is not

Dark-Swan does not hide your IP address. It does not encrypt your messages. It does not prevent a sufficiently motivated adversary with physical access from finding you.

It is an identity layer, not a full anonymity system. Think of it as a cryptographic pseudonym — durable, verifiable, and sovereign — on top of which you can build whatever communication or trust infrastructure you need.

---

## Constraints and trade-offs we accept

- **Key security is the user's responsibility.** Random encrypted key files are preferred. Legacy seed mode is convenient, but weak seeds are brute-forceable.
- **4-letter symbols will collide at scale.** This is acceptable because the canonical DID fingerprint is the real identity key. The symbol is a label, not authority.
- **No federation yet.** The registry is local JSON. This is a pragmatic starting point, not an architectural commitment. Federation and transparency logs are on the roadmap.
- **Handle linkability if your ID is known.** We do not pretend otherwise. The handle rotation is a convenience layer, not a strong unlinkability guarantee.

---

## The name

A "dark swan" is a rare, hard-to-predict event with outsized significance — an inversion of Nassim Taleb's black swan framing. The name reflects a belief that genuine, user-sovereign identity on public networks is currently rare and undervalued — but when it arrives at scale, its impact will be disproportionate.
