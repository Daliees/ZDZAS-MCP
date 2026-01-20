"""Tests for configuration management"""

import os
import pytest
from src.zas.core.config import Config, config


class TestConfig:
	"""Test configuration management"""

	def test_config_loads_from_env(self, monkeypatch):
		"""Test that config loads from environment variables"""
		monkeypatch.setenv("OPENAI_API_KEY", "test_key_123")
		monkeypatch.setenv("ZENDESK_SUBDOMAIN", "test_subdomain")

		# Reload config
		test_config = Config()
		assert test_config.OPENAI_API_KEY == "test_key_123"
		assert test_config.ZENDESK_SUBDOMAIN == "test_subdomain"

	def test_config_defaults(self):
		"""Test configuration defaults"""
		assert Config.CHAT_API_PORT == 9000
		assert Config.MCP_SERVER_PORT == 8000
		assert Config.ENVIRONMENT == "development"

	def test_config_validation(self, monkeypatch):
		"""Test configuration validation"""
		# Clear required vars
		monkeypatch.delenv("OPENAI_API_KEY", raising=False)
		monkeypatch.delenv("ZENDESK_SUBDOMAIN", raising=False)

		test_config = Config()
		missing = test_config.validate()
		assert "OPENAI_API_KEY" in missing
		assert "ZENDESK_SUBDOMAIN" in missing
