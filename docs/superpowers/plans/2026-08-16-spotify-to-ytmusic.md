# spotify-to-ytmusic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 내가 소유한 Spotify 플레이리스트를 YouTube Music에 같은 구성으로 복제하고, 재실행 시 새로 추가된 곡만 증분 동기화하는 Claude Code 스킬을 만든다.

**Architecture:** 순수 로직(정규화·점수·상태·리포트·응답 검증)과 API 호출을 파일 단위로 분리한다. 순수 모듈은 pytest로 검증하고, 상태가 가장 복잡한 `sync_playlist`는 ytmusicapi를 흉내내는 fake 클라이언트로 흐름 전체를 검증한다.

**Tech Stack:** Python 3.10+, spotipy>=2.26.0, ytmusicapi, pytest

> **상태: 실행 완료 (2026-08-16).** 단, **Task 5(Spotify 수집)는 계획대로 구현하지 않았다.**
> 사용자에게 Spotify Premium이 없어 Web API 경로가 성립하지 않으므로, embed 페이지
> (`/embed/playlist/<id>`)의 `__NEXT_DATA__`를 파싱하는 방식으로 대체했다. spotipy 의존이
>사라졌고 인증·Premium·소유권이 모두 불필요해졌다. 대신 embed는 100곡 상한이 있다.
> 나머지 Task(1~4, 6~9)는 계획대로 구현되었다. 최종 설계는 스펙 문서를 보라:
> `docs/superpowers/specs/2026-08-16-spotify-to-ytmusic-design.md`
> 실제 테스트 수는 96개다 (계획의 88개 + embed 파서·잘림 경고 테스트 추가분).

**개정 이력:** 2026-08-16 Codex 교차 검토로 P1 11건 발견. Spotify 2026-02 마이그레이션(`track`→`item`, 소유 플레이리스트 한정, Premium 필수) 반영 및 전 태스크 개정.

## Global Constraints

- 스킬 디렉토리: `/Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/`
- `SKILL.md`의 frontmatter `description`은 **반드시 single-line 큰따옴표 문자열** (README 제약 — 여러 줄이면 Skill 도구가 인식하지 못함)
- 모든 사용자 대면 출력(에러 메시지, 리포트, 진행 로그)은 **한국어**
- 서드파티 import는 모듈 최상단에서 `try/except ImportError`로 감싸 **플래그만 세우고 모듈 로드는 성공시킨다.** 실제 사용 시점에 `pip3 install --break-system-packages <pkg>` 안내를 내고 종료한다. 순수 함수 테스트가 서드파티 미설치 상태에서도 돌아야 하기 때문이다
- 순수 로직 모듈(`match.py`, `state.py`, `report.py`)은 **표준 라이브러리만** import한다
- 데이터 홈은 `SPOTIFY_TO_YTMUSIC_HOME` 환경변수로 재정의 가능, 기본값 `~/.claude/spotify-to-ytmusic/`. 테스트는 항상 이 환경변수로 tmp 디렉토리를 가리킨다
- 매칭 임계값 기본값 **0.75**, 아티스트 게이트 **0.5**, 버전 페널티 **0.25**
- 곡당 요청 간격 기본값 **0.3초**, 재시도 **최대 3회 시도(= 2회 재시도), 대기 1초 → 2초**
- 모든 테스트는 `spotify-to-ytmusic/scripts/`를 작업 디렉토리로 삼아 실행한다 (모듈을 top-level import로 쓰기 위함)
- **파라미터화 테스트는 케이스 하나가 테스트 하나로 집계된다.** 각 태스크의 기대 개수는 이 기준이다. 실제 개수가 다르면 멈추고 원인을 확인한다

## Codex 교차 검토에서 반영한 것

구현 전 Codex CLI로 계획을 검토해 아래를 고쳤다. 각 항목은 해당 태스크에 반영되어 있다.

| 발견 | 반영 |
|---|---|
| Spotify 2026-02 마이그레이션: `track`→`item`, `/tracks`→`/items`, 소유/협업 플레이리스트만, Premium 필수 | Task 5 전면 수정, spotipy 하한 2.26.0, SKILL.md 전제조건 |
| 정규화 테스트 2건이 실제로 실패 (`_NON_WORD`가 공백 치환이라 `don t`, `ac dc`가 됨) | Task 1: 아포스트로피는 삭제, 나머지는 공백. 기대값 수정 |
| 아티스트 게이트가 총점 cap이라 `--threshold 0.65`면 무력화 | Task 2: cap 제거, `best_match`에서 독립 게이트로 |
| 재생시간이 같은 라이브 버전이 0.83으로 통과 | Task 2: 버전 페널티 신설 |
| `--dry-run`이 state를 오염시켜 다음 실제 실행이 아무것도 안 함 | Task 7: dry-run은 state를 저장하지 않음 |
| 실패 시 `continue`가 `sleep`과 체크포인트 저장을 건너뜀 | Task 7: 곡 처리 실패를 예외로 만들지 않아 `continue` 자체를 제거 |
| `KeyboardInterrupt`가 최종 저장을 우회 | Task 7: `try/finally` |
| state 쓰기가 비원자적 → 깨진 JSON → 조용히 새 state → **중복 플레이리스트 생성** | Task 3: `os.replace` 원자적 쓰기 + 손상 시 예외 |
| ytmusicapi 쓰기 응답을 버림 (`create_playlist`는 실패 시 dict 반환) | Task 6: 응답 검증 함수 신설 |
| `duplicates=False`는 중복 시 에러 반환 + 아무것도 추가 안 함 | Task 6/7: 중복 에러를 "이미 존재함"으로 해석해 matched 기록 |
| `--all`에서 리포트 생성이 try 밖, 전부 실패해도 exit 0 | Task 7: 리포트까지 격리, 실패 시 exit 1 |
| `check_spotify()`가 인증을 실제로 확인하지 않음 | Task 8: `current_user()` 호출 |
| `sync_playlist`에 테스트가 0개 | Task 7: fake 클라이언트로 12개 시나리오 |
| `album`/`isrc`를 수집하지만 아무 데도 안 씀 | Task 5: 제거 |
| 리포트 파일명이 분 단위라 `--all`에서 충돌 | Task 4: 초 단위 |

## File Structure

```
spotify-to-ytmusic/
├── SKILL.md
├── requirements.txt
└── scripts/
    ├── match.py                  # 정규화 + 점수 + 게이트 (표준 라이브러리만)
    ├── state.py                  # state 원자적 로드/저장 (표준 라이브러리만)
    ├── report.py                 # 리포트 마크다운 (표준 라이브러리만)
    ├── fetch_spotify.py          # Spotify → tracks JSON
    ├── sync_ytmusic.py           # 검색 → 매칭 → 추가 → state/리포트
    ├── check_auth.py             # 양쪽 인증 실동작 점검
    ├── test_match.py             # 27 tests
    ├── test_state.py             # 11 tests
    ├── test_report.py            # 8 tests
    ├── test_fetch_spotify.py     # 11 tests
    └── test_sync_ytmusic.py      # 31 tests
```

