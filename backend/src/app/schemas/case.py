from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=2)
    note: str = Field(min_length=2)


class CaseResponse(BaseModel):
    id: str
    title: str
    note: str
