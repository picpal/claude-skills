"""match.py 단위 테스트."""

import pytest

from match import (
    ARTIST_GATE,
    DEFAULT_THRESHOLD,
    MatchResult,
    best_match,
    normalize_artist,
    normalize_title,
    score_candidate,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Bohemian Rhapsody - Remastered 2011", "bohemian rhapsody"),
        ("Perfect (feat. Beyonce)", "perfect"),
        ("Shape of You [Radio Edit]", "shape of you"),
        ("Hello (Deluxe Edition)", "hello"),
        ("Yesterday (Bonus Track)", "yesterday"),
        # 아포스트로피는 삭제한다. 공백으로 치환하면 "don t"가 되어
        # "Dont"로 표기한 후보와 매칭되지 않는다.
        ("Don't Stop Me Now", "dont stop me now"),
        ("밤편지", "밤편지"),
        # (Live)는 의도적으로 제거하지 않는다 — 버전 페널티가 처리한다.
        ("Song (Live)", "song live"),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Ed Sheeran", "ed sheeran"),
        # 슬래시는 구분자이므로 공백으로 치환한다 (삭제가 아니다).
        ("AC/DC", "ac dc"),
        ("Guns N' Roses", "guns n roses"),
        ("아이유 (IU)", "아이유 iu"),
        ("  Queen  ", "queen"),
    ],
)
def test_normalize_artist(raw, expected):
    assert normalize_artist(raw) == expected


def _track(title, artists, duration_ms=200_000):
    return {"id": "t1", "title": title, "artists": artists, "duration_ms": duration_ms}


def _cand(title, artists, duration_sec=200, video_id="v1"):
    return {
        "video_id": video_id,
        "title": title,
        "artists": artists,
        "duration_sec": duration_sec,
    }


def test_exact_match_scores_high():
    score = score_candidate(
        _track("Perfect", ["Ed Sheeran"], 263_000),
        _cand("Perfect", ["Ed Sheeran"], 263),
    )
    assert score.total >= 0.95


def test_remaster_suffix_still_matches():
    score = score_candidate(
        _track("Bohemian Rhapsody", ["Queen"], 355_000),
        _cand("Bohemian Rhapsody - Remastered 2011", ["Queen"], 358),
    )
    assert score.total >= DEFAULT_THRESHOLD


def test_feat_notation_difference_still_matches():
    score = score_candidate(
        _track("Perfect (feat. Beyonce)", ["Ed Sheeran", "Beyonce"], 263_000),
        _cand("Perfect", ["Ed Sheeran"], 261),
    )
    assert score.total >= DEFAULT_THRESHOLD


def test_korean_artist_matches():
    score = score_candidate(
        _track("밤편지", ["아이유"], 253_000),
        _cand("밤편지", ["아이유"], 253),
    )
    assert score.total >= 0.95


def test_missing_duration_uses_neutral_score():
    score = score_candidate(
        _track("Perfect", ["Ed Sheeran"], 263_000),
        _cand("Perfect", ["Ed Sheeran"], None),
    )
    assert score.total >= DEFAULT_THRESHOLD


def test_cover_fails_artist_gate():
    """제목과 재생시간이 같아도 아티스트가 다르면 아티스트 점수가 게이트 미달이다."""
    score = score_candidate(
        _track("Perfect", ["Ed Sheeran"], 263_000),
        _cand("Perfect", ["Boyce Avenue"], 262),
    )
    assert score.artist < ARTIST_GATE


def test_cover_rejected_even_with_low_threshold():
    """게이트는 임계값과 독립이다. --threshold를 낮춰도 커버곡은 통과하지 못한다."""
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [_cand("Perfect", ["Boyce Avenue"], 262, video_id="cover")]
    result = best_match(track, candidates, threshold=0.1)
    assert result.candidate is None
    assert result.best_candidate["video_id"] == "cover"


def test_short_artist_name_is_not_substring_matched():
    """'IU'가 'Ruin'에 부분 문자열로 걸려 오탐하면 안 된다."""
    score = score_candidate(
        _track("Some Song", ["IU"], 200_000),
        _cand("Some Song", ["Ruin"], 200),
    )
    assert score.artist < ARTIST_GATE


def test_live_version_with_duration_gap_is_rejected():
    result = best_match(
        _track("Creep", ["Radiohead"], 238_000),
        [_cand("Creep (Live)", ["Radiohead"], 298)],
    )
    assert result.candidate is None


def test_live_version_with_same_duration_is_rejected_by_penalty():
    """재생시간이 같으면 재생시간 신호로는 막을 수 없다. 버전 페널티가 막아야 한다."""
    result = best_match(
        _track("Creep", ["Radiohead"], 238_000),
        [_cand("Creep (Live)", ["Radiohead"], 238)],
    )
    assert result.candidate is None


def test_live_original_matches_live_candidate():
    """원곡이 라이브면 라이브 후보와 매칭되는 것이 맞다. 페널티가 걸리면 안 된다."""
    score = score_candidate(
        _track("Creep - Live", ["Radiohead"], 298_000),
        _cand("Creep (Live)", ["Radiohead"], 298),
    )
    assert score.penalty == 0.0
    assert score.total >= DEFAULT_THRESHOLD


def test_best_match_picks_highest_eligible():
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [
        _cand("Perfect", ["Boyce Avenue"], 262, video_id="cover"),
        _cand("Perfect", ["Ed Sheeran"], 263, video_id="real"),
    ]
    result = best_match(track, candidates)
    assert result.candidate["video_id"] == "real"
    assert result.score >= 0.95


def test_best_match_with_no_candidates():
    assert best_match(_track("Perfect", ["Ed Sheeran"]), []) == MatchResult(None, 0.0, None)


def test_threshold_is_configurable_for_genuine_matches():
    """아티스트가 맞는데 점수가 낮은 후보는 임계값을 낮추면 통과해야 한다."""
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [_cand("Perfect Storm", ["Ed Sheeran"], 200, video_id="loose")]
    assert best_match(track, candidates).candidate is None
    assert best_match(track, candidates, threshold=0.6).candidate["video_id"] == "loose"