총 88개 테스트.

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
# spotipy 2.26.0부터 Spotify 2026-02 마이그레이션(/playlists/{id}/items)을 지원한다.
# 2.24/2.25는 구 엔드포인트를 호출하므로 이 스킬과 호환되지 않는다.
spotipy>=2.26.0
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
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: PASS — 13 passed

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/requirements.txt spotify-to-ytmusic/scripts/match.py spotify-to-ytmusic/scripts/test_match.py
git commit -m "feat(spotify-to-ytmusic): 제목/아티스트 정규화 함수 추가"
```

---

## Task 2: 점수 계산 · 버전 페널티 · 아티스트 게이트

**Files:**
- Modify: `spotify-to-ytmusic/scripts/match.py` (Task 1 파일에 추가)
- Test: `spotify-to-ytmusic/scripts/test_match.py` (Task 1 파일에 추가)

**Interfaces:**
- Consumes: `normalize_title`, `normalize_artist` (Task 1)
- Produces:
  - `DEFAULT_THRESHOLD: float = 0.75`, `ARTIST_GATE: float = 0.5`, `VERSION_PENALTY: float = 0.25`
  - `Score` — `NamedTuple(total: float, title: float, artist: float, duration: float, penalty: float)`
  - `score_candidate(track: dict, candidate: dict) -> Score`
  - `best_match(track: dict, candidates: list[dict], threshold: float = DEFAULT_THRESHOLD) -> MatchResult`
  - `MatchResult` — `NamedTuple(candidate: dict | None, score: float, best_candidate: dict | None)`
    - `candidate`: 게이트와 임계값을 모두 통과해 채택된 후보. 없으면 `None`
    - `score`: 채택된 후보의 점수. 채택이 없으면 최고 총점
    - `best_candidate`: 게이트·임계값과 무관한 최고 총점 후보. 후보가 없으면 `None`
  - track dict: `{"id": str, "title": str, "artists": list[str], "duration_ms": int}`
  - candidate dict: `{"video_id": str, "title": str, "artists": list[str], "duration_sec": int | None}`

**핵심 설계:** 아티스트 게이트는 총점 상한(cap)이 아니라 `best_match`의 독립 조건이다. cap으로 만들면 사용자가 `--threshold`를 낮췄을 때 커버곡이 통과한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`test_match.py` **끝에 이어서 추가**:

```python
from match import (
    ARTIST_GATE,
    DEFAULT_THRESHOLD,
    MatchResult,
    best_match,
    score_candidate,
)


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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: FAIL — `ImportError: cannot import name 'ARTIST_GATE' from 'match'`

- [ ] **Step 3: 점수 계산 구현**

`match.py` **끝에 이어서 추가**:

```python
from difflib import SequenceMatcher
from typing import NamedTuple

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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_match.py -v`
Expected: PASS — 27 passed

실패하면 임계값·게이트 상수를 테스트에 맞춰 바꾸지 말 것. 아래로 개별 점수를 찍어 어느 신호가 예상과 다른지 먼저 확인한다.

```bash
python3 -c "
import match
print(match.score_candidate(
    {'title':'Creep','artists':['Radiohead'],'duration_ms':238000},
    {'title':'Creep (Live)','artists':['Radiohead'],'duration_sec':238}))
"
```

- [ ] **Step 5: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/match.py spotify-to-ytmusic/scripts/test_match.py
git commit -m "feat(spotify-to-ytmusic): 점수 계산·버전 페널티·아티스트 게이트 추가"
```

---

## Task 3: state 저장소 (원자적 쓰기 + 손상 감지)

**Files:**
- Create: `spotify-to-ytmusic/scripts/state.py`
- Test: `spotify-to-ytmusic/scripts/test_state.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `StateCorrupted(Exception)`
  - `data_home() -> Path`, `state_dir() -> Path`, `report_dir() -> Path`, `auth_file() -> Path`
  - `state_path(playlist_id: str) -> Path`
  - `new_state(playlist_id: str, playlist_name: str) -> dict`
  - `load_state(playlist_id: str, playlist_name: str = "") -> dict` — 파일이 없으면 `new_state`, **손상됐으면 `StateCorrupted`**
  - `save_state(state: dict) -> Path` — 임시 파일 + `os.replace`로 원자적 저장

**핵심 설계:** 손상된 state를 만났을 때 조용히 새 state로 넘어가면 `yt_playlist_id`를 잃고 다음 실행이 **중복 플레이리스트를 만든다.** 반드시 예외를 던져 사용자가 개입하게 한다.

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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state'`

- [ ] **Step 3: state.py 구현**

`spotify-to-ytmusic/scripts/state.py`:

```python
#!/usr/bin/env python3
"""동기화 상태(state) 파일의 경로 결정과 원자적 읽기/쓰기를 담당한다.

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


class StateCorrupted(Exception):
    """state 파일을 읽을 수 없을 때. 조용한 복구는 중복 플레이리스트를 만든다."""


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
    """state 파일을 읽는다. 없으면 새 state, 손상됐으면 StateCorrupted."""
    path = state_path(playlist_id)
    if not path.exists():
        return new_state(playlist_id, playlist_name)

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise StateCorrupted(
            f"state 파일을 읽을 수 없습니다: {path}\n"
            f"사유: {exc}\n"
            "내용을 확인한 뒤 파일을 지우고 다시 실행하세요. "
            "그대로 새로 시작하면 YouTube Music에 중복 플레이리스트가 생깁니다."
        ) from exc

    if not isinstance(loaded, dict) or "spotify_playlist_id" not in loaded:
        raise StateCorrupted(
            f"state 파일 형식이 올바르지 않습니다: {path}\n"
            "내용을 확인한 뒤 파일을 지우고 다시 실행하세요."
        )

    base = new_state(playlist_id, playlist_name)
    base.update(loaded)
    if playlist_name:
        base["spotify_playlist_name"] = playlist_name
    return base


def save_state(state: dict) -> Path:
    """state를 원자적으로 저장하고 last_sync를 갱신한다.

    임시 파일에 쓴 뒤 os.replace로 교체한다. 직접 덮어쓰면 중단 시
    잘린 JSON이 남고, 그 파일은 다음 실행에서 StateCorrupted를 유발한다.
    """
    state["last_sync"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path = state_path(state["spotify_playlist_id"])
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)
    return path
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_state.py -v`
Expected: PASS — 11 passed

