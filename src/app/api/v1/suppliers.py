// src/app/api/v1/suppliers.py
"""Supplier API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.app.database import get_db
from src.app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse
)
from src.app.services.crud_service import CRUDService
from src.app.models.supplier import Supplier

router = APIRouter()
crud_service = CRUDService(Supplier)


@router.post("/", response_model=SupplierResponse, status_code=201)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    """Create a new supplier."""
    # Check if code already exists
    existing = db.query(Supplier).filter(
        Supplier.code == supplier.code,
        Supplier.is_deleted == False  # noqa: E712
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Supplier code already exists")
    
    return crud_service.create(db, supplier.model_dump())


@router.get("/", response_model=SupplierListResponse)
def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    code: Optional[str] = None,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all suppliers with pagination."""
    skip = (page - 1) * page_size
    
    filters = {}
    if code:
        filters["code"] = code
    if name:
        filters["name"] = name
    if is_active is not None:
        filters["is_active"] = is_active
    
    items = crud_service.get_multi(db, skip=skip, limit=page_size, filters=filters if filters else None)
    total = crud_service.get_count(db, filters=filters if filters else None)
    total_pages = (total + page_size - 1) // page_size
    
    return SupplierListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db)
):
    """Get a supplier by ID."""
    supplier = crud_service.get(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    supplier: SupplierUpdate,
    db: Session = Depends(get_db)
):
    """Update a supplier."""
    existing = crud_service.get(db, supplier_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return crud_service.update(db, supplier_id, supplier.model_dump(exclude_unset=True))


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db)
):
    """Soft delete a supplier."""
    if not crud_service.delete(db, supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return None
