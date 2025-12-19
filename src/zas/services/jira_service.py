"""Jira API service."""

from typing import Any, Dict, List, Optional

from ..core import BaseAPIClient, Config
from ..core.exceptions import ConfigurationException


class JiraService(BaseAPIClient):
    """Service for interacting with the Jira API."""
    
    def __init__(self, config: Config):
        """
        Initialize the Jira service.
        
        Args:
            config: Application configuration
            
        Raises:
            ConfigurationException: If Jira is not configured
        """
        if not config.jira:
            raise ConfigurationException("Jira configuration is not available")
        
        super().__init__(
            base_url=config.jira.base_url.rstrip("/"),
            auth=config.jira.auth,
            timeout=config.api_timeout,
            rate_limit_delay=config.rate_limit_delay,
        )
        self.config = config
    
    def get_issue(
        self,
        issue_key: str,
        max_comments: int = 5
    ) -> Dict[str, Any]:
        """
        Get Jira issue details.
        
        Args:
            issue_key: Issue key (e.g., 'TGR-123')
            max_comments: Maximum number of comments to include
            
        Returns:
            Issue data with simplified comments
        """
        data = self.get(f"/rest/api/3/issue/{issue_key}")
        fields = data.get("fields", {}) or {}
        
        # Extract basic info
        status = (fields.get("status") or {}).get("name")
        assignee = fields.get("assignee") or {}
        assignee_name = assignee.get("displayName")
        summary = fields.get("summary")
        
        # Process comments
        comments_block = fields.get("comment") or {}
        comments = comments_block.get("comments") or []
        
        # Sort by created date and get latest
        comments_sorted = sorted(
            comments,
            key=lambda c: c.get("created", ""),
        )
        latest = comments_sorted[-max_comments:] if comments_sorted else []
        
        # Simplify comment data
        simplified_comments = []
        for comment in latest:
            author = (comment.get("author") or {}).get("displayName")
            body = comment.get("body")
            
            # Handle Atlassian Document Format (ADF)
            body_text = self._extract_text_from_adf(body)
            
            simplified_comments.append({
                "author": author,
                "created": comment.get("created"),
                "updated": comment.get("updated"),
                "body": body_text[:2000],  # Truncate for agent context
            })
        
        return {
            "key": data.get("key"),
            "summary": summary,
            "status": status,
            "assignee": assignee_name,
            "updated": fields.get("updated"),
            "latest_comments": simplified_comments,
            "raw": {
                "id": data.get("id"),
                "self": data.get("self"),
            },
        }
    
    def _extract_text_from_adf(self, body: Any) -> str:
        """
        Extract plain text from Atlassian Document Format.
        
        Args:
            body: ADF body object or plain string
            
        Returns:
            Plain text content
        """
        if isinstance(body, str):
            return body
        
        if not isinstance(body, dict):
            return str(body) if body is not None else ""
        
        # Extract text from ADF structure
        if "content" in body:
            text_parts = []
            for block in body.get("content", []):
                for content in block.get("content", []):
                    if text := content.get("text"):
                        text_parts.append(text)
            return "\n".join(text_parts)
        
        return str(body)
