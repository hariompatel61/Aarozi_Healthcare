"""Add payments table

Revision ID: 20241013_10
Revises: 20241013_09
Create Date: 2024-10-13 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_10'
down_revision: Union[str, None] = '20241013_09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('provider_reference', sa.String(length=255), nullable=True),
        sa.Column('receipt_no', sa.String(length=64), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='success'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'receipt_no', name='uq_payments_tenant_receipt_no'),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_payments_tenant_idempotency_key'),
    )
    op.create_index('ix_payments_tenant_id', 'payments', ['tenant_id'])
    op.create_index('ix_payments_invoice_id', 'payments', ['invoice_id'])
    op.create_index('ix_payments_idempotency_key', 'payments', ['idempotency_key'])
    op.create_index('idx_payments_invoice', 'payments', ['invoice_id', 'received_at'])


def downgrade() -> None:
    op.drop_index('idx_payments_invoice', table_name='payments')
    op.drop_index('ix_payments_idempotency_key', table_name='payments')
    op.drop_index('ix_payments_invoice_id', table_name='payments')
    op.drop_index('ix_payments_tenant_id', table_name='payments')
    op.drop_table('payments')
