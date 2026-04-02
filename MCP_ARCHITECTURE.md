# Understanding MCP in This Project

> **📚 Technical Deep-Dive Documentation**  
> This is a comprehensive technical reference for developers who want to understand the Model Context Protocol (MCP) implementation in depth. For a quick architecture overview, see [README.md](README.md).  
> 
> **Topics Covered:**  
> - MCP protocol fundamentals  
> - Client-server architecture patterns  
> - Our 3-agent system (SQL, RAG, Weather)  
> - Design decisions & trade-offs  
> - Troubleshooting guide  
> - Best practices & patterns

---

## Overview

This document explains how we use the Model Context Protocol (MCP) in this warehouse AI assistant project, and how it differs from the Unit 6 course approach.

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard that allows AI applications to connect to external tools and data sources securely. Think of it as a "USB-C port for AI" - it provides a standardized way to connect AI systems to external tools.

**Key Concept:** MCP uses a **client-server architecture**:
- **MCP Server** = Provides tools (database queries, API calls, etc.)
- **MCP Client** = Uses those tools (AI application or agent)
- **Transport** = How they communicate (stdio, HTTP, SSE)

---

## Two MCP Approaches: Unit 6 vs This Project

### Approach 1: MCP for External AI Apps (Unit 6)

**Use Case:** Configure Claude Desktop or VS Code Copilot to use your custom tools

**Architecture:**
```
You (human) → [Claude Desktop/VS Code] → [Your MCP Server] → [Database/API]
                  (MCP Client)              (Python script)
```

**How it works:**
1. Create an MCP server script (`mcp_server.py`)
2. Create a **`mcp.json` configuration file**
3. Place `mcp.json` in:
   - **Claude Desktop:** `%APPDATA%\Claude\mcp.json` (Windows)
   - **VS Code Copilot:** Workspace settings or user settings
4. The external app launches your server as a subprocess

**Example `mcp.json`:**
```json
{
  "mcpServers": {
    "warehouse": {
      "type": "stdio",
      "command": "E:\\Projects\\warehouse-ai-assistant\\.venv\\Scripts\\python.exe",
      "args": ["run_mcp_server.py"],
      "cwd": "E:\\Projects\\warehouse-ai-assistant"
    }
  }
}
```

**Pros:**
- ✅ Use with existing AI UIs (Claude, Copilot)
- ✅ No coding required for the client side
- ✅ Great for human-in-the-loop scenarios

**Cons:**
- ❌ Requires manual configuration
- ❌ Tied to specific AI applications
- ❌ Less control over agent behavior

---

### Approach 2: MCP for Custom Autonomous Agents (This Project)

**Use Case:** Build a programmatic agent that uses MCP tools autonomously

**Architecture:**
```
You (human) → [Your Python Agent] → [Your MCP Server] → [Database/API]
               (SQLAgent class)       (warehouse_mcp.py)
                (MCP Client)
```

**How it works:**
1. Create an MCP server script (`src/tools/warehouse_mcp.py`)
2. Create a launcher script (`run_mcp_server.py`)
3. **No `mcp.json` file needed!**
4. Your Python agent launches the server programmatically

**Implementation:**

**MCP Server (`src/tools/warehouse_mcp.py`):**
```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Warehouse Operations MCP", lifespan=lifespan)

@mcp.tool()
def search_orders(order_number: str = None, status: str = None, ctx: Context = None):
    """Search for orders with flexible filtering."""
    db = ctx.request_context.lifespan_context["db"]
    # ... query logic ...
    return {"orders": results, "count": len(results)}

@mcp.tool()
def check_inventory(item_sku: str = None, ctx: Context = None):
    """Check current inventory levels."""
    db = ctx.request_context.lifespan_context["db"]
    # ... query logic ...
    return {"inventory_records": results}

# More tools...
```

**Launcher (`run_mcp_server.py`):**
```python
from src.tools.warehouse_mcp import mcp
import asyncio

if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
```

