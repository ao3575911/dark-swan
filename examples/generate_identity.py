from ds_protocol_core import DSIdentity

if __name__ == "__main__":
    ds = DSIdentity("dark-swan@protocol")
    print("Symbolic ID:", ds.symbolic_id)
    print("Ephemeral Handle:", ds.derive_ephemeral_handle())
