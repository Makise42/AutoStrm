from pathlib import Path


def test_run_sh_menu_text() -> None:
    content = Path("run.sh").read_text(encoding="utf-8")

    assert "3. 拉取所有Ani Open番剧" in content
    assert '"$PYTHON_BIN" -m app.main o2s' in content
    assert '"$PYTHON_BIN" -m app.main a2o' in content
    assert '"$PYTHON_BIN" -m app.main a2o-all' in content


def test_config_uses_short_top_level_keys() -> None:
    content = Path("config/config.yaml.example").read_text(encoding="utf-8")

    assert "Openlist2Strm:" in content
    assert "Ani2Openlist:" in content
    assert "Openlist2StrmList" not in content
    assert "Ani2OpenlistList" not in content
