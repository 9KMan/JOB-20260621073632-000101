// src/services/balance.py
"""Balance tracking service."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.balance import Balance, BalanceType
from src.models.document import Document


class BalanceService:
    """Service for balance tracking operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_balance(
        self,
        document_id: str,
        balance_type: BalanceType,
        amount: Optional[Decimal] = None,
    ) -> Balance:
        """Get existing or create new balance record."""
        result = await self.db.execute(
            select(Balance).where(
                Balance.document_id == document_id,
                Balance.balance_type == balance_type,
            )
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            document = await self.db.get(Document, document_id)
            balance = Balance(
                document_id=document_id,
                balance_type=balance_type,
                original_amount=amount or document.total_amount,
            )
            self.db.add(balance)
            await self.db.flush()
        
        return balance
    
    async def update_matched_amount(
        self,
        balance_id: str,
        amount: Decimal,
        reference_document_id: Optional[str] = None,
        reference_document_number: Optional[str] = None,
    ) -> Balance:
        """Update matched amount on a balance."""
        balance = await self.db.get(Balance, balance_id)
        if not balance:
            raise ValueError(f"Balance {balance_id} not found")
        
        balance.matched_amount += amount
        if reference_document_id:
            balance.reference_document_id = reference_document_id
            balance.reference_document_number = reference_document_number
        
        await self.db.flush()
        return balance
    
    async def get_document_balance(self, document_id: str) -> dict[str, Decimal]:
        """Get balance summary for a document."""
        result = await self.db.execute(
            select(Balance).where(Balance.document_id == document_id)
        )
        balances = result.scalars().all()
        
        total_original = Decimal("0")
        total_matched = Decimal("0")
        
        for balance in balances:
            total_original += balance.original_amount
            total_matched += balance.matched_amount
        
        return {
            "original_amount": total_original,
            "matched_amount": total_matched,
            "open_amount": total_original - total_matched,
        }
    
    async def reverse_match(
        self,
        balance_id: str,
        amount: Decimal,
    ) -> Balance:
        """Reverse a match by reducing matched amount."""
        balance = await self.db.get(Balance, balance_id)
        if not balance:
            raise ValueError(f"Balance {balance_id} not found")
        
        balance.matched_amount = max(Decimal("0"), balance.matched_amount - amount)
        
        await self.db.flush()
        return balance
