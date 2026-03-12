import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.transaction_schema import (
    AsyncProcessResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services import transaction_service
from app.websocket.manager import manager
from app.workers.celery_worker import process_transaction_task
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])

# Create
@router.post("/create", response_model=TransactionResponse)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TransactionResponse:
    try:
        transaction, created = transaction_service.create_transaction(
            db=db,
            user_id=payload.user_id,
            amount=payload.amount,
            tx_type=payload.type,
        )
        if created:
            logger.info("New transaction created: %s", transaction.id)
        else:
            logger.info("Transaction already created %s", transaction.id)
        return transaction
    except Exception as exc:
        logger.exception("Error creating transaction")
        raise HTTPException(status_code=500, detail=str(exc))


# Async with queue
@router.post(
    "/async-process",
    response_model=AsyncProcessResponse,
    status_code=202, #Accepted
)
def async_process_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AsyncProcessResponse:
    try:
        transaction, _ = transaction_service.create_transaction(
            db=db,
            user_id=payload.user_id,
            amount=payload.amount,
            tx_type=payload.type,
        )


        task = process_transaction_task.delay(str(transaction.id))
        manager.pending_tasks[task.id] = str(transaction.id)
        logger.info(
            "Transaction %s enqueued as Celery task %s",
            transaction.id,
            task.id,
        )

        return AsyncProcessResponse(
            transaction_id=transaction.id,
            status=transaction.status,
            task_id=task.id,
        )
    except Exception as exc:
        logger.exception("Error enqueueing transaction")
        raise HTTPException(status_code=500, detail=str(exc))


# Get transactions
@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list:
    return transaction_service.get_all_transactions(db)


@router.websocket("/stream")
async def transaction_stream(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug("Received from WS client: %s", data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
