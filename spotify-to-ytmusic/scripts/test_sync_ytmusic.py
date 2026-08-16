"""sync_ytmusic.py 테스트.

순수 함수(응답 파싱·검증)와, ytmusicapi를 흉내내는 fake 클라이언트로
sync_playlist 흐름 전체를 검증한다. 네트워크를 쓰지 않는다.
"""

import pytest

import state as state_module
import sync_ytmusic
from sync_ytmusic import (
    YTDuplicateError,
    YTWriteError,
    parse_duration,
    to_candidate,
    validate_add_response,
    validate_create_response,
)


@pytest.fixture(autouse=True)
def tmp_home(tmp_path, monkeypatch):
    """홈 디렉토리 격리 + 테스트가 실제로 잠들지 않게 한다."""
    monkeypatch.setenv("SPOTIFY_TO_YTMUSIC_HOME", str(tmp_path))
    monkeypatch.setattr(sync_ytmusic.time, "sleep", lambda _s: None)
    return tmp_path


# --------------------------------------------------------------------------
# 순수 함수
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("3:52", 232),
        ("1:03:52", 3832),
        ("0:45", 45),
        (232, 232),
        (None, None),
        ("", None),
        ("알 수 없음", None),
    ],
)
def test_parse_duration(value, expected):
    assert parse_duration(value) == expected


def test_to_candidate_maps_search_result():
    result = {
        "videoId": "abc123",
        "title": "Perfect",
        "artists": [{"name": "Ed Sheeran", "id": "x"}],
        "duration": "4:23",
    }
    assert to_candidate(result) == {
        "video_id": "abc123",
        "title": "Perfect",
        "artists": ["Ed Sheeran"],
        "duration_sec": 263,
    }


def test_to_candidate_prefers_duration_seconds_field():
    result = {
        "videoId": "abc123",
        "title": "Perfect",
        "artists": [{"name": "Ed Sheeran"}],
        "duration_seconds": 263,
    }
    assert to_candidate(result)["duration_sec"] == 263


def test_to_candidate_without_video_id_returns_none():
    assert to_candidate({"title": "Perfect", "artists": []}) is None


def test_to_candidate_tolerates_missing_duration():
    cand = to_candidate({"videoId": "abc", "title": "T", "artists": [{"name": "A"}]})
    assert cand["duration_sec"] is None


def test_to_candidate_tolerates_string_artists():
    """ytmusicapi가 아티스트를 문자열로 주는 경우도 있다."""
    cand = to_candidate({"videoId": "abc", "title": "T", "artists": ["A", {"name": "B"}]})
    assert cand["artists"] == ["A", "B"]


def test_validate_create_response_returns_id():
    assert validate_create_response("PLabc123") == "PLabc123"


def test_validate_create_response_rejects_dict():
    """실패 시 create_playlist는 응답 dict를 그대로 돌려준다. 저장하면 안 된다."""
    with pytest.raises(YTWriteError):
        validate_create_response({"error": {"code": 400}})


def test_validate_create_response_rejects_empty_string():
    with pytest.raises(YTWriteError):
        validate_create_response("   ")


def test_validate_add_response_accepts_success():
    validate_add_response({"status": "STATUS_SUCCEEDED", "playlistEditResults": []})


def test_validate_add_response_detects_duplicate():
    """duplicates=False는 중복이 있으면 에러를 반환하고 아무것도 추가하지 않는다."""
    with pytest.raises(YTDuplicateError):
        validate_add_response(
            {"status": "STATUS_FAILED", "message": "Cannot add duplicate items"}
        )


def test_validate_add_response_rejects_other_failure():
    with pytest.raises(YTWriteError):
        validate_add_response({"status": "STATUS_FAILED", "message": "quota exceeded"})


def test_validate_add_response_rejects_non_dict():
    with pytest.raises(YTWriteError):
        validate_add_response("ok")


# --------------------------------------------------------------------------
# sync_playlist 흐름 (fake 클라이언트)
# --------------------------------------------------------------------------


class FakeYT:
    """ytmusicapi 인터페이스를 흉내내는 최소 구현."""

    def __init__(
        self,
        create_result="PLfake",
        add_response=None,
        search_error=None,
        missing_playlist=False,
    ):
        self.create_result = create_result
        self.add_response = add_response or {"status": "STATUS_SUCCEEDED"}
        self.search_error = search_error
        self.missing_playlist = missing_playlist
        self.created = []
        self.added = []
        self.searches = []

    def search(self, query, filter=None, limit=5):
        self.searches.append(query)
        if self.search_error:
            raise self.search_error
        return [
            {
                "videoId": "vid1",
                "title": "Perfect",
                "artists": [{"name": "Ed Sheeran"}],
                "duration_seconds": 263,
            }
        ]

    def create_playlist(self, title, description, privacy_status="PRIVATE"):
        self.created.append((title, privacy_status))
        return self.create_result

    def add_playlist_items(self, playlist_id, video_ids, duplicates=False):
        self.added.append((playlist_id, tuple(video_ids)))
        return self.add_response

    def get_playlist(self, playlist_id, limit=1):
        if self.missing_playlist:
            raise RuntimeError("playlist not found")
        return {"id": playlist_id}


def _song(track_id):
    return {
        "id": track_id,
        "title": "Perfect",
        "artists": ["Ed Sheeran"],
        "duration_ms": 263_000,
    }


