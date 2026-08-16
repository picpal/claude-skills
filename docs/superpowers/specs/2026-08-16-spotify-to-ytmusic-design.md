# spotify-to-ytmusic 스킬 설계

작성일: 2026-08-16
개정일: 2026-08-16 (2차: Spotify 읽기를 Web API → embed 페이지 파싱으로 교체. Premium·소유권·인증 요건 소멸)

## 목적

공유받은 Spotify 플레이리스트를 YouTube Music에 동일한 구성으로 복제한다. 반복 실행 시 새로 추가된 곡만 증분 동기화한다.

Spotify 계정도 Premium도 필요 없다. 공개(또는 링크 공유) 플레이리스트의 embed 페이지에 트랙 목록 JSON이 들어 있어 그것만 파싱한다.

## 결정 사항 요약

| 항목 | 결정 | 이유 |
|---|---|---|
| Spotify 읽기 | **embed 페이지(`/embed/playlist/<id>`)의 `__NEXT_DATA__` JSON 파싱** | 인증·Premium·소유권·브라우저가 모두 불필요. 순수 HTTP + JSON |
| YouTube Music 쓰기 | ytmusicapi (browser 헤더 인증) | 공식 API는 플레이리스트 조작 쿼터가 비현실적 |
| 매칭 실패 처리 | 자동 추가 + 미매칭 리포트 | 중단 없이 완주. 사용자는 사후에 리포트만 확인 |
| 재실행 동작 | 증분 동기화 (새 곡만 추가) | 중복 없음. 기 매칭 곡은 재검색하지 않아 2회차부터 빠름 |
| 입력 | 플레이리스트 URL/ID (여러 개 가능) | 공유 링크를 그대로 붙여넣으면 된다 |

의도적으로 채택하지 않은 것:
- **Spotify Web API** — 2026년 2월 개편으로 플레이리스트 내용은 소유자/협업자만 조회 가능하고, Development Mode 앱은 소유자의 Premium 구독이 필요하다. 공유받은 플레이리스트를 다루는 이 스킬의 목적과 맞지 않는다
- **브라우저 자동화** — embed 파싱으로 같은 데이터를 얻을 수 있어 불필요하다. 가상 스크롤·DOM 변경 취약성만 떠안게 된다
- **완전 미러링(Spotify 삭제분을 YT에서도 제거)** — 수동으로 YT에 더해둔 곡까지 지울 위험이 있어 제외
- **애매한 건마다 사용자 확인** — 100곡 플레이리스트에서 확인 요청이 10회 이상 발생해 흐름이 끊김
- **ISRC 기반 매칭** — embed 데이터에 ISRC가 없고, YouTube Music 검색도 ISRC 조회를 지원하지 않는다

## Spotify 읽기: embed 페이지 파싱

`https://open.spotify.com/embed/playlist/<id>` 를 평범한 GET으로 받으면 HTML 안에
`<script id="__NEXT_DATA__" type="application/json">` 이 있고, 그 안에 `trackList` 배열이 들어 있다.

실측(2026-08-16, 54곡 공유 플레이리스트) 기준 항목 형태:

```json
{
  "uri": "spotify:track:64LDTMmwjwpI416zpQbIRt",
  "title": "Flowerpot (Bonus Track)",
  "subtitle": "Alex",
  "duration": 265653,
  "isPlayable": true,
  "entityType": "track"
}
```

| embed 필드 | 우리 필드 | 비고 |
|---|---|---|
| `uri` | `id` | `spotify:track:` 접두사를 떼어 track ID로 쓴다. state 키가 된다 |
| `title` | `title` | 그대로 |
| `subtitle` | `artists` | 쉼표로 분리. 첫 번째가 주 아티스트 |
| `duration` | `duration_ms` | **이미 밀리초**. 변환 불필요 |

플레이리스트 이름은 같은 JSON의 `name` 필드에서 얻는다.

### 100곡 상한

**embed는 최대 100곡까지만 반환한다.** 실측으로 확인했다 — 100곡을 넘는 Rock Classics와 All Out 80s가 둘 다 정확히 100개를 반환했다.

