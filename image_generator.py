"""
Pillow를 사용하여 숏츠용 슬라이드 이미지를 생성합니다.
"""

import os
import re
import math
import random
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# 폰트 다운로드 URL (Noto Sans KR - Google Fonts, OFL 라이선스)
FONT_URLS = {
    "regular": "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf",
}

FONT_DIR = Path("assets/fonts")
FONT_CACHE = {}


def _ensure_font() -> str:
    """폰트 파일이 없으면 다운로드합니다."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    font_path = FONT_DIR / "NotoSansKR.ttf"

    if font_path.exists():
        return str(font_path)

    print("📥 한글 폰트 다운로드 중 (최초 1회)...")
    try:
        urllib.request.urlretrieve(FONT_URLS["regular"], str(font_path))
        print("✅ 폰트 다운로드 완료!")
    except Exception as e:
        print(f"⚠️  폰트 다운로드 실패: {e}")
        print("   assets/fonts/ 폴더에 .ttf 폰트를 직접 넣어주세요.")
        return None

    return str(font_path)


def _get_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """폰트 객체를 캐시에서 가져오거나 새로 로드합니다."""
    key = (font_path, size)
    if key not in FONT_CACHE:
        if font_path and os.path.exists(font_path):
            FONT_CACHE[key] = ImageFont.truetype(font_path, size)
        else:
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def _hex_to_rgb(hex_color: str) -> tuple:
    """HEX 색상 코드를 RGB 튜플로 변환합니다."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _strip_emoji(text: str) -> str:
    """텍스트에서 이모지를 제거합니다 (폰트가 렌더링하지 못하므로)."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\u2702-\u27B0"
        "\u2640-\u2642"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\u200d"
        "\ufe0f"
        "\u2764"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def _create_gradient(width: int, height: int, colors: list) -> Image.Image:
    """세로 그라데이션 배경을 생성합니다."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    rgb_colors = [_hex_to_rgb(c) for c in colors]

    if len(rgb_colors) == 1:
        img.paste(rgb_colors[0], (0, 0, width, height))
        return img

    segments = len(rgb_colors) - 1
    segment_height = height / segments

    for y in range(height):
        segment_idx = min(int(y / segment_height), segments - 1)
        local_pos = (y - segment_idx * segment_height) / segment_height

        c1 = rgb_colors[segment_idx]
        c2 = rgb_colors[segment_idx + 1]

        r = int(c1[0] + (c2[0] - c1[0]) * local_pos)
        g = int(c1[1] + (c2[1] - c1[1]) * local_pos)
        b = int(c1[2] + (c2[2] - c1[2]) * local_pos)

        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def _add_background_decoration(img: Image.Image, accent_color: str):
    """배경에 장식 요소를 추가합니다 (원, 라인, 글로우 등)."""
    width, height = img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    color = _hex_to_rgb(accent_color)

    # 1. 반투명 큰 원 (보케 효과)
    random.seed(42)  # 일관된 디자인
    for _ in range(6):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        radius = random.randint(100, 350)
        alpha = random.randint(8, 25)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(*color, alpha),
        )

    # 2. 상단/하단 장식 라인
    line_margin = 160
    draw.line(
        [(line_margin, 100), (width - line_margin, 100)],
        fill=(*color, 60), width=2,
    )
    draw.line(
        [(line_margin, height - 100), (width - line_margin, height - 100)],
        fill=(*color, 60), width=2,
    )

    # 3. 모서리 장식 (L자 형태)
    corner_len = 60
    corner_alpha = 50
    # 좌상단
    draw.line([(60, 60), (60 + corner_len, 60)], fill=(*color, corner_alpha), width=2)
    draw.line([(60, 60), (60, 60 + corner_len)], fill=(*color, corner_alpha), width=2)
    # 우상단
    draw.line([(width - 60, 60), (width - 60 - corner_len, 60)], fill=(*color, corner_alpha), width=2)
    draw.line([(width - 60, 60), (width - 60, 60 + corner_len)], fill=(*color, corner_alpha), width=2)
    # 좌하단
    draw.line([(60, height - 60), (60 + corner_len, height - 60)], fill=(*color, corner_alpha), width=2)
    draw.line([(60, height - 60), (60, height - 60 - corner_len)], fill=(*color, corner_alpha), width=2)
    # 우하단
    draw.line([(width - 60, height - 60), (width - 60 - corner_len, height - 60)], fill=(*color, corner_alpha), width=2)
    draw.line([(width - 60, height - 60), (width - 60, height - 60 - corner_len)], fill=(*color, corner_alpha), width=2)

    # 합성
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))