- [ ] **Step 5: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/state.py spotify-to-ytmusic/scripts/test_state.py
git commit -m "feat(spotify-to-ytmusic): 원자적 state 저장소 추가"
```

---

## Task 4: 리포트 생성

**Files:**
- Create: `spotify-to-ytmusic/scripts/report.py`
- Test: `spotify-to-ytmusic/scripts/test_report.py`

**Interfaces:**
- Consumes: `state.report_dir()` (Task 3)
- Produces:
  - `LOW_CONFIDENCE_MAX: float = 0.85`
  - `build_report(state_data: dict, run: dict) -> str`
  - `write_report(playlist_name: str, content: str, now: datetime | None = None) -> Path` — 파일명은 **초 단위**
  - run dict:
    ```python
    {
      "total": int, "already": int, "interrupted": bool,
      "newly_matched": [{"title", "artists", "yt_title", "score", "video_id"}],
      "newly_unmatched": [{"title", "artists", "best_candidate", "score", "reason"}],
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
    run = {
        "total": 3,
        "already": 1,
        "interrupted": False,
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
    assert table_line.count("|") == 6 + 2  # 5열 경계 6개 + 이스케이프된 2개


def test_write_report_uses_second_precision(tmp_home):
    """--all에서 같은 분에 두 리포트가 나오면 분 단위 파일명은 충돌한다."""
    path = report.write_report(
        "My List", "# 내용", now=datetime(2026, 8, 16, 14, 30, 45)
    )
    assert path == tmp_home / "reports" / "My List-20260816-143045.md"
    assert path.read_text(encoding="utf-8") == "# 내용"
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


def _cell(value) -> str:
    """표 셀 값을 안전하게 만든다. 파이프와 개행은 표를 깨뜨린다."""
    text = str(value) if value is not None else ""
    text = text.replace("|", "\\|")
    return " ".join(text.split())


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
            "- YouTube Music 플레이리스트: "
            f"https://music.youtube.com/playlist?list={yt_id}"
        )
    if run.get("interrupted"):
        lines.append("- **사용자 중단으로 조기 종료됨. 다시 실행하면 이어서 진행합니다.**")

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
                f"| {_cell(item.get('title'))} "
                f"| {_cell(_artists(item.get('artists', [])))} "
                f"| {_cell(item.get('best_candidate') or '(후보 없음)')} "
                f"| {item.get('score', 0):.2f} "
                f"| {_cell(item.get('reason'))} |"
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
                f"| {_cell(item.get('title'))} "
                f"| {_cell(_artists(item.get('artists', [])))} "
                f"| {_cell(item.get('yt_title'))} "
                f"| {item.get('score', 0):.2f} |"
            )
        lines.append("")

    if not unmatched and not low:
        lines += [
            "모든 곡이 높은 신뢰도로 매칭되었습니다. 확인이 필요한 항목이 없습니다.",
            "",
        ]

    return "\n".join(lines)


def _safe_name(value: str) -> str:
    cleaned = _UNSAFE.sub("_", value).strip()
    return re.sub(r"\s+", " ", cleaned) or "playlist"


def write_report(playlist_name: str, content: str, now: datetime | None = None) -> Path:
    """리포트를 파일로 저장하고 경로를 돌려준다.

    파일명은 초 단위다. 분 단위면 --all로 여러 플레이리스트를 처리할 때
    같은 파일을 덮어쓴다.
    """
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    path = state.report_dir() / f"{_safe_name(playlist_name)}-{stamp}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_report.py -v`
Expected: PASS — 8 passed

`test_report_escapes_pipes_and_newlines_in_cells`의 파이프 개수 단언이 틀리면, 실제 출력 줄을 찍어 경계 파이프와 이스케이프된 파이프 개수를 세어 단언을 실제에 맞게 고친다. 이스케이프 자체가 동작하는지(`\|`가 있고 개행이 없는지)가 이 테스트의 핵심이다.

- [ ] **Step 5: 누적 테스트 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -q`
Expected: PASS — 46 passed (27 + 11 + 8)

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/report.py spotify-to-ytmusic/scripts/test_report.py
git commit -m "feat(spotify-to-ytmusic): 마크다운 리포트 생성 추가"
```

---

## Task 5: Spotify 트랙 수집 (2026-02 스키마)

**Files:**
- Create: `spotify-to-ytmusic/scripts/fetch_spotify.py`
- Test: `spotify-to-ytmusic/scripts/test_fetch_spotify.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `extract_playlist_id(value: str) -> str | None`
  - `parse_items(items: list) -> tuple[list[dict], int]` — **순수 함수**, `(트랙 목록, 건너뛴 개수)`
  - `PlaylistNotFound`, `AmbiguousPlaylist`, `PlaylistAccessDenied` (모두 `Exception`)
  - `find_playlist_by_name(sp, name: str) -> dict`
  - `fetch_playlist(sp, playlist_id: str) -> dict`
  - `fetch_all_playlists(sp) -> list[dict]`
  - `build_client()`
  - CLI: `python3 fetch_spotify.py <url|id|name>` → stdout JSON 객체 / `--all` → JSON 배열

**핵심 변경 (Spotify 2026-02):**
- 응답 필드가 `items[].track` → `items[].item`. `fields` 표현식도 `items(item(...)),next`
- `sp.playlist_items()`가 `/playlists/{id}/items`를 호출한다 (spotipy 2.26+). 메서드명은 그대로
- 소유/협업 플레이리스트가 아니면 내용을 받을 수 없다. 이 경우 사유를 명시하고 중단
- `album`, `isrc`는 수집하지 않는다 (매칭에 쓰지 않음)

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_fetch_spotify.py`:

```python
"""fetch_spotify.py의 순수 함수 단위 테스트."""

import pytest

from fetch_spotify import extract_playlist_id, parse_items


@pytest.mark.parametrize(
    "value,expected",
    [
        (
            "https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n",
            "3cEYpjA9oz9GiPac4AsH4n",
        ),
        (
            "https://open.spotify.com/playlist/3cEYpjA9oz9GiPac4AsH4n?si=abc123",
            "3cEYpjA9oz9GiPac4AsH4n",
        ),
        ("spotify:playlist:3cEYpjA9oz9GiPac4AsH4n", "3cEYpjA9oz9GiPac4AsH4n"),
        ("3cEYpjA9oz9GiPac4AsH4n", "3cEYpjA9oz9GiPac4AsH4n"),
        ("내 플레이리스트", None),
        ("", None),
        ("https://open.spotify.com/album/3cEYpjA9oz9GiPac4AsH4n", None),
    ],
)
def test_extract_playlist_id(value, expected):
    assert extract_playlist_id(value) == expected


def test_parse_items_reads_2026_schema():
    """2026-02 마이그레이션 이후 항목 키는 'track'이 아니라 'item'이다."""
    items = [
        {
            "item": {
                "id": "sp1",
                "name": "Perfect",
                "duration_ms": 263_000,
                "artists": [{"name": "Ed Sheeran"}, {"name": "Beyonce"}],
            }
        }
    ]
    tracks, skipped = parse_items(items)
    assert skipped == 0
    assert tracks == [
        {
            "id": "sp1",
            "title": "Perfect",
            "artists": ["Ed Sheeran", "Beyonce"],
            "duration_ms": 263_000,
        }
    ]


def test_parse_items_skips_null_and_idless_entries():
    items = [
        {"item": None},
        {"item": {"name": "Local File", "duration_ms": 1000, "artists": []}},
        {},
        {
            "item": {
                "id": "sp2",
                "name": "OK",
                "duration_ms": 1000,
                "artists": [{"name": "A"}],
            }
        },
    ]
    tracks, skipped = parse_items(items)
    assert skipped == 3
    assert [t["id"] for t in tracks] == ["sp2"]


def test_parse_items_tolerates_missing_fields():
    tracks, skipped = parse_items([{"item": {"id": "sp3"}}])
    assert skipped == 0
    assert tracks[0] == {"id": "sp3", "title": "", "artists": [], "duration_ms": 0}


def test_parse_items_handles_empty_list():
    assert parse_items([]) == ([], 0)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_fetch_spotify.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_spotify'`

