from fastapi import APIRouter

from app.api.v1.deps import CurrentUser
from app.schemas.chat import ChatRequest, ChatResponse, Citation

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(payload: ChatRequest, current_user: CurrentUser) -> ChatResponse:
    # TODO: call RagService. This placeholder keeps frontend integration simple.
    return ChatResponse(
        answer=(
            "This is a scaffold response. The RAG pipeline will retrieve relevant document chunks, "
            "generate a grounded answer, and attach citations."
        ),
        citations=[
            Citation(
                document_id="demo-document-id",
                title="Demo source",
                page=1,
                snippet="Source snippets will be shown here.",
            )
        ],
    )
