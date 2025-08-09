MOCK_USER_INFO = {
    "name": "강준현",
    "account_number": "3333-01-1234567",
    "bank_name": "Mock Sol Bank",
    "balance": 1450000
}

# 더미 거래내역 데이터 (프론트엔드와 동일)
MOCK_TRANSACTIONS = [
    {
        "id": "1",
        "type": "withdrawal",
        "amount": 50000,
        "balance": 1450000,
        "description": "홍길동",
        "bank": "카카오뱅크",
        "accountNumber": "3333-01-1234567",
        "date": "2025-08-03",
        "time": "14:30"
    },
    {
        "id": "2",
        "type": "deposit",
        "amount": 300000,
        "balance": 1500000,
        "description": "월급",
        "bank": None,
        "accountNumber": None,
        "date": "2025-08-01",
        "time": "09:00"
    },
    {
        "id": "3",
        "type": "withdrawal",
        "amount": 25000,
        "balance": 1200000,
        "description": "김철수",
        "bank": "신한은행",
        "accountNumber": "110-123-456789",
        "date": "2025-07-30",
        "time": "16:45"
    },
    {
        "id": "4",
        "type": "deposit",
        "amount": 100000,
        "balance": 1225000,
        "description": "용돈",
        "bank": None,
        "accountNumber": None,
        "date": "2025-07-28",
        "time": "12:00"
    },
    {
        "id": "5",
        "type": "withdrawal",
        "amount": 15000,
        "balance": 1125000,
        "description": "스타벅스",
        "bank": None,
        "accountNumber": None,
        "date": "2025-07-25",
        "time": "10:30"
    },
    {
        "id": "6",
        "type": "withdrawal",
        "amount": 80000,
        "balance": 1140000,
        "description": "이영희",
        "bank": "우리은행",
        "accountNumber": "1002-123-456789",
        "date": "2025-07-23",
        "time": "19:20"
    },
    {
        "id": "7",
        "type": "deposit",
        "amount": 200000,
        "balance": 1220000,
        "description": "부모님용돈",
        "bank": None,
        "accountNumber": None,
        "date": "2025-07-20",
        "time": "08:15"
    },
    {
        "id": "8",
        "type": "withdrawal",
        "amount": 35000,
        "balance": 1020000,
        "description": "마트결제",
        "bank": None,
        "accountNumber": None,
        "date": "2025-07-18",
        "time": "17:50"
    },
    {
        "id": "9",
        "type": "deposit",
        "amount": 500000,
        "balance": 1055000,
        "description": "보너스",
        "bank": None,
        "accountNumber": None,
        "date": "2025-07-15",
        "time": "11:30"
    },
    {
        "id": "10",
        "type": "withdrawal",
        "amount": 120000,
        "balance": 555000,
        "description": "박민수",
        "bank": "하나은행",
        "accountNumber": "123-456789-001",
        "date": "2025-07-10",
        "time": "13:45"
    }
]

# MOCK_CONTACTS 제거 - MOCK_TRANSACTIONS에서 추출하여 사용