# models/delivery_note.py
"""Delivery note models (re-exported from purchase_order.py for clarity)."""
from models.purchase_order import (
    DeliveryNote,
    DeliveryNoteLine,
)

__all__ = ["DeliveryNote", "DeliveryNoteLine"]
