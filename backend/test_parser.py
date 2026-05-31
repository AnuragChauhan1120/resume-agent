import sys
sys.path.append(".")  # tells Python to look in current directory for modules

from app.pipeline.parser import parse_resume
from app.pipeline.chunker import chunk_resume
from app.pipeline.embedder import embed_chunks, embed_query
from app.pipeline.store import init_collection, store_chunks, search
from app.pipeline.embedder import embed_query

result = parse_resume("res.pdf")  # drop any pdf in backend/ folder

print("=== METADATA ===")
print(result.metadata)

print("\n=== SECTIONS FOUND ===")
for section, content in result.sections.items():
    print(f"\n[{section.upper()}]")
    print(content[:200])  # first 200 chars of each section


chunks = chunk_resume(result, result.metadata["filename"])

print(f"\n=== {len(chunks)} CHUNKS CREATED ===")
for i, chunk in enumerate(chunks):
    print(f"\n[Chunk {i} | section: {chunk.metadata['section']} | strategy: {chunk.metadata['strategy']}]")
    print(chunk.text[:150])
    print("---")


embedded = embed_chunks(chunks)

print(f"\n=== EMBEDDINGS ===")
for item in embedded:
    print(f"Section: {item['chunk'].metadata['section']} | vector dims: {len(item['vector'])} | first 5 values: {item['vector'][:5]}")

# Test semantic similarity
q_vector = embed_query("machine learning projects")
print(f"\nQuery vector dims: {len(q_vector)}")


# Init collection
init_collection()

# Store chunks
ids = store_chunks(embedded)
print(f"\n=== STORED {len(ids)} POINTS IN QDRANT ===")

# Now search
query = "machine learning and deep learning experience"
q_vector = embed_query(query)
results = search(q_vector, top_k=3)

print(f"\n=== SEARCH RESULTS FOR: '{query}' ===")
for r in results:
    print(f"\nScore: {r['score']:.4f} | Section: {r['section']}")
    print(r['text'][:200])
    print("---")