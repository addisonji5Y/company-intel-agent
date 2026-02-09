"""
LLM utility - thin wrapper around Anthropic Claude API.
All agent LLM calls go through here.
"""
import os
import json
from anthropic import Anthropic


def get_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")
    return Anthropic(api_key=api_key)


MODEL = "claude-sonnet-4-20250514"


def chat(system_prompt: str, user_message: str, json_mode: bool = False) -> str:
    """
    Simple single-turn LLM call.
    If json_mode=True, instructs model to return valid JSON.
    """
    client = get_client()

    if json_mode:
        system_prompt += "\n\nYou MUST respond with valid JSON only. No markdown, no explanation, just JSON."

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def parse_json_response(text: str) -> dict:
    """Try to parse JSON from LLM response, handling common issues."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)
