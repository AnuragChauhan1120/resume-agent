from tavily import TavilyClient
from app.core.config import settings
from app.pipeline.embedder import embed_query
from app.pipeline.store import search
from app.pipeline.generator import generate_answer
from groq import Groq

tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
groq_client = Groq(api_key=settings.GROQ_API_KEY)


def extract_resume_profile(filename: str) -> str:
    """
    Pull the most relevant chunks from the resume and summarize
    into a profile string for job searching.
    """
    # Get skills and experience chunks
    skills_vector = embed_query("technical skills programming languages frameworks")
    experience_vector = embed_query("work experience internship projects")

    skills_chunks = search(skills_vector, top_k=2, filename=filename)
    experience_chunks = search(experience_vector, top_k=3, filename=filename)

    all_chunks = {c["text"]: c for c in skills_chunks + experience_chunks}
    combined = "\n\n".join(c["text"] for c in all_chunks.values())

    # Ask LLM to extract a clean profile
    prompt = f"""Extract a concise job search profile from this resume content.
Output format:
- Role: (target job title)
- Skills: (top 8-10 technical skills, comma separated)
- Experience level: (fresher/junior/mid)
- Domain: (e.g. data science, full stack, ML engineering)

Resume content:
{combined}

Profile:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=200
    )

    return response.choices[0].message.content


def build_search_queries(profile: str) -> list[str]:
    """
    Build targeted job search queries from the profile.
    """
    prompt = f"""Generate 3 specific job search queries for this profile.
Queries should target real job listings on job boards.
Include role, key skills, and experience level.
Output only 3 queries, one per line.

Profile:
{profile}

Search queries:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=150
    )

    queries = response.choices[0].message.content.strip().split('\n')
    return [q.strip() for q in queries if q.strip()][:3]


# def search_jobs(queries: list[str]) -> list[dict]:
#     """
#     Search for jobs using Tavily for each query.
#     Deduplicate by URL.
#     """
#     seen_urls = set()
#     jobs = []

#     for query in queries:
#         # results = tavily.search(
#         #     query=query + " job opening 2025",
#         #     max_results=5,
#         #     search_depth="basic"
#         #)
#         results = tavily.search(
#             query=query + " job opening site:linkedin.com/jobs OR site:indeed.com OR site:naukri.com",
#             max_results=5,
#             search_depth="basic",
#             include_domains=["linkedin.com/jobs", "indeed.com", "naukri.com", "internshala.com", "unstop.com"]
#         )

#         for r in results.get("results", []):
#             if r["url"] not in seen_urls:
#                 seen_urls.add(r["url"])
#                 jobs.append({
#                     "title": r.get("title", ""),
#                     "url": r.get("url", ""),
#                     "snippet": r.get("content", "")[:300],
#                     "query_used": query
#                 })
#             # Skip LinkedIn profile pages
#             if "/in/" in r["url"]:
#                 continue

#     return jobs

# def search_jobs(queries: list[str]) -> list[dict]:    
#     seen_urls = set()
#     jobs = []

#     for query in queries:
#         results = tavily.search(
#             query=query + " job opening 2025 India OR remote",
#             max_results=5,
#             search_depth="basic"
#         )

#         for r in results.get("results", []):
#             url = r["url"]
            
#             # Filter out non-job pages
#             if any(skip in url for skip in ["/in/", "youtube.com", "graphy.com", "jobtensor"]):
#                 continue
            
#             if url not in seen_urls:
#                 seen_urls.add(url)
#                 jobs.append({
#                     "title": r.get("title", ""),
#                     "url": url,
#                     "snippet": r.get("content", "")[:300],
#                     "query_used": query
#                 })

#     return jobs

def search_jobs(queries: list[str]) -> list[dict]:     #for pdf provided is resume or not 
    seen_urls = set()
    jobs = []

    for query in queries:
        try:
            results = tavily.search(
                query=query + " job opening 2025 India OR remote",
                max_results=5,
                search_depth="basic"
            )
            for r in results.get("results", []):
                url = r["url"]
                if any(skip in url for skip in ["/in/", "youtube.com", "graphy.com"]):
                    continue
                if url not in seen_urls:
                    seen_urls.add(url)
                    jobs.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "snippet": r.get("content", "")[:300],
                        "query_used": query
                    })
        except Exception as e:
            print(f"[Job Finder] Search failed for query '{query}': {e}")
            continue  # skip this query, try the next one

    return jobs


def rank_jobs(jobs: list[dict], profile: str) -> list[dict]:
    """
    Ask LLM to rank jobs by relevance to the profile.
    """
    jobs_text = "\n\n".join(
        f"[{i+1}] {j['title']}\n{j['snippet']}"
        for i, j in enumerate(jobs)
    )

    prompt = f"""Rank these job listings by relevance to this candidate profile.
Return only the ranking as numbers in order, comma separated (e.g. 3,1,5,2,4).
Most relevant first.

Profile:
{profile}

Jobs:
{jobs_text}

Ranking:"""

    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=50
    )

    ranking_str = response.choices[0].message.content.strip()
    
    try:
        ranking = [int(x.strip()) - 1 for x in ranking_str.split(',')]
        ranked = [jobs[i] for i in ranking if i < len(jobs)]
        # Add any jobs not in ranking at the end
        ranked_indices = set(ranking)
        for i, job in enumerate(jobs):
            if i not in ranked_indices:
                ranked.append(job)
        return ranked
    except:
        return jobs  # fallback to original order if parsing fails


def find_jobs(filename: str) -> dict:
    """
    Main entry point — full job finding pipeline.
    """
    print("\n[Job Finder] Extracting resume profile...")
    profile = extract_resume_profile(filename)
    print(f"Profile:\n{profile}")

    print("\n[Job Finder] Building search queries...")
    queries = build_search_queries(profile)
    print(f"Queries: {queries}")

    print("\n[Job Finder] Searching for jobs...")
    jobs = search_jobs(queries)
    print(f"Found {len(jobs)} unique listings")

    print("\n[Job Finder] Ranking jobs...")
    ranked = rank_jobs(jobs, profile)

    return {
        "profile": profile,
        "queries_used": queries,
        "jobs": ranked
    }
