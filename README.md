# LinkedIn MCP Automation Project – Full Specification

## 0 · Quick Summary
Build a human‑like LinkedIn activity agent that runs ~10 h/day on one personal account. It must keep risk low (strict rate limits, random delays, no politics/toxicity) while using Model Context Protocol (MCP) tooling. All LLM calls default to `gpt-4.1-nano`.

### Fast‑Test Mode (temporary)
To validate rapidly before human‑like timing, set `FAST_TEST=true`:
- Delay window shrinks to **1–5 s**.
- Daily caps bypassed; scheduler processes entire queue once.
- Optional: `MOCK_LINKEDIN=true` to stub Playwright calls and log only.
- Optional: `MODERATION=off` to skip OpenAI moderation (re‑enable before production).

Unset `FAST_TEST` once everything operates end‑to‑end; system reverts to safe caps and randomized delays.

## 1 · Objectives
1. **Automate** daily LinkedIn actions (invites, likes, comments) under safe caps.
2. **Generate** short, positive, professional comments via GPT‑4.1‑nano.
3. **Log** every action to a local SQLite DB and expose basic analytics.
4. **Modular design** so future features slot in easily.

## 2 · Risk & Compliance
- **Max invites/day**: 30 (20 for the first week – auto‑ramp)
- **Max likes/day**: 40
- **Max comments/day**: 12
- **Action spacing**: Random 120–240 s; never >5 invites/15 min
- **Active hours**: 08:30–12:30 and 14:00–18:30 America/Denver
- **Politics/toxicity**: Blocked by moderation filter
- **Captchas**: Abort run & notify if >0 captchas

## 3 · Key Technologies
- Python 3.11+
- FastMCP (MCP tool protocol)
- Playwright for LinkedIn automation
- OpenAI Python SDK
- SQLite3 for state persistence
- AsyncIO / LangGraph for orchestration

## 4 · Repository Layout
```
linkedin-mcp-bot/
├── .env.example
├── README.md
├── Dockerfile
├── docker-compose.yml
├── mcp_server.py         # Phase 2 tool‑server
├── orchestrator.py       # Phase 3 scheduler
├── commenter.py          # Phase 4 LLM utils
├── prospecting.yml       # Phase 5 keywords/companies
├── stats.py             # Phase 6 CLI analytics
├── dashboard.py         # Phase 6 Streamlit dashboard MVP
└── config/daily.yml     # Phase 7 daily caps & schedule
```

## 5 · Environment Variables (`.env`)
```bash
OPENAI_API_KEY="sk-…"
GPT_MODEL="gpt-4.1-nano"
LINKEDIN_USERNAME="you@example.com"
LINKEDIN_PASSWORD="…"
FAST_TEST=false
MOCK_LINKEDIN=false
MODERATION=on
ACTIVITY_CONFIG="./config/daily.yml"
DB_URL="sqlite:///state.db"
TZ="America/Denver"
```

## 6 · Getting Started
1. Clone this repo and copy `.env.example` to `.env`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the MCP tool server:
   ```bash
   FAST_TEST=true python mcp_server.py
   ```
4. In another shell, start the scheduler:
   ```bash
   FAST_TEST=true python orchestrator.py
   ```
5. View analytics:
   ```bash
   python stats.py
   streamlit run dashboard.py
   ``` 