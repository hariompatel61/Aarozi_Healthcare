"""user role scope - user_roles"""

from alembic import op
import sqlalchemy as sa

revision = "20241012_05_user_role_scope"
down_revision = "20241012_04_role_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(length=36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("branch_scope_json", sa.JSON(), nullable=True),
        sa.Column("department_scope_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("user_roles")
