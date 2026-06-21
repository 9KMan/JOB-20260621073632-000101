// src/app/models/document.py
"""Document type enumerations."""
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    
    def __str__(self) -> str:
        return self.value
