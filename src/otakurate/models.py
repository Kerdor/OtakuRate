from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .domain.enums import MediaType


class ReleaseStatus(str, __import__("enum").Enum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    FINISHED = "finished"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"


class Title(Base):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    alternative_titles: Mapped[list] = mapped_column(JSON, default=list)
    media_type: Mapped[MediaType]
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    release_status: Mapped[ReleaseStatus | None] = mapped_column(
        Enum(ReleaseStatus, name="releasestatus"),
        nullable=True,
    )
    genres: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
