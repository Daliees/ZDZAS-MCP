# 🧠 ZDZAS-MCP

**Zendesk AI Management & Integration Server**

<small>(fotoZAS-placeholder)</small>

---

## 🚀 Over het project

ZDZAS-MCP is een krachtige, modulaire MCP-server gebouwd voor volledige integratie tussen:

- **Zendesk** (tickets, kennisbank, gebruikersdata)
- **Jira** (technische incidenten & developer updates)
- **Confluence** (productdocumentatie & handleidingen)
- **AI-agenten** die beslissingen nemen op basis van data uit deze systemen

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
- ✔ **Salesforce Lightning Web Component** voor chat interface met streaming responses
- ✔ **Real-time AI Chat** met typing indicators en conversation management

---

## 🖼️ Screenshots

Vervang onderstaande placeholders door jouw echte screenshots wanneer beschikbaar.

- 📌 MCP Server Dashboard
- 📌 Zendesk AI Agent met MCP Tools
- 📌 Jira-informatie direct in de Zendesk AI
- 📌 Confluence-documentatie automatisch opgehaald

---

## 🧩 Tool Overzicht

Hieronder staat een overzicht van alle tools die de MCP-server exposeert voor de Zendesk AI agent.

### 🔧 Algemene Tools

| Tool | Doel |
|------|------|
| `ping` | Test of de MCP-server actief is |
| `tickets_export_csv` | Exporteert tickets naar CSV-bestand |
| `tickets_search` | Geavanceerde zoekopdrachten in Zendesk |
| `ticket_get` | Haalt ticketdetails op |
| `ticket_comments` | Haalt alle comments op |
| `ticket_add_internal_note` | Voegt interne notitie toe |
| `tickets_tag_stats` | Analyseert tag-statistieken |

### 📊 Analyse & AI Tools

| Tool | Doel |
|------|------|
| `ticket_cluster_topics` | Clustert tickets op onderwerp |
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
| `kb_list_permissions_and_segments` | Haalt toegangs- en permissiegroepen op |

### 🛠️ Jira Tools

| Tool | Doel |
|------|------|
| `jira_get_issue` | Haalt status, comments & updates van Jira-issues op |

**Gebruiksvoorbeelden:**
- Supportticket is "geparkeerd" → haal real-time developer updates op
- Jira-issue bevat laatste foutanalyse → toon samenvatting aan agent

### 📘 Confluence Tools

| Tool | Doel |
|------|------|
| `confluence_search_pages` | Zoekt productdocumentatie en handleidingen |
| `confluence_get_page` | Haalt volledige pagina-inhoud op |

**Gebruiksvoorbeelden:**
- Agent heeft productuitleg nodig
- Ticket bevat foutmelding → zoek direct in Confluence-documentatie

---

## 🔒 Veiligheid & Authenticatie

Het project maakt gebruik van veilige API-authenticatie via environment variables:

- **Zendesk** subdomein, e-mail & API-token
- **Jira** base URL, e-mail & API-token
- **Confluence** base URL, e-mail & API-token

Deze worden dynamisch ingelezen vanuit:
- `./.env` (naast app.py)
- of systeemvariabelen in productie.

---

## 🧱 Architectuur

```
ZDZAS-MCP/
│
├── app.py                     # MCP server + alle tools
├── chat_api.py                # FastAPI chat endpoint met streaming
├── zas_agent.py               # AI agent met tool integraties
├── .env                       # Environment configuratie
├── salesforce/                # Salesforce Lightning Web Component
│   ├── force-app/
│   │   └── main/default/
│   │       ├── lwc/zasChatUtility/     # Chat component
│   │       └── classes/                # Apex controllers
│   ├── README.md              # Salesforce setup guide
│   ├── QUICKSTART.md          # Quick setup guide
│   └── test-harness.html      # Local testing tool
├── docs/
│   ├── screenshots/           # Screenshot afbeeldingen
│   └── images/                # Banners / visuals
└── requirements.txt           # Dependencies
```

---

## 💼 Salesforce Integratie

ZDZAS-MCP bevat nu een volledig functionerende **Salesforce Lightning Web Component** die:

- 🎨 Moderne chat interface biedt met Salesforce Lightning Design System
- 💬 Real-time streaming responses toont met typing indicators
- 🔄 Conversatie context behoudt over meerdere berichten
- 🚀 Direct integreert met de chat API endpoint
- 📱 Responsive werkt op desktop en mobile
- ✨ Alle enterprise features bevat: error handling, session management, tests

### Quick Start voor Salesforce

```bash
# 1. Start de API services
python app.py        # Terminal 1
python chat_api.py   # Terminal 2

# 2. Deploy naar Salesforce
cd salesforce
sf org login web --alias my-org
sf project deploy start --source-dir force-app

# 3. Configureer Remote Site Settings in Salesforce Setup
# 4. Voeg component toe aan een Lightning page
```

📖 **Volledige documentatie**: Zie [`salesforce/README.md`](salesforce/README.md) voor:
- Gedetailleerde installatie instructies
- API endpoint configuratie
- Testing in Salesforce
- Troubleshooting guide
- Advanced customization opties

🧪 **Test lokaal eerst**: Open [`salesforce/test-harness.html`](salesforce/test-harness.html) in je browser om de API te testen voordat je naar Salesforce deployt.

---

## 🤖 Hoe de AI-agent dit gebruikt

De MCP-tools worden automatisch zichtbaar in de Zendesk AI Agent.

De agent gebruikt deze tools volgens logica zoals:
- Haal Jira-status op → samenvatten voor supportmedewerker
- Vind relevante Confluence-documenten → gebruik in antwoord
- Genereer KB-artikelen → automatisch opgeslagen als concept
- Analyseer tickets of clusters → aanbevelingen genereren

Dit maakt de agent:
- **slimmer**
- **contextbewust**
- **realtime**
- **efficiënter**

---

## 🔧 Onderhoud & uitbreidbaarheid

Het project is modulair opgezet:

- Tools worden toegevoegd via `@mcp.tool`
- Helpers zijn gegroepeerd (Zendesk, Jira, Confluence)
- Nieuwe tools zijn eenvoudig te registreren
- Logging & foutafhandeling zijn centraal geregeld
