# spotify-to-ytmusic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spotify 플레이리스트를 YouTube Music에 동일하게 복제하고, 재실행 시 새 곡만 증분 동기화하는 Claude Code 스킬을 만든다.

**Architecture:** 순수 로직(정규화·점수 계산·상태·리포트)과 API 호출(spotipy·ytmusicapi)을 파일 단위로 분리한다. 순수 모듈은 pytest로 완전히 검증하고, API 모듈은 얇은 오케스트레이션만 담당해 수동 스모크 테스트로 확인한다.

**Tech Stack:** Python 3.10+, spotipy, ytmusicapi, pytest

## Global Constraints

- 스킬 디렉토리: `/Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/`
- `SKILL.md`의 frontmatter `description`은 **반드시 single-line 큰따옴표 문자열** (README 제약 — 여러 줄이면 Skill 도구가 인식하지 못함)
- 모든 사용자 대면 출력(에러 메시지, 리포트, 진행 로그)은 **한국어**
- 서드파티 import는 `try/except ImportError`로 감싸고, 실패 시 `pip3 install --break-system-packages <pkg>` 안내를 낸다 (기존 `evidence-capture` 컨벤션)
- 단, 순수 로직 모듈(`match.py`, `state.py`, `report.py`)은 **표준 라이브러리만** import한다 — 서드파티 미설치 상태에서도 테스트가 돌아야 한다
- 데이터 홈 디렉토리는 `SPOTIFY_TO_YTMUSIC_HOME` 환경변수로 재정의 가능하고, 기본값은 `~/.claude/spotify-to-ytmusic/`. 테스트는 항상 이 환경변수로 tmp 디렉토리를 가리킨다
- 매칭 임계값 기본값: **0.75**
- 곡당 요청 간격 기본값: **0.3초**
- 재시도: 지수 백오프 1초 → 2초 → 4초, 최대 3회
- 모든 테스트 실행은 `spotify-to-ytmusic/scripts/` 디렉토리를 작업 디렉토리로 삼는다 (모듈을 평범한 top-level import로 쓰기 위함)

## 스펙 대비 변경 사항 (2건)

구현 계획을 짜면서 스펙(`docs/superpowers/specs/2026-08-16-spotify-to-ytmusic-design.md`)에서 두 가지를 조정했다.

1. **`state.py` / `report.py` 분리** — 스펙은 상태 관리와 리포트 작성을 `sync_ytmusic.py`에 뒀지만, 그러면 리포트 마크다운 생성이 API 호출에 묶여 단위 테스트가 불가능해진다. 스펙이 `match.py`를 분리한 것과 같은 이유로 두 모듈을 떼어낸다.
2. **아티스트 게이트 추가** — 스펙의 단순 가중합만 쓰면 커버곡(제목 동일·아티스트 다름·재생시간 유사)이 약 0.73점으로 임계값 0.75에 너무 가깝게 붙는다. `artist_score < 0.5`면 총점을 0.70으로 상한 처리해 "아티스트가 다르면 매칭 아님" 규칙을 명시적으로 만든다.

## File Structure

```
spotify-to-ytmusic/
├── SKILL.md                      # 스킬 정의 · 워크플로우 · 인증 셋업 문서
├── requirements.txt              # spotipy, ytmusicapi
└── scripts/
    ├── match.py                  # 정규화 + 점수 계산 (표준 라이브러리만)
    ├── state.py                  # state 파일 경로/로드/저장 (표준 라이브러리만)
    ├── report.py                 # 리포트 마크다운 생성/저장 (표준 라이브러리만)
    ├── fetch_spotify.py          # Spotify → tracks JSON
    ├── sync_ytmusic.py           # 검색 → 매칭 → 추가 → state/리포트 갱신
    ├── check_auth.py             # 양쪽 인증 점검 + 셋업 안내
    ├── test_match.py             # match.py 단위 테스트
    ├── test_state.py             # state.py 단위 테스트
    ├── test_report.py            # report.py 단위 테스트
    └── test_fetch_spotify.py     # extract_playlist_id 단위 테스트
```

| 파일 | 책임 | 서드파티 의존 |
|---|---|---|
| `match.py` | 제목/아티스트 정규화, 후보 점수 계산, 최적 후보 선정 | 없음 |
| `state.py` | 데이터 홈 경로 결정, state JSON 로드/저장 | 없음 |
| `report.py` | 실행 결과 → 마크다운 리포트 문자열 생성 및 파일 저장 | 없음 |
| `fetch_spotify.py` | 플레이리스트 ID 추출, 이름 검색, 트랙 목록 수집 | spotipy |
| `sync_ytmusic.py` | YT 검색 결과 정규화, 매칭 호출, 플레이리스트 생성/추가, 전체 흐름 조율 | ytmusicapi |
| `check_auth.py` | 인증 상태 점검, 미설정 시 셋업 절차 출력 | spotipy, ytmusicapi |

---

## Task 1: 스킬 골격 + 정규화 함수

**Files:**
- Create: `spotify-to-ytmusic/requirements.txt`
- Create: `spotify-to-ytmusic/scripts/match.py`
- Test: `spotify-to-ytmusic/scripts/test_match.py`

**Interfaces:**
- Consumes: (없음 — 첫 태스크)
- Produces:
  - `normalize_title(title: str) -> str`
  - `normalize_artist(artist: str) -> str`

- [ ] **Step 1: 디렉토리와 requirements.txt 생성**

```bash
mkdir -p /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts
cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic
cat > requirements.txt <<'EOF'
spotipy>=2.24.0
ytmusicapi>=1.7.0
EOF
```

- [ ] **Step 2: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_match.py`:

```python
"""match.py 단위 테스트."""

import pytest

from match import normalize_artist, normalize_title


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Bohemian Rhapsody - Remastered 2011", "bohemian rhapsody"),
        ("Perfect (feat. Beyonce)", "perfect"),
        ("Shape of You [Radio Edit]", "shape of you"),
        ("Hello (Deluxe Edition)", "hello"),
        ("Yesterday (Bonus Track)", "yesterday"),
        ("Don't Stop Me Now", "dont stop me now"),
        ("밤편지", "밤편지"),
        # (Live)는 의도적으로 제거하지 않는다 — 라이브 버전은 다른 곡으로 취급해야 한다
        ("Song (Live)", "song live"),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Ed Sheeran", "ed sheeran"),
        ("AC/DC", "acdc"),
        ("아이유 (IU)", "아이유 iu"),
        ("  Queen  ", "queen"),
    ],
)
def test_normalize_artist(raw, expected):
    assert normalize_artist(raw) == expected
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'match'`

- [ ] **Step 4: 정규화 함수 구현**

`spotify-to-ytmusic/scripts/match.py`:

```python
#!/usr/bin/env python3
"""Spotify 트랙과 YouTube Music 검색 후보 간의 매칭 점수를 계산한다.

이 모듈은 네트워크에 접근하지 않는다. 표준 라이브러리만 사용하므로
서드파티 패키지 없이도 단위 테스트가 가능하다.
"""

import re

# 괄호/대괄호 안의 부가 표기. (Live)는 의도적으로 제외한다 —
# 라이브 버전은 스튜디오 버전과 다른 곡으로 취급해야 하기 때문이다.
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

