# The goal is to be able to route queries to the appropriate functions based on the content of the query.
from datetime import datetime, timedelta
import re
from enum import Enum

from expenses import get_expense

EXPENSE_KEYWORDS = [
    "expense",
    "expenses",
    "spend",
    "spent",
    "spending",
    "cost",
    "costs",
    "purchase",
    "purchases",
    "bought",
    "buy",
    "groceries",
    "shopping",
    "eating out",
    "bills",
    "transport",
    "rent",
    "mortgage",
]

PORTFOLIO_KEYWORDS = [
    "portfolio",
    "stock",
    "stocks",
    "share",
    "shares",
    "holding",
    "holdings",
    "investment",
    "investments",
    "invested",
    "invest",
    "dividend",
    "dividends",
    "return",
    "returns",
    "p&l",
    "profit",
    "loss",
]

ADD_KEYWORDS = [
    "add",
    "spent",
    "spend",
    "bought",
    "buy",
    "purchase",
    "purchased"
]

QUERY_KEYWORDS = [
    "how much",
    "how many",
    "show",
    "what",
    "list",
    "breakdown",
    "total",
    "expenses",
    "spending"
]

EDIT_KEYWORDS = [
    "edit",
    "change",
    "update",
    "correct",
    "modify"
]

DELETE_KEYWORDS = [
    "delete",
    "remove",
    "cancel"
]

class Route(Enum):
    UNKNOWN = "UNKNOWN"
    EXPENSE = "EXPENSE"
    PORTFOLIO = "PORTFOLIO"

class Expense_Intent(Enum):
    UNKNOWN = "UNKNOWN"
    ADD = "ADD"
    QUERY = "QUERY"
    EDIT = "EDIT"
    DELETE = "DELETE"


def expense_intent_parser(message):

    text = message.text.lower().strip()

    scores = {
        Expense_Intent.ADD: 0,
        Expense_Intent.QUERY: 0,
        Expense_Intent.EDIT: 0,
        Expense_Intent.DELETE: 0
    }

    # Score each intent
    for keyword in ADD_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            scores[Expense_Intent.ADD] += 1

    for keyword in QUERY_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            scores[Expense_Intent.QUERY] += 1

    for keyword in EDIT_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            scores[Expense_Intent.EDIT] += 1

    for keyword in DELETE_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            scores[Expense_Intent.DELETE] += 1

    # Find highest score
    highest_score = max(scores.values())

    if highest_score == 0:
        return Expense_Intent.UNKNOWN

    highest_intents = [
        intent
        for intent, score in scores.items()
        if score == highest_score
    ]

    # Ambiguous request
    if len(highest_intents) > 1:
        return Expense_Intent.UNKNOWN

    return highest_intents[0]

def parse_expense_add(message):
    """
    Extracts amount, description and date from an expense-add message.

    Examples:
        "I spent 23.50 at Tesco yesterday"
        "Add 20 groceries"
        "15.50 at Uber on 25/09/2026"

    Returns:
        {
            "amount": float or None,
            "description": str or None,
            "date": str or None
        }
    """

    text = message.text.strip()

    result = {
        "amount": None,
        "description": None,
        "date": None
    }

    # --------------------------------------------------
    # 1. Extract amount
    # --------------------------------------------------

    amount_pattern = r"£?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)"

    amount_match = re.search(amount_pattern, text)

    if amount_match:
        amount_string = amount_match.group(1)

        # Remove commas
        amount_string = amount_string.replace(",", "")

        result["amount"] = float(amount_string)

    # --------------------------------------------------
    # 2. Extract date
    # --------------------------------------------------

    

    # Explicit relative dates
    relative_dates = {
        "today": 0,
        "yesterday": -1,
        "tomorrow": 1
    }

    for date_word, day_offset in relative_dates.items():
        if re.search(r"\b" + date_word + r"\b", text.lower()):
            result["date"] = (
                datetime.today() + timedelta(days=day_offset)
            ).strftime("%-d/%-m/%y")
            break

    # DD/MM/YYYY or DD/MM/YY
    if result["date"] is None:

        date_pattern = r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b"

        date_match = re.search(date_pattern, text)

        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3))

            if year < 100:
                year += 2000

            try:
                date_object = datetime(year, month, day)
                result["date"] = date_object.strftime("%d/%m/%Y")
            except ValueError:
                # Date format was present but date itself was invalid
                result["date"] = None

    # --------------------------------------------------
    # 3. Extract description
    # --------------------------------------------------

    description = text

    # Remove common command phrases
    description = re.sub(
        r"^\s*(add|record|log)\s+",
        "",
        description,
        flags=re.IGNORECASE
    )

    # Remove amount
    description = re.sub(
        amount_pattern,
        "",
        description,
        flags=re.IGNORECASE
    )

    # Remove date words
    description = re.sub(
        r"\b(today|yesterday|tomorrow)\b",
        "",
        description,
        flags=re.IGNORECASE
    )

    # Remove explicit dates
    description = re.sub(
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        "",
        description
    )

    # Remove common connecting words
    description = re.sub(
        r"\b(i\s+)?(spent|spend|paid|pay)\b",
        "",
        description,
        flags=re.IGNORECASE
    )

    description = re.sub(
        r"\b(at|on|for)\b",
        "",
        description,
        flags=re.IGNORECASE
    )

    # Remove leftover punctuation
    description = re.sub(r"\s*[/,-]\s*", " ", description)

    # Clean whitespace
    description = re.sub(r"\s+", " ", description).strip()

    if description:
        result["description"] = description

    return result

def resolve_expense_query(query):
    resolved_query = {}
    expense_intent = expense_intent_parser(query)
    if expense_intent == Expense_Intent.ADD:
        resolved_query = parse_expense_add(query)
        get_expense(query, resolved_query)
    elif expense_intent == Expense_Intent.EDIT:
        pass
    elif expense_intent == Expense_Intent.QUERY:
        pass
    elif expense_intent == Expense_Intent.DELETE:
        pass
    else:
        return
    return resolved_query


def resolve_portfolio_query(query):
    pass

def route_query(query):
    """
    Main router to route queries -> eventual output func
    """

    parsed_route = route_parser(query)

    if parsed_route == Route.EXPENSE:
        resolved_query = resolve_expense_query(query)
    elif parsed_route == Route.PORTFOLIO:
        resolved_query = resolve_portfolio_query(query)
    else:
        pass
    return resolved_query

def route_parser(message):
    """
    Determines whether a message relates to expenses or portfolio.

    Returns:
        "expense"
        "portfolio"
        "unknown"
    """

    text = message.text.lower().strip()

    expense_score = 0
    portfolio_score = 0

    # Check expense keywords
    for keyword in EXPENSE_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            expense_score += 1

    # Check portfolio keywords
    for keyword in PORTFOLIO_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            portfolio_score += 1

    # Determine route
    if expense_score > portfolio_score:
        return Route.EXPENSE
    elif portfolio_score > expense_score:
        return Route.PORTFOLIO
    else:
        return Route.UNKNOWN