from fastapi import FastAPI, Query
from starlette.middleware.cors import CORSMiddleware

from app.models import SearchRequest, SearchResponse, ErrorResponse
from app.services import SearchService
from app.services.user_service import UserService


app = FastAPI(
    title="SOL Bank API",
    version="1.0.0",
    description="SOL Bank Backend API"
)
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 설정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_service = SearchService()
user_service = UserService()

@app.get("/")
async def root():
    return {"message": "SOL Bank API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# User API
@app.get("/api/user/info")
async def get_user_info():
    return user_service.get_user_info()


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    result = search_service.process_query(request.query)
    return SearchResponse(**result)