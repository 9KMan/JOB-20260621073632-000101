# src/services/balance_service.py
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.app.config import settings
from src.models.balance import Balance, BalanceType
from src.models.purchase_order import PurchaseOrder
from src.models.invoice import Invoice
from src.models.delivery_note import DeliveryNote


class BalanceService:
    """Service for balance tracking operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_balance_by_id(self, balance_id: uuid.UUID) -> Optional[Balance]:
        """Get balance by ID."""
        return self.db.query(Balance).filter(Balance.id == balance_id).first()
    
    def get_balances_by_po(self, po_id: uuid.UUID) -> List[Balance]:
        """Get all balances for a purchase order."""
        return self.db.query(Balance).filter(
            Balance.purchase_order_id == po_id
        ).all()
    
    def get_balances_by_reference(self, reference_type: str, reference_id: uuid.UUID) -> List[Balance]:
        """Get balances by reference document."""
        return self.db.query(Balance).filter(
            Balance.reference_type == reference_type,
            Balance.reference_id == reference_id
        ).all()
    
    def get_unsettled_balances(self, purchase_order_id: Optional[uuid.UUID] = None) -> List[Balance]:
        """Get all unsettled balances, optionally filtered by PO."""
        query = self.db.query(Balance).filter(Balance.is_settled == False)
        if purchase_order_id:
            query = query.filter(Balance.purchase_order_id == purchase_order_id)
        return query.all()
    
    def create_invoice_to_po_balance(
        self,
        invoice: Invoice,
        purchase_order: PurchaseOrder,
        matched_amount: Decimal = Decimal("0.00")
    ) -> Balance:
        """Create a balance record for invoice-to-PO relationship."""
        remaining = invoice.total_amount - matched_amount
        balance = Balance(
            balance_type=BalanceType.INVOICE_TO_PO.value,
            reference_type="INVOICE",
            reference_id=invoice.id,
            original_amount=invoice.total_amount,
            matched_amount=matched_amount,
            remaining_amount=remaining,
            purchase_order_id=purchase_order.id,
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def create_delivery_to_po_balance(
        self,
        delivery_note: DeliveryNote,
        purchase_order: PurchaseOrder,
        matched_amount: Decimal = Decimal("0.00")
    ) -> Balance:
        """Create a balance record for delivery-to-PO relationship."""
        remaining = delivery_note.total_amount - matched_amount
        balance = Balance(
            balance_type=BalanceType.DELIVERY_TO_PO.value,
            reference_type="DELIVERY",
            reference_id=delivery_note.id,
            original_amount=delivery_note.total_amount,
            matched_amount=matched_amount,
            remaining_amount=remaining,
            purchase_order_id=purchase_order.id,
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def create_invoice_to_delivery_balance(
        self,
        invoice: Invoice,
        delivery_note: DeliveryNote,
        matched_amount: Decimal = Decimal("0.00")
    ) -> Balance:
        """Create a balance record for invoice-to-delivery relationship."""
        remaining = invoice.total_amount - matched_amount
        balance = Balance(
            balance_type=BalanceType.INVOICE_TO_DELIVERY.value,
            reference_type="INVOICE",
            reference_id=invoice.id,
            original_amount=invoice.total_amount,
            matched_amount=matched_amount,
            remaining_amount=remaining,
            purchase_order_id=delivery_note.purchase_order_id,
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def update_balance(
        self,
        balance_id: uuid.UUID,
        matched_amount: Optional[Decimal] = None,
        remaining_amount: Optional[Decimal] = None,
        is_settled: Optional[bool] = None,
    ) -> Optional[Balance]:
        """Update a balance record."""
        balance = self.get_balance_by_id(balance_id)
        if not balance:
            return None
        
        if matched_amount is not None:
            balance.matched_amount = matched_amount
        if remaining_amount is not None:
            balance.remaining_amount = remaining_amount
        if is_settled is not None:
            balance.is_settled = is_settled
            if is_settled:
                balance.settlement_date = date.today()
        
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def settle_balance(self, balance_id: uuid.UUID) -> Optional[Balance]:
        """Settle a balance."""
        return self.update_balance(balance_id, is_settled=True)
    
    def recalculate_po_balance(self, po_id: uuid.UUID) -> dict:
        """Recalculate and aggregate balances for a PO."""
        balances = self.get_balances_by_po(po_id)
        
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return {"error": "Purchase order not found"}
        
        invoice_to_po = [b for b in balances if b.balance_type == BalanceType.INVOICE_TO_PO.value]
        delivery_to_po = [b for b in balances if b.balance_type == BalanceType.DELIVERY_TO_PO.value]
        
        total_invoice_matched = sum((b.matched_amount for b in invoice_to_po), Decimal("0.00"))
        total_delivery_matched = sum((b.matched_amount for b in delivery_to_po), Decimal("0.00"))
        total_invoice_remaining = sum((b.remaining_amount for b in invoice_to_po), Decimal("0.00"))
        total_delivery_remaining = sum((b.remaining_amount for b in delivery_to_po), Decimal("0.00"))
        
        return {
            "purchase_order_id": str(po_id),
            "po_total": po.total_amount,
            "total_invoice_matched": total_invoice_matched,
            "total_delivery_matched": total_delivery_matched,
            "total_invoice_remaining": total_invoice_remaining,
            "total_delivery_remaining": total_delivery_remaining,
            "is_fully_matched": total_invoice_remaining == Decimal("0.00") and total_delivery_remaining == Decimal("0.00"),
        }
    
    def delete_balance(self, balance_id: uuid.UUID) -> bool:
        """Delete a balance record."""
        balance = self.get_balance_by_id(balance_id)
        if not balance:
            return False
        self.db.delete(balance)
        self.db.commit()
        return True
