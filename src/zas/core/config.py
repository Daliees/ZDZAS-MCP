"""Configuration management for ZAS."""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from .exceptions import ConfigurationException


@dataclass
class ZendeskConfig:
    """Zendesk API configuration."""
    
    subdomain: str
    email: str
    api_token: str
    
    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        return f"https://{self.subdomain}.zendesk.com/api/v2"
    
    @property
    def auth(self) -> tuple[str, str]:
        """Get authentication tuple."""
        return (f"{self.email}/token", self.api_token)


@dataclass
class JiraConfig:
    """Jira API configuration."""
    
    base_url: str
    email: str
    api_token: str
    
    @property
    def auth(self) -> tuple[str, str]:
        """Get authentication tuple."""
        return (self.email, self.api_token)


@dataclass
class ConfluenceConfig:
    """Confluence API configuration."""
    
    base_url: str
    email: str
    api_token: str
    
    @property
    def auth(self) -> tuple[str, str]:
        """Get authentication tuple."""
        return (self.email, self.api_token)


@dataclass
class Config:
    """Central configuration for the ZAS application."""
    
    zendesk: ZendeskConfig
    jira: Optional[JiraConfig] = None
    confluence: Optional[ConfluenceConfig] = None
    
    # MCP Server settings
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000
    mcp_path: str = "/mcp"
    
    # Chat API settings
    chat_api_host: str = "0.0.0.0"
    chat_api_port: int = 3000
    
    # MCP Proxy settings
    mcp_proxy_host: str = "0.0.0.0"
    mcp_proxy_port: int = 8080
    
    # API settings
    api_timeout: int = 20
    rate_limit_delay: float = 0.15
    
    # Logging
    feedback_log_path: str = "zas_feedback_log.jsonl"
    
    # Telegram notifications
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: bool = False
    
    # Dashboard settings
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 5000
    
    # AI Orchestration
    orchestration_enabled: bool = False
    num_evaluator_agents: int = 3
    
    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.
        
        Args:
            env_path: Optional path to .env file
            
        Returns:
            Config instance
            
        Raises:
            ConfigurationException: If required variables are missing
        """
        if env_path:
            load_dotenv(env_path)
        else:
            # Try to load from current directory
            base_dir = Path(__file__).parent.parent.parent.parent
            env_file = base_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file)
        
        # Validate required Zendesk config
        missing = []
        for key in ("ZENDESK_SUBDOMAIN", "ZENDESK_EMAIL", "ZENDESK_API_TOKEN"):
            if not os.getenv(key):
                missing.append(key)
        
        if missing:
            raise ConfigurationException(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        zendesk = ZendeskConfig(
            subdomain=os.getenv("ZENDESK_SUBDOMAIN"),
            email=os.getenv("ZENDESK_EMAIL"),
            api_token=os.getenv("ZENDESK_API_TOKEN"),
        )
        
        # Optional Jira config
        jira = None
        if all(os.getenv(k) for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")):
            jira = JiraConfig(
                base_url=os.getenv("JIRA_BASE_URL"),
                email=os.getenv("JIRA_EMAIL"),
                api_token=os.getenv("JIRA_API_TOKEN"),
            )
        
        # Optional Confluence config
        confluence = None
        if all(os.getenv(k) for k in ("CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN")):
            confluence = ConfluenceConfig(
                base_url=os.getenv("CONFLUENCE_BASE_URL"),
                email=os.getenv("CONFLUENCE_EMAIL"),
                api_token=os.getenv("CONFLUENCE_API_TOKEN"),
            )
        
        return cls(
            zendesk=zendesk,
            jira=jira,
            confluence=confluence,
            mcp_host=os.getenv("MCP_HOST", "127.0.0.1"),
            mcp_port=int(os.getenv("MCP_PORT", "8000")),
            chat_api_host=os.getenv("CHAT_API_HOST", "0.0.0.0"),
            chat_api_port=int(os.getenv("CHAT_API_PORT", "3000")),
            mcp_proxy_host=os.getenv("MCP_PROXY_HOST", "0.0.0.0"),
            mcp_proxy_port=int(os.getenv("MCP_PROXY_PORT", "8080")),
            feedback_log_path=os.getenv("ZAS_FEEDBACK_LOG", "zas_feedback_log.jsonl"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            telegram_enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            dashboard_host=os.getenv("DASHBOARD_HOST", "0.0.0.0"),
            dashboard_port=int(os.getenv("DASHBOARD_PORT", "5000")),
            orchestration_enabled=os.getenv("ORCHESTRATION_ENABLED", "false").lower() == "true",
            num_evaluator_agents=int(os.getenv("NUM_EVALUATOR_AGENTS", "3")),
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
