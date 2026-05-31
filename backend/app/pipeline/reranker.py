from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    pairs = [[query, chunk["text"]] for chunk in chunks]
    scores = model.predict(pairs)
    
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)
    
    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]