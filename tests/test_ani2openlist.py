from datetime import date

import pytest

from app.modules.ani2openlist import Ani2Openlist, iter_ani_open_seasons


def test_iter_ani_open_seasons_skips_2019_4_and_includes_current_quarter() -> None:
    seasons = iter_ani_open_seasons(today=date(2026, 4, 29))

    assert seasons[0] == (2019, 1)
    assert (2019, 4) not in seasons
    assert seasons[-1] == (2026, 4)


def test_get_season_key_skips_missing_2019_4() -> None:
    task = Ani2Openlist(url="http://openlist:5244", token="token")

    with pytest.raises(ValueError, match="2019-4"):
        task.get_season_key(2019, 4)


@pytest.mark.asyncio
async def test_openani_recursive_parser(monkeypatch) -> None:
    task = Ani2Openlist(url="http://openlist:5244", token="token")
    responses = {
        "https://openani.an-i.workers.dev/2026-4/": {
            "files": [
                {
                    "mimeType": "application/vnd.google-apps.folder",
                    "name": "Test Anime",
                }
            ]
        },
        "https://openani.an-i.workers.dev/2026-4/Test%20Anime/": {
            "files": [
                {
                    "mimeType": "video/mp4",
                    "name": "EP01.mp4",
                    "size": "123",
                    "createdTime": "2026-04-01T00:00:00.000Z",
                }
            ]
        },
    }

    class Response:
        status_code = 200

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    async def fake_post(url: str, **kwargs):
        return Response(responses[url])

    monkeypatch.setattr("app.modules.ani2openlist.ani2openlist.RequestUtils.post", fake_post)
    url_dict = {}

    await task.update_season_anime_dict(url_dict, year=2026, month=4)

    assert url_dict["2026-4"]["Test Anime"]["EP01.mp4"][0] == "123"
    assert url_dict["2026-4"]["Test Anime"]["EP01.mp4"][2].endswith("EP01.mp4?d=true")

