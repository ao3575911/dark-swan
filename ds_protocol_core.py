#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib, base64, time
from cryptography.hazmat.primitives.asymmetric import ed25519

class DSIdentity:
    def __init__(self, seed: str):
        self.seed = seed.encode()
        h = hashlib.sha256(self.seed).digest()
        self.key = ed25519.Ed25519PrivateKey.from_private_bytes(h)
        self.public = self.key.public_key()
        self.symbolic_id = base64.urlsafe_b64encode(h[:8]).decode()

    def derive_ephemeral_handle(self):
        epoch_day = int(time.time() // 86400)
        h = hashlib.sha3_256(self.seed + str(epoch_day).encode()).digest()
        return "ds_" + base64.urlsafe_b64encode(h[:6]).decode()

    def sign_message(self, msg: str):
        sig = self.key.sign(msg.encode())
        return base64.urlsafe_b64encode(sig).decode()

    def verify_message(self, msg: str, signature: str):
        try:
            self.public.verify(base64.urlsafe_b64decode(signature), msg.encode())
            return True
        except Exception:
            return False
