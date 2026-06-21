// src/services/document_service.py
"""Document service for CRUD operations on invoices, POs, and delivery notes."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from src.models.document import (
    Document,
    DocumentLine,
    DocumentStatus,
    DocumentType,
    Invoice,
    PurchaseOrder,
    DeliveryNote,
    PurchaseOrderLine,
    DeliveryNoteLine,
    Supplier,
)
from src.models.matching import MatchResult


class DocumentService:
    """Service for document operations."""

    def __init__(self, db: Session):
        """Initialize document service."""
        self.db = db

    # ==================== Invoice Operations ====================

    def create_invoice(
        self,
        invoice_number: str,
        supplier_id: UUID,
        subtotal: Decimal,
        issue_date: date,
        po_number: Optional[str] = None,
        tax_amount: Decimal = Decimal("0.00"),
        due_date: Optional[date] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None,
        lines: Optional[List[dict]] = None,
    ) -> Invoice:
        """Create a new invoice."""
        total_amount = subtotal + tax_amount

        invoice = Invoice(
            invoice_number=invoice_number,
            supplier_id=supplier_id,
            po_number=po_number,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            balance_amount=total_amount,
            currency=currency,
            issue_date=issue_date,
            due_date=due_date,
            notes=notes,
            created_by=created_by,
            status=DocumentStatus.PENDING.value,
            received_date=datetime.utcnow(),
        )

        self.db.add(invoice)
        self.db.flush()

        # Create line items if provided
        if lines:
            for line_data in lines:
                line = DocumentLine(
                    document_id=invoice.id,
                    document_type=DocumentType.INVOICE.value,
                    line_number=line_data.get("line_number", "1"),
                    product_code=line_data.get("product_code", ""),
                    product_name=line_data.get("product_name", ""),
                    description=line_data.get("description"),
                    quantity=line_data.get("quantity", 1),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    unit_price=line_data.get("unit_price", Decimal("0")),
                    subtotal=line_data.get("subtotal", Decimal("0")),
                    tax_rate=line_data.get("tax_rate", Decimal("0")),
                    tax_amount=line_data.get("tax_amount", Decimal("0")),
                    total_amount=line_data.get("total_amount", Decimal("0")),
                    balance_quantity=line_data.get("quantity", 1),
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID."""
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.document))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return self.db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

    def get_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        po_number: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[Invoice], int]:
        """Get paginated list of invoices."""
        query = self.db.query(Invoice)

        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        if status:
            query = query.filter(Invoice.status == status)
        if po_number:
            query = query.filter(Invoice.po_number == po_number)
        if from_date:
            query = query.filter(Invoice.issue_date >= from_date)
        if to_date:
            query = query.filter(Invoice.issue_date <= to_date)

        total = query.count()
        invoices = query.order_by(Invoice.issue_date.desc()).offset(skip).limit(limit).all()

        return invoices, total

    def update_invoice(self, invoice: Invoice, **kwargs) -> Invoice:
        """Update invoice fields."""
        for key, value in kwargs.items():
            if hasattr(invoice, key) and value is not None:
                setattr(invoice, key, value)

        # Recalculate total if subtotal or tax changed
        if "subtotal" in kwargs or "tax_amount" in kwargs:
            invoice.total_amount = invoice.subtotal + invoice.tax_amount

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete_invoice(self, invoice: Invoice) -> None:
        """Soft delete invoice."""
        invoice.is_active = False
        self.db.commit()

    # ==================== Purchase Order Operations ====================

    def create_purchase_order(
        self,
        po_number: str,
        supplier_id: UUID,
        subtotal: Decimal,
        order_date: date,
        tax_amount: Decimal = Decimal("0.00"),
        expected_delivery_date: Optional[date] = None,
        currency: str = "USD",
        terms: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None,
        lines: Optional[List[dict]] = None,
    ) -> PurchaseOrder:
        """Create a new purchase order."""
        total_amount = subtotal + tax_amount

        # Get supplier info
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            supplier_code=supplier.supplier_code if supplier else "",
            supplier_name=supplier.supplier_name if supplier else "",
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            balance_amount=total_amount,
            currency=currency,
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            terms=terms,
            notes=notes,
            created_by=created_by,
            status=DocumentStatus.DRAFT.value,
        )

        self.db.add(po)
        self.db.flush()

        # Create line items if provided
        if lines:
            for line_data in lines:
                line = PurchaseOrderLine(
                    purchase_order_id=po.id,
                    line_number=line_data.get("line_number", "1"),
                    product_code=line_data.get("product_code", ""),
                    product_name=line_data.get("product_name", ""),
                    description=line_data.get("description"),
                    quantity=line_data.get("quantity", 1),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    unit_price=line_data.get("unit_price", Decimal("0")),
                    subtotal=line_data.get("subtotal", Decimal("0")),
                    tax_rate=line_data.get("tax_rate", Decimal("0")),
                    tax_amount=line_data.get("tax_amount", Decimal("0")),
                    total_amount=line_data.get("total_amount", Decimal("0")),
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(po)
        return po

    def get_purchase_order_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    def get_purchase_order_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(PurchaseOrder.po_number == po_number)
            .first()
        )

    def get_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[PurchaseOrder], int]:
        """Get paginated list of purchase orders."""
        query = self.db.query(PurchaseOrder)

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        if from_date:
            query = query.filter(PurchaseOrder.order_date >= from_date)
        if to_date:
            query = query.filter(PurchaseOrder.order_date <= to_date)

        total = query.count()
        purchase_orders = query.order_by(PurchaseOrder.order_date.desc()).offset(skip).limit(limit).all()

        return purchase_orders, total

    def update_purchase_order(self, po: PurchaseOrder, **kwargs) -> PurchaseOrder:
        """Update purchase order fields."""
        for key, value in kwargs.items():
            if hasattr(po, key) and value is not None:
                setattr(po, key, value)

        # Recalculate total if subtotal or tax changed
        if "subtotal" in kwargs or "tax_amount" in kwargs:
            po.total_amount = po.subtotal + po.tax_amount

        self.db.commit()
        self.db.refresh(po)
        return po

    # ==================== Delivery Note Operations ====================

    def create_delivery_note(
        self,
        dn_number: str,
        supplier_id: UUID,
        subtotal: Decimal,
        issue_date: date,
        po_number: Optional[str] = None,
        tax_amount: Decimal = Decimal("0.00"),
        received_date: Optional[datetime] = None,
        carrier: Optional[str] = None,
        tracking_number: Optional[str] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None,
        lines: Optional[List[dict]] = None,
    ) -> DeliveryNote:
        """Create a new delivery note."""
        total_amount = subtotal + tax_amount

        dn = DeliveryNote(
            dn_number=dn_number,
            supplier_id=supplier_id,
            po_number=po_number,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            balance_amount=total_amount,
            currency=currency,
            issue_date=issue_date,
            received_date=received_date or datetime.utcnow(),
            carrier=carrier,
            tracking_number=tracking_number,
            notes=notes,
            created_by=created_by,
            status=DocumentStatus.PENDING.value,
        )

        self.db.add(dn)
        self.db.flush()

        # Create line items if provided
        if lines:
            for line_data in lines:
                line = DeliveryNoteLine(
                    delivery_note_id=dn.id,
                    line_number=line_data.get("line_number", "1"),
                    product_code=line_data.get("product_code", ""),
                    product_name=line_data.get("product_name", ""),
                    description=line_data.get("description"),
                    quantity=line_data.get("quantity", 1),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    unit_price=line_data.get("unit_price", Decimal("0")),
                    subtotal=line_data.get("subtotal", Decimal("0")),
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(dn)
        return dn

    def get_delivery_note_by_id(self, dn_id: UUID) -> Optional[DeliveryNote]:
        """Get delivery note by ID."""
        return (
            self.db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .filter(DeliveryNote.id == dn_id)
            .first()
        )

    def get_delivery_note_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get delivery note by DN number."""
        return (
            self.db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .filter(DeliveryNote.dn_number == dn_number)
            .first()
        )

    def get_delivery_notes(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        po_number: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Tuple[List[DeliveryNote], int]:
        """Get paginated list of delivery notes."""
        query = self.db.query(DeliveryNote)

        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        if status:
            query = query.filter(DeliveryNote.status == status)
        if po_number:
            query = query.filter(DeliveryNote.po_number == po_number)
        if from_date:
            query = query.filter(DeliveryNote.issue_date >= from_date)
        if to_date:
            query = query.filter(DeliveryNote.issue_date <= to_date)

        total = query.count()
        delivery_notes = query.order_by(DeliveryNote.issue_date.desc()).offset(skip).limit(limit).all()

        return delivery_notes, total

    def update_delivery_note(self, dn: DeliveryNote, **kwargs) -> DeliveryNote:
        """Update delivery note fields."""
        for key, value in kwargs.items():
            if hasattr(dn, key) and value is not None:
                setattr(dn, key, value)

        # Recalculate total if subtotal or tax changed
        if "subtotal" in kwargs or "tax_amount" in kwargs:
            dn.total_amount = dn.subtotal + dn.tax_amount

        self.db.commit()
        self.db.refresh(dn)
        return dn

    # ==================== Supplier Operations ====================

    def create_supplier(
        self,
        supplier_code: str,
        supplier_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
    ) -> Supplier:
        """Create a new supplier."""
        supplier = Supplier(
            supplier_code=supplier_code,
            supplier_name=supplier_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            tax_id=tax_id,
            payment_terms=payment_terms,
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def get_supplier_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_supplier_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        return self.db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()

    def get_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool = True,
    ) -> Tuple[List[Supplier], int]:
        """Get paginated list of suppliers."""
        query = self.db.query(Supplier).filter(Supplier.is_active == is_active)
        total = query.count()
        suppliers = query.order_by(Supplier.supplier_name).offset(skip).limit(limit).all()
        return suppliers, total
