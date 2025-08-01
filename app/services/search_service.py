import re
from typing import Dict, Any, List, Optional
from .nlp_service import NLPService
from app.repositories import get_transaction_repository


class SearchService:

    def __init__(self):
        # 의존성 주입
        self.nlp_service = NLPService()
        self.transaction_repo = get_transaction_repository()

    def process_query(self, query: str) -> Dict[str, Any]:
        """메인 검색 처리 로직"""
        try:
            # 1. NLP로 텍스트 파싱
            parsed_result = self.nlp_service.parse_query(query)

            intent = parsed_result["intent"]
            entities = parsed_result["entities"]
            confidence = parsed_result["confidence"]

            # 2. 의도별 처리
            if intent == "transfer":
                return self._handle_transfer_intent(entities, confidence)
            elif intent == "search":
                return self._handle_search_intent(entities, confidence)
            # elif intent == "menu":
            #     return self._handle_menu_intent(query, confidence)
            # else:
            #     return self._handle_unknown_intent(query, confidence)

        except Exception as e:
            return self._handle_error(str(e))

    def _handle_transfer_intent(self, entities: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """송금 의도 처리"""
        person_name = entities.get("person")
        amount = entities.get("amount")

        # 이름이 없으면 에러
        if not person_name:
            return {
                "success": True,
                "action_type": "error",
                "redirect_url": "/search",
                "screen_data": {},
                "confidence": confidence,
                "message": "송금할 사람의 이름을 알려주세요.",
                "suggestions": ["김네모 10만원", "엄마 5만원 보내줘", "최근 송금 내역 보기"]
            }

        # 거래내역에서 해당 이름으로 송금한 기록 찾기
        contact_info = self.transaction_repo.find_contact_by_name(person_name)

        if not contact_info:
            return {
                "success": True,
                "action_type": "error",
                "redirect_url": "/search",
                "screen_data": {},
                "confidence": confidence,
                "message": f"{person_name}님에게 송금한 기록이 없습니다.",
                "suggestions": [
                    f"{person_name} 계좌 직접 입력",
                    "최근 송금 내역 확인",
                    "연락처에서 계좌 찾기"
                ]
            }

        return {
            "success": True,
            "action_type": "transfer",
            "redirect_url": "/transfer",
            "screen_data": {
                "recipient_name": contact_info["name"],
                "recipient_account": contact_info["account"],
                "recipient_bank": contact_info["bank"],
                "amount": amount,
                "currency": "KRW",
                "last_transfer_date": contact_info.get("last_transfer_date"),
                "last_transfer_amount": contact_info.get("last_transfer_amount")
            },
            "confidence": confidence,
            "message": f"{contact_info['name']}님에게 {amount:,}원을 송금하시겠습니까?" if amount else f"{contact_info['name']}님에게 송금하시겠습니까?",
            "suggestions": ["금액 수정", "메모 추가", "송금 내역 확인"]
        }

    def _handle_search_intent(self, entities: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """조회 의도 처리"""
        merchant = entities.get("merchant")
        person_name = entities.get("person")
        date = entities.get("date")

        transactions = []
        filter_info = {}
        message = ""

        # 가맹점별 조회
        if merchant:
            transactions = self.transaction_repo.search_by_merchant(merchant)
            filter_info["merchant"] = merchant
            message = f"{merchant} 거래내역을 찾았습니다."

        # 사람별 송금 내역 조회
        elif person_name:
            transactions = self.transaction_repo.search_by_recipient_name(person_name)
            filter_info["recipient"] = person_name
            message = f"{person_name}님과의 송금내역을 찾았습니다."

        # 날짜별 조회 (추후 구현)
        elif date:
            # 날짜 파싱 로직 필요
            transactions = self.transaction_repo.get_recent_transactions(limit=20)
            filter_info["date"] = date
            message = f"{date} 거래내역을 조회합니다."

        # 기본: 최근 거래내역
        else:
            transactions = self.transaction_repo.get_recent_transactions(limit=20)
            message = "최근 거래내역입니다."

        return {
            "success": True,
            "action_type": "search",
            "redirect_url": "/transactions",
            "screen_data": {
                "transactions": transactions,
                "filter": filter_info,
                "total_count": len(transactions)
            },
            "confidence": confidence,
            "message": message,
            "suggestions": ["기간별 조회", "카테고리별 조회", "금액별 조회"]
        }

    # def _handle_menu_intent(self, query: str, confidence: float) -> Dict[str, Any]:
    #     """메뉴 의도 처리"""
    #     # 메뉴 검색
    #     menu_results = self.menu_repo.search_by_keyword(query)
    #
    #     if menu_results:
    #         # 가장 일치하는 메뉴
    #         best_match = menu_results[0]
    #
    #         return {
    #             "success": True,
    #             "action_type": "menu",
    #             "redirect_url": best_match["screen_url"],
    #             "screen_data": {
    #                 "menu_id": best_match["id"],
    #                 "menu_title": best_match["title"],
    #                 "menu_description": best_match["description"],
    #                 "menu_category": best_match["category"],
    #                 "alternative_menus": menu_results[1:3] if len(menu_results) > 1 else []
    #             },
    #             "confidence": confidence,
    #             "message": f"{best_match['title']} 화면으로 이동합니다.",
    #             "suggestions": ["설정 가이드", "고객센터 문의", "인기 메뉴 보기"]
    #         }
    #
    #     # 매칭되는 메뉴가 없으면 인기 메뉴 제안
    #     popular_menus = self.menu_repo.get_popular_menus(limit=3)
    #
    #     return {
    #         "success": True,
    #         "action_type": "menu",
    #         "redirect_url": "/settings",
    #         "screen_data": {
    #             "original_query": query,
    #             "popular_menus": popular_menus,
    #             "all_categories": ["설정", "이체", "조회", "보안", "카드"]
    #         },
    #         "confidence": confidence,
    #         "message": f"'{query}'와 관련된 메뉴를 찾지 못했습니다.",
    #         "suggestions": ["해외결제 막기", "자동이체 관리", "알림 설정"]
    #     }
    #
    # def _handle_unknown_intent(self, query: str, confidence: float) -> Dict[str, Any]:
    #     """알 수 없는 의도 처리"""
    #     # 최근 송금 연락처 제안
    #     recent_contacts = self.transaction_repo.get_recent_transfer_contacts(limit=3)
    #     contact_suggestions = [f"{c['name']} 송금" for c in recent_contacts]
    #
    #     # 인기 메뉴 제안
    #     popular_menus = self.menu_repo.get_popular_menus(limit=2)
    #     menu_suggestions = [menu["keywords"][0] for menu in popular_menus if menu["keywords"]]
    #
    #     all_suggestions = contact_suggestions + menu_suggestions + ["거래내역 조회"]
    #
    #     return {
    #         "success": True,
    #         "action_type": "unknown",
    #         "redirect_url": "/search",
    #         "screen_data": {
    #             "original_query": query,
    #             "recent_contacts": recent_contacts,
    #             "popular_menus": popular_menus,
    #             "help_examples": [
    #                 "김네모 10만원 보내줘",
    #                 "스타벅스 거래내역",
    #                 "해외결제 막기"
    #             ]
    #         },
    #         "confidence": confidence,
    #         "message": "죄송합니다. 요청을 이해하지 못했습니다.",
    #         "suggestions": all_suggestions[:5]  # 최대 5개만
    #     }

    def _handle_error(self, error_message: str) -> Dict[str, Any]:
        """에러 처리"""
        return {
            "success": False,
            "action_type": "error",
            "redirect_url": "/search",
            "screen_data": {
                "error_details": error_message
            },
            "confidence": 0.0,
            "message": "처리 중 오류가 발생했습니다.",
            "suggestions": ["다시 시도해보세요", "고객센터 문의"]
        }

    # def get_search_suggestions(self) -> Dict[str, Any]:
    #     """검색 제안사항 생성 (홈 화면 등에서 사용)"""
    #     recent_contacts = self.transaction_repo.get_recent_transfer_contacts(limit=3)
    #     popular_menus = self.menu_repo.get_popular_menus(limit=3)
    #
    #     return {
    #         "recent_transfers": [
    #             f"{contact['name']} 송금" for contact in recent_contacts
    #         ],
    #         "popular_menus": [
    #             menu["title"] for menu in popular_menus
    #         ],
    #         "common_queries": [
    #             "거래내역 조회",
    #             "스타벅스 결제내역",
    #             "이번달 사용내역"
    #         ]
    #     }