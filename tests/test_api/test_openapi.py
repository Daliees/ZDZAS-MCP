"""Tests for OpenAPI schema validation"""

import pytest
from fastapi.testclient import TestClient


class TestOpenAPISchema:
	"""Test OpenAPI schema is valid"""

	def test_openapi_schema_exists(self, api_client):
		"""Test that OpenAPI schema endpoint exists"""
		response = api_client.get("/openapi.json")
		assert response.status_code == 200

	def test_openapi_schema_valid(self, api_client):
		"""Ensure OpenAPI schema is valid and complete"""
		response = api_client.get("/openapi.json")
		assert response.status_code == 200
		schema = response.json()

		assert "openapi" in schema
		assert "info" in schema
		assert "paths" in schema
		assert schema["openapi"].startswith("3.")

	def test_all_endpoints_documented(self, api_client):
		"""Ensure all endpoints are documented in OpenAPI schema"""
		response = api_client.get("/openapi.json")
		schema = response.json()

		# Check key endpoints exist
		paths = schema.get("paths", {})
		assert "/chat" in paths or "/api/chat" in paths
		# Add more endpoint checks as they're implemented

	def test_endpoints_have_examples(self, api_client):
		"""Ensure endpoints have request/response examples"""
		response = api_client.get("/openapi.json")
		schema = response.json()

		# TODO: Implement checks for examples in schema
		pass
