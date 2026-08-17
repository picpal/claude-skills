#!/usr/bin/env python3
"""Spotify 트랙과 YouTube Music 검색 후보 간의 매칭 점수를 계산한다.

이 모듈은 네트워크에 접근하지 않는다. 표준 라이브러리만 사용하므로
서드파티 패키지 없이도 단위 테스트가 가능하다.
"""

import re
from difflib import SequenceMatcher
from typing import NamedTuple

# 아포스트로피는 삭제한다. 공백으로 바꾸면 "don't" -> "don t"가 되어
# "Dont"로 표기한 후보와 매칭되지 않는다.
_APOSTROPHE = re.compile(r"['’`]")

# 괄호/대괄호 안의 부가 표기. live/remix/cover는 의도적으로 제외한다 —
# 다른 버전은 다른 곡으로 취급해야 하며, 버전 페널티가 따로 처리한다.
_PAREN_NOISE = re.compile(
    r"[\(\[]\s*"
    r"(feat\.?|ft\.?|with|remastered|remaster|deluxe|explicit|"
    r"bonus track|single version|radio edit)"
    r"[^)\]]*[\)\]]",
    re.IGNORECASE,
)

# " - Remastered 2011" 같은 하이픈 접미사
_HYPHEN_NOISE = re.compile(
    r"\s+-\s+.*\b"
    r"(remastered|remaster|deluxe|explicit|bonus track|"
    r"single version|radio edit|mono|stereo)"
    r"\b.*$",
    re.IGNORECASE,
)

# 나머지 문장부호는 구분자로 보고 공백으로 치환한다. "AC/DC" -> "ac dc".
_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")

DEFAULT_THRESHOLD = 0.75

# 아티스트 점수가 이 값 미만이면 임계값과 무관하게 채택하지 않는다.
# 총점 상한(cap)으로 처리하면 --threshold를 낮췄을 때 게이트가 무력화된다.
ARTIST_GATE = 0.5

# 후보에만 있는 버전 표기에 대한 감점. 재생시간이 우연히 비슷한
# 라이브 버전은 재생시간 신호만으로 막을 수 없다.
VERSION_PENALTY = 0.25

_W_TITLE = 0.5
_W_ARTIST = 0.3
_W_DURATION = 0.2

_VERSION_MARKERS = (
    "live",
    "remix",
    "cover",
    "karaoke",
    "instrumental",
    "acoustic",
    "nightcore",
    "sped",
    "slowed",
    "remake",
)


def normalize_title(title: str) -> str:
    """비교용으로 제목을 정규화한다. 원본은 리포트 출력을 위해 별도 보관한다."""
    if not title:
        return ""
    text = title.lower()
    text = _APOSTROPHE.sub("", text)
    text = _PAREN_NOISE.sub(" ", text)
    text = _HYPHEN_NOISE.sub(" ", text)
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def normalize_artist(artist: str) -> str:
    """비교용으로 아티스트명을 정규화한다."""
    if not artist:
        return ""
    text = artist.lower()
    text = _APOSTROPHE.sub("", text)
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


class Score(NamedTuple):
    """점수 내역. 게이트 판정을 위해 아티스트 점수를 따로 노출한다."""

    total: float
    title: float
    artist: float
    duration: float
    penalty: float


class MatchResult(NamedTuple):
    """매칭 결과.

    candidate:      게이트와 임계값을 모두 통과한 후보. 없으면 None
    score:          채택된 후보의 점수 (채택이 없으면 최고 총점)
    best_candidate: 게이트·임계값과 무관한 최고 총점 후보 (후보가 없으면 None)
    """

    candidate: dict | None
    score: float
    best_candidate: dict | None


def _title_score(track_title: str, cand_title: str) -> float:
    a = normalize_title(track_title)
    b = normalize_title(cand_title)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _artist_score(track_artists: list[str], cand_artists: list[str]) -> float:
    """주 아티스트가 후보 아티스트 중 하나와 일치하는지 본다.

    부분 문자열 대신 토큰 부분집합으로 비교한다. 'IU'가 'Ruin'에
    부분 문자열로 걸리는 오탐을 막기 위해서다.
    """
    primary = normalize_artist(track_artists[0]) if track_artists else ""
    if not primary:
        return 0.5
    cand_norm = [normalize_artist(a) for a in cand_artists if a]
    cand_norm = [a for a in cand_norm if a]
    if not cand_norm:
        return 0.0

    primary_tokens = set(primary.split())
    for cand in cand_norm:
        if primary == cand:
            return 1.0
        if primary_tokens and primary_tokens <= set(cand.split()):
            return 1.0
    return max(SequenceMatcher(None, primary, c).ratio() for c in cand_norm)


def _duration_score(duration_ms: int | None, duration_sec: int | None) -> float:
    """재생시간 근접도. 후보에 정보가 없으면 중립값 0.5를 준다."""
    if not duration_ms or duration_sec is None:
        return 0.5
    diff = abs(duration_ms / 1000.0 - duration_sec)
    if diff <= 3:
        return 1.0
    if diff <= 10:
        return 0.5
    return 0.0


def _version_penalty(track_title: str, cand_title: str) -> float:
    """후보에만 있는 버전 표기를 감점한다. 양쪽 모두에 있으면 감점하지 않는다."""
    track_tokens = set(normalize_title(track_title).split())
    cand_tokens = set(normalize_title(cand_title).split())
    for marker in _VERSION_MARKERS:
        if marker in cand_tokens and marker not in track_tokens:
            return VERSION_PENALTY
    return 0.0


def score_candidate(track: dict, candidate: dict) -> Score:
    """트랙과 후보의 매칭 점수를 계산한다."""
    title = _title_score(track.get("title", ""), candidate.get("title", ""))
    artist = _artist_score(track.get("artists") or [], candidate.get("artists") or [])
    duration = _duration_score(track.get("duration_ms"), candidate.get("duration_sec"))
    penalty = _version_penalty(track.get("title", ""), candidate.get("title", ""))

    total = _W_TITLE * title + _W_ARTIST * artist + _W_DURATION * duration - penalty
    total = max(0.0, total)
    return Score(
        round(total, 4),
        round(title, 4),
        round(artist, 4),
        round(duration, 4),
        penalty,
    )


def best_match(
    track: dict,
    candidates: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> MatchResult:
    """게이트와 임계값을 모두 통과하는 최고점 후보를 고른다."""
    if not candidates:
        return MatchResult(None, 0.0, None)

    scored = [(score_candidate(track, c), c) for c in candidates]
    scored.sort(key=lambda pair: pair[0].total, reverse=True)
    top_score, top_candidate = scored[0]

    for score, candidate in scored:
        if score.artist >= ARTIST_GATE and score.total >= threshold:
            return MatchResult(candidate, score.total, top_candidate)

    return MatchResult(None, top_score.total, top_candidate)
