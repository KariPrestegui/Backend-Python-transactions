
import sys
import time
import random
import logging

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_env

logger = logging.getLogger(__name__)

REDIS_URL = get_env("REDIS_URL", required=True)
DATABASE_URL = get_env("DATABASE_URL", required=True)

celery_app = Celery(
    "workers",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_pool="solo" if sys.platform == "win32" else "prefork",
)

_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@celery_app.task(bind=True, name="process_transaction", max_retries=3)
def process_transaction_task(self, transaction_id: str) -> dict:
    logger.info("Processing transaction %s …", transaction_id)

    # Simulate work
    processing_time = random.uniform(3, 5)
    time.sleep(processing_time)

    # Determine outcome
    new_status = "processed" if random.random() > 0.1 else "failed"

    # Update DB
    db = _SessionLocal()
    try:
        from app.models.transaction import Transaction

        transaction = (
            db.query(Transaction).filter(Transaction.id == transaction_id).first()
        )
        if not transaction:
            logger.error("Transaction %s not found", transaction_id)
            return {"transaction_id": transaction_id, "status": "not_found"}

        transaction.status = new_status
        db.commit()
        logger.info(
            "Transaction %s → %s (%.1fs)",
            transaction_id,
            new_status,
            processing_time,
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Error processing transaction %s", transaction_id)
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()

    return {
        "transaction_id": transaction_id,
        "status": new_status,
        "processing_time": round(processing_time, 2),
    }
