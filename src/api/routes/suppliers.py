// src/api/routes/suppliers.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User
from src.models.supplier import Supplier
from src.api.routes.auth import get_current_user
from src.api.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier."""
    existing_supplier = db.query(Supplier).filter(
        Supplier.supplier_code == supplier_data.supplier_code
    ).first()
    
    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with code {supplier_data.supplier_code} already exists"
        )
    
    supplier = Supplier(
        supplier_code=supplier_data.supplier_code,
        name=supplier_data.name,
        email=supplier_data.email,
        phone=supplier_data.phone,
        address_line1=supplier_data.address_line1,
        address_line2=supplier_data.address_line2,
        city=supplier_data.city,
        state=supplier_data.state,
        postal_code=supplier_data.postal_code,
        country=supplier_data.country,
        tax_id=supplier_data.tax_id,
        payment_terms=supplier_data.payment_terms,
        notes=supplier_data.notes,
        created_by=current_user.id
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.get("/", response_model=SupplierListResponse)
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None
):
    """List all suppliers with pagination."""
    query = db.query(Supplier)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Supplier.supplier_code.ilike(search_term) |
            Supplier.name.ilike(search_term)
        )
    
    total = query.count()
    items = query.order_by(Supplier.name)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return SupplierListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a supplier by ID."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    supplier.updated_by = current_user.id
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a supplier (soft delete)."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    supplier.is_active = False
    supplier.updated_by = current_user.id
    db.commit()
