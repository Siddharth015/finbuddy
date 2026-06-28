"""Keyword-based auto categorization for transactions.

Lightweight and dependency-free so it works offline. The AI layer can refine
these later, but this keeps the bot instant and free to run.
"""
from __future__ import annotations

# Ordered roughly by specificity. First matching category wins.
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "food": (
        "zomato", "swiggy", "restaurant", "cafe", "coffee", "starbucks", "pizza",
        "dominos", "mcd", "kfc", "burger", "dinner", "lunch", "breakfast", "snack",
        "food", "eat", "biryani", "dhaba",
    ),
    "groceries": (
        "grocery", "groceries", "bigbasket", "blinkit", "zepto", "dmart", "instamart",
        "vegetables", "milk", "supermarket", "kirana",
    ),
    "transport": (
        "uber", "ola", "rapido", "auto", "cab", "taxi", "metro", "bus", "train",
        "fuel", "petrol", "diesel", "parking", "toll", "fastag",
    ),
    "shopping": (
        "amazon", "flipkart", "myntra", "ajio", "shopping", "clothes", "shoes",
        "mall", "nykaa", "meesho",
    ),
    "entertainment": (
        "netflix", "spotify", "prime", "hotstar", "movie", "cinema", "pvr", "inox",
        "game", "concert", "youtube",
    ),
    "bills": (
        "electricity", "water", "gas", "wifi", "internet", "broadband", "recharge",
        "mobile", "phone", "dth", "bill", "subscription",
    ),
    "rent": ("rent", "maintenance", "society"),
    "health": (
        "pharmacy", "medicine", "apollo", "hospital", "doctor", "clinic", "gym",
        "fitness", "health", "medical", "1mg", "pharmeasy",
    ),
    "travel": (
        "flight", "hotel", "airbnb", "trip", "vacation", "makemytrip", "goibibo",
        "irctc", "booking", "travel", "ticket",
    ),
    "education": (
        "course", "udemy", "coursera", "book", "tuition", "school", "college", "fees",
    ),
    "investment": (
        "sip", "mutual", "stock", "shares", "fd", "gold", "crypto", "bitcoin",
        "invest", "zerodha", "groww",
    ),
    "income": (
        "salary", "income", "refund", "cashback", "interest", "dividend", "bonus",
        "credited",
    ),
}


def categorize(note: str) -> str:
    """Return a category slug for a transaction note, ``"other"`` if unknown."""
    if not note:
        return "other"
    text = note.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def all_categories() -> list[str]:
    return [*_CATEGORY_KEYWORDS.keys(), "other"]
