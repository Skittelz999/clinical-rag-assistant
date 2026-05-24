from fastapi import APIRouter

from app.api.v1.deps import CurrentUser
from app.schemas.case import CaseCreate, CaseResponse

router = APIRouter()


@router.post("", response_model=CaseResponse)
async def create_case(payload: CaseCreate, current_user: CurrentUser) -> CaseResponse:
    return CaseResponse(id="demo-case-id", title=payload.title, note=payload.note)


@router.get("", response_model=list[CaseResponse])
async def list_cases(current_user: CurrentUser) -> list[CaseResponse]:
    return []
