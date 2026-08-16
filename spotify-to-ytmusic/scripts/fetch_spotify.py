#!/usr/bin/env python3
"""Spotify 플레이리스트의 트랙 목록을 JSON으로 뽑는다.

Spotify Web API를 쓰지 않는다. 2026년 2월 개편으로 플레이리스트 내용은
소유자·협업자만 조회할 수 있고 Development Mode 앱은 Premium이 필요해졌다.
대신 embed 페이지(/embed/playlist/<id>)의 __NEXT_DATA__ JSON을 파싱한다.
인증·Premium·소유권·브라우저가 모두 불필요하다.

주의: embed는 최대 100곡까지만 반환한다.

사용법:
    python3 fetch_spotify.py "https://open.spotify.com/playlist/<id>?si=..."
    python3 fetch_spotify.py <url1> <url2> ...
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

EMBED_URL = "https://open.spotify.com/embed/playlist/{}"
EMBED_TRACK_CAP = 100
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)
_URL_RE = re.compile(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)")
_URI_RE = re.compile(r"^spotify:playlist:([A-Za-z0-9]+)$")
_RAW_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")

STRUCTURE_HINT = (
    "Spotify가 embed 페이지 구조를 변경했을 수 있습니다.\n"
    "scripts/test_fetch_spotify.py의 픽스처를 실제 응답에 맞춰 갱신해야 합니다."
)


class PlaylistFetchError(Exception):
    """embed 페이지를 가져오지 못했다."""


class PlaylistParseError(Exception):
    """embed 페이지에서 트랙 목록을 찾지 못했다."""


def extract_playlist_id(value: str) -> str | None:
    """URL/URI/생 ID에서 플레이리스트 ID를 뽑는다.

    공유 링크에 붙는 ?si=...&utm_source=... 같은 쿼리스트링은 무시한다.
    """
    if not value:
        return None
    value = value.strip()

    match = _URL_RE.search(value)
    if match:
        return match.group(1)

    match = _URI_RE.match(value)
    if match:
        return match.group(1)

    if _RAW_ID_RE.match(value):
        return value
    return None


def _id_from_uri(uri, kind: str) -> str | None:
    """'spotify:track:ID' 에서 ID만 뽑는다. 종류가 다르면 None."""
    prefix = f"spotify:{kind}:"
    if isinstance(uri, str) and uri.startswith(prefix):
        return uri[len(prefix) :] or None
    return None


def _split_artists(subtitle) -> list[str]:
    """embed의 subtitle은 'A, B, C' 형태의 아티스트 문자열이다."""
    if not subtitle:
        return []
    return [part.strip() for part in str(subtitle).split(",") if part.strip()]


def parse_track_list(track_list) -> tuple[list[dict], int]:
    """embed trackList 배열을 우리 트랙 스키마로 바꾼다.

    반환: (트랙 목록, 건너뛴 개수)
    에피소드처럼 uri가 track이 아니거나 제목이 없는 항목은 건너뛴다.
    """
    tracks = []
    skipped = 0
    for item in track_list or []:
        if not isinstance(item, dict):
            skipped += 1
            continue
        track_id = _id_from_uri(item.get("uri", ""), "track")
        title = (item.get("title") or "").strip()
        if not track_id or not title:
            skipped += 1
            continue
        tracks.append(
            {
                "id": track_id,
                "title": title,
                "artists": _split_artists(item.get("subtitle")),
                "duration_ms": int(item.get("duration") or 0),
            }
        )
    return tracks, skipped


def _find_entity(obj):
    """trackList를 가진 dict를 찾는다. embed의 플레이리스트 엔티티다.

    경로(props.pageProps.state.data.entity)를 하드코딩하지 않는 이유는
    Next.js 구조가 바뀌어도 trackList만 있으면 계속 동작하게 하기 위해서다.
    """
    if isinstance(obj, dict):
        if isinstance(obj.get("trackList"), list):
            return obj
        for value in obj.values():
            found = _find_entity(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_entity(value)
            if found is not None:
                return found
    return None


def parse_embed(html_text: str) -> dict:
    """embed 페이지 HTML에서 플레이리스트 정보를 뽑는다. 순수 함수."""
    match = _NEXT_DATA_RE.search(html_text or "")
    if not match:
        raise PlaylistParseError(f"__NEXT_DATA__ 스크립트를 찾지 못했습니다.\n{STRUCTURE_HINT}")

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise PlaylistParseError(
            f"__NEXT_DATA__ JSON을 해석하지 못했습니다: {exc}\n{STRUCTURE_HINT}"
        ) from exc

    entity = _find_entity(data)
    if entity is None:
        raise PlaylistParseError(f"trackList를 찾지 못했습니다.\n{STRUCTURE_HINT}")

    raw_list = entity["trackList"]
    tracks, skipped = parse_track_list(raw_list)

    return {
        "playlist_id": _id_from_uri(entity.get("uri", ""), "playlist") or "",
        "playlist_name": entity.get("name") or entity.get("title") or "",
        "playlist_description": entity.get("subtitle") or "",
        "tracks": tracks,
        "skipped": skipped,
        "truncated": len(raw_list) >= EMBED_TRACK_CAP,
    }


def fetch_embed(playlist_id: str, timeout: float = 15.0) -> str:
    """embed 페이지 HTML을 가져온다. 인증이 필요 없다."""
    request = urllib.request.Request(
        EMBED_URL.format(playlist_id),
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise PlaylistFetchError(
            f"embed 페이지를 가져오지 못했습니다 (HTTP {exc.code}): {playlist_id}\n"
            "플레이리스트가 비공개이거나 삭제되었을 수 있습니다."
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise PlaylistFetchError(f"네트워크 오류: {exc}") from exc


def fetch_playlist(playlist_id: str, timeout: float = 15.0) -> dict:
    """embed 페이지를 가져와 파싱한다."""
    return parse_embed(fetch_embed(playlist_id, timeout=timeout))


def _report(payload: dict) -> None:
    """수집 결과를 stderr로 요약한다."""
    name = payload["playlist_name"] or payload["playlist_id"]
    print(f"수집: {name} — {len(payload['tracks'])}곡", file=sys.stderr)
    if payload["skipped"]:
        print(
            f"  건너뛴 항목 {payload['skipped']}개 (트랙이 아니거나 제목 없음)",
            file=sys.stderr,
        )
    if payload["truncated"]:
        print(
            f"  경고: embed는 최대 {EMBED_TRACK_CAP}곡까지만 제공합니다. "
            "원본이 이보다 많으면 일부가 빠졌습니다.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Spotify 플레이리스트 트랙 수집 (embed 파싱, 인증 불필요)"
    )
    parser.add_argument("playlists", nargs="+", help="플레이리스트 URL 또는 ID (여러 개 가능)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP 타임아웃(초)")
    args = parser.parse_args()

    collected = []
    failures = 0
    for value in args.playlists:
        playlist_id = extract_playlist_id(value)
        if not playlist_id:
            print(f"플레이리스트 URL/ID를 인식하지 못했습니다: {value}", file=sys.stderr)
            failures += 1
            continue
        try:
            payload = fetch_playlist(playlist_id, timeout=args.timeout)
        except (PlaylistFetchError, PlaylistParseError) as exc:
            print(f"수집 실패 ({playlist_id}): {exc}", file=sys.stderr)
            failures += 1
            continue
        if not payload["playlist_id"]:
            payload["playlist_id"] = playlist_id
        _report(payload)
        collected.append(payload)

    if not collected:
        return 1

    output = collected[0] if len(collected) == 1 else collected
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
