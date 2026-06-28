from decimal import Decimal

import pytest

from app.models.enums import TxnType
from app.services.parser import ParseError, parse_expense


def test_basic_dash_format():
    parsed = parse_expense("1000-zomato")
    assert parsed.amount == Decimal("1000.00")
    assert parsed.note == "zomato"
    assert parsed.type == TxnType.EXPENSE


def test_space_separated():
    parsed = parse_expense("250 auto")
    assert parsed.amount == Decimal("250.00")
    assert parsed.note == "auto"


def test_income_with_plus():
    parsed = parse_expense("+50000 salary")
    assert parsed.amount == Decimal("50000.00")
    assert parsed.type == TxnType.INCOME


def test_income_by_keyword():
    parsed = parse_expense("interest 1200")
    assert parsed.type == TxnType.INCOME


def test_k_suffix():
    parsed = parse_expense("1.2k groceries")
    assert parsed.amount == Decimal("1200.00")
    assert parsed.note == "groceries"


def test_lakh_suffix():
    parsed = parse_expense("2l flight booking")
    assert parsed.amount == Decimal("200000.00")


def test_note_before_amount():
    parsed = parse_expense("rent 15000")
    assert parsed.amount == Decimal("15000.00")
    assert parsed.note == "rent"


def test_empty_raises():
    with pytest.raises(ParseError):
        parse_expense("   ")


def test_no_amount_raises():
    with pytest.raises(ParseError):
        parse_expense("hello world")
