from __future__ import annotations

from typing import List, Dict, Any, Optional

import os
import traceback

from pydantic import BaseModel

from agents import (
    Agent,
    ModelSettings,
    TResponseInputItem,
    Runner,
    RunConfig,
    trace,
    function_tool,
)

import requests
import json
# ---------------------------------------------------------------------------
# MCP HTTP client (naar FastMCP server in app.py)
# ---------------------------------------------------------------------------

MCP_SERVER_URL = os.getenv("ZAS_MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
print("DEBUG ZAS MCP_SERVER_URL:", MCP_SERVER_URL, flush=True)


def _parse_mcp_response(tool_name: str, resp: requests.Response) -> Any:
    """
    Parse de HTTP-response van de MCP-server tot een Python-object.
    Ondersteunt zowel JSON als evt. text/event-stream (SSE).
    """
    ct = (resp.headers.get("Content-Type") or "").lower()
    body = resp.text

    # Baselogging zodat we zien wat er gebeurt
    print(f"[MCP DEBUG] tool={tool_name} status={resp.status_code} content_type={ct}")
    # body tijdelijk loggen bij het debuggen:
    # print(f"[MCP DEBUG] body snippet={body[:200]!r}")

    if not body:
        raise RuntimeError(
            f"MCP response from {tool_name} had empty body (status {resp.status_code})"
        )

    # Gewone JSON
    if "application/json" in ct:
        try:
            return resp.json()
        except Exception as e:
            print(f"[MCP ERROR] JSON decode error for tool {tool_name}: {e}")
            print("Raw body snippet:", body[:300])
            raise

    # text/event-stream (SSE): pak laatste 'data:'-regel met JSON
    if "text/event-stream" in ct:
        data_line = None
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data_line = line[len("data:"):].strip()
        if not data_line:
            raise RuntimeError(f"MCP SSE response from {tool_name} had no data: line")
        try:
            return json.loads(data_line)
        except Exception as e:
            print(f"[MCP ERROR] SSE JSON decode error for tool {tool_name}: {e}")
            print("Raw data_line snippet:", data_line[:300])
            raise

    # Onbekend content-type
    raise RuntimeError(
        f"Unexpected Content-Type from MCP for tool {tool_name}: {ct}. "
        f"Body snippet: {body[:200]!r}"
    )


def _mcp_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Roep een FastMCP tool aan via HTTP JSON-RPC.
    Geeft zoveel mogelijk direct de payload van de tool terug.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    headers = {
        "Content-Type": "application/json",
        # FastMCP wil dat beide types geaccepteerd worden
        "Accept": "application/json, text/event-stream",
    }

    try:
        resp = requests.post(MCP_SERVER_URL, json=payload, headers=headers, timeout=60)
    except Exception:
        print(f"=== MCP CALL FAILED (no HTTP response) for tool '{tool_name}' ===")
        traceback.print_exc()
        print("=== END MCP ERROR ===")
        raise

    try:
        resp.raise_for_status()
    except Exception:
        print(f"=== MCP CALL HTTP ERROR for tool '{tool_name}' ===")
        print("Status code:", resp.status_code)
        print("Headers:", resp.headers)
        print("Body snippet:", resp.text[:500])
        print("=== END MCP ERROR ===")
        raise

    try:
        data = _parse_mcp_response(tool_name, resp)
    except Exception:
        print(f"=== MCP CALL PARSE ERROR for tool '{tool_name}' ===")
        traceback.print_exc()
        print("=== END MCP ERROR ===")
        raise

    # JSON-RPC envelop afwikkelen
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"MCP error from {tool_name}: {data['error']}")

    result = data.get("result") if isinstance(data, dict) else data

    # FastMCP stopt tekst vaak in result.content[0].text
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and first.get("type") == "text":
                return first.get("text")

    return result


# ---------------------------------------------------------------------------
# Function tools (Agents SDK) -> proxy naar FastMCP tools
# ---------------------------------------------------------------------------

# ===== Tickets =====

@function_tool
def tickets_search(query: str, limit: int = 50) -> Any:
    """Zoek tickets via de FastMCP tool 'tickets_search'."""
    return _mcp_call("tickets_search", {"query": query, "limit": limit})