정확히 100곡이 나오면 잘렸을 가능성이 있으므로 **경고를 출력한다.** 100곡 초과 플레이리스트를 다뤄야 하면 별도 수집 경로(브라우저 자동화 등)가 필요하며, 그건 이 스펙의 범위 밖이다.

### 취약성

비공개 인터페이스이므로 Spotify가 embed 페이지 구조를 바꾸면 깨진다. 대응:

- `__NEXT_DATA__`를 못 찾거나 `trackList`가 없으면 **명확한 사유와 함께 중단한다.** 빈 목록으로 조용히 성공하면 안 된다
- 파싱은 순수 함수로 분리해 저장된 픽스처로 테스트한다. 구조가 바뀌면 픽스처를 갱신해 고친다

## 아키텍처

```
fetch_spotify.py  →  tracks.json  →  sync_ytmusic.py  →  YT 플레이리스트 + 리포트
                                          ↕
                                     match.py (점수 계산)
                                     state.py / report.py
```

### 디렉토리 구조

```
spotify-to-ytmusic/
├── SKILL.md
├── requirements.txt
└── scripts/
    ├── check_auth.py
    ├── fetch_spotify.py
    ├── match.py
    ├── report.py
    ├── state.py
    ├── sync_ytmusic.py
    ├── test_fetch_spotify.py
    ├── test_match.py
    ├── test_report.py
    ├── test_state.py
    └── test_sync_ytmusic.py
```

### 모듈 책임

| 모듈 | 책임 | 서드파티 의존 |
|---|---|---|
| `match.py` | 제목/아티스트 정규화, 후보 점수 계산, 최적 후보 선정 | 없음 |
| `state.py` | 데이터 홈 경로 결정, state JSON 원자적 로드/저장 | 없음 |
| `report.py` | 실행 결과 → 마크다운 리포트 생성 및 저장 | 없음 |
| `fetch_spotify.py` | URL에서 ID 추출, embed 페이지 취득, `__NEXT_DATA__` 파싱 | **없음** (urllib) |
| `sync_ytmusic.py` | YT 검색·쓰기, 응답 검증, 매칭 호출, 전체 흐름 조율 | ytmusicapi |
| `check_auth.py` | YT 인증 실동작 점검 + Spotify embed 도달 확인 | ytmusicapi |

Spotify 쪽 서드파티 의존이 사라져 `fetch_spotify.py`도 표준 라이브러리만 쓴다. 덕분에 HTTP 취득 함수 하나만 빼면 전부 단위 테스트가 가능하다.

## 데이터 계약

### fetch_spotify.py 출력 (tracks.json)

```json
{
  "playlist_id": "46WRCRFym2ofhc5l72Tf6B",
  "playlist_name": "밍밍 茶차2",
  "playlist_description": "",
  "tracks": [
    {
      "id": "64LDTMmwjwpI416zpQbIRt",
      "title": "Flowerpot (Bonus Track)",
      "artists": ["Alex"],
      "duration_ms": 265653
    }
  ]
}
```

`uri`가 `spotify:track:`으로 시작하지 않는 항목(에피소드 등)이나 `title`이 없는 항목은 건너뛰고, 건너뛴 개수를 stderr에 보고한다.

### 입력 지정 방식

- **URL**: 공유 링크를 그대로 받는다. `?si=...&utm_source=...` 같은 쿼리스트링이 붙어 있어도 ID만 뽑아낸다
- **ID**: 22자 base62 ID를 직접 받는다
- **여러 개**: URL을 여러 개 나열하면 순서대로 처리한다. 플레이리스트마다 독립적인 state 파일과 리포트를 만들고, 하나가 실패해도 다음으로 진행하되 **하나라도 실패했으면 종료 코드 1을 반환한다**

이름으로 검색하는 기능은 없다. 내 라이브러리에 접근하지 않기 때문이다.

### state 파일

경로: `~/.claude/spotify-to-ytmusic/state/<spotify_playlist_id>.json`

