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
    if run.get("truncated"):
        lines.append(
            "- **경고: Spotify embed는 최대 100곡까지만 제공합니다. "
            "원본 플레이리스트가 100곡을 넘으면 일부가 빠졌을 수 있습니다.**"
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

    파일명은 초 단위다. 분 단위면 여러 플레이리스트를 연속 처리할 때
    같은 파일을 덮어쓴다.
    """
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    path = state.report_dir() / f"{_safe_name(playlist_name)}-{stamp}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
