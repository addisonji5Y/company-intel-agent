"""
Business Agent - Provides an overview of what a company does.
"""
from backend.tools.llm import chat

SYNTHESIZE_PROMPT = """You are a business analyst providing company overviews.

Given search results about a company, provide a concise business overview covering:
- What the company does (core product/service)
- Target market / customers
- Business model (how they make money)
- Notable facts (funding stage, size, key metrics if available)

IMPORTANT: If company context is provided, use it to ensure you are analyzing the CORRECT company.
There may be multiple companies with similar names - focus only on the verified target company.

Keep it to 3-4 short paragraphs. Be factual and specific based on the search results.
"""


def synthesize(company_name: str, search_results: list[dict], company_context: str | None = None) -> str:
    """
    Synthesize search results into a business overview.
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

Based on these search results, provide a business overview of {company_name}."""

    return chat(SYNTHESIZE_PROMPT, user_msg)
