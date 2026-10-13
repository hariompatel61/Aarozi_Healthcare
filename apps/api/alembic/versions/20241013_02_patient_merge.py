"""Patient merge audit schema and merged_into_patient_id column"""

from alembic import op
import sqlalchemy as sa

revision = "20241013_02_patient_merge"
down_revision = "20241013_01_patient_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("merged_into_patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_patients_merged_into", "patients", ["merged_into_patient_id"])

    op.create_table(
        "patient_merge_audits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("merge_details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_patient_merge_audits_tenant_created", "patient_merge_audits", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_patient_merge_audits_tenant_created", table_name="patient_merge_audits")
    op.drop_table("patient_merge_audits")
    op.drop_index("ix_patients_merged_into", table_name="patients")
    op.drop_column("patients", "merged_into_patient_id")
