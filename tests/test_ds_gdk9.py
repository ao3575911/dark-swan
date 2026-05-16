"""Tests for ds_gdk9.py — GDk9 symbolic bridge."""
import sys
import os
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ds_gdk9 import (
    bytes_to_word,
    pubkey_to_symbolic_id,
    symbolic_id_profile,
    derive_handle,
    _sym_class,
    _sym_energy,
    _digital_root,
)


class TestBytesToWord(unittest.TestCase):
    def test_length(self):
        self.assertEqual(len(bytes_to_word(b'\x00' * 4, 4)), 4)
        self.assertEqual(len(bytes_to_word(b'\x00' * 8, 8)), 8)

    def test_all_uppercase_alpha(self):
        word = bytes_to_word(os.urandom(16), 4)
        self.assertTrue(word.isupper())
        self.assertTrue(word.isalpha())

    def test_zero_bytes_is_A(self):
        self.assertEqual(bytes_to_word(b'\x00\x00\x00\x00', 4), 'AAAA')

    def test_modulo_wraps(self):
        # 26 % 26 == 0 → 'A'
        self.assertEqual(bytes_to_word(bytes([26]), 1), 'A')
        # 27 % 26 == 1 → 'B'
        self.assertEqual(bytes_to_word(bytes([27]), 1), 'B')


class TestPubkeyToSymbolicId(unittest.TestCase):
    def test_deterministic(self):
        raw = os.urandom(32)
        self.assertEqual(pubkey_to_symbolic_id(raw), pubkey_to_symbolic_id(raw))

    def test_length_4(self):
        raw = os.urandom(32)
        sid = pubkey_to_symbolic_id(raw)
        self.assertEqual(len(sid), 4)
        self.assertTrue(sid.isupper())

    def test_different_keys_different_ids(self):
        a = pubkey_to_symbolic_id(b'\x00' * 32)
        b = pubkey_to_symbolic_id(b'\xff' * 32)
        self.assertNotEqual(a, b)


class TestSymbolicIdProfile(unittest.TestCase):
    def test_keys_present(self):
        p = symbolic_id_profile('FWEM')
        for key in ('word', 'total_energy', 'digital_root', 'dominant_class',
                    'class_counts', 'steps'):
            self.assertIn(key, p)

    def test_word_uppercased(self):
        self.assertEqual(symbolic_id_profile('fwem')['word'], 'FWEM')

    def test_step_count(self):
        p = symbolic_id_profile('FWEM')
        self.assertEqual(len(p['steps']), 4)

    def test_dr_in_range(self):
        p = symbolic_id_profile('FWEM')
        self.assertIn(p['digital_root'], range(1, 10))

    def test_fwem_energy_approx(self):
        p = symbolic_id_profile('FWEM')
        self.assertAlmostEqual(p['total_energy'], 42.04, places=1)

    def test_dominant_class_is_valid(self):
        valid = {'idempotent', 'biphasic', 'involutive', 'asymmetric', 'mixed'}
        p = symbolic_id_profile('FWEM')
        self.assertIn(p['dominant_class'], valid)


class TestSymClass(unittest.TestCase):
    def test_known_classes(self):
        self.assertEqual(_sym_class('A'), 'idempotent')
        self.assertEqual(_sym_class('B'), 'biphasic')
        self.assertEqual(_sym_class('N'), 'involutive')
        self.assertEqual(_sym_class('F'), 'asymmetric')

    def test_lowercase_same(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            self.assertEqual(_sym_class(ch), _sym_class(ch.upper()))

    def test_non_alpha_none(self):
        self.assertIsNone(_sym_class('1'))
        self.assertIsNone(_sym_class(' '))


class TestSymEnergy(unittest.TestCase):
    def test_idempotent(self):
        self.assertAlmostEqual(_sym_energy('A'), 1.0)

    def test_biphasic(self):
        self.assertAlmostEqual(_sym_energy('E'), math.sin(5), places=10)

    def test_involutive(self):
        self.assertAlmostEqual(_sym_energy('N'), 1.0 / 14.0, places=10)

    def test_asymmetric(self):
        self.assertAlmostEqual(_sym_energy('F'), 7.0)

    def test_non_alpha_zero(self):
        self.assertEqual(_sym_energy(' '), 0.0)


class TestDigitalRoot(unittest.TestCase):
    def test_single_digits(self):
        for n in range(1, 10):
            self.assertEqual(_digital_root(n), n)

    def test_nine_returns_nine(self):
        self.assertEqual(_digital_root(9), 9)
        self.assertEqual(_digital_root(18), 9)
        self.assertEqual(_digital_root(27), 9)

    def test_multi_digit(self):
        self.assertEqual(_digital_root(10), 1)
        self.assertEqual(_digital_root(11), 2)
        self.assertEqual(_digital_root(99), 9)

    def test_zero_or_negative(self):
        self.assertEqual(_digital_root(0), 9)


class TestDeriveHandle(unittest.TestCase):
    def test_format(self):
        h = derive_handle('FWEM', 0)
        self.assertTrue(h.startswith('ds-'))
        self.assertEqual(len(h), 7)  # ds- + 4 letters

    def test_deterministic(self):
        self.assertEqual(derive_handle('FWEM', 42), derive_handle('FWEM', 42))

    def test_rotates_daily(self):
        self.assertNotEqual(derive_handle('FWEM', 0), derive_handle('FWEM', 1))

    def test_different_ids_different_handles(self):
        self.assertNotEqual(derive_handle('FWEM', 0), derive_handle('ABCD', 0))
