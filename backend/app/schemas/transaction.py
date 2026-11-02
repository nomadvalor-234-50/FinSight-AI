from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):

    description: str = Field(min_length=1, max_length=255)

    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    transaction_type: Literal["income", "expense"]

    category: str | None = None

    transaction_date: date


class TransactionResponse(TransactionCreate):

    id: int

    model_config = ConfigDict(from_attributes=True)