- [ ] **Step 3: fetch_spotify.py 구현**

`spotify-to-ytmusic/scripts/fetch_spotify.py`:

```python
#!/usr/bin/env python3
"""Spotify 플레이리스트의 트랙 목록을 JSON으로 뽑는다.

Spotify가 2026-02에 Web API를 개편했다. 플레이리스트 항목 엔드포인트는
/playlists/{id}/items이고 항목 키는 'track'이 아니라 'item'이다.
또한 소유하거나 협업 중인 플레이리스트만 내용을 조회할 수 있다.

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

# 2026-02 스키마: items[].item (구 스키마의 items[].track)
ITEM_FIELDS = "items(item(id,name,duration_ms,artists(name))),next"

_URL_RE = re.compile(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)")
_URI_RE = re.compile(r"^spotify:playlist:([A-Za-z0-9]+)$")
_RAW_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")

ACCESS_HINT = (
    "Spotify는 2026년 2월부터 본인이 소유하거나 협업 중인 플레이리스트의 "
    "내용만 제공합니다. 다른 사람의 플레이리스트나 Spotify 에디토리얼 "
    "플레이리스트(예: Today's Top Hits)는 복제할 수 없습니다.\n"
    "내 라이브러리로 복사한 뒤 다시 시도하세요."
)


class PlaylistNotFound(Exception):
    pass


class AmbiguousPlaylist(Exception):
    pass


class PlaylistAccessDenied(Exception):
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


def parse_items(items: list) -> tuple[list[dict], int]:
    """플레이리스트 항목 배열을 트랙 목록으로 바꾼다.

    반환: (트랙 목록, 건너뛴 개수)
    로컬 파일·삭제된 트랙·팟캐스트 에피소드는 id가 없어 건너뛴다.
    """
    tracks = []
    skipped = 0
    for entry in items or []:
        item = (entry or {}).get("item")
        if not item or not item.get("id"):
            skipped += 1
            continue
        tracks.append(
            {
                "id": item["id"],
                "title": item.get("name", ""),
                "artists": [a["name"] for a in item.get("artists", []) if a.get("name")],
                "duration_ms": item.get("duration_ms") or 0,
            }
        )
    return tracks, skipped


def build_client():
    """인증된 spotipy 클라이언트를 만든다."""
    if not SPOTIPY_AVAILABLE:
        print(
            "Error: spotipy 필요. 설치: "
            "pip3 install --break-system-packages 'spotipy>=2.26.0'",
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
    try:
        meta = sp.playlist(playlist_id, fields="id,name,description")
    except Exception as exc:
        raise PlaylistAccessDenied(f"{exc}\n\n{ACCESS_HINT}") from exc

    tracks: list[dict] = []
    skipped = 0

    try:
        results = sp.playlist_items(
            playlist_id, fields=ITEM_FIELDS, additional_types=["track"]
        )
    except Exception as exc:
        raise PlaylistAccessDenied(f"{exc}\n\n{ACCESS_HINT}") from exc

    while results:
        page_tracks, page_skipped = parse_items(results.get("items", []))
        tracks.extend(page_tracks)
        skipped += page_skipped
        results = sp.next(results) if results.get("next") else None

    if not tracks and skipped == 0:
        # 내용이 비어 오는 가장 흔한 원인은 소유/협업이 아닌 플레이리스트다.
        print(f"경고: 트랙이 하나도 조회되지 않았습니다.\n{ACCESS_HINT}", file=sys.stderr)
    if skipped:
        print(
            f"건너뛴 항목 {skipped}개 (로컬 파일, 삭제된 트랙, 에피소드 등)",
            file=sys.stderr,
        )

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
        if not payload:
            print("수집된 플레이리스트가 없습니다.", file=sys.stderr)
            return 1
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
        except PlaylistAccessDenied as exc:
            print(f"플레이리스트에 접근할 수 없습니다:\n{exc}", file=sys.stderr)
            return 1

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_fetch_spotify.py -v`
Expected: PASS — 11 passed

- [ ] **Step 5: CLI가 spotipy 없이도 로드되는지 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 fetch_spotify.py --help`
Expected: argparse 도움말 출력, exit 0

- [ ] **Step 6: spotipy 설치 후 실제 시그니처 확인**

계획은 spotipy 2.26의 `playlist_items(playlist_id, fields=..., additional_types=...)` 시그니처와 `/playlists/{id}/items` 엔드포인트를 전제한다. 설치 후 실제와 맞는지 확인한다.

```bash
pip3 install --break-system-packages 'spotipy>=2.26.0'
python3 -c "
import inspect, spotipy
print('spotipy', spotipy.__version__)
print(inspect.signature(spotipy.Spotify.playlist_items))
print('items endpoint:', 'items' in inspect.getsource(spotipy.Spotify.playlist_items))
"
```
Expected: 버전 2.26.0 이상, 시그니처에 `fields`와 `additional_types`가 있고 엔드포인트에 `items` 포함

시그니처가 다르면 **계획을 따르지 말고 실제 API에 맞춰 고친 뒤 그 사실을 보고한다.**

- [ ] **Step 7: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/fetch_spotify.py spotify-to-ytmusic/scripts/test_fetch_spotify.py
git commit -m "feat(spotify-to-ytmusic): Spotify 트랙 수집 (2026-02 스키마)"
```

---

## Task 6: YT 응답 파싱·검증 함수

**Files:**
- Create: `spotify-to-ytmusic/scripts/sync_ytmusic.py` (순수 함수 부분만)
- Test: `spotify-to-ytmusic/scripts/test_sync_ytmusic.py`

**Interfaces:**
- Consumes: (없음)
- Produces:
  - `parse_duration(value) -> int | None`
  - `to_candidate(result: dict) -> dict | None`
  - `YTWriteError(Exception)`, `YTDuplicateError(Exception)`, `YTPlaylistMissing(Exception)`
  - `validate_create_response(response) -> str` — 문자열 ID 반환, 아니면 `YTWriteError`
  - `validate_add_response(response) -> None` — 실패면 `YTWriteError`, 중복이면 `YTDuplicateError`
  - 상수: `MAX_ATTEMPTS = 3`, `SEARCH_LIMIT = 5`, `SAVE_EVERY = 10`, `SUCCESS_STATUS`

