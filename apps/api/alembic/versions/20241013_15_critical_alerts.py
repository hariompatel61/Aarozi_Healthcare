"""Add critical_alerts table

Revision ID: 20241013_15
Revises: 20241013_14
Create Date: 2024-10-14 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_15'
down_revision: Union[str, None] = '20241013_14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'critical_alerts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('result_id', sa.String(length=36), sa.ForeignKey('results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('result_value_id', sa.String(length=36), sa.ForeignKey('result_values.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analyte_code', sa.String(length=64), nullable=False),
        sa.Column('flag', sa.String(length=30), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending_acknowledgement'),
        sa.Column('communicated_to', sa.String(length=255), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_critical_alerts_tenant_id', 'critical_alerts', ['tenant_id'])
    op.create_index('ix_critical_alerts_status', 'critical_alerts', ['tenant_id', 'status'])
    op.create_index('ix_critical_alerts_patient_id', 'critical_alerts', ['patient_id'])
    op.create_index('ix_critical_alerts_result_id', 'critical_alerts', ['result_id'])


def downgrade() -> None:
    op.drop_table('critical_alerts')
