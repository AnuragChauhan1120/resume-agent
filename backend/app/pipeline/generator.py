from groq import Groq
from app.core.config import settings
from typing import Generator

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_answer(question: str, chunks: list[dict]) -> str:
    context = _build_context(chunks)
    prompt = _build_prompt(question, context)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024
    )

    return response.choices[0].message.content


def generate_answer_stream(question: str, chunks: list[dict]) -> Generator:
    """
    Same as generate_answer but streams tokens as they arrive.
    Returns a generator that yields text chunks.
    """
    context = _build_context(chunks)
    prompt = _build_prompt(question, context)

    stream = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
        stream=True   # this is the only difference
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


def _build_prompt(question: str, context: str) -> str:
    return f"""You are an expert career advisor analyzing a resume.

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


def _build_context(chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} - {chunk['section'].upper()}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


def generate_hypothetical_chunk(question: str) -> str:
    prompt = f"""Generate a short resume excerpt that would perfectly answer this question.
Write it as if it's extracted from a real resume — bullet points, concrete details, no fluff.
Only output the resume text, nothing else.

Question: {question}

Resume excerpt:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=200
    )

    return response.choices[0].message.content


def generate_queries(question: str) -> list[str]:
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
    return [question] + queries[:4]