_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """비교용으로 제목을 정규화한다. 원본은 리포트 출력을 위해 별도 보관한다."""
    if not title:
        return ""
    text = title.lower()
    text = _PAREN_NOISE.sub(" ", text)
    text = _HYPHEN_NOISE.sub(" ", text)
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def normalize_artist(artist: str) -> str:
    """비교용으로 아티스트명을 정규화한다."""
    if not artist:
        return ""
    text = artist.lower()
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: PASS — 12 passed

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/requirements.txt spotify-to-ytmusic/scripts/match.py spotify-to-ytmusic/scripts/test_match.py
git commit -m "feat(spotify-to-ytmusic): 제목/아티스트 정규화 함수 추가"
```

---

## Task 2: 매칭 점수 계산과 최적 후보 선정

**Files:**
- Modify: `spotify-to-ytmusic/scripts/match.py` (Task 1 파일에 추가)
- Test: `spotify-to-ytmusic/scripts/test_match.py` (Task 1 파일에 추가)

**Interfaces:**
- Consumes: `normalize_title(str) -> str`, `normalize_artist(str) -> str` (Task 1)
- Produces:
  - `DEFAULT_THRESHOLD: float` — 값 `0.75`
  - `score_candidate(track: dict, candidate: dict) -> float` — 0.0~1.0
  - `best_match(track: dict, candidates: list[dict], threshold: float = DEFAULT_THRESHOLD) -> MatchResult`
  - `MatchResult` — `NamedTuple(candidate: dict | None, score: float, best_candidate: dict | None)`
    - `candidate`: 임계값을 넘어 채택된 후보. 못 넘으면 `None`
    - `score`: 최고 점수 (후보가 없으면 `0.0`)
    - `best_candidate`: 임계값과 무관한 최고점 후보. 후보가 없으면 `None`
  - track dict 형태: `{"id": str, "title": str, "artists": list[str], "album": str, "duration_ms": int, "isrc": str | None}`
  - candidate dict 형태: `{"video_id": str, "title": str, "artists": list[str], "duration_sec": int | None}`

- [ ] **Step 1: 실패하는 테스트 작성**

`test_match.py` **끝에 이어서 추가**:

```python
from match import DEFAULT_THRESHOLD, MatchResult, best_match, score_candidate


def _track(title, artists, duration_ms=200_000):
    return {
        "id": "t1",
        "title": title,
        "artists": artists,
        "album": "",
        "duration_ms": duration_ms,
        "isrc": None,
    }


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
    assert score >= 0.95


def test_remaster_suffix_still_matches():
    score = score_candidate(
        _track("Bohemian Rhapsody", ["Queen"], 355_000),
        _cand("Bohemian Rhapsody - Remastered 2011", ["Queen"], 358),
    )
    assert score >= DEFAULT_THRESHOLD


def test_feat_notation_difference_still_matches():
    score = score_candidate(
        _track("Perfect (feat. Beyonce)", ["Ed Sheeran", "Beyonce"], 263_000),
        _cand("Perfect", ["Ed Sheeran"], 261),
    )
    assert score >= DEFAULT_THRESHOLD


def test_cover_by_different_artist_is_rejected():
    """제목과 재생시간이 같아도 아티스트가 다르면 매칭이 아니다."""
    score = score_candidate(
        _track("Perfect", ["Ed Sheeran"], 263_000),
        _cand("Perfect", ["Boyce Avenue"], 262),
    )
    assert score < DEFAULT_THRESHOLD


def test_live_version_is_rejected():
    """제목이 유사하고 아티스트가 같아도 재생시간이 크게 다르면 매칭이 아니다."""
    score = score_candidate(
        _track("Creep", ["Radiohead"], 238_000),
        _cand("Creep (Live)", ["Radiohead"], 298),
    )
    assert score < DEFAULT_THRESHOLD


def test_korean_artist_matches():
    score = score_candidate(
        _track("밤편지", ["아이유"], 253_000),
        _cand("밤편지", ["아이유"], 253),
    )
    assert score >= 0.95


def test_short_artist_name_is_not_substring_matched():
    """'IU'가 'Ruin'에 부분 문자열로 걸려 오탐하면 안 된다."""
    score = score_candidate(
        _track("Some Song", ["IU"], 200_000),
        _cand("Some Song", ["Ruin"], 200),
    )
    assert score < DEFAULT_THRESHOLD


def test_missing_duration_uses_neutral_score():
    score = score_candidate(
        _track("Perfect", ["Ed Sheeran"], 263_000),
        _cand("Perfect", ["Ed Sheeran"], None),
    )
    assert score >= DEFAULT_THRESHOLD


def test_best_match_picks_highest_scorer():
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [
        _cand("Perfect", ["Boyce Avenue"], 262, video_id="cover"),
        _cand("Perfect", ["Ed Sheeran"], 263, video_id="real"),
    ]
    result = best_match(track, candidates)
    assert result.candidate is not None
    assert result.candidate["video_id"] == "real"
    assert result.score >= 0.95


def test_best_match_below_threshold_returns_none_but_keeps_best():
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [_cand("Perfect", ["Boyce Avenue"], 262, video_id="cover")]
    result = best_match(track, candidates)
    assert result.candidate is None
    assert result.best_candidate is not None
    assert result.best_candidate["video_id"] == "cover"
    assert 0.0 < result.score < DEFAULT_THRESHOLD


def test_best_match_with_no_candidates():
    result = best_match(_track("Perfect", ["Ed Sheeran"]), [])
    assert result == MatchResult(None, 0.0, None)


def test_threshold_is_configurable():
    track = _track("Perfect", ["Ed Sheeran"], 263_000)
    candidates = [_cand("Perfect", ["Boyce Avenue"], 262)]
    lenient = best_match(track, candidates, threshold=0.1)
    assert lenient.candidate is not None
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: FAIL — `ImportError: cannot import name 'DEFAULT_THRESHOLD' from 'match'`

- [ ] **Step 3: 점수 계산 구현**

`match.py` **끝에 이어서 추가**:

```python
from difflib import SequenceMatcher
from typing import NamedTuple

DEFAULT_THRESHOLD = 0.75

_W_TITLE = 0.5
_W_ARTIST = 0.3
_W_DURATION = 0.2

# 아티스트가 확실히 다르면(게이트 미달) 총점을 이 값으로 상한 처리한다.
# 커버곡은 제목·재생시간이 거의 같아 가중합만으로는 임계값에 위험하게 근접한다.
_ARTIST_GATE = 0.5
_ARTIST_GATE_CAP = 0.70


class MatchResult(NamedTuple):
    """매칭 결과.

    candidate:      임계값을 넘어 채택된 후보. 못 넘으면 None
    score:          최고 점수 (후보가 없으면 0.0)
    best_candidate: 임계값과 무관한 최고점 후보 (후보가 없으면 None)
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


def score_candidate(track: dict, candidate: dict) -> float:
    """트랙과 후보의 매칭 점수를 0.0~1.0으로 계산한다."""
    title = _title_score(track.get("title", ""), candidate.get("title", ""))
    artist = _artist_score(track.get("artists") or [], candidate.get("artists") or [])
    duration = _duration_score(track.get("duration_ms"), candidate.get("duration_sec"))

    total = _W_TITLE * title + _W_ARTIST * artist + _W_DURATION * duration
    if artist < _ARTIST_GATE:
        total = min(total, _ARTIST_GATE_CAP)
    return round(total, 4)


def best_match(
    track: dict,
    candidates: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> MatchResult:
    """후보 중 최고점을 고르고, 임계값 통과 여부를 함께 돌려준다."""
    if not candidates:
        return MatchResult(None, 0.0, None)

    scored = [(score_candidate(track, c), c) for c in candidates]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_score, top_candidate = scored[0]

    if top_score >= threshold:
        return MatchResult(top_candidate, top_score, top_candidate)
    return MatchResult(None, top_score, top_candidate)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: PASS — 24 passed

테스트가 실패하면 임계값이 아니라 점수 계산을 확인한다. `python3 -c` 로 개별 점수를 찍어보고 어느 신호가 예상과 다른지 먼저 파악할 것. 임계값 상수를 테스트에 맞춰 바꾸지 말 것 — 0.75는 스펙이 정한 값이다.

- [ ] **Step 5: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/match.py spotify-to-ytmusic/scripts/test_match.py
git commit -m "feat(spotify-to-ytmusic): 매칭 점수 계산 및 최적 후보 선정 추가"
```

