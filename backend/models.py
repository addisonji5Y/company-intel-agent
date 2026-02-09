from pydantic import BaseModel
from typing import Optional
from enum import Enum


class IntentType(str, Enum):
    COMPETITOR = "competitor_analysis"
    FOUNDER = "founder_lookup"
    BUSINESS = "business_overview"
    UNKNOWN = "unknown"


class UserRequest(BaseModel):
    company_name: str
    website: Optional[str] = None
    query: str


class CompanyVerification(BaseModel):
    """Result of company identity verification"""
    verified: bool
    company_description: str  # What we know about the target company
    similar_companies: list[str]  # Other companies with similar names found
    verification_method: str  # How we verified (e.g., "website match")


class RouterResult(BaseModel):
    intent: IntentType
    reasoning: str
    search_queries: list[str]
    company_context: Optional[str] = None  # Verified company info to pass to specialist agents


class AgentEvent(BaseModel):
    """SSE event sent to frontend"""
    agent: str       # which agent is acting
    event: str       # thinking / tool_call / tool_result / final_answer / error
    content: str     # the actual message