def _playlist(track_ids=("t1",)):
    return {
        "playlist_id": "sp_pl",
        "playlist_name": "테스트 목록",
        "playlist_description": "",
        "tracks": [_song(tid) for tid in track_ids],
    }


def test_first_sync_creates_playlist_and_adds_track():
    yt = FakeYT()
    st, run = sync_ytmusic.sync_playlist(yt, _playlist())
    assert len(yt.created) == 1
    assert yt.added == [("PLfake", ("vid1",))]
    assert st["yt_playlist_id"] == "PLfake"
    assert "t1" in st["matched"]
    assert len(run["newly_matched"]) == 1


def test_second_run_adds_nothing():
    sync_ytmusic.sync_playlist(FakeYT(), _playlist())
    yt2 = FakeYT()
    st, run = sync_ytmusic.sync_playlist(yt2, _playlist())
    assert yt2.added == []
    assert yt2.searches == []
    assert run["already"] == 1


def test_new_track_only_is_synced():
    sync_ytmusic.sync_playlist(FakeYT(), _playlist())
    yt2 = FakeYT()
    st, run = sync_ytmusic.sync_playlist(yt2, _playlist(("t1", "t2")))
    assert len(yt2.added) == 1
    assert run["already"] == 1
    assert "t2" in st["matched"]


def test_dry_run_writes_no_state_and_no_remote_writes():
    """dry-run이 state를 남기면 다음 실제 실행이 아무것도 하지 않는다."""
    yt = FakeYT()
    st, run = sync_ytmusic.sync_playlist(yt, _playlist(), dry_run=True)
    assert yt.created == []
    assert yt.added == []
    assert len(run["newly_matched"]) == 1
    assert not state_module.state_path("sp_pl").exists()


def test_dry_run_then_real_run_still_creates_playlist():
    sync_ytmusic.sync_playlist(FakeYT(), _playlist(), dry_run=True)
    yt2 = FakeYT()
    sync_ytmusic.sync_playlist(yt2, _playlist())
    assert len(yt2.created) == 1
    assert yt2.added == [("PLfake", ("vid1",))]


def test_search_failure_records_unmatched_and_continues():
    yt = FakeYT(search_error=RuntimeError("boom"))
    st, run = sync_ytmusic.sync_playlist(yt, _playlist(("t1", "t2")))
    assert len(run["newly_unmatched"]) == 2
    assert st["matched"] == {}
    # 두 곡 모두 최대 시도 횟수만큼 시도했다 (두 번째 곡도 처리됐다는 증거)
    assert len(yt.searches) == 2 * sync_ytmusic.MAX_ATTEMPTS


def test_delay_applies_on_failure_path(monkeypatch):
    """실패 시 딜레이를 건너뛰면 레이트리밋 상황에서 연타하게 된다."""
    slept = []
    monkeypatch.setattr(sync_ytmusic.time, "sleep", lambda s: slept.append(s))
    yt = FakeYT(search_error=RuntimeError("boom"))
    sync_ytmusic.sync_playlist(yt, _playlist(), delay=0.3)
    assert 0.3 in slept


def test_add_failure_is_not_recorded_as_matched():
    yt = FakeYT(add_response={"status": "STATUS_FAILED", "message": "quota exceeded"})
    st, run = sync_ytmusic.sync_playlist(yt, _playlist())
    assert st["matched"] == {}
    assert len(run["newly_unmatched"]) == 1
    assert "추가 실패" in run["newly_unmatched"][0]["reason"]


def test_duplicate_is_recorded_as_matched():
    """수동으로 넣어둔 곡을 매번 미매칭으로 보고하지 않는다."""
    yt = FakeYT(
        add_response={"status": "STATUS_FAILED", "message": "Cannot add duplicate items"}
    )
    st, run = sync_ytmusic.sync_playlist(yt, _playlist())
    assert "t1" in st["matched"]
    assert run["newly_unmatched"] == []


def test_create_playlist_error_dict_raises_and_is_not_stored():
    yt = FakeYT(create_result={"error": {"code": 400}})
    with pytest.raises(YTWriteError):
        sync_ytmusic.sync_playlist(yt, _playlist())
    assert state_module.load_state("sp_pl")["yt_playlist_id"] is None


def test_missing_remote_playlist_is_detected():
    """플레이리스트가 삭제됐는데 '변경 없음'을 보고하면 거짓 성공이다."""
    sync_ytmusic.sync_playlist(FakeYT(), _playlist())
    with pytest.raises(sync_ytmusic.YTPlaylistMissing):
        sync_ytmusic.sync_playlist(FakeYT(missing_playlist=True), _playlist())


def test_keyboard_interrupt_saves_progress(monkeypatch):
    original = sync_ytmusic.search_candidates
    calls = {"n": 0}

    def flaky(yt, track):
        calls["n"] += 1
        if calls["n"] > 1:
            raise KeyboardInterrupt
        return original(yt, track)

    monkeypatch.setattr(sync_ytmusic, "search_candidates", flaky)

    st, run = sync_ytmusic.sync_playlist(FakeYT(), _playlist(("t1", "t2")))
    assert run["interrupted"] is True
    assert "t1" in st["matched"]
    assert state_module.load_state("sp_pl")["matched"].get("t1") is not None


def test_truncation_flag_is_carried_into_run():
    """embed 100곡 상한 경고가 리포트까지 전달되어야 한다."""
    data = _playlist()
    data["truncated"] = True
    _st, run = sync_ytmusic.sync_playlist(FakeYT(), data)
    assert run["truncated"] is True