---

## Task 3: state 저장소

**Files:**
- Create: `spotify-to-ytmusic/scripts/state.py`
- Test: `spotify-to-ytmusic/scripts/test_state.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `data_home() -> Path` — `SPOTIFY_TO_YTMUSIC_HOME` 환경변수 또는 `~/.claude/spotify-to-ytmusic`
  - `state_dir() -> Path`, `report_dir() -> Path`, `auth_file() -> Path` (= `<home>/browser.json`)
  - `state_path(playlist_id: str) -> Path`
  - `new_state(playlist_id: str, playlist_name: str) -> dict`
  - `load_state(playlist_id: str, playlist_name: str = "") -> dict` — 없으면 `new_state` 반환
  - `save_state(state: dict) -> Path`
  - state dict 형태:
    ```python
    {
      "spotify_playlist_id": str,
      "spotify_playlist_name": str,
      "yt_playlist_id": str | None,
      "matched": {spotify_track_id: {"video_id": str, "score": float, "yt_title": str}},
      "unmatched": [{"track_id": str, "title": str, "artists": list[str],
                     "best_candidate": str, "score": float, "reason": str}],
      "last_sync": str | None,   # ISO 8601
    }
    ```

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_state.py`:

```python
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
    assert st["spotify_playlist_name"] == "Fresh"
    assert st["matched"] == {}


def test_save_then_load_roundtrip(tmp_home):
    st = state.new_state("pl1", "My List")
    st["yt_playlist_id"] = "PLabc"
    st["matched"]["t1"] = {"video_id": "v1", "score": 0.91, "yt_title": "Song"}
    path = state.save_state(st)

    assert path == tmp_home / "state" / "pl1.json"
    assert path.exists()

    loaded = state.load_state("pl1")
    assert loaded["yt_playlist_id"] == "PLabc"
    assert loaded["matched"]["t1"]["score"] == 0.91


def test_save_state_sets_last_sync():
    st = state.new_state("pl1", "My List")
    state.save_state(st)
    assert st["last_sync"] is not None
    loaded = state.load_state("pl1")
    assert loaded["last_sync"] == st["last_sync"]


def test_save_state_creates_directory(tmp_home):
    assert not (tmp_home / "state").exists()
    state.save_state(state.new_state("pl1", "My List"))
    assert (tmp_home / "state").is_dir()


def test_state_path_sanitizes_playlist_id():
    """경로 구분자가 섞인 id로 디렉토리를 탈출하지 못하게 한다."""
    path = state.state_path("../../etc/passwd")
    assert path.parent == state.state_dir()


def test_saved_file_is_readable_json(tmp_home):
    st = state.new_state("pl1", "한글 리스트")
    state.save_state(st)
    raw = (tmp_home / "state" / "pl1.json").read_text(encoding="utf-8")
    assert "한글 리스트" in raw
    assert json.loads(raw)["spotify_playlist_name"] == "한글 리스트"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state'`

- [ ] **Step 3: state.py 구현**

`spotify-to-ytmusic/scripts/state.py`:

```python
#!/usr/bin/env python3
"""동기화 상태(state) 파일의 경로 결정과 읽기/쓰기를 담당한다.

네트워크에 접근하지 않으며 표준 라이브러리만 사용한다.
데이터 홈은 SPOTIFY_TO_YTMUSIC_HOME 환경변수로 재정의할 수 있다 (테스트용).
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

_DEFAULT_HOME = Path.home() / ".claude" / "spotify-to-ytmusic"
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


def data_home() -> Path:
    """데이터 홈 디렉토리. 환경변수는 호출 시점에 읽는다."""
    override = os.environ.get("SPOTIFY_TO_YTMUSIC_HOME")
    return Path(override) if override else _DEFAULT_HOME


def state_dir() -> Path:
    return data_home() / "state"


def report_dir() -> Path:
    return data_home() / "reports"


def auth_file() -> Path:
    return data_home() / "browser.json"


def _safe_name(value: str) -> str:
    """파일명으로 쓸 수 있게 정리한다. 경로 구분자는 모두 제거된다."""
    cleaned = _UNSAFE.sub("_", value).strip("._")
    return cleaned or "unknown"


def state_path(playlist_id: str) -> Path:
    return state_dir() / f"{_safe_name(playlist_id)}.json"


def new_state(playlist_id: str, playlist_name: str) -> dict:
    return {
        "spotify_playlist_id": playlist_id,
        "spotify_playlist_name": playlist_name,
        "yt_playlist_id": None,
        "matched": {},
        "unmatched": [],
        "last_sync": None,
    }


def load_state(playlist_id: str, playlist_name: str = "") -> dict:
    """state 파일을 읽는다. 없거나 깨졌으면 새 state를 돌려준다."""
    path = state_path(playlist_id)
    if not path.exists():
        return new_state(playlist_id, playlist_name)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_state(playlist_id, playlist_name)

    base = new_state(playlist_id, playlist_name)
    base.update(loaded)
    if playlist_name:
        base["spotify_playlist_name"] = playlist_name
    return base


def save_state(state: dict) -> Path:
    """state를 저장하고 last_sync를 갱신한다. 저장 경로를 돌려준다."""
    state["last_sync"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path = state_path(state["spotify_playlist_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_state.py -v`
Expected: PASS — 8 passed

- [ ] **Step 5: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/state.py spotify-to-ytmusic/scripts/test_state.py
git commit -m "feat(spotify-to-ytmusic): state 저장소 추가"
```

---

## Task 4: 리포트 생성

**Files:**
- Create: `spotify-to-ytmusic/scripts/report.py`
- Test: `spotify-to-ytmusic/scripts/test_report.py`

**Interfaces:**
- Consumes: `state.report_dir()` (Task 3)
- Produces:
  - `LOW_CONFIDENCE_MAX: float` — 값 `0.85`
  - `build_report(state: dict, run: dict) -> str` — 마크다운 문자열
  - `write_report(playlist_name: str, content: str, now: datetime | None = None) -> Path`
  - run dict 형태:
    ```python
    {
      "total": int,            # Spotify 플레이리스트 전체 곡 수
      "already": int,          # 이미 동기화되어 이번에 건너뛴 곡 수
      "newly_matched": [{"title": str, "artists": list[str],
                         "yt_title": str, "score": float, "video_id": str}],
      "newly_unmatched": [{"title": str, "artists": list[str],
                           "best_candidate": str, "score": float, "reason": str}],
    }
    ```

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_report.py`:

```python
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
    run = {"total": 3, "already": 1, "newly_matched": [], "newly_unmatched": []}
    run.update(overrides)
    return run


def test_report_contains_summary_numbers():
    md = report.build_report(_state(), _run())
    assert "My List" in md
    assert "3" in md
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
    assert "Some Artist" in md
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
    assert "Iffy Song" in md
    # 고신뢰도 곡은 확인 권장 표에 등장하지 않는다
    low_section = md.split("확인 권장", 1)[1]
    assert "Sure Song" not in low_section


def test_report_omits_detail_sections_when_all_clean():
    """미매칭도 저신뢰도도 없으면 상세 표 대신 안내 문구만 남는다."""
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


def test_write_report_creates_file(tmp_home):
    path = report.write_report(
        "My List", "# 내용", now=datetime(2026, 8, 16, 14, 30)
    )
    assert path == tmp_home / "reports" / "My List-20260816-1430.md"
    assert path.read_text(encoding="utf-8") == "# 내용"


def test_write_report_sanitizes_playlist_name(tmp_home):
    path = report.write_report(
        "a/b:c", "x", now=datetime(2026, 8, 16, 14, 30)
    )
    assert path == tmp_home / "reports" / "a_b_c-20260816-1430.md"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'report'`

- [ ] **Step 3: report.py 구현**

`spotify-to-ytmusic/scripts/report.py`:

