class SearchService:
    def process_query(self, query: str):
        if "김네모" in query and "만원" in query:
            return {
                "action_type": "transfer",
                "redirect_url": "/transfer",
                "screen_data": {"recipient_name": "김네모"}
            }
        return {"action_type": "unknown", "redirect_url": "/search"}