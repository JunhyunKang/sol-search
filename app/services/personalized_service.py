import os
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.services.user_service import UserService


class PersonalizedExplanation(BaseModel):
    """맞춤 설명 모델"""
    explanation: str = Field(description="사용자 맞춤 친근한 설명")
    key_points: List[str] = Field(description="핵심 포인트들 (쉬운 언어로)")
    recommendations: List[str] = Field(description="사용자 상황에 맞는 추천사항")
    easy_terms: Dict[str, str] = Field(description="어려운 금융용어의 쉬운 설명")


class PersonalizedService:
    def __init__(self):
        # Gemini API 키 설정
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found, using fallback explanations")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.3,  # 약간의 창의성
            )

        self.user_service = UserService()
        self.output_parser = PydanticOutputParser(pydantic_object=PersonalizedExplanation)

    def get_personalized_explanation(self, product_type: str, product_id: str = None, user_id: str = "default_user") -> \
    Dict[str, Any]:
        """사용자 맞춤형 설명 생성"""

        # 사용자 정보 가져오기
        user_info = self.user_service.get_user_info(user_id)

        # Gemini를 사용할 수 있는 경우
        if self.llm:
            try:
                return self._generate_ai_explanation(product_type, product_id, user_info)
            except Exception as e:
                print(f"Gemini API 오류: {e}")
                return self._generate_fallback_explanation(product_type, product_id, user_info)

        # Fallback 설명
        return self._generate_fallback_explanation(product_type, product_id, user_info)

    def _generate_ai_explanation(self, product_type: str, product_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini를 사용한 맞춤 설명 생성"""

        format_instructions = self.output_parser.get_format_instructions()

        # 상품 정보 정의
        product_info = self._get_product_info(product_type, product_id)

        prompt_template = PromptTemplate(
            template="""
당신은 친근하고 쉽게 설명하는 은행 직원입니다. 
고객의 상황에 맞춰 금융상품을 쉽고 친근하게 설명해주세요.

## 고객 정보:
- 이름: {name} ({age}세, {gender}, {job})
- 계좌 잔액: {balance:,}원

## 설명할 상품:
{product_description}

## 설명 가이드라인:
1. 고객의 이름을 사용해 친근하게 말하기
2. 나이대와 직업을 고려한 맞춤 설명
3. 잔액 수준을 고려한 현실적인 조언
4. 어려운 금융용어는 쉽게 풀어서 설명
5. 구체적인 예시와 비유 사용
6. "~예요", "~해요" 등 친근한 말투 사용

{format_instructions}
""",
            input_variables=["name", "age", "gender", "job", "balance", "product_description"],
            partial_variables={"format_instructions": format_instructions}
        )

        prompt = prompt_template.format(
            name=user_info["name"],
            age=user_info["age"],
            gender=user_info["gender"],
            job=user_info["job"],
            balance=user_info["balance"],
            product_description=product_info
        )

        response = self.llm.invoke(prompt)
        parsed_result = self.output_parser.parse(response.content)

        return {
            "success": True,
            "explanation": parsed_result.explanation,
            "key_points": parsed_result.key_points,
            "recommendations": parsed_result.recommendations,
            "user_context": self._get_user_context(user_info),
            "easy_terms": parsed_result.easy_terms
        }

    def _generate_fallback_explanation(self, product_type: str, product_id: str, user_info: Dict[str, Any]) -> Dict[
        str, Any]:
        """Fallback 맞춤 설명 생성"""

        name = user_info["name"]
        age = user_info["age"]
        job = user_info["job"]
        balance = user_info["balance"]

        if product_type == "card":
            return self._get_card_explanation(name, age, job, balance, product_id)
        elif product_type == "loan":
            return self._get_loan_explanation(name, age, job, balance, product_id)
        else:
            return {
                "success": False,
                "explanation": "해당 상품에 대한 설명을 찾을 수 없어요.",
                "key_points": [],
                "recommendations": [],
                "user_context": self._get_user_context(user_info),
                "easy_terms": {}
            }

    def _get_card_explanation(self, name: str, age: int, job: str, balance: int, product_id: str) -> Dict[str, Any]:
        """카드 상품 설명"""

        age_group = "20대" if age < 30 else "30대" if age < 40 else "40대 이상"

        explanations = {
            "shinhan-check": {
                "explanation": f"{name}님처럼 {age_group} {job}분들이 가장 많이 선택하는 카드예요! 현재 잔액 {balance:,}원 정도면 월 한도 100만원이 딱 적당해요. 연회비도 없어서 부담 없이 시작할 수 있어요.",
                "key_points": [
                    "연회비 무료로 부담 없어요",
                    "온라인 쇼핑할 때 할인 받을 수 있어요",
                    "교통비도 할인되어 돈 절약돼요",
                    "월 한도 100만원으로 적당해요"
                ],
                "recommendations": [
                    "첫 카드로 시작하기 좋아요",
                    "일상 생활용으로 추천해요",
                    f"{age_group} {job}분들이 많이 써요"
                ]
            },
            "shinhan-premium": {
                "explanation": f"{name}님 잔액을 보니 프리미엄 카드도 충분히 관리하실 수 있을 것 같아요! 공항 라운지도 무료로 이용하고, 호텔에서 할인도 받을 수 있어요. 연회비 5만원이지만 혜택을 생각하면 오히려 이득이에요.",
                "key_points": [
                    "공항에서 편안히 쉴 수 있는 라운지 이용 가능",
                    "호텔 예약할 때 할인 받을 수 있어요",
                    "골프장 이용료도 할인돼요",
                    "월 한도 300만원으로 여유로워요"
                ],
                "recommendations": [
                    "여행 자주 다니시면 추천해요",
                    "프리미엄 서비스 경험해보세요",
                    f"{job}분들이 선호하는 카드예요"
                ]
            },
            "shinhan-youth": {
                "explanation": f"{name}님 나이라면 청년 카드가 딱이에요! 영화 보러 갈 때, 카페 갈 때마다 할인받고, 교통비는 아예 무료예요. {age_group}를 위해 특별히 만든 카드라 혜택이 짱이에요!",
                "key_points": [
                    "영화관에서 할인받아요",
                    "카페에서 커피 할인돼요",
                    "교통비 무료로 돈 절약!",
                    "월 한도 50만원으로 적당해요"
                ],
                "recommendations": [
                    f"{age_group}에게 딱 맞는 카드예요",
                    "학생이나 사회초년생에게 추천",
                    "일상 할인 혜택이 많아요"
                ]
            }
        }

        card_info = explanations.get(product_id, explanations["shinhan-check"])

        return {
            "success": True,
            **card_info,
            "user_context": {
                "age_group": age_group,
                "job_category": job,
                "balance_level": "적정" if balance > 1000000 else "보통"
            },
            "easy_terms": {
                "연회비": "카드를 1년 동안 쓰기 위해 내는 돈이에요",
                "한도": "카드로 쓸 수 있는 최대 금액이에요",
                "캐시백": "쓴 돈의 일부를 다시 돌려받는 거예요"
            }
        }

    def _get_loan_explanation(self, name: str, age: int, job: str, balance: int, product_id: str = None) -> Dict[
        str, Any]:
        """대출 상품 설명"""

        age_group = "20대" if age < 30 else "30대" if age < 40 else "40대 이상"

        return {
            "success": True,
            "explanation": f"{name}님처럼 {age_group} {job}분들이 많이 이용하는 대출이에요! 현재 잔액 {balance:,}원을 보니 상환 능력이 충분해 보여요. 금리도 합리적이고 상환 방법도 선택할 수 있어요.",
            "key_points": [
                "금리가 다른 곳보다 낮아요",
                f"{job}분들에게 우대금리 적용돼요",
                "상환 방법을 선택할 수 있어요",
                "중도상환 수수료가 저렴해요"
            ],
            "recommendations": [
                f"{age_group} {job}분들이 많이 이용해요",
                "계획적인 자금 운용에 도움돼요",
                "신용등급 관리에도 좋아요"
            ],
            "user_context": {
                "age_group": age_group,
                "job_category": job,
                "balance_level": "적정" if balance > 1000000 else "보통"
            },
            "easy_terms": {
                "금리": "돈을 빌리는 대가로 내는 이자 비율이에요",
                "원리금균등상환": "매달 같은 금액을 갚는 방식이에요",
                "원금균등상환": "처음엔 많이 갚고 나중엔 적게 갚는 방식이에요",
                "중도상환": "빌린 돈을 미리 다 갚는 거예요"
            }
        }

    def _get_product_info(self, product_type: str, product_id: str) -> str:
        """상품 정보 반환"""

        if product_type == "card":
            card_info = {
                "shinhan-check": "신한 체크카드 - 연회비 없는 기본 체크카드, 온라인 쇼핑몰 할인, 교통비 할인, 월 한도 100만원",
                "shinhan-premium": "신한 프리미엄 체크카드 - 공항라운지 이용, 호텔 할인, 골프장 이용, 연회비 5만원, 월 한도 300만원",
                "shinhan-youth": "신한 청년 체크카드 - 20-30대 전용, 영화관 할인, 카페 할인, 교통비 무료, 월 한도 50만원"
            }
            return card_info.get(product_id, "일반 체크카드")

        elif product_type == "loan":
            return "대출 상품 - 주택담보대출, 신용대출, 전세자금대출 등 다양한 대출 상품"

        return "금융 상품"

    def _get_user_context(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 컨텍스트 생성"""
        age = user_info["age"]
        job = user_info["job"]
        balance = user_info["balance"]

        return {
            "age_group": "20대" if age < 30 else "30대" if age < 40 else "40대 이상",
            "job_category": job,
            "balance_level": "적정" if balance > 1000000 else "보통"
        }