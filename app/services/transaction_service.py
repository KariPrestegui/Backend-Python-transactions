
import hashlib
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def _generate_idempotency_key(user_id: str, amount: float, tx_type: str) -> str:
    raw = f"{user_id}:{amount}:{tx_type}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_transaction(
    db: Session,
    user_id: str,
    amount: float,
    tx_type: str,
) -> tuple[Transaction, bool]:
    key = _generate_idempotency_key(user_id, amount, tx_type)

# Check for an existing transaction with the same idempotency key
    existing: Optional[Transaction] = (
        db.query(Transaction).filter(Transaction.idempotency_key == key).first()
    )
    if existing:
        logger.info("Returning existing transaction %s", existing.id)
        return existing, False

    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        type=tx_type,
        status="pending",
        idempotency_key=key,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    logger.info("Created transaction %s for user %s", transaction.id, user_id)
    return transaction, True


def get_transaction_by_id(db: Session, transaction_id: UUID) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def update_transaction_status(
    db: Session,
    transaction_id: UUID,
    new_status: str,
) -> Optional[Transaction]:
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        logger.warning("Transaction %s not found for status update", transaction_id)
        return None

    transaction.status = new_status
    db.commit()
    db.refresh(transaction)
    logger.info("Transaction %s status → %s", transaction_id, new_status)
    return transaction


def get_all_transactions(db: Session) -> list[Transaction]:
    return db.query(Transaction).order_by(Transaction.created_at.desc()).all()
