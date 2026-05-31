from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


# def generate_answer(question: str, chunks: list[dict]) -> str:       very strict answers , downside of controlling hallucination too much
#     # Build context from retrieved chunks
#     context = _build_context(chunks)
    
#     # The prompt is the most important part — structure matters
#     prompt = f"""You are a helpful assistant analyzing a resume.

# Use ONLY the information provided in the context below to answer the question.
# If the answer isn't in the context, say "I couldn't find that in the resume."
# Do not make up or infer information that isn't explicitly stated.

# CONTEXT:
# {context}

# QUESTION:
# {question}

# ANSWER:"""

#     response = client.chat.completions.create(
#         model=settings.GROQ_MODEL,
#         messages=[
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2,   # low temperature = factual, less creative
#         max_tokens=1024
#     )
    
#     return response.choices[0].message.content

def generate_answer(question: str, chunks: list[dict]) -> str:
    context = _build_context(chunks)

    prompt = f"""You are an expert career advisor analyzing a resume.

Use the resume context below as your primary source. You can:
- State facts directly from the resume
- Make reasonable inferences and interpretations based on the resume content
- Give career advice grounded in what the resume shows
- Highlight patterns, strengths, and gaps you observe

Only say "I couldn't find that in the resume" if the question asks for something
completely absent with zero basis for inference (e.g. salary, personal preferences).

RESUME CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024
    )

    return response.choices[0].message.content

def _build_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a readable context block.
    Each chunk gets labeled with its section so the LLM knows where it came from.
    """
    context_parts = []
    
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} - {chunk['section'].upper()}]\n{chunk['text']}"
        )
    
    return "\n\n---\n\n".join(context_parts)

def generate_queries(question: str) -> list[str]:
    """
    Generate multiple rephrasings of the question to cast a wider retrieval net.
    """
    prompt = f"""Generate 4 different ways to search for the answer to this question in a resume.
Each rephrasing should approach it from a different angle.
Output only the 4 queries, one per line, no numbering or bullets.

Question: {question}

Queries:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    
    queries = response.choices[0].message.content.strip().split('\n')
    queries = [q.strip() for q in queries if q.strip()]
    
    # Always include the original question too
    return [question] + queries[:4]