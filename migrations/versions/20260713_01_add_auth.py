"""add authenticated ownership and group membership"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260713_01"
down_revision = "20260709_01"
branch_labels = None
depends_on = None

group_role = postgresql.ENUM("owner", "member", name="group_role", create_type=False)


def upgrade() -> None:
    op.alter_column("events", "created_by", new_column_name="owner_id")
    op.alter_column(
        "events",
        "owner_id",
        existing_type=sa.String(200),
        type_=sa.Uuid(),
        postgresql_using="owner_id::uuid",
    )
    op.drop_index("ix_events_created_by", table_name="events")
    op.create_index("ix_events_owner_id", "events", ["owner_id"])
    op.alter_column(
        "votes",
        "voter_id",
        existing_type=sa.String(200),
        type_=sa.Uuid(),
        postgresql_using="voter_id::uuid",
    )

    group_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "group_members",
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", group_role, nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )
    op.create_index("ix_group_members_user_id", "group_members", ["user_id"])
    op.execute(
        """
        INSERT INTO group_members (group_id, user_id, role, joined_at)
        SELECT DISTINCT eg.group_id, e.owner_id, 'owner'::group_role, CURRENT_TIMESTAMP
        FROM event_groups AS eg
        JOIN events AS e ON e.id = eg.event_id
        ON CONFLICT (group_id, user_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_group_members_user_id", table_name="group_members")
    op.drop_table("group_members")
    group_role.drop(op.get_bind(), checkfirst=True)
    op.alter_column(
        "votes",
        "voter_id",
        existing_type=sa.Uuid(),
        type_=sa.String(200),
        postgresql_using="voter_id::text",
    )
    op.drop_index("ix_events_owner_id", table_name="events")
    op.alter_column(
        "events",
        "owner_id",
        existing_type=sa.Uuid(),
        type_=sa.String(200),
        postgresql_using="owner_id::text",
    )
    op.alter_column("events", "owner_id", new_column_name="created_by")
    op.create_index("ix_events_created_by", "events", ["created_by"])

