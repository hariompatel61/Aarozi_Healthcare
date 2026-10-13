"""patient and patient identifier schema"""

from alembic import op
import sqlalchemy as sa

revision = "20241013_01_patient_schema"
down_revision = "20241012_06_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("branch_id", sa.String(length=36), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("patient_no", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("middle_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(length=20), nullable=True),
        sa.Column("mobile_normalized", sa.String(length=30), nullable=True, index=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("blood_group", sa.String(length=10), nullable=True),
        sa.Column("address_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("emergency_contact_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "patient_no", name="uq_patients_tenant_patient_no"),
    )
    op.create_index("ix_patients_tenant_mobile", "patients", ["tenant_id", "mobile_normalized"])
    op.create_index("ix_patients_tenant_names", "patients", ["tenant_id", "last_name", "first_name"])

    op.create_table(
        "patient_identifiers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("identifier_type", sa.String(length=50), nullable=False),
        sa.Column("identifier_value", sa.String(length=100), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "identifier_type", "identifier_value", name="uq_patient_identifiers_tenant_type_val"),
    )


def downgrade() -> None:
    op.drop_table("patient_identifiers")
    op.drop_index("ix_patients_tenant_names", table_name="patients")
    op.drop_index("ix_patients_tenant_mobile", table_name="patients")
    op.drop_table("patients")
