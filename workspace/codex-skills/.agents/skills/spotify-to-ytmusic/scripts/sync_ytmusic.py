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
        "truncated": bool(playlist_data.get("truncated")),
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
        print(f"\n총 {len(playlists)}개 중 {done}개 완료, {failures}개 실패", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
