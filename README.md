# Jupyter Notebook 이미지 GitHub 업로드 도구

Jupyter Notebook 파일(.ipynb) 내부의 BASE64로 인코딩된 이미지를 자동으로 GitHub 저장소에 업로드하고 URL로 변환해주는 Python 스크립트입니다.

## 주요 기능

- 지정된 폴더 내 모든 `.ipynb` 파일 자동 검색
- BASE64로 인코딩된 이미지 자동 감지
- GitHub 저장소에 이미지 자동 업로드
- BASE64 문자열을 GitHub CDN URL로 자동 치환
- 처리 통계 및 진행 상황 실시간 표시
- 중복 이미지 자동 제거 (해시 기반)

## 설치 방법

### 1. Python 환경 확인
Python 3.6 이상이 필요합니다.

```bash
python --version
```

### 2. 필수 패키지 설치

```bash
pip install requests
```

### 3. 스크립트 다운로드

```bash
git clone https://github.com/ssafy-jinhyeok/AI.git
cd AI
```

## 사용 방법

### 1. GitHub Personal Access Token 생성

1. GitHub 설정 → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 필요한 권한 선택:
   - `repo` (전체 저장소 접근)
4. 토큰 생성 후 안전한 곳에 복사

### 2. 환경 변수 설정

**Linux/Mac:**
```bash
export GITHUB_TOKEN=your_github_token_here
```

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN="your_github_token_here"
```

**Windows (CMD):**
```cmd
set GITHUB_TOKEN=your_github_token_here
```

### 3. 스크립트 설정

`script.py` 파일의 다음 부분을 수정:

```python
REPO_OWNER = 'your-github-username'  # GitHub 사용자명
REPO_NAME = 'your-repo-name'         # 저장소 이름
```

### 4. 실행

```bash
python script.py
```

## 작동 방식

```
1. 현재 폴더 및 하위 폴더의 모든 .ipynb 파일 검색
   ↓
2. 각 노트북 파일에서 BASE64 이미지 패턴 탐지
   ↓
3. 발견된 이미지를 SHA256 해시 기반 파일명으로 변환
   ↓
4. GitHub API를 통해 저장소에 이미지 업로드
   ↓
5. 원본 노트북의 BASE64 문자열을 GitHub URL로 치환
   ↓
6. 변경된 노트북 파일 저장
```

## 출력 예시

```
============================================================
총 3개의 노트북 파일 발견
============================================================

처리 중: ./notebooks/example.ipynb
  발견된 BASE64 문자열: 5개
  고유 이미지: 3개
  [1/3] 업로드 중: a1b2c3d4e5f6g7h8.png... ✓
  [2/3] 업로드 중: 9i8j7k6l5m4n3o2p.png... ✓
  [3/3] 업로드 중: q1r2s3t4u5v6w7x8.png... ✓
  ✓ 완료: 3개 이미지 업로드 및 치환

============================================================
처리 완료!
  처리된 노트북: 3개
  업로드된 이미지: 15개
  에러: 0개
============================================================
```

## 디렉토리 구조

```
AI/
├── script.py              # 메인 스크립트
├── README.md             # 이 파일
├── LICENSE.md            # 라이선스
└── notebook_images/      # 업로드된 이미지 저장 폴더 (GitHub)
    ├── a1b2c3d4e5f6g7h8.png
    ├── 9i8j7k6l5m4n3o2p.png
    └── ...
```

## 라이선스

이 프로젝트의 라이센스 내용은 [LICENSE.md](LICENSE.md)를 참조하세요.