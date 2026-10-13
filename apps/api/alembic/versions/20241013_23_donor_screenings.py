"""Add donor_screenings table

Revision ID: 20241013_23
Revises: 20241013_22
Create Date: 2024-10-13 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_23'
down_revision: Union[str, None] = '20241013_22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'donor_screenings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('donor_id', sa.String(length=36), sa.ForeignKey('donors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('screening_no', sa.String(length=50), nullable=False),
        sa.Column('weight_kg', sa.Numeric(5, 2), nullable=True),
        sa.Column('blood_pressure_systolic', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_diastolic', sa.Integer(), nullable=True),
        sa.Column('pulse_bpm', sa.Integer(), nullable=True),
        sa.Column('temperature_c', sa.Numeric(4, 2), nullable=True),
        sa.Column('hemoglobin_g_dl', sa.Numeric(4, 2), nullable=True),
        sa.Column('questionnaire_responses', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, default='passed'),  # passed, deferred_temporary, deferred_permanent, rejected
        sa.Column('eligibility_status', sa.String(length=30), nullable=False, default='eligible'),  # eligible, ineligible
        sa.Column('deferral_reason', sa.Text(), nullable=True),
        sa.Column('deferred_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deferral_id', sa.String(length=36), sa.ForeignKey('donor_deferrals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('screened_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('screened_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_donor_screenings_tenant_id', 'donor_screenings', ['tenant_id'])
    op.create_index('ix_donor_screenings_donor_id', 'donor_screenings', ['donor_id'])
    op.create_index('ix_donor_screenings_status', 'donor_screenings', ['tenant_id', 'status'])
    op.create_unique_constraint('uq_donor_screenings_screening_no', 'donor_screenings', ['tenant_id', 'screening_no'])


def downgrade() -> None:
    op.drop_table('donor_screenings')
