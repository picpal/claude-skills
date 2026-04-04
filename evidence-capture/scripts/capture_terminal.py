#!/usr/bin/env python3
"""터미널 명령 실행 결과 또는 로그 파일을 터미널 스타일 PNG로 캡처하는 스크립트."""

import argparse
import html
import os
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow 필요. 설치: pip3 install --break-system-packages Pillow", file=sys.stderr)
    sys.exit(1)


def run_command(command: str) -> str:
    """명령어를 실행하고 stdout+stderr를 반환한다."""
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        if output:
            output += "\n"
        output += result.stderr
    return output.rstrip("\n")


def read_file_lines(filepath: str, start: int | None = None, end: int | None = None) -> str:
    """파일에서 지정 범위의 줄을 읽는다."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    if start is not None and end is not None:
        start_idx = max(0, start - 1)
        end_idx = min(len(all_lines), end)
        lines = all_lines[start_idx:end_idx]
    elif len(all_lines) > 50:
        lines = all_lines[-50:]
    else:
        lines = all_lines

    return "".join(lines).rstrip("\n")


def render_terminal_png(text: str, output_path: str, title: str = "", prompt_line: str = ""):
    """터미널 스타일로 텍스트를 PNG로 렌더링한다."""
    bg_color = "#1e1e1e"
    text_color = "#d4d4d4"
    prompt_color = "#4ec9b0"
    header_bg = "#333333"
    header_color = "#cccccc"

    # 한글 지원 폰트 우선, 없으면 모노스페이스 폴백
    font = None
    for font_path in [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]:
        try:
            font = ImageFont.truetype(font_path, 14)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    lines = text.split("\n")
    line_height = 20
    char_width = 8.5
    padding = 16
    header_height = 40 if (title or prompt_line) else 0

    max_line_len = max((len(line) for line in lines), default=0)
    max_line_len = max(max_line_len, len(prompt_line) if prompt_line else 0, len(title) if title else 0)

    img_width = int(max(max_line_len * char_width + padding * 2, 600))
    img_height = len(lines) * line_height + padding * 2 + header_height

    # 프롬프트 라인 추가 시 높이 증가
    if prompt_line:
        img_height += line_height + 8

    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    y = 0

    # 헤더 영역
    if title or prompt_line:
        draw.rectangle([(0, 0), (img_width, header_height)], fill=header_bg)
        header_text = title if title else ""
        draw.text((12, 10), header_text, fill=header_color, font=font)
        y = header_height

    # 프롬프트 라인 (명령어 표시)
    if prompt_line:
        y += 8
        draw.text((padding, y), f"$ {prompt_line}", fill=prompt_color, font=font)
        y += line_height + 4

    # 출력 텍스트
    y += padding // 2
    for line in lines:
        draw.text((padding, y), line, fill=text_color, font=font)
        y += line_height

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"OK: {output_path} ({img.width}x{img.height})")


def main():
    parser = argparse.ArgumentParser(description="터미널 출력/로그를 PNG로 캡처")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--command", help="실행할 명령어")
    group.add_argument("--file", help="로그 파일 경로")
    parser.add_argument("--lines", help="줄 범위 (로그 파일용, 예: 100-150)")
    parser.add_argument("--output", required=True, help="출력 PNG 경로")
    parser.add_argument("--title", default="", help="증적 항목명 (헤더에 표시)")
    args = parser.parse_args()

    if args.command:
        text = run_command(args.command)
        prompt_line = args.command
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: 파일을 찾을 수 없음: {args.file}", file=sys.stderr)
            sys.exit(1)
        start, end = None, None
        if args.lines:
            parts = args.lines.split("-")
            start, end = int(parts[0]), int(parts[1])
        text = read_file_lines(args.file, start, end)
        prompt_line = f"cat {args.file}" + (f" (L{args.lines})" if args.lines else "")

    render_terminal_png(text, args.output, title=args.title, prompt_line=prompt_line)


if __name__ == "__main__":
    main()
