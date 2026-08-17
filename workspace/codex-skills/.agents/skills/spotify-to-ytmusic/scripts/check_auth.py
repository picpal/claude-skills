#!/usr/bin/env python3
"""동기화 전 사전 점검.

Spotify는 인증이 필요 없다 (embed 페이지 파싱). 도달 가능한지만 확인한다.
YouTube Music은 실제로 API를 호출해 인증이 살아 있는지 확인한다.
"""

import sys

import state

# 도달 확인용 공개 플레이리스트 (Today's Top Hits)
PROBE_PLAYLIST = "37i9dQZF1DXcBWIGoYBM5M"

YTMUSIC_SETUP = """\
[YouTube Music 셋업]
  1. 브라우저에서 https://music.youtube.com 에 로그인한다
  2. 개발자 도구(F12) → Network 탭을 연다
  3. 페이지를 새로고침하고, /youtubei/v1/ 로 시작하는 POST 요청을 하나 고른다
  4. 그 요청의 Request Headers 전체를 복사한다
  5. 아래 명령을 실행하고, 프롬프트에 복사한 헤더를 붙여넣은 뒤 Ctrl-D 를 누른다:

     ytmusicapi browser --file {auth_path}

  주의: 세션이 만료되면 같은 절차를 다시 수행해야 한다
        YouTube Premium은 필요 없다\
"""


def check_spotify() -> tuple[bool, str]:
    """embed 페이지에 도달해 파싱까지 되는지 확인한다. 인증은 필요 없다."""
    try:
        import fetch_spotify
    except ImportError as exc:
        return False, f"fetch_spotify 모듈을 불러오지 못했습니다: {exc}"

    try:
        payload = fetch_spotify.fetch_playlist(PROBE_PLAYLIST, timeout=10)
    except Exception as exc:
        return False, f"embed 페이지 확인 실패: {exc}"

    count = len(payload["tracks"])
    if count == 0:
        return False, "embed 페이지는 열렸지만 트랙을 얻지 못했습니다 (구조 변경 가능성)"
    return True, f"인증 불필요. 도달 확인됨 (테스트 플레이리스트 {count}곡 파싱)"


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
        print("\n준비 완료. 동기화를 시작할 수 있습니다.")
        return 0

    if not ytmusic_ok:
        print()
        print(YTMUSIC_SETUP.format(auth_path=state.auth_file()))
    return 1


if __name__ == "__main__":
    sys.exit(main())
