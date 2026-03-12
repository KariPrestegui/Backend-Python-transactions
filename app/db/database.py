import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_env

logger = logging.getLogger(__name__)

DATABASE_URL = get_env("DATABASE_URL", required=True)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import transaction, request_log, user

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
