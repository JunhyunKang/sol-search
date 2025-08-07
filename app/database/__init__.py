"""
Database Package

데이터베이스 연결 및 관리를 담당합니다.
"""

from .connection import get_db_connection, close_db_connection
from .setup import initialize_database, create_dummy_data

# 데이터베이스 초기화 상태 추적
_database_initialized = False

def ensure_database_initialized():
    """데이터베이스가 초기화되었는지 확인하고 필요시 초기화"""
    global _database_initialized
    if not _database_initialized:
        initialize_database()
        _database_initialized = True

__all__ = [
    "get_db_connection",
    "close_db_connection",
    "initialize_database",
    "create_dummy_data",
    "ensure_database_initialized"
]