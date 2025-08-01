import re
import spacy
from typing import Dict, Any, List, Optional


class NLPService:
    def __init__(self):
        # spaCy 한국어 모델 로드 (실패시 정규식만 사용)
        try:
            self.nlp = spacy.load("ko_core_news_sm")
            self.use_spacy = True
            print("✅ spaCy 한국어 모델 로드 성공")
        except Exception as e:
            self.nlp = None
            self.use_spacy = False
            print(f"⚠️ spaCy 모델 로드 실패: {e}")
            print("📝 정규식 패턴만 사용합니다")

        # 키워드 풀
        self.transfer_keywords = ["보내", "송금", "이체", "만원", "원", "줘", "보내줘"]
        self.search_keywords = ["내역", "거래", "조회", "언제", "얼마", "부터", "까지"]
        self.menu_keywords = ["설정", "막기", "해제", "등록", "변경", "어떻게"]

        # 금액 패턴
        self.amount_patterns = [
            r'(\d+)만원',
            r'(\d+)만',
            r'(\d{1,3}(?:,\d{3})*)원',
            r'(\d+)원'
        ]

        # 가맹점 패턴 (나중에 확장 가능)
        self.merchant_patterns = ["스타벅스", "무신사", "GS25", "이마트", "교촌치킨", "맥도날드", "올리브영", "다이소"]

    def parse_query(self, text: str) -> Dict[str, Any]:
        """메인 파싱 함수 - spaCy + 정규식 조합"""
        # 1. spaCy로 기본 개체명 추출
        spacy_entities = self._extract_with_spacy(text) if self.use_spacy else {}

        # 2. 정규식으로 보완 추출
        regex_entities = self._extract_with_regex(text)

        # 3. 두 결과 병합 (정규식 우선 - 더 정확함)
        entities = self._merge_entities(spacy_entities, regex_entities)

        # 4. 의도 분류
        intent = self.classify_intent(text, entities)

        # 5. 신뢰도 계산
        confidence = self.calculate_confidence(intent, entities, text)

        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "original_text": text,
            "used_spacy": self.use_spacy
        }

    def _extract_with_spacy(self, text: str) -> Dict[str, Any]:
        """spaCy로 개체명 추출"""
        if not self.use_spacy:
            return {}

        doc = self.nlp(text)
        entities = {
            "person": None,
            "amount": None,
            "raw_amount": None,
            "merchant": None,
            "date": None,
            "money_entities": [],
            "person_entities": []
        }

        # spaCy 개체명 인식 결과
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["person_entities"].append(ent.text)
                if not entities["person"]:  # 첫 번째 사람명 사용
                    entities["person"] = ent.text

            elif ent.label_ == "MONEY":
                entities["money_entities"].append(ent.text)
                # 금액 정규화 시도
                normalized = self._normalize_spacy_money(ent.text)
                if normalized and not entities["amount"]:
                    entities["amount"] = normalized
                    entities["raw_amount"] = ent.text

            elif ent.label_ == "ORG":
                # 조직명이 가맹점일 수 있음
                if not entities["merchant"]:
                    entities["merchant"] = ent.text

            elif ent.label_ == "DATE":
                if not entities["date"]:
                    entities["date"] = ent.text

        return entities

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """정규식으로 개체명 추출 (기존 로직)"""
        entities = {
            "person": None,
            "amount": None,
            "raw_amount": None,
            "merchant": None,
            "date": None,
            "action": None
        }

        # 금액 추출
        entities.update(self._extract_amount(text))

        # 이름 추출 (한국어 이름 패턴)
        entities["person"] = self._extract_person_name(text)

        # 가맹점 추출
        entities["merchant"] = self._extract_merchant(text)

        # 날짜 표현 추출
        entities["date"] = self._extract_date(text)

        # 액션 추출
        entities["action"] = self._extract_action(text)

        return entities

    def _merge_entities(self, spacy_entities: Dict, regex_entities: Dict) -> Dict[str, Any]:
        """spaCy와 정규식 결과 병합 (정규식 우선)"""
        merged = {}

        # 정규식 결과를 기본으로 사용
        for key, value in regex_entities.items():
            merged[key] = value

        # spaCy 결과로 보완 (정규식에서 못 찾은 것만)
        for key, value in spacy_entities.items():
            if key not in merged or merged[key] is None:
                merged[key] = value

        # spaCy 고유 정보도 보존
        if "person_entities" in spacy_entities:
            merged["spacy_persons"] = spacy_entities["person_entities"]
        if "money_entities" in spacy_entities:
            merged["spacy_money"] = spacy_entities["money_entities"]

        return merged

    def _normalize_spacy_money(self, money_text: str) -> Optional[int]:
        """spaCy가 찾은 금액 정규화"""
        try:
            # "10만원", "100000원" 등을 숫자로 변환
            if "만" in money_text:
                number = re.findall(r'(\d+)', money_text)
                if number:
                    return int(number[0]) * 10000
            else:
                number = re.findall(r'(\d+)', money_text.replace(',', ''))
                if number:
                    return int(number[0])
        except:
            pass
        return None

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """호환성을 위한 기존 메서드"""
        return self.parse_query(text)["entities"]

    def classify_intent(self, text: str, entities: Dict[str, Any]) -> str:
        """의도 분류 (기존 로직 유지)"""
        # 송금 의도: 사람명 + 금액 또는 송금 키워드
        if self._is_transfer_intent(text, entities):
            return "transfer"

        # 조회 의도: 조회 키워드 또는 가맹점명
        if self._is_search_intent(text, entities):
            return "search"

        # 메뉴 의도: 설정 관련 키워드
        if self._is_menu_intent(text, entities):
            return "menu"

        return "unknown"

    def calculate_confidence(self, intent: str, entities: Dict[str, Any], text: str) -> float:
        """신뢰도 계산 - spaCy 사용시 보너스"""
        confidence = 0.5  # 기본 신뢰도

        # 의도별 가중치
        if intent == "transfer":
            if entities.get("person") and entities.get("amount"):
                confidence = 0.9  # 이름 + 금액 = 높은 신뢰도
                # spaCy가 둘 다 찾았으면 보너스
                if (self.use_spacy and
                        entities.get("spacy_persons") and
                        entities.get("spacy_money")):
                    confidence = min(0.95, confidence + 0.05)
            elif entities.get("person") or entities.get("amount"):
                confidence = 0.7  # 하나만 있으면 중간 신뢰도

        elif intent == "search":
            if entities.get("merchant"):
                confidence = 0.8  # 가맹점명 있으면 높은 신뢰도
            elif any(keyword in text for keyword in self.search_keywords):
                confidence = 0.7

        elif intent == "menu":
            if any(keyword in text for keyword in self.menu_keywords):
                confidence = 0.8

        # spaCy 사용시 전체적으로 신뢰도 약간 증가
        if self.use_spacy and confidence > 0.5:
            confidence = min(1.0, confidence + 0.05)

        return confidence

    # 기존 정규식 메서드들 (그대로 유지)
    def _extract_amount(self, text: str) -> Dict[str, Any]:
        """금액 추출"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text)
            if match:
                raw_amount = match.group(1)
                normalized_amount = self._normalize_amount(raw_amount, pattern)
                return {
                    "raw_amount": raw_amount,
                    "amount": normalized_amount
                }

        return {"raw_amount": None, "amount": None}

    def _extract_person_name(self, text: str) -> Optional[str]:
        """이름 추출"""
        # 한국어 이름 패턴 (2-4글자)
        name_patterns = [
            r'([가-힣]{2,4})(?:에게|한테|님|씨)',  # "김네모에게", "엄마님"
            r'([가-힣]{2,4})(?=\s|$|[0-9])',  # "김네모 10만원"
        ]

        possible_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            possible_names.extend(matches)

        # 중복 제거 및 일반적이지 않은 단어 필터링
        excluded_words = {"만원", "거래", "내역", "송금", "이체", "조회", "설정", "해외", "결제"}

        for name in possible_names:
            if name not in excluded_words and len(name) >= 2:
                return name

        return None

    def _extract_merchant(self, text: str) -> Optional[str]:
        """가맹점 추출"""
        for merchant in self.merchant_patterns:
            if merchant in text:
                return merchant

        # 추가 패턴 (카페, 마트 등)
        merchant_suffix_patterns = [
            r'([가-힣]+카페)',
            r'([가-힣]+마트)',
            r'([가-힣]+치킨)',
        ]

        for pattern in merchant_suffix_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """날짜 표현 추출"""
        date_patterns = [
            r'(\d{1,2}월)',
            r'(어제|오늘|내일)',
            r'(지난주|이번주|다음주)',
            r'(지난달|이번달|다음달)',
            r'(\d{1,2}일)',
            r'(\d+일전)',
            r'(\d+주전)',
            r'(\d+개월전)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_action(self, text: str) -> Optional[str]:
        """액션 추출"""
        action_patterns = {
            "send": ["보내", "송금", "이체", "줘"],
            "search": ["조회", "찾아", "보여", "알려"],
            "block": ["막아", "막기", "차단"],
            "set": ["설정", "등록", "변경"],
        }

        for action_type, keywords in action_patterns.items():
            if any(keyword in text for keyword in keywords):
                return action_type

        return None

    def _is_transfer_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """송금 의도인지 판단"""
        # 명확한 조건: 사람명 + 금액
        if entities.get("person") and entities.get("amount"):
            return True

        # 송금 키워드 포함
        if any(keyword in text for keyword in self.transfer_keywords):
            return True

        return False

    def _is_search_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """조회 의도인지 판단"""
        # 가맹점명이 있으면 거래내역 조회
        if entities.get("merchant"):
            return True

        # 조회 키워드 포함
        if any(keyword in text for keyword in self.search_keywords):
            return True

        # 날짜 표현이 있으면 조회 가능성 높음
        if entities.get("date") and not entities.get("person"):
            return True

        return False

    def _is_menu_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """메뉴 의도인지 판단"""
        # 메뉴/설정 키워드 포함
        if any(keyword in text for keyword in self.menu_keywords):
            return True

        # 특정 기능 키워드 (해외결제, 자동이체 등)
        menu_specific_keywords = ["해외결제", "자동이체", "알림", "한도", "비밀번호", "인증"]
        if any(keyword in text for keyword in menu_specific_keywords):
            return True

        return False

    def _normalize_amount(self, raw_amount: str, pattern: str) -> int:
        """금액 정규화"""
        try:
            number = int(raw_amount.replace(',', ''))

            # "만원" 패턴이면 10000 곱하기
            if "만" in pattern:
                return number * 10000
            else:
                return number
        except ValueError:
            return 0

    def get_extracted_info_summary(self, parsed_result: Dict[str, Any]) -> str:
        """파싱 결과 요약 (디버깅용)"""
        entities = parsed_result["entities"]
        intent = parsed_result["intent"]
        confidence = parsed_result["confidence"]
        used_spacy = parsed_result.get("used_spacy", False)

        summary_parts = [
            f"의도: {intent} (신뢰도: {confidence:.2f})",
            f"NLP: {'spaCy+정규식' if used_spacy else '정규식만'}"
        ]

        if entities.get("person"):
            summary_parts.append(f"사람: {entities['person']}")

        if entities.get("amount"):
            summary_parts.append(f"금액: {entities['amount']:,}원")

        if entities.get("merchant"):
            summary_parts.append(f"가맹점: {entities['merchant']}")

        if entities.get("date"):
            summary_parts.append(f"날짜: {entities['date']}")

        # spaCy 추가 정보
        if used_spacy:
            if entities.get("spacy_persons"):
                summary_parts.append(f"spaCy 사람: {entities['spacy_persons']}")
            if entities.get("spacy_money"):
                summary_parts.append(f"spaCy 금액: {entities['spacy_money']}")

        return " | ".join(summary_parts)

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """텍스트에서 개체명 추출"""
        entities = {
            "person": None,
            "amount": None,
            "raw_amount": None,
            "merchant": None,
            "date": None,
            "action": None
        }

        # 금액 추출
        entities.update(self._extract_amount(text))

        # 이름 추출 (한국어 이름 패턴)
        entities["person"] = self._extract_person_name(text)

        # 가맹점 추출
        entities["merchant"] = self._extract_merchant(text)

        # 날짜 표현 추출
        entities["date"] = self._extract_date(text)

        # 액션 추출
        entities["action"] = self._extract_action(text)

        return entities

    def classify_intent(self, text: str, entities: Dict[str, Any]) -> str:
        """의도 분류"""
        # 송금 의도: 사람명 + 금액 또는 송금 키워드
        if self._is_transfer_intent(text, entities):
            return "transfer"

        # 조회 의도: 조회 키워드 또는 가맹점명
        if self._is_search_intent(text, entities):
            return "search"

        # 메뉴 의도: 설정 관련 키워드
        if self._is_menu_intent(text, entities):
            return "menu"

        return "unknown"

    def calculate_confidence(self, intent: str, entities: Dict[str, Any], text: str) -> float:
        """신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도

        # 의도별 가중치
        if intent == "transfer":
            if entities["person"] and entities["amount"]:
                confidence = 0.9  # 이름 + 금액 = 높은 신뢰도
            elif entities["person"] or entities["amount"]:
                confidence = 0.7  # 하나만 있으면 중간 신뢰도

        elif intent == "search":
            if entities["merchant"]:
                confidence = 0.8  # 가맹점명 있으면 높은 신뢰도
            elif any(keyword in text for keyword in self.search_keywords):
                confidence = 0.7

        elif intent == "menu":
            if any(keyword in text for keyword in self.menu_keywords):
                confidence = 0.8

        return min(confidence, 1.0)

    def _extract_amount(self, text: str) -> Dict[str, Any]:
        """금액 추출"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text)
            if match:
                raw_amount = match.group(1)
                normalized_amount = self._normalize_amount(raw_amount, pattern)
                return {
                    "raw_amount": raw_amount,
                    "amount": normalized_amount
                }

        return {"raw_amount": None, "amount": None}

    def _extract_person_name(self, text: str) -> Optional[str]:
        """이름 추출"""
        # 한국어 이름 패턴 (2-4글자)
        name_patterns = [
            r'([가-힣]{2,4})(?:에게|한테|님|씨)',  # "김네모에게", "엄마님"
            r'([가-힣]{2,4})(?=\s|$|[0-9])',  # "김네모 10만원"
        ]

        possible_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            possible_names.extend(matches)

        # 중복 제거 및 일반적이지 않은 단어 필터링
        excluded_words = {"만원", "거래", "내역", "송금", "이체", "조회", "설정", "해외", "결제"}

        for name in possible_names:
            if name not in excluded_words and len(name) >= 2:
                return name

        return None

    def _extract_merchant(self, text: str) -> Optional[str]:
        """가맹점 추출"""
        for merchant in self.merchant_patterns:
            if merchant in text:
                return merchant

        # 추가 패턴 (카페, 마트 등)
        merchant_suffix_patterns = [
            r'([가-힣]+카페)',
            r'([가-힣]+마트)',
            r'([가-힣]+치킨)',
        ]

        for pattern in merchant_suffix_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """날짜 표현 추출"""
        date_patterns = [
            r'(\d{1,2}월)',
            r'(어제|오늘|내일)',
            r'(지난주|이번주|다음주)',
            r'(지난달|이번달|다음달)',
            r'(\d{1,2}일)',
            r'(\d+일전)',
            r'(\d+주전)',
            r'(\d+개월전)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_action(self, text: str) -> Optional[str]:
        """액션 추출"""
        action_patterns = {
            "send": ["보내", "송금", "이체", "줘"],
            "search": ["조회", "찾아", "보여", "알려"],
            "block": ["막아", "막기", "차단"],
            "set": ["설정", "등록", "변경"],
        }

        for action_type, keywords in action_patterns.items():
            if any(keyword in text for keyword in keywords):
                return action_type

        return None

    def _is_transfer_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """송금 의도인지 판단"""
        # 명확한 조건: 사람명 + 금액
        if entities["person"] and entities["amount"]:
            return True

        # 송금 키워드 포함
        if any(keyword in text for keyword in self.transfer_keywords):
            return True

        return False

    def _is_search_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """조회 의도인지 판단"""
        # 가맹점명이 있으면 거래내역 조회
        if entities["merchant"]:
            return True

        # 조회 키워드 포함
        if any(keyword in text for keyword in self.search_keywords):
            return True

        # 날짜 표현이 있으면 조회 가능성 높음
        if entities["date"] and not entities["person"]:
            return True

        return False

    def _is_menu_intent(self, text: str, entities: Dict[str, Any]) -> bool:
        """메뉴 의도인지 판단"""
        # 메뉴/설정 키워드 포함
        if any(keyword in text for keyword in self.menu_keywords):
            return True

        # 특정 기능 키워드 (해외결제, 자동이체 등)
        menu_specific_keywords = ["해외결제", "자동이체", "알림", "한도", "비밀번호", "인증"]
        if any(keyword in text for keyword in menu_specific_keywords):
            return True

        return False

    def _normalize_amount(self, raw_amount: str, pattern: str) -> int:
        """금액 정규화"""
        try:
            number = int(raw_amount.replace(',', ''))

            # "만원" 패턴이면 10000 곱하기
            if "만" in pattern:
                return number * 10000
            else:
                return number
        except ValueError:
            return 0

    def get_extracted_info_summary(self, parsed_result: Dict[str, Any]) -> str:
        """파싱 결과 요약 (디버깅용)"""
        entities = parsed_result["entities"]
        intent = parsed_result["intent"]
        confidence = parsed_result["confidence"]

        summary_parts = [f"의도: {intent} (신뢰도: {confidence:.2f})"]

        if entities["person"]:
            summary_parts.append(f"사람: {entities['person']}")

        if entities["amount"]:
            summary_parts.append(f"금액: {entities['amount']:,}원")

        if entities["merchant"]:
            summary_parts.append(f"가맹점: {entities['merchant']}")

        if entities["date"]:
            summary_parts.append(f"날짜: {entities['date']}")

        return " | ".join(summary_parts)