**핵심 설계:** ytmusicapi는 실패를 예외가 아니라 반환값으로 알린다. `create_playlist`는 실패 시 응답 dict를 그대로 돌려주므로, 검증 없이 저장하면 dict가 `yt_playlist_id`가 된다. `add_playlist_items`는 `{"status": ...}`를 돌려주며 `duplicates=False`일 때 중복이 있으면 **에러를 반환하고 아무것도 추가하지 않는다.** 한 곡씩 추가하므로 이 에러는 "그 곡이 이미 있다"는 뜻이고, 실패가 아니라 "이미 존재함"으로 해석해야 한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`spotify-to-ytmusic/scripts/test_sync_ytmusic.py`:

```python
"""sync_ytmusic.py 테스트."""

import pytest

from sync_ytmusic import (
    YTDuplicateError,
    YTWriteError,
    parse_duration,
    to_candidate,
    validate_add_response,
    validate_create_response,
)


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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sync_ytmusic'`

- [ ] **Step 3: 순수 함수 구현**

`spotify-to-ytmusic/scripts/sync_ytmusic.py` (이 태스크에서는 아래까지만 작성):

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

MAX_ATTEMPTS = 3  # 최초 시도 + 재시도 2회
SEARCH_LIMIT = 5
SAVE_EVERY = 10
SUCCESS_STATUS = "STATUS_SUCCEEDED"

# 인증·권한 오류는 재시도해도 달라지지 않는다.
_NO_RETRY_HINTS = ("unauthorized", "forbidden", "401", "403", "auth")

# 중복 판정 힌트. ytmusicapi가 실패 사유를 문자열로만 알려주는 경우가 있어
# 최선 노력으로 감지하고, 못 잡으면 일반 쓰기 실패로 처리한다.
_DUPLICATE_HINTS = ("duplicate", "already in", "already exists")


class YTWriteError(Exception):
    """YouTube Music 쓰기가 실패했다."""


class YTDuplicateError(Exception):
    """추가하려는 곡이 이미 플레이리스트에 있다."""


class YTPlaylistMissing(Exception):
    """state에 기록된 YT 플레이리스트에 접근할 수 없다."""


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
        name = artist.get("name") if isinstance(artist, dict) else artist
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


def validate_create_response(response) -> str:
    """create_playlist 반환값을 검증한다.

    성공하면 플레이리스트 ID 문자열, 실패하면 응답 dict가 온다.
    검증 없이 저장하면 dict가 yt_playlist_id로 기록된다.
    """
    if isinstance(response, str) and response.strip():
        return response.strip()
    raise YTWriteError(f"플레이리스트 생성에 실패했습니다: {response!r}")


def validate_add_response(response) -> None:
    """add_playlist_items 반환값을 검증한다.

    duplicates=False에서 중복이면 에러가 반환되고 아무것도 추가되지 않는다.
    한 곡씩 추가하므로 이 에러는 '그 곡이 이미 있다'는 뜻이다.
    """
    if not isinstance(response, dict):
        raise YTWriteError(f"곡 추가 응답이 올바르지 않습니다: {response!r}")

    if str(response.get("status", "")) == SUCCESS_STATUS:
        return

    text = json.dumps(response, ensure_ascii=False).lower()
    if any(hint in text for hint in _DUPLICATE_HINTS):
        raise YTDuplicateError(f"이미 플레이리스트에 있는 곡입니다: {response!r}")
    raise YTWriteError(f"곡 추가에 실패했습니다: {response!r}")
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: PASS — 19 passed

- [ ] **Step 5: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/sync_ytmusic.py spotify-to-ytmusic/scripts/test_sync_ytmusic.py
git commit -m "feat(spotify-to-ytmusic): YT 응답 파싱·검증 함수 추가"
```

---

## Task 7: 동기화 오케스트레이션 + fake 클라이언트 테스트

**Files:**
- Modify: `spotify-to-ytmusic/scripts/sync_ytmusic.py` (Task 6 파일에 추가)
- Test: `spotify-to-ytmusic/scripts/test_sync_ytmusic.py` (Task 6 파일에 추가)

**Interfaces:**
- Consumes:
  - `match.best_match`, `match.DEFAULT_THRESHOLD` (Task 2)
  - `state.load_state`, `state.save_state`, `state.state_path`, `state.auth_file` (Task 3)
  - `report.build_report`, `report.write_report` (Task 4)
  - `to_candidate`, `validate_create_response`, `validate_add_response`, 예외 3종, 상수 (Task 6)
- Produces:
  - `search_candidates(yt, track) -> list[dict]`
  - `ensure_playlist_exists(yt, playlist_id) -> None`
  - `sync_playlist(yt, playlist_data, threshold, delay, privacy, dry_run) -> tuple[dict, dict]`
  - CLI: `--tracks <path|->`, `--threshold`, `--delay`, `--public`, `--dry-run`

**이 태스크가 고치는 P1 5건:**
1. `--dry-run`이 state를 저장하지 않는다
2. 곡 처리 실패를 예외로 만들지 않아 `continue`가 사라지고, 딜레이·체크포인트가 모든 경로에서 실행된다
3. `try/finally`로 `KeyboardInterrupt` 시에도 state를 저장한다
4. 기록된 YT 플레이리스트가 실제로 있는지 확인한다 (없으면 "변경 없음" 거짓 성공)
5. `--all`에서 리포트 생성까지 격리하고, 하나라도 실패하면 exit 1

- [ ] **Step 1: 실패하는 테스트 작성**

`test_sync_ytmusic.py` **끝에 이어서 추가**:

```python
import state as state_module
import sync_ytmusic


@pytest.fixture(autouse=True)
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setenv("SPOTIFY_TO_YTMUSIC_HOME", str(tmp_path))
    monkeypatch.setattr(sync_ytmusic.time, "sleep", lambda _s: None)
    return tmp_path


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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: FAIL — `AttributeError: module 'sync_ytmusic' has no attribute 'sync_playlist'`

- [ ] **Step 3: 오케스트레이션 구현**

`sync_ytmusic.py` **끝에 이어서 추가**:

