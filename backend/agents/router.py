"""
Router Agent - Analyzes user intent and routes to the right specialist agent.

This is the "brain" that decides what the user wants:
- competitor_analysis: Find competitors
- founder_lookup: Find founder/team info
- business_overview: Explain what the company does

Also handles company verification when website is provided to disambiguate
companies with similar names.
"""
from backend.models import IntentType, RouterResult, CompanyVerification
from backend.tools.llm import chat, parse_json_response
from backend.tools.search import search

ROUTER_SYSTEM_PROMPT = """You are an intent router for a company intelligence system.

Given a user's query about a company, determine:
1. The intent type (one of: competitor_analysis, founder_lookup, business_overview)
2. Your reasoning for this classification
3. 1-2 search queries that would help answer the user's question

IMPORTANT: If company_context is provided, use it to make your search queries more specific.
Include distinguishing details (industry, location, website domain) in search queries to avoid confusion with similarly-named companies.

Respond in this exact JSON format:
{
    "intent": "competitor_analysis" | "founder_lookup" | "business_overview",
    "reasoning": "Brief explanation of why you chose this intent",
    "search_queries": ["query 1", "query 2"]
}

Rules:
- If the user asks about competitors, rivals, alternatives, or similar companies → competitor_analysis
- If the user asks about founders, CEO, team, leadership, or who started it → founder_lookup
- If the user asks what the company does, their products, business model, or anything else → business_overview
"""

VERIFY_COMPANY_PROMPT = """You are a company identification specialist.

Given search results about a company, analyze and extract:
1. The actual identity of the target company (based on website if provided)
2. Any other companies with similar names that appeared in search results
3. Key distinguishing information about the target company

Respond in this exact JSON format:
{
    "target_company": {
        "name": "Official company name",
        "description": "What this company does (1-2 sentences)",
        "industry": "Primary industry",
        "distinguishing_info": "Key facts that distinguish this from similar-named companies"
    },
    "similar_companies": [
        {"name": "Similar Company 1", "description": "Brief description"},
        {"name": "Similar Company 2", "description": "Brief description"}
    ],
    "confidence": "high" | "medium" | "low"
}

If the search results clearly identify the company via the website, confidence should be "high".
List any other companies with similar names found in the results under similar_companies.
"""


def verify_company(company_name: str, website: str) -> tuple[CompanyVerification, list[dict]]:
    """
    Verify company identity using website.
    Returns (verification_result, search_results).
    """
    # Search using website to get accurate company info
    search_query = f"site:{website} OR \"{website}\" {company_name}"
    results = search(search_query, max_results=3)

    # Also search just the company name to find similar companies
    name_results = search(f"{company_name} company", max_results=3)
    all_results = results + name_results

    if not all_results:
        return CompanyVerification(
            verified=False,
            company_description=f"Could not verify {company_name}",
            similar_companies=[],
            verification_method="no search results"
        ), []

    # Use LLM to analyze search results
    search_context = "\n\n".join([
        f"Source: {r['title']} ({r['url']})\n{r['content']}"
        for r in all_results
    ])

    user_msg = f"""Target Company: {company_name}
Website: {website}

Search Results:
{search_context}

Analyze these results to identify the target company and any similarly-named companies."""

    raw = chat(VERIFY_COMPANY_PROMPT, user_msg, json_mode=True)
    data = parse_json_response(raw)

    target = data.get("target_company", {})
    similar = data.get("similar_companies", [])

    similar_names = [s.get("name", "") + ": " + s.get("description", "") for s in similar if s.get("name")]

    description = target.get("description", "")
    if target.get("industry"):
        description += f" (Industry: {target.get('industry')})"
    if target.get("distinguishing_info"):
        description += f" - {target.get('distinguishing_info')}"

    return CompanyVerification(
        verified=data.get("confidence") in ["high", "medium"],
        company_description=description,
        similar_companies=similar_names,
        verification_method=f"website verification via {website}"
    ), all_results


def route(company_name: str, website: str | None, user_query: str, company_context: str | None = None) -> RouterResult:
    """
    Analyze user intent and return routing decision.
    If company_context is provided, use it to generate more specific search queries.
    """
    context_info = ""
    if company_context:
        context_info = f"\nVerified Company Context: {company_context}"

    user_message = f"""Company: {company_name}
Website: {website or 'not provided'}{context_info}
User's question: {user_query}"""

    raw = chat(ROUTER_SYSTEM_PROMPT, user_message, json_mode=True)
    data = parse_json_response(raw)

    return RouterResult(
        intent=IntentType(data["intent"]),
        reasoning=data["reasoning"],
        search_queries=data.get("search_queries", [f"{company_name} {user_query}"]),
        company_context=company_context,
    )
