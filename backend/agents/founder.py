"""
Founder Agent - Finds founder and leadership information for a company.
"""
from backend.tools.llm import chat

SYNTHESIZE_PROMPT = """You are a company research analyst focused on leadership teams.

Given search results about a company's founders/leadership, provide a concise summary.

IMPORTANT: If company context is provided, use it to ensure you are analyzing the CORRECT company.
There may be multiple companies with similar names - focus only on the verified target company.

Include:
- Founder name(s) and brief background
- Current CEO (if different from founder)
- Notable leadership team members (if found)

Keep it concise - a short paragraph per person. Focus on facts from the search results.
"""


def synthesize(company_name: str, search_results: list[dict], company_context: str | None = None) -> str:
    """
    Synthesize search results into a founder/leadership summary.
    Returns the synthesized answer.
    """
    search_context = "\n\n".join([
        f"Source: {r['title']} ({r['url']})\n{r['content']}"
        for r in search_results
    ])

    context_info = ""
    if company_context:
        context_info = f"\nVerified Company Context: {company_context}\n"

    user_msg = f"""Company: {company_name}{context_info}
Search Results:
{search_context}

Based on these search results, who founded {company_name} and who leads it now?"""

    return chat(SYNTHESIZE_PROMPT, user_msg)
