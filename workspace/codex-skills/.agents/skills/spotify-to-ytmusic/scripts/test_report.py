"""report.py 단위 테스트."""

from datetime import datetime

import pytest

import report
import state


@pytest.fixture(autouse=True)
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setenv("SPOTIFY_TO_YTMUSIC_HOME", str(tmp_path))
    return tmp_path


def _state():
    st = state.new_state("pl1", "My List")
    st["yt_playlist_id"] = "PLabc"
    return st


def _run(**overrides):
    run = {
        "total": 3,
        "already": 1,
        "interrupted": False,
        "truncated": False,
        "newly_matched": [],
        "newly_unmatched": [],
    }
    run.update(overrides)
    return run


def test_report_contains_summary_numbers():
    md = report.build_report(_state(), _run())
    assert "My List" in md
    assert "이미 동기화" in md


def test_report_contains_youtube_playlist_link():
    md = report.build_report(_state(), _run())
    assert "https://music.youtube.com/playlist?list=PLabc" in md


def test_report_lists_unmatched_tracks():
    run = _run(
        newly_unmatched=[
            {
                "title": "Rare Song",
                "artists": ["Some Artist"],
                "best_candidate": "Rare Song (Cover)",
                "score": 0.61,
                "reason": "임계값 미달",
            }
        ]
    )
    md = report.build_report(_state(), run)
    assert "Rare Song" in md
    assert "0.61" in md
    assert "임계값 미달" in md


def test_report_flags_low_confidence_matches():
    run = _run(
        newly_matched=[
            {"title": "Sure Song", "artists": ["A"], "yt_title": "Sure Song",
             "score": 0.97, "video_id": "v1"},
            {"title": "Iffy Song", "artists": ["B"], "yt_title": "Iffy Song (Remix)",
             "score": 0.78, "video_id": "v2"},
        ]
    )
    md = report.build_report(_state(), run)
    assert "확인 권장" in md
    low_section = md.split("확인 권장", 1)[1]
    assert "Iffy Song" in low_section
    assert "Sure Song" not in low_section


def test_report_omits_detail_sections_when_all_clean():
    run = _run(
        newly_matched=[
            {"title": "Sure Song", "artists": ["A"], "yt_title": "Sure Song",
             "score": 0.97, "video_id": "v1"},
        ]
    )
    md = report.build_report(_state(), run)
    assert "## 미매칭 목록" not in md
    assert "확인 권장" not in md
    assert "확인이 필요한 항목이 없습니다" in md


def test_report_notes_interruption():
    md = report.build_report(_state(), _run(interrupted=True))
    assert "중단" in md


def test_report_notes_truncation():
    """100곡 상한에 걸렸으면 리포트에도 남아야 한다."""
    md = report.build_report(_state(), _run(truncated=True))
    assert "100곡" in md


def test_report_escapes_pipes_and_newlines_in_cells():
    """표 셀에 파이프나 개행이 들어가면 마크다운 표가 깨진다."""
    run = _run(
        newly_unmatched=[
            {
                "title": "A | B\nC",
                "artists": ["X | Y"],
                "best_candidate": None,
                "score": 0.0,
                "reason": "후보 없음",
            }
        ]
    )
    md = report.build_report(_state(), run)
    table_line = [ln for ln in md.splitlines() if "후보 없음" in ln][0]
    assert "\\|" in table_line
    assert "\n" not in table_line
    # 5열 표의 경계 파이프 6개 + 이스케이프된 파이프 2개
    assert table_line.count("|") == 8


def test_write_report_uses_second_precision(tmp_home):
    """여러 플레이리스트를 같은 분에 처리하면 분 단위 파일명은 충돌한다."""
    path = report.write_report(
        "My List", "# 내용", now=datetime(2026, 8, 16, 14, 30, 45)
    )
    assert path == tmp_home / "reports" / "My List-20260816-143045.md"
    assert path.read_text(encoding="utf-8") == "# 내용"