```python
def _should_retry(exc: Exception) -> bool:
    """인증·권한 오류는 재시도해도 달라지지 않는다."""
    text = str(exc).lower()
    return not any(hint in text for hint in _NO_RETRY_HINTS)


def _with_retry(func, description: str):
    """최대 MAX_ATTEMPTS번 시도한다. 대기는 1초 → 2초."""
    delay = 1.0
    last_exc = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if not _should_retry(exc) or attempt == MAX_ATTEMPTS:
                break
            print(
                f"  재시도 {attempt}/{MAX_ATTEMPTS - 1} ({description}): {exc}",
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


def ensure_playlist_exists(yt, playlist_id: str) -> None:
    """state에 기록된 플레이리스트가 실제로 있는지 확인한다.

    이 확인이 없으면 플레이리스트가 삭제된 뒤에도 '변경 없음'이라는
    거짓 성공을 보고한다.
    """
    try:
        yt.get_playlist(playlist_id, limit=1)
    except Exception as exc:
        raise YTPlaylistMissing(
            f"기록된 YouTube Music 플레이리스트에 접근할 수 없습니다: {playlist_id}\n"
            f"사유: {exc}\n"
            "삭제됐거나 다른 계정의 것일 수 있습니다. "
            "state 파일을 지우면 새로 만듭니다."
        ) from exc


def _unmatched_entry(track: dict, best: dict | None, score: float, reason: str) -> dict:
    return {
        "track_id": track["id"],
        "title": track.get("title", ""),
        "artists": track.get("artists", []),
        "best_candidate": best["title"] if best else None,
        "score": score,
        "reason": reason,
    }


def _process_track(yt, st, run, track, position, total, threshold, dry_run) -> None:
    """곡 하나를 처리한다. 개별 실패를 예외로 올리지 않는다.

    예외로 올리면 호출부가 continue를 써야 하고, 그러면 딜레이와
    체크포인트 저장을 건너뛰게 된다.
    """
    label = f"{track.get('title', '')} — {', '.join(track.get('artists') or [])}"
    prefix = f"  [{position}/{total}]"

    try:
        candidates = search_candidates(yt, track)
    except Exception as exc:
        run["newly_unmatched"].append(
            _unmatched_entry(track, None, 0.0, f"검색 실패: {exc}")
        )
        print(f"{prefix} 검색 실패: {label}", file=sys.stderr)
        return

    result = match.best_match(track, candidates, threshold=threshold)
    if result.candidate is None:
        reason = "임계값 미달" if result.best_candidate else "후보 없음"
        run["newly_unmatched"].append(
            _unmatched_entry(track, result.best_candidate, result.score, reason)
        )
        print(f"{prefix} 미매칭({result.score:.2f}): {label}", file=sys.stderr)
        return

    video_id = result.candidate["video_id"]
    note = "추가"

    if not dry_run:
        try:
            response = _with_retry(
                lambda: yt.add_playlist_items(
                    st["yt_playlist_id"], [video_id], duplicates=False
                ),
                f"곡 추가: {label}",
            )
            validate_add_response(response)
        except YTDuplicateError:
            # 사용자가 수동으로 넣어둔 곡. 실패가 아니라 이미 완료된 상태다.
            note = "이미 존재"
        except Exception as exc:
            run["newly_unmatched"].append(
                _unmatched_entry(track, result.candidate, result.score, f"추가 실패: {exc}")
            )
            print(f"{prefix} 추가 실패: {label}", file=sys.stderr)
            return

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
    print(f"{prefix} {note}({result.score:.2f}): {label}", file=sys.stderr)


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

    st = state.load_state(playlist_id, playlist_name)  # 손상 시 StateCorrupted
    pending = [t for t in tracks if t["id"] not in st["matched"]]

    run = {
        "total": len(tracks),
        "already": len(tracks) - len(pending),
        "interrupted": False,
        "newly_matched": [],
        "newly_unmatched": [],
    }

    print(f"[{playlist_name}] 전체 {len(tracks)}곡, 신규 {len(pending)}곡", file=sys.stderr)

    if st["yt_playlist_id"] and not dry_run:
        ensure_playlist_exists(yt, st["yt_playlist_id"])

    if not pending:
        print("변경 없음 — 이미 모두 동기화되어 있습니다.", file=sys.stderr)
        return st, run

    if not dry_run and not st["yt_playlist_id"]:
        response = _with_retry(
            lambda: yt.create_playlist(
                playlist_name or "Spotify Import",
                playlist_data.get("playlist_description", "")
                or "Spotify에서 복제한 플레이리스트",
                privacy_status=privacy,
            ),
            "플레이리스트 생성",
        )
        st["yt_playlist_id"] = validate_create_response(response)
        state.save_state(st)
        print(f"YT 플레이리스트 생성: {st['yt_playlist_id']}", file=sys.stderr)

    try:
        for position, track in enumerate(pending, start=1):
            _process_track(yt, st, run, track, position, len(pending), threshold, dry_run)
            if not dry_run and position % SAVE_EVERY == 0:
                st["unmatched"] = run["newly_unmatched"]
                state.save_state(st)
            time.sleep(delay)
    except KeyboardInterrupt:
        run["interrupted"] = True
        print("\n중단 요청을 받았습니다. 진행 상황을 저장합니다.", file=sys.stderr)
    finally:
        # dry-run은 저장하지 않는다. 저장하면 matched가 채워져
        # 다음 실제 실행이 '변경 없음'으로 끝나고 플레이리스트를 만들지 않는다.
        if not dry_run:
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
        help=f"매칭 임계값 (기본 {match.DEFAULT_THRESHOLD}). "
        "아티스트 게이트는 이 값과 무관하게 항상 적용된다",
    )
    parser.add_argument("--delay", type=float, default=0.3, help="곡당 요청 간격(초)")
    parser.add_argument("--public", action="store_true", help="플레이리스트를 공개로 생성")
    parser.add_argument("--dry-run", action="store_true", help="매칭만 하고 YT에 쓰지 않는다")
    args = parser.parse_args()

    if not YTMUSIC_AVAILABLE:
        print(
            "Error: ytmusicapi 필요. 설치: pip3 install --break-system-packages ytmusicapi",
            file=sys.stderr,
        )
        return 1

    payload = load_payload(args.tracks)
    playlists = payload if isinstance(payload, list) else [payload]

    if args.dry_run:
        # dry-run은 검색만 한다. 인증 파일이 있으면 쓰고, 없으면 비인증 클라이언트.
        auth = state.auth_file()
        yt = YTMusic(str(auth)) if auth.exists() else YTMusic()
    else:
        yt = build_client()

    failures = 0
    done = 0
    for playlist_data in playlists:
        name = playlist_data.get("playlist_name", "?")
        try:
            st, run = sync_playlist(
                yt,
                playlist_data,
                threshold=args.threshold,
                delay=args.delay,
                privacy="PUBLIC" if args.public else "PRIVATE",
                dry_run=args.dry_run,
            )
            content = report.build_report(st, run)
            path = report.write_report(
                st.get("spotify_playlist_name") or "playlist", content
            )
            done += 1
            print(f"리포트: {path}", file=sys.stderr)
        except Exception as exc:
            failures += 1
            print(f"동기화 실패: {name} — {exc}", file=sys.stderr)

    if len(playlists) > 1:
        print(
            f"\n총 {len(playlists)}개 중 {done}개 완료, {failures}개 실패",
            file=sys.stderr,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest test_sync_ytmusic.py -v`
Expected: PASS — 31 passed

- [ ] **Step 5: 전체 테스트 + CLI 확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -q && python3 sync_ytmusic.py --help`
Expected: 88 passed, 이어서 argparse 도움말 출력

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/sync_ytmusic.py spotify-to-ytmusic/scripts/test_sync_ytmusic.py
git commit -m "feat(spotify-to-ytmusic): 동기화 오케스트레이션 및 fake 클라이언트 테스트 추가"
```

---

## Task 8: 인증 점검 (실동작 확인)

**Files:**
- Create: `spotify-to-ytmusic/scripts/check_auth.py`

