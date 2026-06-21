# src/api/v1/routes.py
import math
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.api.v1 import schemas
from src.models.database import get_db
from src.models.entities import (
    BalanceLedger,
    DeliveryNote,
    DeliveryNoteLine,
    Invoice,
    InvoiceLine,
    MatchStatus,
    MatchingConfirmation,
    MatchingResult,
    PurchaseOrder,
    PurchaseOrderLine,
    User,
)
from src.services.auth import get_current_active_user, get_password_hash, verify_password
from src.services.matching import MatchingEngine

router = APIRouter()


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Register a new user."""
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=schemas.Token)
async def login(
    credentials: schemas.UserLogin,
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate user and return JWT token."""
    from src.services.auth import create_access_token
    
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=schemas.UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current authenticated user."""
    return current_user


# ============================================================================
# Purchase Order Endpoints
# ============================================================================


@router.post("/purchase-orders", response_model=schemas.PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: schemas.PurchaseOrderCreate,
    db: Session = Depends(get_db),
) -> PurchaseOrder:
    """Create a new Purchase Order with lines."""
    # Check if PO number exists
    existing_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_data.po_number
    ).first()
    if existing_po:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order {po_data.po_number} already exists"
        )
    
    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        po_date=po_data.po_date,
        expected_delivery_date=po_data.expected_delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
    )
    db.add(po)
    db.flush()
    
    # Create PO lines
    for line_data in po_data.lines:
        po_line = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            uom=line_data.uom,
        )
        db.add(po_line)
    
    # Create balance ledger entry
    balance_entry = BalanceLedger(
        reference_type="PO",
        reference_id=po.id,
        original_amount=po_data.total_amount,
        remaining_balance=po_data.total_amount,
    )
    db.add(balance_entry)
    
    db.commit()
    db.refresh(po)
    return po


@router.get("/purchase-orders", response_model=schemas.PurchaseOrderListResponse)
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> schemas.PurchaseOrderListResponse:
    """List all Purchase Orders with pagination."""
    query = db.query(PurchaseOrder).filter(PurchaseOrder.is_deleted == False)
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    total = query.count()
    pages = math.ceil(total / size)
    
    items = (
        query
        .options(joinedload(PurchaseOrder.lines))
        .order_by(PurchaseOrder.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return schemas.PurchaseOrderListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/purchase-orders/{po_id}", response_model=schemas.PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
) -> PurchaseOrder:
    """Get a Purchase Order by ID."""
    po = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.lines))
        .filter(PurchaseOrder.id == po_id)
        .first()
    )
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    return po


@router.patch("/purchase-orders/{po_id}", response_model=schemas.PurchaseOrderResponse)
async def update_purchase_order(
    po_id: UUID,
    po_update: schemas.PurchaseOrderUpdate,
    db: Session = Depends(get_db),
) -> PurchaseOrder:
    """Update a Purchase Order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    
    update_data = po_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    db.commit()
    db.refresh(po)
    return po


@router.delete("/purchase-orders/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Soft delete a Purchase Order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    po.is_deleted = True
    db.commit()


# ============================================================================
# Invoice Endpoints
# ============================================================================


@router.post("/invoices", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
) -> Invoice:
    """Create a new Invoice with lines."""
    existing_invoice = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_data.invoice_number
    ).first()
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice_data.invoice_number} already exists"
        )
    
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
    )
    db.add(invoice)
    db.flush()
    
    for line_data in invoice_data.lines:
        invoice_line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            uom=line_data.uom,
            po_line_id=line_data.po_line_id,
        )
        db.add(invoice_line)
    
    # Create balance ledger entry
    balance_entry = BalanceLedger(
        reference_type="INVOICE",
        reference_id=invoice.id,
        original_amount=invoice_data.total_amount,
        remaining_balance=invoice_data.total_amount,
    )
    db.add(balance_entry)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/invoices", response_model=schemas.InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> schemas.InvoiceListResponse:
    """List all Invoices with pagination."""
    query = db.query(Invoice).filter(Invoice.is_deleted == False)
    
    if supplier_id:
        query = query.filter(Invoice.supplier_id == supplier_id)
    if status:
        query = query.filter(Invoice.status == status)
    
    total = query.count()
    pages = math.ceil(total / size)
    
    items = (
        query
        .options(joinedload(Invoice.lines))
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return schemas.InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/invoices/{invoice_id}", response_model=schemas.InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> Invoice:
    """Get an Invoice by ID."""
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.lines))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    return invoice


