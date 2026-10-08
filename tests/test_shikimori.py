import json
from unittest.mock import patch

from otakurate.domain.enums import MediaType
from otakurate.integrations.shikimori import ShikimoriAdapter


def test_shikimori_fetch_user_rates():
    payload = [
        {
            "id": 7,
            "target_id": 42,
            "target_type": "Anime",
            "status": "completed",
            "score": 9,
            "anime": {"id": 42, "name": "Test Anime", "russian": "Тестовое аниме"},
        }
    ]

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(payload).encode()

    with patch(
        "otakurate.integrations.shikimori.urlopen",
        return_value=Response(),
    ) as mocked:
        rates = ShikimoriAdapter().fetch_user_rates(
            external_user_id="123",
            media_type=MediaType.ANIME,
        )

    assert rates[0]["_media_type"] == "anime"
    assert {k: v for k, v in rates[0].items() if k != "_media_type"} == payload[0]
    mocked.assert_called_once()
