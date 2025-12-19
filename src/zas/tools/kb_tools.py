"""Knowledge base (Help Center) MCP tools."""

import traceback
from typing import Any, Dict

from ..services import ZendeskService


class KnowledgeBaseTools:
    """MCP tools for knowledge base operations."""
    
    def __init__(self, zendesk: ZendeskService):
        """
        Initialize KB tools.
        
        Args:
            zendesk: Zendesk service instance
        """
        self.zendesk = zendesk
    
    def generate_draft(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        [KB-Agent] Generate draft article from solved tickets.
        
        Bundles data from solved tickets; the LLM agent creates the final text.
        
        Args:
            query: Search query for tickets
            limit: Max tickets to analyze
            
        Returns:
            Draft context data or error
        """
        try:
            tickets = self.zendesk.search_tickets(query + " status:solved", limit=limit)
            bundle = []
            
            for ticket in tickets:
                ticket_id = ticket["id"]
                comments = []
                
                try:
                    comment_data = self.zendesk.get_ticket_comments(
                        ticket_id,
                        public_only=True
                    )
                    comments = [c["body"] for c in comment_data]
                except Exception:
                    pass
                
                bundle.append({
                    "id": ticket_id,
                    "subject": ticket.get("subject"),
                    "summary": (comments[0][:200] if comments else ""),
                    "comments": comments,
                })
            
            combined_text = "\n\n".join([
                f"### Ticket {b['id']}: {b['subject']}\n{b['summary']}"
                for b in bundle
            ])
            
            return {
                "ok": True,
                "tickets_used": len(bundle),
                "draft_context": combined_text[:10000],  # Limit for LLM context
                "hint": "Use this context in the agent to write a knowledge base article.",
            }
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def search_articles(
        self,
        query: str,
        limit: int = 20,
        label_names: str = "",
        locale: str = "",
    ) -> Dict[str, Any]:
        """
        [KB-Agent] Search Zendesk Help Center articles.
        
        Args:
            query: Search text (title/body/labels)
            limit: Max results (max 100)
            label_names: Optional comma-separated labels (e.g., "2fa,login")
            locale: Optional locale filter (e.g., "nl")
            
        Returns:
            Dict with articles list or error
        """
        try:
            q = (query or "").strip()
            if not q and not label_names:
                return {
                    "ok": False,
                    "error": "Provide at least a query or label_names."
                }
            
            raw_results = self.zendesk.search_articles(
                query=q,
                limit=limit,
                label_names=label_names or None,
                locale=locale or None,
            )
            
            articles = []
            for art in raw_results:
                articles.append({
                    "id": art.get("id"),
                    "title": art.get("title"),
                    "locale": art.get("locale"),
                    "label_names": art.get("label_names", []),
                    "draft": art.get("draft", False),
                    "url": art.get("html_url"),
                    "snippet": art.get("snippet", ""),
                })
            
            return {"ok": True, "count": len(articles), "articles": articles}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def create_draft_article(
        self,
        section_id: int,
        title: str,
        body: str,
        locale: str = "nl",
    ) -> Dict[str, Any]:
        """
        [KB-Agent] Create a new draft knowledge base article.
        
        Args:
            section_id: Help Center section ID
            title: Article title
            body: Article HTML body
            locale: Article locale (default: nl)
            
        Returns:
            Created article data or error
        """
        try:
            if not title.strip():
                return {"ok": False, "error": "Title cannot be empty"}
            if not body.strip():
                return {"ok": False, "error": "Body cannot be empty"}
            
            article = self.zendesk.create_article(
                section_id=section_id,
                title=title,
                body=body,
                locale=locale,
                draft=True,
            )
            
            return {
                "ok": True,
                "article": {
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "url": article.get("html_url"),
                    "draft": article.get("draft"),
                },
            }
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
