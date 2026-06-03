from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# --- Models ---

class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    num_chunks = Column(Integer)
    sections_found = Column(JSON)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class JobSearch(Base):
    __tablename__ = "job_searches"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    profile = Column(Text)
    queries_used = Column(JSON)
    jobs_found = Column(Integer)
    searched_at = Column(DateTime, default=datetime.utcnow)


class QAHistory(Base):
    __tablename__ = "qa_history"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    question = Column(Text)
    answer = Column(Text)
    asked_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()