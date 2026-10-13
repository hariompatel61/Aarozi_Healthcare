"""Add commission_ledger table

Revision ID: 20241013_12
Revises: 20241013_11
Create Date: 2024-10-13 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_12'
down_revision: Union[str, None] = '20241013_11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'commission_ledger',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referral_partner_id', sa.String(length=36), sa.ForeignKey('referral_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settlement_reference', sa.String(length=128), nullable=True),
        sa.Column('settled_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('breakdown_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_commission_ledger_tenant_id', 'commission_ledger', ['tenant_id'])
    op.create_index('ix_commission_ledger_partner_id', 'commission_ledger', ['referral_partner_id'])
    op.create_index('ix_commission_ledger_invoice_id', 'commission_ledger', ['invoice_id'])
    op.create_index('ix_commission_ledger_tenant_status', 'commission_ledger', ['tenant_id', 'status'])
    op.create_index('ix_commission_ledger_partner_status', 'commission_ledger', ['tenant_id', 'referral_partner_id', 'status'])


def downgrade() -> None:
    op.drop_table('commission_ledger')