```json
{
  "spotify_playlist_id": "46WRCRFym2ofhc5l72Tf6B",
  "spotify_playlist_name": "밍밍 茶차2",
  "yt_playlist_id": "PLxxx",
  "matched": {
    "<spotify_track_id>": { "video_id": "dQw4...", "score": 0.92, "yt_title": "..." }
  },
  "unmatched": [
    { "track_id": "...", "title": "...", "artists": ["..."], "best_candidate": "...", "score": 0.61, "reason": "임계값 미달" }
  ],
  "last_sync": "2026-08-16T14:30:00+09:00"
}
```

**저장 규칙:**

- 각 곡 처리 직후가 아니라 **10곡마다, 그리고 종료 시** 저장한다. 종료 저장은 `try/finally`에 두어 `KeyboardInterrupt`로 중단되어도 실행된다
- 쓰기는 **원자적**이어야 한다. 임시 파일에 쓰고 `os.replace()`로 교체한다
- **깨진 state 파일을 만나면 조용히 새 state를 만들지 않고 예외를 던지고 중단한다.** 새 state로 넘어가면 `yt_playlist_id`를 잃어 다음 실행이 **중복 플레이리스트를 생성한다.** 사용자가 파일을 확인하고 지울지 판단해야 한다
- `unmatched`는 누적하지 않고 이번 실행 결과로 덮어쓴다. 지난번 미매칭 곡은 `matched`에 없으므로 어차피 다음 실행에서 다시 시도된다

## 매칭 로직

Spotify 트랙 하나당 `ytmusic.search(query, filter="songs", limit=5)`로 후보를 얻고 각 후보에 점수를 부여한다.

검색 쿼리: `"{title} {primary_artist}"`

### 정규화

비교 전 제목에 다음을 순서대로 적용한다.