**Interfaces:**
- Consumes: `state.auth_file()`, `state.data_home()` (Task 3)
- Produces: CLI — 양쪽 정상이면 exit 0, 하나라도 실패면 셋업 절차 출력 후 exit 1

**핵심 변경:** `check_spotify()`가 환경변수 존재만 보지 않고 실제로 `current_user()`를 호출한다. 환경변수만 확인하면 잘못된 자격증명, 틀린 Redirect URI, 만료된 토큰이 모두 OK로 보고된다. Premium 여부도 함께 확인한다 — Development Mode 앱은 Premium이 필요하다.

- [ ] **Step 1: check_auth.py 구현**

`spotify-to-ytmusic/scripts/check_auth.py`:

```python
#!/usr/bin/env python3
"""Spotify / YouTube Music 인증 상태를 점검하고 미설정 시 셋업 절차를 안내한다."""

import os
import sys

import state

SCOPE = "playlist-read-private playlist-read-collaborative"

SPOTIFY_SETUP = """\
[Spotify 셋업]
  사전 조건: Spotify Premium 구독이 필요합니다.
             Development Mode 앱은 소유자가 Premium이어야 동작합니다.

  1. https://developer.spotify.com/dashboard 에서 앱을 생성한다
  2. 앱 설정에서 Redirect URI에 http://127.0.0.1:8888/callback 을 등록한다
  3. 셸 설정 파일(~/.zshrc)에 아래를 추가하고 새 셸을 연다:

     export SPOTIPY_CLIENT_ID="<Client ID>"
     export SPOTIPY_CLIENT_SECRET="<Client Secret>"
     export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"

  4. 최초 실행 시 브라우저 인증 창이 열린다. 승인하면 토큰이 캐시된다

  참고: Spotify는 2026년 2월부터 본인이 소유하거나 협업 중인 플레이리스트의
        내용만 제공한다. 다른 사람의 플레이리스트나 에디토리얼 플레이리스트는
        복제할 수 없다.\
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
        for name in (
            "SPOTIPY_CLIENT_ID",
            "SPOTIPY_CLIENT_SECRET",
            "SPOTIPY_REDIRECT_URI",
        )
        if not os.environ.get(name)
    ]
    if missing:
        return False, f"환경변수 미설정: {', '.join(missing)}"

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        return (
            False,
            "spotipy 미설치 — pip3 install --break-system-packages 'spotipy>=2.26.0'",
        )

    # 환경변수 존재만 보면 잘못된 자격증명·틀린 Redirect URI·만료된 토큰이
    # 전부 OK로 보고된다. 실제로 호출해봐야 한다.
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE, open_browser=False))
        user = sp.current_user()
    except Exception as exc:
        return False, f"인증 실패: {exc}"

    label = user.get("display_name") or user.get("id") or "(이름 없음)"
    if user.get("product") != "premium":
        return (
            False,
            f"{label} 계정이 Premium이 아닙니다 (product={user.get('product')}). "
            "Development Mode 앱은 소유자의 Premium 구독이 필요합니다",
        )
    return True, f"인증됨: {label} (premium)"


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

```bash
cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts
SPOTIFY_TO_YTMUSIC_HOME=/tmp/s2y-check-test env -u SPOTIPY_CLIENT_ID python3 check_auth.py; echo "exit=$?"
```
Expected: `Spotify      : NG — 환경변수 미설정: SPOTIPY_CLIENT_ID` 와 셋업 절차 출력, `exit=1`

- [ ] **Step 3: 테스트 산출물 정리**

```bash
rm -rf /tmp/s2y-check-test
```

- [ ] **Step 4: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/scripts/check_auth.py
git commit -m "feat(spotify-to-ytmusic): 인증 실동작 점검 스크립트 추가"
```

---

## Task 9: SKILL.md 작성 및 README 등록

**Files:**
- Create: `spotify-to-ytmusic/SKILL.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1~8의 모든 스크립트 CLI
- Produces: Skill 도구가 인식하는 스킬 정의

- [ ] **Step 1: SKILL.md 작성**

`spotify-to-ytmusic/SKILL.md` — frontmatter의 `description`은 반드시 한 줄:

```markdown
---
name: spotify-to-ytmusic
description: "내 Spotify 플레이리스트를 YouTube Music에 동일한 구성으로 복제하는 스킬. spotipy로 트랙 목록을 읽고 ytmusicapi로 검색·매칭해 YT Music 플레이리스트를 만들며, 재실행 시 새로 추가된 곡만 증분 동기화한다. 사용자가 '스포티파이 플레이리스트 유튜브 뮤직으로', '플레이리스트 옮겨줘', '플레이리스트 복제', '플레이리스트 이전', 'spotify to ytmusic', '스포티파이에서 유튜브뮤직으로', '플레이리스트 동기화', '음악 목록 옮기기' 등을 언급하면 이 스킬을 사용한다."
---

# Spotify → YouTube Music 플레이리스트 복제

내 Spotify 플레이리스트를 YouTube Music에 같은 구성으로 만든다. 다시 실행하면 새로 추가된 곡만 붙인다.

## 전제 조건 (먼저 확인할 것)

