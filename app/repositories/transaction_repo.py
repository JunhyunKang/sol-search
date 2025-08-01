from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseRepository


class TransactionRepository(BaseRepository):
    """거래내역 관리 레포지토리"""

    def __init__(self):
        super().__init__()
        # 더미 거래내역
        self.transactions = [
            {
                "id": 1,
                "date": "2024-01-15",
                "time": "14:30",
                "merchant": "스타벅스 강남점",
                "category": "카페",
                "amount": -4500,
                "type": "결제",
                "balance": 1245000,
                "memo": "아메리카노 2잔",
                "recipient_name": None,
                "recipient_account": None,
                "recipient_bank": None
            },
            {
                "id": 2,
                "date": "2024-01-15",
                "time": "10:15",
                "merchant": None,
                "category": "송금",
                "amount": -100000,
                "type": "송금",
                "balance": 1249500,
                "memo": "용돈",
                "recipient_name": "김네모",
                "recipient_account": "110-123-456789",
                "recipient_bank": "하나은행"
            },
            {
                "id": 3,
                "date": "2024-01-14",
                "time": "19:20",
                "merchant": "무신사",
                "category": "쇼핑",
                "amount": -89000,
                "type": "결제",
                "balance": 1349500,
                "memo": "티셔츠 구매",
                "recipient_name": None,
                "recipient_account": None,
                "recipient_bank": None
            },
            {
                "id": 4,
                "date": "2024-01-13",
                "time": "16:45",
                "merchant": None,
                "category": "송금",
                "amount": -50000,
                "type": "송금",
                "balance": 1438500,
                "memo": "생일 축하금",
                "recipient_name": "박세모",
                "recipient_account": "555-777-888999",
                "recipient_bank": "국민은행"
            },
            {
                "id": 5,
                "date": "2024-01-12",
                "time": "16:45",
                "merchant": "GS25 역삼점",
                "category": "편의점",
                "amount": -12000,
                "type": "결제",
                "balance": 1450500,
                "memo": "생필품",
                "recipient_name": None,
                "recipient_account": None,
                "recipient_bank": None
            },
            {
                "id": 6,
                "date": "2024-01-11",
                "time": "09:20",
                "merchant": None,
                "category": "송금",
                "amount": -200000,
                "type": "송금",
                "balance": 1462500,
                "memo": "월세",
                "recipient_name": "이동그라미",
                "recipient_account": "987-654-321098",
                "recipient_bank": "신한은행"
            },
            {
                "id": 7,
                "date": "2024-01-10",
                "time": "12:30",
                "merchant": "교촌치킨",
                "category": "음식",
                "amount": -28000,
                "type": "결제",
                "balance": 1478500,
                "memo": "점심 배달",
                "recipient_name": None,
                "recipient_account": None,
                "recipient_bank": None
            },
            {
                "id": 8,
                "date": "2024-01-09",
                "time": "14:15",
                "merchant": None,
                "category": "송금",
                "amount": -30000,
                "type": "송금",
                "balance": 1506500,
                "memo": "용돈",
                "recipient_name": "최삼각",
                "recipient_account": "111-222-333444",
                "recipient_bank": "우리은행"
            },
            {
                "id": 9,
                "date": "2024-01-08",
                "time": "09:15",
                "merchant": "이마트",
                "category": "마트",
                "amount": -45000,
                "type": "결제",
                "balance": 1536500,
                "memo": "장보기",
                "recipient_name": None,
                "recipient_account": None,
                "recipient_bank": None
            },
            {
                "id": 10,
                "date": "2024-01-07",
                "time": "11:30",
                "merchant": None,
                "category": "송금",
                "amount": -25000,
                "type": "송금",
                "balance": 1581500,
                "memo": "택시비",
                "recipient_name": "정오각",
                "recipient_account": "666-777-888999",
                "recipient_bank": "신한은행"
            }
        ]

    def find_all(self) -> List[Dict[str, Any]]:
        """모든 거래내역 조회"""
        return sorted(self.transactions, key=lambda x: x["date"], reverse=True)

    def find_by_id(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """ID로 거래내역 조회"""
        for transaction in self.transactions:
            if transaction["id"] == transaction_id:
                return transaction.copy()
        return None

    def get_recent_transfer_contacts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 송금한 사람들 조회 (중복 제거)"""
        transfer_contacts = {}

        # 송금 거래만 필터링하고 최신순 정렬
        transfers = [t for t in self.transactions if t["type"] == "송금" and t["recipient_name"]]
        transfers.sort(key=lambda x: (x["date"], x["time"]), reverse=True)

        # 중복 제거 (같은 사람은 최신 거래만)
        for transfer in transfers:
            name = transfer["recipient_name"]
            if name not in transfer_contacts:
                transfer_contacts[name] = {
                    "name": name,
                    "account": transfer["recipient_account"],
                    "bank": transfer["recipient_bank"],
                    "last_transfer_date": transfer["date"],
                    "last_transfer_amount": abs(transfer["amount"]),
                    "last_memo": transfer["memo"]
                }

        # limit 만큼만 반환
        return list(transfer_contacts.values())[:limit]

    def find_contact_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """이름으로 최근 송금 연락처 찾기"""
        recent_contacts = self.get_recent_transfer_contacts()

        for contact in recent_contacts:
            if contact["name"] == name:
                return contact

        return None

    def search_by_merchant(self, merchant: str) -> List[Dict[str, Any]]:
        """가맹점명으로 거래내역 검색"""
        results = []
        merchant_lower = merchant.lower()

        for transaction in self.transactions:
            if (transaction["merchant"] and
                    merchant_lower in transaction["merchant"].lower()):
                results.append(transaction.copy())

        return sorted(results, key=lambda x: x["date"], reverse=True)

    def search_by_recipient_name(self, name: str) -> List[Dict[str, Any]]:
        """받는 사람 이름으로 송금 내역 검색"""
        results = []

        for transaction in self.transactions:
            if (transaction["recipient_name"] and
                    name in transaction["recipient_name"]):
                results.append(transaction.copy())

        return sorted(results, key=lambda x: x["date"], reverse=True)

    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 거래내역 검색"""
        results = []
        for transaction in self.transactions:
            if transaction["category"] == category:
                results.append(transaction.copy())

        return sorted(results, key=lambda x: x["date"], reverse=True)

    def search_by_date_range(self, date_from: str, date_to: str = None) -> List[Dict[str, Any]]:
        """날짜 범위로 거래내역 검색"""
        if date_to is None:
            date_to = datetime.now().strftime("%Y-%m-%d")

        results = []
        for transaction in self.transactions:
            if date_from <= transaction["date"] <= date_to:
                results.append(transaction.copy())

        return sorted(results, key=lambda x: x["date"], reverse=True)

    def search_by_amount_range(self, min_amount: int = None, max_amount: int = None) -> List[Dict[str, Any]]:
        """금액 범위로 거래내역 검색"""
        results = []
        for transaction in self.transactions:
            amount = abs(transaction["amount"])  # 절댓값으로 비교

            if min_amount is not None and amount < min_amount:
                continue
            if max_amount is not None and amount > max_amount:
                continue

            results.append(transaction.copy())

        return sorted(results, key=lambda x: x["date"], reverse=True)

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 거래내역 조회"""
        sorted_transactions = sorted(self.transactions, key=lambda x: (x["date"], x["time"]), reverse=True)
        return [transaction.copy() for transaction in sorted_transactions[:limit]]

    def get_monthly_summary(self, year_month: str) -> Dict[str, Any]:
        """월별 거래 요약"""
        monthly_transactions = [
            t for t in self.transactions
            if t["date"].startswith(year_month)
        ]

        total_income = sum(t["amount"] for t in monthly_transactions if t["amount"] > 0)
        total_expense = sum(abs(t["amount"]) for t in monthly_transactions if t["amount"] < 0)

        return {
            "year_month": year_month,
            "total_transactions": len(monthly_transactions),
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense,
            "transactions": monthly_transactions
        }
