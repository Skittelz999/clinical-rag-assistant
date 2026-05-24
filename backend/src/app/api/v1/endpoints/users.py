from fastapi import APIRouter

from app.api.v1.deps import CurrentUser
from app.schemas.user import CurrentUserResponse

router = APIRouter()


@router.get("/me", response_model=CurrentUserResponse)
async def read_me(current_user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(**current_user)
