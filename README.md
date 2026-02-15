# 🎬 AI Shorts Generator (숏츠 영상 자동 생성기)

> Gemini API + TTS 나레이션을 활용하여 유튜브 숏츠 / 릴스 / 틱톡용 세로 영상을 자동으로 생성하는 도구입니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gemini](https://img.shields.io/badge/Google-Gemini%20API-orange.svg)](https://ai.google.dev/)
[![TTS](https://img.shields.io/badge/TTS-edge--tts-purple.svg)](https://github.com/rany2/edge-tts)

## 📌 소개

비개발자도 쉽게 사용할 수 있는 숏츠 영상 자동 생성 도구입니다.
**모든 기능이 무료**로 작동합니다 (Gemini 무료 티어 + edge-tts 무료).

**지원하는 콘텐츠 유형:**
- 🌅 **오늘의 명언** - 매일 새로운 명언과 해설
- 📚 **영어 공부** - 영어 표현/단어 학습
- 💡 **오늘의 상식** - 흥미로운 상식/지식
- 🧠 **동기부여** - 동기부여 메시지
- ✏️ **커스텀** - 원하는 주제로 자유롭게 생성

## 🎥 생성되는 영상 구조

```
[인트로 슬라이드] → [메인 콘텐츠 슬라이드 1~3장] → [아웃트로 슬라이드]
         ↓                    ↓                        ↓
     TTS 나레이션         TTS 나레이션             TTS 나레이션
```

- 해상도: 1080x1920 (9:16 세로)
- 길이: TTS 길이에 자동 맞춤 (보통 20~60초)
- 배경: 그라데이션 + Ken Burns (줌인/줌아웃) 효과
- 나레이션: TTS 음성이 텍스트를 읽어줌 (edge-tts, 무료)
- BGM: 배경음악 자동 적용 (선택사항, TTS와 믹싱)

## ⚡ 빠른 시작

### 1. 사전 준비

#### Python 설치 (3.9 이상)

**Windows:**
1. https://www.python.org/downloads/ 에서 다운로드
2. 설치 시 **"Add Python to PATH"** 반드시 체크!
3. 터미널에서 확인: `python --version`

**Mac:**
```bash
# Homebrew로 설치 (권장)
brew install python

# 또는 공식 사이트에서 다운로드
# https://www.python.org/downloads/

# 확인
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
python3 --version
```

#### ffmpeg 설치

**Windows:**
1. https://www.gyan.dev/ffmpeg/builds/ 접속
2. `ffmpeg-release-essentials.zip` 다운로드
3. 압축 해제 후 `bin` 폴더 경로를 환경변수 PATH에 추가
4. 터미널에서 확인: `ffmpeg -version`

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

#### Gemini API 키 발급 (무료)

1. https://aistudio.google.com/apikey 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 API 키 복사

> 💡 Gemini API 무료 티어: 분당 60회, 하루 1,500회 요청 가능 (개인 사용에 충분)

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/shorts-generator.git
cd shorts-generator

# 가상환경 생성 (권장)
python -m venv venv            # Windows
python3 -m venv venv           # Mac/Linux

# 가상환경 활성화
venv\Scripts\activate           # Windows (CMD)
venv\Scripts\Activate.ps1       # Windows (PowerShell)
source venv/bin/activate        # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 3. 설정

```bash
# 설정 파일 복사
copy config.example.yaml config.yaml    # Windows (CMD)
cp config.example.yaml config.yaml      # Mac/Linux/PowerShell
```

`config.yaml`을 열어서 Gemini API 키를 입력하세요:

```yaml
gemini:
  api_key: "여기에_API_키_입력"

# TTS 나레이션 설정 (기본 ON)
tts:
  enabled: true          # false로 하면 무음 영상
  voice: "ko-female"     # ko-female, ko-male, en-female, en-male
  rate: "+0%"            # 읽기 속도 (-50% ~ +50%)
```

### 4. 실행

```bash
# 오늘의 명언 영상 생성
python main.py --type quote

# 영어 공부 영상 생성
python main.py --type english

# 오늘의 상식 영상 생성
python main.py --type knowledge

# 동기부여 영상 생성
python main.py --type motivation

# 커스텀 주제로 생성
python main.py --type custom --topic "파이썬 꿀팁"
```

> 💡 Mac/Linux에서 `python`이 안 되면 `python3`으로 실행하세요.

생성된 영상은 `output/` 폴더에 저장됩니다!

## 📂 프로젝트 구조

```
shorts-generator/
├── main.py                 # 메인 실행 파일
├── content_generator.py    # Gemini API 콘텐츠 생성
├── tts_generator.py        # TTS 나레이션 생성 (edge-tts)
├── image_generator.py      # 슬라이드 이미지 생성 (Pillow)
├── video_generator.py      # ffmpeg 영상 합성
├── config.example.yaml     # 설정 파일 예시
├── config.yaml             # 내 설정 (git 무시)
├── requirements.txt        # 패키지 목록
├── assets/
│   ├── fonts/              # 폰트 파일 (자동 다운로드)
│   └── bgm/                # 배경음악 (선택사항)
├── output/                 # 생성된 영상
└── templates/              # 슬라이드 템플릿 설정
    └── themes.yaml         # 테마 설정
```

## 🎨 테마 커스터마이징

`templates/themes.yaml`에서 색상을 변경할 수 있습니다:

```yaml
themes:
  quote:
    gradient: ["#0f0c29", "#302b63", "#24243e"]  # 그라데이션 색상
    title_color: "#FFD700"
    text_color: "#FFFFFF"
    accent_color: "#FF6B6B"
```

## 🔊 TTS 나레이션

기본적으로 TTS가 활성화되어 있어 슬라이드 텍스트를 음성으로 읽어줍니다.

**사용 가능한 음성:**

| 설정값 | 음성 | 설명 |
|--------|------|------|
| `ko-female` | ko-KR-SunHiNeural | 한국어 여성 (기본) |
| `ko-male` | ko-KR-InJoonNeural | 한국어 남성 |
| `en-female` | en-US-JennyNeural | 영어 여성 |
| `en-male` | en-US-GuyNeural | 영어 남성 |

**읽기 속도 조절:**

```yaml
tts:
  rate: "+0%"    # 기본 속도
  rate: "+20%"   # 20% 빠르게
  rate: "-10%"   # 10% 느리게
```

> 💡 TTS는 **edge-tts**를 사용하며 완전 무료입니다 (API 키 불필요).
> TTS를 끄려면 `tts.enabled: false`로 설정하세요.

## 🎵 배경음악 추가

`assets/bgm/` 폴더에 `.mp3` 파일을 넣으면 자동으로 배경음악이 적용됩니다.

> ⚠️ 저작권 프리 음악을 사용해주세요!
> 추천: [YouTube Audio Library](https://studio.youtube.com/channel/UC/music), [Pixabay Music](https://pixabay.com/music/)

## 🔄 자동화 (선택사항)

### cron (Linux/Mac)

```bash
# 매일 오전 9시에 명언 영상 자동 생성
0 9 * * * cd /path/to/shorts-generator && source venv/bin/activate && python main.py --type quote
```

### 작업 스케줄러 (Windows)

1. "작업 스케줄러" 열기
2. "기본 작업 만들기" 클릭
3. 트리거: 매일, 원하는 시간
4. 동작: `python main.py --type quote` 실행

## ❓ 문제 해결

### 공통

| 증상 | 해결 방법 |
|------|-----------|
| `ffmpeg not found` | ffmpeg 설치 후 PATH에 추가되었는지 확인 |
| `config.yaml 파일을 찾을 수 없습니다` | `config.example.yaml`을 복사하여 `config.yaml` 생성 |
| `Gemini API 키가 설정되지 않았습니다` | `config.yaml`에서 API 키 입력 확인 |
| TTS 생성 실패 | 인터넷 연결 확인 (edge-tts는 온라인 필요) |

### Windows

| 증상 | 해결 방법 |
|------|-----------|
| 한글이 깨져서 출력 | PowerShell에서 `$env:PYTHONIOENCODING="utf-8"` 설정 후 실행 |
| `python`이 안 됨 | Python 설치 시 "Add to PATH" 체크 확인, 또는 `py` 명령어 사용 |
| ffmpeg PATH 설정 | 시스템 환경변수 → Path → ffmpeg의 `bin` 폴더 추가 |

### Mac

| 증상 | 해결 방법 |
|------|-----------|
| `python` 명령어 없음 | `python3`으로 실행, 또는 `alias python=python3` 설정 |
| `pip` 명령어 없음 | `pip3`으로 실행 |
| Homebrew가 없음 | https://brew.sh 에서 설치 |

### Linux

| 증상 | 해결 방법 |
|------|-----------|
| `pip` 없음 | `sudo apt install python3-pip` |
| 폰트 다운로드 실패 | `assets/fonts/`에 `.ttf` 폰트를 직접 넣기 |

## 💰 비용

| 항목 | 비용 |
|------|------|
| Gemini API (콘텐츠 생성) | **무료** (Google AI Studio 무료 티어) |
| edge-tts (나레이션) | **무료** (API 키 불필요) |
| ffmpeg (영상 합성) | **무료** (오픈소스) |
| **합계** | **$0 / 영상** |

## 🤝 기여하기

PR과 Issue는 언제나 환영합니다!

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포하세요!
