from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class SearchResponse(BaseModel):
    # 기본 정보
    success: bool = True
    action_type: str  # "transfer", "search", "menu", "unknown"

    # 화면 이동 정보
    redirect_url: str
    screen_data: Dict[str, Any]

    # 추가 정보
    confidence: Optional[float] = None
    message: Optional[str] = None
    suggestions: Optional[List[str]] = []

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "action_type": "transfer",
                "redirect_url": "/transfer",
                "screen_data": {
                    "recipient_name": "김네모",
                    "recipient_account": "110-123-456789",
                    "recipient_bank": "하나은행",
                    "amount": 100000
                },
                "confidence": 0.9,
                "message": "김네모님에게 송금을 진행하시겠습니까?",
                "suggestions": ["연락처에 추가", "자주 보내는 계좌로 등록"]
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error_code": "CONTACT_NOT_FOUND",
                "message": "연락처에서 해당 이름을 찾을 수 없습니다.",
                "details": "김네모님의 계좌 정보가 등록되어 있지 않습니다."
            }
        }