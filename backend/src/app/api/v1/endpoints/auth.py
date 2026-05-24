from fastapi import APIRouter

from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    # Demo-only login. Replace with user lookup and password verification.
    token = create_access_token(subject=payload.email)
    return TokenResponse(access_token=token, token_type="bearer")
