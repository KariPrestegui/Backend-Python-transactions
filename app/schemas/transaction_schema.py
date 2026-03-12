from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    # Fields created with Pydantic's Field to include validation rules
    user_id: str = Field(..., min_length=1, max_length=100, examples=["user-123"])
    amount: float = Field(..., gt=0, examples=[150.75])
    type: str = Field(..., min_length=1, max_length=50, examples=["deposit"])


class SummarizeRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=50_000, examples=["Long article text…"]
    )


class TransactionResponse(BaseModel):
    id: UUID
    user_id: str
    amount: float
    type: str
    status: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SummarizeResponse(BaseModel):
    summary: str
    model_used: str
    request_id: UUID

    model_config = {"from_attributes": True}


class AsyncProcessResponse(BaseModel):
    transaction_id: UUID
    status: str = "pending"
    task_id: str
    message: str = "Transaction queued for processing"


class ErrorResponse(BaseModel):
    detail: str
