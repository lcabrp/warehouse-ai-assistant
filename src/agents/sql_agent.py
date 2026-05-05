"""
SQL Query Agent - LangGraph Implementation
==========================================

This agent connects to the Warehouse MCP server and can answer questions
about warehouse operations by querying the database.

Architecture (Unit 7 ReAct Pattern):
    User Question
        ↓
    [Agent Node] ← ─ ─ ─ ─ ─ ─ ─ ┐
        ↓                         │
    Reasoning: What tool to call? │
        ↓                         │
    [Tool Call Node]              │
        ↓                         │
    Execute MCP tool              │
        ↓                         │
    Observation: Got results      │
        └─────────────────────────┘
        ↓
    [Agent Node]
        ↓
    Final Answer

Key Features from Unit 7:
1. **Message Truncation**: Keep last N messages to avoid token limits
2. **ReAct Loop**: Reason → Act → Observe → Repeat
3. **Async Operations**: Use async/await for MCP calls
4. **State Management**: TypedDict for type-safe state
"""

import asyncio
from typing import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, trim_messages
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.message import add_messages

from ..config import settings
from ..tools.warehouse_mcp import (
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseQueryTimeoutError,
)


# ==============================================================================
# State Definition (Unit 7 Pattern)
# ==============================================================================

class AgentState(TypedDict):
    """
    State for the SQL agent graph.
    
    Why TypedDict?
    - Type checking at development time
    - Clear contract for what data flows through the graph
    - LangGraph automatically handles state updates
    
    The Annotated[list, add_messages] pattern:
    - 'add_messages' is a reducer that appends new messages
    - Prevents duplicate messages in history
    - Essential for conversation memory
    """
    messages: Annotated[list, add_messages]


# ==============================================================================
# SQL Agent Class
# ==============================================================================

