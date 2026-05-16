"""Tests for ds_proof.py — Proof card creation and verification."""
import sys
import os
import json
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_protocol_core import DSIdentity
from ds_proof import create_proof, verify_proof, load_proof, save_proof, _canonical


class TestCreateProof(unittest.TestCase):
    def setUp(self):
        self.ident = DSIdentity('proof-test-seed')

    def test_type_field(self):
        p = create_proof(self.ident, 'test claim')
        self.assertEqual(p['type'], 'dark-swan-proof')

    def test_did_format(self):
        p = create_proof(self.ident, 'test claim')
        self.assertEqual(p['did'], f'did:ds:{self.ident.symbolic_id}')

    def test_symbol_matches_identity(self):
        p = create_proof(self.ident, 'test claim')
        self.assertEqual(p['symbol'], self.ident.symbolic_id)

    def test_claim_preserved(self):
        p = create_proof(self.ident, 'I built dark-swan')
        self.assertEqual(p['claim'], 'I built dark-swan')

    def test_pubkey_present(self):
        p = create_proof(self.ident, 'claim')
        self.assertEqual(p['pubkey'], self.ident.public_key_b64())

    def test_signature_present(self):
        p = create_proof(self.ident, 'claim')
        self.assertIn('signature', p)
        self.assertIsInstance(p['signature'], str)
        self.assertGreater(len(p['signature']), 10)

    def test_issued_at_format(self):
        p = create_proof(self.ident, 'claim')
        self.assertRegex(p['issued_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_expires_at_format(self):
        p = create_proof(self.ident, 'claim')
        self.assertRegex(p['expires_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_expires_after_issued(self):
        p = create_proof(self.ident, 'claim')
        self.assertGreater(p['expires_at'], p['issued_at'])

    def test_custom_context(self):
        p = create_proof(self.ident, 'claim', context='example.com/ctx')
        self.assertEqual(p['context'], 'example.com/ctx')

    def test_custom_ttl(self):
        p1 = create_proof(self.ident, 'c', ttl_hours=1)
        p2 = create_proof(self.ident, 'c', ttl_hours=48)
        self.assertLess(p1['expires_at'], p2['expires_at'])


class TestVerifyProof(unittest.TestCase):
    def setUp(self):
        self.ident = DSIdentity('verify-proof-seed')
        self.proof = create_proof(self.ident, 'test claim')

    def test_valid_proof(self):
        ok, reason = verify_proof(self.proof)
        self.assertTrue(ok)
        self.assertEqual(reason, 'valid')

    def test_wrong_type_fails(self):
        bad = dict(self.proof, type='not-a-proof')
        ok, reason = verify_proof(bad)
        self.assertFalse(ok)
        self.assertIn('type', reason)

    def test_tampered_claim_fails(self):
        bad = dict(self.proof, claim='tampered')
        ok, _ = verify_proof(bad)
        self.assertFalse(ok)

    def test_tampered_pubkey_fails(self):
        other = DSIdentity('other-seed')
        bad = dict(self.proof, pubkey=other.public_key_b64())
        ok, _ = verify_proof(bad)
        self.assertFalse(ok)

    def test_expired_proof_fails(self):
        past = dict(self.proof)
        past['expires_at'] = '2000-01-01T00:00:00Z'
        ok, reason = verify_proof(past)
        self.assertFalse(ok)
        self.assertIn('expired', reason)

    def test_malformed_expires_at_fails(self):
        bad = dict(self.proof, expires_at='not-a-date')
        ok, reason = verify_proof(bad)
        self.assertFalse(ok)

    def test_missing_expires_at_fails(self):
        bad = {k: v for k, v in self.proof.items() if k != 'expires_at'}
        ok, reason = verify_proof(bad)
        self.assertFalse(ok)

    def test_missing_signature_fails(self):
        bad = {k: v for k, v in self.proof.items() if k != 'signature'}
        ok, _ = verify_proof(bad)
        self.assertFalse(ok)


class TestCanonical(unittest.TestCase):
    def test_excludes_signature_field(self):
        proof = {'type': 'x', 'claim': 'y', 'signature': 'sig'}
        canon = _canonical(proof)
        self.assertNotIn('signature', canon)

    def test_sorted_keys(self):
        proof = {'z': '1', 'a': '2', 'signature': 'x'}
        canon = _canonical(proof)
        data = json.loads(canon)
        self.assertEqual(list(data.keys()), sorted(data.keys()))

    def test_deterministic(self):
        p = create_proof(DSIdentity('canon-test'), 'claim')
        self.assertEqual(_canonical(p), _canonical(p))


class TestSaveLoadProof(unittest.TestCase):
    def setUp(self):
        self.ident = DSIdentity('saveload-seed')
        self.proof = create_proof(self.ident, 'save-load test')
        fd, self.path = tempfile.mkstemp(suffix='.json')
        os.close(fd)

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_round_trip(self):
        save_proof(self.proof, self.path)
        loaded = load_proof(self.path)
        self.assertEqual(loaded, self.proof)

    def test_saved_file_is_valid_json(self):
        save_proof(self.proof, self.path)
        with open(self.path) as fh:
            parsed = json.load(fh)
        self.assertIsInstance(parsed, dict)

    def test_loaded_proof_verifies(self):
        save_proof(self.proof, self.path)
        loaded = load_proof(self.path)
        ok, reason = verify_proof(loaded)
        self.assertTrue(ok, reason)
