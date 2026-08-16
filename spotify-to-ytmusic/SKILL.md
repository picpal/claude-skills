---
name: spotify-to-ytmusic
description: "공유받은 Spotify 플레이리스트를 YouTube Music에 동일한 구성으로 복제하는 스킬. Spotify embed 페이지를 파싱해 곡 목록을 얻고(인증·Premium 불필요) ytmusicapi로 검색·매칭해 YT Music 플레이리스트를 만들며, 재실행 시 새로 추가된 곡만 증분 동기화한다. 사용자가 '스포티파이 플레이리스트 유튜브 뮤직으로', '플레이리스트 옮겨줘', '플레이리스트 복제', '플레이리스트 이전', 'spotify to ytmusic', '스포티파이에서 유튜브뮤직으로', '플레이리스트 동기화', '음악 목록 옮기기' 등을 언급하거나 Spotify 플레이리스트 링크를 주며 옮겨달라고 하면 이 스킬을 사용한다."
---

# Spotify → YouTube Music 플레이리스트 복제

공유받은 Spotify 플레이리스트를 YouTube Music에 같은 구성으로 만든다. 다시 실행하면 새로 추가된 곡만 붙인다.

## 전제 조건

| 항목 | 필요 여부 |
|---|---|
| Spotify 계정 / Premium | **불필요** |
| Spotify 플레이리스트 소유권 | **불필요** (공유 링크만 있으면 된다) |
| YouTube Music 계정 | 필요 (인증 1회 설정) |
| YouTube Premium | **불필요** |

**단, embed는 최대 100곡까지만 제공한다.** 100곡이 나오면 잘렸을 수 있다는 경고가 출력되며, 리포트에도 기록된다.

## 동작 방식

```
fetch_spotify.py  →  tracks.json  →  sync_ytmusic.py  →  YT 플레이리스트 + 리포트
                                          ↕
                                     match.py (점수 계산)
                                     state/<playlist_id>.json
```

Spotify Web API를 쓰지 않는다. 2026년 2월 개편으로 플레이리스트 내용은 소유자·협업자만 조회할 수 있고 Development Mode 앱은 Premium이 필요해졌기 때문이다. 대신 `open.spotify.com/embed/playlist/<id>` 의 `__NEXT_DATA__` JSON을 파싱한다 — 여기에 제목·아티스트·재생시간(ms)·track ID가 모두 들어 있다.

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
pip3 install --break-system-packages ytmusicapi
```

Spotify 쪽은 설치할 것이 없다 (표준 라이브러리만 사용).

### YouTube Music 인증

```bash
python3 scripts/check_auth.py
```

미설정이면 셋업 절차가 그대로 출력된다. 요약하면: music.youtube.com에 로그인한 브라우저의 개발자 도구에서 `/youtubei/v1/` POST 요청의 Request Headers를 복사 → `ytmusicapi browser --file ~/.claude/spotify-to-ytmusic/browser.json` 실행 후 붙여넣기.

## 워크플로우

### 1단계: 사전 점검

`python3 scripts/check_auth.py`를 먼저 실행한다. exit code가 0이 아니면 **동기화를 시작하지 말고** 출력된 셋업 절차를 사용자에게 전달한다.

### 2단계: 곡 목록 수집

공유 링크를 그대로 넘긴다. `?si=...` 같은 쿼리스트링이 붙어 있어도 된다.

```bash
cd <스킬 디렉토리>/scripts
python3 fetch_spotify.py "https://open.spotify.com/playlist/<id>?si=..." > /tmp/tracks.json
```

수집 결과(곡 수, 건너뛴 항목, 100곡 잘림 경고)가 stderr에 나온다. **곡 수를 사용자에게 먼저 알리고 진행한다.**

여러 개를 한 번에:
```bash
python3 fetch_spotify.py "<url1>" "<url2>" > /tmp/all.json
```

### 3단계: 동기화

```bash
python3 sync_ytmusic.py --tracks /tmp/tracks.json
```

파이프로 한 번에:
```bash
python3 fetch_spotify.py "<url>" | python3 sync_ytmusic.py --tracks -
```

먼저 결과를 보고 싶으면 `--dry-run`을 붙인다. dry-run은 state를 저장하지 않으므로 이후 실제 실행에 영향을 주지 않는다.

매칭된 곡은 검색+추가로 요청이 2회다. 50곡이면 1~2분, 100곡이면 2~4분 정도로 안내한다.

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
| `--dry-run` | 꺼짐 | 매칭 결과만 보고 YT에 쓰지 않는다. **state도 저장하지 않는다** |

## 파일 위치

| 용도 | 경로 |
|---|---|
| YT 인증 | `~/.claude/spotify-to-ytmusic/browser.json` |
| 동기화 상태 | `~/.claude/spotify-to-ytmusic/state/<playlist_id>.json` |
| 리포트 | `~/.claude/spotify-to-ytmusic/reports/<이름>-<날짜시각>.md` |

`SPOTIFY_TO_YTMUSIC_HOME` 환경변수로 위치를 바꿀 수 있다.

## 주의사항

- **단방향이다.** Spotify에서 곡을 지워도 YT에서는 지워지지 않는다
- **embed는 100곡 상한이 있다.** 그 이상은 별도 수집 경로가 필요하다
- state 파일을 지우면 다음 실행에서 **새 YT 플레이리스트를 만든다.** 기존 것과 이어 붙이려면 state를 유지해야 한다
- state 파일이 손상되면 스크립트가 중단된다. 조용히 새로 시작하면 중복 플레이리스트가 생기기 때문이다
- 중간에 Ctrl-C로 끊어도 진행 상황은 저장된다. 다시 실행하면 이어서 진행한다
- YT 플레이리스트를 수동으로 삭제했다면 스크립트가 감지하고 중단한다
- embed 파싱은 비공개 인터페이스에 의존한다. Spotify가 구조를 바꾸면 `PlaylistParseError`와 함께 중단되며, `test_fetch_spotify.py`의 픽스처를 갱신해 고친다

## 테스트

순수 로직과 동기화 흐름 전체에 테스트가 있다 (96개, 네트워크 불필요):

```bash
cd <스킬 디렉토리>/scripts && python3 -m pytest -q
```

매칭 로직이나 동기화 흐름을 손봤다면 반드시 이 테스트를 돌린다.
