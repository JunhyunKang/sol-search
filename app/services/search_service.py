import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .nlp_service import GeminiNLPService
from app.data import MOCK_TRANSACTIONS


class SearchService:

    def __init__(self):
        # Gemini NLP 서비스 사용
        self.nlp_service = GeminiNLPService()

    def _get_contact_from_transactions(self, person_name: str) -> Optional[Dict[str, Any]]:
        """MOCK_TRANSACTIONS에서 특정 사람의 최근 송금 정보 추출"""
        # 해당 사람에게 송금한 거래 찾기 (출금 + 사람 이름이 있는 거래)
        person_transactions = [
            t for t in MOCK_TRANSACTIONS
            if t["type"] == "withdrawal"
               and t.get("bank") is not None  # 은행 정보가 있는 송금
               and person_name in t["description"]
        ]

        if not person_transactions:
            return None

        # 가장 최근 거래 찾기
        latest_transaction = max(person_transactions, key=lambda x: f"{x['date']} {x['time']}")

        return {
            "name": person_name,
            "bank": latest_transaction["bank"],
            "account": latest_transaction["accountNumber"],
            "last_transfer_date": latest_transaction["date"],
            "last_transfer_amount": latest_transaction["amount"]
        }

    def _get_all_transfer_contacts(self) -> List[str]:
        """MOCK_TRANSACTIONS에서 송금 가능한 모든 연락처 이름 추출"""
        contacts = set()
        for t in MOCK_TRANSACTIONS:
            if (t["type"] == "withdrawal"
                    and t.get("bank") is not None
                    and t.get("accountNumber") is not None):
                # description에서 사람 이름 추출 (한글 2-4글자)
                import re
                names = re.findall(r'[가-힣]{2,4}', t["description"])
                for name in names:
                    if name not in ["만원", "거래", "내역", "송금", "이체"]:  # 제외할 단어들
                        contacts.add(name)
        return list(contacts)

    def process_query(self, query: str) -> Dict[str, Any]:
        """메인 검색 처리 로직"""
        try:
            # 1. NLP로 텍스트 파싱
            parsed_result = self.nlp_service.parse_query(query)

            intent = parsed_result["intent"]
            entities = parsed_result["entities"]
            confidence = parsed_result["confidence"]

            # 🔍 파싱 결과 확인용 프린트문들
            print(f"🔍 검색어: {query}")
            print(f"📊 파싱 결과:")
            print(f"   - 의도(intent): {intent}")
            print(f"   - 개체명(entities): {entities}")
            print(f"   - 신뢰도(confidence): {confidence}")
            print(f"   - 사용모델: {parsed_result.get('used_model', 'unknown')}")
            if parsed_result.get('reasoning'):
                print(f"   - 분석근거: {parsed_result['reasoning']}")
            print("-" * 50)

            # 2. 의도별 처리
            if intent == "transfer":
                result = self._handle_transfer_intent(entities, confidence, query)
            elif intent == "search":
                result = self._handle_search_intent(entities, confidence, query)
            elif intent == "menu":
                result = self._handle_menu_intent(entities, confidence, query)
            else:
                result = self._handle_unknown_intent(query, confidence)

            # 🎯 최종 응답 확인용 프린트문
            print(f"🎯 최종 응답:")
            print(f"   - action_type: {result.get('action_type')}")
            print(f"   - redirect_url: {result.get('redirect_url')}")
            print(f"   - message: {result.get('message')}")
            print("=" * 50)

            return result

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            return self._handle_error(str(e))

    def _handle_transfer_intent(self, entities: Dict[str, Any], confidence: float, query: str) -> Dict[str, Any]:
        """송금 의도 처리"""
        person_name = entities.get("person")
        amount = entities.get("amount")

        # 이름이 없으면 에러
        if not person_name:
            available_contacts = self._get_all_transfer_contacts()
            return {
                "success": False,
                "action_type": "unknown",
                "redirect_url": "/search",
                "screen_data": {
                    "original_query": query,
                    "help_examples": [
                        f"{available_contacts[0]} 10만원 보내줘" if available_contacts else "홍길동 10만원 보내줘",
                        "김철수에게 5만원",
                        "엄마 용돈 보내기"
                    ]
                },
                "confidence": confidence,
                "message": "송금할 사람의 이름을 알려주세요.",
                "suggestions": [f"{name} 송금" for name in available_contacts[:3]] if available_contacts else ["최근 송금 내역"]
            }

        # 거래내역에서 해당 이름의 계좌 정보 찾기
        contact_info = self._get_contact_from_transactions(person_name)

        if not contact_info:
            available_contacts = self._get_all_transfer_contacts()
            return {
                "success": False,
                "action_type": "unknown",
                "redirect_url": "/search",
                "screen_data": {
                    "original_query": query,
                    "available_contacts": available_contacts
                },
                "confidence": confidence,
                "message": f"{person_name}님에게 송금한 기록이 없습니다.",
                "suggestions": [
                                   "계좌 직접 입력",
                                   "연락처에서 찾기"
                               ] + ([f"{name} 송금" for name in available_contacts[:2]] if available_contacts else [])
            }

        # 성공적인 송금 응답
        screen_data = {
            "recipient_name": contact_info["name"],
            "recipient_account": contact_info["account"],
            "recipient_bank": contact_info["bank"],
            "currency": "KRW",
            "last_transfer_date": contact_info.get("last_transfer_date"),
            "last_transfer_amount": contact_info.get("last_transfer_amount")
        }

        # 금액이 있으면 추가
        if amount:
            screen_data["amount"] = amount

        message = f"{contact_info['name']}님에게"
        if amount:
            message += f" {amount:,}원을"
        message += " 송금하시겠습니까?"

        return {
            "success": True,
            "action_type": "transfer",
            "redirect_url": "/transfer",
            "screen_data": screen_data,
            "confidence": confidence,
            "message": message,
            "suggestions": ["금액 수정", "메모 추가", "송금 내역 확인"]
        }

    def _handle_search_intent(self, entities: Dict[str, Any], confidence: float, query: str) -> Dict[str, Any]:
        """조회 의도 처리"""
        merchant = entities.get("merchant")
        person_name = entities.get("person")
        date_range = entities.get("date_range")  # Gemini가 추출한 날짜 범위 객체

        # 기본 필터
        filter_data = {
            "merchant": None,
            "recipient": None,
            "type": "all"
        }

        transactions = []
        message = ""

        # 기간별 검색 (Gemini가 date_range를 추출한 경우)
        if date_range and isinstance(date_range, dict):
            return self._handle_gemini_period_search(date_range, entities, confidence, query)

        # 기간 관련 검색 처리 (폴백)
        if self._is_period_query(query):
            return self._handle_period_search(query, confidence)

        # 가맹점별 조회 (스타벅스, 마트 등)
        if merchant:
            transactions = [t for t in MOCK_TRANSACTIONS if merchant in t["description"]]
            filter_data["merchant"] = merchant
            message = f"{merchant} 거래내역을 찾았습니다."

        # 사람별 송금 내역 조회
        elif person_name:
            transactions = [t for t in MOCK_TRANSACTIONS
                            if t["type"] == "withdrawal" and person_name in t["description"]]
            filter_data["recipient"] = person_name
            message = f"{person_name}님과의 송금내역을 찾았습니다."

        # 거래 타입별 조회 (입금/출금)
        elif "입금" in query:
            transactions = [t for t in MOCK_TRANSACTIONS if t["type"] == "deposit"]
            filter_data["type"] = "deposit"
            message = "입금내역을 조회했습니다."

        elif "출금" in query or "송금" in query:
            transactions = [t for t in MOCK_TRANSACTIONS if t["type"] == "withdrawal"]
            filter_data["type"] = "withdrawal"
            message = "출금내역을 조회했습니다."

        # 기본: 최근 거래내역
        else:
            transactions = MOCK_TRANSACTIONS[:10]  # 최근 10건
            message = "최근 거래내역입니다."

        return {
            "success": True,
            "action_type": "search",
            "redirect_url": "/history",
            "screen_data": {
                "transactions": transactions,
                "filter": filter_data,
                "total_count": len(transactions)
            },
            "confidence": confidence,
            "message": message,
            "suggestions": ["기간별 조회", "카테고리별 조회", "금액별 조회"]
        }

    def _handle_gemini_period_search(self, date_range: Dict[str, Any], entities: Dict[str, Any], confidence: float,
                                     query: str) -> Dict[str, Any]:
        """Gemini가 추출한 기간 정보로 검색 처리"""
        start_date = date_range.get("start_date")
        end_date = date_range.get("end_date")
        period_description = date_range.get("description", "지정 기간")

        if not start_date or not end_date:
            # 날짜 정보가 불완전하면 폴백 처리
            return self._handle_period_search(query, confidence)

        # 거래 타입 확인 (Gemini가 추출한 것 우선 사용)
        transaction_type = "all"
        gemini_transaction_type = entities.get("transaction_type")

        if gemini_transaction_type:
            if gemini_transaction_type == "입금":
                transaction_type = "deposit"
            elif gemini_transaction_type == "출금":
                transaction_type = "withdrawal"
        else:
            # Gemini가 추출하지 못한 경우 키워드로 판단
            if "입금" in query:
                transaction_type = "deposit"
            elif "출금" in query or "송금" in query:
                transaction_type = "withdrawal"

        # 거래내역 필터링
        filtered_transactions = []
        try:
            for t in MOCK_TRANSACTIONS:
                t_date = datetime.strptime(t["date"], "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                # 날짜 범위 확인
                if start_dt <= t_date <= end_dt:
                    # 거래 타입 확인
                    if transaction_type == "all":
                        filtered_transactions.append(t)
                    elif transaction_type == "deposit" and t["type"] == "deposit":
                        filtered_transactions.append(t)
                    elif transaction_type == "withdrawal" and t["type"] == "withdrawal":
                        filtered_transactions.append(t)

        except ValueError as e:
            print(f"❌ 날짜 파싱 에러: {e}")
            # 에러 시 폴백 처리
            return self._handle_period_search(query, confidence)

        # 응답 생성
        filter_data = {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "period_type": date_range.get("period_type", "custom"),
                "description": period_description
            },
            "type": transaction_type,
            "merchant": None,
            "recipient": None
        }

        # 거래 타입에 따른 메시지 생성
        type_text = ""
        if transaction_type == "deposit":
            type_text = " 입금"
        elif transaction_type == "withdrawal":
            type_text = " 출금"

        message = f"{period_description}{type_text}내역을 조회했습니다."

        print(f"🔍 필터링 결과: {len(filtered_transactions)}건 (타입: {transaction_type})")

        return {
            "success": True,
            "action_type": "search",
            "redirect_url": "/history",
            "screen_data": {
                "transactions": filtered_transactions,
                "filter": filter_data,
                "total_count": len(filtered_transactions)
            },
            "confidence": confidence,
            "message": message,
            "suggestions": ["월별 요약", "카테고리별 분석", "지출 패턴 보기"]
        }

    def _handle_period_search(self, query: str, confidence: float) -> Dict[str, Any]:
        """기간별 검색 처리"""
        today = datetime.now()
        start_date = None
        end_date = today.strftime("%Y-%m-%d")
        period_description = ""

        # 기간 파싱
        if "최근" in query:
            if "1주일" in query or "일주일" in query:
                start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
                period_description = "최근 1주일"
            elif "1개월" in query or "한달" in query:
                start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
                period_description = "최근 1개월"
            elif "3개월" in query:
                start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
                period_description = "최근 3개월"
            elif "6개월" in query:
                start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                period_description = "최근 6개월"

        elif "1월" in query:
            start_date = "2025-01-01"
            end_date = "2025-01-31"
            period_description = "2025년 1월"
        elif "지난달" in query:
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1).strftime("%Y-%m-%d")
            end_date = last_month.strftime("%Y-%m-%d")
            period_description = f"{last_month.year}년 {last_month.month}월"

        # 기본값 설정
        if not start_date:
            start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            period_description = "최근 1개월"

        # 거래 타입 확인
        transaction_type = "all"
        if "입금" in query:
            transaction_type = "deposit"
        elif "출금" in query or "송금" in query:
            transaction_type = "withdrawal"

        # 거래내역 필터링
        filtered_transactions = []
        for t in MOCK_TRANSACTIONS:
            t_date = datetime.strptime(t["date"], "%Y-%m-%d")
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            if start_dt <= t_date <= end_dt:
                if transaction_type == "all" or t["type"] == transaction_type:
                    filtered_transactions.append(t)

        # 응답 생성
        filter_data = {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "period_type": "custom",
                "description": period_description
            },
            "type": transaction_type,
            "merchant": None,
            "recipient": None
        }

        type_text = ""
        if transaction_type == "deposit":
            type_text = " 입금"
        elif transaction_type == "withdrawal":
            type_text = " 출금"

        message = f"{period_description}{type_text}내역을 조회했습니다."

        return {
            "success": True,
            "action_type": "search",
            "redirect_url": "/history",
            "screen_data": {
                "transactions": filtered_transactions,
                "filter": filter_data,
                "total_count": len(filtered_transactions)
            },
            "confidence": confidence,
            "message": message,
            "suggestions": ["월별 요약", "카테고리별 분석", "지출 패턴 보기"]
        }

    def _is_period_query(self, query: str) -> bool:
        """기간 관련 검색인지 판단"""
        period_keywords = [
            "최근", "지난", "이번", "1주일", "일주일", "1개월", "한달", "3개월", "6개월",
            "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월",
            "지난달", "이번달", "작년", "올해"
        ]
        return any(keyword in query for keyword in period_keywords)

    def _handle_menu_intent(self, entities: Dict[str, Any], confidence: float, query: str) -> Dict[str, Any]:
        """메뉴 의도 처리"""

        # 1. 먼저 Gemini가 분석한 menu_type 확인
        menu_type = entities.get("menu_type")

        if menu_type:
            # Gemini 분석 결과에 따른 정확한 라우팅
            menu_routes = {
                "exchange": {
                    "url": "/exchange",
                    "message": "환전 화면으로 이동합니다.",
                    "suggestions": ["환율 확인", "환전 신청", "환전 내역"]
                },
                "exchangeCalculator": {
                    "url": "/exchangeCalculator",
                    "message": "환율계산기 화면으로 이동합니다.",
                    "suggestions": ["실시간 환율", "통화 변환", "환전 신청"]
                },
                "exchangeAlerts": {
                    "url": "/exchangeAlerts",
                    "message": "환율알림설정 화면으로 이동합니다.",
                    "suggestions": ["알림 추가", "알림 관리", "환율 확인"]
                },
                "cardApplication": {
                    "url": "/cardApplication",
                    "message": "카드 신청 화면으로 이동합니다.",
                    "suggestions": ["카드 혜택 보기", "신청 자격 확인", "발급 현황"]
                },
                "loan": {
                    "url": "/loan",
                    "message": "대출관리 화면으로 이동합니다.",
                    "suggestions": ["대출 현황", "서류 조회", "이자 계산"]
                },
                "loanDocuments": {
                    "url": "/loanDocuments",
                    "message": "대출서류조회 화면으로 이동합니다.",
                    "suggestions": ["계약서 다운로드", "증명서 발급", "서류 목록"]
                },
                "loanCalculator": {
                    "url": "/loanCalculator",
                    "message": "대출이자계산기 화면으로 이동합니다.",
                    "suggestions": ["이자 계산", "상환 계획", "대출 상품"]
                },
                "history": {
                    "url": "/history",
                    "message": "입출금내역 화면으로 이동합니다.",
                    "suggestions": ["기간별 조회", "거래 필터", "내역 다운로드"]
                },
                "transfer": {
                    "url": "/transfer",
                    "message": "송금 화면으로 이동합니다.",
                    "suggestions": ["받는분 입력", "금액 설정", "이체 한도"]
                }
            }

            route_info = menu_routes.get(menu_type)
            if route_info:
                print(f"✅ Gemini 분석 결과 사용: {menu_type} → {route_info['url']}")
                return {
                    "success": True,
                    "action_type": "menu",
                    "redirect_url": route_info["url"],
                    "screen_data": {"menu_type": menu_type},
                    "confidence": confidence,
                    "message": route_info["message"],
                    "suggestions": route_info["suggestions"]
                }

        # 2. Gemini 분석이 없거나 실패한 경우 기존 키워드 매칭 사용 (폴백)
        print(f"⚠️ Gemini menu_type 없음, 키워드 매칭 사용")

        # 환율알림 관련 (우선순위 높임)
        if any(keyword in query for keyword in ["환율알림", "환율 알림", "알림설정", "환율 설정"]):
            return {
                "success": True,
                "action_type": "menu",
                "redirect_url": "/exchangeAlerts",
                "screen_data": {},
                "confidence": confidence,
                "message": "환율알림설정 화면으로 이동합니다.",
                "suggestions": ["알림 추가", "알림 관리", "환율 확인"]
            }

        # 환율계산기 관련
        elif any(keyword in query for keyword in ["환율계산", "환율 계산", "계산기", "환전 계산"]):
            return {
                "success": True,
                "action_type": "menu",
                "redirect_url": "/exchangeCalculator",
                "screen_data": {},
                "confidence": confidence,
                "message": "환율계산기 화면으로 이동합니다.",
                "suggestions": ["실시간 환율", "통화 변환", "환전 신청"]
            }

        # 환전 관련 (우선순위 낮춤)
        elif any(keyword in query for keyword in ["환전", "달러", "엔화", "유로", "외화"]):
            return {
                "success": True,
                "action_type": "menu",
                "redirect_url": "/exchange",
                "screen_data": {},
                "confidence": confidence,
                "message": "환전 화면으로 이동합니다.",
                "suggestions": ["환율 확인", "환전 신청", "환전 내역"]
            }

        # 나머지 메뉴들...
        elif any(keyword in query for keyword in ["카드", "체크카드", "신용카드", "카드신청"]):
            return {
                "success": True,
                "action_type": "menu",
                "redirect_url": "/cardApplication",
                "screen_data": {},
                "confidence": confidence,
                "message": "카드 신청 화면으로 이동합니다.",
                "suggestions": ["카드 혜택 보기", "신청 자격 확인", "발급 현황"]
            }

        # 기타 등등...
        else:
            return {
                "success": True,
                "action_type": "menu",
                "redirect_url": "/settings",
                "screen_data": {
                    "menu_category": "기타",
                    "original_query": query
                },
                "confidence": confidence,
                "message": "관련 메뉴로 이동합니다.",
                "suggestions": ["설정", "고객센터", "도움말"]
            }

    def _handle_unknown_intent(self, query: str, confidence: float) -> Dict[str, Any]:
        """알 수 없는 의도 처리"""
        available_contacts = self._get_all_transfer_contacts()

        return {
            "success": False,
            "action_type": "unknown",
            "redirect_url": "/search",
            "screen_data": {
                "original_query": query,
                "recent_contacts": available_contacts[:3],  # 상위 3개만
                "help_examples": [
                    f"{available_contacts[0]} 10만원 보내줘" if available_contacts else "홍길동 10만원 보내줘",
                    "스타벅스 거래내역",
                    "최근 3개월 출금내역",
                    "환전하기",
                    "카드 신청"
                ]
            },
            "confidence": confidence,
            "message": "죄송합니다. 요청을 이해하지 못했습니다.",
            "suggestions": (
                               [f"{name} 송금" for name in available_contacts[:2]] if available_contacts else []
                           ) + [
                               "거래내역 조회",
                               "환전 신청",
                               "카드 관리"
                           ]
        }

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