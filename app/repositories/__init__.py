from app.repositories.transaction_repo import TransactionRepository

_transaction_repo = None

def get_transaction_repository() -> TransactionRepository:
    """거래내역 레포지토리 싱글톤 인스턴스 반환"""
    global _transaction_repo
    if _transaction_repo is None:
        _transaction_repo = TransactionRepository()
    return _transaction_repo


__all__ = [
    "TransactionRepository",
    "get_transaction_repository",
]