**Agent Client (`src/agents/sql_agent.py`):**
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# Your agent is the MCP client
self.mcp_client = MultiServerMCPClient({
    "warehouse": {
        "transport": "stdio",
        "command": str(python_exe),
        "args": ["run_mcp_server.py"],
        "cwd": str(workspace_root),
    }
})

# Load tools from MCP server
tools = await self.mcp_client.get_tools()
# Returns: ['search_orders', 'get_order_details', 'check_inventory', ...]

# Create agent with these tools
self.agent_executor = create_agent(self.llm, tools=tools)
```

**Pros:**
- ✅ Full programmatic control
- ✅ No external app configuration needed
- ✅ Self-contained Python application
- ✅ Can integrate into larger systems
- ✅ Better for autonomous agents

**Cons:**
- ❌ More code to write
- ❌ Can't easily use with Claude Desktop UI

---

## Our Three-Agent System

### 1. SQL Agent (Database Queries via MCP)

**6 MCP Tools Available:**

1. **`search_orders`** - Find orders by number, status, warehouse, date range
2. **`get_order_details`** - Get complete order info with line items
3. **`check_inventory`** - Query stock levels and availability
4. **`get_shipment_status`** - Track shipments and identify delays
5. **`get_exceptions`** - Find operational issues (scanner problems, damaged goods)
6. **`get_labor_metrics`** - Employee productivity and picking efficiency

### 2. RAG Agent (Document Search - No MCP)

**Uses InMemoryVectorStore directly:**
- Loads 5 markdown files from `docs/` folder
- 46 chunks embedded with `text-embedding-3-small`
- No MCP needed - direct vector similarity search
- Source: Warehouse operational procedures

### 3. Weather Agent (Web Search via Tavily - No MCP)

**Uses Tavily API directly:**
- Web search tool for weather, news, transportation disruptions
- Created via `@tool` decorator from LangChain
- HTTP API calls to Tavily (not MCP)
- Provides external context for shipment delays

**Note:** While we could have implemented Tavily through MCP (as shown in Unit 7 Lab with the Tavily MCP server), we chose direct integration for simplicity. The patterns are equivalent:

```python
# MCP approach (Unit 7 Lab):
research_client = MultiServerMCPClient({
    "tavily": {
        "transport": "http",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={key}",
    }
})
tools = await research_client.get_tools()

# Direct approach (our project):
from tavily import TavilyClient
tavily_client = TavilyClient(api_key=key)

@tool
def search_web(query: str) -> str:
    results = tavily_client.search(query, search_depth="advanced")
    return format_results(results)
