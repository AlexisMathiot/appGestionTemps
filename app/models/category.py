import re
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base
from app.models.user import utcnow

COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "(goal_type IS NULL) = (goal_value IS NULL)",
            name="ck_categories_goal_consistency",
        ),
        CheckConstraint(
            "goal_value > 0",
            name="ck_categories_goal_value_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # #RRGGBB
    goal_type: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "daily" | "weekly"
    goal_value: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # minutes
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Self-referential relationships
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    parent: Mapped["Category | None"] = relationship(
        "Category", back_populates="children", remote_side=[id]
    )

    # TimeEntry relationship
    time_entries = relationship("TimeEntry", back_populates="category")

    @validates("color")
    def validate_color(self, _key: str, value: str) -> str:
        if not COLOR_HEX_RE.match(value):
            raise ValueError(f"color must be #RRGGBB hex, got: {value!r}")
        return value
