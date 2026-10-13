"""Profiles and Packages schema: profiles, profile_items, packages, and package_items tables."""

from alembic import op
import sqlalchemy as sa

revision = "20241013_04_profiles_and_packages"
down_revision = "20241013_03_test_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_profiles_tenant_code"),
    )
    op.create_index("ix_profiles_tenant_code", "profiles", ["tenant_id", "code"])
    op.create_index("ix_profiles_tenant_status", "profiles", ["tenant_id", "status"])

    op.create_table(
        "profile_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("test_id", sa.String(length=36), sa.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="1"),
        sa.UniqueConstraint("profile_id", "test_id", name="uq_profile_items_profile_test"),
    )
    op.create_index("ix_profile_items_profile_id", "profile_items", ["profile_id"])
    op.create_index("ix_profile_items_test_id", "profile_items", ["test_id"])

    op.create_table(
        "packages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_packages_tenant_code"),
    )
    op.create_index("ix_packages_tenant_code", "packages", ["tenant_id", "code"])
    op.create_index("ix_packages_tenant_status", "packages", ["tenant_id", "status"])

    op.create_table(
        "package_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("package_id", sa.String(length=36), sa.ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("test_id", sa.String(length=36), sa.ForeignKey("tests.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("profile_id", sa.String(length=36), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_package_items_package_id", "package_items", ["package_id"])
    op.create_index("ix_package_items_test_id", "package_items", ["test_id"])
    op.create_index("ix_package_items_profile_id", "package_items", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_package_items_profile_id", table_name="package_items")
    op.drop_index("ix_package_items_test_id", table_name="package_items")
    op.drop_index("ix_package_items_package_id", table_name="package_items")
    op.drop_table("package_items")

    op.drop_index("ix_packages_tenant_status", table_name="packages")
    op.drop_index("ix_packages_tenant_code", table_name="packages")
    op.drop_table("packages")

    op.drop_index("ix_profile_items_test_id", table_name="profile_items")
    op.drop_index("ix_profile_items_profile_id", table_name="profile_items")
    op.drop_table("profile_items")

    op.drop_index("ix_profiles_tenant_status", table_name="profiles")
    op.drop_index("ix_profiles_tenant_code", table_name="profiles")
    op.drop_table("profiles")
