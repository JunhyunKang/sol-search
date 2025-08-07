from typing import Dict, Any
from app.data.mock_data import MOCK_USER_INFO


class UserService:
    def __init__(self):
        self.user_data = MOCK_USER_INFO.copy()

    def get_user_info(self, user_id: str = "default_user") -> Dict[str, Any]:
        return self.user_data.copy()