
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth_schema import Token, UserCreate, UserResponse
from app.services import auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

_EMAIL_ALREADY_REGISTERED = "is already registered"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error (invalid email, password too short)"},
        500: {"description": "Unexpected server error"},
    },
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = auth_service.register_user(db, payload.email, payload.password)
        return user
    except ValueError as exc:
        msg = str(exc)
        if _EMAIL_ALREADY_REGISTERED in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        logger.exception("Unexpected error during registration")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again")
    except Exception as exc:
        logger.exception("Error during registration")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again")



@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain a JWT access token",
    responses={
        200: {"description": "Authentication successful. Returns a Bearer token"},
        401: {"description": "Incorrect email or password"},
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:

    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(subject=user.email)
    logger.info("User %s logged in", user.email)
    return Token(access_token=token)

