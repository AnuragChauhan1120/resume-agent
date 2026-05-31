from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.resume import router as resume_router
from app.pipeline.store import init_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_collection()
    yield

app = FastAPI(title="Resume Agent", lifespan=lifespan)

app.add_middleware(                #new addition for CORS error
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)

@app.get("/")
async def root():
    return {"status": "running"}