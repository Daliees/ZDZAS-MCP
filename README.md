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

## 📚 Documentation

For detailed documentation, please see the [docs](docs/) folder:
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration instructions
- **[Architecture](docs/ARCHITECTURE.md)** - Project structure and design
- **[Tools Reference](docs/TOOLS.md)** - Complete guide to all available tools

---

## 🌟 Kernfunctionaliteit

- ✔ Automatische ticketanalyse & categorisatie
- ✔ Kennisbankartikelen genereren (draft + final)
- ✔ Technische updates ophalen uit Jira (status, comments, developer notes)
- ✔ Productdocumentatie ophalen uit Confluence
- ✔ Ticket-clustering, metrics, tagging & exports
- ✔ Modulair ontwerp — eenvoudig nieuwe tools toevoegen
- ✔ Veilige integratie via env-variabelen

---

## 🖼️ Screenshots

Vervang onderstaande placeholders door jouw echte screenshots wanneer beschikbaar.

- 📌 MCP Server Dashboard
- 📌 Zendesk AI Agent met MCP Tools
- 📌 Jira-informatie direct in de Zendesk AI
- 📌 Confluence-documentatie automatisch opgehaald

---

## 🧩 Tool Overzicht

Voor een volledig overzicht van alle tools, zie de [Tools Reference](docs/TOOLS.md) documentatie.

### Categorieën

- **Algemene Tools** - ping, tickets_export_csv, tickets_search, ticket_get, ticket_comments, etc.
- **Analyse & AI Tools** - ticket_cluster_topics, ticket_categorize, ticket_generate_draft, etc.
- **Kennisbank Tools** - kb_search_articles, kb_generate_draft, kb_create_draft_article, etc.
- **Jira Tools** - jira_get_issue voor real-time developer updates
- **Confluence Tools** - confluence_search_pages, confluence_get_page voor productdocumentatie

---

## 🔒 Veiligheid & Authenticatie

Het project maakt gebruik van veilige API-authenticatie via environment variables:

- **Zendesk** subdomein, e-mail & API-token
- **Jira** base URL, e-mail & API-token
- **Confluence** base URL, e-mail & API-token

Deze worden dynamisch ingelezen vanuit `.env` (gebruik `.env.example` als template).

Voor gedetailleerde installatie-instructies, zie de [Setup Guide](docs/SETUP.md).

---

## 🧱 Architectuur

Voor een gedetailleerd overzicht van de projectstructuur, zie de [Architecture](docs/ARCHITECTURE.md) documentatie.

Het project is modulair opgezet met gescheiden tool-modules voor verschillende functionaliteiten (Zendesk, Jira, Confluence).

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
