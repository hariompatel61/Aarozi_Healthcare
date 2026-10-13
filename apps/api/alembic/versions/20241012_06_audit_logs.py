"""audit logs - audit foundation"""

from alembic import op
import sqlalchemy as sa

revision = "20241012_06_audit_logs"
down_revision = "20241012_05_user_role_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("branch_id", sa.String(length=36), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("action_code", sa.String(length=100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True, index=True),
        sa.Column("entity_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
