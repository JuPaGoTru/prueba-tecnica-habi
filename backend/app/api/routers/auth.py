from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.application.dtos import LoginInputDTO, RegisterInputDTO, TokenOutputDTO
from app.application.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.repositories import UserRepository
from app.api.dependencies import get_user_repository

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenOutputDTO, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterInputDTO,
    repo: UserRepository = Depends(get_user_repository),
):
    try:
        return await RegisterUserUseCase(repo).execute(body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenOutputDTO)
async def login(
    body: LoginInputDTO,
    repo: UserRepository = Depends(get_user_repository),
):
    try:
        return await LoginUserUseCase(repo).execute(body)
    except (InvalidCredentialsError, InactiveUserError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenOutputDTO)
async def refresh(
    body: RefreshRequest,
    repo: UserRepository = Depends(get_user_repository),
):
    try:
        return await RefreshTokenUseCase(repo).execute(body.refresh_token)
    except (InvalidTokenError, InactiveUserError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