1. 소문자 변환
2. 아포스트로피 계열(`'`, `’`, `` ` ``) **삭제** — `don't`와 `dont`가 같은 문자열이 되어야 한다
3. 괄호/대괄호 안의 부가 표기 제거: `feat.`, `ft.`, `with`, `remaster(ed)`, `deluxe`, `explicit`, `bonus track`, `single version`, `radio edit`
4. ` - Remastered 2011` 형태의 하이픈 접미사 제거
5. 나머지 문장부호를 **공백으로 치환** — `AC/DC`는 `ac dc`가 된다. 구분자이므로 삭제가 아니라 공백이 맞다
6. 연속 공백 정리

2단계와 5단계를 구분하는 것이 중요하다. 전부 공백으로 치환하면 `don't` → `don t`가 되어 `dont`와 매칭되지 않는다.

`live`, `remix`, `cover` 같은 버전 표기는 **제거하지 않는다.** 다른 곡으로 취급해야 하기 때문이며, 아래 버전 페널티가 이를 처리한다.

### 점수 계산

| 신호 | 가중치 | 방식 |
|---|---|---|
| 제목 유사도 | 0.5 | 정규화된 제목끼리 `difflib.SequenceMatcher` ratio |
| 아티스트 일치 | 0.3 | 주 아티스트(정규화)의 토큰 집합이 후보 아티스트의 토큰 집합에 포함되면 1.0, 아니면 후보들과의 최대 ratio |
| 재생시간 차 | 0.2 | ≤3초 → 1.0, ≤10초 → 0.5, 초과 → 0.0. 후보에 duration 정보가 없으면 0.5 (중립) |

총점 = 세 항목의 가중합 − 버전 페널티

아티스트 비교에 부분 문자열이 아니라 토큰 집합을 쓰는 이유: `IU`가 `Ruin`에 부분 문자열로 걸리는 오탐을 막기 위해서다.

### 버전 페널티

후보 제목에는 있고 원곡 제목에는 없는 버전 표기가 하나라도 있으면 **0.25를 감점**한다.

표기 목록: `live`, `remix`, `cover`, `karaoke`, `instrumental`, `acoustic`, `nightcore`, `sped`, `slowed`, `remake`

양쪽 모두에 있으면 감점하지 않는다. 원곡이 라이브 버전이면 라이브 후보와 매칭되는 것이 맞다.

이 페널티가 없으면 재생시간이 우연히 비슷한 라이브 버전이 0.83점으로 통과한다. 재생시간 신호만으로는 막을 수 없다.

### 채택 기준

두 조건을 **모두** 만족해야 채택한다.

1. **아티스트 게이트**: `artist_score >= 0.5`
2. **임계값**: `total >= threshold` (기본 0.75)

아티스트 게이트는 임계값과 독립이다. 총점 상한(cap)으로 처리하면 사용자가 `--threshold`를 낮췄을 때 게이트가 무력화된다. 커버곡은 제목·재생시간이 원곡과 거의 같아 총점 0.81까지 나오므로, 임계값 조정으로 열려서는 안 된다.

임계값 미달 시 건너뛰고 `unmatched`에 기록한다. 이때 게이트와 무관한 최고점 후보를 함께 남겨 사용자가 "이게 맞았을 수도" 판단할 수 있게 한다.

임계값은 `--threshold` 옵션으로 조정 가능하며 기본값 0.75는 SKILL.md에 명시한다.

## 동기화 흐름

1. state 파일 로드 (없으면 신규, 깨졌으면 중단)
2. `yt_playlist_id`가 있으면 **실제로 존재하는지 확인한다.** 삭제됐거나 다른 계정의 것이면 사유를 알리고 중단한다. 이 확인이 없으면 플레이리스트가 사라진 뒤에도 "변경 없음"이라는 거짓 성공을 보고한다
3. `yt_playlist_id`가 없으면 `create_playlist(...)` 호출. **반환값이 문자열 ID인지 검증한다** — 실패 시 에러 dict를 반환하므로 그대로 저장하면 안 된다
4. Spotify 트랙 중 `matched`에 키가 없는 것만 대상으로 선정
5. 대상이 없으면 "변경 없음" 출력 후 종료
6. 각 대상 트랙: 검색 → 매칭 → `add_playlist_items(...)` → **응답의 `status`가 성공인지 검증**
7. 리포트 작성

플레이리스트 생성은 비공개(PRIVATE) 기본. `--public`으로 변경 가능.

### YouTube Music 쓰기 응답 처리

ytmusicapi는 실패를 예외가 아니라 반환값으로 알리는 경우가 있다. 반환값을 버리면 실패한 곡이 성공으로 기록된다.

| 호출 | 성공 | 실패 | 처리 |
|---|---|---|---|
| `create_playlist` | 플레이리스트 ID 문자열 | 응답 dict | 문자열이 아니면 예외로 전환 |
| `add_playlist_items` | `{"status": "STATUS_SUCCEEDED", ...}` | 상태가 다른 dict | 성공 상태가 아니면 실패로 처리 |

`duplicates=False`는 "중복이면 조용히 건너뛴다"가 아니라 **"중복이 있으면 에러를 반환하고 아무것도 추가하지 않는다"** 이다. 한 번에 한 곡씩 추가하므로 이 에러는 "그 곡이 이미 플레이리스트에 있다"는 뜻이 명확하다. 따라서 **실패가 아니라 "이미 존재함"으로 간주해 `matched`에 기록한다.** 사용자가 수동으로 넣어둔 곡을 매번 미매칭으로 보고하지 않기 위해서다.

### `--dry-run`

매칭 결과만 출력하고 **state를 저장하지 않는다.** 저장하면 `matched`가 채워져 다음 실제 실행이 "변경 없음"으로 끝나고 플레이리스트를 만들지 않는다. dry-run이 실제 실행을 망가뜨려서는 안 된다.

## 리포트

경로: `~/.claude/spotify-to-ytmusic/reports/<playlist_name>-<YYYYMMDD-HHMMSS>.md`

초 단위까지 쓴다. 분 단위면 여러 플레이리스트를 연속 처리할 때 같은 파일을 덮어쓸 수 있다.

포함 내용:
- 요약: 전체 곡 수 / 이미 동기화됨 / 이번 처리 / 매칭 성공 / 미매칭
- 미매칭 목록 표: 원곡 제목·아티스트, 최고 후보, 점수, 사유
- 낮은 신뢰도로 추가된 곡 (0.75 ~ 0.85): 확인 권장
- YT 플레이리스트 링크

표 셀에 들어가는 값은 파이프(`|`)와 개행을 이스케이프한다.

## 에러 처리

| 상황 | 처리 |
|---|---|
| embed 페이지 취득 실패(네트워크·404) | 사유를 명시하고 중단 |
| `__NEXT_DATA__`/`trackList` 없음 | "Spotify가 페이지 구조를 변경했을 수 있다"는 사유와 함께 중단. 빈 목록으로 조용히 성공하지 않는다 |
| 트랙 100개 정확히 반환 | 잘렸을 수 있다는 **경고** 출력 후 계속 진행 |
| YT 인증 미설정/무효 | `check_auth.py`가 셋업 절차를 출력하고 exit 1. 동기화를 시작하지 않음 |
| state 파일 손상 | 예외를 던지고 중단. 새 state로 조용히 넘어가지 않음 (중복 플레이리스트 방지) |
| YT 플레이리스트 소실 | 사유를 알리고 중단 |
| YT 검색/쓰기 실패 | 재시도 후 실패하면 `unmatched`에 사유와 함께 기록하고 **다음 곡으로 진행** |
| 재시도 | 최대 3회 시도(= 2회 재시도), 대기 1초 → 2초. 인증·검증 오류는 재시도하지 않음 |
| 요청 간격 | 곡당 기본 0.3초. **성공·실패 경로 모두에서 적용한다** — 실패 시 건너뛰면 레이트리밋 상황에서 딜레이 없이 연타하게 된다. 매칭된 곡은 검색+추가로 요청이 2회임을 문서에 명시 |
| 중간 중단(Ctrl-C) | `try/finally`로 state를 저장하고 종료. 재실행 시 이어서 진행 |
| 여러 플레이리스트 중 개별 실패 | 리포트 생성까지 포함해 플레이리스트 단위로 격리. 하나 실패해도 계속하되 종료 코드 1 |

전체 실행이 중단되는 경우는 Spotify 파싱 실패, YT 인증 실패, state 손상, YT 플레이리스트 소실 네 가지다. 개별 곡의 문제는 전체를 멈추지 않는다.

## 인증 셋업 (사용자 1회 수동 작업)

Spotify 쪽은 아무 설정도 필요 없다. YouTube Music만 설정한다.

`ytmusicapi browser --file ~/.claude/spotify-to-ytmusic/browser.json` 으로 설정한다. music.youtube.com에 로그인한 브라우저의 개발자 도구에서 인증된 POST 요청의 request header를 복사해 붙여넣는다.

OAuth 방식 대신 browser 헤더 방식을 택한 이유는 Google Cloud 프로젝트 생성과 OAuth 클라이언트 등록이 필요 없어 진입 장벽이 낮기 때문이다. 단점은 세션 만료 시 재설정이 필요하다는 것과, ytmusicapi가 browser 방식을 유지보수 부담이 큰 경로로 보고 OAuth를 권장한다는 점이다. 세션 만료는 `check_auth.py`가 실제 호출로 감지해 재설정을 안내한다.

YouTube Premium은 필요 없다. 플레이리스트 생성·수정은 무료 계정에서도 동작한다.

## 테스트 전략

### 순수 로직 단위 테스트

`match.py`, `state.py`, `report.py`, `fetch_spotify.py`의 파싱 함수, `sync_ytmusic.py`의 응답 검증 함수는 네트워크 의존이 없으므로 케이스 테이블로 검증한다.

`fetch_spotify.parse_embed` 최소 커버 케이스:

| 케이스 | 기대 결과 |
|---|---|
| 정상 trackList | 실측 필드가 우리 스키마로 매핑됨 |
| `subtitle`에 아티스트 여러 명 | 쉼표로 분리 |
| `uri`가 track이 아님 (에피소드) | 건너뛰고 skipped 증가 |
| `title` 없음 | 건너뛰고 skipped 증가 |
| `__NEXT_DATA__` 없음 | 예외 |
| `trackList` 없음 | 예외 |
| 트랙 100개 | 잘림 경고 플래그 |

`match.py` 최소 커버 케이스:

| 케이스 | 기대 결과 |
|---|---|
| 완전 일치 | 총점 ≥ 0.95 |
| 리마스터 표기 차이 | 임계값 통과 |
| feat. 표기 위치 차이 | 임계값 통과 |
| 아포스트로피 차이 (`Don't` vs `Dont`) | 정규화 결과 동일 |
| 다른 아티스트의 커버곡 | 아티스트 게이트에서 탈락. `--threshold`를 0.1로 낮춰도 탈락 |
| 짧은 아티스트명 오탐 (`IU` vs `Ruin`) | 게이트 탈락 |
| 라이브 버전 (재생시간 60초 차) | 임계값 미달 |
| 라이브 버전 (재생시간 동일) | 버전 페널티로 임계값 미달 |
| 원곡도 라이브인 경우 | 페널티 없이 통과 |
| 한글 아티스트명 | 통과 |
| 후보 없음 | None 반환, 예외 없음 |
| 후보에 duration 없음 | 중립 점수, 예외 없음 |

### 동기화 흐름 테스트 (fake 클라이언트)

`sync_playlist`는 이 스킬에서 가장 상태가 복잡한 함수인데 API에 묶여 있다는 이유로 검증을 생략하면, 단위 테스트가 전부 통과해도 dry-run 오염·중복 생성·재시도 같은 실패가 그대로 남는다. ytmusicapi 인터페이스를 흉내내는 fake 클라이언트를 만들어 검증한다.

| 시나리오 | 검증 내용 |
|---|---|
| 신규 동기화 | 플레이리스트 생성 1회, 매칭된 곡만 추가, state 기록 |
| 재실행 | 추가·검색 호출 0회, "변경 없음" |
| 곡 1개 추가 후 재실행 | 그 곡만 검색·추가 |
| `--dry-run` | state 파일이 생기지 않음, 쓰기 호출 0회 |
| 검색 예외 | 재시도 후 unmatched 기록, 다음 곡 진행 |
| 실패 경로의 딜레이 | 실패해도 `sleep(delay)`가 호출됨 |
| 추가 응답이 실패 상태 | unmatched 기록, matched에 들어가지 않음 |
| 중복 에러 응답 | "이미 존재함"으로 matched 기록 |
| `create_playlist`가 dict 반환 | 예외로 전환, state에 dict가 저장되지 않음 |
| YT 플레이리스트 소실 | 예외 |
| 처리 중 `KeyboardInterrupt` | state가 저장된 상태로 종료 |

### 통합 검증

실제 네트워크가 필요한 것은 두 가지뿐이다.

1. `fetch_spotify.py`로 실제 공유 URL을 받아 곡 수와 필드가 맞는지 확인 (인증 불필요하므로 언제든 실행 가능)
2. YT 동기화 스모크 테스트 — 인증 설정 후 수동으로 진행

## SKILL.md 요건

- frontmatter `description`은 **single-line 문자열** (README에 명시된 제약)
- 트리거 표현: "스포티파이 플레이리스트 유튜브 뮤직으로", "플레이리스트 옮겨줘", "spotify to ytmusic", "플레이리스트 복제", "플레이리스트 이전"
- **Spotify 인증이 필요 없다는 점**과 **100곡 상한**을 명시
- YT 인증 셋업 절차를 단계별로 포함
- 매칭 임계값 기본값과 조정 방법 명시. **아티스트 게이트는 임계값을 낮춰도 유지된다는 점을 함께 적는다**
- 미매칭 리포트를 사용자에게 한국어로 요약해 보고하라는 지시 포함

## 완료 후 작업

- README.md 스킬 목록 표와 디렉토리 구조에 `spotify-to-ytmusic` 추가
- `~/.claude/skills/spotify-to-ytmusic` 심볼릭 링크 안내
