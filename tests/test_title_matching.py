from otakurate.database import SessionLocal
from otakurate.domain.enums import MediaType
from otakurate.models import ExternalSource, ExternalTitle, Title, TitleMatchCandidate, MatchStatus
from otakurate.services.title_matching import find_title_by_external_id, should_merge_by_title_name


def test_external_id_is_primary_matching_signal():
    with SessionLocal.begin() as session:
        source = ExternalSource(key="match-source", name="Match Source")
        title = Title(title="Original", media_type=MediaType.ANIME)
        session.add_all([source, title])
        session.flush()
        session.add(ExternalTitle(source_id=source.id, title_id=title.id, external_id="42"))
        session.flush()
        assert find_title_by_external_id(session, source.id, "42").id == title.id


def test_unknown_external_id_does_not_match_by_name():
    with SessionLocal.begin() as session:
        source = ExternalSource(key="name-source", name="Name Source")
        title = Title(title="Same Name", media_type=MediaType.ANIME)
        session.add_all([source, title])
        session.flush()
        assert find_title_by_external_id(session, source.id, "missing") is None
        assert should_merge_by_title_name(existing_title=title, incoming_title="Same Name") is False


def test_match_candidate_stores_uncertain_match_and_confidence():
    with SessionLocal.begin() as session:
        source = ExternalSource(key="candidate-source", name="Candidate Source")
        title = Title(title="Candidate", media_type=MediaType.ANIME)
        session.add_all([source, title])
        session.flush()
        candidate = TitleMatchCandidate(
            source_id=source.id,
            external_id="99",
            candidate_title_id=title.id,
            confidence=0.72,
            status=MatchStatus.PENDING,
            evidence={"title_similarity": 0.72},
        )
        session.add(candidate)
        session.flush()
        assert candidate.status == MatchStatus.PENDING
        assert candidate.confidence == 0.72
