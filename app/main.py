import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import transactions, assistant, auth
from app.db.database import init_db
from app.websocket.manager import manager
from app.workers.celery_worker import celery_app


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def _poll_celery_results() -> None:
    while True:
        try:
            completed = []
            for task_id, tx_id in list(manager.pending_tasks.items()):
                result = celery_app.AsyncResult(task_id)
                if result.ready():
                    status = (
                        result.result.get("status", "unknown")
                        if result.result
                        else "failed"
                    )
                    await manager.broadcast(
                        {
                            "event": "transaction_update",
                            "transaction_id": tx_id,
                            "status": status,
                        }
                    )
                    completed.append(task_id)

            for task_id in completed:
                manager.pending_tasks.pop(task_id, None)

        except Exception:
            logger.debug("Celery poll cycle skipped")

        await asyncio.sleep(2)



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    init_db()
    poll_task = asyncio.create_task(_poll_celery_results())
    logger.info("Application ready")
    yield
    poll_task.cancel()
    logger.info("Application shutting down")



app = FastAPI(
    title="Python project",
    description="Technical test backend Python",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(assistant.router)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok"}
