// src/workers/matching_worker.py
"""
Background matching worker for batch processing
Can be integrated with Celery for production use
"""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services.matching_service import MatchingService
from src.models.invoice import Invoice, InvoiceStatus


class MatchingWorker:
    """Background worker for processing pending invoices"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.matching_service = MatchingService(self.db)
    
    def run_batch(self, limit: int = 100) -> List[str]:
        """Process pending invoices in batch"""
        processed = []
        
        pending_invoices = self.db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.SUBMITTED
        ).limit(limit).all()
        
        for invoice in pending_invoices:
            try:
                self.matching_service.perform_three_way_match(
                    invoice_id=str(invoice.id)
                )
                processed.append(str(invoice.id))
            except Exception as e:
                print(f"Error processing invoice {invoice.id}: {e}")
                continue
        
        self.db.close()
        return processed
    
    def run_scheduled(self):
        """Scheduled job entry point"""
        print(f"[{datetime.utcnow()}] Starting scheduled matching job")
        processed = self.run_batch()
        print(f"[{datetime.utcnow()}] Completed processing {len(processed)} invoices")


if __name__ == "__main__":
    worker = MatchingWorker()
    worker.run_scheduled()
