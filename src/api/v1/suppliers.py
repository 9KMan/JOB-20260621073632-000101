// src/api/v1/suppliers.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.app.database import get_db
from src.models.models import Supplier
from src.schemas.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    APIResponse,
)
from src.services.auth_service import get_current_active_user

router = APIRouter()


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Create a new supplier."""
    # Check if code already exists
    existing = db.query(Supplier).filter(Supplier.code == supplier_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with code '{supplier_data.code}' already exists",
        )
    
    supplier = Supplier(**supplier_data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search by code or name"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List all suppliers with optional filtering."""
    query = db.query(Supplier)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Supplier.code.ilike(search_term)) | (Supplier.name.ilike(search_term))
        )
    
    suppliers = query.order_by(Supplier.name).offset(skip).limit(limit).all()
    
    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get a supplier by ID."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )
    
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Update a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )
    
    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Delete a supplier (soft delete by deactivating)."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )
    
    # Soft delete
    supplier.is_active = False
    db.commit()
    
    return None
