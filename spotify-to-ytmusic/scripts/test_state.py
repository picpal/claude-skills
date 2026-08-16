"""state.py 단위 테스트."""

import json

import pytest

import state


@pytest.fixture(autouse=True)
def tmp_home(tmp_path, monkeypatch):
    """모든 테스트가 실제 홈 디렉토리를 건드리지 않도록 격리한다."""
    monkeypatch.setenv("SPOTIFY_TO_YTMUSIC_HOME", str(tmp_path))
    return tmp_path


def test_data_home_follows_env(tmp_home):
    assert state.data_home() == tmp_home
    assert state.state_dir() == tmp_home / "state"
    assert state.report_dir() == tmp_home / "reports"
    assert state.auth_file() == tmp_home / "browser.json"


def test_new_state_has_expected_shape():
    st = state.new_state("pl1", "My List")
    assert st["spotify_playlist_id"] == "pl1"
    assert st["spotify_playlist_name"] == "My List"
    assert st["yt_playlist_id"] is None
    assert st["matched"] == {}
    assert st["unmatched"] == []
    assert st["last_sync"] is None


def test_load_state_returns_new_state_when_missing():
    st = state.load_state("nope", "Fresh")
    assert st["spotify_playlist_id"] == "nope"
    assert st["matched"] == {}


def test_save_then_load_roundtrip(tmp_home):
    st = state.new_state("pl1", "My List")
    st["yt_playlist_id"] = "PLabc"
    st["matched"]["t1"] = {"video_id": "v1", "score": 0.91, "yt_title": "Song"}
    path = state.save_state(st)

    assert path == tmp_home / "state" / "pl1.json"
    loaded = state.load_state("pl1")
    assert loaded["yt_playlist_id"] == "PLabc"
    assert loaded["matched"]["t1"]["score"] == 0.91


def test_save_state_sets_last_sync():
    st = state.new_state("pl1", "My List")
    state.save_state(st)
    assert st["last_sync"] is not None
    assert state.load_state("pl1")["last_sync"] == st["last_sync"]


def test_save_state_creates_directory(tmp_home):
    assert not (tmp_home / "state").exists()
    state.save_state(state.new_state("pl1", "My List"))
    assert (tmp_home / "state").is_dir()


def test_state_path_sanitizes_playlist_id():
    """경로 구분자가 섞인 id로 디렉토리를 탈출하지 못하게 한다."""
    assert state.state_path("../../etc/passwd").parent == state.state_dir()


def test_saved_file_is_readable_json(tmp_home):
    state.save_state(state.new_state("pl1", "한글 리스트"))
    raw = (tmp_home / "state" / "pl1.json").read_text(encoding="utf-8")
    assert json.loads(raw)["spotify_playlist_name"] == "한글 리스트"


def test_load_state_raises_on_corrupt_file(tmp_home):
    """조용히 새 state를 만들면 yt_playlist_id를 잃고 중복 플레이리스트가 생긴다."""
    (tmp_home / "state").mkdir(parents=True)
    (tmp_home / "state" / "pl1.json").write_text('{"broken": ', encoding="utf-8")
    with pytest.raises(state.StateCorrupted):
        state.load_state("pl1")


def test_load_state_raises_on_wrong_shape(tmp_home):
    (tmp_home / "state").mkdir(parents=True)
    (tmp_home / "state" / "pl1.json").write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(state.StateCorrupted):
        state.load_state("pl1")


def test_save_state_leaves_no_temp_file(tmp_home):
    state.save_state(state.new_state("pl1", "My List"))
    assert list((tmp_home / "state").glob("*.tmp")) == []
