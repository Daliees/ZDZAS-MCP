"""Configuration management for ZDZAS-MCP"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration management"""

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # MCP Server
    ZAS_MCP_SERVER_URL: str = os.getenv("ZAS_MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))

    # Zendesk
    ZENDESK_SUBDOMAIN: str = os.getenv("ZENDESK_SUBDOMAIN", "")
    ZENDESK_EMAIL: str = os.getenv("ZENDESK_EMAIL", "")
    ZENDESK_API_KEY: str = os.getenv("ZENDESK_API_KEY", "")

    # Jira
    JIRA_DOMAIN: str = os.getenv("JIRA_DOMAIN", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")

    # Confluence
    CONFLUENCE_DOMAIN: str = os.getenv("CONFLUENCE_DOMAIN", "")
    CONFLUENCE_EMAIL: str = os.getenv("CONFLUENCE_EMAIL", "")
    CONFLUENCE_API_TOKEN: str = os.getenv("CONFLUENCE_API_TOKEN", "")

    # Salesforce
    SALESFORCE_INSTANCE_URL: Optional[str] = os.getenv("SALESFORCE_INSTANCE_URL")
    SALESFORCE_USERNAME: Optional[str] = os.getenv("SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD: Optional[str] = os.getenv("SALESFORCE_PASSWORD")
    SALESFORCE_SECURITY_TOKEN: Optional[str] = os.getenv("SALESFORCE_SECURITY_TOKEN")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./zas.db")

    # Server
    CHAT_API_HOST: str = os.getenv("CHAT_API_HOST", "0.0.0.0")
    CHAT_API_PORT: int = int(os.getenv("CHAT_API_PORT", "9000"))
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "9001"))

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration and return list of missing variables"""
        missing = []
        required_vars = [
            "OPENAI_API_KEY",
            "ZENDESK_SUBDOMAIN",
            "ZENDESK_EMAIL",
            "ZENDESK_API_KEY",
        ]

        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        return missing


# Create singleton instance
config = Config()
