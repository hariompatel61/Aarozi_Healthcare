"""Add invoices and invoice_items tables

Revision ID: 20241013_08
Revises: 20241013_07
Create Date: 2024-10-13 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_08'
down_revision: Union[str, None] = '20241013_07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('invoice_no', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='issued'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('grand_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'invoice_no', name='uq_invoices_tenant_invoice_no'),
    )
    op.create_index('ix_invoices_tenant_id', 'invoices', ['tenant_id'])
    op.create_index('ix_invoices_branch_id', 'invoices', ['branch_id'])
    op.create_index('ix_invoices_patient_id', 'invoices', ['patient_id'])
    op.create_index('ix_invoices_order_id', 'invoices', ['order_id'])
    op.create_index('ix_invoices_tenant_status', 'invoices', ['tenant_id', 'status'])
    op.create_index('ix_invoices_tenant_patient', 'invoices', ['tenant_id', 'patient_id', 'status'])

    op.create_table(
        'invoice_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_item_id', sa.String(length=36), sa.ForeignKey('order_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('item_type', sa.String(length=30), nullable=False, server_default='test'),
        sa.Column('item_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('qty', sa.Numeric(precision=14, scale=3), nullable=False, server_default='1.000'),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_rate_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('line_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_invoice_items_tenant_id', 'invoice_items', ['tenant_id'])
    op.create_index('ix_invoice_items_invoice_id', 'invoice_items', ['invoice_id'])
    op.create_index('ix_invoice_items_order_item_id', 'invoice_items', ['order_item_id'])


def downgrade() -> None:
    op.drop_table('invoice_items')
    op.drop_table('invoices')
