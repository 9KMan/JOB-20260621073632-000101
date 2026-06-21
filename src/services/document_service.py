# src/services/document_service.py
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from src.models.invoice import Invoice, InvoiceLineItem
from src.models.delivery_note import DeliveryNote, DeliveryNoteLineItem


class DocumentService:
    """Service for document operations (PO, Invoice, Delivery Note)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Purchase Order Operations ====================
    
    def get_purchase_order(self, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.line_items)
        ).filter(PurchaseOrder.id == po_id).first()
    
    def get_purchase_order_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.line_items)
        ).filter(PurchaseOrder.po_number == po_number).first()
    
    def get_purchase_orders(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get purchase orders with filters."""
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.line_items)
        )
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        total = query.count()
        pos = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
        
        return pos, total
    
    def create_purchase_order(self, po_data: dict) -> PurchaseOrder:
        """Create a new purchase order."""
        line_items_data = po_data.pop("line_items", [])
        
        po = PurchaseOrder(**po_data)
        self.db.add(po)
        self.db.flush()  # Get the PO ID
        
        # Create line items
        for item_data in line_items_data:
            item = PurchaseOrderLineItem(purchase_order_id=po.id, **item_data)
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(po)
        return po
    
    def update_purchase_order(self, po_id: uuid.UUID, po_data: dict) -> Optional[PurchaseOrder]:
        """Update a purchase order."""
        po = self.get_purchase_order(po_id)
        if not po:
            return None
        
        for key, value in po_data.items():
            if hasattr(po, key) and value is not None:
                setattr(po, key, value)
        
        self.db.commit()
        self.db.refresh(po)
        return po
    
    def delete_purchase_order(self, po_id: uuid.UUID) -> bool:
        """Delete a purchase order."""
        po = self.get_purchase_order(po_id)
        if not po:
            return False
        
        self.db.delete(po)
        self.db.commit()
        return True
    
    # ==================== Invoice Operations ====================
    
    def get_invoice(self, invoice_id: uuid.UUID) -> Optional[Invoice]:
        """Get invoice by ID."""
        return self.db.query(Invoice).options(
            joinedload(Invoice.line_items),
            joinedload(Invoice.purchase_order)
        ).filter(Invoice.id == invoice_id).first()
    
    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return self.db.query(Invoice).options(
            joinedload(Invoice.line_items),
            joinedload(Invoice.purchase_order)
        ).filter(Invoice.invoice_number == invoice_number).first()
    
    def get_invoices(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Invoice], int]:
        """Get invoices with filters."""
        query = self.db.query(Invoice).options(
            joinedload(Invoice.line_items),
            joinedload(Invoice.purchase_order)
        )
        
        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        if status:
            query = query.filter(Invoice.status == status)
        if purchase_order_id:
            query = query.filter(Invoice.purchase_order_id == purchase_order_id)
        
        total = query.count()
        invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
        
        return invoices, total
    
    def create_invoice(self, invoice_data: dict) -> Invoice:
        """Create a new invoice."""
        line_items_data = invoice_data.pop("line_items", [])
        
        if "purchase_order_id" in invoice_data and invoice_data["purchase_order_id"]:
            invoice_data["purchase_order_id"] = uuid.UUID(invoice_data["purchase_order_id"])
        
        invoice = Invoice(**invoice_data)
        self.db.add(invoice)
        self.db.flush()
        
        for item_data in line_items_data:
            item = InvoiceLineItem(invoice_id=invoice.id, **item_data)
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
    
    def update_invoice(self, invoice_id: uuid.UUID, invoice_data: dict) -> Optional[Invoice]:
        """Update an invoice."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        for key, value in invoice_data.items():
            if hasattr(invoice, key) and value is not None:
                setattr(invoice, key, value)
        
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
    
    def delete_invoice(self, invoice_id: uuid.UUID) -> bool:
        """Delete an invoice."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return False
        
        self.db.delete(invoice)
        self.db.commit()
        return True
    
    # ==================== Delivery Note Operations ====================
    
    def get_delivery_note(self, dn_id: uuid.UUID) -> Optional[DeliveryNote]:
        """Get delivery note by ID."""
        return self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.line_items),
            joinedload(DeliveryNote.purchase_order)
        ).filter(DeliveryNote.id == dn_id).first()
    
    def get_delivery_note_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get delivery note by DN number."""
        return self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.line_items),
            joinedload(DeliveryNote.purchase_order)
        ).filter(DeliveryNote.dn_number == dn_number).first()
    
    def get_delivery_notes(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[DeliveryNote], int]:
        """Get delivery notes with filters."""
        query = self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.line_items),
            joinedload(DeliveryNote.purchase_order)
        )
        
        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        if status:
            query = query.filter(DeliveryNote.status == status)
        if purchase_order_id:
            query = query.filter(DeliveryNote.purchase_order_id == purchase_order_id)
        
        total = query.count()
        dns = query.order_by(DeliveryNote.created_at.desc()).offset(skip).limit(limit).all()
        
        return dns, total
    
    def create_delivery_note(self, dn_data: dict) -> DeliveryNote:
        """Create a new delivery note."""
        line_items_data = dn_data.pop("line_items", [])
        
        if "purchase_order_id" in dn_data and dn_data["purchase_order_id"]:
            dn_data["purchase_order_id"] = uuid.UUID(dn_data["purchase_order_id"])
        
        delivery_note = DeliveryNote(**dn_data)
        self.db.add(delivery_note)
        self.db.flush()
        
        for item_data in line_items_data:
            item = DeliveryNoteLineItem(delivery_note_id=delivery_note.id, **item_data)
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(delivery_note)
        return delivery_note
    
    def update_delivery_note(self, dn_id: uuid.UUID, dn_data: dict) -> Optional[DeliveryNote]:
        """Update a delivery note."""
        delivery_note = self.get_delivery_note(dn_id)
        if not delivery_note:
            return None
        
        for key, value in dn_data.items():
            if hasattr(delivery_note, key) and value is not None:
                setattr(delivery_note, key, value)
        
        self.db.commit()
        self.db.refresh(delivery_note)
        return delivery_note
    
    def delete_delivery_note(self, dn_id: uuid.UUID) -> bool:
        """Delete a delivery note."""
        delivery_note = self.get_delivery_note(dn_id)
        if not delivery_note:
            return False
        
        self.db.delete(delivery_note)
        self.db.commit()
        return True
