from . import server
import asyncio

def main():
    """패키지의 메인 진입점"""
    asyncio.run(server.main())

# 패키지 레벨에서 중요한 항목들 노출
__all__ = ['main', 'server'] 