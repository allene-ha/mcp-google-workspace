"""
Google API 인증 공통 모듈
Google Sheets와 Google Docs API를 위한 통합 인증 시스템
"""

import base64
import os
import json
from typing import Any, Optional, List
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 통합 스코프 - Sheets와 Docs 모두 포함
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

# 환경 변수 설정
CREDENTIALS_CONFIG = os.environ.get('CREDENTIALS_CONFIG')
TOKEN_PATH = os.environ.get('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.environ.get('SERVICE_ACCOUNT_PATH', 'service_account.json')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID', '')


@dataclass
class GoogleWorkspaceContext:
    """Google Workspace 서비스 컨텍스트"""
    sheets_service: Any
    docs_service: Any
    drive_service: Any
    folder_id: Optional[str] = None


def get_authenticated_services() -> GoogleWorkspaceContext:
    """
    Google Workspace API 서비스들을 인증하고 반환
    
    Returns:
        GoogleWorkspaceContext: 인증된 서비스들
    """
    creds = None

    # Base64 인코딩된 자격증명 확인 (환경 변수)
    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)), 
            SCOPES
        )
    
    # 서비스 계정 인증 먼저 시도
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH,
                scopes=SCOPES
            )
            print("서비스 계정 인증 사용")
            print(f"Google Drive 폴더 ID: {DRIVE_FOLDER_ID or '지정되지 않음'}")
        except Exception as e:
            print(f"서비스 계정 인증 오류: {e}")
            print("OAuth 플로우로 대체")
            creds = None
    
    # OAuth 플로우로 대체
    if not creds:
        print("OAuth 인증 플로우 사용")
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as token:
                creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
                
        # 자격증명이 유효하지 않으면 새로 가져오기
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 다음 실행을 위해 자격증명 저장
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
    
    # 서비스 빌드
    sheets_service = build('sheets', 'v4', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    return GoogleWorkspaceContext(
        sheets_service=sheets_service,
        docs_service=docs_service,
        drive_service=drive_service,
        folder_id=DRIVE_FOLDER_ID if DRIVE_FOLDER_ID else None
    ) 