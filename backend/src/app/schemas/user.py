from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    id: str
    role: str
    organization_id: str
