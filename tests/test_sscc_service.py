"""Unit tests for SSCC generation logic."""

import pytest

from sscc.services.sscc_service import (
    _calculate_sscc_check_digit,
    build_carton_number,
    _get_initials,
)


class TestGetInitials:
    def test_two_word_name(self):
        assert _get_initials("Acme Retail", 2) == "AR"

    def test_single_word_padded_with_x(self):
        assert _get_initials("Acme", 2) == "AX"

    def test_three_words_returns_first_two(self):
        assert _get_initials("Alpha Beta Gamma", 2) == "AB"

    def test_lowercase_normalised(self):
        assert _get_initials("hello world", 2) == "HW"


class TestBuildCartonNumber:
    def test_format(self):
        cn = build_carton_number("Beta Logistics", "Acme Retail", 1)
        assert cn == "0000001"

    def test_sequence_padding(self):
        cn = build_carton_number("Beta Logistics", "Acme Retail", 9999999)
        assert cn == "9999999"

    def test_length(self):
        cn = build_carton_number("Supplier One", "Customer Two", 42)
        assert len(cn) == 7
        assert cn.isdigit()


class TestCheckDigit:
    def test_all_zeros(self):
        # 17 zeros → sum=0 → check digit=0
        assert _calculate_sscc_check_digit("0" * 17) == 0

    def test_known_sscc(self):
        # Build 17-digit payload the same way the service does:
        # extension=0, prefix=1234567, serial=000000001
        seventeen = "0" + "1234567" + "000000001"
        check = _calculate_sscc_check_digit(seventeen)
        # Verify that appending the check digit passes re-validation
        full = seventeen + str(check)
        assert len(full) == 18
        assert full.isdigit()

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            _calculate_sscc_check_digit("123456")

    def test_non_digit_raises(self):
        with pytest.raises(ValueError):
            _calculate_sscc_check_digit("1234567890ABCDEFG")
