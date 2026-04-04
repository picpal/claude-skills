#!/usr/bin/env python3
"""소스코드를 구문 강조하여 PNG 이미지로 캡처하는 스크립트."""

import argparse
import os
import sys
import textwrap
from pathlib import Path

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, TextLexer
    from pygments.formatters import ImageFormatter
except ImportError:
    print("Error: pygments 필요. 설치: pip3 install --break-system-packages pygments", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow 필요. 설치: pip3 install --break-system-packages Pillow", file=sys.stderr)
    sys.exit(1)


def parse_line_range(range_str: str) -> tuple[int, int]:
    """'시작-끝' 형식의 줄 범위를 파싱한다."""
    parts = range_str.split("-")
    if len(parts) != 2:
        raise ValueError(f"잘못된 줄 범위: {range_str} (형식: 시작-끝)")
    return int(parts[0]), int(parts[1])


def read_lines(filepath: str, start: int | None = None, end: int | None = None) -> tuple[str, int]:
    """파일에서 지정 범위의 줄을 읽는다. 시작 줄 번호를 반환한다."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    if start is not None and end is not None:
        start_idx = max(0, start - 1)
        end_idx = min(len(all_lines), end)
        lines = all_lines[start_idx:end_idx]
        line_offset = start
    else:
        lines = all_lines
        line_offset = 1

    return "".join(lines), line_offset


def add_header(image: Image.Image, header_text: str, bg_color: str = "#2d2d2d", text_color: str = "#e0e0e0") -> Image.Image:
    """이미지 상단에 헤더를 추가한다."""
    header_height = 40
    new_img = Image.new("RGB", (image.width, image.height + header_height), bg_color)

    draw = ImageDraw.Draw(new_img)
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

    draw.text((12, 10), header_text, fill=text_color, font=font)
    new_img.paste(image, (0, header_height))
    return new_img


def main():
    parser = argparse.ArgumentParser(description="소스코드를 PNG로 캡처")
    parser.add_argument("--file", required=True, help="소스 파일 경로")
    parser.add_argument("--lines", help="줄 범위 (예: 10-30)")
    parser.add_argument("--output", required=True, help="출력 PNG 경로")
    parser.add_argument("--title", default="", help="증적 항목명 (헤더에 표시)")
    parser.add_argument("--font-size", type=int, default=16, help="폰트 크기 (기본: 16)")
    parser.add_argument("--width", type=int, default=120, help="줄 너비 문자 수 (기본: 120)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: 파일을 찾을 수 없음: {args.file}", file=sys.stderr)
        sys.exit(1)

    start, end = None, None
    if args.lines:
        start, end = parse_line_range(args.lines)

    code, line_offset = read_lines(args.file, start, end)

    try:
        lexer = get_lexer_for_filename(args.file)
    except Exception:
        lexer = TextLexer()

    formatter = ImageFormatter(
        style="monokai",
        font_size=args.font_size,
        line_numbers=True,
        line_number_start=line_offset,
        image_pad=16,
        line_pad=4,
    )

    png_data = highlight(code, lexer, formatter)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # 임시로 저장 후 헤더 추가
    from io import BytesIO
    img = Image.open(BytesIO(png_data))

    # 헤더 텍스트 구성
    header_parts = []
    if args.title:
        header_parts.append(args.title)
    header_parts.append(args.file)
    if args.lines:
        header_parts.append(f"L{args.lines}")
    header_text = "  |  ".join(header_parts)

    img = add_header(img, header_text)
    img.save(args.output, "PNG")

    print(f"OK: {args.output} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
