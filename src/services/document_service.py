// src/services/document_service.py
"""Document service for managing PO, Invoice, and Delivery Note operations."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.document import Document, DocumentLineItem, DocumentType, DocumentStatus
from models.user import User


class DocumentService:
    """Service for document operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(
        self,
        document_type: DocumentType,
        document_number: str,
        supplier_id: str,
        supplier_name: str,
        total_amount: Decimal,
        document_date: datetime,
        tax_amount: Optional[Decimal] = None,
        currency: str = "USD",
        due_date: Optional[datetime] = None,
        delivery_date: Optional[datetime] = None,
        supplier_reference: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[dict] = None,
        created_by: Optional[User] = None,
        line_items: Optional[List[dict]] = None,
    ) -> Document:
        """Create a new document with optional line items."""
        tax_amount = tax_amount or Decimal("0.00")
        
        document = Document(
            document_type=document_type,
            document_number=document_number,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            total_amount=total_amount,
            tax_amount=tax_amount,
            currency=currency,
            document_date=document_date,
            due_date=due_date,
            delivery_date=delivery_date,
            supplier_reference=supplier_reference,
            notes=notes,
            metadata=metadata,
            created_by=created_by.id if created_by else None,
        )
        
        self.session.add(document)
        await self.session.flush()
        
        # Add line items if provided
        if line_items:
            for idx, item_data in enumerate(line_items):
                line_item = DocumentLineItem(
                    document_id=document.id,
                    line_number=idx + 1,
                    product_code=item_data.get("product_code", ""),
                    product_name=item_data.get("product_name", ""),
                    description=item_data.get("description"),
                    quantity=item_data.get("quantity", Decimal("1")),
                    unit_of_measure=item_data.get("unit_of_measure", "EA"),
                    unit_price=item_data.get("unit_price", Decimal("0")),
                    line_total=item_data.get("line_total", Decimal("0")),
                    tax_rate=item_data.get("tax_rate", Decimal("0")),
                    expected_quantity=item_data.get("expected_quantity"),
                    delivered_quantity=item_data.get("delivered_quantity"),
                    invoiced_quantity=item_data.get("invoiced_quantity"),
                    metadata=item_data.get("metadata"),
                )
                self.session.add(line_item)
            
            await self.session.flush()
        
        return document

    async def get_document_by_id(
        self, document_id: uuid.UUID, include_line_items: bool = False
    ) -> Optional[Document]:
        """Get document by ID with optional line items."""
        query = select(Document).where(Document.id == document_id)
        
        if include_line_items:
            query = query.options(selectinload(Document.line_items))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_document_by_number(
        self,
        document_number: str,
        document_type: Optional[DocumentType] = None,
        supplier_id: Optional[str] = None,
    ) -> Optional[Document]:
        """Get document by document number with optional filters."""
        conditions = [Document.document_number == document_number]
        
        if document_type:
            conditions.append(Document.document_type == document_type)
        
        if supplier_id:
            conditions.append(Document.supplier_id == supplier_id)
        
        query = select(Document).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        supplier_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Document], int]:
        """Get paginated list of documents with filters."""
        conditions = []
        
        if document_type:
            conditions.append(Document.document_type == document_type)
        
        if status:
            conditions.append(Document.status == status)
        
        if supplier_id:
            conditions.append(Document.supplier_id == supplier_id)
        
        if date_from:
            conditions.append(Document.document_date >= date_from)
        
        if date_to:
            conditions.append(Document.document_date <= date_to)
        
        # Count query
        count_query = select(func.count(Document.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Data query
        offset = (page - 1) * page_size
        data_query = (
            select(Document)
            .options(selectinload(Document.line_items))
            .where(and_(*conditions)) if conditions else select(Document)
        )
        data_query = (
            data_query.order_by(Document.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(data_query)
        documents = list(result.scalars().all())
        
        return documents, total

    async def update_document_status(
        self, document_id: uuid.UUID, status: DocumentStatus
    ) -> Optional[Document]:
        """Update document status."""
        document = await self.get_document_by_id(document_id)
        
        if not document:
            return None
        
        document.status = status
        await self.session.flush()
        
        return document

    async def update_match_info(
        self,
        document_id: uuid.UUID,
        matched_amount: Decimal,
        matched_document_id: uuid.UUID,
        match_score: float,
    ) -> Optional[Document]:
        """Update document with matching information."""
        document = await self.get_document_by_id(document_id)
        
        if not document:
            return None
        
        document.matched_amount = matched_amount
        document.matched_document_id = matched_document_id
        document.match_score = match_score
        
        if matched_amount >= document.total_amount:
            document.status = DocumentStatus.MATCHED
        
        await self.session.flush()
        
        return document

    async def get_open_pos_by_supplier(
        self, supplier_id: str, include_line_items: bool = True
    ) -> List[Document]:
        """Get open (unmatched or partially matched) POs by supplier."""
        conditions = [
            Document.document_type == DocumentType.PURCHASE_ORDER,
            Document.supplier_id == supplier_id,
            Document.status.in_([DocumentStatus.PENDING, DocumentStatus.MATCHED]),
        ]
        
        query = select(Document).where(and_(*conditions))
        
        if include_line_items:
            query = query.options(selectinload(Document.line_items))
        
        query = query.order_by(Document.document_date.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_invoices_by_supplier(
        self, supplier_id: str, include_line_items: bool = True
    ) -> List[Document]:
        """Get pending invoices by supplier."""
        conditions = [
            Document.document_type == DocumentType.INVOICE,
            Document.supplier_id == supplier_id,
            Document.status == DocumentStatus.PENDING,
        ]
        
        query = select(Document).where(and_(*conditions))
        
        if include_line_items:
            query = query.options(selectinload(Document.line_items))
        
        query = query.order_by(Document.document_date.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_delivery_notes_by_supplier(
        self, supplier_id: str, include_line_items: bool = True
    ) -> List[Document]:
        """Get pending delivery notes by supplier."""
        conditions = [
            Document.document_type == DocumentType.DELIVERY_NOTE,
            Document.supplier_id == supplier_id,
            Document.status == DocumentStatus.PENDING,
        ]
        
        query = select(Document).where(and_(*conditions))
        
        if include_line_items:
            query = query.options(selectinload(Document.line_items))
        
        query = query.order_by(Document.document_date.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and its line items."""
        document = await self.get_document_by_id(document_id)
        
        if not document:
            return False
        
        await self.session.delete(document)
        await self.session.flush()
        
        return True

    async def add_line_item(
        self,
        document_id: uuid.UUID,
        line_number: int,
        product_code: str,
        product_name: str,
        quantity: Decimal,
        unit_price: Decimal,
        unit_of_measure: str = "EA",
        description: Optional[str] = None,
        tax_rate: Optional[Decimal] = None,
    ) -> Optional[DocumentLineItem]:
        """Add a line item to a document."""
        document = await self.get_document_by_id(document_id)
        
        if not document:
            return None
        
        line_total = quantity * unit_price
        if tax_rate:
            line_total = line_total * (1 + tax_rate / 100)
        
        line_item = DocumentLineItem(
            document_id=document_id,
            line_number=line_number,
            product_code=product_code,
            product_name=product_name,
            description=description,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            unit_price=unit_price,
            line_total=line_total,
            tax_rate=tax_rate or Decimal("0"),
        )
        
        self.session.add(line_item)
        await self.session.flush()
        
        return line_item

    async def get_line_items(
        self, document_id: uuid.UUID
    ) -> List[DocumentLineItem]:
        """Get all line items for a document."""
        query = (
            select(DocumentLineItem)
            .where(DocumentLineItem.document_id == document_id)
            .order_by(DocumentLineItem.line_number)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
