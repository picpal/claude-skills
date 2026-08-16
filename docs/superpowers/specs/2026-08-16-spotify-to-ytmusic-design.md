# spotify-to-ytmusic 스킬 설계

작성일: 2026-08-16

## 목적

Spotify 플레이리스트를 YouTube Music에 동일한 구성으로 복제한다. 반복 실행 시 새로 추가된 곡만 증분 동기화한다.

## 결정 사항 요약

| 항목 | 결정 | 이유 |
|---|---|---|
| 접근 방식 | API 기반 (spotipy + ytmusicapi) | 브라우저 자동화 대비 빠르고 안정적. 매칭 결과를 데이터로 다룰 수 있어 리포트·재시도가 가능 |
| 매칭 실패 처리 | 자동 추가 + 미매칭 리포트 | 중단 없이 완주. 사용자는 사후에 리포트만 확인 |
| 재실행 동작 | 증분 동기화 (새 곡만 추가) | 중복 없음. 기 매칭 곡은 재검색하지 않아 2회차부터 빠름 |
| 입력 범위 | 플레이리스트 URL/이름 지정 + `--all` 전체 일괄 | 구현 추가비용이 작고 활용도가 큼 |

의도적으로 채택하지 않은 것:
- **완전 미러링(Spotify 삭제분을 YT에서도 제거)** — 수동으로 YT에 더해둔 곡까지 지울 위험이 있어 제외
- **Liked Songs 복제** — 곡 수가 수천 개면 검색 호출이 과도해짐. 필요해지면 별도 옵션으로 추가
- **애매한 건마다 사용자 확인** — 100곡 플레이리스트에서 확인 요청이 10회 이상 발생해 흐름이 끊김

## 아키텍처

```
fetch_spotify.py  →  tracks.json  →  sync_ytmusic.py  →  YT 플레이리스트 + 리포트
                                          ↕
                                     match.py (순수 함수)
                                     state/<playlist_id>.json
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
    ├── sync_ytmusic.py
    └── test_match.py
```

### 모듈 책임

| 모듈 | 책임 | 의존성 |
|---|---|---|
| `check_auth.py` | 양쪽 인증 상태 점검. 미설정 시 셋업 절차를 출력하고 비정상 종료 | spotipy, ytmusicapi |
| `fetch_spotify.py` | 플레이리스트 메타 + 트랙 목록 추출 → JSON 출력. `--all` 시 내 플레이리스트 전체 순회 | spotipy |
| `match.py` | 후보 리스트 → 점수 계산 및 최적 후보 선정. **네트워크 접근 없음** | 표준 라이브러리만 |
| `sync_ytmusic.py` | YT 검색 → `match` 호출 → 플레이리스트 생성/증분 추가 → state 갱신 → 리포트 작성 | ytmusicapi |
| `test_match.py` | `match.py` 케이스 테이블 테스트 | pytest |

`match.py`를 분리하는 이유: 매칭 품질이 이 스킬의 핵심 가치인데 API 호출에 묶여 있으면 튜닝할 때마다 실제 네트워크 호출이 필요해진다. 순수 함수로 떼어내면 케이스 테이블로 회귀 테스트가 가능하다.

## 데이터 계약

### fetch_spotify.py 출력 (tracks.json)

```json
{
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M",
  "playlist_name": "Today's Top Hits",
  "playlist_description": "...",
  "tracks": [
    {
      "id": "spotify_track_id",
      "title": "Song Title",
      "artists": ["Primary Artist", "Featured Artist"],
      "album": "Album Name",
      "duration_ms": 213000,
      "isrc": "USUM71900001"
    }
  ]
}
```

로컬 파일·삭제된 트랙 등 `track` 객체가 null이거나 id가 없는 항목은 건너뛰고, 건너뛴 개수를 stderr에 보고한다.

### 입력 지정 방식

- **URL 또는 ID**: `https://open.spotify.com/playlist/<id>` 에서 id를 추출하거나, id를 직접 받는다
- **이름**: 내 플레이리스트 목록을 순회해 대소문자 무시 정확 일치를 먼저 찾고, 없으면 부분 일치를 찾는다. 부분 일치가 2개 이상이면 후보 목록을 출력하고 중단한다 (임의 선택하지 않음)
- **`--all`**: 내 플레이리스트 전체를 순회한다. 플레이리스트마다 독립적인 state 파일과 독립적인 리포트를 생성하고, 하나가 실패해도 다음 플레이리스트로 진행한다. 마지막에 전체 요약을 출력한다

