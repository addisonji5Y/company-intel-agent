"""
FastAPI Server - Serves the frontend and provides SSE endpoint for agent events.

Endpoints:
- GET /           → Serves the frontend HTML
- POST /analyze   → SSE stream of agent events
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from backend.models import UserRequest
from backend.orchestrator import run_pipeline

# Load .env file (absolute path + override to handle pre-existing empty env vars)
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

app = FastAPI(title="Company Intel Agent")

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/analyze")
async def analyze(request: UserRequest):
    """
    Main endpoint: accepts company info + query, returns SSE stream.
    Each event is a JSON object with {agent, event, content}.
    """
    import json

    async def event_generator():
        async for event_dict in run_pipeline(request):
            yield {
                "event": "message",
                "data": json.dumps(event_dict, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


# Serve any other static files (CSS, JS if we split them later)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
