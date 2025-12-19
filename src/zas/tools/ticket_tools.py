"""Ticket-related MCP tools."""

import traceback
from typing import Any, Dict

from ..services import ZendeskService


class TicketTools:
    """MCP tools for ticket operations."""
    
    def __init__(self, zendesk: ZendeskService):
        """
        Initialize ticket tools.
        
        Args:
            zendesk: Zendesk service instance
        """
        self.zendesk = zendesk
    
    def search(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """
        [General-Agent] Search Zendesk tickets with Zendesk search syntax.
        
        Args:
            query: Search query (e.g., 'type:ticket status<solved created>2025-01-01')
            limit: Maximum number of results
            
        Returns:
            Dict with count and tickets list
        """
        try:
            raw = self.zendesk.search_tickets(query=query, limit=limit)
            items = []
            
            for hit in raw:
                items.append({
                    "id": hit.get("id"),
                    "subject": hit.get("subject"),
                    "status": hit.get("status"),
                    "priority": hit.get("priority"),
                    "assignee_id": hit.get("assignee_id"),
                    "requester_id": hit.get("requester_id"),
                    "organization_id": hit.get("organization_id"),
                    "tags": hit.get("tags", []),
                    "created_at": hit.get("created_at"),
                    "updated_at": hit.get("updated_at"),
                })
            
            return {"count": len(items), "tickets": items}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def get(self, ticket_id: int) -> Dict[str, Any]:
        """
        [Ticket-Agent] Get full ticket details.
        
        Args:
            ticket_id: The ticket ID
            
        Returns:
            Ticket data or error dict
        """
        try:
            ticket = self.zendesk.get_ticket(ticket_id)
            return {"ok": True, "ticket": ticket}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def get_comments(
        self,
        ticket_id: int,
        include_public: bool = True
    ) -> Dict[str, Any]:
        """
        [Ticket-Agent] Get all comments for a ticket.
        
        Args:
            ticket_id: The ticket ID
            include_public: Filter to only public comments
            
        Returns:
            Dict with comments list or error
        """
        try:
            comments = self.zendesk.get_ticket_comments(
                ticket_id=ticket_id,
                public_only=include_public
            )
            return {"ok": True, "count": len(comments), "comments": comments}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def add_internal_note(self, ticket_id: int, body: str) -> Dict[str, Any]:
        """
        [Ticket-Agent] Add an internal note (private comment) to a ticket.
        
        Args:
            ticket_id: The ticket ID
            body: Note text
            
        Returns:
            Success status or error
        """
        try:
            text = (body or "").strip()
            if not text:
                return {
                    "ok": False,
                    "error": "De body van de interne opmerking mag niet leeg zijn."
                }
            
            ticket = self.zendesk.add_internal_note(ticket_id, text)
            return {"ok": True, "ticket": ticket}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
    
    def update_ticket(
        self,
        ticket_id: int,
        status: str = None,
        priority: str = None,
        assignee_id: int = None,
        tags: list = None,
    ) -> Dict[str, Any]:
        """
        [Ticket-Agent] Update ticket fields.
        
        Args:
            ticket_id: The ticket ID
            status: New status (open, pending, solved, closed)
            priority: New priority (low, normal, high, urgent)
            assignee_id: New assignee user ID
            tags: List of tags to set
            
        Returns:
            Updated ticket or error
        """
        try:
            update_data = {}
            if status:
                update_data["status"] = status
            if priority:
                update_data["priority"] = priority
            if assignee_id is not None:
                update_data["assignee_id"] = assignee_id
            if tags is not None:
                update_data["tags"] = tags
            
            if not update_data:
                return {"ok": False, "error": "No fields to update"}
            
            ticket = self.zendesk.update_ticket(ticket_id, update_data)
            return {"ok": True, "ticket": ticket}
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
