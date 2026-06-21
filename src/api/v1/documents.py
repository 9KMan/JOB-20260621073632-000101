// src/api/v1/documents.py
"""Document management endpoints."""
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_active_user, require_role
from src.api.schemas.common import PaginatedResponse, PaginationParams
from src.api.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
)
from src.database import get_async_session
from src.models.document import Document, DocumentLine, DocumentStatus, DocumentType
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Document",
    description="Create a new document (PO, Invoice, or Delivery Note)",
)
async def create_document(
    document_data: DocumentCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_role("admin", "accountant"))],
) -> Document:
    """
    Create a new document.

    Args:
        document_data: Document creation data
        session: Database session
        current_user: Current authenticated user

    Returns:
        Document: Created document
    """
    # Create document
    document = Document(
        document_number=document_data.document_number,
        document_type=document_data.document_type,
        supplier_code=document_data.supplier_code,
        supplier_name=document_data.supplier_name,
        supplier_reference=document_data.supplier_reference,
        document_date=document_data.document_date,
        due_date=document_data.due_date,
        delivery_date=document_data.delivery_date,
        currency=document_data.currency,
        notes=document_data.notes,
        metadata_json=document_data.metadata_json,
        subtotal=document_data.subtotal,
        tax_amount=document_data.tax_amount,
        total_amount=document_data.total_amount,
        remaining_balance=document_data.total_amount,
    )

    session.add(document)
    await session.flush()

    # Create document lines
    for line_data in document_data.lines:
        line = DocumentLine(
            document_id=document.id,
            line_number=line_data.line_number,
            external_line_reference=line_data.external_line_reference,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            linked_po_line_id=line_data.linked_po_line_id,
        )
        session.add(line)

    await session.commit()
    await session.refresh(document)

    logger.info(f"Document created: {document.document_number}")
    return document


@router.get(
    "/",
    response_model=PaginatedResponse[DocumentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Documents",
    description="List all documents with pagination and filtering",
)
async def list_documents(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    pagination: PaginationParams = Depends(),
    document_type: DocumentType | None = Query(default=None, description="Filter by document type"),
    status_filter: DocumentStatus | None = Query(default=None, alias="status", description="Filter by status"),
    supplier_code: str | None = Query(default=None, description="Filter by supplier code"),
    date_from: str | None = Query(default=None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: str | None = Query(default=None, description="Filter by date to (YYYY-MM-DD)"),
) -> PaginatedResponse[DocumentListResponse]:
    """
    List documents with pagination and filtering.

    Args:
        session: Database session
        current_user: Current authenticated user
        pagination: Pagination parameters
        document_type: Filter by document type
        status_filter: Filter by status
        supplier_code: Filter by supplier code
        date_from: Filter by date from
        date_to: Filter by date to

    Returns:
        PaginatedResponse: Paginated document list
    """
    query = select(Document).where(Document.is_deleted == False)

    # Apply filters
    if document_type:
        query = query.where(Document.document_type == document_type)

    if status_filter:
        query = query.where(Document.status == status_filter)

    if supplier_code:
        query = query.where(Document.supplier_code == supplier_code)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Document.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)

    result = await session.execute(query)
    documents = result.scalars().all()

    return PaginatedResponse.create(
        items=[DocumentListResponse.model_validate(doc) for doc in documents],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document",
    description="Get a document by ID",
)
async def get_document(
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Document:
    """
    Get a document by ID.

    Args:
        document_id: Document ID
        session: Database session
        current_user: Current authenticated user

    Returns:
        Document: Document
    """
    result = await session.execute(
        select(Document)
        .options(selectinload(Document.lines))
        .where(Document.id == document_id, Document.is_deleted == False)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Document",
    description="Update a document",
)
async def update_document(
    document_id: uuid.UUID,
    document_data: DocumentUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_role("admin", "accountant"))],
) -> Document:
    """
    Update a document.

    Args:
        document_id: Document ID
        document_data: Update data
        session: Database session
        current_user: Current authenticated user

    Returns:
        Document: Updated document
    """
    result = await session.execute(
        select(Document)
        .options(selectinload(Document.lines))
        .where(Document.id == document_id, Document.is_deleted == False)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    await session.commit()
    await session.refresh(document)

    logger.info(f"Document updated: {document.document_number}")
    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
    description="Soft delete a document",
)
async def delete_document(
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_role("admin"))],
) -> None:
    """
    Soft delete a document.

    Args:
        document_id: Document ID
        session: Database session
        current_user: Current authenticated user
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.is_deleted == False)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.is_deleted = True
    await session.commit()

    logger.info(f"Document deleted: {document.document_number}")
