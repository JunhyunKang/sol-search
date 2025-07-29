from fastapi import FastAPI
from app.models import SearchRequest, SearchResponse, ErrorResponse
from app.services import SearchService

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

search_service = SearchService()

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    result = search_service.process_query(request.query)
    return SearchResponse(**result)