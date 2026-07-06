from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter,
    FieldCondition, MatchValue
)
from app.core.config import settings
import uuid

if settings.QDRANT_URL:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
else:
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def init_collection():
    existing = [c.name for c in client.get_collections().collections]
    
    if settings.COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        # Create index for filename filtering
        client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="filename",
            field_schema="keyword"
        )
        print(f"Created collection: {settings.COLLECTION_NAME}")
    else:
        # Add index if collection exists but index doesn't
        try:
            client.create_payload_index(
                collection_name=settings.COLLECTION_NAME,
                field_name="filename",
                field_schema="keyword"
            )
        except:
            pass
        print(f"Collection already exists: {settings.COLLECTION_NAME}")


def store_chunks(embedded: list[dict]) -> list[str]:
    init_collection()  # always ensure collection exists
    
    filename = embedded[0]["chunk"].metadata["filename"]
    
    # Delete existing points for this filename to prevent duplicates
    client.delete(
        collection_name=settings.COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(
                key="filename",
                match=MatchValue(value=filename)
            )]
        )
    )
    
    points = []
    ids = []
    
    for item in embedded:
        chunk = item["chunk"]
        vector = item["vector"]
        
        point_id = str(uuid.uuid4())
        ids.append(point_id)
        
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "text": chunk.text,
                "section": chunk.metadata["section"],
                "filename": chunk.metadata["filename"],
                "chunk_index": chunk.metadata["chunk_index"],
                "strategy": chunk.metadata["strategy"]
            }
        ))
    
    client.upsert(
        collection_name=settings.COLLECTION_NAME,
        points=points
    )
    
    return ids


def search(query_vector: list[float], top_k: int = 5, filename: str = None) -> list[dict]:
    query_filter = None
    if filename:
        query_filter = Filter(
            must=[FieldCondition(
                key="filename",
                match=MatchValue(value=filename)
            )]
        )
    
    results = client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True
    ).points
    
    return [
        {
            "score": r.score,
            "text": r.payload["text"],
            "section": r.payload["section"],
            "filename": r.payload["filename"]
        }
        for r in results
    ]