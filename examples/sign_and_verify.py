"""Example: sign a message and verify it with only the public key.

Demonstrates that verification requires no seed — anyone with the
public key can independently confirm the signature and re-derive the
symbolic ID.
"""
from ds_protocol_core import DSIdentity, verify_message, pubkey_to_id

# ── Signer side (holds the seed) ─────────────────────────────────────────────
identity  = DSIdentity("dark-swan@protocol")
message   = "publish: the medium is the message"
signature = identity.sign(message)

print("=== signer ===")
print("id     :", identity.symbolic_id)
print("pubkey :", identity.public_key_b64())
print("sig    :", signature[:48] + "…")

# ── Verifier side (only needs pubkey + sig) ───────────────────────────────────
pubkey = identity.public_key_b64()

print("\n=== verifier ===")
ok = verify_message(pubkey, message, signature)
print("valid  :", ok)                               # True
print("id     :", pubkey_to_id(pubkey))             # re-derived, no seed needed

# Tampered message should fail
ok_tampered = verify_message(pubkey, message + "!", signature)
print("tamper :", ok_tampered)                      # False
