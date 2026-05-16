# Dark-Swan Philosophy

> "Graceful anonymity through symbolic verification."

---

## Why this project exists

Identity on the internet is broken in two opposite directions.

On one side: centralised platforms that require a real name, email, phone number, and payment method before you can say anything at all. Your identity is owned by the platform. They can delete you, shadow-ban you, sell your metadata, or hand it to governments. You are a tenant in someone else's panopticon.

On the other side: the fully anonymous throwaway account — no accountability, no continuity, no verifiable history. Nothing stops a bad actor from creating a thousand such accounts. Nothing stops a conversation from being astroturfed.

Dark-Swan is built for the space in between.

It gives you a **persistent pseudonymous identity** — stable enough to build a reputation, verifiable enough that others can confirm you are the same entity across contexts, anonymous enough that no one learns who you are from the identifier alone.

---

## The core idea: keys, not names

Your identity is derived from a keypair, not from a database entry. There is no registration, no authority to approve you, and no central list that can be seized or taken offline.

```
your secret seed → deterministic keypair → public key → symbolic ID
```

The symbolic ID (`KLNI`, `FWEM`, …) is a 4-letter word derived from your public key. Anyone can verify that a given public key produces a given symbolic ID — independently, without contacting any server. If you sign a message with your key, anyone who holds your public key can confirm it was you, with no third party involved.

---

## Symbolic grounding (GDk9)

Dark-Swan IDs are not just random hex strings. Each 4-letter word carries structure from the GDk9 symbolic system: a digital root, a dominant symmetry class, a total energy. These are derived properties — you cannot choose them directly — but they make identities *feel* different from each other in a meaningful way.

This is not magic. It is a design choice to make the identity space humanly navigable: a registry of thousands of identities that can be searched by character, by energy, by class. A fingerprint that a person can speak aloud and that a community can learn to recognise.

---

## Ephemeral handles and temporal unlinkability

Your symbolic ID is stable. Your handle (`ds-QVWK`) rotates every UTC day.

If someone only knows your handle, they cannot tell whether you were online yesterday or last week — unless they already know your symbolic ID. This gives a layer of temporal unlinkability for observers who do not have prior context. It is not perfect anonymity. It is **graceful anonymity**: meaningful protection without making the system unusable.

---

## Portable proofs

Signing a message proves you hold a private key. But a raw signature is context-free — it requires the verifier to know what was signed, hold your public key, and do the verification themselves.

A proof card packages all of that into a single portable document: your DID, your symbolic ID, your current handle, a free-text claim, an expiry, your public key, and an Ed25519 signature over the whole thing. Anyone can verify it with zero infrastructure — no registry lookup, no server, no seed. It is sovereignty made portable.

This is the lightest possible unit of verifiable trust: a single JSON file that can be attached to an email, posted in a forum, or embedded in another document, and that stands on its own.

---

## What this is not

Dark-Swan does not hide your IP address. It does not encrypt your messages. It does not prevent a sufficiently motivated adversary with physical access from finding you.

It is an identity layer, not a full anonymity system. Think of it as a cryptographic pseudonym — durable, verifiable, and sovereign — on top of which you can build whatever communication or trust infrastructure you need.

---

## Constraints and trade-offs we accept

- **Seed security is the user's responsibility.** If your seed is weak or exposed, your identity is compromised. We cannot change this without introducing a custodian, which defeats the purpose.
- **4-letter IDs will collide at scale.** This is a known limitation, acceptable for early adoption. The v0.3 DID upgrade introduces a longer fingerprint while preserving the human-readable short form.
- **No federation yet.** The registry is local JSON. This is a pragmatic starting point, not an architectural commitment. Federation and transparency logs are on the roadmap.
- **Handle linkability if your ID is known.** We do not pretend otherwise. The handle rotation is a convenience layer, not a strong unlinkability guarantee.

---

## The name

A "dark swan" is a rare, hard-to-predict event with outsized significance — an inversion of Nassim Taleb's black swan framing. The name reflects a belief that genuine, user-sovereign identity on public networks is currently rare and undervalued — but when it arrives at scale, its impact will be disproportionate.
