from otakurate.database import Base
from otakurate.models import RatingCriterion, RatingProfile, RatingProfileCriterion, UserRating


def test_rating_profile_tables_are_registered():
    assert "rating_criteria" in Base.metadata.tables
    assert "rating_profiles" in Base.metadata.tables
    assert "rating_profile_criteria" in Base.metadata.tables


def test_rating_profile_has_version_and_media_type():
    assert RatingProfile.__table__.c.version.nullable is False
    assert RatingProfile.__table__.c.media_type.nullable is False


def test_rating_profile_criterion_has_weight_order_and_enabled():
    columns = RatingProfileCriterion.__table__.c
    assert columns.weight.nullable is False
    assert columns.order_index.nullable is False
    assert columns.enabled.nullable is False


def test_user_rating_stores_profile_version():
    assert UserRating.__table__.c.rating_profile_version.nullable is False


def test_rating_criterion_key_is_unique():
    assert RatingCriterion.__table__.c.key.unique is True