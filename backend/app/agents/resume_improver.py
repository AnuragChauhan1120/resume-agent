from groq import Groq
from app.core.config import settings
from app.pipeline.embedder import embed_query
from app.pipeline.store import search
from app.pipeline.reranker import rerank

groq_client = Groq(api_key=settings.GROQ_API_KEY)


def analyze_gaps(resume_chunks: list[dict], job_description: str) -> str:
    """
    Compare resume against job description and identify gaps.
    """
    resume_text = "\n\n".join(c["text"] for c in resume_chunks)

    prompt = f"""You are an expert resume reviewer.
Compare this resume against the job description and identify:
1. Missing skills or technologies
2. Weak or vague bullet points that should be stronger
3. Missing quantifiable achievements
4. Sections that need more detail
5. Strengths that are well-aligned

Be specific and actionable. Reference exact lines from the resume.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

ANALYSIS:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content


def suggest_improvements(resume_chunks: list[dict], gap_analysis: str) -> str:
    """
    Generate specific rewrite suggestions based on gap analysis.
    """
    resume_text = "\n\n".join(c["text"] for c in resume_chunks)

    prompt = f"""Based on this gap analysis, suggest specific rewrites for weak bullet points.
For each suggestion:
- Quote the original line
- Provide an improved version
- Explain why it's better

Focus on making bullet points more impactful with metrics and specific technologies.

RESUME:
{resume_text}

GAP ANALYSIS:
{gap_analysis}

SUGGESTIONS:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1000
    )

    return response.choices[0].message.content


def rewrite_section(section_text: str, job_description: str, section_name: str) -> str:
    """
    Fully rewrite a specific resume section to better match a job description.
    """
    prompt = f"""Rewrite this {section_name} section to better match the job description.
Keep all factual information accurate — only improve phrasing, impact, and relevance.
Use strong action verbs and quantifiable achievements where possible.
Match keywords from the job description naturally.

ORIGINAL {section_name.upper()}:
{section_text}

JOB DESCRIPTION:
{job_description}

REWRITTEN {section_name.upper()}:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=800
    )

    return response.choices[0].message.content


def improve_resume(filename: str, job_description: str) -> dict:
    """
    Main entry point — full resume improvement pipeline.
    """
    # Get all relevant resume chunks
    query_vector = embed_query("experience projects skills achievements")
    chunks = search(query_vector, top_k=8, filename=filename)
    reranked = rerank(job_description, chunks, top_k=6)

    print("\n[Improver] Analyzing gaps...")
    gap_analysis = analyze_gaps(reranked, job_description)

    print("\n[Improver] Generating suggestions...")
    suggestions = suggest_improvements(reranked, gap_analysis)

    # Rewrite the work experience section specifically
    experience_vector = embed_query("work experience internship")
    experience_chunks = search(experience_vector, top_k=2, filename=filename)
    experience_text = "\n\n".join(c["text"] for c in experience_chunks)

    print("\n[Improver] Rewriting experience section...")
    rewritten_experience = rewrite_section(experience_text, job_description, "work experience")

    return {
        "gap_analysis": gap_analysis,
        "suggestions": suggestions,
        "rewritten_experience": rewritten_experience
    }
