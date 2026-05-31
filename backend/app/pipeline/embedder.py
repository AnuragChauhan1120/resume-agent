from sentence_transformers import SentenceTransformer
from app.pipeline.chunker import Chunk
from app.core.config import settings

# Load once at module level — expensive to reload every call
model = SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_chunks(chunks: list[Chunk]) -> list[dict]:
    """
    Takes chunks, returns list of {chunk, vector} dicts
    """
    texts = [chunk.text for chunk in chunks]
    
    # This is the core call — runs all texts through the neural net
    # batch processing is more efficient than one by one
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,       # qdrant expects numpy or plain list
        normalize_embeddings=True    # normalizes to unit length — important for cosine similarity
    )
    
    embedded = []
    for chunk, vector in zip(chunks, vectors):
        embedded.append({
            "chunk": chunk,
            "vector": vector.tolist()  # convert numpy array to plain list
        })
    
    return embedded


def embed_query(query: str) -> list[float]:
    """
    Embed a single search query — same model, same space
    so query vector is comparable to chunk vectors
    """
    vector = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    return vector.tolist()