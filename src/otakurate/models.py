from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import CheckConstraint, JSON, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
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
    release_status: Mapped[ReleaseStatus | None] = mapped_column(Enum(ReleaseStatus, name="releasestatus"), nullable=True)
    genres: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ExternalSource(Base):
    __tablename__ = "external_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ExternalTitle(Base):
    __tablename__ = "external_titles"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "external_id",
            name="uq_external_titles_source_external_id",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    media_type: Mapped[MediaType | None] = mapped_column(Enum(MediaType, name="mediatype"), nullable=True)
    external_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alternative_titles: Mapped[list] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class MatchStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class TitleMatchCandidate(Base):
    __tablename__ = "title_match_candidates"
    __table_args__ = (UniqueConstraint("source_id", "external_id", "candidate_title_id", name="uq_title_match_candidates_source_external_title"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    candidate_title_id: Mapped[int | None] = mapped_column(ForeignKey("titles.id"), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus, name="matchstatus"), default=MatchStatus.PENDING, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class TitleRelationType(StrEnum):
    ADAPTATION = "adaptation"
    SEASON = "season"
    SEQUEL = "sequel"
    PREQUEL = "prequel"
    SPIN_OFF = "spin_off"
    SIDE_STORY = "side_story"
    ALTERNATIVE = "alternative"
    RELATED = "related"


class TitleRelation(Base):
    __tablename__ = "title_relations"
    __table_args__ = (
        CheckConstraint("source_title_id != target_title_id", name="ck_title_relations_not_self"),
        UniqueConstraint("source_title_id", "target_title_id", "relation_type", name="uq_title_relations_source_target_type"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    source_title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    target_title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    relation_type: Mapped[TitleRelationType] = mapped_column(Enum(TitleRelationType, name="titlerelationtype"), nullable=False)
    order_index: Mapped[int | None] = mapped_column(nullable=True)


class Franchise(Base):
    __tablename__ = "franchises"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class FranchiseTitle(Base):
    __tablename__ = "franchise_titles"
    __table_args__ = (UniqueConstraint("franchise_id", "title_id", name="uq_franchise_titles_franchise_title"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    franchise_id: Mapped[int] = mapped_column(ForeignKey("franchises.id"), nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    order_index: Mapped[int | None] = mapped_column(nullable=True)


class UserExternalAccount(Base):
    __tablename__ = "user_external_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "source_id",
            name="uq_user_external_accounts_user_source",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"), nullable=False)
    external_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class RatingCriterion(Base):
    __tablename__ = "rating_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class RatingProfile(Base):
    __tablename__ = "rating_profiles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_type", "profile_key", "version",
            name="uq_rating_profiles_user_media_key_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="ratingprofilemediatype"), nullable=False
    )
    profile_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)


class RatingProfileCriterion(Base):
    __tablename__ = "rating_profile_criteria"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "criterion_id",
            name="uq_rating_profile_criteria_profile_criterion",
        ),
        UniqueConstraint(
            "profile_id", "order_index",
            name="uq_rating_profile_criteria_profile_order",
        ),
        CheckConstraint("weight > 0", name="ck_rating_profile_criteria_weight_positive"),
        CheckConstraint("order_index >= 0", name="ck_rating_profile_criteria_order_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("rating_profiles.id"), nullable=False)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("rating_criteria.id"), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False)
    order_index: Mapped[int] = mapped_column(nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

class UserList(Base):
    __tablename__ = "user_lists"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "media_type", "name",
            name="uq_user_lists_user_media_name",
        ),
        UniqueConstraint(
            "user_id", "media_type", "system_key",
            name="uq_user_lists_user_media_system_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="userlistmediatype"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    system_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_system: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class LibraryEntry(Base):
    __tablename__ = "library_entries"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "title_id",
            name="uq_library_entries_user_title",
        ),
        CheckConstraint(
            "progress_current IS NULL OR progress_current >= 0",
            name="ck_library_entries_progress_current_nonnegative",
        ),
        CheckConstraint(
            "progress_total IS NULL OR progress_total > 0",
            name="ck_library_entries_progress_total_positive",
        ),
        CheckConstraint(
            "progress_current IS NULL OR progress_total IS NULL OR progress_current <= progress_total",
            name="ck_library_entries_progress_not_over_total",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("user_lists.id"),
        nullable=False,
    )
    progress_current: Mapped[int | None] = mapped_column(nullable=True)
    progress_total: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UserTag(Base):
    __tablename__ = "user_tags"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "name",
            name="uq_user_tags_user_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class LibraryEntryTag(Base):
    __tablename__ = "library_entry_tags"
    __table_args__ = (
        UniqueConstraint(
            "library_entry_id", "tag_id",
            name="uq_library_entry_tags_entry_tag",
        ),
    )

    library_entry_id: Mapped[int] = mapped_column(
        ForeignKey("library_entries.id"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("user_tags.id"),
        primary_key=True,
    )


class UserExternalRating(Base):
    __tablename__ = "user_external_ratings"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "external_title_id",
            name="uq_user_external_ratings_user_external_title",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    external_title_id: Mapped[int] = mapped_column(
        ForeignKey("external_titles.id"), nullable=False
    )
    rating: Mapped[float] = mapped_column(nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class UserRating(Base):
    __tablename__ = "user_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "title_id", name="uq_user_ratings_user_title"),
        CheckConstraint("overall_rating >= 1 AND overall_rating <= 10", name="ck_user_ratings_overall_range"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id"), nullable=False)
    overall_rating: Mapped[int] = mapped_column(nullable=False)
    criteria_values: Mapped[dict] = mapped_column(JSON, default=dict)
    rating_profile_version: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FriendRequestStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friend_requests_pair"),
        CheckConstraint("requester_id != addressee_id", name="ck_friend_requests_not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friendrequeststatus"),
        default=FriendRequestStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )


class FriendRequestStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friend_requests_pair"),
        CheckConstraint("requester_id != addressee_id", name="ck_friend_requests_not_self"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friendrequeststatus"),
        default=FriendRequestStatus.PENDING, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
