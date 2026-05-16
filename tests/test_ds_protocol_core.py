"""Tests for ds_protocol_core.py — DSIdentity and standalone verify."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_protocol_core import DSIdentity, verify_message, pubkey_to_id


class TestDSIdentityInit(unittest.TestCase):
    def setUp(self):
        self.identity = DSIdentity('test-seed-abc')

    def test_symbolic_id_is_4_letters(self):
        sid = self.identity.symbolic_id
        self.assertEqual(len(sid), 4)
        self.assertTrue(sid.isupper())
        self.assertTrue(sid.isalpha())

    def test_symbolic_id_deterministic(self):
        a = DSIdentity('test-seed-abc')
        b = DSIdentity('test-seed-abc')
        self.assertEqual(a.symbolic_id, b.symbolic_id)

    def test_different_seeds_different_ids(self):
        a = DSIdentity('seed-one')
        b = DSIdentity('seed-two')
        self.assertNotEqual(a.symbolic_id, b.symbolic_id)

    def test_pubkey_b64_length(self):
        # Ed25519 raw pubkey is 32 bytes → base64url is 44 chars (without padding) or 43-44
        pk = self.identity.public_key_b64()
        self.assertGreaterEqual(len(pk), 40)

    def test_pubkey_raw_length(self):
        self.assertEqual(len(self.identity.public_key_raw()), 32)

    def test_symbolic_id_derived_from_pubkey(self):
        from ds_gdk9 import pubkey_to_symbolic_id
        raw = self.identity.public_key_raw()
        expected = pubkey_to_symbolic_id(raw)
        self.assertEqual(self.identity.symbolic_id, expected)


class TestSignVerify(unittest.TestCase):
    def setUp(self):
        self.identity = DSIdentity('sign-test-seed')
        self.msg = 'hello dark-swan'

    def test_sign_and_verify(self):
        sig = self.identity.sign(self.msg)
        self.assertTrue(self.identity.verify(self.msg, sig))

    def test_wrong_message_fails(self):
        sig = self.identity.sign(self.msg)
        self.assertFalse(self.identity.verify('wrong message', sig))

    def test_wrong_signature_fails(self):
        self.assertFalse(self.identity.verify(self.msg, 'AAAAAAAAAAAAAAAA'))

    def test_signature_is_string(self):
        sig = self.identity.sign(self.msg)
        self.assertIsInstance(sig, str)

    def test_cross_identity_verify_fails(self):
        other = DSIdentity('other-seed')
        sig   = self.identity.sign(self.msg)
        self.assertFalse(other.verify(self.msg, sig))


class TestStandaloneVerify(unittest.TestCase):
    def setUp(self):
        self.identity = DSIdentity('standalone-test')
        self.msg      = 'standalone message'
        self.sig      = self.identity.sign(self.msg)
        self.pubkey   = self.identity.public_key_b64()

    def test_verify_message_valid(self):
        self.assertTrue(verify_message(self.pubkey, self.msg, self.sig))

    def test_verify_message_wrong_msg(self):
        self.assertFalse(verify_message(self.pubkey, 'other', self.sig))

    def test_verify_message_bad_sig(self):
        self.assertFalse(verify_message(self.pubkey, self.msg, 'AAAA'))

    def test_verify_message_bad_pubkey(self):
        self.assertFalse(verify_message('AAAA', self.msg, self.sig))


class TestPubkeyToId(unittest.TestCase):
    def test_matches_identity_sid(self):
        ident = DSIdentity('pubkey-to-id-test')
        derived = pubkey_to_id(ident.public_key_b64())
        self.assertEqual(derived, ident.symbolic_id)

    def test_deterministic(self):
        ident = DSIdentity('det-test')
        pk    = ident.public_key_b64()
        self.assertEqual(pubkey_to_id(pk), pubkey_to_id(pk))


class TestEphemeralHandle(unittest.TestCase):
    def test_format(self):
        ident  = DSIdentity('handle-test')
        handle = ident.ephemeral_handle(0)
        self.assertTrue(handle.startswith('ds-'))
        self.assertEqual(len(handle), 7)

    def test_rotates(self):
        ident = DSIdentity('handle-test')
        self.assertNotEqual(ident.ephemeral_handle(0), ident.ephemeral_handle(1))

    def test_same_day_consistent(self):
        ident = DSIdentity('handle-test')
        self.assertEqual(ident.ephemeral_handle(99), ident.ephemeral_handle(99))


class TestProfile(unittest.TestCase):
    def test_returns_dict(self):
        ident = DSIdentity('profile-test')
        p = ident.profile()
        self.assertIsInstance(p, dict)
        self.assertIn('digital_root', p)
        self.assertIn('total_energy', p)

    def test_profile_word_matches_symbolic_id(self):
        ident = DSIdentity('profile-match')
        p     = ident.profile()
        self.assertEqual(p['word'], ident.symbolic_id)
