// src/services/balance_service.py
"""
Balance Resolution Service

Handles balance tracking for partial matches, split invoices, and multi-delivery scenarios.
"""

import logging
from typing import List, Optional, Dict
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.models import (
    PurchaseOrder, PurchaseOrderLine,
    Invoice, InvoiceLine,
    DeliveryNote, DeliveryNoteLine,
    BalanceLedger
)

logger = logging.getLogger(__name__)


class BalanceService:
    """Service for balance resolution operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_po_line_balance(
        self,
        po_line_id: UUID
    ) -> Dict[str, Decimal]:
        """Get balance for a specific PO line."""
        po_line = self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.id == po_line_id
        ).first()
        
        if not po_line:
            return {"ordered": Decimal("0"), "invoiced": Decimal("0"), "delivered": Decimal("0")}
        
        ordered = Decimal(str(po_line.quantity))
        
        # Calculate invoiced quantity
        invoiced = Decimal("0")
        invoice_lines = self.db.query(InvoiceLine).filter(
            InvoiceLine.po_line_id == po_line_id
        ).all()
        for line in invoice_lines:
            invoiced += Decimal(str(line.quantity))
        
        # Calculate delivered quantity
        delivered = Decimal("0")
        dn_lines = self.db.query(DeliveryNoteLine).filter(
            DeliveryNoteLine.po_line_id == po_line_id
        ).all()
        for line in dn_lines:
            delivered += Decimal(str(line.quantity))
        
        return {
            "ordered": ordered,
            "invoiced": invoiced,
            "delivered": delivered,
            "open_to_invoice": max(Decimal("0"), ordered - invoiced),
            "open_to_deliver": max(Decimal("0"), ordered - delivered)
        }

    def get_po_balance_summary(self, po_id: UUID) -> Dict:
        """Get balance summary for entire PO."""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            return {"error": "PO not found"}
        
        line_balances = []
        for line in po.lines:
            line_balances.append({
                "line_id": str(line.id),
                "line_number": line.line_number,
                "description": line.description,
                **self.get_po_line_balance(line.id)
            })
        
        # Calculate totals
        total_ordered = sum(lb["ordered"] for lb in line_balances)
        total_invoiced = sum(lb["invoiced"] for lb in line_balances)
        total_delivered = sum(lb["delivered"] for lb in line_balances)
        
        return {
            "po_id": str(po.id),
            "po_number": po.po_number,
            "total_amount": po.total_amount,
            "lines": line_balances,
            "summary": {
                "total_ordered": total_ordered,
                "total_invoiced": total_invoiced,
                "total_delivered": total_delivered,
                "invoiced_percentage": float(total_invoiced / total_ordered * 100) if total_ordered > 0 else 0,
                "delivered_percentage": float(total_delivered / total_ordered * 100) if total_ordered > 0 else 0
            }
        }

    def create_partial_invoice_balance(
        self,
        invoice_id: UUID,
        po_id: UUID,
        line_amounts: Dict[UUID, Decimal]
    ) -> List[BalanceLedger]:
        """Create balance entries for partial invoice."""
        balances = []
        
        for po_line_id, amount in line_amounts.items():
            balance = BalanceLedger(
                document_type="INVOICE",
                document_id=invoice_id,
                document_line_id=po_line_id,
                balance_type="INVOICED",
                amount=amount,
                related_document_type="PO",
                related_document_id=po_id,
                notes=f"Partial invoice allocation"
            )
            balances.append(balance)
            self.db.add(balance)
        
        self.db.commit()
        logger.info(f"Created partial invoice balance for invoice {invoice_id}")
        return balances

    def create_partial_delivery_balance(
        self,
        dn_id: UUID,
        po_id: UUID,
        line_amounts: Dict[UUID, Decimal]
    ) -> List[BalanceLedger]:
        """Create balance entries for partial delivery."""
        balances = []
        
        for po_line_id, amount in line_amounts.items():
            balance = BalanceLedger(
                document_type="DN",
                document_id=dn_id,
                document_line_id=po_line_id,
                balance_type="DELIVERED",
                amount=amount,
                related_document_type="PO",
                related_document_id=po_id,
                notes=f"Partial delivery allocation"
            )
            balances.append(balance)
            self.db.add(balance)
        
        self.db.commit()
        logger.info(f"Created partial delivery balance for DN {dn_id}")
        return balances

    def record_payment(self, invoice_id: UUID, amount: Decimal, notes: Optional[str] = None) -> Invoice:
        """Record payment for an invoice."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        new_paid = invoice.amount_paid + amount
        invoice.amount_paid = min(new_paid, invoice.total_amount)
        
        # Update status if fully paid
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = "PAID"
        
        # Create balance ledger entry
        balance = BalanceLedger(
            document_type="INVOICE",
            document_id=invoice_id,
            balance_type="PAID",
            amount=amount,
            related_document_type="INVOICE",
            related_document_id=invoice_id,
            notes=notes or f"Payment recorded"
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(invoice)
        
        logger.info(f"Recorded payment of {amount} for invoice {invoice.invoice_number}")
        return invoice

    def get_vendor_balance_summary(self, vendor_id: UUID) -> Dict:
        """Get balance summary for all PO balances related to a vendor."""
        # Get all open POs for vendor
        pos = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.status == "OPEN",
                PurchaseOrder.is_deleted == False
            )
        ).all()
        
        summary = {
            "vendor_id": str(vendor_id),
            "total_open_po": len(pos),
            "total_open_amount": Decimal("0"),
            "total_invoiced_amount": Decimal("0"),
            "total_delivered_amount": Decimal("0"),
            "total_paid_amount": Decimal("0"),
            "purchase_orders": []
        }
        
        for po in pos:
            po_balance = self.get_po_balance_summary(po.id)
            summary["total_open_amount"] += Decimal(str(po.total_amount))
            summary["purchase_orders"].append(po_balance)
            
            # Calculate amounts from balance
            for inv in po.invoices:
                if not inv.is_deleted:
                    summary["total_invoiced_amount"] += Decimal(str(inv.total_amount))
                    summary["total_paid_amount"] += Decimal(str(inv.amount_paid))
            
            for dn in po.delivery_notes:
                if not dn.is_deleted:
                    summary["total_delivered_amount"] += Decimal(str(dn.total_amount))
        
        summary["outstanding_balance"] = (
            summary["total_invoiced_amount"] - summary["total_paid_amount"]
        )
        
        return summary

    def get_balance_ledger_entries(
        self,
        document_type: Optional[str] = None,
        document_id: Optional[UUID] = None,
        balance_type: Optional[str] = None,
        limit: int = 100
    ) -> List[BalanceLedger]:
        """Get balance ledger entries with optional filters."""
        query = self.db.query(BalanceLedger)
        
        if document_type:
            query = query.filter(BalanceLedger.document_type == document_type)
        if document_id:
            query = query.filter(BalanceLedger.document_id == document_id)
        if balance_type:
            query = query.filter(BalanceLedger.balance_type == balance_type)
        
        return query.order_by(BalanceLedger.created_at.desc()).limit(limit).all()

    def reconcile_balance_discrepancies(
        self,
        po_id: UUID
    ) -> Dict[str, List]:
        """Identify and return balance discrepancies for a PO."""
        po_balance = self.get_po_balance_summary(po_id)
        discrepancies = {
            "over_invoiced": [],
            "under_invoiced": [],
            "over_delivered": [],
            "under_delivered": [],
            "payment_discrepancies": []
        }
        
        for line in po_balance.get("lines", []):
            line_id = UUID(line["line_id"])
            
            # Check invoicing discrepancies
            if line["invoiced"] > line["ordered"]:
                discrepancies["over_invoiced"].append({
                    "line_id": str(line_id),
                    "line_number": line["line_number"],
                    "description": line["description"],
                    "ordered": str(line["ordered"]),
                    "invoiced": str(line["invoiced"]),
                    "difference": str(line["invoiced"] - line["ordered"])
                })
            elif line["invoiced"] < line["ordered"] * Decimal("0.9"):  # 10% threshold
                discrepancies["under_invoiced"].append({
                    "line_id": str(line_id),
                    "line_number": line["line_number"],
                    "description": line["description"],
                    "ordered": str(line["ordered"]),
                    "invoiced": str(line["invoiced"]),
                    "difference": str(line["ordered"] - line["invoiced"])
                })
            
            # Check delivery discrepancies
            if line["delivered"] > line["ordered"]:
                discrepancies["over_delivered"].append({
                    "line_id": str(line_id),
                    "line_number": line["line_number"],
                    "description": line["description"],
                    "ordered": str(line["ordered"]),
                    "delivered": str(line["delivered"]),
                    "difference": str(line["delivered"] - line["ordered"])
                })
            elif line["delivered"] < line["ordered"] * Decimal("0.9"):
                discrepancies["under_delivered"].append({
                    "line_id": str(line_id),
                    "line_number": line["line_number"],
                    "description": line["description"],
                    "ordered": str(line["ordered"]),
                    "delivered": str(line["delivered"]),
                    "difference": str(line["ordered"] - line["delivered"])
                })
        
        return discrepancies
