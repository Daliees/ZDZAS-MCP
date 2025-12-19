"""Jira integration MCP tools."""

import traceback
from typing import Any, Dict, Optional

from ..services import JiraService
from ..core.exceptions import ConfigurationException


class JiraTools:
    """MCP tools for Jira integration."""
    
    def __init__(self, jira: Optional[JiraService]):
        """
        Initialize Jira tools.
        
        Args:
            jira: Jira service instance (can be None if not configured)
        """
        self.jira = jira
    
    def get_issue(self, issue_key: str, max_comments: int = 5) -> Dict[str, Any]:
        """
        [Jira-Agent] Get details of a Jira issue including recent comments.
        
        Args:
            issue_key: Issue key (e.g., 'TGR-123')
            max_comments: Maximum number of comments to include
            
        Returns:
            Issue data or error
        """
        try:
            if not self.jira:
                return {
                    "ok": False,
                    "error": "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
                }
            
            if not issue_key:
                return {"ok": False, "error": "issue_key cannot be empty."}
            
            issue_data = self.jira.get_issue(issue_key, max_comments)
            return {"ok": True, **issue_data}
        
        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}