| 조건 | 내용 |
|---|---|
| **Spotify Premium** | Development Mode 앱은 소유자가 Premium이어야 동작한다 |
| **소유/협업 플레이리스트만** | Spotify는 2026년 2월부터 본인이 소유하거나 협업 중인 플레이리스트의 내용만 제공한다. 다른 사람의 플레이리스트나 Spotify 에디토리얼 플레이리스트(Today's Top Hits 등)는 복제할 수 없다. 필요하면 먼저 내 라이브러리로 복사해야 한다 |

사용자가 남의 플레이리스트 URL을 주면 **작업을 시작하기 전에** 이 제약을 알린다.

## 동작 방식

```
fetch_spotify.py  →  tracks.json  →  sync_ytmusic.py  →  YT 플레이리스트 + 리포트
                                          ↕
                                     match.py (점수 계산)
                                     state/<playlist_id>.json
```

곡마다 YT Music에서 상위 5개 후보를 검색해 점수를 매기고, 두 조건을 **모두** 만족하는 후보만 추가한다.

| 신호 | 가중치 |
|---|---|
| 제목 유사도 (부가 표기 제거 후 비교) | 0.5 |
| 아티스트 일치 | 0.3 |
| 재생시간 근접도 | 0.2 |
| 버전 표기 페널티 (후보에만 `live`/`remix`/`cover` 등이 있으면) | −0.25 |

**채택 조건 1 — 아티스트 게이트:** 아티스트 점수 ≥ 0.5
**채택 조건 2 — 임계값:** 총점 ≥ 0.75 (기본값)

아티스트 게이트는 `--threshold`와 **독립**이다. 임계값을 낮춰도 커버곡은 통과하지 못한다.

## 사전 준비 (최초 1회)

### 패키지 설치

```bash
pip3 install --break-system-packages 'spotipy>=2.26.0' ytmusicapi
```

spotipy는 2.26.0 이상이어야 한다. 그 이전 버전은 Spotify가 2026년 2월에 폐기한 엔드포인트를 호출한다.

### 인증 상태 확인

```bash
python3 scripts/check_auth.py
```

실제로 API를 호출해 확인한다. 미설정 항목이 있으면 셋업 절차가 그대로 출력되므로 사용자에게 전달한다.

## 워크플로우

### 1단계: 인증 확인

`python3 scripts/check_auth.py`를 먼저 실행한다. exit code가 0이 아니면 **동기화를 시작하지 말고** 출력된 셋업 절차를 전달한다.

### 2단계: 대상 확인

URL인지, 플레이리스트 이름인지, 전체 일괄인지 파악한다. 이름이 여러 개와 일치하면 스크립트가 후보를 출력하고 멈추므로 사용자에게 되묻는다.

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

매칭된 곡은 검색+추가로 요청이 2회다. 100곡이면 2~3분 정도로 안내한다.

### 4단계: 결과 보고

리포트 경로가 stderr에 출력된다. 리포트를 읽고 **한국어로 요약**한다:

- 전체 / 이미 동기화됨 / 이번 처리 / 매칭 성공 / 미매칭 곡 수
- 미매칭 곡 목록 (제목 · 아티스트 · 최고 후보 · 점수 · 사유)
- 낮은 신뢰도(0.85 미만)로 추가된 곡이 있으면 확인 권장으로 함께 안내
- YT Music 플레이리스트 링크

미매칭이 전체의 20%를 넘으면 `--threshold 0.65`로 재실행을 제안한다. 이미 매칭된 곡은 재검색하지 않으므로 비용이 낮고, 아티스트 게이트는 그대로 유지되므로 커버곡이 새로 섞이지는 않는다.

## 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--threshold` | 0.75 | 매칭 임계값. 낮추면 더 많이 추가된다. 아티스트 게이트는 영향받지 않는다 |
| `--delay` | 0.3 | 곡당 요청 간격(초). ytmusicapi는 비공식 API라 너무 빠르면 차단될 수 있다 |
| `--public` | 꺼짐 | 새 플레이리스트를 공개로 생성 (기본은 비공개) |
| `--dry-run` | 꺼짐 | 매칭 결과만 보고 YT에 쓰지 않는다. **state도 저장하지 않으므로** 이후 실제 실행에 영향을 주지 않는다 |

## 파일 위치

| 용도 | 경로 |
|---|---|
| YT 인증 | `~/.claude/spotify-to-ytmusic/browser.json` |
| 동기화 상태 | `~/.claude/spotify-to-ytmusic/state/<playlist_id>.json` |
| 리포트 | `~/.claude/spotify-to-ytmusic/reports/<이름>-<날짜시각>.md` |

`SPOTIFY_TO_YTMUSIC_HOME` 환경변수로 위치를 바꿀 수 있다.

## 주의사항

- **단방향이다.** Spotify에서 곡을 지워도 YT에서는 지워지지 않는다
- state 파일을 지우면 다음 실행에서 **새 YT 플레이리스트를 만든다.** 기존 것과 이어 붙이려면 state를 유지해야 한다
- state 파일이 손상되면 스크립트가 중단된다. 조용히 새로 시작하면 중복 플레이리스트가 생기기 때문이다. 파일을 확인하고 지울지 판단한다
- 중간에 Ctrl-C로 끊어도 진행 상황은 저장된다. 다시 실행하면 이어서 진행한다
- YT 플레이리스트를 수동으로 삭제했다면 스크립트가 감지하고 중단한다. state 파일을 지우면 새로 만든다

## 테스트

순수 로직과 동기화 흐름 전체에 테스트가 있다 (88개):

```bash
cd <스킬 디렉토리>/scripts && python3 -m pytest -v
```

매칭 로직이나 동기화 흐름을 손봤다면 반드시 이 테스트를 돌린다.
```

- [ ] **Step 2: SKILL.md frontmatter가 한 줄인지 확인**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
python3 -c "
text = open('spotify-to-ytmusic/SKILL.md', encoding='utf-8').read()
block = text.split('---')[1]
desc = [l for l in block.strip().splitlines() if l.startswith('description:')]
assert len(desc) == 1, 'description 줄이 정확히 1개여야 한다'
assert desc[0].rstrip().endswith('\"'), 'description은 한 줄 큰따옴표 문자열이어야 한다'
print('OK: frontmatter 형식 정상')
"
```
Expected: `OK: frontmatter 형식 정상`

- [ ] **Step 3: README 스킬 목록 표에 행 추가**

`README.md`의 스킬 목록 표에서 `gen-report-monodeck-ppt` 행 **다음에** 추가:

```markdown
| [spotify-to-ytmusic](./spotify-to-ytmusic) | 내 Spotify 플레이리스트를 YouTube Music에 동일 구성으로 복제. 재실행 시 새 곡만 증분 동기화하고 미매칭 곡은 리포트로 남김 (Premium·소유 플레이리스트 필요) | "스포티파이 플레이리스트 유튜브뮤직으로", "플레이리스트 옮겨줘", "플레이리스트 복제" |
```

- [ ] **Step 4: README 디렉토리 구조에 항목 추가**

디렉토리 구조 코드블록의 마지막 스킬 항목 다음에 추가:

```
├── spotify-to-ytmusic/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
```

- [ ] **Step 5: 전체 테스트 재확인**

Run: `cd /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic/scripts && python3 -m pytest -q`
Expected: PASS — 88 passed

- [ ] **Step 6: 커밋**

```bash
cd /Users/picpal/Desktop/workspace/claude-skills
git add spotify-to-ytmusic/SKILL.md README.md
git commit -m "docs(spotify-to-ytmusic): SKILL.md 작성 및 README 등록"
```

- [ ] **Step 7: 심볼릭 링크 안내**

구현자는 아래를 **안내만 하고 직접 실행하지 않는다** (사용자 홈 디렉토리 변경):

```bash
ln -s /Users/picpal/Desktop/workspace/claude-skills/spotify-to-ytmusic ~/.claude/skills/spotify-to-ytmusic
```

---

## 수동 스모크 테스트 (인증 셋업 후, 사용자와 함께)

자동화하지 않는다. 실제 API가 필요하다. **내가 소유한** 5~10곡짜리 테스트 플레이리스트로 진행한다.

- [ ] `python3 check_auth.py` → Spotify/YT 모두 OK, Premium 확인
- [ ] `--dry-run` 실행 → 매칭 점수가 합리적인지 확인, **state 파일이 생기지 않았는지 확인**
- [ ] `--dry-run` 없이 실행 → YT Music에 비공개 플레이리스트 생성 및 곡 추가 확인
- [ ] 같은 명령 재실행 → `변경 없음 — 이미 모두 동기화되어 있습니다.` 확인
- [ ] Spotify에 1곡 추가 후 재실행 → 그 곡만 추가되는지 확인
- [ ] YT에서 플레이리스트를 삭제하고 재실행 → 중단되고 사유가 안내되는지 확인
- [ ] 리포트 파일을 열어 요약 표와 미매칭 목록 렌더링 확인
