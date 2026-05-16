"""Tests for ds_registry.py — DSRegistry CRUD and search."""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_protocol_core import DSIdentity
from ds_registry import DSRegistry


class TestRegistryRobustness(unittest.TestCase):
    """Registry must survive edge-case file states."""

    def _tmp(self) -> str:
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        return path

    def test_empty_file_loads_without_crash(self):
        path = self._tmp()
        # file exists but is empty
        open(path, 'w').close()
        try:
            reg = DSRegistry(path)
            self.assertEqual(reg.count(), 0)
        finally:
            os.unlink(path)

    def test_whitespace_only_file_loads_without_crash(self):
        path = self._tmp()
        with open(path, 'w') as fh:
            fh.write('   \n\t\n')
        try:
            reg = DSRegistry(path)
            self.assertEqual(reg.count(), 0)
        finally:
            os.unlink(path)

    def test_malformed_json_raises_value_error(self):
        path = self._tmp()
        with open(path, 'w') as fh:
            fh.write('{"bad":')
        try:
            with self.assertRaises(ValueError):
                DSRegistry(path)
        finally:
            os.unlink(path)

    def test_truncated_json_raises_value_error(self):
        path = self._tmp()
        with open(path, 'w') as fh:
            fh.write('{"key": "val"')
        try:
            with self.assertRaises(ValueError):
                DSRegistry(path)
        finally:
            os.unlink(path)


def _make_registry() -> tuple:
    """Return (registry, tmp_path) backed by a temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    tmp.close()
    os.unlink(tmp.name)          # let DSRegistry create it fresh
    return DSRegistry(tmp.name), tmp.name


class TestRegistryCommit(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _make_registry()
        self.ident = DSIdentity('registry-commit-test')

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_commit_returns_record(self):
        rec = self.reg.commit(self.ident.public_key_b64(), 'ds-TEST')
        self.assertEqual(rec['symbolic_id'], self.ident.symbolic_id)

    def test_commit_persists(self):
        self.reg.commit(self.ident.public_key_b64(), 'ds-TEST')
        reg2 = DSRegistry(self.path)
        self.assertIsNotNone(reg2.resolve(self.ident.symbolic_id))

    def test_duplicate_raises(self):
        self.reg.commit(self.ident.public_key_b64(), 'ds-A')
        with self.assertRaises(ValueError):
            self.reg.commit(self.ident.public_key_b64(), 'ds-B')

    def test_overwrite_allowed(self):
        self.reg.commit(self.ident.public_key_b64(), 'ds-A')
        rec = self.reg.commit(self.ident.public_key_b64(), 'ds-B', overwrite=True)
        self.assertEqual(rec['handle'], 'ds-B')

    def test_record_has_profile(self):
        rec = self.reg.commit(self.ident.public_key_b64(), 'ds-TEST')
        self.assertIn('profile', rec)
        self.assertIn('digital_root', rec['profile'])
        self.assertIn('dominant_class', rec['profile'])

    def test_count_increments(self):
        self.assertEqual(self.reg.count(), 0)
        self.reg.commit(self.ident.public_key_b64(), 'ds-TEST')
        self.assertEqual(self.reg.count(), 1)


class TestRegistryResolve(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _make_registry()
        self.ident = DSIdentity('registry-resolve-test')
        self.reg.commit(self.ident.public_key_b64(), 'ds-ABCD')

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_resolve_by_symbolic_id(self):
        rec = self.reg.resolve(self.ident.symbolic_id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec['symbolic_id'], self.ident.symbolic_id)

    def test_resolve_missing_returns_none(self):
        self.assertIsNone(self.reg.resolve('ZZZZ'))

    def test_resolve_by_handle(self):
        rec = self.reg.resolve_by_handle('ds-ABCD')
        self.assertIsNotNone(rec)

    def test_resolve_by_handle_missing(self):
        self.assertIsNone(self.reg.resolve_by_handle('ds-XXXX'))


class TestRegistrySearch(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _make_registry()
        # Register several identities
        seeds = ['alpha', 'beta', 'gamma', 'delta', 'epsilon']
        self.idents = [DSIdentity(s) for s in seeds]
        for i, ident in enumerate(self.idents):
            self.reg.commit(ident.public_key_b64(), f'ds-H{i:03d}', overwrite=True)

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_search_by_dr_valid_range(self):
        for dr in range(1, 10):
            results = self.reg.search_by_dr(dr)
            for r in results:
                self.assertEqual(r['profile']['digital_root'], dr)

    def test_search_by_dr_all_accounted(self):
        total = sum(len(self.reg.search_by_dr(dr)) for dr in range(1, 10))
        self.assertEqual(total, self.reg.count())

    def test_search_by_class_valid(self):
        for cls in ('idempotent', 'biphasic', 'involutive', 'asymmetric'):
            results = self.reg.search_by_class(cls)
            for r in results:
                self.assertEqual(r['profile']['dominant_class'], cls)

    def test_search_by_energy_range(self):
        results = self.reg.search_by_energy_range(0, 1000)
        self.assertEqual(len(results), self.reg.count())

    def test_search_by_energy_range_narrow(self):
        results = self.reg.search_by_energy_range(-1, -0.5)
        # May be empty, but should not error
        self.assertIsInstance(results, list)

    def test_all_records(self):
        self.assertEqual(len(self.reg.all_records()), self.reg.count())


class TestRegistryVerification(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _make_registry()
        self.ident = DSIdentity('verify-test')
        self.reg.commit(self.ident.public_key_b64(), 'ds-VRF')

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_verify_record_valid(self):
        msg = 'verify this'
        sig = self.ident.sign(msg)
        self.assertTrue(self.reg.verify_record(self.ident.symbolic_id, msg, sig))

    def test_verify_record_wrong_msg(self):
        msg = 'verify this'
        sig = self.ident.sign(msg)
        self.assertFalse(self.reg.verify_record(self.ident.symbolic_id, 'wrong', sig))

    def test_verify_record_missing_id(self):
        self.assertFalse(self.reg.verify_record('ZZZZ', 'msg', 'sig'))

    def test_verify_pubkey_matches(self):
        self.assertTrue(
            self.reg.verify_pubkey_matches(
                self.ident.symbolic_id,
                self.ident.public_key_b64()
            )
        )

    def test_verify_pubkey_wrong_key(self):
        other = DSIdentity('other-seed')
        self.assertFalse(
            self.reg.verify_pubkey_matches(
                self.ident.symbolic_id,
                other.public_key_b64()
            )
        )


class TestRegistryUpdateRemove(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _make_registry()
        self.ident = DSIdentity('update-remove-test')
        self.reg.commit(self.ident.public_key_b64(), 'ds-OLD')

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_update_handle(self):
        self.reg.update_handle(self.ident.symbolic_id, 'ds-NEW')
        rec = self.reg.resolve(self.ident.symbolic_id)
        self.assertEqual(rec['handle'], 'ds-NEW')

    def test_update_handle_missing_raises(self):
        with self.assertRaises(KeyError):
            self.reg.update_handle('ZZZZ', 'ds-X')

    def test_remove(self):
        self.reg.remove(self.ident.symbolic_id)
        self.assertIsNone(self.reg.resolve(self.ident.symbolic_id))
        self.assertEqual(self.reg.count(), 0)

    def test_remove_missing_no_error(self):
        self.reg.remove('ZZZZ')   # should not raise
