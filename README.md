# Google Workspace MCP 서버

Google Sheets, Google Docs, Google Drive를 모두 지원하는 통합 MCP (Model Context Protocol) 서버입니다.

## 🚀 주요 기능

### Google Sheets
- 📊 **데이터 읽기/쓰기**: 스프레드시트에서 데이터를 읽고 업데이트
- 📝 **시트 관리**: 시트 목록 조회, 새 스프레드시트 생성

### Google Docs
- 📖 **문서 읽기**: 텍스트, JSON, 마크다운 형식으로 문서 내용 조회
- ✍️ **텍스트 편집**: 텍스트 추가, 삽입, 삭제
- 🎨 **서식 적용**: 굵게, 기울임, 색상, 글꼴 등 텍스트 서식
- 📋 **구조 요소**: 표 삽입, 페이지 나누기

### Google Drive
- 📂 **스프레드시트 검색**: Drive 내 특정 폴더 또는 전체에서 스프레드시트 목록 조회 (`list_spreadsheets`)
- 🔍 **통합 파일 검색**: Drive 내 특정 폴더 또는 전체에서 Sheets/Docs 파일 통합 검색 (`search_workspace_files`)

### 기타 서버 기능
- ℹ️ **상태 정보**: 연결 상태 및 사용 가능한 도구 확인 (`get_workspace_info`)

## 📦 설치

이 프로젝트는 로컬 개발 및 테스트를 위해 다음 방법으로 설치할 수 있습니다.

1.  **저장소 복제 (Clone Repository)**:
    ```bash
    git clone <저장소_URL>
    cd mcp-google-workspace
    ```

2.  **가상 환경 생성 및 활성화 ( 권장)**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate   # Windows
    ```

3.  **의존성 및 프로젝트 설치 (Editable Mode)**:
    `uv` (권장) 또는 `pip`을 사용하여 설치합니다.
    ```bash
    # uv 사용 시
    uv pip install -e .

    # pip 사용 시
    pip install -e .
    ```
    `-e .` 옵션은 프로젝트를 "편집 가능" 모드로 설치하여, 소스 코드를 변경하면 바로 적용됩니다.

### Google API 설정

#### Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. 다음 API들을 활성화:
   - Google Sheets API
   - Google Docs API  
   - Google Drive API

#### OAuth 자격증명 생성
1. "APIs & Services" → "Credentials"
2. "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. 생성된 JSON 파일을 `credentials.json`으로 저장

#### OAuth 동의 화면 설정
1. "APIs & Services" → "OAuth consent screen"
2. User Type: "External" 선택
3. 필수 정보 입력
4. Scopes 추가:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/drive.file`
5. Test users에 본인 이메일 추가

## 🔧 사용법

프로젝트가 편집 가능 모드 (`-e .`)로 설치되었다면, `pyproject.toml`에 정의된 스크립트를 통해 MCP 서버를 실행할 수 있습니다.

```bash
# 가상 환경이 활성화된 상태에서 실행
mcp-google-workspace
```

또는 Python 모듈로 직접 실행할 수도 있습니다 (프로젝트 루트 디렉토리에서):

```bash
python -m src.mcp_google_workspace.server
```

### Claude Desktop에서 사용

`mcp_config.json` 파일에 다음 설정 추가 (`mcp.json` 또는 `mcp_servers.json` 등 환경에 따라 파일명 상이할 수 있음):

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "mcp-google-workspace",
      "env": {
        "CREDENTIALS_PATH": "/path/to/credentials.json",
        "TOKEN_PATH": "/path/to/token.json"
      }
    }
  }
}
```

### 환경 변수

- `CREDENTIALS_PATH`: OAuth 자격증명 파일 경로 (기본값: 워크스페이스 루트의 `credentials.json`)
- `TOKEN_PATH`: 토큰 저장 파일 경로 (기본값: 워크스페이스 루트의 `token.json`)
- `DRIVE_FOLDER_ID`: 작업할 특정 Google Drive 폴더 ID (선택사항, 지정하지 않으면 전체 Drive 검색)

(참고: `SERVICE_ACCOUNT_PATH`는 현재 OAuth 2.0 사용자 인증 흐름을 사용하므로 이 구현에서는 사용되지 않습니다.)

## 🛠️ 사용 가능한 도구들

기능별로 그룹화된 사용 가능한 도구 목록입니다. `get_workspace_info`를 통해 전체 동적 목록을 확인할 수도 있습니다.

### Google Sheets 도구
- `get_sheet_data`: 시트 데이터 조회
- `update_cells`: 셀 데이터 업데이트
- `list_sheets`: 특정 스프레드시트 내의 시트 이름 목록 조회
- `create_spreadsheet`: 새 스프레드시트 생성

### Google Docs 도구
- `read_google_doc`: 문서 내용 읽기
- `append_to_google_doc`: 문서 끝에 텍스트 추가
- `insert_text`: 특정 위치에 텍스트 삽입
- `delete_range`: 범위 내용 삭제
- `apply_text_formatting`: 텍스트 서식 적용
- `insert_table`: 표 삽입
- `insert_page_break`: 페이지 나누기 삽입

### Google Drive 도구
- `list_spreadsheets`: Google Drive에서 스프레드시트 목록 조회
- `search_workspace_files`: Google Drive에서 Sheets/Docs 파일 검색

### 기타 서버 도구
- `get_workspace_info`: 연결 정보 및 현재 사용 가능한 모든 도구 목록 (동적) 조회
- `simple_context_test`: (개발 및 테스트용) 컨텍스트 접근 테스트

## 💡 사용 예시

Claude Desktop에서 다음과 같이 사용할 수 있습니다:

```
"스프레드시트 목록을 보여주세요"
"문서 ID가 'abc123'인 Google Docs를 읽어주세요"
"새로운 '프로젝트 계획' 스프레드시트를 만들어주세요"
"문서에 '회의 요약'이라는 제목을 굵게 추가해주세요"
```

## 🔒 보안

- `credentials.json`과 `token.json` 파일은 안전하게 보관하세요
- 이 파일들을 공개 저장소에 업로드하지 마세요
- `.gitignore`에 자격증명 파일들이 포함되어 있는지 확인하세요

## 🤝 기여

이슈나 개선 제안이 있으시면 GitHub에서 자유롭게 제기해주세요!

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. # mcp-google-workspace
# mcp-google-workspace
