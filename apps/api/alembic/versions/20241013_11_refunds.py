"""Add refunds table and refund_total on invoices

Revision ID: 20241013_11
Revises: 20241013_10
Create Date: 2024-10-13 22:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_11'
down_revision: Union[str, None] = '20241013_10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'invoices',
        sa.Column('refund_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
    )
    op.create_table(
        'refunds',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('payment_id', sa.String(length=36), sa.ForeignKey('payments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('refund_no', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='completed'),
        sa.Column('provider_reference', sa.String(length=255), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('processed_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'refund_no', name='uq_refunds_tenant_refund_no'),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_refunds_tenant_idempotency_key'),
    )
    op.create_index('ix_refunds_tenant_id', 'refunds', ['tenant_id'])
    op.create_index('ix_refunds_invoice_id', 'refunds', ['invoice_id'])
    op.create_index('ix_refunds_idempotency_key', 'refunds', ['idempotency_key'])
    op.create_index('idx_refunds_invoice', 'refunds', ['invoice_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_refunds_invoice', table_name='refunds')
    op.drop_index('ix_refunds_idempotency_key', table_name='refunds')
    op.drop_index('ix_refunds_invoice_id', table_name='refunds')
    op.drop_index('ix_refunds_tenant_id', table_name='refunds')
    op.drop_table('refunds')
    op.drop_column('invoices', 'refund_total')
