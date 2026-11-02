from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from sqlalchemy.orm import Session

from app.services.recurring_detector import (
    detect_recurring_transactions
)

from pydantic import ValidationError

from app.services.categorizer import categorize_transaction

from decimal import Decimal
import csv
import io


from app.database.connection import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse
)

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"]
)


# Add transaction
@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):

    transaction_data = transaction.model_dump()

    transaction_data["category"] = categorize_transaction(
        description=transaction.description,
        transaction_type=transaction.transaction_type,
        existing_category=transaction.category
    )

    new_transaction = Transaction(
        **transaction_data
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


# Get all transactions
@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db)
):

    transactions = db.query(Transaction).order_by(
        Transaction.transaction_date.desc()
    ).all()

    return transactions


# Delete transaction
@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):

    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }

    
def generate_transaction_fingerprint(transaction):
    """
    Generate a normalized identity for a transaction.
    """

    description = " ".join(
        transaction.description.strip().casefold().split()
    )

    amount = str(
        Decimal(str(transaction.amount)).quantize(
            Decimal("0.01")
        )
    )

    transaction_type = transaction.transaction_type.strip().lower()

    category = (
        transaction.category.strip().casefold()
        if transaction.category
        else ""
    )

    transaction_date = transaction.transaction_date.isoformat()

    return (
        description,
        amount,
        transaction_type,
        category,
        transaction_date
    )
# Upload CSV transactions
@router.post("/upload")
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # 1. Validate file
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed."
        )

    contents = await file.read()

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 5 MB."
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file is empty."
        )

    # 2. Decode CSV
    try:
        decoded_content = contents.decode("utf-8-sig")

        csv_file = io.StringIO(decoded_content)

        reader = csv.DictReader(csv_file)

        if not reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="CSV headers are missing."
            )

        reader.fieldnames = [
            name.strip() for name in reader.fieldnames
        ]

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must use UTF-8 encoding."
        )

    # 3. Check required columns
    required_columns = {
        "description",
        "amount",
        "transaction_type",
        "category",
        "transaction_date"
    }

    missing_columns = required_columns - set(reader.fieldnames)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Required CSV columns are missing.",
                "missing_columns": sorted(missing_columns)
            }
        )

    # 4. Load existing transaction fingerprints
    existing_transactions = db.query(Transaction).all()

    seen_fingerprints = {
        generate_transaction_fingerprint(transaction)
        for transaction in existing_transactions
    }

    new_transactions = []

    imported_count = 0
    duplicate_count = 0
    row_count = 0

    # 5. Validate and process CSV rows
    try:

        for row_number, row in enumerate(reader, start=2):

            if not any(
                value and value.strip()
                for value in row.values()
                if isinstance(value, str)
            ):
                continue

            row_count += 1

            if row_count > 5000:
                raise HTTPException(
                    status_code=400,
                    detail="Maximum 5000 transactions allowed."
                )

            cleaned_row = {
                key.strip(): value.strip()
                if isinstance(value, str)
                else value
                for key, value in row.items()
                if key is not None
            }

            if cleaned_row.get("transaction_type"):
                cleaned_row["transaction_type"] = (
                    cleaned_row["transaction_type"].lower()
                )

            if not cleaned_row.get("category"):
                cleaned_row["category"] = None

            # Validate transaction
            validated_data = TransactionCreate.model_validate(
                cleaned_row
            )
            # Automatically categorize transaction
            categorized_data = validated_data.model_copy(
                update={
                    "category": categorize_transaction(
                        description=validated_data.description,
                        transaction_type=validated_data.transaction_type,
                        existing_category=validated_data.category
                    )
                }
            )

            # Generate fingerprint
            fingerprint = generate_transaction_fingerprint(
                categorized_data
            )

            # 6. Check duplicates
            if fingerprint in seen_fingerprints:
                duplicate_count += 1
                continue

            # 7. Add new transaction
            transaction = Transaction(
                **categorized_data.model_dump()
            )

            new_transactions.append(transaction)

            # Prevent duplicates within the same CSV
            seen_fingerprints.add(fingerprint)

            imported_count += 1

        # 8. Save new transactions
        if new_transactions:
            db.add_all(new_transactions)
            db.commit()

    except ValidationError as error:

        db.rollback()

        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid transaction data in CSV.",
                "errors": error.errors(include_input=False)
            }
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to import transactions."
        )

    # 9. Return import report
    return {
        "message": "CSV processing completed successfully.",
        "filename": file.filename,
        "total_rows_processed": row_count,
        "imported": imported_count,
        "duplicates_skipped": duplicate_count,
        "status": "success"
    }
@router.get("/recurring")
def get_recurring_transactions(
    db: Session = Depends(get_db)
):

    # Retrieve all transactions
    transactions = (
        db.query(Transaction)
        .all()
    )

    # Detect recurring payments
    recurring_payments = (
        detect_recurring_transactions(transactions)
    )

    return {
        "message": "Recurring payment analysis completed.",
        "total_recurring": len(recurring_payments),
        "recurring_payments": recurring_payments
    }