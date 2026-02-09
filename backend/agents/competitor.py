"""
Competitor Agent - Finds top competitors for a given company.
"""
from backend.tools.llm import chat

SYNTHESIZE_PROMPT = """You are a competitive intelligence analyst.

Given search results about a company's competitors, provide a concise analysis.

IMPORTANT: If company context is provided, use it to ensure you are analyzing the CORRECT company.
There may be multiple companies with similar names - focus only on the verified target company.

Format your response as:
1. **[Competitor Name]** - One sentence about what they do and why they compete.
2. **[Competitor Name]** - ...
3. **[Competitor Name]** - ...

Keep it to the top 3 competitors. Be specific and concise.
If the search results don't contain enough info, say what you know and note the gaps.
"""


def synthesize(company_name: str, search_results: list[dict], company_context: str | None = None) -> str:
    """
    Synthesize search results into a competitor analysis.
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

Based on these search results, who are the top 3 competitors of {company_name}?"""

    return chat(SYNTHESIZE_PROMPT, user_msg)
