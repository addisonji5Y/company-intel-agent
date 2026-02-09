# Company Intel Agent

> A lightweight multi-agent system for company intelligence — built for **Vibe Coding Training**.

Demonstrates how LLM agents think, route, use tools, and collaborate — all with transparent, real-time logging.

## Architecture

```
User Input (company + question)
        │
        ▼
┌──────────────────┐
│   Router Agent    │  ← Claude decides the intent
│  "What does the   │     Returns: intent + search queries
│   user want?"     │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
🏢 Competitor 👤 Founder  📊 Business
   Agent        Agent       Agent
    │            │           │
    ▼            ▼           ▼
  Tavily       Tavily      Tavily
  Search       Search      Search
    │            │           │
    ▼            ▼           ▼
  Claude       Claude      Claude
  Synthesize   Synthesize  Synthesize
    │            │           │
    └─────┬──────┴───────────┘
          ▼
    Final Answer (streamed to frontend)
```

## Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/addisonji5Y/company-intel-agent.git
cd company-intel-agent
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
cp .env.example .env
# Edit .env and add your keys:
# ANTHROPIC_API_KEY=sk-ant-...
# TAVILY_API_KEY=tvly-...
```

### 3. Run

```bash
python -m backend.main
```

Open http://localhost:8000 in your browser.

---

## 🚀 Deploy to Hugging Face Spaces

### Deploy via Hugging Face Web UI

1. **Create a new Space**
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose a name for your Space
   - Select **Docker** as the SDK
   - Choose visibility (Public/Private)

2. **Upload files**
   - Upload all project files to the Space repository
   - Required files:
     ```
     ├── Dockerfile
     ├── requirements.txt
     ├── backend/
     │   ├── __init__.py
     │   ├── main.py
     │   ├── orchestrator.py
     │   ├── models.py
     │   ├── agents/
     │   │   ├── __init__.py
     │   │   ├── router.py
     │   │   ├── competitor.py
     │   │   ├── founder.py
     │   │   └── business.py
     │   └── tools/
     │       ├── __init__.py
     │       ├── llm.py
     │       └── search.py
     └── frontend/
         └── index.html
     ```

3. **Configure Secrets**
   - Go to your Space's **Settings** → **Repository secrets**
   - Add the following secrets:
     - `ANTHROPIC_API_KEY`: Your Anthropic API key
     - `TAVILY_API_KEY`: Your Tavily API key

4. **Wait for build**
   - The Space will automatically build and deploy
   - Check the "Logs" tab if there are any issues
---

## 🔧 Troubleshooting Deployment

### Common Issues

**1. Build fails with "Module not found"**
- Ensure all `__init__.py` files are present in `backend/`, `backend/agents/`, and `backend/tools/`

**2. App shows "Error: ANTHROPIC_API_KEY not set"**
- Go to Space Settings → Repository secrets
- Add your API keys (they are injected as environment variables)

**3. App doesn't load / Connection refused**
- Check that Dockerfile uses port 7860 (Hugging Face requirement)
- Verify the CMD in Dockerfile points to correct module path

**4. Slow cold starts**
- First request after idle period may take 30-60 seconds
- Consider upgrading to a paid Space for persistent containers

### Viewing Logs

- Go to your Space → **Logs** tab
- Select "Build" to see Docker build logs
- Select "Container" to see runtime logs

---

## Project Structure

```
company-intel-agent/
├── backend/
│   ├── main.py              # FastAPI server + SSE endpoint
│   ├── orchestrator.py      # Agent pipeline coordinator
│   ├── models.py            # Data models (intent types, events)
│   ├── agents/
│   │   ├── router.py        # 🧠 Router: understands intent
│   │   ├── competitor.py    # 🏢 Finds competitors
│   │   ├── founder.py       # 👤 Finds founders
│   │   └── business.py      # 📊 Business overview
│   └── tools/
│       ├── llm.py           # Claude API wrapper
│       └── search.py        # Tavily search wrapper
├── frontend/
│   └── index.html           # Single-file frontend (HTML+CSS+JS)
├── Dockerfile               # For Hugging Face Spaces deployment
├── .dockerignore
├── requirements.txt
└── README.md
```

## API Keys

- **Anthropic**: https://console.anthropic.com/
- **Tavily**: https://tavily.com/ (free tier: 1000 searches/month)

## License

MIT
