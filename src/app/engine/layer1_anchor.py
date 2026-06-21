// src/app/engine/layer1_anchor.py
"""Layer 1: Anchoring - Establishes deterministic anchor using PO as source of truth."""

from typing import Optional
from sqlalchemy.orm import Session

from src.app.models import PurchaseOrder


class Layer1Anchor:
    """
    Layer 1 - Anchoring Engine
    
    Uses the Purchase Order as the single source of truth for anchoring.
    When an invoice or delivery note arrives, the system first tries to
    match it against open POs by supplier and PO number.
    This establishes a deterministic anchor for all downstream matching.
    """

    def __init__(self):
        """Initialize Layer 1 anchoring engine."""
        pass

    def find_anchor_po(
        self,
        db: Session,
        supplier_id: str,
        po_reference: Optional[str] = None,
        document_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Find the anchor purchase order for a given document.
        
        Search order:
        1. Exact PO number match (po_reference)
        2. PO number in invoice/delivery note reference field
        3. Open POs by supplier (fallback)
        
        Args:
            db: Database session
            supplier_id: Supplier UUID
            po_reference: Explicit PO reference from document
            document_number: Document number for searching references
            
        Returns:
            Purchase order ID if found, None otherwise
        """
        # Strategy 1: Direct PO number match
        if po_reference:
            po = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == po_reference,
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.is_deleted == False,  # noqa: E712
                PurchaseOrder.status == "OPEN"
            ).first()
            
            if po:
                return po.id

        # Strategy 2: Search open POs by supplier
        open_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.is_deleted == False,  # noqa: E712
            PurchaseOrder.status == "OPEN"
        ).order_by(PurchaseOrder.created_at.desc()).all()

        if not open_pos:
            return None

        # If only one open PO, use it
        if len(open_pos) == 1:
            return open_pos[0].id

        # Strategy 3: Try to match by PO number in document reference
        if document_number:
            for po in open_pos:
                if self._contains_po_reference(document_number, po.po_number):
                    return po.id

        # Fallback: Return most recent open PO
        return open_pos[0].id if open_pos else None

    def validate_anchor(
        self,
        db: Session,
        po_id: str,
        supplier_id: str
    ) -> bool:
        """
        Validate that the anchor PO is still valid.
        
        Args:
            db: Database session
            po_id: Purchase order ID
            supplier_id: Expected supplier ID
            
        Returns:
            True if anchor is valid, False otherwise
        """
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == po_id,
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.is_deleted == False,  # noqa: E712
            PurchaseOrder.status == "OPEN"
        ).first()

        return po is not None

    def get_anchor_context(
        self,
        db: Session,
        po_id: str
    ) -> dict:
        """
        Get full context for an anchor PO.
        
        Args:
            db: Database session
            po_id: Purchase order ID
            
        Returns:
            Dictionary with PO details and context
        """
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == po_id
        ).first()

        if not po:
            return {}

        return {
            "po_id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "order_date": po.order_date,
            "expected_delivery_date": po.expected_delivery_date,
            "total_amount": float(po.total_amount),
            "currency": po.currency,
            "status": po.status,
            "line_count": len(po.lines),
            "lines": [
                {
                    "line_number": line.line_number,
                    "item_code": line.item_code,
                    "description": line.description,
                    "quantity": float(line.quantity),
                    "unit_price": float(line.unit_price),
                    "line_total": float(line.line_total)
                }
                for line in po.lines
            ]
        }

    def _contains_po_reference(self, document_number: str, po_number: str) -> bool:
        """Check if document number contains PO reference."""
        return po_number.lower() in document_number.lower()
