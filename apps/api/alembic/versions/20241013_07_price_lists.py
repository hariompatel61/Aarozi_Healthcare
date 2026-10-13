"""Add price_lists and price_list_items tables

Revision ID: 20241013_07
Revises: 20241013_06
Create Date: 2024-10-13 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_07'
down_revision: Union[str, None] = '20241013_06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'price_lists',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_price_lists_tenant_code'),
    )
    op.create_index('ix_price_lists_tenant_id', 'price_lists', ['tenant_id'])
    op.create_index('ix_price_lists_branch_id', 'price_lists', ['branch_id'])
    op.create_index('ix_price_lists_status', 'price_lists', ['tenant_id', 'status'])
    op.create_index('ix_price_lists_dates', 'price_lists', ['tenant_id', 'effective_from', 'effective_to'])

    op.create_table(
        'price_list_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price_list_id', sa.String(length=36), sa.ForeignKey('price_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_type', sa.String(length=30), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('rate', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('min_rate', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('max_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('price_list_id', 'item_type', 'item_id', name='uq_price_list_item_target'),
    )
    op.create_index('ix_price_list_items_tenant_id', 'price_list_items', ['tenant_id'])
    op.create_index('ix_price_list_items_price_list_id', 'price_list_items', ['price_list_id'])
    op.create_index('ix_price_list_items_item_lookup', 'price_list_items', ['tenant_id', 'item_type', 'item_id'])


def downgrade() -> None:
    op.drop_table('price_list_items')
    op.drop_table('price_lists')
