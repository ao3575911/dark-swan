"""Tests for ds_cli.py — argument parsing and validation."""
import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_cli import build_parser, cmd_search, _VALID_CLASSES
from ds_protocol_core import DSIdentity
from ds_registry import DSRegistry


def _tmp_registry() -> tuple:
    tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    tmp.close()
    os.unlink(tmp.name)
    reg = DSRegistry(tmp.name)
    ident = DSIdentity('cli-test-seed')
    reg.commit(ident.public_key_b64(), ident.ephemeral_handle())
    return reg, tmp.name


class TestSearchValidation(unittest.TestCase):
    def setUp(self):
        self.reg, self.path = _tmp_registry()

    def tearDown(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def _run_search(self, extra_args: list) -> int:
        """Run ds search with extra_args; return exit code."""
        parser = build_parser()
        args = parser.parse_args(['--registry', self.path, '--no-color', 'search'] + extra_args)
        try:
            cmd_search(args, en=False)
            return 0
        except SystemExit as exc:
            return int(exc.code)

    def test_dr_valid_boundary_low(self):
        self.assertEqual(self._run_search(['--dr', '1']), 0)

    def test_dr_valid_boundary_high(self):
        self.assertEqual(self._run_search(['--dr', '9']), 0)

    def test_dr_zero_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--dr', '0']), 0)

    def test_dr_ten_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--dr', '10']), 0)

    def test_dr_negative_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--dr', '-1']), 0)

    def test_class_idempotent_valid(self):
        self.assertEqual(self._run_search(['--class', 'idempotent']), 0)

    def test_class_biphasic_valid(self):
        self.assertEqual(self._run_search(['--class', 'biphasic']), 0)

    def test_class_involutive_valid(self):
        self.assertEqual(self._run_search(['--class', 'involutive']), 0)

    def test_class_asymmetric_valid(self):
        self.assertEqual(self._run_search(['--class', 'asymmetric']), 0)

    def test_class_invalid_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--class', 'badclass']), 0)

    def test_class_mixed_exits_nonzero(self):
        # 'mixed' appears in profile output but is not a valid search class
        self.assertNotEqual(self._run_search(['--class', 'mixed']), 0)

    def test_energy_range_valid(self):
        self.assertEqual(self._run_search(['--energy-range', '0,100']), 0)

    def test_energy_range_equal_low_high_valid(self):
        self.assertEqual(self._run_search(['--energy-range', '50,50']), 0)

    def test_energy_range_inverted_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--energy-range', '50,10']), 0)

    def test_energy_range_malformed_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--energy-range', 'notanumber']), 0)

    def test_energy_range_missing_comma_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--energy-range', '1020']), 0)

    def test_energy_range_three_parts_exits_nonzero(self):
        self.assertNotEqual(self._run_search(['--energy-range', '10,20,30']), 0)


class TestValidClassesConstant(unittest.TestCase):
    def test_all_four_classes_present(self):
        self.assertIn('idempotent',  _VALID_CLASSES)
        self.assertIn('biphasic',    _VALID_CLASSES)
        self.assertIn('involutive',  _VALID_CLASSES)
        self.assertIn('asymmetric',  _VALID_CLASSES)

    def test_no_extra_classes(self):
        self.assertEqual(len(_VALID_CLASSES), 4)
