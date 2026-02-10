# 🧠 ZDZAS-MCP

**Zendesk AI Management & Integration Server — powered by LangChain**

---

## 🚀 Over het project

ZDZAS-MCP is een krachtige, modulaire MCP-server gebouwd voor volledige integratie tussen:

- **Zendesk** (tickets, kennisbank, gebruikersdata)
- **Jira** (technische incidenten & developer updates)
- **Confluence** (productdocumentatie & handleidingen)
- **AI-agenten** (LangChain) die beslissingen nemen op basis van data uit deze systemen

Het project breidt de standaard Zendesk AI-functionaliteit uit met een set slimme tools die real-time context, analyses en contentgeneratie mogelijk maken. Hierdoor kunnen supportmedewerkers sneller, consistenter en met meer kennis antwoorden — zonder handmatig te schakelen tussen systemen.

---

## 🌟 Kernfunctionaliteit

- ✔ Automatische ticketanalyse & categorisatie
- ✔ Kennisbankartikelen genereren (draft + final)
- ✔ Technische updates ophalen uit Jira (status, comments, developer notes)
- ✔ Productdocumentatie ophalen uit Confluence
- ✔ Ticket-clustering, metrics, tagging & exports
- ✔ Modulair ontwerp — eenvoudig nieuwe tools toevoegen
- ✔ Veilige integratie via env-variabelen
- ✔ **LangChain-powered** AI agent met tool-calling

---

## 🧩 Architectuur

```
ZDZAS-MCP/
│
├── app.py                     # MCP server entrypoint (HTTP mode)
├── core.py                    # Centrale config, env, API helpers
├── zas_agent.py               # LangChain agent + tool definities
├── chat_api.py                # FastAPI chat endpoint
├── mcp_proxy.py               # MCP HTTP proxy
├── server_wrapper.py          # Flask wrapper
│
├── tools_ticket.py            # MCP tools: tickets
├── tools_kb.py                # MCP tools: kennisbank
├── tools_jira.py              # MCP tools: Jira
├── tools_confluence.py        # MCP tools: Confluence
├── tools_reporting.py         # MCP tools: reporting/export
├── tools_general.py           # MCP tools: algemeen
│
├── src/zendesk_mcp_server/    # Installeerbaar module-pakket
│   ├── __init__.py
│   ├── server.py
│   └── zendesk_client.py
│
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project metadata & build config
├── Dockerfile                 # Docker containerisatie
├── Procfile                   # Heroku deployment
├── start_mcp.sh               # Startup script (MCP + ngrok)
├── .env.example               # Environment variabelen template
└── LICENSE                    # Apache 2.0
```

### Twee lagen

| Laag | Beschrijving |
|------|-------------|
| **MCP Server** | FastMCP tools (`tools_*.py`) die de Zendesk/Jira/Confluence APIs wrappen. Bereikbaar via HTTP JSON-RPC op `/mcp`. |
| **LangChain Agent** | `zas_agent.py` definieert LangChain `@tool` functies en bouwt de agent met `langchain.agents.create_agent`. De agent roept de API helpers uit `core.py` direct aan (geen HTTP roundtrip). |

---

## 🛠️ Tool Overzicht

### 🔧 Algemene Tools

| Tool | Doel |
|------|------|
| `ping` | Test of de agent/MCP-server actief is |
| `tickets_export_csv` | Exporteert tickets naar CSV-bestand |
| `tickets_search` | Geavanceerde zoekopdrachten in Zendesk |
| `ticket_get` | Haalt ticketdetails op |
| `ticket_comments` | Haalt alle comments op |
| `ticket_add_internal_note` | Voegt interne notitie toe |
| `tickets_tag_stats` | Analyseert tag-statistieken |

### 📊 Analyse & AI Tools

| Tool | Doel |
|------|------|
| `ticket_categorize` | Categoriseert tickets automatisch |
| `ticket_generate_draft` | Genereert conceptantwoorden via AI |
| `ticket_solution_rate` | Berekent oplossingstypes / succesratio's |
| `tickets_analyze` | End-to-end ticketanalyse |

### 📚 Kennisbank Tools

| Tool | Doel |
|------|------|
| `kb_search_articles` | Zoekt artikelen in Zendesk Guide |
| `kb_generate_draft` | Genereert nieuwe KB-artikelinhoud |
| `kb_create_draft_article` | Maakt conceptartikelen in een sectie |

### 🛠️ Jira Tools

| Tool | Doel |
|------|------|
| `jira_get_issue` | Haalt status, comments & updates van Jira-issues op |

### 📘 Confluence Tools

| Tool | Doel |
|------|------|
| `confluence_search_pages` | Zoekt productdocumentatie en handleidingen |
| `confluence_get_page` | Haalt volledige pagina-inhoud op |

---

## 🔧 Installatie & Gebruik

### Vereisten

- Python 3.12+
- OpenAI API key
- Zendesk subdomain, e-mail & API token

### Lokale ontwikkeling

```bash
# 1. Maak een virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Installeer dependencies
pip install -r requirements.txt

# 3. Configureer environment
cp .env.example .env
# Vul de API keys en credentials in

# 4. Start de MCP server (optioneel, voor externe tools)
python app.py
# Server: http://127.0.0.1:8000/mcp

# 5. Start de Chat API (LangChain agent)
python chat_api.py
# Chat endpoint: http://127.0.0.1:9000/chat
```

### Docker

```bash
docker build -t zdzas-mcp .
docker run --env-file .env zdzas-mcp
```

---

## 🔒 Veiligheid & Authenticatie

Het project maakt gebruik van veilige API-authenticatie via environment variables:

- **Zendesk** subdomein, e-mail & API-token
- **Jira** base URL, e-mail & API-token (optioneel)
- **Confluence** base URL, e-mail & API-token (optioneel)
- **OpenAI** API key (voor LangChain agent)

Deze worden dynamisch ingelezen vanuit `.env` of systeemvariabelen.

---

## 🤖 LangChain Agent

De AI-agent is gebouwd met [LangChain](https://python.langchain.com/) en gebruikt:

- **`langchain.agents.create_agent`** — creëert een tool-calling agent graph
- **`langchain_openai.ChatOpenAI`** — OpenAI chat model (default: `gpt-4.1-mini`)
- **`langchain_core.tools.tool`** — decorator voor tool-definities
- **`langchain_core.messages`** — gestructureerd berichtenformaat

De agent:
- Haalt Jira-status op → samenvatten voor supportmedewerker
- Vindt relevante Confluence-documenten → gebruikt in antwoord
- Genereert KB-artikelen → automatisch opgeslagen als concept
- Analyseert tickets of clusters → aanbevelingen genereren

---

## 🔧 Onderhoud & uitbreidbaarheid

Het project is modulair opgezet:

- LangChain tools worden gedefinieerd met `@tool` decorator in `zas_agent.py`
- MCP tools worden geregistreerd via `@mcp.tool` in `tools_*.py`
- API helpers zijn gegroepeerd in `core.py` (Zendesk, Jira, Confluence)
- Nieuwe tools zijn eenvoudig toe te voegen aan beide lagen
- Model is configureerbaar via `ZAS_MODEL` environment variabele
