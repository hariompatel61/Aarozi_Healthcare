"""permission catalog - permissions"""

from alembic import op
import sqlalchemy as sa

revision = "20241012_03_permission_catalog"
down_revision = "20241012_02_identity_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column("module", sa.String(length=50), nullable=False, index=True),
        sa.Column("resource", sa.String(length=50), nullable=False, index=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="normal"),
    )


def downgrade() -> None:
    op.drop_table("permissions")
