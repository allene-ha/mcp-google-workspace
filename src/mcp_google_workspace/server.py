#!/usr/bin/env python
"""
통합 Google Workspace MCP 서버
Google Sheets와 Google Docs API를 모두 지원하는 MCP 서버
"""

import os
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# MCP imports
from mcp.server.fastmcp import FastMCP, Context

# 로컬 임포트
from .auth.google_auth import get_authenticated_services, GoogleWorkspaceContext


@asynccontextmanager
async def workspace_lifespan(server: FastMCP) -> AsyncIterator[GoogleWorkspaceContext]:
    """Google Workspace API 연결 생명주기 관리"""
    print("Google Workspace MCP 서버 초기화 중...")
    
    try:
        # 인증된 서비스들 가져오기
        workspace_ctx = get_authenticated_services()
        print("Google Workspace API 인증 성공")
        
        yield workspace_ctx
        
    except Exception as e:
        print(f"Google Workspace API 초기화 실패: {e}")
        raise
    finally:
        print("Google Workspace API 연결 정리 완료")


# MCP 서버 초기화
mcp = FastMCP(
    "Google Workspace",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=workspace_lifespan
)


# ===== GOOGLE SHEETS 도구들 =====

@mcp.tool()
def get_sheet_data(
    spreadsheet_id: str, 
    sheet: str,
    range: Optional[str] = None,
    ctx: Context = None
) -> List[List[Any]]:
    """
    Google 스프레드시트에서 데이터를 가져옵니다.
    
    Args:
        spreadsheet_id: 스프레드시트 ID (URL에서 확인)
        sheet: 시트 이름
        range: 선택적 셀 범위 (A1 표기법, 예: 'A1:C10')
    
    Returns:
        2차원 배열 형태의 시트 데이터
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    sheets_service = workspace_ctx.sheets_service
    
    # 범위 구성
    if range:
        full_range = f"{sheet}!{range}"
    else:
        full_range = sheet
    
    # Sheets API 호출
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=full_range
    ).execute()
    
    # 결과에서 값 추출
    values = result.get('values', [])
    return values


@mcp.tool()
def update_cells(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    data: List[List[Any]],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Google 스프레드시트의 셀을 업데이트합니다.
    
    Args:
        spreadsheet_id: 스프레드시트 ID
        sheet: 시트 이름
        range: 셀 범위 (A1 표기법)
        data: 업데이트할 값들의 2차원 배열
    
    Returns:
        업데이트 작업 결과
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    sheets_service = workspace_ctx.sheets_service
    
    # 범위 구성
    full_range = f"{sheet}!{range}"
    
    # 값 범위 객체 준비
    value_range_body = {
        'values': data
    }
    
    # Sheets API 호출하여 값 업데이트
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueInputOption='USER_ENTERED',
        body=value_range_body
    ).execute()
    
    return result


@mcp.tool()
def list_sheets(spreadsheet_id: str, ctx: Context = None) -> List[str]:
    """
    Google 스프레드시트의 모든 시트 이름을 나열합니다.
    
    Args:
        spreadsheet_id: 스프레드시트 ID
    
    Returns:
        시트 이름들의 리스트
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    sheets_service = workspace_ctx.sheets_service
    
    # 스프레드시트 메타데이터 가져오기
    result = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields='sheets(properties(title))'
    ).execute()
    
    # 시트 이름들 추출
    sheets = result.get('sheets', [])
    return [sheet['properties']['title'] for sheet in sheets]


