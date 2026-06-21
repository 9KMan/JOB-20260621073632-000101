// src/api/routes/documents.py
"""Document management endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.database import get_db
from src.api.schemas.document import (
    DocumentCreate,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentResponse,
    DocumentTypeEnum,
    DocumentUpdate,
)
from src.models.document import Document, DocumentLine

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Create a new document (Invoice, Delivery Note, or Purchase Order)."""
    document = Document(
        document_type=document_data.document_type,
        document_number=document_data.document_number,
        supplier_id=document_data.supplier_id,
        supplier_name=document_data.supplier_name,
        supplier_reference=document_data.supplier_reference,
        currency=document_data.currency,
        subtotal=document_data.subtotal,
        tax_amount=document_data.tax_amount,
        total_amount=document_data.total_amount,
        document_date=document_data.document_date,
        due_date=document_data.due_date,
        status=document_data.status,
        metadata=document_data.metadata,
    )

    db.add(document)
    await db.flush()

    # Create document lines
    for line_data in document_data.lines:
        line = DocumentLine(
            document_id=document.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            total_amount=line_data.total_amount,
            uom=line_data.uom,
            tax_code=line_data.tax_code,
        )
        db.add(line)

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Get a document by ID with all its lines."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.lines))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    document_type: Optional[DocumentTypeEnum] = Query(None),
    supplier_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> list[DocumentResponse]:
    """List documents with optional filters."""
    query = select(Document).options(selectinload(Document.lines))

    if document_type:
        query = query.where(Document.document_type == document_type)
    if supplier_id:
        query = query.where(Document.supplier_id == supplier_id)
    if status_filter:
        query = query.where(Document.status == status_filter)

    query = query.offset(skip).limit(limit).order_by(Document.created_at.desc())

    result = await db.execute(query)
    documents = result.scalars().all()

    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """Update a document."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.lines))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    update_data = document_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "metadata" and value:
            # Merge with existing metadata
            current_metadata = document.metadata or {}
            current_metadata.update(value)
            setattr(document, field, current_metadata)
        elif field != "lines":
            setattr(document, field, value)

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft delete a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    document.is_deleted = True
    await db.commit()
