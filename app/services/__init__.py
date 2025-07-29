"""
Business Logic Services Package

비즈니스 로직을 담당하는 서비스들을 정의합니다.
"""

# from .nlp_service import NLPService
from .search_service import SearchService
# from .banking_service import BankingService

# 서비스 인스턴스들 (싱글톤 패턴)
_nlp_service = None
_search_service = None
_banking_service = None

# def get_nlp_service() -> NLPService:
#     """NLP 서비스 싱글톤 인스턴스 반환"""
#     global _nlp_service
#     if _nlp_service is None:
#         _nlp_service = NLPService()
#     return _nlp_service

def get_search_service() -> SearchService:
    """검색 서비스 싱글톤 인스턴스 반환"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

# def get_banking_service() -> BankingService:
#     """뱅킹 서비스 싱글톤 인스턴스 반환"""
#     global _banking_service
#     if _banking_service is None:
#         _banking_service = BankingService()
#     return _banking_service

__all__ = [
    # "NLPService",
    "SearchService",
    # "BankingService",
    # "get_nlp_service",
    "get_search_service",
    # "get_banking_service"
]