```python
#!/usr/bin/env python3
"""동기화 실행 결과를 마크다운 리포트로 만든다.

네트워크에 접근하지 않으며 표준 라이브러리와 state 모듈만 사용한다.
"""

import re
from datetime import datetime
from pathlib import Path

import state

# 이 점수 미만으로 추가된 곡은 잘못 매칭됐을 수 있어 확인을 권한다.
LOW_CONFIDENCE_MAX = 0.85

_UNSAFE = re.compile(r"[^\w\s.-]", re.UNICODE)


def _artists(names: list[str]) -> str:
    return ", ".join(names) if names else "(미상)"


def _escape(text: str) -> str:
    """마크다운 표의 셀 구분자가 깨지지 않게 파이프를 이스케이프한다."""
    return str(text).replace("|", "\\|")


def build_report(state_data: dict, run: dict) -> str:
    name = state_data.get("spotify_playlist_name") or "(이름 없음)"
    yt_id = state_data.get("yt_playlist_id")
    matched = run.get("newly_matched", [])
    unmatched = run.get("newly_unmatched", [])
    processed = len(matched) + len(unmatched)

    lines = [
        f"# 동기화 리포트 — {name}",
        "",
        f"- 실행 시각: {state_data.get('last_sync') or '(미기록)'}",
    ]
    if yt_id:
        lines.append(
            f"- YouTube Music 플레이리스트: "
            f"https://music.youtube.com/playlist?list={yt_id}"
        )
    lines += [
        "",
        "## 요약",
        "",
        "| 항목 | 곡 수 |",
        "|---|---|",
        f"| Spotify 전체 | {run.get('total', 0)} |",
        f"| 이미 동기화됨 (건너뜀) | {run.get('already', 0)} |",
        f"| 이번에 처리 | {processed} |",
        f"| 매칭 성공 | {len(matched)} |",
        f"| 미매칭 | {len(unmatched)} |",
        "",
    ]

    if unmatched:
        lines += [
            "## 미매칭 목록",
            "",
            "아래 곡은 자동 추가되지 않았다. YouTube Music에서 직접 찾아 추가한다.",
            "",
            "| 원곡 | 아티스트 | 최고 후보 | 점수 | 사유 |",
            "|---|---|---|---|---|",
        ]
        for item in unmatched:
            lines.append(
                f"| {_escape(item.get('title', ''))} "
                f"| {_escape(_artists(item.get('artists', [])))} "
                f"| {_escape(item.get('best_candidate') or '(후보 없음)')} "
                f"| {item.get('score', 0):.2f} "
                f"| {_escape(item.get('reason', ''))} |"
            )
        lines.append("")

    low = [m for m in matched if m.get("score", 0) < LOW_CONFIDENCE_MAX]
    if low:
        lines += [
            f"## 낮은 신뢰도로 추가된 곡 (확인 권장, 점수 < {LOW_CONFIDENCE_MAX})",
            "",
            "| 원곡 | 아티스트 | 추가된 YT 곡 | 점수 |",
            "|---|---|---|---|",
        ]
        for item in low:
            lines.append(
                f"| {_escape(item.get('title', ''))} "
                f"| {_escape(_artists(item.get('artists', [])))} "
                f"| {_escape(item.get('yt_title', ''))} "
                f"| {item.get('score', 0):.2f} |"
            )
        lines.append("")

    if not unmatched and not low:
        lines += ["모든 곡이 높은 신뢰도로 매칭되었습니다. 확인이 필요한 항목이 없습니다.", ""]

    return "\n".join(lines)


def _safe_name(value: str) -> str:
    cleaned = _UNSAFE.sub("_", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "playlist"


def write_report(playlist_name: str, content: str, now: datetime | None = None) -> Path:
    """리포트를 파일로 저장하고 경로를 돌려준다."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M")
    path = state.report_dir() / f"{_safe_name(playlist_name)}-{stamp}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_report.py -v`
Expected: PASS — 7 passed

- [ ] **Step 5: 전체 단위 테스트 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -v`
Expected: PASS — 39 passed

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/report.py spotify-to-ytmusic/scripts/test_report.py
git commit -m "feat(spotify-to-ytmusic): 마크다운 리포트 생성 추가"
```

---

## Task 5: Spotify 트랙 수집

**Files:**
- Create: `spotify-to-ytmusic/scripts/fetch_spotify.py`
- Test: `spotify-to-ytmusic/scripts/test_fetch_spotify.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `extract_playlist_id(value: str) -> str | None` — URL/URI/생 ID에서 ID 추출, 아니면 `None`
  - `PlaylistNotFound(Exception)`, `AmbiguousPlaylist(Exception)`
  - `find_playlist_by_name(sp, name: str) -> dict` — spotipy playlist 객체
  - `fetch_playlist(sp, playlist_id: str) -> dict` — tracks.json 형태
  - `fetch_all_playlists(sp) -> list[dict]`
  - `build_client()` — 인증된 spotipy 클라이언트
  - CLI: `python3 fetch_spotify.py <url|id|name>` → stdout에 JSON 객체
  - CLI: `python3 fetch_spotify.py --all` → stdout에 JSON 배열
  - tracks.json 형태: `{"playlist_id", "playlist_name", "playlist_description", "tracks": [{"id","title","artists","album","duration_ms","isrc"}]}`

**중요:** spotipy import는 모듈 최상단에서 `try/except`로 감싸 실패해도 모듈이 로드되게 한다. `extract_playlist_id` 테스트가 spotipy 미설치 상태에서도 돌아야 하기 때문이다.

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_fetch_spotify.py`:

```python
"""fetch_spotify.py의 순수 함수 단위 테스트."""

import pytest

from fetch_spotify import extract_playlist_id


@pytest.mark.parametrize(
    "value,expected",
    [
        (
            "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "37i9dQZF1DXcBWIGoYBM5M",
        ),
        (
            "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123",
            "37i9dQZF1DXcBWIGoYBM5M",
        ),
        (
            "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
            "37i9dQZF1DXcBWIGoYBM5M",
        ),
        ("37i9dQZF1DXcBWIGoYBM5M", "37i9dQZF1DXcBWIGoYBM5M"),
        ("내 플레이리스트", None),
        ("", None),
        ("https://open.spotify.com/album/37i9dQZF1DXcBWIGoYBM5M", None),
    ],
)
def test_extract_playlist_id(value, expected):
    assert extract_playlist_id(value) == expected
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_fetch_spotify.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_spotify'`

- [ ] **Step 3: fetch_spotify.py 구현**

`spotify-to-ytmusic/scripts/fetch_spotify.py`:

