from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.transaction import Transaction

from fastapi import Query

from app.services.cashflow_forecaster import (
    forecast_cash_flow
)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def get_financial_summary(
    db: Session = Depends(get_db)
):

    # Calculate total income
    total_income = (
        db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        )
        .filter(Transaction.transaction_type == "income")
        .scalar()
    )

    # Calculate total expenses
    total_expenses = (
        db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        )
        .filter(Transaction.transaction_type == "expense")
        .scalar()
    )

    # Calculate total number of transactions
    total_transactions = (
        db.query(func.count(Transaction.id)).scalar()
    )

    # Calculate net cash flow
    net_cash_flow = total_income - total_expenses

    # Calculate category-wise expenses
    category_data = (
        db.query(
            func.coalesce(
                Transaction.category,
                "Uncategorized"
            ).label("category"),
            func.sum(Transaction.amount).label("total")
        )
        .filter(Transaction.transaction_type == "expense")
        .group_by(Transaction.category)
        .all()
    )

    expense_categories = [
        {
            "category": category,
            "amount": amount
        }
        for category, amount in category_data
    ]

    return {
        "currency": "INR",
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "total_transactions": total_transactions,
        "expense_categories": expense_categories
    }

@router.get("/forecast")
def get_cash_flow_forecast(
    starting_balance: float,
    days: int = Query(default=60, ge=1, le=365),
    db: Session = Depends(get_db)
):

    # Retrieve all transactions
    transactions = (
        db.query(Transaction)
        .all()
    )

    # Generate financial forecast
    forecast = forecast_cash_flow(
        transactions=transactions,
        starting_balance=starting_balance,
        forecast_days=days
    )

    return forecast