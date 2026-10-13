"""Add donations and blood_units tables

Revision ID: 20241013_24
Revises: 20241013_23
Create Date: 2024-10-13 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_24'
down_revision: Union[str, None] = '20241013_23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'donations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('donor_id', sa.String(length=36), sa.ForeignKey('donors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('donor_screenings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('donation_no', sa.String(length=50), nullable=False),
        sa.Column('donation_type', sa.String(length=30), nullable=False, default='whole_blood'),  # whole_blood, plateletpheresis, etc.
        sa.Column('bag_type', sa.String(length=30), nullable=False, default='single'),  # single, double, triple, quadruple, apheresis
        sa.Column('volume_ml', sa.Integer(), nullable=False, default=450),
        sa.Column('blood_group', sa.String(length=20), nullable=True),
        sa.Column('venipuncture_site', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, default='completed'),  # completed, incomplete, adverse_reaction
        sa.Column('screening_status', sa.String(length=30), nullable=False, default='passed'),
        sa.Column('eligibility_status', sa.String(length=30), nullable=False, default='eligible'),
        sa.Column('deferral_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('collected_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('donated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_donations_tenant_id', 'donations', ['tenant_id'])
    op.create_index('ix_donations_donor_id', 'donations', ['donor_id'])
    op.create_index('ix_donations_status', 'donations', ['tenant_id', 'status'])
    op.create_unique_constraint('uq_donations_donation_no', 'donations', ['tenant_id', 'donation_no'])

    op.create_table(
        'blood_units',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('donation_id', sa.String(length=36), sa.ForeignKey('donations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('unit_no', sa.String(length=50), nullable=False),
        sa.Column('component_type', sa.String(length=50), nullable=False),  # whole_blood, packed_red_cells, fresh_frozen_plasma, etc.
        sa.Column('blood_group', sa.String(length=20), nullable=True),
        sa.Column('volume_ml', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, default='collected'),  # collected, testing, quarantined, released, reserved, issued, discarded
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('expiry_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_blood_units_tenant_id', 'blood_units', ['tenant_id'])
    op.create_index('ix_blood_units_donation_id', 'blood_units', ['donation_id'])
    op.create_index('ix_blood_stock', 'blood_units', ['tenant_id', 'blood_group', 'component_type', 'status', 'expiry_at'])
    op.create_unique_constraint('uq_blood_units_unit_no', 'blood_units', ['tenant_id', 'unit_no'])


def downgrade() -> None:
    op.drop_table('blood_units')
    op.drop_table('donations')
