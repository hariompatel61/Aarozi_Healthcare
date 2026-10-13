"""Add digital_signatures table

Revision ID: 20241013_20
Revises: 20241013_19
Create Date: 2024-10-14 07:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_20'
down_revision: Union[str, None] = '20241013_19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'digital_signatures',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('qualifications', sa.String(length=255), nullable=True),
        sa.Column('designation', sa.String(length=255), nullable=True),
        sa.Column('registration_no', sa.String(length=100), nullable=True),
        sa.Column('signature_image_data', sa.Text(), nullable=True),
        sa.Column('stamp_text', sa.String(length=255), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_digital_signatures_tenant_user'),
    )
    op.create_index('ix_digital_signatures_tenant_id', 'digital_signatures', ['tenant_id'])
    op.create_index('ix_digital_signatures_user_id', 'digital_signatures', ['user_id'])
    op.create_index('ix_digital_signatures_status', 'digital_signatures', ['tenant_id', 'status'])


def downgrade() -> None:
    op.drop_table('digital_signatures')
