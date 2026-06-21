// api/routes/suppliers.py
"""Supplier routes."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_role
from api.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from core.database import get_db
from models.user import User
from models.supplier import Supplier

router = APIRouter()


@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Supplier]:
    """
    List all suppliers with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        search: Search by code or name
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of suppliers
    """
    query = db.query(Supplier)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Supplier.code.ilike(search_term)) |
            (Supplier.name.ilike(search_term))
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Supplier:
    """
    Get a supplier by ID.
    
    Args:
        supplier_id: Supplier UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Supplier details
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )
    return supplier


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> Supplier:
    """
    Create a new supplier.
    
    Args:
        supplier_data: Supplier data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created supplier
    """
    # Check for duplicate code
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


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> Supplier:
    """
    Update a supplier.
    
    Args:
        supplier_id: Supplier UUID
        supplier_data: Supplier update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated supplier
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )
    
    # Check for duplicate code if changing
    if supplier_data.code and supplier_data.code != supplier.code:
        existing = db.query(Supplier).filter(
            Supplier.code == supplier_data.code,
            Supplier.id != supplier_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with code '{supplier_data.code}' already exists",
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
    current_user: User = Depends(require_role("admin")),
) -> None:
    """
    Delete a supplier (hard delete).
    
    Args:
        supplier_id: Supplier UUID
        db: Database session
        current_user: Current authenticated user
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )
    
    db.delete(supplier)
    db.commit()
