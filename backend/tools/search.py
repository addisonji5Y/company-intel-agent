"""
Tavily Search Tool - wraps Tavily API for agent use.
Keeps it simple: search and return top results.
"""
import os
from tavily import TavilyClient


def get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in environment")
    return TavilyClient(api_key=api_key)


def search(query: str, max_results: int = 3) -> list[dict]:
    """
    Search the web using Tavily.
    Returns a list of {title, url, content} dicts.
    """
    client = get_tavily_client()
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
    )
    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:500],  # truncate for speed
        })
    return results
