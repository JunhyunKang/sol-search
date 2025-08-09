import os
import json
import re
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv  # 추가

# .env 파일 로드 (추가)
load_dotenv()

class IntentAnalysis(BaseModel):
    """의도 분석 결과 모델"""
    intent: str = Field(description="분석된 의도: transfer, search, menu, unknown 중 하나")
    confidence: float = Field(description="신뢰도 (0.0 ~ 1.0)")
    entities: Dict[str, Any] = Field(description="추출된 개체명 정보")
    reasoning: str = Field(description="분석 근거")


class GeminiNLPService:
    def __init__(self):
        # Gemini API 키 설정 (환경변수에서 가져오기)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정해주세요")

        # Gemini 모델 초기화
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # 또는 "models/gemini-2.0-flash"
            google_api_key=self.api_key,
            temperature=0.1,  # 일관성을 위해 낮은 온도 설정
        )

        # 출력 파서 설정
        self.output_parser = PydanticOutputParser(pydantic_object=IntentAnalysis)

        # 프롬프트 템플릿 설정
        self.prompt_template = self._create_prompt_template()

    def _create_prompt_template(self) -> PromptTemplate:
        """의도 분석을 위한 프롬프트 템플릿 생성"""

        format_instructions = self.output_parser.get_format_instructions()

        template = """
당신은 한국의 은행 앱 자연어 검색 시스템의 의도 분석 전문가입니다.
사용자의 검색어를 분석하여 정확한 의도와 개체명을 추출해주세요.
사용자 검색어의 의도를 파악해 아래 의도분류에 따라 분류하고, 필요한 개체명을 추출합니다.

## 의도 분류 (intent):
1. **transfer**: 송금/이체 관련
   - 예시: "홍길동 10만원 보내줘", "김철수에게 송금", "박민수 5천원"
   - 특징: 사람 이름 + 금액, 또는 송금/이체 키워드

2. **search**: 거래내역/조회 관련  
   - 예시: "거래내역", "최근 3개월 출금내역", "1월 입금내역"
   - 특징: 내역, 조회, 가맹점명, 기간 표현

3. **menu**: 특정 메뉴 페이지로 이동
   - 구현된 페이지들:
     * 환전: "환전", "달러 환율"
     * 환율계산기: "환율계산", "환율 계산기"  
     * 환율알림: "환율알림", "환율 알림설정"
     * 카드신청: "카드신청", "체크카드"
     * 대출관리: "대출", "대출조회"
     * 대출서류: "대출서류", "계약서"
     * 대출계산기: "대출계산", "이자계산"
     * 입출금내역: "입출금내역", "거래내역"
     * 송금: "계좌이체", "송금하기"

4. **unknown**: 위에 해당하지 않는 경우

## 의도별 개체명 추출 (entities):

### transfer (송금) 시:
- person: 사람 이름 (한글 2-4글자) - 필수
- amount: 금액 (정수 숫자만, 단위 없이. 예: 2000, 50000) - 선택

### search (조회) 시:
- merchant: 가맹점명 (스타벅스, 맥도날드, GS25 등) - 선택
- date_range: 기간 정보 객체 - 선택
  * start_date: 시작일 (YYYY-MM-DD 형식, 예: "2025-08-01")
  * end_date: 종료일 (YYYY-MM-DD 형식, 예: "2025-08-31")  
  * period_type: 기간 유형 ("month", "week", "recent", "custom")
  * description: 기간 설명 (예: "2025년 8월", "최근 1개월")
- transaction_type: 거래 타입 (입금, 출금, 전체) - 선택
- person: 송금 상대방 이름 (송금내역 조회시) - 선택

기간 추출 규칙:
- "8월" → start_date: "2025-08-01", end_date: "2025-08-31", description: "2025년 8월"
- "1월" → start_date: "2025-01-01", end_date: "2025-01-31", description: "2025년 1월"  
- "최근 1개월" → start_date: "2025-07-10", end_date: "2025-08-10", description: "최근 1개월"
- "최근 3개월" → start_date: "2025-05-10", end_date: "2025-08-10", description: "최근 3개월"
- "지난 두달" → start_date: "2025-06-10", end_date: "2025-08-10", description: "지난 두달"
- "지난달" → start_date: "2025-07-01", end_date: "2025-07-31", description: "2025년 7월"
- 현재 날짜는 2025년 8월 10일로 가정하여 계산

### menu (메뉴이동) 시:
- menu_type: 메뉴 종류 - 필수
  * "exchange" - 환전
  * "exchangeCalculator" - 환율계산기
  * "exchangeAlerts" - 환율알림설정
  * "cardApplication" - 카드신청
  * "loan" - 대출관리
  * "loanDocuments" - 대출서류조회
  * "loanCalculator" - 대출이자계산기
  * "history" - 입출금내역
  * "transfer" - 송금

### unknown 시:
- 개체명 추출하지 않음

## 신뢰도 (confidence):
- 0.9~1.0: 매우 확실 (명확한 키워드 + 개체명)
- 0.7~0.8: 확실 (키워드 매칭)
- 0.5~0.6: 보통 (애매한 표현)
- 0.3~0.4: 불확실 (관련성 낮음)
- 0.0~0.2: 매우 불확실

사용자 검색어: "{query}"

분석 결과를 JSON 형태로 정확히 출력해주세요.

{format_instructions}
"""

        return PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions}
        )

    def parse_query(self, text: str) -> Dict[str, Any]:
        """메인 파싱 함수"""
        try:
            # 프롬프트 생성
            prompt = self.prompt_template.format(query=text)

            # Gemini 호출
            response = self.llm.invoke(prompt)

            # 응답 파싱
            try:
                parsed_result = self.output_parser.parse(response.content)

                return {
                    "intent": parsed_result.intent,
                    "entities": parsed_result.entities,
                    "confidence": parsed_result.confidence,
                    "reasoning": parsed_result.reasoning,
                    "original_text": text,
                    "used_model": "gemini-pro"
                }
            except Exception as parse_error:
                print(f"파싱 에러, 폴백 처리: {parse_error}")
                return self._fallback_parse(text)

        except Exception as e:
            print(f"Gemini API 에러, 폴백 처리: {e}")
            return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Gemini 실패 시 폴백 처리 (기존 정규식 로직)"""

        # 간단한 규칙 기반 분류
        intent = "unknown"
        confidence = 0.5
        entities = {}

        # 송금 패턴 체크
        if self._check_transfer_pattern(text):
            intent = "transfer"
            confidence = 0.7
            entities = self._extract_transfer_entities(text)

        # 조회 패턴 체크
        elif self._check_search_pattern(text):
            intent = "search"
            confidence = 0.6
            entities = self._extract_search_entities(text)

        # 메뉴 패턴 체크
        elif self._check_menu_pattern(text):
            intent = "menu"
            confidence = 0.6
            entities = self._extract_menu_entities(text)

        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "reasoning": "폴백 처리 (정규식 기반)",
            "original_text": text,
            "used_model": "fallback"
        }

    def _check_transfer_pattern(self, text: str) -> bool:
        """송금 패턴 체크"""
        transfer_keywords = ["보내", "송금", "이체", "만원", "원", "줘"]
        name_pattern = r'[가-힣]{2,4}'

        return (any(keyword in text for keyword in transfer_keywords) or
                bool(re.search(name_pattern, text)))

    def _check_search_pattern(self, text: str) -> bool:
        """조회 패턴 체크"""
        search_keywords = ["내역", "거래", "조회", "결제", "출금", "입금"]
        return any(keyword in text for keyword in search_keywords)

    def _check_menu_pattern(self, text: str) -> bool:
        """메뉴 패턴 체크"""
        menu_keywords = ["환전", "카드", "대출", "계산", "알림"]
        return any(keyword in text for keyword in menu_keywords)

    def _extract_transfer_entities(self, text: str) -> Dict[str, Any]:
        """송금 개체명 추출"""
        entities = {}

        # 이름 추출 (필수)
        name_match = re.search(r'([가-힣]{2,4})(?:에게|한테|님)?', text)
        if name_match:
            entities["person"] = name_match.group(1)

        # 금액 추출 (선택)
        amount_patterns = [r'(\d+)만원?', r'(\d{1,3}(?:,\d{3})*)원?']
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                raw_amount = match.group(1).replace(',', '')
                if '만' in pattern:
                    entities["amount"] = int(raw_amount) * 10000
                else:
                    entities["amount"] = int(raw_amount)
                break

        return entities

    def _extract_search_entities(self, text: str) -> Dict[str, Any]:
        """조회 개체명 추출"""
        entities = {}

        # 가맹점 추출
        merchants = ["스타벅스", "맥도날드", "이마트", "GS25", "교촌치킨", "무신사"]
        for merchant in merchants:
            if merchant in text:
                entities["merchant"] = merchant
                break

        # 기간 추출
        date_patterns = ["최근", "지난", "이번", "1월", "2월", "3월", "개월", "주일", "어제", "오늘"]
        for pattern in date_patterns:
            if pattern in text:
                entities["date"] = pattern
                break

        # 거래 타입 추출
        if "입금" in text:
            entities["transaction_type"] = "deposit"
        elif "출금" in text or "송금" in text:
            entities["transaction_type"] = "withdrawal"
        else:
            entities["transaction_type"] = "all"

        # 송금내역 조회시 상대방 이름
        if "송금" in text or "이체" in text:
            name_match = re.search(r'([가-힣]{2,4})(?:에게|한테|님)?', text)
            if name_match:
                entities["person"] = name_match.group(1)

        return entities

    def _extract_menu_entities(self, text: str) -> Dict[str, Any]:
        """메뉴 개체명 추출"""
        entities = {}

        # 메뉴 타입 매핑 (우선순위 순서)
        menu_mapping = [
            (["환율계산", "환율 계산", "계산기"], "exchangeCalculator"),
            (["환율알림", "환율 알림", "알림설정"], "exchangeAlerts"),
            (["대출서류", "대출 서류", "계약서", "서류조회"], "loanDocuments"),
            (["대출계산", "대출 계산", "이자계산", "이자 계산"], "loanCalculator"),
            (["카드신청", "카드 신청", "체크카드", "신용카드"], "cardApplication"),
            (["입출금내역", "거래내역", "내역조회"], "history"),
            (["계좌이체", "송금하기", "이체하기"], "transfer"),
            (["환전", "달러", "유로", "엔화"], "exchange"),
            (["대출", "대출조회", "대출관리"], "loan"),
        ]

        # 우선순위에 따라 매칭
        for keywords, menu_type in menu_mapping:
            if any(keyword in text for keyword in keywords):
                entities["menu_type"] = menu_type
                break

        return entities