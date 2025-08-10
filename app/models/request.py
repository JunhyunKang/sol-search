from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str

    class Config:
        schema_extra = {
            "example": {
                "query": "김네모 10만원 보내줘",
            }
        }
class ExplanationRequest(BaseModel):
    product_type: str  # "card" 또는 "loan"
    product_id: Optional[str] = None  # 특정 상품 ID (선택사항)

    class Config:
        schema_extra = {
            "example": {
                "product_type": "card",
                "product_id": "shinhan-check"
            }
        }