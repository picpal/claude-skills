"""
Live auto-caption SRT → 정제된 텍스트 (타임스탬프 포함).

라이브 영상의 YouTube 자동자막은 누적 표시 방식이라 이전 줄이 다음 줄의 prefix로
반복된다. 이 스크립트는 prefix-dedup으로 한 번에 정리한다.

usage:
    python dedup_subs.py <input.srt> <output.txt>
"""

import re
import sys
from pathlib import Path


def dedup_srt(src_path: Path, dest_path: Path) -> tuple[int, int]:
    raw = src_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\n+", raw.strip())

    lines: list[str] = []
    last = ""
    for b in blocks:
        parts = b.strip().split("\n")
        if len(parts) < 3:
            continue
        ts = parts[1]
        text = " ".join(p.strip() for p in parts[2:]).strip()
        if not text:
            continue
        # 이전 줄이 현재 줄의 prefix → 누적 자막의 짧은 버전 → skip
        if last and text.startswith(last):
            last = text
            continue
        # 현재 줄이 이전 줄의 prefix → 누적 자막의 잔여 → skip
        if last and last.startswith(text):
            continue
        start = ts.split(" --> ")[0].split(",")[0]
        lines.append(f"[{start}] {text}")
        last = text

    out = "\n".join(lines)
    dest_path.write_text(out, encoding="utf-8")
    return len(lines), len(out)


def main():
    if len(sys.argv) != 3:
        print("usage: python dedup_subs.py <input.srt> <output.txt>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    if not src.exists():
        print(f"input not found: {src}", file=sys.stderr)
        sys.exit(1)

    dest.parent.mkdir(parents=True, exist_ok=True)
    n_lines, n_chars = dedup_srt(src, dest)
    print(f"줄: {n_lines}, 문자: {n_chars:,}, 파일: {dest}")


if __name__ == "__main__":
    main()
