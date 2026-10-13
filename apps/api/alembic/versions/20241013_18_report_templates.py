"""Add report_templates table

Revision ID: 20241013_18
Revises: 20241013_17
Create Date: 2024-10-14 05:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_18'
down_revision: Union[str, None] = '20241013_17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'report_templates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='pathology'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('schema_json', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'code', 'version', name='uq_report_templates_tenant_code_version'),
    )
    op.create_index('ix_report_templates_tenant_id', 'report_templates', ['tenant_id'])
    op.create_index('ix_report_templates_code', 'report_templates', ['code'])
    op.create_index('ix_report_templates_status', 'report_templates', ['status'])
    op.create_index('ix_report_templates_category', 'report_templates', ['category'])


def downgrade() -> None:
    op.drop_table('report_templates')