@mcp.tool()
def create_spreadsheet(title: str, ctx: Context = None) -> Dict[str, Any]:
    """
    새 Google 스프레드시트를 생성합니다.
    
    Args:
        title: 스프레드시트 제목
    
    Returns:
        생성된 스프레드시트 정보
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    sheets_service = workspace_ctx.sheets_service
    
    # 스프레드시트 생성 요청
    spreadsheet_body = {
        'properties': {
            'title': title
        }
    }
    
    result = sheets_service.spreadsheets().create(
        body=spreadsheet_body
    ).execute()
    
    return {
        'spreadsheet_id': result['spreadsheetId'],
        'title': result['properties']['title'],
        'url': result['spreadsheetUrl']
    }


@mcp.tool()
def list_spreadsheets(ctx: Context = None, limit: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Google Drive에서 스프레드시트 목록을 가져옵니다.
    
    Args:
        limit: 가져올 최대 스프레드시트 개수 (기본값: 모두)
    
    Returns:
        스프레드시트 ID와 제목이 포함된 딕셔너리 리스트
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    drive_service = workspace_ctx.drive_service
    
    # 스프레드시트 파일들 검색
    query = "mimeType='application/vnd.google-apps.spreadsheet'"
    if workspace_ctx.folder_id:
        query += f" and '{workspace_ctx.folder_id}' in parents"
    
    try:
        result = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=limit if limit else 100
        ).execute()
        
        files = result.get('files', [])
        return [{'id': file['id'], 'title': file['name']} for file in files]
        
    except Exception as e:
        print(f"스프레드시트 목록 가져오기 실패: {e}")
        return []


# ===== GOOGLE DOCS 도구들 =====

@mcp.tool()
def read_google_doc(
    document_id: str,
    format: str = "text",
    ctx: Context = None
) -> str:
    """
    Google 문서의 내용을 읽어옵니다.
    
    Args:
        document_id: Google 문서 ID
        format: 출력 형식 ('text', 'json', 'markdown')
    
    Returns:
        문서 내용
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
        
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    try:
        if format in ['json', 'markdown']:
            # 전체 구조 가져오기
            result = docs_service.documents().get(documentId=document_id).execute()
        else:
            # 텍스트만 가져오기
            fields = 'body(content(paragraph(elements(textRun(content)))))'
            result = docs_service.documents().get(
                documentId=document_id,
                fields=fields
            ).execute()
        
        if format == 'json':
            import json
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        if format == 'markdown':
            # TODO: 마크다운 변환 구현
            raise NotImplementedError("마크다운 변환은 아직 구현되지 않았습니다.")
        
        # 기본: 텍스트 형식
        text_content = ""
        if 'body' in result and 'content' in result['body']:
            for element in result['body']['content']:
                if 'paragraph' in element and 'elements' in element['paragraph']:
                    for pe in element['paragraph']['elements']:
                        if 'textRun' in pe and 'content' in pe['textRun']:
                            text_content += pe['textRun']['content']
        
        if not text_content.strip():
            return "문서를 찾았지만 내용이 비어있습니다."
        
        # 긴 텍스트 자르기
        max_length = 4000
        if len(text_content) > max_length:
            return f"내용:\n---\n{text_content[:max_length]}... [잘림 {len(text_content)} 글자]"
        else:
            return f"내용:\n---\n{text_content}"
            
    except Exception as e:
        if hasattr(e, 'resp') and e.resp.status == 404:
            raise ValueError(f"문서를 찾을 수 없습니다 (ID: {document_id})")
        elif hasattr(e, 'resp') and e.resp.status == 403:
            raise ValueError(f"문서 접근 권한이 없습니다 (ID: {document_id})")
        else:
            raise ValueError(f"문서 읽기 실패: {str(e)}")

