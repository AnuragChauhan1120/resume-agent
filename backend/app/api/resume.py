from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.resume import SearchRequest, SearchResponse, UploadResponse, ChunkResult
from app.pipeline.parser import parse_resume
from app.pipeline.chunker import chunk_resume
from app.pipeline.embedder import embed_chunks, embed_query
from app.pipeline.store import store_chunks, search
from app.models.resume import AskRequest, AskResponse
from app.pipeline.reranker import rerank
from app.pipeline.generator import generate_answer, generate_queries
from app.agents.job_finder import find_jobs
from app.models.resume import JobResult, JobSearchResponse
from app.agents.resume_improver import improve_resume
from app.models.resume import ImproveRequest, ImproveResponse
import tempfile
import os

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    
    # Save uploaded file to a temp location — we need a real path for fitz
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Run the full pipeline
        parsed = parse_resume(tmp_path)

        #Quick doc type check using section names — no LLM call needed
        resume_sections = {"experience", "work experience", "education", "skills", "technical skills", "projects"}
        found_sections = set(parsed.sections.keys())
        is_resume = len(resume_sections & found_sections) >= 2

        if not is_resume:
            raise HTTPException(
                status_code=400, 
                detail="This doesn't look like a resume. Please upload a resume PDF."
            )
        
        chunks = chunk_resume(parsed, file.filename)
        for i, chunk in enumerate(chunks):
            print(f"\n--- CHUNK {i} ---")
            print(f"Section: {chunk.metadata['section']}")
            print(f"Text: {chunk.text}")
            print(f"Length: {len(chunk.text)}")
        embedded = embed_chunks(chunks)
        ids = store_chunks(embedded)
        
        return UploadResponse(
            filename=file.filename,
            num_chunks=len(chunks),
            sections_found=list(parsed.sections.keys()),
            chunk_ids=ids
        )
    
    finally:
        os.unlink(tmp_path)  # always clean up temp file


@router.post("/search", response_model=SearchResponse)
async def search_resume(request: SearchRequest):
    query_vector = embed_query(request.query)
    
    results = search(
        query_vector=query_vector,
        top_k=request.top_k,
        filename=request.filename
    )
    
    return SearchResponse(
        query=request.query,
        results=[ChunkResult(**r) for r in results]
    )

# @router.post("/ask", response_model=AskResponse)       // basic without reranker and random generator 
# async def ask_resume(request: AskRequest):
#     # Retrieve relevant chunks
#     query_vector = embed_query(request.question)
#     chunks = search(
#         query_vector=query_vector,
#         top_k=request.top_k,
#         filename=request.filename
#     )
    
#     if not chunks:
#         raise HTTPException(status_code=404, detail="No resume data found")
    
#     # Generate answer from chunks
#     answer = generate_answer(request.question, chunks)
    
#     return AskResponse(
#         question=request.question,
#         answer=answer,
#         sources=[ChunkResult(**c) for c in chunks]
#     )


# @router.post("/ask", response_model=AskResponse)        //with reranker
# async def ask_resume(request: AskRequest):
#     query_vector = embed_query(request.question)
    
#     # Fetch more candidates than needed, then rerank
#     chunks = search(
#         query_vector=query_vector,
#         top_k=request.top_k * 3,  # cast wider net
#         filename=request.filename
#     )
    
#     if not chunks:
#         raise HTTPException(status_code=404, detail="No resume data found")
    
#     # Rerank by actually reading query + chunk together
#     reranked = rerank(request.question, chunks, top_k=request.top_k)
    
#     answer = generate_answer(request.question, reranked)
    
#     return AskResponse(
#         question=request.question,
#         answer=answer,
#         sources=[ChunkResult(**c) for c in reranked]
#     )


@router.post("/ask", response_model=AskResponse)
async def ask_resume(request: AskRequest):
    # Step 1: generate multiple query rephrasings
    queries = generate_queries(request.question)
    print(f"\nGenerated queries: {queries}")
    
    # Step 2: search with each query, collect all results
    all_chunks = []
    seen_texts = set()
    
    for query in queries:
        query_vector = embed_query(query)
        results = search(
            query_vector=query_vector,
            top_k=request.top_k,
            filename=request.filename
        )
        
        # Deduplicate by text content
        for chunk in results:
            if chunk["text"] not in seen_texts:
                seen_texts.add(chunk["text"])
                all_chunks.append(chunk)
    
    if not all_chunks:
        raise HTTPException(status_code=404, detail="No resume data found")
    
    print(f"\nUnique chunks retrieved: {len(all_chunks)}")
    
    # Step 3: rerank the full deduplicated pool
    reranked = rerank(request.question, all_chunks, top_k=request.top_k)
    
    # Step 4: generate answer from reranked chunks
    answer = generate_answer(request.question, reranked)
    
    return AskResponse(
        question=request.question,
        answer=answer,
        sources=[ChunkResult(**c) for c in reranked]
    )

# @router.post("/find-jobs", response_model=JobSearchResponse)     //tried to validate if pdf is resume or not , but threw errors in such cases
# async def find_jobs_endpoint(filename: str):
#     # Quick check — ask the LLM if this looks like a resume
#     query_vector = embed_query("name contact experience education skills")
#     chunks = search(query_vector, top_k=3, filename=filename)
    
#     if not chunks:
#         raise HTTPException(status_code=400, detail="No content found for this file")
    
#     # Check if it looks like a resume
#     combined = " ".join(c["text"] for c in chunks).lower()
#     resume_signals = ["experience", "education", "skills", "project", "intern", "university"]
#     matches = sum(1 for s in resume_signals if s in combined)
    
#     if matches < 2:
#         raise HTTPException(status_code=400, detail="This doesn't look like a resume. Please upload a resume PDF.")
    
#     result = find_jobs(filename)
#     return JobSearchResponse(
#         profile=result["profile"],
#         queries_used=result["queries_used"],
#         jobs=[JobResult(**j) for j in result["jobs"]]
#     )

@router.post("/find-jobs", response_model=JobSearchResponse)
async def find_jobs_endpoint(filename: str):
    result = find_jobs(filename)
    return JobSearchResponse(
        profile=result["profile"],
        queries_used=result["queries_used"],
        jobs=[JobResult(**j) for j in result["jobs"]]
    )


@router.post("/improve", response_model=ImproveResponse)
async def improve_resume_endpoint(request: ImproveRequest):
    result = improve_resume(request.filename, request.job_description)
    return ImproveResponse(**result)