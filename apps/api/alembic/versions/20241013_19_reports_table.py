"""Add reports table

Revision ID: 20241013_19
Revises: 20241013_18
Create Date: 2024-10-14 06:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_19'
down_revision: Union[str, None] = '20241013_18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('result_id', sa.String(length=36), sa.ForeignKey('results.id', ondelete='CASCADE'), nullable=True),
        sa.Column('report_no', sa.String(length=64), nullable=False),
        sa.Column('template_id', sa.String(length=36), sa.ForeignKey('report_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qr_token', sa.String(length=128), nullable=True, unique=True),
        sa.Column('signature_hash', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'report_no', name='uq_reports_tenant_report_no'),
    )
    op.create_index('ix_reports_tenant_id', 'reports', ['tenant_id'])
    op.create_index('ix_reports_patient_id', 'reports', ['patient_id'])
    op.create_index('ix_reports_result_id', 'reports', ['result_id'])
    op.create_index('ix_reports_qr_token', 'reports', ['qr_token'])
    op.create_index('ix_reports_status', 'reports', ['tenant_id', 'status'])


def downgrade() -> None:
    op.drop_table('reports')
