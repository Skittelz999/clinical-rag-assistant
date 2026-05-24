from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.v1.deps import CurrentUser
from app.schemas.document import DocumentChunksResponse, DocumentResponse
from app.services.document_service import (
    DocumentNotFoundError,
    DocumentProcessingUnexpectedError,
    DocumentStorageError,
    DocumentTooLargeError,
    DocumentValidationError,
    document_service,
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    current_user: CurrentUser,
    file: UploadFile | None = File(default=None),
) -> DocumentResponse:
    try:
        return await document_service.upload_pdf(file)
    except DocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DocumentTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except DocumentStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the uploaded document.",
        ) from exc
    except DocumentProcessingUnexpectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected document processing error.",
        ) from exc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(current_user: CurrentUser) -> list[DocumentResponse]:
    return await document_service.list_documents()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(current_user: CurrentUser, document_id: str) -> DocumentResponse:
    try:
        return await document_service.get_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{document_id}/chunks", response_model=DocumentChunksResponse)
async def list_document_chunks(
    current_user: CurrentUser,
    document_id: str,
) -> DocumentChunksResponse:
    try:
        return await document_service.list_document_chunks(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