```python
#!/usr/bin/env python3
"""Spotify 플레이리스트의 트랙 목록을 JSON으로 뽑는다.

사용법:
    python3 fetch_spotify.py "https://open.spotify.com/playlist/<id>"
    python3 fetch_spotify.py "내 플레이리스트 이름"
    python3 fetch_spotify.py --all
"""

import argparse
import json
import re
import sys

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    SPOTIPY_AVAILABLE = True
except ImportError:  # 순수 함수 테스트는 spotipy 없이도 돌아야 한다
    SPOTIPY_AVAILABLE = False

SCOPE = "playlist-read-private playlist-read-collaborative"

_URL_RE = re.compile(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)")
_URI_RE = re.compile(r"^spotify:playlist:([A-Za-z0-9]+)$")
_RAW_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")


class PlaylistNotFound(Exception):
    pass


class AmbiguousPlaylist(Exception):
    pass


def extract_playlist_id(value: str) -> str | None:
    """URL/URI/생 ID에서 플레이리스트 ID를 뽑는다. 이름이면 None."""
    if not value:
        return None
    value = value.strip()

    match = _URL_RE.search(value)
    if match:
        return match.group(1)

    match = _URI_RE.match(value)
    if match:
        return match.group(1)

    if "/" not in value and " " not in value and _RAW_ID_RE.match(value):
        return value
    return None


def build_client():
    """인증된 spotipy 클라이언트를 만든다."""
    if not SPOTIPY_AVAILABLE:
        print(
            "Error: spotipy 필요. 설치: pip3 install --break-system-packages spotipy",
            file=sys.stderr,
        )
        sys.exit(1)
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))


def _iter_user_playlists(sp):
    results = sp.current_user_playlists(limit=50)
    while results:
        for item in results["items"]:
            if item:
                yield item
        results = sp.next(results) if results.get("next") else None


def find_playlist_by_name(sp, name: str) -> dict:
    """이름으로 내 플레이리스트를 찾는다.

    정확 일치(대소문자 무시)를 우선하고, 없으면 부분 일치를 찾는다.
    부분 일치가 2개 이상이면 임의로 고르지 않고 예외를 던진다.
    """
    target = name.strip().lower()
    playlists = list(_iter_user_playlists(sp))

    exact = [p for p in playlists if p["name"].strip().lower() == target]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise AmbiguousPlaylist([p["name"] for p in exact])

    partial = [p for p in playlists if target in p["name"].strip().lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        raise AmbiguousPlaylist([p["name"] for p in partial])
    raise PlaylistNotFound(name)


def fetch_playlist(sp, playlist_id: str) -> dict:
    """플레이리스트 메타와 트랙 목록을 수집한다."""
    meta = sp.playlist(playlist_id, fields="id,name,description")
    tracks = []
    skipped = 0

    results = sp.playlist_items(
        playlist_id,
        fields="items(track(id,name,duration_ms,artists(name),"
        "album(name),external_ids(isrc))),next",
        additional_types=["track"],
    )
    while results:
        for item in results["items"]:
            track = item.get("track")
            if not track or not track.get("id"):
                skipped += 1  # 로컬 파일, 삭제된 트랙, 팟캐스트 에피소드 등
                continue
            tracks.append(
                {
                    "id": track["id"],
                    "title": track.get("name", ""),
                    "artists": [a["name"] for a in track.get("artists", [])],
                    "album": (track.get("album") or {}).get("name", ""),
                    "duration_ms": track.get("duration_ms") or 0,
                    "isrc": (track.get("external_ids") or {}).get("isrc"),
                }
            )
        results = sp.next(results) if results.get("next") else None

    if skipped:
        print(f"건너뛴 항목 {skipped}개 (로컬 파일 또는 삭제된 트랙)", file=sys.stderr)

    return {
        "playlist_id": meta["id"],
        "playlist_name": meta.get("name", ""),
        "playlist_description": meta.get("description", "") or "",
        "tracks": tracks,
    }


def fetch_all_playlists(sp) -> list[dict]:
    """내 플레이리스트 전체를 수집한다. 개별 실패는 건너뛴다."""
    collected = []
    for item in _iter_user_playlists(sp):
        try:
            collected.append(fetch_playlist(sp, item["id"]))
            print(f"수집 완료: {item['name']}", file=sys.stderr)
        except Exception as exc:  # 하나가 실패해도 나머지는 계속
            print(f"수집 실패: {item['name']} — {exc}", file=sys.stderr)
    return collected


def main() -> int:
    parser = argparse.ArgumentParser(description="Spotify 플레이리스트 트랙 수집")
    parser.add_argument("playlist", nargs="?", help="플레이리스트 URL, ID, 또는 이름")
    parser.add_argument("--all", action="store_true", help="내 플레이리스트 전체 수집")
    args = parser.parse_args()

    if not args.all and not args.playlist:
        parser.error("플레이리스트를 지정하거나 --all을 사용한다")

    sp = build_client()

    if args.all:
        payload = fetch_all_playlists(sp)
    else:
        playlist_id = extract_playlist_id(args.playlist)
        if playlist_id is None:
            try:
                playlist_id = find_playlist_by_name(sp, args.playlist)["id"]
            except AmbiguousPlaylist as exc:
                print("이름이 여러 플레이리스트와 일치합니다:", file=sys.stderr)
                for candidate in exc.args[0]:
                    print(f"  - {candidate}", file=sys.stderr)
                print("정확한 이름이나 URL로 다시 지정하세요.", file=sys.stderr)
                return 1
            except PlaylistNotFound:
                print(f"플레이리스트를 찾을 수 없습니다: {args.playlist}", file=sys.stderr)
                return 1
        try:
            payload = fetch_playlist(sp, playlist_id)
        except Exception as exc:
            print(f"플레이리스트 접근 실패: {exc}", file=sys.stderr)
            return 1

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_fetch_spotify.py -v`
Expected: PASS — 7 passed

- [ ] **Step 5: CLI가 인자 없이도 죽지 않는지 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 fetch_spotify.py --help`
Expected: argparse 도움말 출력, exit 0 (spotipy 미설치여도 여기까지는 통과해야 한다)

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/fetch_spotify.py spotify-to-ytmusic/scripts/test_fetch_spotify.py
git commit -m "feat(spotify-to-ytmusic): Spotify 트랙 수집 스크립트 추가"
```

---

## Task 6: YouTube Music 동기화

**Files:**
- Create: `spotify-to-ytmusic/scripts/sync_ytmusic.py`
- Test: `spotify-to-ytmusic/scripts/test_sync_ytmusic.py`

**Interfaces:**
- Consumes:
  - `match.best_match(track, candidates, threshold) -> MatchResult`, `match.DEFAULT_THRESHOLD` (Task 2)
  - `state.load_state(playlist_id, playlist_name) -> dict`, `state.save_state(state) -> Path`, `state.auth_file() -> Path` (Task 3)
  - `report.build_report(state_data, run) -> str`, `report.write_report(name, content) -> Path` (Task 4)
  - `fetch_spotify.py`가 출력한 tracks.json 형태
- Produces:
  - `to_candidate(result: dict) -> dict | None` — ytmusicapi 검색 결과 1건 → candidate dict
  - `parse_duration(value) -> int | None` — `"3:52"` 또는 초 정수 → 초
  - `sync_playlist(yt, playlist_data, threshold, delay, privacy, dry_run) -> tuple[dict, dict]` — `(state, run)`
  - CLI: `python3 sync_ytmusic.py --tracks tracks.json [--threshold 0.75] [--delay 0.3] [--public] [--dry-run]`
  - CLI: `--tracks -` 이면 stdin에서 읽는다 (fetch_spotify와 파이프 연결용)

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_sync_ytmusic.py`:

```python
"""sync_ytmusic.py의 순수 함수 단위 테스트."""

import pytest

