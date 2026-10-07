from datetime import date, datetime, timezone\nfrom enum import StrEnum

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .domain.enums import MediaType


class ReleaseStatus(StrEnum):
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


class ExternalSource(Base):
    __tablename__ = "external_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ExternalTitle(Base):
    __tablename__ = "external_titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    media_type: Mapped[MediaType | None] = mapped_column(
        Enum(MediaType, name="mediatype"),
        nullable=True,
    )
    external_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    alternative_titles: Mapped[list] = mapped_column(JSON, default=list)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class UserExternalAccount(Base):
    __tablename__ = "user_external_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(nullable=False)
    external_user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    external_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