@mcp.tool()
def append_to_google_doc(
    document_id: str,
    text_to_append: str,
    add_newline_if_needed: bool = True,
    ctx: Context = None
) -> str:
    """
    Google 문서 끝에 텍스트를 추가합니다.
    
    Args:
        document_id: Google 문서 ID
        text_to_append: 추가할 텍스트
        add_newline_if_needed: 필요시 줄바꿈 자동 추가
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    try:
        # 문서 끝 인덱스 가져오기
        doc_info = docs_service.documents().get(
            documentId=document_id,
            fields='body(content(endIndex))'
        ).execute()
        
        end_index = 1
        if 'body' in doc_info and 'content' in doc_info['body']:
            last_element = doc_info['body']['content'][-1]
            if 'endIndex' in last_element:
                end_index = last_element['endIndex'] - 1
        
        # 텍스트 준비
        text_to_insert = text_to_append
        if add_newline_if_needed and end_index > 1:
            text_to_insert = '\n' + text_to_append
        
        if not text_to_insert:
            return "추가할 내용이 없습니다."
        
        # 배치 업데이트 요청
        requests = [{
            'insertText': {
                'location': {'index': end_index},
                'text': text_to_insert
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"문서 {document_id}에 텍스트를 성공적으로 추가했습니다."
        
    except Exception as e:
        raise ValueError(f"텍스트 추가 실패: {str(e)}")

@mcp.tool()
def insert_text(
    document_id: str,
    text_to_insert: str,
    index: int,
    ctx: Context = None
) -> str:
    """
    문서의 특정 위치에 텍스트를 삽입합니다.
    
    Args:
        document_id: Google 문서 ID
        text_to_insert: 삽입할 텍스트
        index: 삽입 위치 (1부터 시작)
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    try:
        requests = [{
            'insertText': {
                'location': {'index': index},
                'text': text_to_insert
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"인덱스 {index}에 텍스트를 성공적으로 삽입했습니다."
        
    except Exception as e:
        raise ValueError(f"텍스트 삽입 실패: {str(e)}")

@mcp.tool()
def delete_range(
    document_id: str,
    start_index: int,
    end_index: int,
    ctx: Context = None
) -> str:
    """
    문서의 지정된 범위 내용을 삭제합니다.
    
    Args:
        document_id: Google 문서 ID
        start_index: 시작 인덱스 (포함)
        end_index: 끝 인덱스 (미포함)
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    if end_index <= start_index:
        raise ValueError("끝 인덱스는 시작 인덱스보다 커야 합니다.")
    
    try:
        requests = [{
            'deleteContentRange': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                }
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"범위 {start_index}-{end_index}의 내용을 성공적으로 삭제했습니다."
        
    except Exception as e:
        raise ValueError(f"범위 삭제 실패: {str(e)}")

@mcp.tool()
def apply_text_formatting(
    document_id: str,
    start_index: int,
    end_index: int,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    font_size: Optional[int] = None,
    font_family: Optional[str] = None,
    foreground_color: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    텍스트에 서식을 적용합니다.
    
    Args:
        document_id: Google 문서 ID
        start_index: 시작 인덱스
        end_index: 끝 인덱스
        bold: 굵게
        italic: 기울임
        underline: 밑줄
        font_size: 글자 크기
        font_family: 글꼴 종류
        foreground_color: 글자 색상 (hex 형식)
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    if end_index <= start_index:
        raise ValueError("끝 인덱스는 시작 인덱스보다 커야 합니다.")
    
    try:
        # 텍스트 스타일 구성
        text_style = {}
        applied_styles = []
        
        if bold is not None:
            text_style['bold'] = bold
            applied_styles.append('굵게' if bold else '굵게 해제')
        
        if italic is not None:
            text_style['italic'] = italic
            applied_styles.append('기울임' if italic else '기울임 해제')
        
        if underline is not None:
            text_style['underline'] = underline
            applied_styles.append('밑줄' if underline else '밑줄 해제')
        
        if font_size is not None:
            text_style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
            applied_styles.append(f'글자크기 {font_size}pt')
        
        if font_family is not None:
            text_style['fontFamily'] = font_family
            applied_styles.append(f'글꼴 {font_family}')
        
        if foreground_color is not None:
            # hex 색상을 RGB로 변환
            color_hex = foreground_color.lstrip('#')
            r = int(color_hex[0:2], 16) / 255.0
            g = int(color_hex[2:4], 16) / 255.0
            b = int(color_hex[4:6], 16) / 255.0
            
            text_style['foregroundColor'] = {
                'color': {
                    'rgbColor': {'red': r, 'green': g, 'blue': b}
                }
            }
            applied_styles.append(f'글자색 {foreground_color}')
        
        if not text_style:
            return "적용할 스타일이 지정되지 않았습니다."
        
        requests = [{
            'updateTextStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': end_index
                },
                'textStyle': text_style,
                'fields': ','.join(text_style.keys())
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"범위 {start_index}-{end_index}에 스타일 적용 완료: {', '.join(applied_styles)}"
        
    except Exception as e:
        raise ValueError(f"텍스트 서식 적용 실패: {str(e)}")

@mcp.tool()
def insert_table(
    document_id: str,
    rows: int,
    columns: int,
    index: int,
    ctx: Context = None
) -> str:
    """
    문서에 표를 삽입합니다.
    
    Args:
        document_id: Google 문서 ID
        rows: 행 수
        columns: 열 수
        index: 삽입 위치
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    try:
        requests = [{
            'insertTable': {
                'location': {'index': index},
                'rows': rows,
                'columns': columns
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"인덱스 {index}에 {rows}x{columns} 표를 성공적으로 삽입했습니다."
        
    except Exception as e:
        raise ValueError(f"표 삽입 실패: {str(e)}")

@mcp.tool()
def insert_page_break(
    document_id: str,
    index: int,
    ctx: Context = None
) -> str:
    """
    지정된 위치에 페이지 나누기를 삽입합니다.
    
    Args:
        document_id: Google 문서 ID
        index: 삽입 위치
    
    Returns:
        작업 결과 메시지
    """
    if ctx is None or not hasattr(ctx, 'request_context') or ctx.request_context is None or not hasattr(ctx.request_context, 'lifespan_context') or ctx.request_context.lifespan_context is None:
        raise ValueError("GoogleWorkspaceContext가 초기화되지 않았습니다. 서버 설정을 확인하세요. (ctx, request_context 또는 lifespan_context 누락)")
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    docs_service = workspace_ctx.docs_service
    
    try:
        requests = [{
            'insertPageBreak': {
                'location': {'index': index}
            }
        }]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return f"인덱스 {index}에 페이지 나누기를 성공적으로 삽입했습니다."
        
    except Exception as e:
        raise ValueError(f"페이지 나누기 삽입 실패: {str(e)}")


# ===== 추가 통합 기능들 =====

@mcp.tool()
def search_workspace_files(
    query: str,
    file_type: str = "all",
    limit: Optional[int] = None,
    ctx: Context = None
) -> List[Dict[str, str]]:
    """
    Google Drive에서 파일을 검색합니다.
    
    Args:
        query: 검색어
        file_type: 파일 타입 ('sheets', 'docs', 'all')
        limit: 가져올 최대 파일 개수 (기본값: 모두)
    
    Returns:
        검색된 파일들의 리스트
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    drive_service = workspace_ctx.drive_service
    
    # 파일 타입에 따른 MIME 타입 설정
    mime_types = {
        'sheets': "mimeType='application/vnd.google-apps.spreadsheet'",
        'docs': "mimeType='application/vnd.google-apps.document'",
        'all': "(mimeType='application/vnd.google-apps.spreadsheet' or mimeType='application/vnd.google-apps.document')"
    }
    
    search_query = f"name contains '{query}' and {mime_types.get(file_type, mime_types['all'])}"
    if workspace_ctx.folder_id:
        search_query += f" and '{workspace_ctx.folder_id}' in parents"
    
    try:
        result = drive_service.files().list(
            q=search_query,
            fields="files(id, name, mimeType)",
            pageSize=limit if limit else 50
        ).execute()
        
        files = result.get('files', [])
        return [
            {
                'id': file['id'], 
                'name': file['name'],
                'type': 'Sheets' if 'spreadsheet' in file['mimeType'] else 'Docs'
            } 
            for file in files
        ]
        
    except Exception as e:
        print(f"파일 검색 실패: {e}")
        return []


@mcp.tool()
def get_workspace_info(ctx: Context = None) -> Dict[str, Any]:
    """
    현재 Google Workspace 연결 정보를 반환합니다.
    
    Returns:
        연결 상태 및 설정 정보
    """
    workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
    
    return {
        'status': 'connected',
        'services': ['Google Sheets', 'Google Docs', 'Google Drive'],
        'working_folder': workspace_ctx.folder_id or 'My Drive (전체)',
        'available_tools': [
            # Sheets 도구들
            'get_sheet_data', 'update_cells', 'list_sheets', 'create_spreadsheet', 'list_spreadsheets',
            # Docs 도구들 (이제 server.py에 직접 정의됨)
            'read_google_doc', 'append_to_google_doc', 'insert_text', 'delete_range', 
            'apply_text_formatting', 'insert_table', 'insert_page_break',
            # 통합 도구들
            'search_workspace_files', 'get_workspace_info'
        ]
    }


@mcp.tool()
def simple_context_test(ctx: Context = None) -> Dict[str, Any]:
    print(f"simple_context_test_called, ctx is None: {ctx is None}")
    if ctx:
        print(f"ctx.request_context is None: {ctx.request_context is None}")
        if ctx.request_context:
            print(f"ctx.request_context.lifespan_context is None: {ctx.request_context.lifespan_context is None}")
    
    try:
        if ctx is None or \
           not hasattr(ctx, 'request_context') or \
           ctx.request_context is None or \
           not hasattr(ctx.request_context, 'lifespan_context') or \
           ctx.request_context.lifespan_context is None:
            return {"status": "error", "message": "Lifespan context not found"}

        workspace_ctx: GoogleWorkspaceContext = ctx.request_context.lifespan_context
        # 실제 서비스 사용 없이, 컨텍스트 객체의 존재만 확인
        return {
            "status": "success", 
            "message": "Lifespan context accessed",
            "context_type": str(type(workspace_ctx))
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """서버 실행"""
    import asyncio
    
    print("=== Google Workspace MCP 서버 시작 ===")
    print("지원 서비스: Google Sheets, Google Docs, Google Drive")
    print("MCP 클라이언트 연결을 기다리는 중...")
    
    # 서버 실행
    mcp.run() 