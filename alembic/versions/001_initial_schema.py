// alembic/versions/001_initial_schema.py
"""Initial schema for AP Automation

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    # Suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('payment_terms_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_suppliers_code', 'suppliers', ['code'])

    # Purchase Orders table
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('po_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('po_number'),
    )
    op.create_index('ix_po_number', 'purchase_orders', ['po_number'])
    op.create_index('ix_po_supplier_id', 'purchase_orders', ['supplier_id'])
    op.create_index('ix_po_status', 'purchase_orders', ['status'])

    # Purchase Order Lines table
    op.create_table(
        'purchase_order_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('purchase_order_id', sa.UUID(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pol_po_id', 'purchase_order_lines', ['purchase_order_id'])
    op.create_index('ix_pol_item_code', 'purchase_order_lines', ['item_code'])

    # Delivery Notes table
    op.create_table(
        'delivery_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dn_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('po_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='RECEIVED'),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dn_number'),
    )
    op.create_index('ix_dn_number', 'delivery_notes', ['dn_number'])
    op.create_index('ix_dn_supplier_id', 'delivery_notes', ['supplier_id'])
    op.create_index('ix_dn_po_id', 'delivery_notes', ['po_id'])
    op.create_index('ix_dn_status', 'delivery_notes', ['status'])

    # Delivery Note Lines table
    op.create_table(
        'delivery_note_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('delivery_note_id', sa.UUID(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('quantity_received', sa.Numeric(precision=15, scale=3), nullable=False),
        sa.Column('quantity_accepted', sa.Numeric(precision=15, scale=3), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('line_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dnl_dn_id', 'delivery_note_lines', ['delivery_note_id'])
    op.create_index('ix_dnl_item_code', 'delivery_note_lines', ['item_code'])

    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('po_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
    )
    op.create_index('ix_inv_number', 'invoices', ['invoice_number'])
    op.create_index('ix_inv_supplier_id', 'invoices', ['supplier_id'])
    op.create_index('ix_inv_po_id', 'invoices', ['po_id'])
    op.create_index('ix_inv_status', 'invoices', ['status'])

    # Invoice Lines table
    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_il_inv_id', 'invoice_lines', ['invoice_id'])
    op.create_index('ix_il_item_code', 'invoice_lines', ['item_code'])

    # Matches table (3-way matching results)
    op.create_table(
        'matches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=True),
        sa.Column('delivery_note_id', sa.UUID(), nullable=True),
        sa.Column('purchase_order_id', sa.UUID(), nullable=True),
        sa.Column('match_type', sa.String(length=20), nullable=False),
        sa.Column('match_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('line_level_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('amount_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('date_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('overall_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('variance_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('variance_reason', sa.Text(), nullable=True),
        sa.Column('decision', sa.String(length=30), nullable=True),
        sa.Column('reviewed_by', sa.UUID(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_match_invoice_id', 'matches', ['invoice_id'])
    op.create_index('ix_match_dn_id', 'matches', ['delivery_note_id'])
    op.create_index('ix_match_po_id', 'matches', ['purchase_order_id'])
    op.create_index('ix_match_status', 'matches', ['match_status'])
    op.create_index('ix_match_decision', 'matches', ['decision'])

    # Match Line Details table
    op.create_table(
        'match_line_details',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('match_id', sa.UUID(), nullable=False),
        sa.Column('invoice_line_id', sa.UUID(), nullable=True),
        sa.Column('delivery_note_line_id', sa.UUID(), nullable=True),
        sa.Column('purchase_order_line_id', sa.UUID(), nullable=True),
        sa.Column('quantity_match', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('quantity_variance', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('amount_match', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('amount_variance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('line_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_line_id'], ['invoice_lines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['delivery_note_line_id'], ['delivery_note_lines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_line_id'], ['purchase_order_lines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mld_match_id', 'match_line_details', ['match_id'])

    # Balance Ledger table
    op.create_table(
        'balance_ledger',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_line_id', sa.UUID(), nullable=True),
        sa.Column('purchase_order_id', sa.UUID(), nullable=True),
        sa.Column('balance_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('matched_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('remaining_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bl_document', 'balance_ledger', ['document_type', 'document_id'])
    op.create_index('ix_bl_po_id', 'balance_ledger', ['purchase_order_id'])
    op.create_index('ix_bl_status', 'balance_ledger', ['status'])
    op.create_index('ix_bl_balance_type', 'balance_ledger', ['balance_type'])

    # Cross Reference table (learning loop)
    op.create_table(
        'cross_references',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=True),
        sa.Column('po_item_code', sa.String(length=50), nullable=True),
        sa.Column('invoice_item_code', sa.String(length=50), nullable=True),
        sa.Column('dn_item_code', sa.String(length=50), nullable=True),
        sa.Column('normalized_po_item', sa.String(length=100), nullable=True),
        sa.Column('normalized_inv_item', sa.String(length=100), nullable=True),
        sa.Column('normalized_dn_item', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_by', sa.UUID(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cr_supplier_id', 'cross_references', ['supplier_id'])
    op.create_index('ix_cr_po_item_code', 'cross_references', ['po_item_code'])
    op.create_index('ix_cr_invoice_item_code', 'cross_references', ['invoice_item_code'])
    op.create_index('ix_cr_dn_item_code', 'cross_references', ['dn_item_code'])

def downgrade() -> None:
    op.drop_table('cross_references')
    op.drop_table('balance_ledger')
    op.drop_table('match_line_details')
    op.drop_table('matches')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('delivery_note_lines')
    op.drop_table('delivery_notes')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('suppliers')
    op.drop_table('users')