```

Both approaches work; direct integration removes one layer of abstraction for a single-purpose tool.

---

## MCP Server Design Patterns

### 1. Lifespan Context Management
```python
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage database connection lifecycle."""
    db = WarehouseDB(str(settings.database_path))
    db.connect()
    try:
        yield {"db": db}  # Inject into tool context
    finally:
        db.close()
```

**Why:** Ensures database connection is:
- Opened when server starts
- Available to all tools via `ctx` parameter
- Properly closed on shutdown

### 2. Context Injection Pattern
```python
@mcp.tool()
def search_orders(..., ctx: Context = None) -> dict:
    """Search orders tool."""
    # Get database from context
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    # Use database
    results = db.execute_query(query, params)
    return {"orders": results}
```

**Why:** 
- Avoids global variables
- Each tool gets fresh database access
- Testable (can mock context)

### 3. Parameterized Queries
```python
query = "SELECT * FROM orders WHERE order_date >= ?"
params = [cutoff_date]

if order_number:
    query += " AND order_number LIKE ?"
    params.append(f"%{order_number}%")

results = db.execute_query(query, tuple(params))
```

**Why:** Prevents SQL injection attacks

### 4. Structured Outputs
```python
return {
    "orders": results,
    "count": len(results),
    "filters_applied": {
        "order_number": order_number,
        "status": status
    }
}
```

**Why:**
- JSON-serializable for LLM consumption
- Includes metadata for better responses
- Could upgrade to Pydantic models later

---

## STDIO Transport Explained

**STDIO = Standard Input/Output**

When you see `"transport": "stdio"`, it means:

```
MCP Client Process              MCP Server Process
     (Agent)                      (warehouse_mcp.py)
        │                                │
        ├──[stdin]──► JSON-RPC ──►───────┤
        │              Messages          │
        │                                │
        │            ┌──────────┐        │
        │            │ Database │        │
        │            │  Query   │        │
        │            └──────────┘        │
        │                                │
        ├──◄────────  Results  ─◄[stdout]┤
        │                                │
        └──◄───────── Logs ────◄[stderr]─┘
```

**Three streams:**
- **stdin** - Client sends tool call requests
- **stdout** - Server sends tool responses (IMPORTANT: must be clean JSON)
- **stderr** - Server logs (debugging, errors)

**Critical:** Server must NOT print to stdout during startup, only JSON-RPC messages!

This is why we use `print(..., file=sys.stderr)` for logging in `warehouse_mcp.py`.

---

## Communication Flow Example

**User asks:** "What orders are delayed?"

**Step 1:** Agent receives question
```python
result = await agent.query("What orders are delayed?")
```

**Step 2:** LLM decides to call `search_orders` tool
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_orders",
    "arguments": {
      "status": "Delayed",
      "days_back": 30
    }
  }
}
```

**Step 3:** MCP client sends this via stdin to server

**Step 4:** Server executes tool
```python
@mcp.tool()
def search_orders(status="Delayed", days_back=30, ctx=None):
    db = ctx.request_context.lifespan_context["db"]
    results = db.execute_query(
        "SELECT * FROM orders WHERE order_status = ? AND order_date >= ?",
        (status, cutoff_date)
    )
    return {"orders": results, "count": len(results)}
```

**Step 5:** Server returns via stdout
```json
{
  "jsonrpc": "2.0",
  "result": {
    "orders": [
      {"order_number": "ORD-102459", "priority": "VIP", ...},
      {"order_number": "ORD-108117", "priority": "VIP", ...}
    ],
    "count": 50
  }
}
```

**Step 6:** Agent receives results and synthesizes answer
```
"Here are the delayed orders:
1. Order ORD-102459 (VIP, Louisville Hub)
2. Order ORD-108117 (VIP, Louisville Hub)
... and 48 more."
```

---

## Troubleshooting Common MCP Issues

### Issue: "Connection closed" error

**Cause:** Server prints to stdout during startup

**Solution:** Use `sys.stderr` for all logging:
```python
import sys
print("Server starting...", file=sys.stderr)
```

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Cause:** MCP not installed in virtual environment

**Solution:**
```bash
uv add mcp
# or
pip install mcp
```

### Issue: Tools not loading

**Cause:** Server path incorrect or not executable

**Solution:** Use absolute path to venv Python:
```python
python_exe = workspace_root / ".venv" / "Scripts" / "python.exe"
command = str(python_exe)  # Must be absolute path
```

### Issue: Database connection errors

**Cause:** Relative paths not resolving correctly

**Solution:** Use absolute paths from settings:
```python
db_path = str(settings.database_path)  # Absolute path
```

---

## Comparison Table

| Feature | Unit 6 Approach | This Project |
|---------|----------------|--------------|
| **MCP Client** | Claude Desktop / VS Code | Custom Python agent |
| **Configuration** | `mcp.json` file | Programmatic launch |
| **Server Launch** | External app | Python subprocess |
| **Use Case** | Human chat interface | Autonomous agent |
| **Setup Complexity** | Medium (config files) | Low (pure Python) |
| **Flexibility** | Limited to app features | Full control |
| **Debugging** | Via app logs | Python debugging |
| **Integration** | Standalone | Part of larger system |

---

## Best Practices

### 1. Server Design
- ✅ Use descriptive tool names and docstrings
- ✅ Include schema descriptions in tool parameters
- ✅ Return structured data with metadata
- ✅ Handle errors gracefully (try/except)
- ✅ Log to stderr, not stdout

### 2. Database Access
- ✅ Use parameterized queries (SQL injection prevention)
- ✅ Read-only operations (safety)
- ✅ Connection pooling via lifespan
- ✅ Return dictionaries (JSON-serializable)

### 3. Tool Design
- ✅ Flexible parameters (optional filters)
- ✅ Reasonable defaults (e.g., `days_back=30`)
- ✅ Clear documentation in docstrings
- ✅ Include usage examples in docs
- ✅ Return counts and metadata

---

## Next Steps: Using MCP with VS Code Copilot

If you want to use our warehouse MCP server with **VS Code Copilot**, create a configuration file in your workspace:

**`.vscode/settings.json`:**
```json
{
  "github.copilot.chat.codeGeneration.instructions": [
    {
      "text": "Use warehouse MCP server for data queries"
    }
  ],
  "mcp.servers": {
    "warehouse": {
      "type": "stdio",
      "command": "E:\\Projects\\warehouse-ai-assistant\\.venv\\Scripts\\python.exe",
      "args": ["run_mcp_server.py"],
      "cwd": "E:\\Projects\\warehouse-ai-assistant"
    }
  }
}
```

Then you can ask Copilot Chat: "What orders are delayed?" and it will use your MCP tools!

---

## Vector Store Decision: InMemoryVectorStore vs Persistent Databases

### Why We Use InMemoryVectorStore

**Decision:** We use `InMemoryVectorStore` from LangChain for the RAG pipeline.

**Alternatives Considered:**
- ChromaDB (persistent, disk-based)
- Pinecone (cloud-hosted, persistent)
- FAISS (Facebook AI Similarity Search)

**Why InMemoryVectorStore is the Right Choice:**

1. **Capstone Rubric Compliance**
   - ✅ No requirement for cross-session persistence
   - ✅ "Conversation management" means multi-turn chat, not persistent storage
   - ✅ Meets all "Excellent" criteria without added complexity

2. **Performance**
   - ✅ Loads 46 chunks in ~2 seconds
   - ✅ No disk I/O overhead
   - ✅ Fast similarity search (in-memory operations)

3. **Simplicity**
   - ✅ No external dependencies (no database to install)
   - ✅ Works out-of-the-box with LangChain
   - ✅ Easier to explain in presentation
   - ✅ Matches Unit 4 course patterns

4. **Cost**
   - ✅ Re-embedding 46 chunks costs ~$0.0001 per startup
   - ✅ Negligible cost for proof-of-concept
   - ✅ No cloud hosting fees

**Trade-offs Accepted:**
- ⚠️ Re-embeds documents on each startup (2 seconds)
- ⚠️ Not suitable for production with thousands of documents
- ⚠️ Doesn't persist across sessions

**When You Would Upgrade:**
- Production deployment with large document sets (1000+ chunks)
- Need for user-specific document collections
- Cross-session conversation history requirements
- Team collaboration features

**Implementation Location:**
- `src/rag/vector_store.py` - VectorStoreManager class
- Line 57: `self.vector_store = InMemoryVectorStore(self.embeddings)`

---

## Resources

- **MCP Specification:** https://spec.modelcontextprotocol.io/
- **FastMCP Documentation:** https://github.com/modelcontextprotocol/python-sdk
- **Unit 6 Course Materials:** `../CodeYouAIClass2026Unit6/`
- **Our MCP Server:** `src/tools/warehouse_mcp.py`
- **Our SQL Agent:** `src/agents/sql_agent.py`
- **Our RAG Agent:** `src/agents/rag_agent.py`
- **Our Weather Agent:** `src/agents/weather_agent.py`
- **Vector Store:** `src/rag/vector_store.py`

---

*Last Updated: April 1, 2026 - Three-agent system with Tavily integration documented*
