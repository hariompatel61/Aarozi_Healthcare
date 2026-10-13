"""Add donors and donor_deferrals tables

Revision ID: 20241013_22
Revises: 20241013_21
Create Date: 2024-10-14 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_22'
down_revision: Union[str, None] = '20241013_21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'donors',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('donor_no', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('sex', sa.String(length=20), nullable=False, server_default='all'),
        sa.Column('blood_group', sa.String(length=20), nullable=True),  # O_POS, O_NEG, A_POS, A_NEG, B_POS, B_NEG, AB_POS, AB_NEG
        sa.Column('mobile', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('national_id', sa.String(length=64), nullable=True),
        sa.Column('abha_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),  # active, deferred_temporary, deferred_permanent, inactive
        sa.Column('last_donation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_donations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'donor_no', name='uq_donors_tenant_donor_no'),
    )
    op.create_index('ix_donors_tenant_id', 'donors', ['tenant_id'])
    op.create_index('ix_donors_mobile', 'donors', ['tenant_id', 'mobile'])
    op.create_index('ix_donors_blood_group', 'donors', ['tenant_id', 'blood_group'])
    op.create_index('ix_donors_status', 'donors', ['tenant_id', 'status'])

    op.create_table(
        'donor_deferrals',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('donor_id', sa.String(length=36), sa.ForeignKey('donors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deferral_type', sa.String(length=30), nullable=False),  # temporary, permanent
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('deferred_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),  # active, lifted
        sa.Column('lift_reason', sa.Text(), nullable=True),
        sa.Column('deferred_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lifted_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deferred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('lifted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_donor_deferrals_tenant_id', 'donor_deferrals', ['tenant_id'])
    op.create_index('ix_donor_deferrals_donor_id', 'donor_deferrals', ['donor_id'])
    op.create_index('ix_donor_deferrals_status', 'donor_deferrals', ['donor_id', 'status'])


def downgrade() -> None:
    op.drop_table('donor_deferrals')
    op.drop_table('donors')
