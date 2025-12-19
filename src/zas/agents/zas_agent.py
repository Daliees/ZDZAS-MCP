"""ZAS Agent - main conversational agent."""

from typing import List, Dict, Any, Optional

from agents import (
    Agent,
    ModelSettings,
    TResponseInputItem,
    Runner,
    RunConfig,
    function_tool,
)

from .mcp_client import MCPClient


class ZASAgent:
    """
    ZAS conversational agent with MCP tool integration.
    
    This agent handles user queries about Zendesk tickets, knowledge base,
    Jira issues, and Confluence pages.
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        """
        Initialize ZAS agent.
        
        Args:
            mcp_client: MCP client for tool calls
            model: LLM model to use
        """
        self.mcp_client = mcp_client
        self.model = model
        
        # Create agent tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = Agent(
            name="ZAS Agent",
            model=ModelSettings(model=model, temperature=0.1),
            instructions=self._get_instructions(),
            tools=self.tools,
        )
    
    def _get_instructions(self) -> str:
        """Get agent system instructions."""
        return """
Je bent ZAS (Zendesk Agent System), een slimme assistent voor Zendesk support agents.

Jouw taken:
- Zoeken en opvragen van Zendesk tickets
- Toevoegen van interne notities aan tickets
- Zoeken in de kennisbank (Help Center)
- Genereren van kennisbankartikelen op basis van opgeloste tickets
- Opvragen van Jira issues (indien geconfigureerd)
- Zoeken in Confluence pagina's (indien geconfigureerd)

Antwoord altijd in het Nederlands, tenzij de gebruiker expliciet om een andere taal vraagt.

Wees beknopt en to-the-point. Geef alleen de gevraagde informatie.

Als je een foutmelding krijgt van een tool, leg dit duidelijk uit aan de gebruiker.
"""
    
    def _create_tools(self) -> List:
        """Create function tools for the agent."""
        tools = []
        
        # Ticket tools
        @function_tool
        def tickets_search(query: str, limit: int = 50) -> Any:
            """Search for Zendesk tickets using Zendesk search syntax."""
            return self.mcp_client.call_tool("tickets_search", {
                "query": query,
                "limit": limit
            })
        
        @function_tool
        def ticket_get(ticket_id: int) -> Any:
            """Get full details of a specific ticket."""
            return self.mcp_client.call_tool("ticket_get", {
                "ticket_id": ticket_id
            })
        
        @function_tool
        def ticket_comments(ticket_id: int, include_public: bool = True) -> Any:
            """Get all comments for a ticket."""
            return self.mcp_client.call_tool("ticket_comments", {
                "ticket_id": ticket_id,
                "include_public": include_public
            })
        
        @function_tool
        def ticket_add_internal_note(ticket_id: int, body: str) -> Any:
            """Add an internal note (private comment) to a ticket."""
            return self.mcp_client.call_tool("ticket_add_internal_note", {
                "ticket_id": ticket_id,
                "body": body
            })
        
        # Knowledge base tools
        @function_tool
        def kb_search_articles(
            query: str,
            limit: int = 20,
            label_names: str = "",
            locale: str = ""
        ) -> Any:
            """Search knowledge base articles."""
            return self.mcp_client.call_tool("kb_search_articles", {
                "query": query,
                "limit": limit,
                "label_names": label_names,
                "locale": locale
            })
        
        @function_tool
        def kb_generate_draft(query: str, limit: int = 20) -> Any:
            """Generate draft knowledge base article from solved tickets."""
            return self.mcp_client.call_tool("kb_generate_draft", {
                "query": query,
                "limit": limit
            })
        
        # Jira tools
        @function_tool
        def jira_get_issue(issue_key: str, max_comments: int = 5) -> Any:
            """Get Jira issue details."""
            return self.mcp_client.call_tool("jira_get_issue", {
                "issue_key": issue_key,
                "max_comments": max_comments
            })
        
        # Confluence tools
        @function_tool
        def confluence_search_pages(
            query: str,
            limit: int = 10,
            space_key: str = ""
        ) -> Any:
            """Search Confluence pages."""
            return self.mcp_client.call_tool("confluence_search_pages", {
                "query": query,
                "limit": limit,
                "space_key": space_key
            })
        
        tools = [
            tickets_search,
            ticket_get,
            ticket_comments,
            ticket_add_internal_note,
            kb_search_articles,
            kb_generate_draft,
            jira_get_issue,
            confluence_search_pages,
        ]
        
        return tools
    
    def run(
        self,
        message: str,
        history: Optional[List[TResponseInputItem]] = None
    ) -> str:
        """
        Run the agent with a user message.
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            Agent response
        """
        if history is None:
            history = []
        
        # Append user message to history
        history.append({"role": "user", "content": message})
        
        # Run agent
        runner = Runner(self.agent)
        result = runner.run(
            input=history,
            config=RunConfig(max_turns=10)
        )
        
        # Extract final message
        final_message = result.final_output or ""
        
        # Append assistant response to history
        if final_message:
            history.append({"role": "assistant", "content": final_message})
        
        return final_message


def run_zas_chat_turn(
    message: str,
    history: Optional[List[TResponseInputItem]] = None
) -> str:
    """
    Run a single chat turn with the ZAS agent.
    
    This is a convenience function for backwards compatibility.
    
    Args:
        message: User message
        history: Conversation history
        
    Returns:
        Agent response
    """
    from .mcp_client import get_mcp_client
    
    mcp_client = get_mcp_client()
    agent = ZASAgent(mcp_client)
    return agent.run(message, history)
