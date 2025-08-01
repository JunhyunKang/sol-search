from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseRepository(ABC):
    """기본 레포지토리 클래스"""

    def __init__(self):
        pass

    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        """모든 데이터 조회"""
        pass

    @abstractmethod
    def find_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """ID로 데이터 조회"""
        pass

