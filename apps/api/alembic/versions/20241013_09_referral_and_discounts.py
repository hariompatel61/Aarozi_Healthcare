"""Add referral partners, referral rules, and invoice partner linkage

Revision ID: 20241013_09
Revises: 20241013_08
Create Date: 2024-10-13 19:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_09'
down_revision: Union[str, None] = '20241013_08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'referral_partners',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('partner_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_referral_partners_tenant_id', 'referral_partners', ['tenant_id'])
    op.create_index('ix_referral_partners_status', 'referral_partners', ['tenant_id', 'status'])

    op.create_table(
        'referral_rules',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('partner_id', sa.String(length=36), sa.ForeignKey('referral_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scope_type', sa.String(length=50), nullable=False, server_default='all'),
        sa.Column('scope_id', sa.String(length=36), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_discount_pct', sa.Numeric(precision=7, scale=4), nullable=False, server_default='0.0'),
        sa.Column('commission_pct', sa.Numeric(precision=7, scale=4), nullable=False, server_default='0.0'),
        sa.Column('commission_fixed', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_referral_rules_tenant_id', 'referral_rules', ['tenant_id'])
    op.create_index('ix_referral_rules_partner_id', 'referral_rules', ['partner_id'])
    op.create_index('ix_referral_rules_lookup', 'referral_rules', ['tenant_id', 'partner_id', 'status'])

    with op.batch_alter_table('invoices') as batch_op:
        batch_op.add_column(sa.Column('referral_partner_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_invoices_referral_partner',
            'referral_partners',
            ['referral_partner_id'],
            ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_index('ix_invoices_referral_partner_id', ['referral_partner_id'])


def downgrade() -> None:
    with op.batch_alter_table('invoices') as batch_op:
        batch_op.drop_constraint('fk_invoices_referral_partner', type_='foreignkey')
        batch_op.drop_index('ix_invoices_referral_partner_id')
        batch_op.drop_column('referral_partner_id')

    op.drop_table('referral_rules')
    op.drop_table('referral_partners')