@function_tool
def ticket_get(ticket_id: int) -> Any:
    """Haal details op voor een specifiek ticket."""
    return _mcp_call("ticket_get", {"ticket_id": ticket_id})


@function_tool
def ticket_comments(ticket_id: int, include_public: bool = True) -> Any:
    """Haal comments op voor een ticket."""
    return _mcp_call(
        "ticket_comments",
        {"ticket_id": ticket_id, "include_public": include_public},
    )


@function_tool
def ticket_add_internal_note(ticket_id: int, body: str) -> Any:
    """Voeg een interne notitie toe aan een ticket."""
    return _mcp_call(
        "ticket_add_internal_note",
        {"ticket_id": ticket_id, "body": body},
    )


@function_tool
def ticket_categorize(query: str, limit: int = 300) -> Any:
    """Categoriseer tickets (clustering/labels) op basis van een query."""
    return _mcp_call("ticket_categorize", {"query": query, "limit": limit})


@function_tool
def ticket_generate_draft(query: str, limit: int = 20) -> Any:
    """Genereer concept-antwoorden op basis van tickets."""
    return _mcp_call("ticket_generate_draft", {"query": query, "limit": limit})


@function_tool
def ticket_solution_rate(query: str, limit: int = 200) -> Any:
    """Beoordeel oplossing-/antwoordkwaliteit voor tickets."""
    return _mcp_call("ticket_solution_rate", {"query": query, "limit": limit})


@function_tool
def ticket_metrics(ticket_id: int) -> Any:
    """Geef metrics terug voor een specifiek ticket."""
    return _mcp_call("ticket_metrics", {"ticket_id": ticket_id})


@function_tool
def tickets_tag_stats(query: str, limit: int = 200) -> Any:
    """Geef tag-statistieken terug voor een selectie tickets."""
    return _mcp_call("tickets_tag_stats", {"query": query, "limit": limit})


@function_tool
def tickets_analyze(
    query: str,
    limit: int = 200,
    enrich_with_metrics: bool = True,
    metrics_sample: int = 50,
) -> Any:
    """Geavanceerde analyse van tickets, optioneel verrijkt met metrics."""
    return _mcp_call(
        "tickets_analyze",
        {
            "query": query,
            "limit": limit,
            "enrich_with_metrics": enrich_with_metrics,
            "metrics_sample": metrics_sample,
        },
    )


# ===== Kennisbank =====

@function_tool
def kb_generate_draft(query: str, limit: int = 20) -> Any:
    """Genereer een concept-kennisbankartikel op basis van opgeloste tickets."""
    return _mcp_call("kb_generate_draft", {"query": query, "limit": limit})


@function_tool
def kb_search_articles(
    query: str,
    limit: int = 20,
    label_names: str = "",
    locale: str = "",
) -> Any:
    """Zoek kennisbankartikelen."""
    return _mcp_call(
        "kb_search_articles",
        {
            "query": query,
            "limit": limit,
            "label_names": label_names,
            "locale": locale,
        },
    )


@function_tool
def kb_create_draft_article(
    section_id: Optional[int] = None,
    title: str = "",
    body: str = "",
    locale: str = "nl",
    permission_group_id: Optional[int] = None,
    user_segment_id: Optional[int] = None,
) -> Any:
    """Maak een concept-kennisbankartikel aan."""
    return _mcp_call(
        "kb_create_draft_article",
        {
            "section_id": section_id,
            "title": title,
            "body": body,
            "locale": locale,
            "permission_group_id": permission_group_id,
            "user_segment_id": user_segment_id,
        },
    )


# ===== Reporting =====

@function_tool
def tickets_export_csv(
    query: str,
    path: str = "tickets_export.csv",
    limit: int = 1000,
) -> Any:
    """Exporteer tickets naar CSV (pad is relatief t.o.v. MCP-server)."""
    return _mcp_call(
        "tickets_export_csv",
        {
            "query": query,
            "path": path,
            "limit": limit,
        },
    )


# ===== General =====

@function_tool
def ping() -> str:
    """Controleer of de FastMCP-server bereikbaar is."""
    res = _mcp_call("ping", {})
    # ping-tool geeft gewoon "pong" terug
    return str(res)


# ===== Jira =====

