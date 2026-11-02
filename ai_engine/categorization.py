
# FinSight AI - Transaction Categorization

categories = {
    "Food": ["zomato", "swiggy", "restaurant", "dominos"],
    "Shopping": ["amazon", "flipkart", "myntra"],
    "Subscription": ["netflix", "spotify", "prime video"],
    "Transportation": ["uber", "ola", "metro"],
    "Utilities": ["bescom", "electricity", "water bill"],
    "Housing": ["rent", "house rent"],
    "Entertainment": ["bookmyshow", "pvr", "cinema"],
    "Income": ["salary", "income", "credited", "freelance", "refund"]
}


def categorize_transaction(description):

    description = str(description).lower()

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in description:
                return category

    return "Other"


if __name__ == "__main__":
    # Small command-line demonstration; importing this module stays silent.
    transactions = [
        "Zomato payment",
        "Amazon purchase",
        "Netflix subscription",
        "Uber ride",
        "BESCOM electricity bill",
        "House rent",
        "Monthly Salary",
    ]

    for transaction in transactions:
        result = categorize_transaction(transaction)
        print(transaction, "->", result)
