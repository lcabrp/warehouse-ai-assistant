# Warehouse AI Assistant — Copilot Instructions

This repo is a **capstone AI project** demonstrating advanced multi-agent systems for warehouse operations. Primary focus: LangGraph agent orchestration, MCP (Model Context Protocol) tool calling, RAG (Retrieval Augmented Generation), web search integration, and intelligent routing with synthesis.

**Architecture:** Multi-agent system with SQL, RAG, and Weather agents  
**Tech Stack:** Python 3.13, LangChain, LangGraph, FastMCP, OpenAI GPT-4o-mini, Tavily, Streamlit  
**Key Concepts:** MCP client-server, agentic AI, tool calling, vector search, LLM routing

---

## Project Structure

```
warehouse-ai-assistant/
├── src/
│   ├── agents/
│   │   ├── sql_agent.py              # Database query agent (MCP client)
│   │   ├── rag_agent.py              # Document search agent (RAG)
│   │   ├── weather_agent.py          # Web search agent (Tavily)
│   │   └── router.py                 # LLM-based routing & synthesis
│   ├── tools/
│   │   └── warehouse_mcp.py          # MCP server (6 database tools)
│   ├── rag/
│   │   └── vector_store.py           # Document embeddings & search
│   └── config/
│       └── settings.py               # Configuration
├── data/
│   ├── warehouse.db                  # SQLite database (10K orders)
│   └── docs/                         # Markdown documentation (RAG source)
├── docs/                             # Project documentation
├── web_app.py                        # Streamlit UI
├── main.py                           # CLI interface
├── generate_data.py                  # Synthetic data generator
├── run_mcp_server.py                 # MCP server launcher
├── test_mcp_server.py                # MCP server tests
├── QUICK_START.py                    # Getting started script
├── README.md                         # Architecture overview
├── MCP_ARCHITECTURE.md               # ⭐ Technical deep dive
└── pyproject.toml                    # Dependencies
```

---

## Architecture Overview

### Multi-Agent System Flow

```
User Question
     ↓
[Router / Classifier LLM]
     ↓
Decision:
     ├─ SQL Agent → MCP Server → Database → Structured Data
     ├─ RAG Agent → Vector Store → Procedures/Documentation
     ├─ Weather Agent → Tavily Search → External Information
     ├─ SQL_WEATHER → Database + Weather → Correlated Analysis
     └─ ALL → SQL + RAG + Weather → Comprehensive Synthesis
     ↓
[Synthesizer LLM] (if multi-source)
     ↓
Response to User
```

### Three Specialized Agents

**1. SQL Agent** (`src/agents/sql_agent.py`)
- Queries warehouse database via MCP tools
- Handles: orders, inventory, shipments, exceptions, metrics
- Uses: FastMCP client, gpt-4o-mini (temp=0)
- Returns: Structured data with analysis

**2. RAG Agent** (`src/agents/rag_agent.py`)
- Searches operational procedures and documentation
- Handles: troubleshooting, policies, how-to guides
- Uses: InMemoryVectorStore, text-embedding-3-small
- **Always cites sources**: Document names and section headers

**3. Weather Agent** (`src/agents/weather_agent.py`)
- Searches web for real-time external information
- Handles: weather, transportation disruptions, carrier delays
- Uses: Tavily API, gpt-4o-mini (temp=0.3)
- **Provides context**: Why shipments might be delayed

---

## MCP (Model Context Protocol) Implementation

### What is MCP?

**MCP = Standardized way for AI to connect to tools**

Think of it as "USB-C for AI" - a protocol that lets AI systems use external tools (databases, APIs) in a consistent way.

**Key Components:**
- **MCP Server:** Provides tools (our warehouse database queries)
- **MCP Client:** Uses those tools (our SQL agent)
- **Transport:** How they communicate (STDIO subprocess)

### Our MCP Architecture

**Server Side** (`src/tools/warehouse_mcp.py`):
```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("warehouse-server")

@mcp.tool()
async def search_orders(
    ctx: Context,
    status: str = None,
    customer_name: str = None,
    limit: int = 10
) -> dict:
    """
    Search warehouse orders by status or customer.
    
    Args:
        status: Order status (pending, shipped, delivered, cancelled)
        customer_name: Customer name to filter by
        limit: Maximum number of results
        
    Returns:
        List of matching orders with details
    """
    # Query database
    # Return results as JSON
```

**6 Available Tools:**
1. `search_orders` - Search orders by status/customer
2. `check_inventory` - Check stock levels
3. `get_shipment_status` - Track shipments
4. `get_exceptions` - View quality exceptions
5. `get_labor_metrics` - Labor productivity data
6. `get_order_details` - Detailed order information

