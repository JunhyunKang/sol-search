import os
from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 기본 앱 설정 (하드코딩 유지)
    APP_NAME: str = "SOL SEARCH API"
    APP_VERSION: str = "1.0.0"

    # 환경 설정 (환경변수 필수!)
    ENVIRONMENT: str
    DEBUG: bool
    HOST: str
    PORT: int

    # 데이터베이스 설정 (환경변수 필수!)
    # DATABASE_URL: str
    # DATABASE_PATH: str

    # CORS 설정 (문자열로 받기 - 나중에 파싱)
    ALLOWED_ORIGINS: str
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # NLP 설정 (환경변수 필수!)
    SPACY_MODEL: str
    NLP_CONFIDENCE_THRESHOLD: float

    # API 설정 (환경변수 필수!)
    API_V1_STR: str

    # 로그 설정 (환경변수 필수!)
    LOG_LEVEL: str
    LOG_FORMAT: str

    # 보안 설정 (환경변수 필수!)
    SECRET_KEY: str

    # 송금 관련 설정 (환경변수 필수!)
    MAX_TRANSFER_AMOUNT: int
    MIN_TRANSFER_AMOUNT: int

    # 검색 설정 (환경변수 필수!)
    MAX_SEARCH_RESULTS: int
    SEARCH_TIMEOUT: int


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_cors_origins(self) -> List[str]:
        """CORS origins를 리스트로 변환"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


def get_settings() -> Settings:
    """설정 인스턴스 생성"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()


def print_settings():
    """현재 설정 정보 출력 (보안 정보 제외)"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print(f"🐛 Debug: {settings.DEBUG}")
    print(f"🔗 Host: {settings.HOST}:{settings.PORT}")
    print(f"📊 Database: {settings.DATABASE_PATH}")
    print(f"🤖 NLP Model: {settings.SPACY_MODEL}")
    print(f"📝 Log Level: {settings.LOG_LEVEL}")
    print(f"🌐 CORS Origins: {settings.get_cors_origins()}")
    print(f"💰 Transfer Limits: {settings.MIN_TRANSFER_AMOUNT:,} ~ {settings.MAX_TRANSFER_AMOUNT:,}원")
    print(f"🔍 Search: Max {settings.MAX_SEARCH_RESULTS} results, {settings.SEARCH_TIMEOUT}s timeout")


def validate_settings():
    """설정값들이 올바른지 간단 검증"""
    print("🔧 설정 검증 중...")

    # 기본 검증들
    errors = []

    if len(settings.SECRET_KEY) < 10:
        errors.append("SECRET_KEY가 너무 짧습니다")

    if settings.MIN_TRANSFER_AMOUNT >= settings.MAX_TRANSFER_AMOUNT:
        errors.append("MIN_TRANSFER_AMOUNT가 MAX_TRANSFER_AMOUNT보다 큽니다")

    if not (0.0 <= settings.NLP_CONFIDENCE_THRESHOLD <= 1.0):
        errors.append("NLP_CONFIDENCE_THRESHOLD는 0.0~1.0 사이여야 합니다")

    if errors:
        print("❌ 설정 오류:")
        for error in errors:
            print(f"   - {error}")
        raise ValueError("설정을 확인해주세요")

    print("✅ 설정 검증 완료!")
    return True