@function_tool
def jira_get_issue(issue_key: str, max_comments: int = 5) -> Any:
    """Haal een Jira-issue op met optioneel aantal comments."""
    return _mcp_call(
        "jira_get_issue",
        {"issue_key": issue_key, "max_comments": max_comments},
    )


# ===== Confluence =====

@function_tool
def confluence_search_pages(query: str, limit: int = 10) -> Any:
    """Zoek Confluence-pagina's."""
    return _mcp_call(
        "confluence_search_pages",
        {"query": query, "limit": limit},
    )


@function_tool
def confluence_get_page(page_id: str, include_body: bool = True) -> Any:
    """Haal een specifieke Confluence-pagina op."""
    return _mcp_call(
        "confluence_get_page",
        {"page_id": page_id, "include_body": include_body},
    )


# ---------------------------------------------------------------------------
# ZAS Agent definitie
# ---------------------------------------------------------------------------

zas = Agent(
    name="ZAS",
    instructions="""
BELANGRIJK: IDs VOOR KENNISBANKARTIKELEN
- Gebruik altijd:
- Permission ID = 295492
- Segment ID = 138711
- Section ID = 115000214091
- Als deze ontbreken: vraag eerst op met kb_list_permissions_and_segments.
Je bent de Zendesk Intelligence Agent.

Analyseer supportdata om trends, efficiëntie en ticketcategorieën te bepalen en kennisartikelen te schrijven.  
Je neemt nooit contact op met klanten; alle output is intern.

TOOLS
- tickets_search – zoek tickets  
- ticket_cluster_topics – detecteer thema’s  
- ticket_categorize – classificeer types  
- ticket_solution_rate – meet oplossingsgraad  
- ticket_generate_draft – maak KB-concept  
- ticket_comments – lees ticketcontext  
- ticket_add_internal_note – voeg interne notitie toe (Wanneer er een comment wordt toegevoegd aan een ticket zet er dan - Comment van ZAS <3 - bij)  
- kb_search_articles – zoek bestaande KB’s  
- kb_create_draft_article – maak nieuw conceptartikel

GEBRUIK
- Bij een ticket analyse check meteen of er een oude ticket is met hetzelfde probleem + kennisbank artikelen die relevant kunnen zijn.
- Combineer tools logisch (bv. cluster → rate → draft).  
- Gebruik add_internal_note voor inzichten: “Situatie… Analyse… Advies…”.  
- Controleer met kb_search_articles of het onderwerp al bestaat; maak anders een draft.  
- Verwijder of maskeer PII met [REDACTED].  
- Meld kort als een tool faalt en ga verder.  
- Standaardquery: `status:solved created>2025-10-01`, limit 100.
- Voor relevante kennisbankartikelen geef je altijd de link (https://... zonder HTML markeringen!) naar de gevonden artikelen mee in jouw antwoord naar de support medewerker
- wanneer er gevraagd word om een interne comment te plaatsen, zet je je volledige analyse in de comment, beginnend met "Analyse door ZAS Agent:", gevolgd door je analyse over desbetreffende ticket.
- Wanneer er gevraagd word om een volledige ticketanalyse uit te voeren, geef dan een gestructureerd antwoord i.p.v. de directe JSON te laten zien.

Gebruik kb_ensure_agent_concept_section om de sectie voor ZAS-conceptartikelen te bepalen.
Gebruik de teruggegeven section_id bij kb_create_draft_article.
Maak geen eigen secties; gebruik altijd deze tool.
- Als een ticket geparkeerd is en er staat een Jira-issue key in het ticket (bijv. in een custom veld of in de omschrijving), gebruik jira_get_issue om de status, toegewezen developer en laatste comments van het technische team op te halen en geef een begrijpelijke samenvatting aan de klant
- Als je inhoudelijke uitleg nodig hebt over de werking van onze software, zoek dan eerst met confluence_search_pagesop relevante zoektermen (feature, module, foutmelding, etc.) en gebruik daarna confluence_get_page om de inhoud te lezen. Vat deze informatie samen in je eigen woorden voor de klant, zonder ruwe HTML te tonen.
OUTPUT
- Wanneer er gevraagd word om een kennisbank concept te maken dan gebruik je kb_list_permissions_and_segments
Permission ID = 295492
Segment ID = 138711
Section ID = 115000214091
- Antwoord beknopt en professioneel in het Nederlands.  
- Analytics → korte samenvatting + JSON.  
- KB → HTML (**PROBLEEM**, **OORZAAK**, **OPLOSSING**, **WANNEER ESCALEREN**) + metadata-JSON.
Voor kennisbankartikelen genereer je altijd HTML (geen Markdown), bijv.:
<h2><strong>PROBLEEM</strong></h2>
<p>...</p>
<h2><strong>OORZAAK</strong></h2>
<p>...</p>
<h2><strong>OPLOSSING</strong></h2>
<p>...</p>
<ol>
  <li>Stap 1...</li>
  <li>Stap 2...</li>
</ol>
<h2><strong>WANNEER ESCALEREN</strong></h2>
<p>...</p>
De string die je aan kb_create_draft_article.body meegeeft moet direct geldige HTML zijn.
Gebruik geen Markdown-syntax zoals **vet**, _cursief_ of ![afbeelding](url).
""",
    model="gpt-4.1-mini",
    tools=[
        # Tickets
        tickets_search,
        ticket_get,
        ticket_comments,
        ticket_add_internal_note,
        ticket_categorize,
        ticket_generate_draft,
        ticket_solution_rate,
        ticket_metrics,
        tickets_tag_stats,
        tickets_analyze,
        # KB
        kb_generate_draft,
        kb_search_articles,
        kb_create_draft_article,
        # Reporting
        tickets_export_csv,
        # General
        ping,
        # Jira
        jira_get_issue,
        # Confluence
        confluence_search_pages,
        confluence_get_page,
    ],
    model_settings=ModelSettings(
        temperature=0.9,
        max_output_tokens=1024,
    ),
)


