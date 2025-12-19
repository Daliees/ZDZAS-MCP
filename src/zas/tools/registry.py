"""MCP tool registry and registration."""

from typing import Callable, Any
from fastmcp import FastMCP

from ..core import Config
from ..services import ZendeskService, JiraService, ConfluenceService
from ..tools import (
    TicketTools,
    KnowledgeBaseTools,
    ReportingTools,
    JiraTools,
    ConfluenceTools,
    GeneralTools,
)


class MCPToolRegistry:
    """Registry for MCP tools with dependency injection."""
    
    def __init__(self, config: Config, mcp: FastMCP):
        """
        Initialize the tool registry.
        
        Args:
            config: Application configuration
            mcp: FastMCP instance
        """
        self.config = config
        self.mcp = mcp
        
        # Initialize services
        self.zendesk = ZendeskService(config)
        
        self.jira = None
        if config.jira:
            try:
                self.jira = JiraService(config)
            except Exception:
                pass
        
        self.confluence = None
        if config.confluence:
            try:
                self.confluence = ConfluenceService(config)
            except Exception:
                pass
        
        # Initialize tool instances
        self.ticket_tools = TicketTools(self.zendesk)
        self.kb_tools = KnowledgeBaseTools(self.zendesk)
        self.reporting_tools = ReportingTools(self.zendesk)
        self.jira_tools = JiraTools(self.jira)
        self.confluence_tools = ConfluenceTools(self.confluence)
        self.general_tools = GeneralTools()
    
    def register_all(self) -> None:
        """Register all tools with the MCP server."""
        # General tools
        self._register_tool("ping", self.general_tools.ping)
        
        # Ticket tools
        self._register_tool("tickets_search", self.ticket_tools.search)
        self._register_tool("ticket_get", self.ticket_tools.get)
        self._register_tool("ticket_comments", self.ticket_tools.get_comments)
        self._register_tool("ticket_add_internal_note", self.ticket_tools.add_internal_note)
        self._register_tool("ticket_update", self.ticket_tools.update_ticket)
        
        # Knowledge base tools
        self._register_tool("kb_generate_draft", self.kb_tools.generate_draft)
        self._register_tool("kb_search_articles", self.kb_tools.search_articles)
        self._register_tool("kb_create_draft_article", self.kb_tools.create_draft_article)
        
        # Reporting tools
        self._register_tool("tickets_export_csv", self.reporting_tools.export_tickets_csv)
        
        # Jira tools
        self._register_tool("jira_get_issue", self.jira_tools.get_issue)
        
        # Confluence tools
        self._register_tool("confluence_search_pages", self.confluence_tools.search_pages)
        self._register_tool("confluence_get_page", self.confluence_tools.get_page)
    
    def _register_tool(self, name: str, func: Callable) -> None:
        """
        Register a single tool with the MCP server.
        
        Args:
            name: Tool name
            func: Tool function
        """
        self.mcp.tool(func)
