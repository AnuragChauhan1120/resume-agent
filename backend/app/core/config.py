from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    COLLECTION_NAME: str = "resumes"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    GROQ_API_KEY: str = "GROQ_API_KEY"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    TAVILY_API_KEY: str = "TAVILY_API_KEY"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    class Config:
        env_file = ".env"

settings = Settings()

