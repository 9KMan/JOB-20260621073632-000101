// alembic/versions/001_initial_migration.py
"""Initial migration - AP Automation Core

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Purchase Orders table
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('po_number', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('supplier_id', sa.String(100), nullable=False, index=True),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='OPEN'),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Purchase Order Lines
    op.create_table(
        'purchase_order_lines',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('purchase_order_id', sa.UUID(), sa.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('quantity_ordered', sa.Numeric(15, 3), nullable=False),
        sa.Column('quantity_received', sa.Numeric(15, 3), default=0),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('line_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('invoice_number', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('supplier_id', sa.String(100), nullable=False, index=True),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('po_reference', sa.String(100), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING'),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Invoice Lines
    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('invoice_id', sa.UUID(), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 3), nullable=False),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('line_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Delivery Notes table
    op.create_table(
        'delivery_notes',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('dn_number', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('supplier_id', sa.String(100), nullable=False, index=True),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('po_reference', sa.String(100), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='RECEIVED'),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('received_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Delivery Note Lines
    op.create_table(
        'delivery_note_lines',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('delivery_note_id', sa.UUID(), sa.ForeignKey('delivery_notes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('quantity_delivered', sa.Numeric(15, 3), nullable=False),
        sa.Column('quantity_received', sa.Numeric(15, 3), default=0),
        sa.Column('unit_price', sa.Numeric(15, 4), nullable=False),
        sa.Column('line_total', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Match Records table
    op.create_table(
        'match_records',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('purchase_order_id', sa.UUID(), sa.ForeignKey('purchase_orders.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('invoice_id', sa.UUID(), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('delivery_note_id', sa.UUID(), sa.ForeignKey('delivery_notes.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('match_type', sa.String(50), nullable=False),
        sa.Column('match_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('line_level_score', sa.Numeric(5, 2), default=0),
        sa.Column('amount_score', sa.Numeric(5, 2), default=0),
        sa.Column('date_score', sa.Numeric(5, 2), default=0),
        sa.Column('decision', sa.String(50), nullable=False, default='PENDING'),
        sa.Column('decided_by', sa.UUID(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Match Decision History
    op.create_table(
        'match_decisions',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('match_record_id', sa.UUID(), sa.ForeignKey('match_records.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('previous_decision', sa.String(50), nullable=True),
        sa.Column('new_decision', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Balance Ledger
    op.create_table(
        'balance_ledger',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False, index=True),
        sa.Column('line_id', sa.UUID(), nullable=True, index=True),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for high-cardinality columns
    op.create_index('ix_balance_document_type_id', 'balance_ledger', ['document_type', 'document_id'])


def downgrade() -> None:
    op.drop_table('balance_ledger')
    op.drop_table('match_decisions')
    op.drop_table('match_records')
    op.drop_table('delivery_note_lines')
    op.drop_table('delivery_notes')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('users')
