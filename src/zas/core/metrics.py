"""Metrics tracking for ZAS services."""

import time
from typing import Dict
from threading import Lock
from datetime import datetime, timedelta


class MetricsTracker:
    """Track metrics for ZAS services."""
    
    def __init__(self):
        """Initialize metrics tracker."""
        self.mcp_requests = 0
        self.chat_requests = 0
        self.proxy_requests = 0
        self.start_time = time.time()
        self._lock = Lock()
        
        # Service status
        self.mcp_status = "❓ Unknown"
        self.chat_status = "❓ Unknown"
        self.proxy_status = "❓ Unknown"
    
    def increment_mcp_requests(self):
        """Increment MCP request counter."""
        with self._lock:
            self.mcp_requests += 1
    
    def increment_chat_requests(self):
        """Increment Chat API request counter."""
        with self._lock:
            self.chat_requests += 1
    
    def increment_proxy_requests(self):
        """Increment MCP Proxy request counter."""
        with self._lock:
            self.proxy_requests += 1
    
    def set_mcp_status(self, status: str):
        """Set MCP server status."""
        with self._lock:
            self.mcp_status = status
    
    def set_chat_status(self, status: str):
        """Set Chat API status."""
        with self._lock:
            self.chat_status = status
    
    def set_proxy_status(self, status: str):
        """Set MCP Proxy status."""
        with self._lock:
            self.proxy_status = status
    
    @property
    def total_requests(self) -> int:
        """Get total request count."""
        with self._lock:
            return self.mcp_requests + self.chat_requests + self.proxy_requests
    
    @property
    def uptime(self) -> str:
        """Get uptime as formatted string."""
        elapsed = time.time() - self.start_time
        delta = timedelta(seconds=int(elapsed))
        
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get all metrics as a dictionary.
        
        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            return {
                "mcp_requests": self.mcp_requests,
                "chat_requests": self.chat_requests,
                "proxy_requests": self.proxy_requests,
                "total_requests": self.total_requests,
                "uptime": self.uptime,
                "mcp_status": self.mcp_status,
                "chat_status": self.chat_status,
                "proxy_status": self.proxy_status,
                "start_time": datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            }
    
    def reset(self):
        """Reset all counters."""
        with self._lock:
            self.mcp_requests = 0
            self.chat_requests = 0
            self.proxy_requests = 0
            self.start_time = time.time()


# Global metrics instance
_metrics: MetricsTracker = MetricsTracker()


def get_metrics() -> MetricsTracker:
    """Get the global metrics tracker instance."""
    return _metrics
