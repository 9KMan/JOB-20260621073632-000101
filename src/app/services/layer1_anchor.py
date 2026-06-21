// src/app/services/layer1_anchor.py
"""Layer 1: PO Anchoring Service.

This layer establishes the single source of truth by anchoring
invoices and delivery notes to purchase orders.
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import PurchaseOrder, POStatus

if TYPE_CHECKING:
    from app.models import Invoice, DeliveryNote


class Layer1AnchorService:
    """
    Layer 1: PO Anchoring Service
    
    Responsibilities:
    - Find the correct PO to anchor incoming invoices/delivery notes
    - Use supplier ID and PO reference as primary matching criteria
    - Only match against open/approved POs
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    def find_anchor_po(
        self,
        supplier_id: str,
        po_reference: str | None = None,
        currency: str | None = None,
    ) -> PurchaseOrder | None:
        """
        Find the PO to anchor against.
        
        Matching strategy:
        1. Try exact PO number match
        2. Try supplier + PO reference match
        3. Try supplier match with open status
        """
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status.in_([POStatus.APPROVED, POStatus.SUBMITTED]),
            PurchaseOrder.is_active == True,
            PurchaseOrder.is_fully_matched == False,
        )

        # Try PO number match first
        if po_reference:
            po = query.filter(
                PurchaseOrder.po_number == po_reference
            ).first()
            if po:
                return po

        # Try supplier reference match
        if po_reference:
            po = query.filter(
                PurchaseOrder.supplier_reference == po_reference
            ).first()
            if po:
                return po

        # Try currency match and return most recent
        if currency:
            po = query.filter(
                PurchaseOrder.currency == currency
            ).order_by(
                PurchaseOrder.po_date.desc()
            ).first()
            if po:
                return po

        # Return most recent open PO for supplier
        po = query.order_by(
            PurchaseOrder.po_date.desc()
        ).first()

        return po

    def validate_anchor(
        self,
        po: PurchaseOrder,
        document: "Invoice | DeliveryNote",
    ) -> dict[str, bool]:
        """
        Validate that the PO is a valid anchor for the document.
        
        Returns validation results with reasons.
        """
        results = {
            "valid": True,
            "supplier_match": po.supplier_id == document.supplier_id,
            "status_valid": po.status in [POStatus.APPROVED, POStatus.SUBMITTED],
            "is_active": po.is_active,
            "not_closed": po.status != POStatus.CLOSED,
            "reasons": [],
        }

        if not results["supplier_match"]:
            results["valid"] = False
            results["reasons"].append(
                f"Supplier mismatch: PO {po.supplier_id} != Document {document.supplier_id}"
            )

        if not results["status_valid"]:
            results["valid"] = False
            results["reasons"].append(
                f"PO status is {po.status}, expected APPROVED or SUBMITTED"
            )

        if not results["is_active"]:
            results["valid"] = False
            results["reasons"].append("PO is not active")

        if not results["not_closed"]:
            results["valid"] = False
            results["reasons"].append("PO is closed")

        return results

    def get_open_pos_for_supplier(
        self,
        supplier_id: str,
        limit: int = 10,
    ) -> list[PurchaseOrder]:
        """Get open POs for a supplier."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([POStatus.APPROVED, POStatus.SUBMITTED]),
                PurchaseOrder.is_active == True,
                PurchaseOrder.is_fully_matched == False,
            )
            .order_by(PurchaseOrder.po_date.desc())
            .limit(limit)
            .all()
        )
