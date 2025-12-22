"""ZAS Agent - main conversational agent."""

from typing import List, Dict, Any, Optional
import json

from .mcp_client import MCPClient


class ZASAgent:
    """
    ZAS conversational agent with MCP tool integration.
    
    This agent handles user queries about Zendesk tickets, knowledge base,
    Jira issues, and Confluence pages.
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
    ):
        """
        Initialize ZAS agent.
        
        Args:
            mcp_client: MCP client for tool access
            model: Claude model to use
            api_key: Anthropic API key (optional, for future use)
        """
        self.mcp_client = mcp_client
        self.model = model
        self.api_key = api_key
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query.
        
        Args:
            query: User's query text
            context: Optional context dict with conversation history, etc.
            
        Returns:
            Response dict with 'response' text and optional 'tools_used'
        """
        # Simple implementation - in production you'd call Claude API here
        # For now, return a basic response
        return {
            "response": f"Received query: {query}",
            "tools_used": [],
            "context": context or {}
        }
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Call an MCP tool directly.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            
        Returns:
            Tool result
        """
        return await self.mcp_client.call_tool(tool_name, parameters)
    
    async def run(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Run the agent with a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Response dict with 'response' text
        """
        # Extract the last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            last_message = user_messages[-1].get("content", "")
            return await self.process_query(last_message, {"messages": messages})
        
        return {
            "response": "No user message found",
            "tools_used": [],
            "context": {}
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        mcp_client = MCPClient("http://127.0.0.1:6000/mcp")
        agent = ZASAgent(mcp_client)
        
        result = await agent.process_query("Show me recent tickets")
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
