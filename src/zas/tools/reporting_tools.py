"""Reporting and export MCP tools."""

import csv
import os
import traceback
from typing import Any, Dict

from ..services import ZendeskService


class ReportingTools:
    """MCP tools for reporting and data export."""
    
    def __init__(self, zendesk: ZendeskService):
        """
        Initialize reporting tools.
        
        Args:
            zendesk: Zendesk service instance
        """
        self.zendesk = zendesk
    
    def export_tickets_csv(
        self,
        query: str,
        path: str = "tickets_export.csv",
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        [KB-Agent] Export tickets to CSV file.
        
        Args:
            query: Search query for tickets
            path: Output file path
            limit: Maximum tickets to export
            
        Returns:
            Dict with export status and path
        """
        try:
            rows = self.zendesk.search_tickets(query=query, limit=limit)
            
            fields = [
                "id", "subject", "status", "priority",
                "assignee_id", "requester_id", "organization_id",
                "tags", "created_at", "updated_at"
            ]
            
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for ticket in rows:
                    writer.writerow({k: ticket.get(k) for k in fields})
            
            return {
                "ok": True,
                "path": os.path.abspath(path),
                "count": len(rows)
            }
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}
