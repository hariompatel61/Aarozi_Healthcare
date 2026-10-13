"""Test Master schema: tests and test_reference_ranges tables with versioning and specimens."""

from alembic import op
import sqlalchemy as sa

revision = "20241013_03_test_master"
down_revision = "20241013_02_patient_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=64), nullable=True),
        sa.Column("specimen_type", sa.String(length=100), nullable=True),
        sa.Column("container_type", sa.String(length=100), nullable=True),
        sa.Column("method", sa.String(length=100), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("decimal_precision", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("analyzer_code", sa.String(length=100), nullable=True),
        sa.Column("loinc_code", sa.String(length=64), nullable=True),
        sa.Column("calculation_formula", sa.Text(), nullable=True),
        sa.Column("is_calculated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active", index=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", "version", name="uq_tests_tenant_code_version"),
    )
    op.create_index("ix_tests_tenant_code", "tests", ["tenant_id", "code"])
    op.create_index("ix_tests_tenant_status", "tests", ["tenant_id", "status"])

    op.create_table(
        "test_reference_ranges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("test_id", sa.String(length=36), sa.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sex", sa.String(length=20), nullable=False, server_default="all"),
        sa.Column("age_min", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("age_max", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("low_value", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("high_value", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("critical_low", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("critical_high", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("text_range", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_test_ref_ranges_test_id", "test_reference_ranges", ["test_id"])


def downgrade() -> None:
    op.drop_index("ix_test_ref_ranges_test_id", table_name="test_reference_ranges")
    op.drop_table("test_reference_ranges")
    op.drop_index("ix_tests_tenant_status", table_name="tests")
    op.drop_index("ix_tests_tenant_code", table_name="tests")
    op.drop_table("tests")
