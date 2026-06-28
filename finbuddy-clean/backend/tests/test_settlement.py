from decimal import Decimal

from app.services.settlement import minimal_transfers


def test_simple_two_person_settlement():
    # User 1 is owed 500, user 2 owes 500.
    balances = {1: Decimal("500.00"), 2: Decimal("-500.00")}
    transfers = minimal_transfers(balances)
    assert transfers == [(2, 1, Decimal("500.00"))]


def test_balanced_has_no_transfers():
    balances = {1: Decimal("0.00"), 2: Decimal("0.00")}
    assert minimal_transfers(balances) == []


def test_three_person_settlement_conserves_money():
    balances = {1: Decimal("300.00"), 2: Decimal("-100.00"), 3: Decimal("-200.00")}
    transfers = minimal_transfers(balances)
    total_to_creditor = sum(amt for _, to, amt in transfers if to == 1)
    assert total_to_creditor == Decimal("300.00")