### state 파일

경로: `~/.claude/spotify-to-ytmusic/state/<spotify_playlist_id>.json`

```json
{
  "spotify_playlist_id": "37i9...",
  "spotify_playlist_name": "Today's Top Hits",
  "yt_playlist_id": "PLxxx",
  "matched": {
    "<spotify_track_id>": { "video_id": "dQw4...", "score": 0.92, "yt_title": "..." }
  },
  "unmatched": [
    { "track_id": "...", "title": "...", "artists": ["..."], "best_candidate": "...", "score": 0.61 }
  ],
  "last_sync": "2026-08-16T14:30:00+09:00"
}
```

state 파일은 **각 곡 처리 직후가 아니라 N곡(기본 10곡)마다 그리고 종료 시** 저장한다. 중간에 중단되어도 마지막 저장 지점부터 이어서 진행할 수 있다.

## 매칭 로직

Spotify 트랙 하나당 `ytmusic.search(query, filter="songs", limit=5)`로 후보를 얻고 각 후보에 점수를 부여한다.

검색 쿼리: `"{title} {primary_artist}"`

### 정규화

비교 전 제목에 다음을 적용한다.

1. 소문자 변환
2. 괄호/대괄호 안의 부가 표기 제거: `feat.`, `ft.`, `with`, `remaster(ed)`, `deluxe`, `explicit`, `bonus track`, `single version`, `radio edit`
3. ` - Remastered 2011` 형태의 하이픈 접미사 제거
4. 특수문자 제거 후 연속 공백 정리

원본 제목은 리포트 출력을 위해 유지한다.

### 점수 계산

| 신호 | 가중치 | 방식 |
|---|---|---|
| 제목 유사도 | 0.5 | 정규화된 제목끼리 `difflib.SequenceMatcher` ratio |
| 아티스트 일치 | 0.3 | 주 아티스트(정규화)가 후보 아티스트 문자열에 포함되면 1.0, 아니면 두 아티스트 문자열의 ratio |
| 재생시간 차 | 0.2 | ≤3초 → 1.0, ≤10초 → 0.5, 초과 → 0.0. 후보에 duration 정보가 없으면 0.5 (중립) |

총점 = 세 항목의 가중합 (0.0 ~ 1.0)

### 채택 기준

- **≥ 0.75** → 자동 추가
- **< 0.75** → 건너뛰고 `unmatched`에 기록. 이때 1위 후보와 점수를 함께 남겨 사용자가 "이게 맞았을 수도" 판단할 수 있게 한다
- 임계값은 `--threshold` 옵션으로 조정 가능하며, 기본값 0.75는 SKILL.md에 명시한다

## 증분 동기화 흐름

1. state 파일 로드 (없으면 신규)
2. `yt_playlist_id`가 없으면 `create_playlist(name, description, privacy_status="PRIVATE")` 호출 후 저장
3. Spotify 트랙 중 `matched`에 키가 없는 것만 대상으로 선정
4. 대상이 없으면 "변경 없음" 출력 후 종료
5. 각 대상 트랙에 대해 검색 → 매칭 → `add_playlist_items(yt_playlist_id, [video_id], duplicates=False)`
6. 리포트 작성

플레이리스트 생성은 비공개(PRIVATE)를 기본으로 한다. `--public` 옵션으로 변경 가능.

## 리포트

경로: `~/.claude/spotify-to-ytmusic/reports/<playlist_name>-<YYYYMMDD-HHMM>.md`

포함 내용:
- 요약: 전체 곡 수 / 신규 처리 / 매칭 성공 / 미매칭 / 이미 동기화됨
- 미매칭 목록 표: 원곡 제목·아티스트, 최고 후보, 점수 — 수동으로 찾아 넣을 수 있게
- 낮은 신뢰도로 추가된 곡 목록 (0.75 ~ 0.85 구간): 잘못 매칭됐을 수 있으니 확인 권장
- YT 플레이리스트 링크

## 에러 처리

