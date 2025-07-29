from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default_user"

    class Config:
        schema_extra = {
            "example": {
                "query": "김네모 10만원 보내줘",
                "user_id": "user123"
            }
        }
