"""Confluence integration MCP tools."""

import traceback
from typing import Any, Dict, Optional

from ..services import ConfluenceService


class ConfluenceTools:
    """MCP tools for Confluence integration."""
    
    def __init__(self, confluence: Optional[ConfluenceService]):
        """
        Initialize Confluence tools.
        
        Args:
            confluence: Confluence service instance (can be None if not configured)
        """
        self.confluence = confluence
    
    def search_pages(
        self,
        query: str,
        limit: int = 10,
        space_key: str = "",
    ) -> Dict[str, Any]:
        """
        [Confluence-Agent] Search for Confluence pages.
        
        Args:
            query: Search query text
            limit: Maximum results
            space_key: Optional space key to limit search
            
        Returns:
            Dict with pages list or error
        """
        try:
            if not self.confluence:
                return {
                    "ok": False,
                    "error": "Confluence is not configured. Set CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN."
                }
            
            if not query.strip():
                return {"ok": False, "error": "Query cannot be empty"}
            
            pages = self.confluence.search_pages(
                query=query,
                limit=limit,
                space_key=space_key or None,
            )
            
            simplified = []
            for page in pages:
                content = page.get("content", {}) or {}
                title = content.get("title", "")
                space = (content.get("space") or {}).get("name", "")
                
                simplified.append({
                    "id": content.get("id"),
                    "title": title,
                    "space": space,
                    "url": content.get("_links", {}).get("webui", ""),
                })
            
            return {"ok": True, "count": len(simplified), "pages": simplified}
        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}
    
    def get_page(
        self,
        page_id: str,
        include_body: bool = True,
    ) -> Dict[str, Any]:
        """
        [Confluence-Agent] Get a specific Confluence page.
        
        Args:
            page_id: The page ID
            include_body: Whether to include page body content
            
        Returns:
            Page data or error
        """
        try:
            if not self.confluence:
                return {
                    "ok": False,
                    "error": "Confluence is not configured."
                }
            
            if not page_id:
                return {"ok": False, "error": "page_id cannot be empty"}
            
            page = self.confluence.get_page(page_id, include_body)
            
            result = {
                "ok": True,
                "id": page.get("id"),
                "title": page.get("title"),
                "space": (page.get("space") or {}).get("name"),
                "version": (page.get("version") or {}).get("number"),
                "url": page.get("_links", {}).get("webui"),
            }
            
            if include_body:
                body = page.get("body", {}).get("storage", {})
                result["body"] = body.get("value", "")[:5000]  # Truncate
            
            return result
        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}
