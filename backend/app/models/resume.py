from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filename: str = None  # optional, filter by specific resume

class ChunkResult(BaseModel):
    score: float
    text: str
    section: str
    filename: str

class SearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]

class UploadResponse(BaseModel):
    filename: str
    num_chunks: int
    sections_found: list[str]
    chunk_ids: list[str]

class AskRequest(BaseModel):
    question: str
    filename: str = None
    top_k: int = 3

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChunkResult]

class JobResult(BaseModel):
    title: str
    url: str
    snippet: str
    query_used: str

class JobSearchResponse(BaseModel):
    profile: str
    queries_used: list[str]
    jobs: list[JobResult]

class ImproveRequest(BaseModel):
    filename: str
    job_description: str

class ImproveResponse(BaseModel):
    gap_analysis: str
    suggestions: str
    rewritten_experience: str