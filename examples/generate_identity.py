"""Example: generate a dark-swan identity and inspect its GDk9 profile."""
from ds_protocol_core import DSIdentity

identity = DSIdentity("dark-swan@protocol")

print("symbolic id :", identity.symbolic_id)          # 4-letter GDk9 word
print("handle      :", identity.ephemeral_handle())   # ds-XXXX, rotates daily
print("pubkey      :", identity.public_key_b64())     # share this; keep seed secret

profile = identity.profile()
print("\nGDk9 profile")
print("  word         :", profile["word"])
print("  digital root :", profile["digital_root"])
print("  energy       :", f'{profile["total_energy"]:.4f}')
print("  class        :", profile["dominant_class"])
print("  steps:")
for s in profile["steps"]:
    print(f'    {s["char"]}  {s["class"]:<12}  pos={s["pos"]:<2}  e={s["energy"]:.4f}')
