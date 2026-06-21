// src/services/balance_service.py
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.invoice import Invoice, InvoiceLine
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine


class BalanceService:
    """
    Layer 3: Balance Resolution
    Tracks partial matches and balances across all document types
    Handles: partial shipments, split invoices, multi-delivery scenarios
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_po_balance(self, po_id: str) -> Dict:
        """Calculate remaining balance for a PO"""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return None
        
        total_ordered = po.total_amount
        total_invoiced = sum(
            inv.total_amount for inv in po.invoices
            if inv.status.value not in ['rejected', 'cancelled']
        )
        total_delivered_value = sum(
            dn.total_amount for dn in po.delivery_notes
            if dn.status.value not in ['cancelled']
        )
        
        return {
            "po_id": str(po.id),
            "po_number": po.po_number,
            "total_ordered": total_ordered,
            "total_invoiced": total_invoiced,
            "total_delivered_value": total_delivered_value,
            "invoice_balance": total_ordered - total_invoiced,
            "delivery_balance": total_ordered - total_delivered_value,
            "invoice_pending": total_invoiced < total_ordered,
            "delivery_pending": total_delivered_value < total_ordered
        }
    
    def get_line_balances(self, po_id: str) -> List[Dict]:
        """Get line-level balances for a PO"""
        po = self.db.query(PurchaseOrder).options(
            PurchaseOrder.lines
        ).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            return []
        
        balances = []
        for po_line in po.lines:
            total_ordered = po_line.quantity
            total_delivered = Decimal("0")
            total_invoiced = Decimal("0")
            
            for inv in po.invoices:
                for inv_line in inv.lines:
                    if inv_line.product_code == po_line.product_code:
                        total_invoiced += inv_line.quantity
            
            for dn in po.delivery_notes:
                for dn_line in dn.lines:
                    if dn_line.product_code == po_line.product_code:
                        total_delivered += dn_line.quantity
            
            balances.append({
                "line_id": str(po_line.id),
                "product_code": po_line.product_code,
                "description": po_line.description,
                "quantity_ordered": total_ordered,
                "quantity_delivered": total_delivered,
                "quantity_invoiced": total_invoiced,
                "delivery_balance": total_ordered - total_delivered,
                "invoice_balance": total_ordered - total_invoiced,
                "fully_delivered": total_delivered >= total_ordered,
                "fully_invoiced": total_invoiced >= total_ordered
            })
        
        return balances
    
    def get_supplier_summary(self, supplier_code: str) -> Dict:
        """Get summary of all activity for a supplier"""
        pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_code == supplier_code
        ).all()
        
        total_ordered = sum(po.total_amount for po in pos)
        total_invoiced = sum(
            sum(inv.total_amount for inv in po.invoices)
            for po in pos
        )
        total_delivered = sum(
            sum(dn.total_amount for dn in po.delivery_notes)
            for po in pos
        )
        
        return {
            "supplier_code": supplier_code,
            "supplier_name": pos[0].supplier_name if pos else None,
            "total_pos": len(pos),
            "total_ordered": total_ordered,
            "total_invoiced": total_invoiced,
            "total_delivered": total_delivered,
            "pending_invoices": total_ordered - total_invoiced,
            "pending_deliveries": total_ordered - total_delivered
        }
    
    def validate_partial_match(
        self,
        po_id: str,
        invoice_amount: Decimal,
        dn_amount: Optional[Decimal] = None
    ) -> Dict:
        """Validate if a partial match is acceptable"""
        balance = self.get_po_balance(po_id)
        
        if not balance:
            return {"valid": False, "reason": "PO not found"}
        
        invoice_valid = invoice_amount <= balance["invoice_balance"]
        dn_valid = True
        if dn_amount:
            dn_valid = dn_amount <= balance["delivery_balance"]
        
        return {
            "valid": invoice_valid and dn_valid,
            "invoice_valid": invoice_valid,
            "dn_valid": dn_valid,
            "reason": self._get_validation_reason(invoice_valid, dn_valid),
            "available_balance": balance["invoice_balance"],
            "available_delivery": balance["delivery_balance"]
        }
    
    def _get_validation_reason(self, invoice_valid: bool, dn_valid: bool) -> str:
        if invoice_valid and dn_valid:
            return "Match is within acceptable balance"
        elif not invoice_valid:
            return "Invoice amount exceeds available balance"
        else:
            return "Delivery amount exceeds available delivery"
