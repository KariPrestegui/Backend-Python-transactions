import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.transaction_schema import SummarizeRequest, SummarizeResponse
from app.services import ai_service
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummarizeResponse:
    try:
        result = await ai_service.summarize_text(db=db, text=payload.text)
        return SummarizeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