**Client Side** (`src/agents/sql_agent.py`):
```python
from langchain_mcp_adapters.client import create_client_session
from langgraph.prebuilt import create_react_agent

# Start MCP server as subprocess
async with create_client_session(
    "python",
    ["run_mcp_server.py"],
    transport="stdio"
) as client:
    # Get tools from server
    tools = await client.get_tools()
    
    # Create LangGraph agent with tools
    agent = create_react_agent(llm, tools)
    
    # Agent can now use database tools
    result = await agent.ainvoke({"messages": [user_query]})
```

### MCP vs Direct Database Access

**Why use MCP instead of direct SQL?**

✅ **Abstraction:** Agent doesn't need SQL knowledge  
✅ **Safety:** Tools control what agent can access  
✅ **Reusability:** Same server works for different AI applications  
✅ **Monitoring:** Centralized logging of tool usage  
✅ **Flexibility:** Can swap backends without changing agent

---

## RAG (Retrieval Augmented Generation)

### Document Processing Pipeline

**1. Load Documents:**
```python
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader("data/docs/", glob="**/*.md")
documents = loader.load()
```

**2. Split into Chunks:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)
# Result: 46 chunks from 5 markdown files
```

**3. Create Embeddings:**
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
```

**4. Store in Vector DB:**
```python
from langchain.vectorstores import InMemoryVectorStore

vector_store = InMemoryVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings
)
```

**5. Query at Runtime:**
```python
# Find relevant documents
results = vector_store.similarity_search(
    "How do I handle damaged inventory?",
    k=3  # Top 3 most relevant chunks
)

# Pass to LLM with context
prompt = f"Context: {results}\n\nQuestion: {user_question}"
```

### RAG Best Practices

**Always cite sources:**
```python
# ✓ GOOD - Include source metadata
response = f"""
Based on the documentation:

{answer}

**Sources:**
- {doc.metadata['source']}
- Section: {doc.metadata['header']}
"""

# ✗ BAD - No citation
response = f"{answer}"  # User can't verify accuracy
```

---

## LangGraph Agent Patterns

### ReAct Agent (SQL & RAG Agents)

**ReAct = Reasoning + Acting**

Agent follows loop:
1. **Reason:** Think about what to do next
2. **Act:** Use a tool or respond
3. **Observe:** See tool result
4. Repeat until answer is complete

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    llm=llm,
    tools=tools,
    state_modifier="You are a warehouse operations assistant..."
)

# Agent automatically decides when/how to use tools
result = await agent.ainvoke({"messages": [user_message]})
```

### Router Agent

**LLM-based classification:**
```python
from langchain_core.prompts import ChatPromptTemplate

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    Classify the user question into one of these categories:
    - SQL: Database queries (orders, inventory, shipments)
    - RAG: Procedures, policies, documentation
    - WEATHER: External information (weather, delays, news)
    - SQL_WEATHER: Both database + external context
    - ALL: Needs all three sources
    """),
    ("human", "{question}")
])

# Get classification
classification = llm.invoke(router_prompt.format(question=user_question))
```

### Synthesis Agent

**Combine multi-source answers:**
```python
synthesis_prompt = f"""
You are synthesizing information from multiple sources:

**Database Data:**
{sql_result}

**Documentation:**
{rag_result}

**External Information:**
{weather_result}