@router.patch("/invoices/{invoice_id}", response_model=schemas.InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_update: schemas.InvoiceUpdate,
    db: Session = Depends(get_db),
) -> Invoice:
    """Update an Invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    update_data = invoice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Soft delete an Invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    invoice.is_deleted = True
    db.commit()


# ============================================================================
# Delivery Note Endpoints
# ============================================================================


@router.post("/delivery-notes", response_model=schemas.DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: schemas.DeliveryNoteCreate,
    db: Session = Depends(get_db),
) -> DeliveryNote:
    """Create a new Delivery Note with lines."""
    existing_dn = db.query(DeliveryNote).filter(
        DeliveryNote.dn_number == dn_data.dn_number
    ).first()
    if existing_dn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery Note {dn_data.dn_number} already exists"
        )
    
    delivery_note = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        dn_date=dn_data.dn_date,
        received_date=dn_data.received_date,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
    )
    db.add(delivery_note)
    db.flush()
    
    for line_data in dn_data.lines:
        dn_line = DeliveryNoteLine(
            delivery_note_id=delivery_note.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            uom=line_data.uom,
            po_line_id=line_data.po_line_id,
        )
        db.add(dn_line)
    
    # Create balance ledger entry
    balance_entry = BalanceLedger(
        reference_type="DN",
        reference_id=delivery_note.id,
        original_amount=dn_data.total_amount,
        remaining_balance=dn_data.total_amount,
    )
    db.add(balance_entry)
    
    db.commit()
    db.refresh(delivery_note)
    return delivery_note


@router.get("/delivery-notes", response_model=schemas.DeliveryNoteListResponse)
async def list_delivery_notes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> schemas.DeliveryNoteListResponse:
    """List all Delivery Notes with pagination."""
    query = db.query(DeliveryNote).filter(DeliveryNote.is_deleted == False)
    
    if supplier_id:
        query = query.filter(DeliveryNote.supplier_id == supplier_id)
    if status:
        query = query.filter(DeliveryNote.status == status)
    
    total = query.count()
    pages = math.ceil(total / size)
    
    items = (
        query
        .options(joinedload(DeliveryNote.lines))
        .order_by(DeliveryNote.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return schemas.DeliveryNoteListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/delivery-notes/{dn_id}", response_model=schemas.DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
) -> DeliveryNote:
    """Get a Delivery Note by ID."""
    delivery_note = (
        db.query(DeliveryNote)
        .options(joinedload(DeliveryNote.lines))
        .filter(DeliveryNote.id == dn_id)
        .first()
    )
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    return delivery_note


@router.patch("/delivery-notes/{dn_id}", response_model=schemas.DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: UUID,
    dn_update: schemas.DeliveryNoteUpdate,
    db: Session = Depends(get_db),
) -> DeliveryNote:
    """Update a Delivery Note."""
    delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    
    update_data = dn_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(delivery_note, field, value)
    
    db.commit()
    db.refresh(delivery_note)
    return delivery_note


@router.delete("/delivery-notes/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Soft delete a Delivery Note."""
    delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    delivery_note.is_deleted = True
    db.commit()


# ============================================================================
# Matching Endpoints
# ============================================================================


@router.post("/matching/match-invoice/{invoice_id}", response_model=List[schemas.MatchResultResponse])
async def match_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> List[MatchingResult]:
    """Match an invoice against Purchase Orders and Delivery Notes."""
    engine = MatchingEngine(db)
    results = engine.match_invoice(invoice_id)
    return results


