from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..integrations.base import ExternalCapability, UserListAdapter
from ..integrations.mapping import map_rating, map_status, normalize_external_id, normalize_title_name
from ..models import (
    ExternalSource,
    ExternalTitle,
    Title,
    TitleMatchCandidate,
    UserExternalAccount,
    UserExternalRating,
    UserList,
)
from .external_titles import ensure_external_source
from .library_entries import add_to_list


@dataclass(frozen=True)
class ImportConflict:
    external_id: str
    title: str
    reason: str
    candidate_title_ids: tuple[int, ...] = ()


@dataclass
class ImportReport:
    imported: int = 0
    created_titles: int = 0
    linked_titles: int = 0
    conflicts: list[ImportConflict] = field(default_factory=list)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _normalize_name(value: str) -> str:
    return normalize_title_name(value)


def _find_name_candidates(
    session: Session,
    *,
    title: str,
    media_type: MediaType,
) -> list[Title]:
    normalized = _normalize_name(title)
    return [
        item
        for item in session.scalars(
            select(Title).where(Title.media_type == media_type)
        )
        if _normalize_name(item.title) == normalized
    ]


def _get_system_list(
    session: Session,
    *,
    user_id: int,
    media_type: MediaType,
    key: str,
) -> UserList | None:
    return session.scalar(
        select(UserList).where(
            UserList.user_id == user_id,
            UserList.media_type == media_type,
            UserList.system_key == key,
        )
    )


def _save_external_rating(
    session: Session,
    *,
    user_id: int,
    external_title_id: int,
    rating: float | int,
) -> None:
    current = session.scalar(
        select(UserExternalRating).where(
            UserExternalRating.user_id == user_id,
            UserExternalRating.external_title_id == external_title_id,
        )
    )
    if current is None:
        session.add(
            UserExternalRating(
                user_id=user_id,
                external_title_id=external_title_id,
                rating=float(rating),
            )
        )
    else:
        current.rating = float(rating)


def import_shikimori_rates(
    session: Session,
    *,
    user_id: int,
    external_user_id: str,
    adapter,
    media_type: MediaType | None = None,
) -> ImportReport:
    source = ensure_external_source(
        session,
        key="shikimori",
        name="Shikimori",
        base_url="https://shikimori.one",
    )
    rates = adapter.fetch_user_rates(
        external_user_id=external_user_id,
        media_type=media_type,
    )
    report = ImportReport()

    for raw_rate in rates:
        rate = adapter._normalize_user_rate(raw_rate)
        item_type = rate["media_type"]
        try:
            external_id = normalize_external_id(rate["external_id"])
        except ValueError:
            report.conflicts.append(
                ImportConflict("", "", "External rate has no target ID.")
            )
            continue

        external_title = session.scalar(
            select(ExternalTitle).where(
                ExternalTitle.source_id == source.id,
                ExternalTitle.external_id == external_id,
            )
        )

        target = rate["target"]
        title_name = target.get("russian") or target.get("name") or external_id

        if external_title is None:
            candidates = _find_name_candidates(
                session, title=title_name, media_type=item_type
            )
            if candidates:
                report.conflicts.append(
                    ImportConflict(
                        external_id=external_id,
                        title=title_name,
                        reason="Existing titles with the same name require manual matching.",
                        candidate_title_ids=tuple(item.id for item in candidates),
                    )
                )
                for candidate in candidates:
                    session.add(
                        TitleMatchCandidate(
                            source_id=source.id,
                            external_id=external_id,
                            candidate_title_id=candidate.id,
                            confidence=1.0,
                            evidence={"reason": "exact_name_match"},
                        )
                    )

            title = Title(
                title=title_name,
                media_type=item_type,
                alternative_titles=[
                    value
                    for value in (target.get("name"), target.get("russian"))
                    if value and value != title_name
                ],
                description=target.get("description"),
                cover_url=(target.get("image") or {}).get("original"),
                release_date=_parse_date(
                    target.get("aired_on") or target.get("released_on")
                ),
                extra_metadata={
                    key: target.get(key)
                    for key in (
                        "kind", "status", "score", "episodes",
                        "episodes_aired", "chapters", "volumes",
                    )
                    if target.get(key) not in (None, "")
                },
            )
            session.add(title)
            session.flush()
            external_title = ExternalTitle(
                title_id=title.id,
                source_id=source.id,
                external_id=external_id,
                media_type=item_type,
                external_title=title_name,
                alternative_titles=title.alternative_titles,
                extra_metadata=title.extra_metadata,
                url=(
                    f"https://shikimori.one/"
                    f"{'animes' if item_type == MediaType.ANIME else 'mangas'}/"
                    f"{external_id}"
                ),
            )
            session.add(external_title)
            session.flush()
            report.created_titles += 1
        else:
            title = session.get(Title, external_title.title_id)
            if title is None:
                report.conflicts.append(
                    ImportConflict(
                        external_id=external_id,
                        title=title_name,
                        reason="External ID points to a missing local title.",
                    )
                )
                continue
            report.linked_titles += 1

        list_key = map_status(item_type, rate["status"])
        if list_key is None:
            report.conflicts.append(
                ImportConflict(
                    external_id=external_id,
                    title=title.title,
                    reason=f"Unsupported external status: {rate['status']!r}.",
                )
            )
            continue

        user_list = _get_system_list(
            session,
            user_id=user_id,
            media_type=item_type,
            key=list_key,
        )
        if user_list is None:
            report.conflicts.append(
                ImportConflict(
                    external_id=external_id,
                    title=title.title,
                    reason=f"System list {list_key!r} is missing.",
                )
            )
            continue

        add_to_list(
            session,
            user_id=user_id,
            title_id=title.id,
            list_id=user_list.id,
        )

        rating = map_rating(rate["rating"])
        if rating is not None:
            _save_external_rating(
                session,
                user_id=user_id,
                external_title_id=external_title.id,
                rating=rating,
            )

        report.imported += 1

    account = session.scalar(
        select(UserExternalAccount).where(
            UserExternalAccount.user_id == user_id,
            UserExternalAccount.source_id == source.id,
        )
    )
    if account is None:
        session.add(
            UserExternalAccount(
                user_id=user_id,
                source_id=source.id,
                external_user_id=external_user_id,
            )
        )
    else:
        account.external_user_id = external_user_id

    session.flush()
    return report
