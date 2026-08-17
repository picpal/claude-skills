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

_DEFAULT_HOME = Path.home() / ".codex" / "spotify-to-ytmusic"
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