# ---------------------------------------------------------------------------
# Workflow API (optioneel)
# ---------------------------------------------------------------------------

class WorkflowInput(BaseModel):
    input_as_text: str


class WorkflowConfig(BaseModel):
    steps: List[Dict[str, Any]] = []


async def run_zas_workflow(
    workflow: Dict[str, Any],
    conversation_history: Optional[List[TResponseInputItem]] = None,
) -> Dict[str, Any]:
    if conversation_history is None:
        conversation_history = []

    workflow_input = WorkflowInput(**workflow.get("input", {}))
    workflow_config = WorkflowConfig(**workflow.get("config", {}))
    _ = workflow_config

    user_item: TResponseInputItem = {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": workflow_input.input_as_text,
            }
        ],
    }

    conversation_history.append(user_item)

    zas_result_temp = await Runner.run(
        zas,
        input=[*conversation_history],
        run_config=RunConfig(
            trace_metadata={
                "__trace_source__": "agent-workflow",
                "workflow_id": workflow.get("id", "wf_unknown"),
            }
        ),
    )

    conversation_history.extend(
        [item.to_input_item() for item in zas_result_temp.new_items]
    )

    return {
        "output_text": zas_result_temp.final_output_as(str),
    }


# ---------------------------------------------------------------------------
# Chat-turn API – wordt aangeroepen door chat_api.py
# ---------------------------------------------------------------------------

async def run_zas_chat_turn(
    message: str,
    history: Optional[List[TResponseInputItem]],
    tenant_id: Optional[str] = None,
    url: Optional[str] = None,
) -> tuple[str, List[TResponseInputItem]]:
    if history is None:
        history = []

    parts: list[str] = []
    if tenant_id:
        parts.append(f"[tenantId: {tenant_id}]")
    if url:
        parts.append(f"[pageUrl: {url}]")
    parts.append(message)

    user_text = "\n".join(parts)

    user_item: TResponseInputItem = {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": user_text,
            }
        ],
    }

    with trace("ZD-ZAS chat-turn"):
        zas_result_temp = await Runner.run(
            zas,
            input=[*history, user_item],
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "chat-api",
                    "workflow_id": "wf_68fb7d9df5548190af58dbdf209871160b343683029ac1e9",
                }
            ),
        )

    updated_history: List[TResponseInputItem] = [
        *history,
        user_item,
        *[item.to_input_item() for item in zas_result_temp.new_items],
    ]

    reply_text = zas_result_temp.final_output_as(str)

    return reply_text, updated_history