class SQLAgent:
    """
    LangGraph-based agent for querying warehouse data.
    
    This agent:
    1. Connects to the Warehouse MCP server (FastMCP)
    2. Uses gpt-4o-mini to reason about questions
    3. Calls appropriate database query tools
    4. Synthesizes answers from query results
    """
    
    def __init__(self):
        """Initialize the SQL agent with MCP client and LLM."""
        self.llm = None
        self.agent_executor = None
        self.mcp_client = None
        
    async def initialize(self):
        """
        Async initialization to connect to MCP server.
        
        Why async?
        - MCP client connection is async
        - Tool loading happens asynchronously
        - Follows Unit 6 MCP patterns
        """
        print("🔧 Initializing SQL Agent...")
        
        # 1. Set up MCP client to connect to our Warehouse MCP server
        workspace_root = settings.project_root
        python_exe = workspace_root / ".venv" / "Scripts" / "python.exe"
        
        # MultiServerMCPClient can connect to multiple MCP servers
        # For now, we just have one: the warehouse database server
        # Following Unit 6 pattern: run the MCP server script directly via stdio
        self.mcp_client = MultiServerMCPClient(
            {
                "warehouse": {
                    "transport": "stdio",  # Standard input/output communication
                    "command": str(python_exe),
                    "args": ["run_mcp_server.py"],  # Run the launcher script
                    "cwd": str(workspace_root),
                }
            }
        )
        
        # 2. Load tools from MCP server
        # These become callable functions the LLM can use
        tools = await self.mcp_client.get_tools()
        print(f"✅ Loaded {len(tools)} tools: {[t.name for t in tools]}")
        
        # 3. Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,  # Deterministic for data queries
        )
        print(f"✅ Using model: {settings.LLM_MODEL}")
        
        # 4. Create the agent using LangChain's create_agent helper
        # This creates a ReAct-style agent that can use our tools
        # The agent automatically gets a system prompt that guides tool usage
        self.agent_executor = create_agent(self.llm, tools=tools)
        
        print("✅ SQL Agent initialized and ready!\n")
    
    async def query(self, question: str) -> str:
        """
        Main entry point: Ask the agent a question with granular error handling.
        
        This method provides specific error messages to users based on the underlying
        database error, helping them understand what went wrong and how to respond.
        
        Args:
            question: Natural language question about warehouse operations
        
        Returns:
            Agent's answer as a string, or a specific error message if something fails
        
        Example:
            answer = await agent.query("What orders are delayed?")
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            # Invoke the agent with the user's question
            # Following Unit 6 pattern: pass messages dict
            result = await self.agent_executor.ainvoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            
            # Extract the final answer (last message)
            final_message = result["messages"][-1]
            return final_message.content
        
        except DatabaseConnectionError as e:
            # Database is offline, corrupted, or inaccessible
            import sys
            print(f"❌ SQL Agent - Connection Error: {e}", file=sys.stderr)
            return (
                "I'm unable to connect to the warehouse database right now. "
                "The database server may be offline or there may be a file access issue. "
                "Please try again in a few moments."
            )
        
        except DatabaseQueryTimeoutError as e:
            # Query is taking too long - likely a performance issue
            import sys
            print(f"❌ SQL Agent - Timeout Error: {e}", file=sys.stderr)
            return (
                "The database query took too long to complete. "
                "This might mean the database is busy or your question requires a complex search. "
                "Please try a simpler or more specific question."
            )
        
        except DatabaseQueryError as e:
            # Query failed - likely syntax or schema issue
            import sys
            print(f"❌ SQL Agent - Query Error: {e}", file=sys.stderr)
            if e.sql_error:
                print(f"    Original error: {e.sql_error}", file=sys.stderr)
            return (
                "The database query failed due to a problem with how your question "
                "was converted to a database search. "
                "Please try rephrasing your question in a different way."
            )
        
        except Exception as e:
            # Unexpected error - generic fallback
            import sys
            print(f"❌ SQL Agent - Unexpected Error: {type(e).__name__}: {e}", file=sys.stderr)
            return (
                "An unexpected error occurred while querying the database. "
                "Please try rephrasing your question or try again later."
            )
    
    async def chat(self, messages: list) -> str:
        """
        Multi-turn conversation interface with granular error handling.
        
        Args:
            messages: List of messages (can be from previous conversation)
        
        Returns:
            Agent's response or specific error message if query fails
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        try:
            result = await self.agent_executor.ainvoke({"messages": messages})
            final_message = result["messages"][-1]
            return final_message.content
        
        except DatabaseConnectionError as e:
            import sys
            print(f"❌ SQL Agent - Connection Error: {e}", file=sys.stderr)
            return (
                "I'm unable to connect to the warehouse database right now. "
                "The database server may be offline or there may be a file access issue. "
                "Please try again in a few moments."
            )
        
        except DatabaseQueryTimeoutError as e:
            import sys
            print(f"❌ SQL Agent - Timeout Error: {e}", file=sys.stderr)
            return (
                "The database query took too long to complete. "
                "This might mean the database is busy or your question requires a complex search. "
                "Please try a simpler or more specific question."
            )
        
        except DatabaseQueryError as e:
            import sys
            print(f"❌ SQL Agent - Query Error: {e}", file=sys.stderr)
            if e.sql_error:
                print(f"    Original error: {e.sql_error}", file=sys.stderr)
            return (
                "The database query failed due to a problem with how your question "
                "was converted to a database search. "
                "Please try rephrasing your question in a different way."
            )
        
        except Exception as e:
            import sys
            print(f"❌ SQL Agent - Unexpected Error: {type(e).__name__}: {e}", file=sys.stderr)
            return (
                "An unexpected error occurred while querying the database. "
                "Please try rephrasing your question or try again later."
            )
    
    async def cleanup(self):
        """Clean up MCP client connection."""
        if self.mcp_client:
            # MCP client cleanup (if needed)
            pass


# ==============================================================================
# Helper Functions
# ==============================================================================

async def create_sql_agent() -> SQLAgent:
    """
    Factory function to create and initialize a SQL agent.
    
    Usage:
        agent = await create_sql_agent()
        answer = await agent.query("Show me delayed orders")
        await agent.cleanup()
    """
    agent = SQLAgent()
    await agent.initialize()
    return agent


# ==============================================================================
# CLI Test Interface
# ==============================================================================

async def main():
    """Simple CLI for testing the SQL agent."""
    print("=" * 60)
    print("Warehouse SQL Agent - Interactive Test")
    print("=" * 60)
    
    # Create agent
    agent = await create_sql_agent()
    
    # Test questions
    test_questions = [
        "What orders are delayed?",
        "Show me critical inventory items",
        "How many open exceptions are there?",
    ]
    
    for question in test_questions:
        print(f"\n🔍 Question: {question}")
        print("-" * 60)
        
        try:
            answer = await agent.query(question)
            print(f"💡 Answer:\n{answer}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    # Cleanup
    await agent.cleanup()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
