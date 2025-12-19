"""Confluence API service."""

from typing import Any, Dict, List, Optional

from ..core import BaseAPIClient, Config
from ..core.exceptions import ConfigurationException


class ConfluenceService(BaseAPIClient):
    """Service for interacting with the Confluence API."""
    
    def __init__(self, config: Config):
        """
        Initialize the Confluence service.
        
        Args:
            config: Application configuration
            
        Raises:
            ConfigurationException: If Confluence is not configured
        """
        if not config.confluence:
            raise ConfigurationException("Confluence configuration is not available")
        
        super().__init__(
            base_url=config.confluence.base_url.rstrip("/"),
            auth=config.confluence.auth,
            timeout=config.api_timeout,
            rate_limit_delay=config.rate_limit_delay,
        )
        self.config = config
    
    def search_pages(
        self,
        query: str,
        limit: int = 10,
        space_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for Confluence pages.
        
        Args:
            query: Search query (CQL)
            limit: Maximum results
            space_key: Optional space to limit search to
            
        Returns:
            List of pages
        """
        cql = f"type=page AND text~'{query}'"
        if space_key:
            cql += f" AND space={space_key}"
        
        params = {
            "cql": cql,
            "limit": limit,
            "expand": "content.title,content.space",
        }
        
        data = self.get("/rest/api/content/search", params=params)
        return data.get("results", [])
    
    def get_page(
        self,
        page_id: str,
        include_body: bool = True,
    ) -> Dict[str, Any]:
        """
        Get a specific Confluence page.
        
        Args:
            page_id: Page ID
            include_body: Whether to include page body content
            
        Returns:
            Page data
        """
        expand = "space,version,history"
        if include_body:
            expand += ",body.storage"
        
        params = {"expand": expand}
        return self.get(f"/rest/api/content/{page_id}", params=params)