def _draw_text_card(img: Image.Image, x: int, y: int, w: int, h: int, radius: int = 30):
    """텍스트 뒤에 반투명 카드 배경을 그립니다."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=radius,
        fill=(0, 0, 0, 70),
    )
    result = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.paste(result)


def _draw_text_wrapped(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont,
                       max_width: int, x: int, y: int, fill: tuple,
                       align: str = "center", line_spacing: int = 15) -> int:
    """텍스트를 자동 줄바꿈하며 그립니다. 최종 y 위치를 반환합니다."""
    # 이모지 제거
    text = _strip_emoji(text)
    if not text:
        return y

    lines = []

    # \n 을 실제 줄바꿈으로 처리
    paragraphs = text.split("\\n") if "\\n" in text else text.split("\n")

    for paragraph in paragraphs:
        words = list(paragraph)
        current_line = ""

        for char in words:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char

        if current_line:
            lines.append(current_line)

    current_y = y
    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if align == "center":
            text_x = x - text_width // 2
        elif align == "left":
            text_x = x
        else:
            text_x = x - text_width

        # 텍스트 그림자 효과 (2단계)
        shadow_color = (0, 0, 0)
        draw.text((text_x + 3, current_y + 3), line, font=font, fill=shadow_color)
        draw.text((text_x + 1, current_y + 1), line, font=font, fill=shadow_color)
        draw.text((text_x, current_y), line, font=font, fill=fill)

        current_y += text_height + line_spacing

    return current_y


def _calc_text_block_height(text: str, font: ImageFont.FreeTypeFont,
                            max_width: int, line_spacing: int = 15) -> int:
    """텍스트 블록의 높이를 미리 계산합니다."""
    text = _strip_emoji(text)
    if not text:
        return 0

    paragraphs = text.split("\\n") if "\\n" in text else text.split("\n")
    total_height = 0
    line_count = 0

    for paragraph in paragraphs:
        current_line = ""
        for char in list(paragraph):
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    bbox2 = font.getbbox(current_line)
                    total_height += (bbox2[3] - bbox2[1]) + line_spacing
                    line_count += 1
                current_line = char
        if current_line:
            bbox2 = font.getbbox(current_line)
            total_height += (bbox2[3] - bbox2[1]) + line_spacing
            line_count += 1

    return total_height


def create_slide(
    slide_data: dict,
    theme: dict,
    width: int = 1080,
    height: int = 1920,
    slide_type: str = "content",
    font_path: str = None,
) -> Image.Image:
    """
    단일 슬라이드 이미지를 생성합니다.

    Args:
        slide_data: 슬라이드 데이터 (main_text, sub_text 등)
        theme: 테마 설정
        width: 이미지 너비
        height: 이미지 높이
        slide_type: 슬라이드 유형 (intro, content, outro)
        font_path: 폰트 파일 경로

    Returns:
        생성된 PIL Image
    """
    # 배경 그라데이션 생성
    img = _create_gradient(width, height, theme["gradient"])

    # 배경 장식 요소 추가
    _add_background_decoration(img, theme["accent_color"])

    draw = ImageDraw.Draw(img)

    # 폰트 준비
    if not font_path:
        font_path = _ensure_font()

    center_x = width // 2
    padding = 120
    max_text_width = width - padding * 2

    if slide_type == "intro":
        # ===== 인트로 슬라이드 =====
        title = _strip_emoji(slide_data.get("intro_title", ""))

        # 텍스트 카드 배경
        title_font = _get_font(font_path, 80)
        title_h = _calc_text_block_height(title, title_font, max_text_width)
        card_y = height // 2 - 120
        card_h = title_h + 160
        _draw_text_card(img, padding - 40, card_y - 40, width - (padding - 40) * 2, card_h)
        draw = ImageDraw.Draw(img)  # draw 재생성 (이미지가 교체되므로)

        # 타이틀
        title_color = _hex_to_rgb(theme["title_color"])
        _draw_text_wrapped(draw, title, title_font, max_text_width,
                           center_x, card_y, title_color)

        # 날짜
        sub_font = _get_font(font_path, 36)
        sub_color = _hex_to_rgb(theme["subtitle_color"])
        from datetime import date
        today = date.today().strftime("%Y.%m.%d")
        _draw_text_wrapped(draw, today, sub_font, max_text_width,
                           center_x, card_y + title_h + 30, sub_color)

    elif slide_type == "outro":
        # ===== 아웃트로 슬라이드 =====
        outro_text = _strip_emoji(slide_data.get("outro_text", "다음에 또 만나요!"))

        # 텍스트 카드 배경
        main_font = _get_font(font_path, 52)
        text_h = _calc_text_block_height(outro_text, main_font, max_text_width)
        sub_font = _get_font(font_path, 36)
        sub_text = "좋아요 & 구독 부탁드려요!"
        sub_h = _calc_text_block_height(sub_text, sub_font, max_text_width)
        card_y = height // 2 - 120
        card_h = text_h + sub_h + 180
        _draw_text_card(img, padding - 40, card_y - 40, width - (padding - 40) * 2, card_h)
        draw = ImageDraw.Draw(img)

        # 메인 텍스트
        text_color = _hex_to_rgb(theme["text_color"])
        end_y = _draw_text_wrapped(draw, outro_text, main_font, max_text_width,
                                   center_x, card_y, text_color)

        # 구독/좋아요 안내
        accent_color = _hex_to_rgb(theme["accent_color"])
        _draw_text_wrapped(draw, sub_text, sub_font, max_text_width,
                           center_x, end_y + 40, accent_color)

    else:
        # ===== 콘텐츠 슬라이드 =====
        main_text = _strip_emoji(slide_data.get("main_text", ""))
        sub_text = _strip_emoji(slide_data.get("sub_text", ""))

        # 텍스트 블록 높이 계산
        main_font = _get_font(font_path, 56)
        main_h = _calc_text_block_height(main_text, main_font, max_text_width, line_spacing=20)
        sub_h = 0
        if sub_text:
            sub_font = _get_font(font_path, 38)
            sub_h = _calc_text_block_height(sub_text, sub_font, max_text_width) + 50

        total_h = main_h + sub_h
        card_y = height // 2 - total_h // 2 - 40
        card_h = total_h + 80
        _draw_text_card(img, padding - 40, card_y, width - (padding - 40) * 2, card_h)
        draw = ImageDraw.Draw(img)

        # 메인 텍스트
        text_color = _hex_to_rgb(theme["text_color"])
        start_y = card_y + 40
        end_y = _draw_text_wrapped(draw, main_text, main_font, max_text_width,
                                   center_x, start_y, text_color, line_spacing=20)

        # 서브 텍스트
        if sub_text:
            sub_font = _get_font(font_path, 38)
            sub_color = _hex_to_rgb(theme["subtitle_color"])
            _draw_text_wrapped(draw, sub_text, sub_font, max_text_width,
                               center_x, end_y + 40, sub_color)

    return img


def generate_slides(content: dict, theme: dict, width: int = 1080, height: int = 1920,
                    font_path: str = None, output_dir: str = "output") -> list:
    """
    콘텐츠 데이터로부터 모든 슬라이드 이미지를 생성합니다.

    Args:
        content: Gemini가 생성한 콘텐츠 딕셔너리
        theme: 테마 설정
        width: 이미지 너비
        height: 이미지 높이
        font_path: 커스텀 폰트 경로
        output_dir: 이미지 저장 디렉토리

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    temp_dir = os.path.join(output_dir, "_temp_slides")
    os.makedirs(temp_dir, exist_ok=True)

    slide_paths = []
    slide_index = 0

    # 1. 인트로 슬라이드
    print("  🎨 인트로 슬라이드 생성 중...")
    intro_img = create_slide(
        {"intro_title": content.get("intro_title", "")},
        theme, width, height, "intro", font_path
    )
    path = os.path.join(temp_dir, f"slide_{slide_index:03d}.png")
    intro_img.save(path, "PNG")
    slide_paths.append(path)
    slide_index += 1

    # 2. 콘텐츠 슬라이드
    for i, slide_data in enumerate(content.get("slides", [])):
        print(f"  🎨 콘텐츠 슬라이드 {i+1} 생성 중...")
        content_img = create_slide(
            slide_data, theme, width, height, "content", font_path
        )
        path = os.path.join(temp_dir, f"slide_{slide_index:03d}.png")
        content_img.save(path, "PNG")
        slide_paths.append(path)
        slide_index += 1

    # 3. 아웃트로 슬라이드
    print("  🎨 아웃트로 슬라이드 생성 중...")
    outro_img = create_slide(
        {"outro_text": content.get("outro_text", "다음에 또 만나요!")},
        theme, width, height, "outro", font_path
    )
    path = os.path.join(temp_dir, f"slide_{slide_index:03d}.png")
    outro_img.save(path, "PNG")
    slide_paths.append(path)

    print(f"  ✅ 총 {len(slide_paths)}장의 슬라이드 생성 완료!")
    return slide_paths
