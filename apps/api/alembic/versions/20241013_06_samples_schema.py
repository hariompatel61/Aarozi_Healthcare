"""Add samples table

Revision ID: 20241013_06
Revises: 20241013_05
Create Date: 2024-10-13 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_06'
down_revision: Union[str, None] = '20241013_05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'samples',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_item_id', sa.String(length=36), sa.ForeignKey('order_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('barcode', sa.String(length=64), nullable=False),
        sa.Column('specimen_type', sa.String(length=100), nullable=True),
        sa.Column('container_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ordered'),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'barcode', name='uq_samples_tenant_barcode'),
    )
    op.create_index('ix_samples_tenant_id', 'samples', ['tenant_id'])
    op.create_index('ix_samples_order_item_id', 'samples', ['order_item_id'])
    op.create_index('ix_samples_barcode', 'samples', ['barcode'])
    op.create_index('ix_samples_tenant_status', 'samples', ['tenant_id', 'status'])
    op.create_index('idx_sample_queue', 'samples', ['tenant_id', 'status', 'received_at'])


def downgrade() -> None:
    op.drop_table('samples')
