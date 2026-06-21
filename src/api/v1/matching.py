// src/api/v1/matching.py
"""Matching engine endpoints."""
import logging
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_active_user, require_role
from src.api.schemas.matching import (
    MatchReviewRequest,
    MatchResultDetailResponse,
    MatchResultResponse,
    MatchScoreResponse,
    MatchingRecordResponse,
)
from src.config import settings
from src.database import get_async_session
from src.models.document import Document, DocumentStatus, DocumentType
from src.models.matching import (
    BalanceRecord,
    MatchConfidence,
    MatchDecision,
    MatchResult,
    MatchingRecord,
)
from src.models.user import User
from src.services.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/documents/{document_id}/match",
    response_model=MatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Match Document",
    description="Run matching algorithm for a document",
)
async def match_document(
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MatchResultResponse:
    """
    Run the 3-way matching algorithm for a document.

    Args:
        document_id: Document to match
        session: Database session
        current_user: Current authenticated user

    Returns:
        MatchResultResponse: Matching results
    """
    # Get document
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.is_deleted == False)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Run matching engine
    engine = MatchingEngine(session)
    match_result = await engine.run_matching(document)

    await session.commit()

    logger.info(f"Matching completed for document: {document.document_number}")
    return match_result


@router.get(
    "/documents/{document_id}/matches",
    response_model=list[MatchingRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Document Matches",
    description="Get all matching records for a document",
)
async def get_document_matches(
    document_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[MatchingRecord]:
    """
    Get all matching records for a document.

    Args:
        document_id: Document ID
        session: Database session
        current_user: Current authenticated user

    Returns:
        list[MatchingRecord]: Matching records
    """
    result = await session.execute(
        select(MatchingRecord).where(
            MatchingRecord.document_id == document_id,
            MatchingRecord.is_deleted == False,
        )
    )
    return result.scalars().all()


@router.get(
    "/records/{record_id}",
    response_model=MatchResultDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Match Record Details",
    description="Get detailed match record with line-level breakdown",
)
async def get_match_record(
    record_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MatchingRecord:
    """
    Get a detailed match record.

    Args:
        record_id: Match record ID
        session: Database session
        current_user: Current authenticated user

    Returns:
        MatchingRecord: Match record with details
    """
    result = await session.execute(
        select(MatchingRecord).where(MatchingRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match record not found",
        )

    return record


@router.post(
    "/records/{record_id}/review",
    response_model=MatchingRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Review Match",
    description="Human review of a pending match",
)
async def review_match(
    record_id: uuid.UUID,
    review_data: MatchReviewRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_role("admin", "accountant"))],
) -> MatchingRecord:
    """
    Review a pending match record.

    Args:
        record_id: Match record ID
        review_data: Review decision
        session: Database session
        current_user: Current authenticated user

    Returns:
        MatchingRecord: Updated match record
    """
    result = await session.execute(
        select(MatchingRecord).where(
            MatchingRecord.id == record_id,
            MatchingRecord.is_deleted == False,
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match record not found",
        )

    # Update review info
    record.decision = review_data.decision
    record.reviewed_by = current_user.id
    record.reviewed_at = date.today()
    record.review_notes = review_data.notes

    # Update result based on decision
    if review_data.decision in [MatchDecision.HUMAN_APPROVED, MatchDecision.AUTO_APPROVED]:
        record.result = MatchResult.CONFIRMED
        record.is_confirmed = True
    elif review_data.decision == MatchDecision.HUMAN_REJECTED:
        record.result = MatchResult.REJECTED
    elif review_data.decision == MatchDecision.DISPUTED:
        record.result = MatchResult.REJECTED

    # Update document status
    doc_result = await session.execute(
        select(Document).where(Document.id == record.document_id)
    )
    document = doc_result.scalar_one_or_none()
    if document:
        if record.result == MatchResult.CONFIRMED:
            document.status = DocumentStatus.APPROVED
        elif record.result == MatchResult.REJECTED:
            document.status = DocumentStatus.REJECTED

    await session.commit()
    await session.refresh(record)

    logger.info(f"Match record reviewed: {record_id}")
    return record


@router.post(
    "/run-batch",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Batch Matching",
    description="Run matching for all pending documents",
)
async def run_batch_matching(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_role("admin", "accountant"))],
    document_type: DocumentType | None = Query(default=None, description="Filter by document type"),
) -> dict:
    """
    Run batch matching for pending documents.

    Args:
        session: Database session
        current_user: Current authenticated user
        document_type: Filter by document type

    Returns:
        dict: Batch processing results
    """
    query = select(Document).where(
        Document.is_deleted == False,
        Document.status.in_([DocumentStatus.SUBMITTED, DocumentStatus.PENDING_REVIEW]),
    )

    if document_type:
        query = query.where(Document.document_type == document_type)

    result = await session.execute(query)
    documents = result.scalars().all()

    engine = MatchingEngine(session)
    processed = 0
    matched = 0
    errors = []

    for doc in documents:
        try:
            await engine.run_matching(doc)
            processed += 1
            if doc.status == DocumentStatus.MATCHED:
                matched += 1
        except Exception as e:
            errors.append({"document_id": str(doc.id), "error": str(e)})

    await session.commit()

    return {
        "processed": processed,
        "matched": matched,
        "errors": errors,
    }
