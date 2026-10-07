from enum import StrEnum

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class MediaType(StrEnum):
    ANIME = "anime"
    MANGA = "manga"


class Title(Base):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[MediaType]
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict)