from sync_ytmusic import parse_duration, to_candidate


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
    cand = to_candidate(result)
    assert cand == {
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
    cand = to_candidate(
        {"videoId": "abc", "title": "T", "artists": [{"name": "A"}]}
    )
    assert cand["duration_sec"] is None


def test_to_candidate_tolerates_string_artists():
    """ytmusicapi가 아티스트를 문자열로 주는 경우도 있다."""
    cand = to_candidate(
        {"videoId": "abc", "title": "T", "artists": ["A", {"name": "B"}]}
    )
    assert cand["artists"] == ["A", "B"]
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sync_ytmusic'`

- [ ] **Step 3: sync_ytmusic.py 구현**

`spotify-to-ytmusic/scripts/sync_ytmusic.py`:

```python
#!/usr/bin/env python3
"""Spotify 트랙 목록을 YouTube Music 플레이리스트로 동기화한다.

사용법:
    python3 fetch_spotify.py "<url>" | python3 sync_ytmusic.py --tracks -
    python3 sync_ytmusic.py --tracks tracks.json --threshold 0.8
"""

import argparse
import json
import sys
import time

import match
import report
import state

try:
    from ytmusicapi import YTMusic

    YTMUSIC_AVAILABLE = True
except ImportError:  # 순수 함수 테스트는 ytmusicapi 없이도 돌아야 한다
    YTMUSIC_AVAILABLE = False

MAX_RETRIES = 3
SEARCH_LIMIT = 5
SAVE_EVERY = 10


def parse_duration(value) -> int | None:
    """'3:52' 또는 '1:03:52' 또는 초 정수를 초로 바꾼다."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    parts = str(value).split(":")
    if not all(p.strip().isdigit() for p in parts):
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + int(part)
    return seconds


def to_candidate(result: dict) -> dict | None:
    """ytmusicapi 검색 결과 1건을 match.py가 쓰는 형태로 바꾼다."""
    video_id = result.get("videoId")
    if not video_id:
        return None

    artists = []
    for artist in result.get("artists") or []:
        if isinstance(artist, dict):
            name = artist.get("name")
        else:
            name = artist
        if name:
            artists.append(name)

    duration = result.get("duration_seconds")
    if duration is None:
        duration = result.get("duration")

    return {
        "video_id": video_id,
        "title": result.get("title", ""),
        "artists": artists,
        "duration_sec": parse_duration(duration),
    }


def _with_retry(func, description: str):
    """지수 백오프로 재시도한다. 끝내 실패하면 마지막 예외를 던진다."""
    delay = 1.0
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                print(
                    f"  재시도 {attempt}/{MAX_RETRIES} ({description}): {exc}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                delay *= 2
    raise last_exc


def search_candidates(yt, track: dict) -> list[dict]:
    """트랙에 대한 YT Music 후보 목록을 얻는다."""
    primary = track["artists"][0] if track.get("artists") else ""
    query = f"{track.get('title', '')} {primary}".strip()
    results = _with_retry(
        lambda: yt.search(query, filter="songs", limit=SEARCH_LIMIT),
        f"검색: {query}",
    )
    candidates = [to_candidate(r) for r in results or []]
    return [c for c in candidates if c]


def sync_playlist(
    yt,
    playlist_data: dict,
    threshold: float = match.DEFAULT_THRESHOLD,
    delay: float = 0.3,
    privacy: str = "PRIVATE",
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """한 플레이리스트를 동기화하고 (state, run) 을 돌려준다."""
    playlist_id = playlist_data["playlist_id"]
    playlist_name = playlist_data.get("playlist_name", "")
    tracks = playlist_data.get("tracks", [])

    st = state.load_state(playlist_id, playlist_name)
    pending = [t for t in tracks if t["id"] not in st["matched"]]

    run = {
        "total": len(tracks),
        "already": len(tracks) - len(pending),
        "newly_matched": [],
        "newly_unmatched": [],
    }

    print(f"[{playlist_name}] 전체 {len(tracks)}곡, 신규 {len(pending)}곡", file=sys.stderr)

    if not pending:
        print("변경 없음 — 이미 모두 동기화되어 있습니다.", file=sys.stderr)
        return st, run

    if not st["yt_playlist_id"] and not dry_run:
        st["yt_playlist_id"] = _with_retry(
            lambda: yt.create_playlist(
                playlist_name or "Spotify Import",
                playlist_data.get("playlist_description", "")
                or "Spotify에서 복제한 플레이리스트",
                privacy_status=privacy,
            ),
            "플레이리스트 생성",
        )
        state.save_state(st)
        print(f"YT 플레이리스트 생성: {st['yt_playlist_id']}", file=sys.stderr)

    for index, track in enumerate(pending, start=1):
        label = f"{track.get('title', '')} — {', '.join(track.get('artists') or [])}"
        try:
            candidates = search_candidates(yt, track)
        except Exception as exc:
            run["newly_unmatched"].append(
                {
                    "track_id": track["id"],
                    "title": track.get("title", ""),
                    "artists": track.get("artists", []),
                    "best_candidate": None,
                    "score": 0.0,
                    "reason": f"검색 실패: {exc}",
                }
            )
            print(f"  [{index}/{len(pending)}] 검색 실패: {label}", file=sys.stderr)
            continue

        result = match.best_match(track, candidates, threshold=threshold)

        if result.candidate is None:
            best = result.best_candidate
            run["newly_unmatched"].append(
                {
                    "track_id": track["id"],
                    "title": track.get("title", ""),
                    "artists": track.get("artists", []),
                    "best_candidate": best["title"] if best else None,
                    "score": result.score,
                    "reason": "임계값 미달" if best else "후보 없음",
                }
            )
            print(
                f"  [{index}/{len(pending)}] 미매칭({result.score:.2f}): {label}",
                file=sys.stderr,
            )
        else:
            video_id = result.candidate["video_id"]
            if not dry_run:
                try:
                    _with_retry(
                        lambda: yt.add_playlist_items(
                            st["yt_playlist_id"], [video_id], duplicates=False
                        ),
                        f"곡 추가: {label}",
                    )
                except Exception as exc:
                    run["newly_unmatched"].append(
                        {
                            "track_id": track["id"],
                            "title": track.get("title", ""),
                            "artists": track.get("artists", []),
                            "best_candidate": result.candidate["title"],
                            "score": result.score,
                            "reason": f"추가 실패: {exc}",
                        }
                    )
                    print(f"  [{index}/{len(pending)}] 추가 실패: {label}", file=sys.stderr)
                    continue

            st["matched"][track["id"]] = {
                "video_id": video_id,
                "score": result.score,
                "yt_title": result.candidate["title"],
            }
            run["newly_matched"].append(
                {
                    "title": track.get("title", ""),
                    "artists": track.get("artists", []),
                    "yt_title": result.candidate["title"],
                    "score": result.score,
                    "video_id": video_id,
                }
            )
            print(
                f"  [{index}/{len(pending)}] 추가({result.score:.2f}): {label}",
                file=sys.stderr,
            )

        if index % SAVE_EVERY == 0:
            # unmatched는 누적하지 않고 이번 실행 결과로 덮어쓴다.
            # 지난번 미매칭 곡은 matched에 없으므로 어차피 이번에 다시 시도된다.
            st["unmatched"] = run["newly_unmatched"]
            state.save_state(st)

        time.sleep(delay)

    st["unmatched"] = run["newly_unmatched"]
    state.save_state(st)
    return st, run


def build_client():
    if not YTMUSIC_AVAILABLE:
        print(
            "Error: ytmusicapi 필요. 설치: pip3 install --break-system-packages ytmusicapi",
            file=sys.stderr,
        )
        sys.exit(1)
    auth = state.auth_file()
    if not auth.exists():
        print(
            f"Error: YT Music 인증 파일이 없습니다: {auth}\n"
            "check_auth.py를 실행해 셋업 절차를 확인하세요.",
            file=sys.stderr,
        )
        sys.exit(1)
    return YTMusic(str(auth))


def load_payload(source: str):
    if source == "-":
        return json.load(sys.stdin)
    with open(source, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="YouTube Music 플레이리스트 동기화")
    parser.add_argument("--tracks", required=True, help="tracks.json 경로 (- 이면 stdin)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=match.DEFAULT_THRESHOLD,
        help=f"매칭 임계값 (기본 {match.DEFAULT_THRESHOLD})",
    )
    parser.add_argument("--delay", type=float, default=0.3, help="곡당 요청 간격(초)")
    parser.add_argument("--public", action="store_true", help="플레이리스트를 공개로 생성")
    parser.add_argument(
        "--dry-run", action="store_true", help="매칭만 하고 YT에 쓰지 않는다"
    )
    args = parser.parse_args()

    payload = load_payload(args.tracks)
    playlists = payload if isinstance(payload, list) else [payload]

    if args.dry_run:
        # dry-run은 검색만 한다. 인증 파일이 있으면 쓰고, 없으면 비인증으로 검색한다.
        if not YTMUSIC_AVAILABLE:
            print(
                "Error: ytmusicapi 필요. 설치: pip3 install --break-system-packages ytmusicapi",
                file=sys.stderr,
            )
            return 1
        auth = state.auth_file()
        yt = YTMusic(str(auth)) if auth.exists() else YTMusic()
    else:
        yt = build_client()

    report_paths = []
    for playlist_data in playlists:
        try:
            st, run = sync_playlist(
                yt,
                playlist_data,
                threshold=args.threshold,
                delay=args.delay,
                privacy="PUBLIC" if args.public else "PRIVATE",
                dry_run=args.dry_run,
            )
        except Exception as exc:
            print(
                f"동기화 실패: {playlist_data.get('playlist_name', '?')} — {exc}",
                file=sys.stderr,
            )
            continue

        content = report.build_report(st, run)
        path = report.write_report(st.get("spotify_playlist_name") or "playlist", content)
        report_paths.append(path)
        print(f"리포트: {path}", file=sys.stderr)

    if len(report_paths) > 1:
        print(f"\n총 {len(report_paths)}개 플레이리스트 처리 완료", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: PASS — 12 passed

- [ ] **Step 5: 전체 테스트 + CLI 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -v && python3 sync_ytmusic.py --help`
Expected: 58 passed, 이어서 argparse 도움말 출력

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/sync_ytmusic.py spotify-to-ytmusic/scripts/test_sync_ytmusic.py
git commit -m "feat(spotify-to-ytmusic): YouTube Music 동기화 스크립트 추가"
```

---

## Task 7: 인증 점검

**Files:**
- Create: `spotify-to-ytmusic/scripts/check_auth.py`

**Interfaces:**
- Consumes: `state.auth_file() -> Path`, `state.data_home() -> Path` (Task 3)
- Produces:
  - CLI: `python3 check_auth.py` — 양쪽 모두 정상이면 exit 0, 하나라도 미설정이면 셋업 절차 출력 후 exit 1

- [ ] **Step 1: check_auth.py 구현**

`spotify-to-ytmusic/scripts/check_auth.py`:

```python
#!/usr/bin/env python3
"""Spotify / YouTube Music 인증 상태를 점검하고 미설정 시 셋업 절차를 안내한다."""

import os
import sys

import state

SPOTIFY_SETUP = """\
[Spotify 셋업]
  1. https://developer.spotify.com/dashboard 에서 앱을 생성한다
  2. 앱 설정에서 Redirect URI에 http://127.0.0.1:8888/callback 을 등록한다
  3. 셸 설정 파일(~/.zshrc)에 아래를 추가하고 새 셸을 연다:

     export SPOTIPY_CLIENT_ID="<Client ID>"
     export SPOTIPY_CLIENT_SECRET="<Client Secret>"
     export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"

  4. 최초 실행 시 브라우저 인증 창이 열린다. 승인하면 토큰이 캐시된다\
"""

YTMUSIC_SETUP = """\
[YouTube Music 셋업]
  1. 브라우저에서 https://music.youtube.com 에 로그인한다
  2. 개발자 도구(F12) → Network 탭을 연다
  3. 페이지를 새로고침하고, /youtubei/v1/ 로 시작하는 POST 요청을 하나 고른다
  4. 그 요청의 Request Headers 전체를 복사한다
  5. 아래 명령을 실행하고, 프롬프트에 복사한 헤더를 붙여넣은 뒤 Ctrl-D 를 누른다:

     ytmusicapi browser --file {auth_path}

  주의: 세션이 만료되면 같은 절차를 다시 수행해야 한다\
"""


def check_spotify() -> tuple[bool, str]:
    missing = [
        name
        for name in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI")
        if not os.environ.get(name)
    ]
    if missing:
        return False, f"환경변수 미설정: {', '.join(missing)}"

    try:
        import spotipy  # noqa: F401
    except ImportError:
        return False, "spotipy 미설치 — pip3 install --break-system-packages spotipy"
    return True, "환경변수와 패키지 모두 확인됨"


def check_ytmusic() -> tuple[bool, str]:
    try:
        from ytmusicapi import YTMusic
    except ImportError:
        return False, "ytmusicapi 미설치 — pip3 install --break-system-packages ytmusicapi"

    auth = state.auth_file()
    if not auth.exists():
        return False, f"인증 파일 없음: {auth}"

    try:
        client = YTMusic(str(auth))
        client.get_library_playlists(limit=1)
    except Exception as exc:
        return False, f"인증 실패(세션 만료 가능): {exc}"
    return True, "인증 파일 유효"


def main() -> int:
    state.data_home().mkdir(parents=True, exist_ok=True)

    spotify_ok, spotify_msg = check_spotify()
    ytmusic_ok, ytmusic_msg = check_ytmusic()

    print(f"Spotify      : {'OK' if spotify_ok else 'NG'} — {spotify_msg}")
    print(f"YouTube Music: {'OK' if ytmusic_ok else 'NG'} — {ytmusic_msg}")

    if spotify_ok and ytmusic_ok:
        print("\n인증 설정이 모두 완료되었습니다.")
        return 0

    print()
    if not spotify_ok:
        print(SPOTIFY_SETUP)
        print()
    if not ytmusic_ok:
        print(YTMUSIC_SETUP.format(auth_path=state.auth_file()))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 미설정 상태에서 안내가 나오는지 확인**

Run:
```bash
cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts
SPOTIFY_TO_YTMUSIC_HOME=/tmp/s2y-check-test env -u SPOTIPY_CLIENT_ID python3 check_auth.py; echo "exit=$?"
```
Expected: `Spotify      : NG — 환경변수 미설정: SPOTIPY_CLIENT_ID...` 와 셋업 절차가 출력되고 `exit=1`

- [ ] **Step 3: 테스트 산출물 정리**

```bash
rm -rf /tmp/s2y-check-test
```

- [ ] **Step 4: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/check_auth.py
git commit -m "feat(spotify-to-ytmusic): 인증 점검 스크립트 추가"
```

---

## Task 8: SKILL.md 작성 및 README 등록

**Files:**
- Create: `spotify-to-ytmusic/SKILL.md`
- Modify: `README.md` (스킬 목록 표, 디렉토리 구조)

**Interfaces:**
- Consumes: Task 1~7의 모든 스크립트 CLI
- Produces: Skill 도구가 인식하는 스킬 정의

- [ ] **Step 1: SKILL.md 작성**

`spotify-to-ytmusic/SKILL.md` — frontmatter의 `description`은 반드시 한 줄이어야 한다:

```markdown
---
name: spotify-to-ytmusic
description: "Spotify 플레이리스트를 YouTube Music에 동일한 구성으로 복제하는 스킬. spotipy로 Spotify 트랙 목록을 읽고 ytmusicapi로 검색·매칭해 YT Music 플레이리스트를 생성하며, 재실행 시 새로 추가된 곡만 증분 동기화한다. 사용자가 '스포티파이 플레이리스트 유튜브 뮤직으로', '플레이리스트 옮겨줘', '플레이리스트 복제', '플레이리스트 이전', 'spotify to ytmusic', '스포티파이에서 유튜브뮤직으로', '플레이리스트 동기화', '음악 목록 옮기기' 등을 언급하면 이 스킬을 사용한다."
---

# Spotify → YouTube Music 플레이리스트 복제

Spotify 플레이리스트를 YouTube Music에 같은 구성으로 만든다. 다시 실행하면 새로 추가된 곡만 붙인다.

## 동작 방식

```
fetch_spotify.py  →  tracks.json  →  sync_ytmusic.py  →  YT 플레이리스트 + 리포트
                                          ↕
                                     match.py (점수 계산)
                                     state/<playlist_id>.json
```

곡마다 YT Music에서 상위 5개 후보를 검색해 점수를 매기고, 임계값(기본 0.75)을 넘는 후보만 추가한다. 못 넘은 곡은 건너뛰고 리포트에 남긴다.

| 신호 | 가중치 |
|---|---|
| 제목 유사도 (부가 표기 제거 후 비교) | 0.5 |
| 아티스트 일치 | 0.3 |
| 재생시간 근접도 | 0.2 |

아티스트 점수가 0.5 미만이면 총점을 0.70으로 상한 처리한다. 커버곡을 원곡으로 오인하지 않기 위해서다.

## 사전 준비 (최초 1회)

### 패키지 설치

```bash
pip3 install --break-system-packages spotipy ytmusicapi
```

### 인증 상태 확인

```bash
python3 scripts/check_auth.py
```

미설정 항목이 있으면 셋업 절차가 그대로 출력된다. 아래는 그 요약이다.

**Spotify** — https://developer.spotify.com/dashboard 에서 앱 생성 → Redirect URI에 `http://127.0.0.1:8888/callback` 등록 → 환경변수 3개(`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`) 설정 → 최초 실행 시 브라우저 인증.

**YouTube Music** — music.youtube.com에 로그인한 브라우저의 개발자 도구에서 `/youtubei/v1/` POST 요청의 Request Headers를 복사 → `ytmusicapi browser --file ~/.claude/spotify-to-ytmusic/browser.json` 실행 후 붙여넣기. 세션이 만료되면 다시 수행한다.

## 워크플로우

### 1단계: 인증 확인

`python3 scripts/check_auth.py`를 먼저 실행한다. exit code가 0이 아니면 **동기화를 시작하지 말고** 출력된 셋업 절차를 사용자에게 전달한다.

### 2단계: 대상 확인

사용자가 준 것이 URL인지, 플레이리스트 이름인지, 전체 일괄인지 파악한다. 이름이 여러 플레이리스트와 일치하면 스크립트가 후보를 출력하고 멈추므로, 사용자에게 어느 것인지 되묻는다.

### 3단계: 실행

플레이리스트 하나:
```bash
cd <스킬 디렉토리>/scripts
python3 fetch_spotify.py "https://open.spotify.com/playlist/<id>" > /tmp/tracks.json
python3 sync_ytmusic.py --tracks /tmp/tracks.json
```

전체 일괄:
```bash
python3 fetch_spotify.py --all > /tmp/all.json
python3 sync_ytmusic.py --tracks /tmp/all.json
```

파이프로 한 번에:
```bash
python3 fetch_spotify.py "<url>" | python3 sync_ytmusic.py --tracks -
```

곡 수가 많으면 시간이 걸린다(곡당 0.3초 + 검색 지연). 100곡이면 1~2분 정도로 안내한다.

### 4단계: 결과 보고

리포트 경로가 stderr에 출력된다. 리포트를 읽고 사용자에게 **한국어로 요약**한다:

- 전체 / 신규 처리 / 매칭 성공 / 미매칭 곡 수
- 미매칭 곡 목록 (제목 · 아티스트 · 최고 후보 · 점수)
- 낮은 신뢰도(0.85 미만)로 추가된 곡이 있으면 확인 권장으로 함께 안내
- YT Music 플레이리스트 링크

미매칭이 많으면(전체의 20% 초과) `--threshold 0.65`로 재실행해 볼 것을 제안한다. 이미 매칭된 곡은 다시 검색하지 않으므로 재실행 비용이 낮다.

## 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--threshold` | 0.75 | 매칭 임계값. 낮추면 더 많이 추가되지만 오매칭이 는다 |
| `--delay` | 0.3 | 곡당 요청 간격(초). ytmusicapi는 비공식 API라 너무 빠르면 차단될 수 있다 |
| `--public` | 꺼짐 | 새 플레이리스트를 공개로 생성 (기본은 비공개) |
| `--dry-run` | 꺼짐 | 매칭 결과만 보고 YT에는 쓰지 않는다 |

## 파일 위치

| 용도 | 경로 |
|---|---|
| YT 인증 | `~/.claude/spotify-to-ytmusic/browser.json` |
| 동기화 상태 | `~/.claude/spotify-to-ytmusic/state/<playlist_id>.json` |
| 리포트 | `~/.claude/spotify-to-ytmusic/reports/<이름>-<날짜>.md` |

`SPOTIFY_TO_YTMUSIC_HOME` 환경변수로 위치를 바꿀 수 있다.

## 주의사항

- **Spotify에서 곡을 지워도 YT에서는 지워지지 않는다.** 추가만 하는 단방향 동기화다
- state 파일을 지우면 다음 실행에서 새 YT 플레이리스트를 만든다. 기존 것과 이어 붙이려면 state의 `yt_playlist_id`를 유지해야 한다
- 중간에 중단되어도 진행 상황은 저장된다. 다시 실행하면 이어서 진행한다

## 테스트

순수 로직은 단위 테스트가 있다:

```bash
cd <스킬 디렉토리>/scripts && python3 -m pytest -v
```

매칭 로직을 손봤다면 반드시 이 테스트를 돌린다.
```

- [ ] **Step 2: SKILL.md frontmatter가 한 줄인지 확인**

Run:
```bash
cd /Users/picpal/Desktop/workspace/claude-skills
python3 -c "
import re, sys
text = open('spotify-to-ytmusic/SKILL.md', encoding='utf-8').read()
block = text.split('---')[1]
lines = [l for l in block.strip().splitlines()]
desc = [l for l in lines if l.startswith('description:')]
assert len(desc) == 1, 'description 줄이 정확히 1개여야 한다'
assert desc[0].rstrip().endswith('\"'), 'description은 한 줄 큰따옴표 문자열이어야 한다'
print('OK: frontmatter 형식 정상')
"
```
Expected: `OK: frontmatter 형식 정상`

- [ ] **Step 3: README 스킬 목록 표에 행 추가**

`README.md`의 스킬 목록 표에서 `gen-report-monodeck-ppt` 행 **다음에** 아래 행을 추가한다:

```markdown
| [spotify-to-ytmusic](./spotify-to-ytmusic) | Spotify 플레이리스트를 YouTube Music에 동일 구성으로 복제. 재실행 시 새 곡만 증분 동기화하고 미매칭 곡은 리포트로 남김 | "스포티파이 플레이리스트 유튜브뮤직으로", "플레이리스트 옮겨줘", "플레이리스트 복제" |
```

- [ ] **Step 4: README 디렉토리 구조에 항목 추가**

`README.md`의 디렉토리 구조 코드블록에서 마지막 스킬 항목 다음에 추가한다:

```
├── spotify-to-ytmusic/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
```

- [ ] **Step 5: 전체 테스트 재확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -v`
Expected: PASS — 58 passed

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/SKILL.md README.md
git commit -m "docs(spotify-to-ytmusic): SKILL.md 작성 및 README 등록"
```

- [ ] **Step 7: 심볼릭 링크 안내**

구현자는 아래 명령을 **사용자에게 안내만 하고 직접 실행하지 않는다** (사용자 홈 디렉토리 변경이므로):

```bash
ln -s /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic ~/.claude/skills/spotify-to-ytmusic
```

---

## 수동 스모크 테스트 (인증 셋업 후, 사용자와 함께)

자동화하지 않는다. 실제 API가 필요하다.

- [ ] 5~10곡짜리 테스트 플레이리스트로 `--dry-run` 실행 → 매칭 점수가 합리적인지 확인
- [ ] `--dry-run` 없이 실행 → YT Music에 비공개 플레이리스트가 생성되고 곡이 들어갔는지 확인
- [ ] 같은 명령 재실행 → `변경 없음 — 이미 모두 동기화되어 있습니다.` 출력 확인
- [ ] Spotify 플레이리스트에 1곡 추가 후 재실행 → 그 1곡만 추가되는지 확인
- [ ] 리포트 파일을 열어 요약 표와 미매칭 목록이 제대로 렌더링되는지 확인
