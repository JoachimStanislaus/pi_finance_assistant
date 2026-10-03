import pytest

from smart_query_router import parse_expense_add, route_query
from unittest.mock import patch
from datetime import datetime, timedelta


def test_amount_description_and_date():
    result = parse_expense_add(
        "I spent 23.50 at Tesco yesterday"
    )

    assert result["amount"] == 23.50
    assert result["description"] == "Tesco"
    assert result["date"] == "yesterday"


def test_amount_and_description_without_date():
    result = parse_expense_add(
        "Add 20 groceries"
    )

    assert result["amount"] == 20.00
    assert result["description"] == "groceries"
    assert result["date"] is None


def test_amount_with_comma():
    result = parse_expense_add(
        "Add 1,250.50 for a new laptop"
    )

    assert result["amount"] == 1250.50
    assert result["description"] == "a new laptop"
    assert result["date"] is None


def test_explicit_date():
    result = parse_expense_add(
        "15.50 at Uber on 25/09/2026"
    )

    assert result["amount"] == 15.50
    assert result["description"] == "Uber"
    assert result["date"] == "25/09/2026"


def test_short_date():
    result = parse_expense_add(
        "15.5 at Uber on 25/09/26"
    )

    assert result["amount"] == 15.50
    assert result["description"] == "Uber"
    assert result["date"] == "25/09/2026"


def test_today():
    result = parse_expense_add(
        "I spent 10 at Tesco today"
    )

    assert result["amount"] == 10.00
    assert result["description"] == "Tesco"
    assert result["date"] == "today"


def test_tomorrow():
    result = parse_expense_add(
        "Add 10 for dinner tomorrow"
    )

    assert result["amount"] == 10.00
    assert result["description"] == "dinner"
    assert result["date"] == "tomorrow"


def test_yesterday():
    result = parse_expense_add(
        "I paid 50 for groceries yesterday"
    )

    assert result["amount"] == 50.00
    assert result["description"] == "groceries"
    assert result["date"] == "yesterday"


def test_without_pound_symbol():
    result = parse_expense_add(
        "I spent 23.50 at Tesco"
    )

    assert result["amount"] == 23.50
    assert result["description"] == "Tesco"


def test_integer_amount():
    result = parse_expense_add(
        "I spent 25 at Tesco"
    )

    assert result["amount"] == 25.00
    assert result["description"] == "Tesco"


def test_decimal_with_one_decimal_place():
    result = parse_expense_add(
        "I spent 25.5 at Tesco"
    )

    assert result["amount"] == 25.50
    assert result["description"] == "Tesco"


def test_different_description():
    result = parse_expense_add(
        "Add 45 for dog food"
    )

    assert result["amount"] == 45.00
    assert result["description"] == "dog food"


def test_missing_date():
    result = parse_expense_add(
        "I spent 30 at Amazon"
    )

    assert result["amount"] == 30.00
    assert result["description"] == "Amazon"
    assert result["date"] is None


def test_missing_amount():
    result = parse_expense_add(
        "I spent some money at Tesco yesterday"
    )

    assert result["amount"] is None
    assert result["description"] == "some money Tesco"
    assert result["date"] == "yesterday"


def test_missing_description():
    result = parse_expense_add(
        "Add £20"
    )

    assert result["amount"] == 20.00
    assert result["description"] is None
    assert result["date"] is None


def test_invalid_date():
    result = parse_expense_add(
        "I spent £20 at Tesco on 32/99/2026"
    )

    assert result["amount"] == 20.00
    assert result["description"] == "Tesco"
    assert result["date"] is None


@pytest.mark.parametrize(
    "message, expected_amount",
    [
        ("£5 Tesco", 5.00),
        ("£10.50 Tesco", 10.50),
        ("£100 Tesco", 100.00),
        ("£1,000 Tesco", 1000.00),
        ("£1,500.75 Tesco", 1500.75),
    ]
)
def test_different_amount_formats(message, expected_amount):
    result = parse_expense_add(message)

    assert result["amount"] == expected_amount

def test_route_query_expense_add():
    class MockMessage:
        def __init__(self, text):
            self.text = text
            self.from_user = type('User', (object,), {'first_name': 'TestUser'})()
            self.chat = type('Chat', (object,), {'id': 12345})()
    with patch("expenses.bot.send_message") as mock_send_message, patch("helper.add_data_to_csv", return_value=True) as mock_append_expense:
        message = MockMessage("I spent 23.50 at Tesco yesterday")
        result = route_query(message)
        yesterday_date = (datetime.today() + timedelta(days=-1)).strftime("%-d/%-m/%y")

        assert result["amount"] == 23.50
        assert result["description"] == "Tesco"
        assert result["date"] == yesterday_date