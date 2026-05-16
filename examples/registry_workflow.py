"""Example: register identities and search the registry.

Shows the full commit → lookup → search → verify workflow using
an in-memory temp registry (deleted after the script exits).
"""

import os
import tempfile

from ds_protocol_core import DSIdentity
from ds_registry import DSRegistry

# Temp registry so this example leaves no files behind
tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
tmp.close()
os.unlink(tmp.name)
reg = DSRegistry(tmp.name)

# ── Register three identities ─────────────────────────────────────────────────
seeds = ['alice@dark-swan', 'bob@dark-swan', 'carol@dark-swan']
identities = [DSIdentity(s) for s in seeds]

for ident in identities:
    rec = reg.commit(ident.public_key_b64(), ident.ephemeral_handle())
    p = rec['profile']
    print(
        f'registered  {rec["symbolic_id"]}  handle={rec["handle"]}'
        f'  dr={p["digital_root"]}  class={p["dominant_class"]}'
    )

# ── Lookup ────────────────────────────────────────────────────────────────────
print('\n--- lookup by symbolic id ---')
alice = identities[0]
rec = reg.resolve(alice.symbolic_id)
print(f'{rec["symbolic_id"]}  →  {rec["handle"]}')

print('\n--- lookup by handle ---')
handle = identities[1].ephemeral_handle()
rec = reg.resolve_by_handle(handle)
print(f'{handle}  →  {rec["symbolic_id"]}')

# ── Search ────────────────────────────────────────────────────────────────────
print('\n--- search by digital root ---')
for dr in range(1, 10):
    results = reg.search_by_dr(dr)
    if results:
        ids = ', '.join(r['symbolic_id'] for r in results)
        print(f'  dr={dr}  {ids}')

print('\n--- search by energy range 0–100 ---')
for r in reg.search_by_energy_range(0, 100):
    print(f'  {r["symbolic_id"]}  energy={r["profile"]["total_energy"]:.4f}')

# ── Signature verification via registry ──────────────────────────────────────
print('\n--- verify signature through registry ---')
msg = 'hello from alice'
sig = alice.sign(msg)
ok = reg.verify_record(alice.symbolic_id, msg, sig)
print(f'record verify: {ok}')  # True

ok_bad = reg.verify_record(alice.symbolic_id, 'tampered', sig)
print(f'tamper verify: {ok_bad}')  # False

# Cleanup
try:
    os.unlink(tmp.name)
except FileNotFoundError:
    pass