| 상황 | 처리 |
|---|---|
| 인증 미설정 | `check_auth.py`가 셋업 절차를 출력하고 exit 1. 동기화는 시작하지 않음 |
| Spotify 플레이리스트 없음 / 접근 불가 | 명확한 메시지 출력 후 중단 |
| YT 검색 실패 / rate limit | 지수 백오프(1초 → 2초 → 4초) 3회 재시도. 그래도 실패하면 `unmatched`에 사유와 함께 기록하고 **다음 곡으로 진행** |
| YT 곡 추가 실패 | 동일하게 재시도 후 실패 시 기록하고 계속 |
| 요청 간격 | 곡당 기본 0.3초 딜레이. ytmusicapi는 비공식 API라 과도한 요청 시 차단될 수 있다 |
| 중간 중단(Ctrl-C 등) | state를 저장하고 종료. 재실행 시 이어서 진행 |

에러로 인해 전체 실행이 중단되는 경우는 인증 실패와 플레이리스트 접근 실패 두 가지뿐이다. 개별 곡의 문제는 전체를 멈추지 않는다.

## 인증 셋업 (사용자 1회 수동 작업)

### Spotify

1. developer.spotify.com/dashboard 에서 앱 생성
2. Redirect URI를 `http://127.0.0.1:8888/callback`으로 등록
3. 환경변수 설정:
   ```bash
   export SPOTIPY_CLIENT_ID="..."
   export SPOTIPY_CLIENT_SECRET="..."
   export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
   ```
4. 최초 실행 시 브라우저 인증 → 토큰 캐시 생성

필요 스코프: `playlist-read-private`, `playlist-read-collaborative`

### YouTube Music

`ytmusicapi browser` 명령으로 설정한다. music.youtube.com에 로그인한 브라우저의 개발자 도구에서 인증된 POST 요청의 request header를 복사해 붙여넣으면 `browser.json`이 생성된다.

OAuth 방식 대신 browser 헤더 방식을 택한 이유: OAuth는 Google Cloud 프로젝트 생성과 OAuth 클라이언트 등록이 필요해 진입 장벽이 높다. browser 방식은 이미 로그인된 세션의 헤더를 복사하는 것으로 끝난다. 단점은 세션 만료 시 재설정이 필요하다는 점이며, `check_auth.py`가 만료를 감지해 재설정 안내를 출력한다.

저장 위치: `~/.claude/spotify-to-ytmusic/browser.json`

## 테스트 전략

### 단위 테스트 (`test_match.py`)

`match.py`는 네트워크 의존이 없으므로 케이스 테이블로 검증한다. 최소 커버 케이스:

| 케이스 | 기대 결과 |
|---|---|
| 완전 일치 | 점수 ≥ 0.95 |
| 리마스터 표기 차이 (`Song - Remastered 2011` vs `Song`) | 임계값 통과 |
| feat. 표기 위치 차이 (`Song (feat. B)` vs `Song`, 아티스트 A 동일) | 임계값 통과 |
| 다른 아티스트의 커버곡 (제목 동일, 아티스트 다름) | 임계값 미달 |
| 라이브 버전 (제목 유사, 재생시간 60초 차) | 임계값 미달 |
| 한글 아티스트명 | 임계값 통과 |
| 후보 목록이 비어 있음 | None 반환, 예외 없음 |
| 후보에 duration 정보 없음 | 중립 점수 적용, 예외 없음 |

### 통합 검증

실제 API 의존이므로 자동화하지 않는다. 5~10곡짜리 테스트 플레이리스트로 수동 스모크 테스트:

1. 최초 실행 → 플레이리스트 생성 확인
2. 재실행 → "변경 없음" 출력 확인
3. Spotify에 1곡 추가 후 재실행 → 해당 곡만 추가되는지 확인

## SKILL.md 요건

- frontmatter `description`은 **single-line 문자열** (README에 명시된 제약)
- 트리거 표현: "스포티파이 플레이리스트 유튜브 뮤직으로", "플레이리스트 옮겨줘", "spotify to ytmusic", "플레이리스트 복제", "플레이리스트 이전"
- 인증 셋업 절차를 단계별로 포함
- 매칭 임계값 기본값과 조정 방법 명시
- 미매칭 리포트를 사용자에게 요약해서 보고하라는 지시 포함

## 완료 후 작업

- README.md 스킬 목록 표와 디렉토리 구조에 `spotify-to-ytmusic` 추가
- `~/.claude/skills/spotify-to-ytmusic` 심볼릭 링크 안내
