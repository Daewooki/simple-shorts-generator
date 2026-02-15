"""
edge-tts를 사용하여 텍스트를 음성으로 변환합니다.
무료이며 API 키가 필요 없습니다.

지원 음성:
  - 한국어 여성: ko-KR-SunHiNeural
  - 한국어 남성: ko-KR-InJoonNeural
  - 영어 여성: en-US-JennyNeural
  - 영어 남성: en-US-GuyNeural
"""

import os
import asyncio
import subprocess

import edge_tts


# 사용 가능한 음성 목록
VOICES = {
    "ko-female": "ko-KR-SunHiNeural",
    "ko-male": "ko-KR-InJoonNeural",
    "en-female": "en-US-JennyNeural",
    "en-male": "en-US-GuyNeural",
}


def _get_audio_duration(file_path: str) -> float:
    """ffprobe를 사용하여 오디오 파일의 길이(초)를 반환합니다."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path,
            ],
            capture_output=True, text=True, timeout=10
        )
        duration = float(result.stdout.strip())
        return duration
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return 5.0  # fallback


def _clean_text_for_tts(text: str) -> str:
    """TTS에 적합하도록 텍스트를 정리합니다."""
    import re

    # 이스케이프된 줄바꿈 → 쉼표(자연스러운 끊어읽기)
    text = text.replace("\\n", ", ")
    text = text.replace("\n", ", ")

    # 이모지 제거 (TTS가 읽지 못함)
    # 주의: 한글 영역(U+AC00~U+D7AF)을 포함하지 않도록 범위 지정
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 이모티콘
        "\U0001F300-\U0001F5FF"  # 심볼 & 픽토그래프
        "\U0001F680-\U0001F6FF"  # 교통 & 지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U0001F900-\U0001F9FF"  # 보충 이모지
        "\U0001FA00-\U0001FA6F"  # 체스 기호
        "\U0001FA70-\U0001FAFF"  # 심볼 확장
        "\u2702-\u27B0"          # Dingbats
        "\u2640-\u2642"
        "\u2600-\u26FF"          # 기타 기호
        "\u2700-\u27BF"          # Dingbats
        "\u200d"                 # Zero Width Joiner
        "\ufe0f"                 # Variation Selector
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    # 연속 공백/쉼표 정리
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r",\s*,", ",", text)
    text = text.strip().strip(",").strip()
    return text


async def _generate_single_tts(
    text: str, voice: str, output_path: str, rate: str = "+0%"
) -> tuple:
    """단일 텍스트에 대해 TTS 음성을 생성합니다."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

    duration = _get_audio_duration(output_path)
    return output_path, duration


def generate_tts(
    text: str,
    voice: str = "ko-KR-SunHiNeural",
    output_path: str = "tts_output.mp3",
    rate: str = "+0%",
) -> tuple:
    """
    단일 텍스트에 대해 TTS를 생성합니다.

    Args:
        text: 변환할 텍스트
        voice: 사용할 음성 (VOICES 딕셔너리 참조)
        output_path: 출력 파일 경로
        rate: 읽기 속도 (예: "+0%", "-10%", "+20%")

    Returns:
        (파일 경로, 오디오 길이) 튜플
    """
    clean_text = _clean_text_for_tts(text)
    if not clean_text:
        clean_text = "..."  # 빈 텍스트 방지

    return asyncio.run(
        _generate_single_tts(clean_text, voice, output_path, rate)
    )


def resolve_voice(voice_setting: str) -> str:
    """설정값을 실제 음성 ID로 변환합니다."""
    # VOICES 딕셔너리에 있는 별칭이면 변환
    if voice_setting in VOICES:
        return VOICES[voice_setting]
    # 이미 전체 음성 ID면 그대로 반환
    return voice_setting


def generate_all_tts(
    content: dict,
    voice: str = "ko-KR-SunHiNeural",
    rate: str = "+0%",
    output_dir: str = "output",
) -> list:
    """
    모든 슬라이드에 대해 TTS를 일괄 생성합니다.

    Args:
        content: Gemini가 생성한 콘텐츠 딕셔너리
        voice: 사용할 음성
        rate: 읽기 속도
        output_dir: TTS 파일 저장 디렉토리

    Returns:
        [{"path": str, "duration": float}, ...] 리스트
        슬라이드 순서(인트로, 콘텐츠1, 콘텐츠2, ..., 아웃트로)와 동일
    """
    temp_dir = os.path.join(output_dir, "_temp_tts")
    os.makedirs(temp_dir, exist_ok=True)

    results = []
    idx = 0

    # 1. 인트로
    intro_text = content.get("intro_title", "")
    if intro_text:
        print("  🔊 인트로 TTS 생성 중...")
        path = os.path.join(temp_dir, f"tts_{idx:03d}.mp3")
        _, duration = generate_tts(intro_text, voice, path, rate)
        results.append({"path": path, "duration": duration})
        idx += 1

    # 2. 콘텐츠 슬라이드
    for i, slide in enumerate(content.get("slides", [])):
        main_text = slide.get("main_text", "")
        sub_text = slide.get("sub_text", "")

        # 메인 텍스트 + 서브 텍스트를 합쳐서 읽기
        full_text = main_text
        if sub_text:
            full_text += ". " + sub_text

        print(f"  🔊 슬라이드 {i + 1} TTS 생성 중...")
        path = os.path.join(temp_dir, f"tts_{idx:03d}.mp3")
        _, duration = generate_tts(full_text, voice, path, rate)
        results.append({"path": path, "duration": duration})
        idx += 1

    # 3. 아웃트로
    outro_text = content.get("outro_text", "")
    if outro_text:
        print("  🔊 아웃트로 TTS 생성 중...")
        path = os.path.join(temp_dir, f"tts_{idx:03d}.mp3")
        _, duration = generate_tts(outro_text, voice, path, rate)
        results.append({"path": path, "duration": duration})

    print(f"  ✅ 총 {len(results)}개의 TTS 생성 완료!")
    return results
