"""create event coordination tables"""

from alembic import op
import sqlalchemy as sa

revision = "20260709_01"
down_revision = None
branch_labels = None
depends_on = None

vote_choice = sa.Enum("going", "maybe", "no", name="vote_choice")


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("invite_code", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_invite_code", "groups", ["invite_code"], unique=True)
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_created_by", "events", ["created_by"])
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_table(
        "event_groups",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "group_id"),
    )
    vote_choice.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("voter_id", sa.String(200), nullable=False),
        sa.Column("choice", vote_choice, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "voter_id", name="uq_vote_event_voter"),
    )
    op.create_index("ix_votes_event_id", "votes", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_votes_event_id", table_name="votes")
    op.drop_table("votes")
    vote_choice.drop(op.get_bind(), checkfirst=True)
    op.drop_table("event_groups")
    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_index("ix_events_created_by", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_groups_invite_code", table_name="groups")
    op.drop_table("groups")