@router.post("/matching/match-delivery-note/{dn_id}", response_model=List[schemas.MatchResultResponse])
async def match_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
) -> List[MatchingResult]:
    """Match a delivery note against Purchase Orders."""
    engine = MatchingEngine(db)
    results = engine.match_delivery_note(dn_id)
    return results


@router.post("/matching/three-way-match", response_model=List[schemas.MatchResultResponse])
async def three_way_match(
    match_request: schemas.MatchRequest,
    db: Session = Depends(get_db),
) -> List[MatchingResult]:
    """Perform 3-way matching between Invoice, Delivery Note, and Purchase Order."""
    engine = MatchingEngine(db)
    results = engine.three_way_match(
        invoice_id=match_request.invoice_id,
        po_id=match_request.po_id,
        dn_id=match_request.dn_id,
    )
    return results


@router.post("/matching/auto-match-pending", response_model=dict)
async def auto_match_pending(
    db: Session = Depends(get_db),
) -> dict:
    """Automatically match all pending invoices and delivery notes."""
    engine = MatchingEngine(db)
    result = engine.auto_match_pending()
    return result


@router.get("/matching/results", response_model=schemas.MatchingResultListResponse)
async def list_matching_results(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    match_status: Optional[str] = None,
    decision: Optional[str] = None,
    db: Session = Depends(get_db),
) -> schemas.MatchingResultListResponse:
    """List all matching results with pagination."""
    query = db.query(MatchingResult).filter(MatchingResult.is_active == True)
    
    if match_status:
        query = query.filter(MatchingResult.match_status == match_status)
    if decision:
        query = query.filter(MatchingResult.decision == decision)
    
    total = query.count()
    pages = math.ceil(total / size)
    
    items = (
        query
        .order_by(MatchingResult.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return schemas.MatchingResultListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/matching/results/{result_id}", response_model=schemas.MatchResultDetailResponse)
async def get_matching_result(
    result_id: UUID,
    db: Session = Depends(get_db),
) -> schemas.MatchResultDetailResponse:
    """Get detailed matching result with line-level matching."""
    result = db.query(MatchingResult).filter(MatchingResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matching result {result_id} not found"
        )
    
    # Parse line matching details
    line_matches = []
    if result.line_matching_details:
        import json
        try:
            details = json.loads(result.line_matching_details)
            line_matches = [schemas.LineMatchDetail(**m) for m in details]
        except (json.JSONDecodeError, ValueError):
            pass
    
    return schemas.MatchResultDetailResponse(
        **{
            k: v for k, v in result.__dict__.items()
            if k in schemas.MatchResultDetailResponse.model_fields
        },
        line_matches=line_matches,
    )


@router.post("/matching/confirm/{result_id}", response_model=schemas.MatchConfirmationResponse)
async def confirm_matching_result(
    result_id: UUID,
    confirmation: schemas.MatchConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MatchingConfirmation:
    """Confirm or reject a matching result."""
    result = db.query(MatchingResult).filter(MatchingResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matching result {result_id} not found"
        )
    
    # Update match status based on confirmation
    if confirmation.confirmation_status == "CONFIRMED":
        result.match_status = MatchStatus.CONFIRMED
    else:
        result.match_status = MatchStatus.REJECTED
    
    # Create confirmation record
    conf_record = MatchingConfirmation(
        matching_result_id=result_id,
        confirmed_by=current_user.id,
        confirmation_status=confirmation.confirmation_status,
        comments=confirmation.comments,
    )
    db.add(conf_record)
    db.commit()
    db.refresh(conf_record)
    return conf_record


# ============================================================================
# Balance Ledger Endpoints
# ============================================================================


@router.get("/balances", response_model=List[schemas.BalanceLedgerResponse])
async def list_unsettled_balances(
    reference_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[BalanceLedger]:
    """List all unsettled balances."""
    query = db.query(BalanceLedger).filter(BalanceLedger.is_settled == False)
    
    if reference_type:
        query = query.filter(BalanceLedger.reference_type == reference_type)
    
    return query.order_by(BalanceLedger.created_at.desc()).all()


@router.post("/balances/{balance_id}/settle", response_model=schemas.BalanceLedgerResponse)
async def settle_balance(
    balance_id: UUID,
    db: Session = Depends(get_db),
) -> BalanceLedger:
    """Mark a balance as settled."""
    from datetime import datetime, timezone
    
    balance = db.query(BalanceLedger).filter(BalanceLedger.id == balance_id).first()
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Balance {balance_id} not found"
        )
    
    balance.is_settled = True
    balance.settled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(balance)
    return balance


# ============================================================================
# Dashboard / Statistics Endpoints
# ============================================================================


@router.get("/dashboard/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
) -> schemas.DashboardStats:
    """Get dashboard statistics."""
    # Purchase Orders
    total_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.is_deleted == False
    ).scalar()
    open_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.is_deleted == False,
        PurchaseOrder.status == "OPEN"
    ).scalar()
    
    # Invoices
    total_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.is_deleted == False
    ).scalar()
    pending_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.is_deleted == False,
        Invoice.status == "PENDING_MATCH"
    ).scalar()
    
    # Delivery Notes
    total_dns = db.query(func.count(DeliveryNote.id)).filter(
        DeliveryNote.is_deleted == False
    ).scalar()
    pending_dns = db.query(func.count(DeliveryNote.id)).filter(
        DeliveryNote.is_deleted == False,
        DeliveryNote.status == "PENDING_MATCH"
    ).scalar()
    
    # Matching Results
    total_matches = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True
    ).scalar()
    pending_matches = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.match_status == MatchStatus.PENDING
    ).scalar()
    auto_approved = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.decision == "AUTO_APPROVE"
    ).scalar()
    human_review = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.decision == "HUMAN_REVIEW"
    ).scalar()
    disputes = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.decision == "DISPUTE"
    ).scalar()
    
    return schemas.DashboardStats(
        total_purchase_orders=total_pos or 0,
        open_purchase_orders=open_pos or 0,
        total_invoices=total_invoices or 0,
        pending_invoices=pending_invoices or 0,
        total_delivery_notes=total_dns or 0,
        pending_delivery_notes=pending_dns or 0,
        total_matching_results=total_matches or 0,
        pending_matches=pending_matches or 0,
        auto_approved=auto_approved or 0,
        human_review_required=human_review or 0,
        disputes=disputes or 0,
    )


