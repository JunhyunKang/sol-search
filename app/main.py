from fastapi import FastAPI
from app.models import SearchRequest, SearchResponse, ErrorResponse
from app.services import SearchService

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    result = SearchService.process_query(request.query)
    # return SearchResponse(**result)
    return