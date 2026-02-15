"""
ffmpeg를 사용하여 슬라이드 이미지를 영상으로 합성합니다.
TTS 오디오가 제공되면 나레이션이 포함된 영상을 생성합니다.
"""

import os
import glob
import subprocess
import shutil


def _check_ffmpeg() -> bool:
    """ffmpeg가 설치되어 있는지 확인합니다."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _find_bgm(bgm_dir: str = "assets/bgm") -> str | None:
    """BGM 디렉토리에서 음악 파일을 찾습니다."""
    if not os.path.exists(bgm_dir):
        return None
    
    audio_exts = ["*.mp3", "*.wav", "*.m4a", "*.ogg"]
    for ext in audio_exts:
        files = glob.glob(os.path.join(bgm_dir, ext))
        if files:
            return files[0]
    
    return None


def _build_zoom_filter(
    width: int, height: int, fps: int, duration: float,
    transition_duration: float, slide_index: int,
) -> str:
    """
    Ken Burns 효과 (줌인/줌아웃) + 페이드 필터를 생성합니다.
    슬라이드마다 줌 방향이 번갈아가며 바뀝니다.
    """
    total_frames = int(fps * duration)
    fade_frames = int(fps * transition_duration)
    fade_out_start = int(fps * (duration - transition_duration))

    # 이미지를 약간 크게 확대해서 줌 여유 공간 확보
    # 줌인: 1.0 → 1.15 / 줌아웃: 1.15 → 1.0
    if slide_index % 2 == 0:
        # 줌인 (천천히 확대)
        zoom_expr = f"min(1+0.15*on/{total_frames},1.15)"
    else:
        # 줌아웃 (천천히 축소)
        zoom_expr = f"max(1.15-0.15*on/{total_frames},1.0)"

    # zoompan: 원본 이미지를 줌하면서 가운데 유지
    zoompan = (
        f"zoompan=z='{zoom_expr}'"
        f":x='iw/2-(iw/zoom/2)'"
        f":y='ih/2-(ih/zoom/2)'"
        f":d={total_frames}"
        f":s={width}x{height}"
        f":fps={fps}"
    )

    fade_in = f"fade=in:0:{fade_frames}"
    fade_out = f"fade=out:{fade_out_start}:{fade_frames}"

    return f"{zoompan},{fade_in},{fade_out}"


def _create_slide_clip(
    slide_path: str,
    output_path: str,
    duration: float,
    fps: int,
    transition_duration: float,
    tts_path: str | None = None,
    slide_index: int = 0,
) -> bool:
    """단일 슬라이드를 비디오 클립으로 변환합니다 (Ken Burns 효과 포함)."""
    vf = _build_zoom_filter(1080, 1920, fps, duration, transition_duration, slide_index)

    if tts_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", slide_path,
            "-i", tts_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", vf,
            "-shortest",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", slide_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", vf,
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # fallback: zoompan 없이 기본 fade만 적용
        fade_frames = int(fps * transition_duration)
        fade_out_start = int(fps * (duration - transition_duration))
        simple_vf = f"scale=1080:1920,fade=in:0:{fade_frames},fade=out:{fade_out_start}:{fade_frames}"

        if tts_path:
            cmd_simple = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", slide_path,
                "-i", tts_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-vf", simple_vf,
                "-shortest",
                output_path,
            ]
        else:
            cmd_simple = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", slide_path,
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-vf", simple_vf,
                output_path,
            ]
        result = subprocess.run(cmd_simple, capture_output=True, text=True)
        return result.returncode == 0

    return True


def create_video(
    slide_paths: list,
    output_path: str,
    fps: int = 30,
    slide_duration: float = 5.0,
    transition_duration: float = 0.5,
    bgm_enabled: bool = False,
    bgm_volume: float = 0.15,
    tts_data: list | None = None,
) -> str:
    """
    슬라이드 이미지들을 영상으로 합성합니다.
    
    Args:
        slide_paths: 슬라이드 이미지 파일 경로 리스트
        output_path: 출력 영상 파일 경로
        fps: 프레임 레이트
        slide_duration: 각 슬라이드 기본 표시 시간 (초, TTS 없을 때 사용)
        transition_duration: 전환 효과 시간 (초)
        bgm_enabled: 배경음악 사용 여부
        bgm_volume: 배경음악 볼륨
        tts_data: TTS 데이터 리스트 [{"path": str, "duration": float}, ...]
                  None이면 TTS 없이 기존 방식으로 생성
    
    Returns:
        생성된 영상 파일 경로
    """
    if not _check_ffmpeg():
        print("❌ ffmpeg가 설치되어 있지 않습니다!")
        print("   설치 방법:")
        print("   - Windows: https://www.gyan.dev/ffmpeg/builds/")
        print("   - Mac: brew install ffmpeg")
        print("   - Linux: sudo apt install ffmpeg")
        raise RuntimeError("ffmpeg not found")
    
    if not slide_paths:
        raise ValueError("슬라이드가 없습니다!")
    
    has_tts = tts_data is not None and len(tts_data) == len(slide_paths)
    
    if has_tts:
        print("🎬 영상 생성 중... (TTS 나레이션 포함)")
    else:
        print("🎬 영상 생성 중...")
    
    temp_dir = os.path.dirname(slide_paths[0])
    temp_videos = []
    
    # 1단계: 각 슬라이드를 개별 비디오 클립으로 변환
    for i, slide_path in enumerate(slide_paths):
        temp_video = os.path.join(temp_dir, f"clip_{i:03d}.mp4")

        # TTS가 있으면 오디오 길이 기반으로 슬라이드 시간 결정
        if has_tts:
            tts_info = tts_data[i]
            tts_path = tts_info["path"]
            # TTS 길이 + 여유 시간 (최소 slide_duration)
            clip_duration = max(tts_info["duration"] + 0.5, slide_duration)
        else:
            tts_path = None
            clip_duration = slide_duration

        success = _create_slide_clip(
            slide_path=slide_path,
            output_path=temp_video,
            duration=clip_duration,
            fps=fps,
            transition_duration=transition_duration,
            tts_path=tts_path,
            slide_index=i,
        )
        
        if not success:
            print(f"  ⚠️  슬라이드 {i+1} 변환 중 오류 발생")
        
        temp_videos.append(temp_video)
        duration_str = f" ({clip_duration:.1f}초)" if has_tts else ""
        print(f"  📹 슬라이드 {i+1}/{len(slide_paths)} 변환 완료{duration_str}")
    
    # 2단계: concat 파일 생성
    concat_file = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_file, "w") as f:
        for video in temp_videos:
            f.write(f"file '{os.path.abspath(video)}'\n")
    
    # 3단계: 영상 합치기
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # TTS가 있는 경우 concat 방식이 다름 (오디오 포함)
    if has_tts:
        # TTS 오디오가 포함된 클립들을 합치기
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ]
        
        if bgm_enabled:
            bgm_path = _find_bgm()
            if bgm_path:
                print(f"  🎵 배경음악 적용: {os.path.basename(bgm_path)}")
                # TTS + BGM 믹싱: TTS 볼륨 유지, BGM 볼륨 낮춤
                temp_no_bgm = os.path.join(temp_dir, "temp_no_bgm.mp4")
                concat_cmd.append(temp_no_bgm)
                
                print("  🔧 TTS 영상 렌더링 중...")
                result = subprocess.run(concat_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"concat failed: {result.stderr[:200]}")
                
                # BGM 믹싱
                print("  🎵 TTS + BGM 믹싱 중...")
                mix_cmd = [
                    "ffmpeg", "-y",
                    "-i", temp_no_bgm,
                    "-i", bgm_path,
                    "-filter_complex",
                    f"[0:a]volume=1.0[tts];[1:a]volume={bgm_volume}[bgm];"
                    f"[tts][bgm]amix=inputs=2:duration=first[a]",
                    "-map", "0:v",
                    "-map", "[a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    output_path,
                ]
                print("  🔧 최종 영상 렌더링 중...")
                result = subprocess.run(mix_cmd, capture_output=True, text=True)
            else:
                print("  ⚠️  BGM 파일을 찾을 수 없어 TTS만 사용합니다.")
                concat_cmd.append(output_path)
                print("  🔧 최종 영상 렌더링 중...")
                result = subprocess.run(concat_cmd, capture_output=True, text=True)
        else:
            concat_cmd.append(output_path)
            print("  🔧 최종 영상 렌더링 중...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True)
    else:
        # TTS 없는 기존 방식
        if bgm_enabled:
            bgm_path = _find_bgm()
            if bgm_path:
                print(f"  🎵 배경음악 적용: {os.path.basename(bgm_path)}")
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0", "-i", concat_file,
                    "-i", bgm_path,
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-filter_complex", f"[1:a]volume={bgm_volume}[bgm];[bgm]apad[a]",
                    "-map", "0:v",
                    "-map", "[a]",
                    "-shortest",
                    "-pix_fmt", "yuv420p",
                    output_path,
                ]
            else:
                print("  ⚠️  BGM 파일을 찾을 수 없어 음악 없이 생성합니다.")
                bgm_enabled = False
        
        if not bgm_enabled:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path,
            ]
        
        print("  🔧 최종 영상 렌더링 중...")
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 영상 생성 실패: {result.stderr[:500]}")
        raise RuntimeError(f"ffmpeg failed: {result.stderr[:200]}")
    
    # 4단계: 임시 파일 정리
    print("  🧹 임시 파일 정리 중...")
    try:
        # 슬라이드 임시 디렉토리
        shutil.rmtree(temp_dir)
    except Exception:
        pass
    
    # TTS 임시 디렉토리도 정리
    tts_temp_dir = os.path.join(os.path.dirname(output_path), "_temp_tts")
    if os.path.exists(tts_temp_dir):
        try:
            shutil.rmtree(tts_temp_dir)
        except Exception:
            pass
    
    # 결과 확인
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"✅ 영상 생성 완료!")
        print(f"   📁 파일: {output_path}")
        print(f"   📊 크기: {file_size:.1f} MB")
        return output_path
    else:
        raise RuntimeError("영상 파일이 생성되지 않았습니다.")
