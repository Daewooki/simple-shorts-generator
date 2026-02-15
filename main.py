"""
🎬 AI Shorts Generator
Gemini API를 활용한 숏츠 영상 자동 생성기

사용법:
    python main.py --type quote          # 오늘의 명언
    python main.py --type english        # 영어 공부
    python main.py --type knowledge      # 오늘의 상식
    python main.py --type motivation     # 동기부여
    python main.py --type custom --topic "파이썬 꿀팁"  # 커스텀
"""

import os
import sys
import argparse
from datetime import datetime

# Windows 콘솔 UTF-8 인코딩 설정 (이모지 출력 지원)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import yaml

from content_generator import generate_content
from image_generator import generate_slides
from tts_generator import generate_all_tts, resolve_voice, VOICES
from video_generator import create_video


def load_config(config_path: str = "config.yaml") -> dict:
    """설정 파일을 로드합니다."""
    if not os.path.exists(config_path):
        print("❌ config.yaml 파일을 찾을 수 없습니다!")
        print("   다음 명령어로 설정 파일을 생성하세요:")
        print("   cp config.example.yaml config.yaml")
        print("   그 후 config.yaml을 열어 Gemini API 키를 입력하세요.")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_theme(content_type: str, themes_path: str = "templates/themes.yaml") -> dict:
    """테마 설정을 로드합니다."""
    if not os.path.exists(themes_path):
        # 기본 테마 반환
        return {
            "gradient": ["#667eea", "#764ba2"],
            "title_color": "#FFFFFF",
            "text_color": "#FFFFFF",
            "accent_color": "#FFD700",
            "subtitle_color": "#D0D0FF",
            "emoji": "✨",
            "intro_title": "오늘의 정보",
        }
    
    with open(themes_path, "r", encoding="utf-8") as f:
        themes = yaml.safe_load(f)
    
    return themes.get("themes", {}).get(content_type, themes["themes"].get("custom", {}))


def main():
    # CLI 인자 파싱
    parser = argparse.ArgumentParser(
        description="🎬 AI Shorts Generator - Gemini API 기반 숏츠 영상 자동 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --type quote              오늘의 명언 영상 생성
  python main.py --type english            영어 공부 영상 생성
  python main.py --type knowledge          오늘의 상식 영상 생성
  python main.py --type motivation         동기부여 영상 생성
  python main.py --type custom --topic "AI 트렌드"   커스텀 주제
        """
    )
    parser.add_argument(
        "--type", "-t",
        choices=["quote", "english", "knowledge", "motivation", "custom"],
        default="quote",
        help="콘텐츠 유형 (기본: quote)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="커스텀 주제 (--type custom 일 때 사용)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="설정 파일 경로 (기본: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # 헤더 출력
    print("=" * 50)
    print("🎬 AI Shorts Generator")
    print("=" * 50)
    print()
    
    # 1. 설정 로드
    print("📋 설정 로드 중...")
    config = load_config(args.config)
    
    api_key = config.get("gemini", {}).get("api_key", "")
    if not api_key or api_key == "여기에_GEMINI_API_키를_입력하세요":
        print("❌ Gemini API 키가 설정되지 않았습니다!")
        print("   config.yaml 파일을 열어 API 키를 입력해주세요.")
        print("   API 키 발급: https://aistudio.google.com/apikey")
        sys.exit(1)
    
    model_name = config.get("gemini", {}).get("model", "gemini-2.0-flash")
    
    # 영상 설정
    video_config = config.get("video", {})
    width = video_config.get("width", 1080)
    height = video_config.get("height", 1920)
    fps = video_config.get("fps", 30)
    slide_duration = video_config.get("slide_duration", 5)
    transition_duration = video_config.get("transition_duration", 0.5)
    
    # TTS 설정
    tts_config = config.get("tts", {})
    tts_enabled = tts_config.get("enabled", True)
    tts_voice = tts_config.get("voice", "ko-female")
    tts_rate = tts_config.get("rate", "+0%")
    
    # BGM 설정
    bgm_config = config.get("bgm", {})
    bgm_enabled = bgm_config.get("enabled", False)
    bgm_volume = bgm_config.get("volume", 0.15)
    
    # 출력 설정
    output_config = config.get("output", {})
    output_dir = output_config.get("directory", "output")
    filename_prefix = output_config.get("filename_prefix", "shorts")
    
    # 폰트 설정
    font_config = config.get("font", {})
    custom_font = font_config.get("custom_font", None)
    
    # 테마 로드
    theme = load_theme(args.type)
    
    content_type_names = {
        "quote": "오늘의 명언",
        "english": "영어 공부",
        "knowledge": "오늘의 상식",
        "motivation": "동기부여",
        "custom": f"커스텀 ({args.topic or '자유 주제'})",
    }
    
    print(f"📌 콘텐츠 유형: {content_type_names[args.type]}")
    print(f"📐 해상도: {width}x{height}")
    print(f"🔊 TTS: {'ON' if tts_enabled else 'OFF'}")
    print(f"🎵 BGM: {'ON' if bgm_enabled else 'OFF'}")
    print()
    
    # 2. 콘텐츠 생성 (Gemini API)
    try:
        content = generate_content(
            api_key=api_key,
            content_type=args.type,
            model_name=model_name,
            topic=args.topic
        )
    except Exception as e:
        print(f"❌ 콘텐츠 생성 실패: {e}")
        sys.exit(1)
    
    print()
    
    # 3. 슬라이드 이미지 생성 (Pillow)
    print("🎨 슬라이드 이미지 생성 중...")
    try:
        slide_paths = generate_slides(
            content=content,
            theme=theme,
            width=width,
            height=height,
            font_path=custom_font,
            output_dir=output_dir,
        )
    except Exception as e:
        print(f"❌ 슬라이드 생성 실패: {e}")
        sys.exit(1)
    
    print()
    
    # 4. TTS 생성 (edge-tts)
    tts_data = None
    if tts_enabled:
        print("🔊 TTS 나레이션 생성 중...")
        try:
            voice = resolve_voice(tts_voice)
            tts_data = generate_all_tts(
                content=content,
                voice=voice,
                rate=tts_rate,
                output_dir=output_dir,
            )
        except Exception as e:
            print(f"⚠️  TTS 생성 실패 (나레이션 없이 계속 진행): {e}")
            tts_data = None
        print()
    
    # 5. 영상 합성 (ffmpeg)
    today = datetime.now().strftime("%Y%m%d")
    output_filename = f"{filename_prefix}_{today}_{args.type}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    try:
        result_path = create_video(
            slide_paths=slide_paths,
            output_path=output_path,
            fps=fps,
            slide_duration=slide_duration,
            transition_duration=transition_duration,
            bgm_enabled=bgm_enabled,
            bgm_volume=bgm_volume,
            tts_data=tts_data,
        )
    except Exception as e:
        print(f"❌ 영상 생성 실패: {e}")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("🎉 숏츠 영상 생성 완료!")
    print(f"📁 파일 위치: {result_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
