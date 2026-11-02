import re


EXPENSE_RULES = {
    "Food": [
        "zomato", "swiggy", "restaurant",
        "food", "cafe", "dominos", "pizza",
        "mcdonald", "kfc", "instamart"
    ],

    "Transportation": [
        "uber", "ola", "rapido", "metro",
        "bus", "train", "petrol", "fuel",
        "irctc", "flight"
    ],

    "Subscription": [
        "netflix", "spotify", "prime video",
        "hotstar", "youtube premium",
        "subscription", "membership"
    ],

    "Shopping": [
        "amazon", "flipkart", "myntra",
        "meesho", "shopping", "mall"
    ],

    "Utilities": [
        "electricity", "bescom", "bill",
        "water", "broadband", "internet",
        "recharge", "gas"
    ],

    "Healthcare": [
        "hospital", "pharmacy", "medical",
        "doctor", "apollo", "medicine"
    ],

    "Entertainment": [
        "movie", "cinema", "bookmyshow",
        "game", "entertainment"
    ],

    "Rent": [
        "rent", "house rent", "maintenance"
    ]
}


INCOME_RULES = {
    "Salary": [
        "salary", "payroll", "monthly salary"
    ],

    "Freelance": [
        "freelance", "client payment",
        "project payment"
    ],

    "Interest": [
        "interest", "fixed deposit",
        "fd interest"
    ],

    "Business Income": [
        "business income", "sales revenue",
        "customer payment"
    ]
}


def contains_keyword(description, keyword):

    pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"

    return re.search(
        pattern,
        description,
        flags=re.IGNORECASE
    ) is not None


def categorize_transaction(
    description,
    transaction_type,
    existing_category=None
):
    """
    Categorize a transaction using keyword matching.

    Preserve an existing category if one was supplied.
    """

    if existing_category and existing_category.strip():
        return existing_category.strip()

    description = description.strip().casefold()

    if transaction_type == "income":

        for category, keywords in INCOME_RULES.items():

            if any(
                contains_keyword(description, keyword)
                for keyword in keywords
            ):
                return category

        return "Other Income"

    for category, keywords in EXPENSE_RULES.items():

        if any(
            contains_keyword(description, keyword)
            for keyword in keywords
        ):
            return category

    return "Other"