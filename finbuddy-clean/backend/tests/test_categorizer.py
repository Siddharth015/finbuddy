from app.services.categorizer import categorize


def test_food():
    assert categorize("zomato dinner") == "food"


def test_transport():
    assert categorize("uber to office") == "transport"


def test_groceries():
    assert categorize("blinkit milk") == "groceries"


def test_unknown_is_other():
    assert categorize("random thing") == "other"


def test_empty_is_other():
    assert categorize("") == "other"
