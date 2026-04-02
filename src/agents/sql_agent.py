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
        Main entry point: Ask the agent a question.
        
        Args:
            question: Natural language question about warehouse operations
        
        Returns:
            Agent's answer as a string
        
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
            
        except Exception as e:
            # Log error but provide graceful user-facing message
            import sys
            print(f"❌ SQL Agent Error: {e}", file=sys.stderr)
            return (
                f"I encountered an error querying the database. "
                f"Please try rephrasing your question or try again later. "
                f"Error: {str(e)[:100]}"
            )
    
    async def chat(self, messages: list) -> str:
        """
        Multi-turn conversation interface.
        
        Args:
            messages: List of messages (can be from previous conversation)
        
        Returns:
            Agent's response
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        result = await self.agent_executor.ainvoke({"messages": messages})
        final_message = result["messages"][-1]
        return final_message.content
    
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
