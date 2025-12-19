#!/usr/bin/env python3
"""
Verification script for the new OOP architecture.

This script validates that all new modules can be imported
and that basic functionality works.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    try:
        # Core
        from src.zas.core import Config, get_config, ZASException, APIException
        from src.zas.core import BaseAPIClient
        print("✓ Core modules imported successfully")
        
        # Services
        from src.zas.services import ZendeskService, JiraService, ConfluenceService
        print("✓ Service modules imported successfully")
        
        # Tools
        from src.zas.tools import (
            TicketTools, KnowledgeBaseTools, ReportingTools,
            JiraTools, ConfluenceTools, GeneralTools
        )
        from src.zas.tools.registry import MCPToolRegistry
        print("✓ Tool modules imported successfully")
        
        # Agents
        from src.zas.agents import MCPClient, ZASAgent
        print("✓ Agent modules imported successfully")
        
        # API
        from src.zas.api import ChatAPI, MCPProxy
        print("✓ API modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.zas.core import Config
        
        # Test that config validation works
        try:
            config = Config.from_env()
            print(f"✓ Configuration loaded successfully")
            print(f"  - Zendesk subdomain: {config.zendesk.subdomain}")
            print(f"  - Jira configured: {config.jira is not None}")
            print(f"  - Confluence configured: {config.confluence is not None}")
            return True
        except Exception as e:
            print(f"✗ Configuration loading failed: {e}")
            print("  (This is expected if .env is not configured)")
            return False
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_service_creation():
    """Test service instantiation."""
    print("\nTesting service creation...")
    
    try:
        from src.zas.core import Config
        from src.zas.services import ZendeskService
        
        try:
            config = Config.from_env()
            zendesk = ZendeskService(config)
            print(f"✓ ZendeskService created successfully")
            print(f"  - Base URL: {zendesk.base_url}")
            return True
        except Exception as e:
            print(f"✗ Service creation failed: {e}")
            print("  (This is expected if .env is not configured)")
            return False
    except Exception as e:
        print(f"✗ Service test failed: {e}")
        return False


def test_tool_creation():
    """Test tool instantiation."""
    print("\nTesting tool creation...")
    
    try:
        from src.zas.core import Config
        from src.zas.services import ZendeskService
        from src.zas.tools import TicketTools, GeneralTools
        
        try:
            config = Config.from_env()
            zendesk = ZendeskService(config)
            ticket_tools = TicketTools(zendesk)
            general_tools = GeneralTools()
            
            print(f"✓ Tools created successfully")
            
            # Test ping
            result = general_tools.ping()
            if result == "pong":
                print(f"✓ GeneralTools.ping() works: {result}")
            else:
                print(f"✗ GeneralTools.ping() returned unexpected: {result}")
            
            return True
        except Exception as e:
            print(f"✗ Tool creation failed: {e}")
            print("  (This is expected if .env is not configured)")
            return False
    except Exception as e:
        print(f"✗ Tool test failed: {e}")
        return False


def test_mcp_server_creation():
    """Test MCP server creation."""
    print("\nTesting MCP server creation...")
    
    try:
        from app_new import create_mcp_server
        from src.zas.core import Config
        
        try:
            config = Config.from_env()
            mcp = create_mcp_server(config)
            print(f"✓ MCP server created successfully")
            print(f"  - Server name: {mcp.name}")
            return True
        except Exception as e:
            print(f"✗ MCP server creation failed: {e}")
            print("  (This is expected if .env is not configured)")
            return False
    except Exception as e:
        print(f"✗ MCP server test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("ZAS OOP Architecture Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Services", test_service_creation()))
    results.append(("Tools", test_tool_creation()))
    results.append(("MCP Server", test_mcp_server_creation()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed (may be due to missing .env configuration)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
