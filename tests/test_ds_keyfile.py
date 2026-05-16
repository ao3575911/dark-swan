"""Tests for random Ed25519 key files and key-file CLI commands."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_protocol_core import DSIdentity

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CLI = os.path.join(ROOT, 'ds_cli.py')


class TestKeyfileAPI(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.pem')
        os.close(fd)
        os.unlink(self.path)

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_generate_random_identities_are_distinct(self):
        a = DSIdentity.generate_random()
        b = DSIdentity.generate_random()
        self.assertNotEqual(a.did, b.did)
        self.assertNotEqual(a.public_key_b64(), b.public_key_b64())

    def test_save_load_encrypted_keyfile_round_trip(self):
        ident = DSIdentity.generate_random()
        ident.save_keyfile(self.path, 'correct horse battery staple')
        loaded = DSIdentity.load_keyfile(self.path, 'correct horse battery staple')
        self.assertEqual(loaded.did, ident.did)
        sig = loaded.sign('hello keyfile')
        self.assertTrue(ident.verify('hello keyfile', sig))

    def test_encrypted_keyfile_requires_passphrase(self):
        ident = DSIdentity.generate_random()
        ident.save_keyfile(self.path, 'secret')
        with self.assertRaises(Exception):
            DSIdentity.load_keyfile(self.path)

    def test_save_load_unencrypted_keyfile_round_trip(self):
        ident = DSIdentity.generate_random()
        ident.save_keyfile(self.path)
        loaded = DSIdentity.load_keyfile(self.path)
        self.assertEqual(loaded.did, ident.did)


class TestKeyfileCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.key_path = os.path.join(self.tmpdir.name, 'id.pem')
        self.proof_path = os.path.join(self.tmpdir.name, 'proof.json')
        self.registry_path = os.path.join(self.tmpdir.name, 'registry.json')

    def tearDown(self):
        self.tmpdir.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, CLI, '--no-color', *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def test_keygen_and_generate_key(self):
        self.run_cli('--json', 'keygen', '--output', self.key_path, '--passphrase', 'pw')
        out = self.run_cli('--json', 'generate-key', self.key_path, '--passphrase', 'pw').stdout
        data = json.loads(out[out.index('{') :])
        self.assertRegex(data['did'], r'^did:ds:[0-9a-f]{32}$')

    def test_sign_key_verify_and_publish_lookup(self):
        self.run_cli('keygen', '--output', self.key_path, '--passphrase', 'pw')
        signed = self.run_cli(
            '--json', 'sign-key', self.key_path, 'msg', '--passphrase', 'pw'
        ).stdout
        data = json.loads(signed[signed.index('{') :])
        self.run_cli('verify', data['pubkey_b64'], 'msg', data['signature'])
        self.run_cli(
            '--registry', self.registry_path, 'publish-key', self.key_path, '--passphrase', 'pw'
        )
        lookup = self.run_cli('--registry', self.registry_path, 'lookup', data['did']).stdout
        self.assertIn(data['id'], lookup)

    def test_proof_create_key_and_verify(self):
        self.run_cli('keygen', '--output', self.key_path, '--passphrase', 'pw')
        self.run_cli(
            'proof',
            'create-key',
            self.key_path,
            '--passphrase',
            'pw',
            '--claim',
            'keyfile proof',
            '-o',
            self.proof_path,
        )
        self.run_cli('proof', 'verify', self.proof_path)

    def test_keygen_requires_encryption_choice(self):
        proc = subprocess.run(
            [sys.executable, CLI, '--no-color', 'keygen', '--output', self.key_path],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('requires --passphrase', proc.stderr)
