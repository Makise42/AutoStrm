from pathlib import Path

from app.modules.openlist.path import OpenlistPath
from app.modules.openlist2strm import Openlist2Strm


def make_path(name: str, full_path: str = "/source/Movie.mkv") -> OpenlistPath:
    return OpenlistPath(
        server_url="http://openlist:5244",
        base_path="",
        full_path=full_path,
        name=name,
        size=100,
        is_dir=False,
        modified="2026-04-29T00:00:00+00:00",
        created="2026-04-29T00:00:00+00:00",
    )


def test_other_ext_video_is_downloaded_with_original_suffix(tmp_path: Path) -> None:
    task = Openlist2Strm(
        url="http://openlist:5244",
        token="token",
        source_dir="/source",
        target_dir=str(tmp_path),
        other_ext="mkv,.ZIP",
    )
    path = make_path("Movie.mkv", "/source/Movie.mkv")

    assert task.download_exts == {".mkv", ".zip"}
    assert task.get_local_path(path) == tmp_path / "Movie.mkv"


def test_normal_video_generates_strm(tmp_path: Path) -> None:
    task = Openlist2Strm(
        url="http://openlist:5244",
        token="token",
        source_dir="/source",
        target_dir=str(tmp_path),
    )
    path = make_path("Movie.mkv", "/source/Movie.mkv")

    assert task.get_local_path(path) == tmp_path / "Movie.strm"


def test_openlist_url_public_url_rewrite(tmp_path: Path) -> None:
    task = Openlist2Strm(
        url="http://openlist:5244",
        public_url="https://media.example.com",
        token="token",
        source_dir="/source",
        target_dir=str(tmp_path),
    )
    path = make_path("Movie.mkv", "/source/Movie.mkv")

    assert task.build_strm_content(path).startswith("https://media.example.com/d/")

