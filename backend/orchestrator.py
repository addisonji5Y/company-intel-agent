"""
Orchestrator - Coordinates the full agent pipeline and yields SSE events.

This is the heart of the system. It:
1. Verifies company identity (when website provided)
2. Calls the Router Agent to understand intent
3. Executes Tavily searches with detailed logging
4. Dispatches to the right specialist agent for synthesis
5. Yields events at every step so the frontend can show what's happening
"""
import json
import asyncio
import traceback
import time
from typing import AsyncGenerator

from backend.models import UserRequest, IntentType
from backend.agents import router, competitor, founder, business
from backend.tools.search import search


def make_event(agent: str, event: str, content: str) -> dict:
    """Create an event dict for SSE."""
    return {
        "agent": agent,
        "event": event,
        "content": content,
    }


async def run_pipeline(request: UserRequest) -> AsyncGenerator[dict, None]:
    """
    Run the full agent pipeline.
    Yields dicts — sse-starlette handles JSON serialization + SSE formatting.
    """
    company = request.company_name
    website = request.website
    query = request.query
    company_context = None

    try:
        # ============================
        # Step 0: Company Verification (if website provided)
        # ============================
        if website:
            yield make_event("Router", "thinking",
                             f"📝 Received request: analyze '{company}' ({website}) - \"{query}\"")
            await asyncio.sleep(0.1)

            yield make_event("Router", "tool_call",
                             f"🔍 Verifying company identity via website: {website}")
            await asyncio.sleep(0.1)

            yield make_event("Router", "tool_call",
                             f"🔍 Searching: site:{website} OR \"{website}\" {company}")
            await asyncio.sleep(0.1)

            yield make_event("Router", "tool_call",
                             f"🔍 Searching: {company} company (to find similar names)")
            await asyncio.sleep(0.1)

            # Run verification in thread pool
            verification, verify_results = await asyncio.to_thread(
                router.verify_company, company, website
            )

            yield make_event("Router", "tool_result",
                             f"📄 Found {len(verify_results)} results for verification")
            await asyncio.sleep(0.1)

            # Show similar companies if found
            if verification.similar_companies:
                yield make_event("Router", "thinking",
                                 f"⚠️ Found companies with similar names:")
                await asyncio.sleep(0.1)
                for similar in verification.similar_companies[:3]:
                    yield make_event("Router", "thinking", f"   • {similar}")
                    await asyncio.sleep(0.05)

            # Show verification result
            if verification.verified:
                yield make_event("Router", "decision",
                                 f"✅ Company verified via {website}")
                await asyncio.sleep(0.1)
                yield make_event("Router", "decision",
                                 f"🏢 Target: {verification.company_description}")
                await asyncio.sleep(0.1)
                company_context = verification.company_description
            else:
                yield make_event("Router", "thinking",
                                 f"⚠️ Could not fully verify company, proceeding with available info")
                await asyncio.sleep(0.1)
                if verification.company_description:
                    company_context = verification.company_description

        else:
            yield make_event("Router", "thinking",
                             f"📝 Received request: analyze '{company}' - \"{query}\"")
            await asyncio.sleep(0.1)
            yield make_event("Router", "thinking",
                             "💡 Tip: Provide website URL for more accurate results when company name is common")
            await asyncio.sleep(0.1)

        # ============================
        # Step 1: Router Agent - Intent Analysis
        # ============================
        yield make_event("Router", "thinking",
                         "🤔 Analyzing user intent... What does the user want to know?")
        await asyncio.sleep(0.1)

        # Run blocking LLM call in thread pool so we don't block the event loop
        result = await asyncio.to_thread(router.route, company, website, query, company_context)

        yield make_event("Router", "thinking",
                         f"💭 Reasoning: {result.reasoning}")
        await asyncio.sleep(0.1)

        intent_labels = {
            IntentType.COMPETITOR: "🏢 Competitor Analysis",
            IntentType.FOUNDER: "👤 Founder Lookup",
            IntentType.BUSINESS: "📊 Business Overview",
        }
        label = intent_labels.get(result.intent, "❓ Unknown")
        yield make_event("Router", "decision",
                         f"✅ Intent identified: {label}")
        await asyncio.sleep(0.1)

        yield make_event("Router", "decision",
                         f"📋 Search queries planned: {json.dumps(result.search_queries, ensure_ascii=False)}")
        await asyncio.sleep(0.1)

        # ============================
        # Step 2: Dispatch to specialist
        # ============================
        synthesize_map = {
            IntentType.COMPETITOR: ("Competitor Agent", competitor.synthesize),
            IntentType.FOUNDER: ("Founder Agent", founder.synthesize),
            IntentType.BUSINESS: ("Business Agent", business.synthesize),
        }

        agent_name, synthesize_fn = synthesize_map.get(
            result.intent,
            ("Business Agent", business.synthesize)
        )

        yield make_event(agent_name, "thinking",
                         f"🚀 {agent_name} activated! Starting research...")
        await asyncio.sleep(0.1)

        # Pass company context to specialist if available
        if company_context:
            yield make_event(agent_name, "thinking",
                             f"📌 Using verified company context: {company_context[:100]}...")
            await asyncio.sleep(0.1)

        # ============================
        # Step 3: Execute Tavily searches with detailed logging
        # ============================
        all_search_results = []

        for i, search_query in enumerate(result.search_queries[:2], 1):
            yield make_event("Tavily", "tool_call",
                             f"🔍 Search [{i}]: \"{search_query}\"")
            await asyncio.sleep(0.1)

            yield make_event("Tavily", "thinking",
                             f"📡 Sending request to Tavily API...")
            await asyncio.sleep(0.1)

            # Execute search and measure time
            start_time = time.time()
            search_results = await asyncio.to_thread(search, search_query, 3)
            elapsed = time.time() - start_time

            yield make_event("Tavily", "tool_result",
                             f"⏱️ Tavily responded in {elapsed:.2f}s - Found {len(search_results)} results")
            await asyncio.sleep(0.1)

            # Show each result
            for j, r in enumerate(search_results, 1):
                title = r.get('title', 'No title')[:60]
                url = r.get('url', '')
                content_preview = r.get('content', '')[:100].replace('\n', ' ')

                yield make_event("Tavily", "tool_result",
                                 f"   📄 Result {j}: {title}")
                await asyncio.sleep(0.05)

                yield make_event("Tavily", "tool_result",
                                 f"      🔗 {url}")
                await asyncio.sleep(0.05)

                yield make_event("Tavily", "tool_result",
                                 f"      💬 \"{content_preview}...\"")
                await asyncio.sleep(0.05)

            all_search_results.extend(search_results)

        yield make_event(agent_name, "tool_result",
                         f"📊 Total: {len(all_search_results)} search results collected")
        await asyncio.sleep(0.1)

        # ============================
        # Step 4: Synthesize with LLM
        # ============================
        yield make_event(agent_name, "thinking",
                         "🧠 Synthesizing search results with Claude...")
        await asyncio.sleep(0.1)

        # Run synthesis in thread pool
        answer = await asyncio.to_thread(
            synthesize_fn, company, all_search_results, company_context
        )

        # ============================
        # Step 5: Return final answer
        # ============================
        yield make_event(agent_name, "final_answer", answer)
        await asyncio.sleep(0.1)

        yield make_event("System", "done", "✅ Analysis complete!")

    except Exception as e:
        yield make_event("System", "error", f"❌ Error: {str(e)}")
        yield make_event("System", "error", traceback.format_exc())