@router.get("/dashboard/match-scores", response_model=schemas.MatchScoreBreakdown)
async def get_match_score_breakdown(
    db: Session = Depends(get_db),
) -> schemas.MatchScoreBreakdown:
    """Get matching score breakdown statistics."""
    from sqlalchemy import case, func
    
    # Count by match type
    invoice_po = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.match_type.like("%invoice%po%")
    ).scalar() or 0
    
    dn_po = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.match_type.like("%dn%po%")
    ).scalar() or 0
    
    invoice_dn = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.match_type.like("%invoice%dn%")
    ).scalar() or 0
    
    three_way = db.query(func.count(MatchingResult.id)).filter(
        MatchingResult.is_active == True,
        MatchingResult.invoice_id.isnot(None),
        MatchingResult.po_id.isnot(None),
        MatchingResult.dn_id.isnot(None)
    ).scalar() or 0
    
    # Average scores
    avg_scores = db.query(
        func.avg(MatchingResult.line_score),
        func.avg(MatchingResult.amount_score),
        func.avg(MatchingResult.date_score),
        func.avg(MatchingResult.total_score),
    ).filter(MatchingResult.is_active == True).first()
    
    return schemas.MatchScoreBreakdown(
        invoice_po_matches=invoice_po,
        dn_po_matches=dn_po,
        invoice_dn_matches=invoice_dn,
        three_way_matches=three_way,
        average_line_score=avg_scores[0] or 0,
        average_amount_score=avg_scores[1] or 0,
        average_date_score=avg_scores[2] or 0,
        average_total_score=avg_scores[3] or 0,
    )
