"""Zendesk API service."""

from typing import Any, Dict, List, Optional
import time

from ..core import BaseAPIClient, Config
from ..core.exceptions import APIException, ValidationException


class ZendeskService(BaseAPIClient):
    """Service for interacting with the Zendesk API."""
    
    def __init__(self, config: Config):
        """
        Initialize the Zendesk service.
        
        Args:
            config: Application configuration
        """
        super().__init__(
            base_url=config.zendesk.base_url,
            auth=config.zendesk.auth,
            timeout=config.api_timeout,
            rate_limit_delay=config.rate_limit_delay,
        )
        self.config = config
    
    # ========== Ticket Operations ==========
    
    def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get full ticket details.
        
        Args:
            ticket_id: The ticket ID
            
        Returns:
            Ticket data
        """
        data = self.get(f"/tickets/{ticket_id}.json")
        return data.get("ticket", {})
    
    def search_tickets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for tickets using Zendesk search syntax.
        
        Args:
            query: Search query (e.g., 'type:ticket status<solved')
            limit: Maximum number of results
            
        Returns:
            List of tickets
        """
        return self._paginate_search(query, limit)
    
    def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a ticket.
        
        Args:
            ticket_id: The ticket ID
            update_data: Fields to update
            
        Returns:
            Updated ticket data
        """
        payload = {"ticket": update_data}
        data = self.put(f"/tickets/{ticket_id}.json", json=payload)
        return data.get("ticket", {})
    
    def add_internal_note(self, ticket_id: int, body: str) -> Dict[str, Any]:
        """
        Add an internal note (private comment) to a ticket.
        
        Args:
            ticket_id: The ticket ID
            body: Comment text
            
        Returns:
            Updated ticket data
        """
        if not body.strip():
            raise ValidationException("Comment body cannot be empty")
        
        payload = {
            "ticket": {
                "comment": {
                    "body": body,
                    "public": False,
                }
            }
        }
        data = self.put(f"/tickets/{ticket_id}.json", json=payload)
        return data.get("ticket", {})
    
    def get_ticket_comments(
        self,
        ticket_id: int,
        public_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all comments for a ticket.
        
        Args:
            ticket_id: The ticket ID
            public_only: If True, return only public comments
            
        Returns:
            List of comments
        """
        data = self.get(f"/tickets/{ticket_id}/comments.json")
        comments = data.get("comments", [])
        
        if public_only:
            comments = [c for c in comments if c.get("public", False)]
        
        return comments
    
    # ========== User Operations ==========
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user details."""
        data = self.get(f"/users/{user_id}.json")
        return data.get("user", {})
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search for users."""
        data = self.get("/users/search.json", params={"query": query})
        return data.get("users", [])
    
    # ========== Organization Operations ==========
    
    def get_organization(self, org_id: int) -> Dict[str, Any]:
        """Get organization details."""
        data = self.get(f"/organizations/{org_id}.json")
        return data.get("organization", {})
    
    # ========== Knowledge Base Operations ==========
    
    def search_articles(
        self,
        query: str,
        limit: int = 20,
        label_names: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search help center articles.
        
        Args:
            query: Search query
            limit: Maximum results
            label_names: Comma-separated labels to filter by
            locale: Locale to filter by (e.g., 'nl')
            
        Returns:
            List of articles
        """
        params = {"per_page": min(100, max(1, limit))}
        
        if query:
            params["query"] = query
        if label_names:
            params["label_names"] = label_names
        
        data = self.get("/help_center/articles/search.json", params=params)
        results = data.get("results", [])
        
        # Client-side locale filtering
        if locale:
            results = [a for a in results if a.get("locale") == locale]
        
        return results[:limit]
    
    def get_article(self, article_id: int) -> Dict[str, Any]:
        """Get article details."""
        data = self.get(f"/help_center/articles/{article_id}.json")
        return data.get("article", {})
    
    def create_article(
        self,
        section_id: int,
        title: str,
        body: str,
        locale: str = "nl",
        draft: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new knowledge base article.
        
        Args:
            section_id: Section to create article in
            title: Article title
            body: Article HTML body
            locale: Article locale
            draft: Create as draft or publish immediately
            
        Returns:
            Created article data
        """
        payload = {
            "article": {
                "title": title,
                "body": body,
                "locale": locale,
                "draft": draft,
            }
        }
        data = self.post(
            f"/help_center/sections/{section_id}/articles.json",
            json=payload
        )
        return data.get("article", {})
    
    # ========== Helper Methods ==========
    
    def _paginate_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Paginate through search results.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of results
        """
        results = []
        page = 1
        per_page = min(100, max(1, limit))
        
        while len(results) < limit:
            data = self.get(
                "/search.json",
                params={"query": query, "page": page, "per_page": per_page}
            )
            
            batch = [
                x for x in data.get("results", [])
                if x.get("result_type") == "ticket"
            ]
            results.extend(batch)
            
            if not data.get("next_page") or len(batch) == 0:
                break
            
            page += 1
            time.sleep(self.rate_limit_delay)
        
        return results[:limit]
