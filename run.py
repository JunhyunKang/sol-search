# run.py
import uvicorn
from app.main import app
from app.config import settings

if __name__ == "__main__":
    print("\n3️⃣ 서버 시작...")
    print(f"📖 API 문서: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔍 헬스체크: http://{settings.HOST}:{settings.PORT}/health")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )