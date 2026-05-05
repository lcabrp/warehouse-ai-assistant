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

## SQL Agent Error Handling (Production-Quality)

### Problem: Generic Error Messages

**Before:** All database errors returned a single generic message:
```
"I encountered an error querying the database. Please try rephrasing your question."
```

**Issue:** Users couldn't understand what actually went wrong:
- Is the database offline? (Connection problem)
- Is my question phrased poorly? (Query syntax)
- Is the system overloaded? (Performance problem)

### Solution: Granular Error Classification

We implemented a three-tier exception hierarchy to distinguish between fundamental failure modes:

#### Exception Hierarchy

```python
# Base exception - catch all warehouse database errors
class WarehouseDatabaseError(Exception):
    pass

# Subclass 1: Connection/Access Issues
class DatabaseConnectionError(WarehouseDatabaseError):
    """Database is offline, corrupted, or inaccessible"""
    # User message: "I'm unable to connect to the warehouse database right now..."

# Subclass 2: Query/Syntax Issues  
class DatabaseQueryError(WarehouseDatabaseError):
    """SQL syntax, schema, or logic error"""
    def __init__(self, message: str, sql_error: str = None, query: str = None):
        super().__init__(message)
        self.sql_error = sql_error  # Original SQLite error (for logs)
        self.query = query          # Failed query (for debugging)
    # User message: "The database query failed due to a problem..."

# Subclass 3: Performance Issues
class DatabaseQueryTimeoutError(WarehouseDatabaseError):
    """Query is taking too long - database locked or overloaded"""
    # User message: "The database query took too long to complete..."
```

#### Error Detection in WarehouseDB

**Connection Detection:**
```python
def connect(self):
    try:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    except sqlite3.DatabaseError as e:
        # Database corruption or format issues
        raise DatabaseConnectionError(...) from e
    except (OSError, IOError) as e:
        # File system issues: missing file, permissions
        raise DatabaseConnectionError(...) from e
```

**Query Execution Detection:**
```python
def execute_query(self, query: str, params: tuple = ()):
    try:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    except sqlite3.OperationalError as e:
        # Most common: syntax, "no such table/column", locks
        error_msg = str(e).lower()
        if "no such table" in error_msg or "no such column" in error_msg:
            raise DatabaseQueryError(
                "The database schema doesn't match the query...",
                sql_error=str(e),
                query=query
            ) from e
        elif "locked" in error_msg or "timeout" in error_msg:
            raise DatabaseQueryTimeoutError(
                "The database is currently locked or busy..."
            ) from e
        else:
            raise DatabaseQueryError(...) from e
            
    except sqlite3.ProgrammingError as e:
        # Syntax error or parameter binding issue
        raise DatabaseQueryError(
            "The SQL query has a syntax error or parameter binding issue.",
            sql_error=str(e),
            query=query
        ) from e
```

#### User-Facing Error Messages in SQLAgent

```python
async def query(self, question: str) -> str:
    try:
        # Execute agent...
        result = await self.agent_executor.ainvoke({"messages": [...]})
        return result["messages"][-1].content
        
    except DatabaseConnectionError as e:
        # Database is offline or inaccessible
        return (
            "I'm unable to connect to the warehouse database right now. "
            "The database server may be offline or there may be a file access issue. "
            "Please try again in a few moments."
        )
    except DatabaseQueryTimeoutError as e:
        # Query is taking too long
        return (
            "The database query took too long to complete. "
            "This might mean the database is busy or your question requires a complex search. "
            "Please try a simpler or more specific question."
        )
    except DatabaseQueryError as e:
        # Query failed due to syntax/schema
        return (
            "The database query failed due to a problem with how your question "
            "was converted to a database search. "
            "Please try rephrasing your question in a different way."
        )
```

#### Benefits

✅ **Users understand what went wrong**
- Actionable guidance for each failure type
- Not just "an error occurred"

✅ **Developers can debug more easily**
- Original SQL errors logged to stderr
- Query text preserved for analysis
- Clear exception hierarchy

✅ **Future-proof**
- Easy to add more specific error types
- Can implement retry logic per error type
- Supports monitoring and alerting

**File Location:** `src/tools/warehouse_mcp.py` (lines 30-185)

---

## RAG Response Citation Validation

### Problem: Fragile Citation Enforcement

**Requirement:** RAG agent must cite document sources (capstone rubric requirement)

**Before:** Enforced via system prompt only:
```python
system_prompt = """ALWAYS cite sources explicitly in your response:
   - Format: "According to [Document Name], [answer]..."
   - Include section headers when relevant
"""
```

**Issue:** Relies on LLM following instructions - not guaranteed:
- LLM might forget citation in some responses
- No structural validation
- No way to verify compliance in tests
- "According to..." sometimes doesn't appear exactly as specified

### Solution: Structural Citation Validation Framework

We built a three-layer validation system:

#### Layer 1: Citation Extraction

```python
class CitationExtractor:
    """Extract citations from text using regex patterns."""
    
    CITATION_PATTERNS = [
        r"According to\s+([^\s,\(]+(?:\.md)?)\s*,",
        r"According to\s+([^\s,\(]+(?:\.md)?)\s*\(\s*([^\)]+)\s*\)\s*,",
        r"As stated in\s+([^\s,\(]+(?:\.md)?)\s*,",
    ]
    
    @staticmethod
    def extract_citations(response: str) -> List[Citation]:
        """Extract all citations, with source and optional section."""
        citations = []
        for pattern in CitationExtractor.CITATION_PATTERNS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                source = match.group(1)
                section = match.group(2) if len(match.groups()) > 1 else None
                citations.append(Citation(source, section, match.start()))
        return citations
```

#### Layer 2: Citation Validation

```python
class CitationValidator:
    """Validate that citations are proper and complete."""
    
    @staticmethod
    def validate_has_citations(response: str) -> Tuple[bool, str]:
        """Check response includes citations (or is 'no results')."""
        if "no relevant procedures found" in response.lower():
            return True, "Valid: No results response"
        
        citations = CitationExtractor.extract_citations(response)
        if not citations:
            return False, "Response contains no citations"
        return True, f"Valid: Found {len(citations)} citation(s)"
    
    @staticmethod
    def validate_citation_format(response: str) -> Tuple[bool, List[str]]:
        """Validate all citations follow expected format."""
        issues = []
        citations = CitationExtractor.extract_citations(response)
        
        for citation in citations:
            if not citation.source or len(citation.source) < 3:
                issues.append(f"Citation has invalid source: '{citation.source}'")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_no_citation_claims_without_citation(response: str):
        """Detect factual claims without attribution."""
        # Find uncited procedural statements like "The procedure is..."
        # or "You should..." without nearby citation
        # Returns issues found
```

#### Layer 3: Runtime Validator

```python
class RAGResponseValidator:
    """Validates responses before returning to users."""
    
    def validate_response(self, response: str) -> ValidationResult:
        """Comprehensive validation of RAG response."""
        issues = []
        
        # Check 1: Not empty
        if not response or not response.strip():
            return ValidationResult(is_valid=False, issues=["Empty response"])
        
        # Check 2: Is "no results" special case?
        is_no_results = any(
            pattern in response.lower()
            for pattern in [
                "no relevant procedures",
                "i don't find that information",
                "cannot find"
            ]
        )
        
        # Check 3: Validate citations
        has_citations, msg = CitationValidator.validate_has_citations(response)
        if not has_citations and not is_no_results:
            issues.append(f"Missing citations - {msg}")
        
        # Check 4: Validate format
        format_valid, format_issues = CitationValidator.validate_citation_format(response)
        if not format_valid:
            issues.extend(format_issues)
        
        # Check 5: Check for uncited claims
        if citations:
            claims_valid, claim_issues = CitationValidator.validate_no_citation_claims_without_citation(response)
            if not claims_valid:
                issues.extend(claim_issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            citations_found=len(citations),
            warning_level="none" if not issues else "warning"
        )
```

#### Using the Validator

**Option 1: Manual Validation in Tests**
```python
from src.rag.citation_validator import RAGResponseValidator

validator = RAGResponseValidator()
response = await rag_agent.query("How do I cycle count?")
validation = validator.validate_response(response)

assert validation.is_valid, f"Citation issues: {validation.issues}"
print(f"Citations found: {validation.citations_found}")
```

**Option 2: Wrap RAG Agent for Automatic Validation**
```python
from src.rag.citation_validator import ValidatedRAGAgent

rag_agent = await create_rag_agent()
validated_agent = ValidatedRAGAgent(rag_agent, strict_mode=True)

# Will raise CitationError if response missing citations
response = await validated_agent.query("How do I cycle count?")
```

**Option 3: Check Citations in Responses**
```python
validator = RAGResponseValidator()
citations = validator.get_citations(response)
sources = validator.get_citation_sources(response)
print(f"Sources cited: {sources}")
```

#### Test Coverage

**17 comprehensive tests** covering:

```python
# Citation Extraction (4 tests)
- Basic citation extraction
- Citations with section headers
- Multiple citations in one response
- Citation presence detection

# Citation Format Validation (4 tests)
- Proper "According to..." syntax
- Multiple sources in one response
- Presence validation
- Special case: "no results" responses

# Citation Completeness (2 tests)
- Detecting uncited claims
- Verifying all sources are cited

# Edge Cases (4 tests)
- Empty responses
- Whitespace-only responses
- Very short responses
- Citation counting

# Consistency (2 tests)
- Same response returns same result
- Extraction is idempotent

# Integration (1 test)
- Real RAG agent response scenarios
```

**Result:** 17/17 tests passing ✅

#### Benefits

✅ **Structural Guarantee**
- Not just system prompt suggestion
- Validated before responses sent to users
- Can enforce strictly or warn

✅ **Testing & Debugging**
- 17 test cases ensure compliance
- Easy to verify in automated tests
- Can identify problematic patterns

✅ **Production-Ready**
- Wrapper agent for strict validation
- Optional integration (backward compatible)
- Can add to CI/CD pipeline

✅ **Rubric Compliance**
- Provably meets capstone citation requirement
- Test evidence of validation
- Can demonstrate during presentation

**File Locations:**
- Citation extraction/validation: `tests/test_rag_citation_validation.py`
- Runtime validator: `src/rag/citation_validator.py`

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
