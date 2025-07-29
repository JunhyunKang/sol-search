__version__ = "1.0.0"
__author__ = "SOL Spot Team"
__email__ = "contact@solspot.com"

# 패키지 레벨에서 필요한 초기화 작업
import logging
from app.config import settings

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

logger = logging.getLogger(__name__)
logger.info(f"SOL Spot API v{__version__} initialized")