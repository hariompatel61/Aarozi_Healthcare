"""Add report_delivery table

Revision ID: 20241013_21
Revises: 20241013_20
Create Date: 2024-10-14 08:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_21'
down_revision: Union[str, None] = '20241013_20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'report_delivery',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(length=30), nullable=False),  # print, download, email, sms, whatsapp
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='sent'),  # queued, sent, delivered, failed, printed
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('dispatched_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_report_delivery_tenant_id', 'report_delivery', ['tenant_id'])
    op.create_index('ix_report_delivery_report_id', 'report_delivery', ['report_id'])
    op.create_index('ix_report_delivery_channel', 'report_delivery', ['tenant_id', 'channel'])
    op.create_index('ix_report_delivery_status', 'report_delivery', ['tenant_id', 'status'])


def downgrade() -> None:
    op.drop_table('report_delivery')
