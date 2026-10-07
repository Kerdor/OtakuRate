from otakurate.rating import (
    ANIME_CRITERIA,
    CRITERION_INFO,
    MANGA_CRITERIA,
    RatingCriterion,
    calculate_rating,
    validate_criteria,
    validate_rating,
)


def test_anime_has_ten_criteria_in_expected_order():
    assert ANIME_CRITERIA == (
        RatingCriterion.STORY,
        RatingCriterion.CHARACTERS,
        RatingCriterion.EMOTIONS,
        RatingCriterion.INTEREST,
        RatingCriterion.ATMOSPHERE,
        RatingCriterion.WORLD,
        RatingCriterion.DEVELOPMENT,
        RatingCriterion.VISUALS,
        RatingCriterion.SOUND,
        RatingCriterion.AFTERTASTE,
    )


def test_manga_has_ten_criteria_in_expected_order():
    assert MANGA_CRITERIA == (
        RatingCriterion.STORY,
        RatingCriterion.CHARACTERS,
        RatingCriterion.EMOTIONS,
        RatingCriterion.INTEREST,
        RatingCriterion.ATMOSPHERE,
        RatingCriterion.WORLD,
        RatingCriterion.DEVELOPMENT,
        RatingCriterion.DRAWING,
        RatingCriterion.PANELING,
        RatingCriterion.AFTERTASTE,
    )


def test_rating_criteria_are_unique():
    assert len(ANIME_CRITERIA) == len(set(ANIME_CRITERIA))
    assert len(MANGA_CRITERIA) == len(set(MANGA_CRITERIA))


def test_every_used_criterion_has_description_and_ten_score_descriptions():
    for criterion in set(ANIME_CRITERIA + MANGA_CRITERIA):
        info = CRITERION_INFO[criterion]
        assert info.name
        assert info.description
        assert len(info.score_descriptions) == 10
        assert all(info.score_descriptions)


def test_rating_accepts_only_integer_values_from_one_to_ten():
    assert validate_rating(1) == 1
    assert validate_rating(10) == 10
    for value in (0, 11, 8.5, True):
        try:
            validate_rating(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {value!r}")


def test_criteria_are_stored_as_raw_integer_values():
    assert validate_criteria({"story": 8, "characters": 9}) == {"story": 8, "characters": 9}


def test_weighted_rating_is_deterministic_and_rounded_to_integer():
    assert calculate_rating({"story": 8, "characters": 9}) == 9
    assert calculate_rating({"story": 8, "characters": 9}, {"story": 2, "characters": 1}) == 8
    assert calculate_rating({"story": 8, "characters": 9}, {"story": 1, "characters": 2}) == 9
