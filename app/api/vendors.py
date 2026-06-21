# app/api/vendors.py
"""Vendor API endpoints."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorListResponse

router = APIRouter()


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    """Create a new vendor."""
    # Check if vendor code already exists
    result = await db.execute(select(Vendor).where(Vendor.code == vendor_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with code '{vendor_data.code}' already exists",
        )

    # Create vendor
    vendor = Vendor(**vendor_data.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


@router.get("/", response_model=VendorListResponse)
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by code or name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> VendorListResponse:
    """List all vendors with pagination and filtering."""
    query = select(Vendor)
    count_query = select(func.count(Vendor.id))

    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            Vendor.code.ilike(f"%{search}%"),
            Vendor.name.ilike(f"%{search}%"),
        )
        filters.append(search_filter)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if is_active is not None:
        active_filter = Vendor.is_active == is_active
        filters.append(active_filter)
        query = query.where(active_filter)
        count_query = count_query.where(active_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Vendor.name)

    result = await db.execute(query)
    vendors = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return VendorListResponse(
        items=[VendorResponse.model_validate(v) for v in vendors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    """Get a vendor by ID."""
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID '{vendor_id}' not found",
        )
    return VendorResponse.model_validate(vendor)


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    vendor_data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    """Update a vendor."""
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID '{vendor_id}' not found",
        )

    # Check if new code conflicts with existing vendor
    if vendor_data.code and vendor_data.code != vendor.code:
        result = await db.execute(
            select(Vendor).where(and_(Vendor.code == vendor_data.code, Vendor.id != vendor_id))
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with code '{vendor_data.code}' already exists",
            )

    # Update fields
    update_data = vendor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)

    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a vendor (soft delete by setting is_active=False)."""
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID '{vendor_id}' not found",
        )

    vendor.is_active = False
    await db.commit()


from sqlalchemy import or_