Provide a comprehensive answer that integrates all three sources.
"""

final_answer = llm.invoke(synthesis_prompt)
```

---

## LangChain Conventions

### Message Patterns

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Create messages
messages = [
    SystemMessage(content="You are a warehouse assistant"),
    HumanMessage(content="What orders are pending?"),
    AIMessage(content="Let me check the database..."),
]

# Invoke LLM
response = llm.invoke(messages)
```

### Tool Calling Pattern

```python
from langchain_core.tools import tool

@tool
def search_inventory(item_name: str) -> dict:
    """
    Search inventory by item name.
    
    Args:
        item_name: Name of the item to search for
        
    Returns:
        Inventory details including quantity and location
    """
    # Query database
    return {"item": item_name, "quantity": 150, "location": "A-12"}

# LLM can call this tool automatically
tools = [search_inventory]
llm_with_tools = llm.bind_tools(tools)
```

### Async Patterns

**Always use async for agents:**
```python
import asyncio

async def query_agent(question: str):
    """Async agent invocation"""
    result = await agent.ainvoke({"messages": [HumanMessage(content=question)]})
    return result

# Run from sync context
result = asyncio.run(query_agent("What orders are pending?"))
```

---

## Configuration & Environment

### Required API Keys

```bash
# .env file (never commit!)
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

### settings.py Pattern

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    tavily_api_key: str
    database_path: str = "data/warehouse.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Streamlit UI Patterns

### Basic App Structure

```python
import streamlit as st

st.set_page_config(page_title="Warehouse AI Assistant", page_icon="🏭")

# Sidebar
with st.sidebar:
    st.header("Settings")
    agent_type = st.selectbox("Agent", ["Auto", "SQL", "RAG", "Weather"])

# Main content
st.title("🏭 Warehouse AI Assistant")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask about warehouse operations..."):
    # Add to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get response
    with st.spinner("Thinking..."):
        response = asyncio.run(query_agent(prompt))
    
    # Display response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
```

### Running Streamlit

```bash
# Start web interface
uv run streamlit run web_app.py

# Or with Python directly
python -m streamlit run web_app.py

# Auto-open browser
streamlit run web_app.py --server.headless false
```

---

## Database Schema

**SQLite database:** `data/warehouse.db`

### Tables

**orders:**
- order_id (PK)
- customer_name
- order_date
- status (pending, shipped, delivered, cancelled)
- total_amount
- region

**inventory:**
- item_id (PK)
- item_name
- quantity
- warehouse_location
- last_updated

**shipments:**
- shipment_id (PK)
- order_id (FK)
- carrier
- tracking_number
- ship_date
- delivery_date
- status

**exceptions:**
- exception_id (PK)
- order_id (FK)
- exception_type (damaged, missing, incorrect)
- description
- reported_date
- resolved (boolean)

**labor_metrics:**
- metric_id (PK)
- employee_id
- shift_date
- hours_worked
- items_picked
- items_packed
- productivity_rate

---

## Development Workflows

### Adding New MCP Tool

1. **Define tool in warehouse_mcp.py:**
```python
@mcp.tool()
async def new_tool(ctx: Context, param: str) -> dict:
    """Tool description for LLM"""
    # Implementation
    return result
```

2. **Test tool:**
```bash
python test_mcp_server.py
```

3. **Agent automatically discovers it** (no changes needed)

### Adding New Agent

1. Create `src/agents/new_agent.py`
2. Follow ReAct pattern with LangGraph
3. Add to router classification
4. Update synthesis logic if needed

### Testing Agent Locally

```bash
# CLI interface
python main.py

# Interactive prompts:
# > What orders are pending?
# > How do I handle damaged inventory?
# > What's the weather in Louisville?
```

---

## Common Pitfalls & Solutions

### MCP Server Won't Start

**Problem:** `ModuleNotFoundError` or connection timeout

**Solution:**
```python
# Ensure correct Python interpreter
async with create_client_session(
    sys.executable,  # Use current Python
    ["run_mcp_server.py"],
    transport="stdio"
) as client:
    ...
```

### RAG Not Finding Documents

**Problem:** Vector store returns no results

**Solution:**
```python
# Check document loading
print(f"Loaded {len(documents)} documents")
print(f"Split into {len(chunks)} chunks")

# Verify embeddings
print(f"Embedding dimension: {len(vectors[0])}")

# Test similarity search
results = vector_store.similarity_search("test", k=1)
print(results)
```

### Agent Not Using Tools

**Problem:** Agent responds without calling tools

**Solution:**
```python
# Strengthen system prompt
state_modifier = """
You are a warehouse assistant. You MUST use the available tools to answer questions.
Never make up information. Always query the database or search documentation.
"""

# Or force tool use
llm_with_tools = llm.bind_tools(tools, tool_choice="required")
```

### Async Event Loop Issues

**Problem:** `RuntimeError: This event loop is already running`

**Solution:**
```python
import asyncio
import nest_asyncio

# Allow nested event loops (Jupyter/Streamlit)
nest_asyncio.apply()

# Or use asyncio.run()
result = asyncio.run(async_function())
```

---

## Running the Application

### Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set API keys
echo "OPENAI_API_KEY=sk-..." > .env
echo "TAVILY_API_KEY=tvly-..." >> .env

# 3. Generate sample data (first time only)
python generate_data.py

# 4. Run web interface
uv run streamlit run web_app.py

# 5. Or run CLI
python main.py
```

### Batch Scripts

```bash
# Windows
start_web.bat    # Launch Streamlit UI
start_cli.bat    # Launch CLI interface

# Both activate venv and run appropriate script
```

---

## Technical Deep Dive

For comprehensive technical details, see:
- **[MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md)** - MCP protocol deep dive
- **[HOW_TO_LAUNCH.md](HOW_TO_LAUNCH.md)** - Detailed setup instructions
- **[REQUIREMENTS_COMPLIANCE.md](REQUIREMENTS_COMPLIANCE.md)** - Project requirements

---

## References

- **LangChain Docs:** https://python.langchain.com/docs/
- **LangGraph Tutorial:** https://langchain-ai.github.io/langgraph/
- **MCP Specification:** https://modelcontextprotocol.io/
- **FastMCP:** https://github.com/jlowin/fastmcp
- **Tavily API:** https://tavily.com/
- **Streamlit Docs:** https://docs.streamlit.io/
