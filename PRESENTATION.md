# 🏭 Warehouse AI Assistant
## Capstone Project Presentation

---

## 📋 Table of Contents
1. [Problem Statement](#problem-statement)
2. [Solution Overview](#solution-overview)
3. [Technology Stack & Tools](#technology-stack--tools)
4. [Architecture & System Design](#architecture--system-design)
5. [Data Generation](#data-generation)
6. [Project Structure & Code Organization](#project-structure--code-organization)
7. [Entry Points & How to Use](#entry-points--how-to-use)
8. [Key Modules & Components](#key-modules--components)
9. [Course Integration](#course-integration)
10. [Real-World Potential](#real-world-potential)
11. [Demo & Testing](#demo--testing)

---

## 🎯 Problem Statement

### The Challenge
Modern warehouse operations face complex information needs:

- **Data Silos**: Operational data lives in databases, procedures live in documents
- **Complex Queries**: Staff need both "what" (data) AND "how" (procedures)
- **Time-Consuming**: Looking up SOPs, checking multiple systems, correlating information
- **Training Gap**: New employees need quick access to both data and guidance
- **24/7 Operations**: Need instant answers without interrupting supervisors

### Real-World Example Scenarios
1. **Order Manager**: "Why is order ORD-102459 delayed and what's the escalation procedure?"
   - Needs: Database query (order status) + Document lookup (escalation process)

2. **Warehouse Associate**: "Show me critical inventory items and explain the replenishment policy"
   - Needs: Live inventory data + Policy documentation

3. **Operations Supervisor**: "What exceptions are open and how should I handle them?"
   - Needs: Exception reports + Troubleshooting procedures

### Why This Matters
- **Efficiency**: Seconds to get answers vs. minutes searching systems
- **Accuracy**: AI cites sources, reducing human error
- **Scalability**: Handles unlimited concurrent queries
- **Training**: Self-service knowledge for new staff

---

## 💡 Solution Overview

### What We Built
An **intelligent multi-agent AI system** that:
1. Automatically **routes questions** to the right specialized agent
2. Queries **structured databases** for operational data
3. Searches **unstructured documents** for procedures and policies
4. **Synthesizes information** from multiple sources into coherent answers
5. Provides **two interfaces**: Web UI and CLI

### Key Innovation
**Smart Routing Architecture**: Unlike single-agent chatbots, our system:
- Uses an LLM classifier to understand question intent
- Routes to specialized agents optimized for specific tasks
- Can invoke multiple agents and synthesize their outputs
- Maintains conversation context across interactions

### User Experience
```
User: "Why is order ORD-102459 delayed?"

System:
1. Classifies question → "SQL query needed"
2. Routes to SQL Agent
3. SQL Agent calls MCP tools to query database
4. Returns structured answer with shipment details

Time: ~3 seconds
```

```
User: "How do I troubleshoot a conveyor jam?"

System:
1. Classifies question → "Procedural knowledge needed"
2. Routes to RAG Agent
3. RAG Agent searches documentation
4. Returns step-by-step instructions with source citations

Time: ~2 seconds
```

---

## 🛠️ Technology Stack & Tools

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.13 | Modern async/await support |
| **LLM** | OpenAI GPT-4o-mini | Latest | Agent reasoning, classification, synthesis |
| **Embeddings** | text-embedding-3-small | Latest | Semantic document search |
| **Database** | SQLite | 3.x | Lightweight, serverless warehouse data |
| **Data Generation** | Faker | 40.11.0+ | Realistic synthetic data |

### AI/ML Frameworks

| Framework | Version | Usage in Project |
|-----------|---------|------------------|
| **LangChain** | 0.3.31+ | Agent orchestration, tool calling, message handling |
| **LangGraph** | 0.3.21+ | Multi-agent workflow coordination |
| **LangChain-OpenAI** | 0.3.1+ | OpenAI LLM and embedding integration |
| **LangChain-Community** | 0.3.31+ | Vector store (InMemoryVectorStore) |

### MCP (Model Context Protocol)

| Package | Version | Purpose |
|---------|---------|---------|
| **mcp** | 1.6.0+ | MCP protocol implementation |
| **langchain-mcp-adapters** | 0.1.0+ | Bridge between LangChain tools and MCP servers |
| **Starlette** | 0.45.2+ | ASGI framework for MCP server |
| **Uvicorn** | 0.34.0+ | ASGI server for running MCP |

### User Interfaces

| Interface | Technology | Why We Chose It |
|-----------|-----------|-----------------|
| **Web UI** | Streamlit 1.39.0+ | Rapid prototyping, built-in chat components, professional look |
| **CLI** | Python asyncio | Lightweight, scriptable, works anywhere |

### Development Tools

| Tool | Purpose |
|------|---------|
| **uv** | Fast Python package manager and environment manager |
| **ruff** | Lightning-fast linting and formatting |
| **pyproject.toml** | Modern Python project configuration |

---

## 🏗️ Architecture & System Design

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │   Web UI (Streamlit) │        │   CLI (asyncio)      │      │
│  │   Port: 8501         │        │   Terminal-based     │      │
│  └──────────┬───────────┘        └──────────┬───────────┘      │
└─────────────┼──────────────────────────────┼──────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTER / CLASSIFIER                          │
│  • LLM-based question classification                            │
│  • Maintains conversation history                               │
│  • Routes to: SQL | RAG | BOTH                                  │
│  • Synthesizes multi-source answers                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                  ↓
┌───────────────┐  ┌──────────────┐  ┌─────────────────┐
│  SQL AGENT    │  │  RAG AGENT   │  │  BOTH           │
│               │  │              │  │  (Sequential)   │
│  Queries data │  │  Searches    │  │  SQL → RAG →    │
│  via MCP      │  │  documents   │  │  Synthesize     │
└───────┬───────┘  └──────┬───────┘  └─────────────────┘
        ↓                  ↓
┌───────────────┐  ┌──────────────────┐
│  MCP SERVER   │  │  VECTOR STORE    │
│               │  │                  │
│  6 Tools:     │  │  46 Chunks       │
│  • search_    │  │  • Cycle counts  │
│    orders     │  │  • Equipment     │
│  • check_     │  │  • Replenishment │
│    inventory  │  │  • Operations    │
│  • get_       │  │  • Troubleshoot  │
│    shipment   │  │                  │
│  • get_order  │  │  Embeddings:     │
│    _details   │  │  text-embedding- │
│  • get_       │  │  3-small         │
│    exceptions │  │                  │
│  • get_labor  │  │                  │
│    _metrics   │  │                  │
└───────┬───────┘  └──────────────────┘
        ↓
┌───────────────────────────┐
│   SQLite Database         │
│   warehouse.db (3.18 MB)  │
│                           │
│   Tables:                 │
│   • warehouses            │
│   • locations             │
│   • items                 │
│   • inventory             │
│   • orders (10,000)       │
│   • order_lines           │
│   • shipments             │
│   • exceptions            │
│   • labor_metrics         │
└───────────────────────────┘
```

### System Flow - Step by Step

#### Example: "Show me critical inventory items and explain the replenishment policy"

```
Step 1: User Input
   ↓
Step 2: Router Receives Question
   • Adds to conversation history
   • Calls classifier LLM
   ↓
Step 3: Classifier LLM Analyzes
   • "Needs database query for inventory levels"
   • "Needs document about replenishment policy"
   • Decision: BOTH
   ↓
Step 4: SQL Agent Execution
   • Receives question
   • Decides to use check_inventory tool
   • MCP server queries: SELECT * FROM inventory WHERE quantity < reorder_point
   • Returns: List of critical items
   ↓
Step 5: RAG Agent Execution
   • Receives question
   • Embeds question query
   • Searches vector store
   • Retrieves relevant chunks from Replenishment_Policy.md
   • Returns: Policy explanation with source citations
   ↓
Step 6: Synthesis
   • Router calls synthesis LLM
   • Combines SQL results + RAG results
   • Creates coherent answer
   ↓
Step 7: Response to User
   "Here are 10 critical inventory items below reorder point:
    [Item data table]
    
    According to the Replenishment Policy (Section 2.1):
    [Policy details]
    
    Recommended action: [Combined guidance]"
```

### Data Flow Architecture

```
┌──────────────┐
│  User Query  │
└──────┬───────┘
       ↓
┌──────────────────┐
│  Classification  │  ← GPT-4o-mini (temp=0.3)
└──────┬───────────┘
       ↓
┌──────────────────────────────────┐
│           Route Decision          │
│  ┌────────┬──────────┬─────────┐ │
│  │  SQL   │   RAG    │  BOTH   │ │
│  └────┬───┴────┬─────┴───┬─────┘ │
└───────┼────────┼─────────┼───────┘
        ↓        ↓         ↓
   ┌────────┐ ┌──────┐ ┌────────────┐
   │SQL Tool│ │Vector│ │Sequential  │
   │Calls   │ │Search│ │Execution + │
   │        │ │      │ │Synthesis   │
   └────┬───┘ └───┬──┘ └──────┬─────┘
        ↓         ↓           ↓
   ┌────────┐ ┌──────┐ ┌────────────┐
   │Database│ │ Docs │ │Combined    │
   │Results │ │Chunks│ │Answer      │
   └────────┘ └──────┘ └────────────┘
```

---

## 📊 Data Generation

### Why We Generated Realistic Data

**Problem**: Capstone projects often use toy datasets that don't reflect real-world complexity.

**Our Approach**: Built a sophisticated data generator using **Faker library** to create:
- Realistic names, addresses, companies
- Believable product SKUs and descriptions
- Time-series data with realistic patterns
- Interconnected relationships between tables

### Database Schema

```sql
warehouses (2 facilities)
  ├─ locations (4,000 slots across warehouses)
  ├─ items (2,000 SKUs)
  └─ inventory (stock levels per location)

orders (10,000 orders)
  ├─ order_lines (20,000+ line items)
  ├─ shipments (tracking & delivery status)
  └─ exceptions (operational issues)

labor_metrics (productivity tracking)
  └─ Time series data for performance analysis
```

### Data Characteristics

| Table | Records | Key Features |
|-------|---------|--------------|
| **orders** | 10,000 | Realistic order numbers (ORD-XXXXXX), statuses, dates |
| **order_lines** | ~20,000 | Multiple items per order, realistic quantities |
| **items** | 2,000 | Product categories (Apparel, Electronics, etc.) |
| **inventory** | 4,000+ | Stock levels, reorder points, location tracking |
| **shipments** | 10,000 | Carrier tracking numbers, delivery dates, delays |
| **exceptions** | 500 | Scanner issues, damaged goods, missing items |
| **labor_metrics** | Time-series | Employee productivity, picking rates |

### Generator Script: `generate_data.py`

**Key Features:**
```python
# Realistic text data
fake = Faker()
order_number = f"ORD-{100000 + i}"
customer_name = fake.company()
tracking_number = fake.bothify("??########")

# Time-series patterns
order_date = datetime.now() - timedelta(days=random.randint(0, 90))
ship_date = order_date + timedelta(days=random.randint(1, 5))

# Business logic
if quantity < reorder_point:
    status = "CRITICAL"
```

**Generation Process:**
1. Creates 9 interconnected tables
2. Ensures referential integrity (foreign keys)
3. Simulates realistic business scenarios
4. Seeds random for reproducibility
5. Total size: ~3.18 MB database

**To regenerate:**
```bash
uv run python generate_data.py
```

### Why This Matters for Real-World Use
✅ **Data looks professional** - Could present to stakeholders  
✅ **Realistic queries work** - Tests actual use cases  
✅ **Scalable pattern** - Easy to expand to millions of records  
✅ **Training value** - Demonstrates production-quality data modeling  

---

## 📁 Project Structure & Code Organization

### Directory Tree

```
warehouse-ai-assistant/
│
├── 📄 PROJECT FILES
│   ├── README.md                    # Main documentation
│   ├── PRESENTATION.md              # This document
│   ├── PROGRESS_SUMMARY.md          # Development log
│   ├── HOW_TO_LAUNCH.md            # Quick start guide
│   ├── REQUIREMENTS_COMPLIANCE.md   # Rubric checklist
│   ├── pyproject.toml              # Dependencies & config
│   └── .env                         # API keys (not in git)
│
├── 🚀 ENTRY POINTS
│   ├── main.py                      # CLI interface
│   ├── web_app.py                  # Streamlit web UI
│   ├── QUICK_START.py              # Minimal example
│   ├── run_mcp_server.py           # MCP server standalone
│   ├── start_cli.bat               # Windows launcher (CLI)
│   └── start_web.bat               # Windows launcher (Web)
│
├── 🔧 DATA & GENERATION
│   ├── generate_data.py            # Database generator
│   ├── test_mcp_server.py          # MCP tools testing
│   └── data/
│       └── warehouse.db            # SQLite database (3.18 MB)
│
├── 📚 DOCUMENTATION
│   └── docs/
│       ├── Cycle_Count_Procedure.md
│       ├── Equipment_Troubleshooting.md
│       ├── Replenishment_Policy.md
│       └── Warehouse_Operations_Handbook.md
│
├── MCP_ARCHITECTURE.md          # Technical documentation (project root)
│
├── 💻 SOURCE CODE
│   └── src/
│       ├── __init__.py
│       │
│       ├── config/                  # Configuration
│       │   ├── __init__.py
│       │   └── settings.py          # Centralized settings
│       │
│       ├── agents/                  # AI Agents
│       │   ├── __init__.py
│       │   ├── router.py            # Main routing logic
│       │   ├── sql_agent.py         # Database query agent
│       │   └── rag_agent.py         # Document retrieval agent
│       │
│       ├── rag/                     # RAG Pipeline
│       │   ├── __init__.py
│       │   ├── document_loader.py   # Markdown chunking
│       │   └── vector_store.py      # Embedding & search
│       │
│       └── tools/                   # MCP Tools
│           ├── __init__.py
│           └── warehouse_mcp.py     # FastMCP server
│
├── 📦 COURSE MATERIALS
│   └── Jan-2026-AI/
│       └── Unit-1-Foundations of GenAI/  # Reference materials
│
└── 🔨 BUILD ARTIFACTS
    ├── __pycache__/                # Python bytecode
    ├── .venv/                       # Virtual environment
    └── templates/                   # Web templates
```

### Module Organization Strategy

**Why this structure?**

1. **Separation of Concerns**
   - `src/` contains all application code
   - `data/` for databases
   - `docs/` for knowledge base
   - Entry points at root for easy access

2. **Modular Design**
   - Each module has single responsibility
   - Easy to test components independently
   - Can swap implementations (e.g., different vector stores)

3. **Professional Standards**
   - Follows Python packaging best practices
   - Uses `pyproject.toml` instead of legacy `setup.py`
   - All modules have `__init__.py` for proper imports

4. **Scalability**
   - Easy to add new agents
   - Easy to add new MCP tools
   - Easy to add new data sources

---

## 🎮 Entry Points & How to Use

### 1. Web UI (Recommended for Presentations)

**Launch:**
```bash
# Method 1: Direct command
uv run streamlit run web_app.py

# Method 2: Batch file (Windows)
start_web.bat
```

**Access:**  
Open browser to: http://localhost:8501

**Features:**
- ✨ Interactive chat interface with history
- 🎨 Color-coded agent badges:
  - 🔵 **Blue** = SQL Agent
  - 🟢 **Green** = RAG Agent
  - 🟠 **Orange** = Both Agents
- 📋 Example questions in sidebar
- 🧹 Clear conversation button
- 💬 Maintains full conversation context

**Best For:**
- Capstone presentations/demos
- Showcasing multi-agent routing visually
- Non-technical users

**Code Entry Point:**
```python
# web_app.py
import streamlit as st
from src.agents.router import create_router

router = await create_router()  # Initializes all agents
response = await router.chat(user_input)  # Routes & executes
```

---

### 2. CLI (Command Line Interface)

**Launch:**
```bash
# Method 1: Direct command
uv run python main.py

# Method 2: Batch file (Windows)
start_cli.bat
```

**Features:**
- 💻 Terminal-based interaction
- ⚡ Fast and lightweight
- 📋 Type `help` for example questions
- 🚪 Type `exit` or `quit` to close

**Best For:**
- Quick testing during development
- Demonstrating both interfaces
- Scripting/automation
- SSH/remote environments

**Code Entry Point:**
```python
# main.py
from src.agents.router import create_router

router = await create_router()  # Initialize
response = await router.chat(question)  # Query
```

---

### 3. Standalone MCP Server

**Launch:**
```bash
uv run python run_mcp_server.py
```

**Purpose:**
- Run MCP server independently
- Test tools without full agent system
- Debugging database queries

**Entry Point:**
```python
# run_mcp_server.py
from src.tools.warehouse_mcp import mcp_server

mcp_server.run()  # Starts FastMCP server
```

---

### 4. Quick Start / Minimal Example

**File:** `QUICK_START.py`

**Purpose:**  
Simplified example showing core concepts without all the production features.

```python
# Minimal usage example
from src.agents.router import create_router

async def main():
    router = await create_router()
    answer = await router.chat("What orders are delayed?")
    print(answer)
```

---

### Installation & Setup

**First Time Setup:**
```bash
# 1. Clone/download project
cd warehouse-ai-assistant

# 2. Install dependencies
uv sync

# 3. Create .env file with API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 4. Generate database
uv run python generate_data.py

# 5. Launch!
uv run streamlit run web_app.py
```

**Requirements:**
- Python 3.13+
- OpenAI API key
- ~50 MB disk space (including dependencies)

---

## 🧩 Key Modules & Components

### 1. Router (`src/agents/router.py`)

**Purpose:** Main orchestration layer - decides which agent(s) to invoke

**Key Class:** `WarehouseRouter`

**Responsibilities:**
```python
class WarehouseRouter:
    def classify_question(self, question: str) -> AgentType:
        """Uses LLM to determine: SQL | RAG | BOTH"""
        
    async def chat(self, question: str) -> str:
        """Main entry point - routes and executes"""
        
    async def handle_both_agents(self, question: str) -> str:
        """Calls SQL → RAG → Synthesizes results"""
```

**Classification Prompt:**
```python
system_prompt = """
You are a question classifier for a warehouse AI assistant.

Classify into:
- SQL: Database queries (orders, inventory, metrics)
- RAG: Procedural questions (how-to, troubleshooting)
- BOTH: Requires data + procedures
"""
```

**LLM Configuration:**
- Model: `gpt-4o-mini`
- Temperature: `0.3` (slightly creative but mostly deterministic)
- Token management: Limits history to last 20 messages

---

### 2. SQL Agent (`src/agents/sql_agent.py`)

**Purpose:** Query warehouse database via MCP tools

**Key Function:** `create_sql_agent()`

**Architecture:**
```python
# LangChain agent with MCP tools
agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=mcp_tools,  # 6 database tools
    state_modifier=truncate_messages  # Token management
)
```

**Available Tools:**
1. `search_orders` - Find orders by criteria
2. `get_order_details` - Full order information
3. `check_inventory` - Stock levels & locations
4. `get_shipment_status` - Tracking & delivery info
5. `get_exceptions` - Operational issues
6. `get_labor_metrics` - Employee productivity

**Tool Calling Flow:**
```
User: "What orders are delayed?"
  ↓
SQL Agent thinks: "Need to search orders with delayed status"
  ↓
Calls: search_orders(status="DELAYED")
  ↓
MCP Server queries: SELECT * FROM orders WHERE status = 'DELAYED'
  ↓
Returns: List of orders
  ↓
Agent formats: "There are 50 delayed orders: ..."
```

**Why Temperature=0:**
- Database queries need consistency
- Same question should give same data
- No creativity needed for factual queries

---

### 3. RAG Agent (`src/agents/rag_agent.py`)

**Purpose:** Search documentation and procedures

**Key Function:** `create_rag_agent()`

**Architecture:**
```python
# LangChain agent with document search tool
agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[search_tool],  # Vector search
    state_modifier=truncate_messages
)
```

**Document Search Tool:**
```python
@tool
async def search_documents(query: str) -> str:
    """Semantic search across warehouse documentation"""
    # 1. Embed query
    # 2. Search vector store
    # 3. Return top 3 chunks with sources
```

**Source Citation:**
- Always includes document name
- Includes section headers
- Relevance scores shown

**Example Output:**
```
**Result 1** (Relevance: 0.89, Source: Equipment_Troubleshooting.md)
## RF Scanner Issues
Section: Common Problems and Solutions
...

**Result 2** (Relevance: 0.82, Source: Warehouse_Operations_Handbook.md)
## Equipment Maintenance
...
```

---

### 4. Weather Agent (`src/agents/weather_agent.py`)

**Purpose:** Search web for external information affecting operations

**Key Function:** `create_weather_agent()`

**Architecture:**
```python
# LangChain agent with Tavily web search tool
agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    tools=[tavily_search_tool],  # Web search
    state_modifier=SystemMessage(content=weather_prompt)
)
```

**Tavily Search Tool:**
```python
@tool
def search_web(query: str) -> str:
    """Search the web for current information"""
    results = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True  # Get AI summary
    )
    # Returns formatted results with sources
```

**Use Cases:**
- "What's the weather in Chicago today?" → Current weather conditions
- "Are there FedEx delays this week?" → Carrier service alerts
- "Why might California deliveries be delayed?" → Regional news/events

**Source Citation:**
- Includes Tavily AI summary
- Top 3 web search results with URLs
- Clear attribution to external sources

**Example Output:**
```
**Summary:** Heavy snowstorm hitting Chicago area causing transportation delays

**Sources:**
1. **Winter Storm Disrupts Logistics in Midwest**
   Heavy snow and ice affecting highway travel...
   Source: https://news.example.com/weather/...

2. **FedEx Issues Service Alert for IL Region**
   Delays expected through March 31...
   Source: https://fedex.com/alerts/...
```

---

### 5. MCP Server (`src/tools/warehouse_mcp.py`)

**Purpose:** Expose database as LLM-callable tools

**Framework:** FastMCP (simplified MCP server implementation)

**Architecture:**
```python
mcp_server = FastMCP("Warehouse Operations")

@mcp_server.tool()
async def search_orders(
    status: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """Search orders with filters"""
    db = ctx.deps  # Injected database connection
    # Execute parameterized query
    # Return results as dict
```

**Database Connection Management:**
```python
@asynccontextmanager
async def lifespan():
    """Manages database lifecycle"""
    db = WarehouseDB(settings.DB_PATH)
    db.connect()
    yield db  # Injected into tool context
    db.close()
```

**Security Features:**
- ✅ Read-only queries (no DELETE/UPDATE)
- ✅ Parameterized queries (SQL injection protection)
- ✅ Connection pooling (via lifespan)

**All 6 Tools:**
1. `search_orders` - Flexible order search
2. `get_order_details` - Single order with line items
3. `check_inventory` - Stock queries
4. `get_shipment_status` - Tracking info
5. `get_exceptions` - Issue reporting
6. `get_labor_metrics` - Productivity data

---

### 5. Document Loader (`src/rag/document_loader.py`)

**Purpose:** Load and chunk markdown documentation

**Strategy:** Two-tier chunking

**Tier 1: Header-based splitting**
```python
header_splitter = MarkdownHeaderTextSplitter([
    ("#", "Header1"),
    ("##", "Header2"),
])
# Preserves document structure
```

**Tier 2: Recursive text splitting**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
# Handles large sections
```

**Result:** 46 chunks across 5 documents

**Why This Approach:**
- Preserves semantic boundaries (headers)
- Maintains context with overlap
- Optimal chunk size for embeddings (1000 chars)

---

### 6. Vector Store (`src/rag/vector_store.py`)

**Purpose:** Semantic search over documentation

**Implementation:** LangChain `InMemoryVectorStore`

**Embedding Model:** `text-embedding-3-small`

**Setup:**
```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(chunks)  # 46 chunks
```

**Search:**
```python
results = vector_store.similarity_search_with_score(
    query=question,
    k=3  # Top 3 most relevant chunks
)
```

**Why InMemoryVectorStore:**
- Fast (no disk I/O)
- Simple (no external dependencies)
- Sufficient for ~50 documents
- Can upgrade to Chroma/Pinecone for production

---

### 7. Configuration (`src/config/settings.py`)

**Purpose:** Centralized settings management

**Key Settings:**
```python
class Settings:
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DB_PATH = BASE_DIR / "data" / "warehouse.db"
    DOCS_DIR = BASE_DIR / "docs"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    # RAG Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_RESULTS = 3
```

**Benefits:**
- Single source of truth
- Easy to modify settings
- Environment variable support
- Type safety with proper imports

---

### Module Import Flow

```
main.py / web_app.py
    ↓
src/agents/router.py
    ↓
    ├─→ src/agents/sql_agent.py
    │       ↓
    │   src/tools/warehouse_mcp.py
    │       ↓
    │   src/config/settings.py
    │
    └─→ src/agents/rag_agent.py
            ↓
        src/rag/vector_store.py
            ↓
        src/rag/document_loader.py
            ↓
        src/config/settings.py
```

---

## 🎓 Course Integration

### What Course Concepts Are Used

This capstone project builds on concepts from multiple units:

#### **Unit 4: RAG (Retrieval Augmented Generation)**

**Concepts Used:**
- ✅ Document chunking strategies
- ✅ Embeddings for semantic search
- ✅ Vector stores
- ✅ Retrieval-based question answering

**Our Implementation:**
```python
# From Unit 4 lessons
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore

# Two-tier chunking (Unit 4 best practice)
header_splitter = MarkdownHeaderTextSplitter(...)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Unit 4 recommendation
    chunk_overlap=200,    # Maintains context
)
```

**Files:**
- `src/rag/document_loader.py` - Chunking pipeline
- `src/rag/vector_store.py` - Embedding & search
- `src/agents/rag_agent.py` - RAG agent implementation

---

#### **Unit 6: MCP (Model Context Protocol) & Function Calling**

**Concepts Used:**
- ✅ FastMCP server implementation
- ✅ Tool/function definitions for LLMs
- ✅ Structured outputs
- ✅ Context management (lifespan pattern)

**Our Implementation:**
```python
# From Unit 6 patterns
from mcp.server.fastmcp import FastMCP, Context

# Lifespan context manager (Unit 6 best practice)
@asynccontextmanager
async def lifespan():
    db = WarehouseDB(settings.DB_PATH)
    db.connect()
    yield db  # Dependency injection
    db.close()

# Tool definitions (Unit 6 pattern)
@mcp_server.tool()
async def search_orders(
    status: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """LLM can call this to search orders"""
    db = ctx.deps
    return query_results
```

**Files:**
- `src/tools/warehouse_mcp.py` - MCP server with 6 tools
- `run_mcp_server.py` - Standalone server runner

---

#### **Unit 7: Agentic AI & LangGraph**

**Concepts Used:**
- ✅ ReAct (Reasoning + Acting) agent pattern
- ✅ Multi-agent systems
- ✅ Agent routing and orchestration
- ✅ Tool calling with LangChain
- ✅ Message history management
- ✅ Token truncation strategies

**Our Implementation:**
```python
# From Unit 7 lessons
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# ReAct agent (Unit 7 pattern)
agent = create_react_agent(
    llm=llm,
    tools=tools,
    state_modifier=truncate_messages  # Token management
)

# Multi-agent orchestration (Unit 7 concept)
class WarehouseRouter:
    def __init__(self):
        self.sql_agent = create_sql_agent()
        self.rag_agent = create_rag_agent()
        self.classifier_llm = ChatOpenAI(...)
```

**Files:**
- `src/agents/router.py` - Multi-agent orchestration
- `src/agents/sql_agent.py` - ReAct SQL agent
- `src/agents/rag_agent.py` - ReAct RAG agent

---

#### **Additional Technologies from Course**

| Technology | Unit | Usage in Project |
|------------|------|------------------|
| **Tavily** | Unit 7 | ✅ USED - Web search for weather and transportation news affecting shipments |
| **LangSmith** | Unit 7 | Available for debugging (optional) |
| **ChromaDB** | Unit 4 | NOT USED - We use InMemoryVectorStore for simplicity |
| **Prompt Engineering** | Units 2-3 | Extensively used in all agent prompts |

---

### Key Differences from Course Examples

While building on course foundations, this project includes unique elements:

1. **Real-World Dataset**
   - Course: Often uses simple CSV files
   - Us: Complex 9-table relational database with 10,000 orders

2. **Production-Ready Structure**
   - Course: Single-file examples
   - Us: Modular `src/` structure with proper packaging

3. **Two Interfaces**
   - Course: Usually CLI only
   - Us: Professional Streamlit web UI + CLI

4. **Domain-Specific**
   - Course: Generic chatbot examples
   - Us: Specialized warehouse operations system

5. **Advanced Routing**
   - Course: Single-agent systems
   - Us: Intelligent multi-agent routing with synthesis

---

## 🚀 Real-World Potential

### Current Capabilities (Demo-Ready Today)

✅ **Functional System**
- Answers complex warehouse questions
- Routes intelligently between data and documentation
- Maintains conversation context
- Professional web interface

✅ **Realistic Data**
- 10,000 orders
- 2,000 inventory items
- Time-series labor metrics
- Interconnected relationships

✅ **Production Patterns**
- Modular architecture
- Error handling
- Security (read-only, parameterized queries)
- Token management

---

### Path to Production Use

#### **Phase 1: Immediate Augmentation (Weeks)**

**What to Add:**
1. **Authentication & Authorization**
   ```python
   # Add user roles: viewer, operator, manager
   # Implement JWT or OAuth
   ```

2. **Persistent Vector Store**
   ```python
   # Replace InMemoryVectorStore with ChromaDB or Pinecone
   # Allows document updates without restart
   ```

3. **Write Operations**
   ```python
   # Add MCP tools for:
   # - Create exceptions
   # - Update order status
   # - Adjust inventory
   ```

4. **Audit Logging**
   ```python
   # Log all queries and actions
   # Track who asked what, when
   ```

**Estimated Effort:** 2-3 weeks for experienced developer

---

#### **Phase 2: Enterprise Features (Months)**

**What to Add:**
1. **Multi-Warehouse Support**
   - User permissions per warehouse
   - Cross-warehouse analytics

2. **Real-Time Data Integration**
   - Connect to live WMS (Warehouse Management System)
   - Sync with ERP systems
   - API integrations

3. **Advanced Analytics**
   - Predictive inventory forecasting
   - Labor optimization recommendations
   - Exception trend analysis

4. **Mobile Interface**
   - React Native or Progressive Web App
   - Barcode scanning integration
   - Voice commands for hands-free operation

5. **Notification System**
   - Slack/Teams integration
   - Email alerts for critical issues
   - Proactive recommendations

**Estimated Effort:** 3-6 months with small team

---

#### **Phase 3: AI Enhancements (Future)**

**What to Add:**
1. **Fine-Tuned Models**
   - Train custom model on company-specific terminology
   - Optimize for warehouse domain

2. **Multi-Modal AI**
   - Image recognition for damaged goods
   - Computer vision for inventory counts
   - OCR for document processing

3. **Autonomous Actions**
   - Auto-create replenishment orders
   - Auto-assign tasks to workers
   - Auto-escalate critical issues

4. **Advanced Reasoning**
   - Root cause analysis for problems
   - What-if scenario planning
   - Optimization suggestions

---

### Real Warehouse Use Cases

#### **1. Operations Floor**
**User:** Warehouse Associate  
**Scenario:** Mid-shift, handling exceptions

```
Associate: "Scanner isn't working in Zone B"
AI: "This is a known issue. According to Equipment Troubleshooting:
     1. Check battery connection
     2. Restart device
     3. If not resolved, use backup scanner from IT desk
     
     I've logged this exception. There are 2 backup scanners available."
```

**Value:**
- Instant troubleshooting (no need to find supervisor)
- Automatic exception logging
- Equipment availability lookup

---

#### **2. Customer Service**
**User:** Customer Service Rep  
**Scenario:** Customer calling about order

```
Rep: "What's the status of order ORD-102459?"
AI: "Order ORD-102459 for Smith Company:
    - Status: DELAYED
    - Expected: May 15 → Revised: May 18
    - Issue: Out of stock on item SKU-1234
    - Current location: Awaiting replenishment
    
    According to escalation policy, customer was notified 
    of 3+ day delays automatically."
```

**Value:**
- Single query gets full order context
- No need to check multiple systems
- Policy compliance verification

---

#### **3. Management Reporting**
**User:** Operations Manager  
**Scenario:** Morning briefing prep

```
Manager: "Show me yesterday's labor productivity and any concerning trends"
AI: "Labor metrics for Dec 15:
    - Average picks/hour: 145 (↓ from 162 previous week)
    - Top performer: John Doe (198 picks/hour)
    - Lowest: Zone C (121 picks/hour)
    
    Concerning: Zone C has had 3 scanner exceptions and 2 
    conveyor jams in the past week, likely affecting productivity.
    
    Recommend: Equipment maintenance review for Zone C."
```

**Value:**
- Combines data from multiple tables
- Surfaces correlations (performance ↔ equipment issues)
- Actionable recommendations

---

#### **4. Training New Employees**
**User:** New Hire  
**Scenario:** First week on the job

```
New Hire: "How do I perform a cycle count?"
AI: "According to the Cycle Count Procedure:
    
    Step 1: Access cycle count list on RF scanner
    Step 2: Navigate to assigned location
    Step 3: Count all items in location
    Step 4: Enter count into scanner
    Step 5: System will flag discrepancies
    
    [Full procedure with screenshots]
    
    Note: You currently have 5 cycle count tasks assigned. 
    Would you like me to list them?"
```

**Value:**
- Self-service learning
- Reduces trainer burden
- Links procedures to actual work

---

### ROI (Return on Investment) Potential

**Cost Savings:**
- ⏱️ **Time Savings**: 5-10 minutes per query → seconds
- 📞 **Reduced Escalations**: Self-service reduces supervisor interruptions
- 📚 **Training Costs**: Faster onboarding, less hands-on training needed
- ❌ **Error Reduction**: AI provides consistent, accurate information

**Productivity Gains:**
- 🚀 **Faster Problem Resolution**: Instant access to troubleshooting
- 📊 **Better Decision Making**: Data-driven insights readily available
- 🔄 **Process Optimization**: AI identifies inefficiencies

**Estimated Financial Impact:**
- Warehouse with 50 employees
- 20 queries per employee per day
- 5 minutes saved per query
- = 83 hours saved per day
- = ~$2,500/day labor savings (at $30/hour)
- = **$650K/year potential savings**

---

### Competitive Advantage

**Current Warehouse Management Systems:**
- Complex interfaces requiring extensive training
- Require knowing which system/report to check
- Data siloed across multiple applications
- Documentation scattered across SharePoint, PDFs, etc.

**Our AI Assistant Advantage:**
- Natural language interface (no training needed)
- Single point of access for all information
- Combines data + procedures automatically
- Available 24/7 without human bottlenecks

**Market Opportunity:**
- Multi-billion dollar warehouse automation market
- Growing demand for AI in logistics
- Can be packaged as:
  - Standalone SaaS product
  - Add-on to existing WMS platforms
  - Custom enterprise solutions

---

## 📊 Demo & Testing

### Recommended Demo Flow for Presentation

#### **1. Introduction (2 minutes)**
- Show project overview slide
- Explain the problem we're solving
- Preview the two interfaces

#### **2. Web Interface Demo (5 minutes)**

**Launch:**
```bash
start_web.bat
```

**Demo Script:**

1. **Simple SQL Query**
   ```
   Type: "What orders are delayed?"
   Show: Blue badge (SQL Agent), structured data response
   Point out: Agent selected MCP tool automatically
   ```

2. **Simple RAG Query**
   ```
   Type: "How do I troubleshoot a broken RF scanner?"
   Show: Green badge (RAG Agent), procedure with source citations
   Point out: Document name and section referenced
   ```

3. **Complex Both Query**
   ```
   Type: "Show me critical inventory items and explain the replenishment policy"
   Show: Orange badge (Both), combined data + procedure
   Point out: Synthesis of SQL results + RAG document
   ```

4. **Conversation Context**
   ```
   Type: "What about for shoes specifically?"
   Show: Maintains context from previous question
   Point out: Conversation history working
   ```

#### **3. CLI Demo (2 minutes)**

**Launch:**
```bash
start_cli.bat
```

**Demo Script:**
```
> help
[Shows example questions organized by agent type]

> What exceptions are open?
[Quick response in terminal]

> exit
```

**Point out:** Same functionality, different interface

#### **4. Architecture Explanation (3 minutes)**

**Show diagram from this presentation:**
- Point to Router/Classifier
- Explain multi-agent routing
- Show MCP server connection
- Show vector store for RAG

**Key Points:**
- "This is a multi-agent system, not a single chatbot"
- "LLM decides which specialized agent to use"
- "Can combine results from multiple sources"

#### **5. Code Walkthrough (3 minutes)**

**Show key files:**

1. **Entry Point** - `main.py` or `web_app.py`
   ```python
   router = await create_router()
   response = await router.chat(question)
   ```

2. **Router** - `src/agents/router.py`
   ```python
   classification = self.classify_question(question)
   if classification == AgentType.SQL:
       return await self.sql_agent.execute(question)
   ```

3. **MCP Tools** - `src/tools/warehouse_mcp.py`
   ```python
   @mcp_server.tool()
   async def search_orders(...):
       # Database query
       return results
   ```

**Point out:**
- Clean, modular structure
- each component has single responsibility
- Professional code quality

#### **6. Data Generation (2 minutes)**

**Show:**
```bash
python generate_data.py
```

**Point out:**
- Uses Faker for realistic data
- 10,000 orders, 2,000 items
- Interconnected tables
- Real-world scenarios

#### **7. Conclusion (2 minutes)**

**Recap:**
- ✅ Solved real warehouse problem
- ✅ Used 4+ course concepts (RAG, MCP, Agents, LangGraph)
- ✅ Production-quality code structure
- ✅ Two functional interfaces
- ✅ Realistic data
- ✅ Ready for real-world augmentation

**Q&A**

---

### Test Scenarios

#### **SQL Agent Tests**

| Question | Expected Agent | Expected Result |
|----------|---------------|-----------------|
| "What orders are delayed?" | SQL | List of delayed orders with details |
| "Show me critical inventory" | SQL | Items below reorder point |
| "What exceptions are open?" | SQL | Active exceptions with types |
| "Status of order ORD-102459?" | SQL | Full order details |
| "Productivity last 7 days?" | SQL | Labor metrics summary |

#### **RAG Agent Tests**

| Question | Expected Agent | Expected Result |
|----------|---------------|-----------------|
| "How do I fix a broken scanner?" | RAG | Troubleshooting steps with source |
| "What is the cycle count procedure?" | RAG | Step-by-step procedure |
| "Replenishment rules?" | RAG | Policy explanation with source |
| "How to handle damaged goods?" | RAG | Process guidelines |
| "Conveyor jam troubleshooting?" | RAG | Equipment troubleshooting steps |

#### **Both Agents Tests**

| Question | Expected Agent | Expected Result |
|----------|---------------|-----------------|
| "Why is order ORD-102459 delayed and what's the procedure?" | BOTH | Order data + escalation policy |
| "Show critical inventory and replenishment policy" | BOTH | Inventory data + policy |
| "Open exceptions and how to handle?" | BOTH | Exception data + troubleshooting |

#### **Conversation Context Tests**

```
1. User: "What orders are delayed?"
   AI: [Lists delayed orders]

2. User: "How many?"
   AI: [Should understand "how many delayed orders"]

3. User: "What about critical inventory?"
   AI: [New topic, should switch context]

4. User: "Why?"
   AI: [Should reference "why inventory is critical"]
```

---

### Known Limitations (To Discuss if Asked)

**Current Limitations:**
1. **No Persistence**: Vector store loads each time (fixable with ChromaDB)
2. **Read-Only**: No write operations (by design for safety)
3. **Static Data**: Database doesn't update live (demo limitation)
4. **No Authentication**: Open access (production would need auth)
5. **Limited Docs**: Only 5 documents (easily expandable)

**Why These Are Acceptable for Capstone:**
- Demonstrate core concepts without overengineering
- Show understanding of production considerations
- Easy to explain enhancement path
- Focus on AI/ML aspects, not enterprise IT

**Production Roadmap Addresses:**
- Persistent vector store: Week 1
- Write operations: Week 2-3
- Authentication: Week 2
- Real-time data: Phase 2

---

### Troubleshooting During Demo

**If Something Goes Wrong:**

1. **"API Key Error"**
   - Have backup `.env` file ready
   - "This is just authentication, the code is solid"

2. **"Module Not Found"**
   - `uv sync` before presentation
   - Have requirements pre-installed

3. **"Database Not Found"**
   - Run `generate_data.py` beforehand
   - Keep backup `warehouse.db` file

4. **"Slow Response"**
   - "Normal - calling OpenAI API"
   - "Production would use caching"

5. **"Wrong Agent Selected"**
   - "This is an interesting edge case"
   - "Shows LLM decision-making"
   - "Could refine classifier prompt"

---

## 📈 Presentation Tips

### Storytelling Approach

**Start with the Problem:**
"Imagine you're a warehouse associate. Your scanner breaks. Do you:
- Stop working and find your supervisor?
- Dig through a 50-page manual?
- Call IT and wait 20 minutes?

What if you could just ask an AI: 'Scanner broken, what do I do?' and get instant, accurate guidance?"

**Show the Solution:**
[Demo the exact scenario above]

**Explain the Technology:**
"Here's how this works under the hood..."

**Discuss Real-World Impact:**
"This could save a 50-person warehouse $650K per year..."

---

### Key Messages to Emphasize

1. **Multi-Agent = Specialized Intelligence**
   - "Not just one chatbot trying to do everything"
   - "Specialized agents optimized for their task"
   - "Like having a data analyst AND a documentation expert"

2. **Course Integration**
   - "Built on 4 course units: RAG, MCP, Agents, LangGraph"
   - "Not just theory - production-quality implementation"

3. **Real Data = Real Insights**
   - "10,000 orders, not a toy dataset"
   - "Faker library for realistic data"
   - "Could swap in real warehouse DB tomorrow"

4. **Production-Ready Architecture**
   - "Modular structure, not a single script"
   - "Follows industry best practices"
   - "Clear path to production use"

5. **Dual Interface**
   - "Built two UIs to show flexibility"
   - "Web for presentations, CLI for devs"
   - "Same backend powers both"

---

### Time Management (20-minute presentation)

| Section | Time | Key Points |
|---------|------|------------|
| **Introduction** | 2 min | Problem statement, why this matters |
| **Solution Overview** | 2 min | What we built, key features |
| **Live Demo - Web UI** | 5 min | Show all three agent types |
| **Architecture** | 3 min | Diagram, explain multi-agent flow |
| **Technology Stack** | 2 min | Tools used, course integration |
| **Code Walkthrough** | 3 min | Show key modules, entry points |
| **Real-World Potential** | 2 min | Production path, ROI |
| **Conclusion** | 1 min | Recap, invite questions |

---

### Backup Slides (If Time Allows)

Prepare extra slides on:
- Detailed database schema
- RAG chunking strategy
- Token management approach
- Security considerations
- Testing methodology
- Alternative approaches considered

---

## 🎯 Summary

### What We Accomplished

✅ **Solved a Real Problem**
- Warehouse operations face information silos
- Built AI assistant that unifies data + documentation

✅ **Applied Advanced AI Techniques**
- Multi-agent system with intelligent routing
- RAG for document retrieval
- MCP for tool calling
- LangGraph for orchestration

✅ **Professional Implementation**
- Modular, production-quality code structure
- Realistic data generation (10,000 orders)
- Two functional interfaces
- Clear documentation

✅ **Course Integration**
- RAG (Unit 4): Chunking, embeddings, vector search
- MCP (Unit 6): FastMCP server, 6 database tools
- Agents (Unit 7): ReAct pattern, multi-agent routing

✅ **Real-World Ready**
- Clear path to production use
- Estimated $650K/year potential ROI
- Can be augmented for actual deployment

---

### Key Takeaways for Evaluators

1. **Complexity**: This is not a simple chatbot - it's a sophisticated multi-agent system
2. **Integration**: Demonstrates mastery of 4+ course concepts working together
3. **Quality**: Production-ready code structure, not throwaway project code
4. **Innovation**: Smart routing + synthesis goes beyond basic examples
5. **Practicality**: Built with real-world deployment in mind

---

### Project Metrics

| Metric | Value |
|--------|-------|
| **Code** | |
| Lines of Python | ~1,500 |
| Modules | 8 |
| Entry Points | 4 (CLI, Web, MCP, QuickStart) |
| **Data** | |
| Database Size | 3.18 MB |
| Total Records | ~23,000 |
| Orders | 10,000 |
| **AI** | |
| Agents | 3 (Router, SQL, RAG) |
| MCP Tools | 6 |
| Document Chunks | 46 |
| **Documentation** | |
| Markdown Files | 10+ |
| Documentation Pages | ~50 pages |

---

## 📞 Contact & Next Steps

### Project Repository
- **Location**: `e:\Projects\warehouse-ai-assistant`
- **Documentation**: See README.md, PROGRESS_SUMMARY.md, HOW_TO_LAUNCH.md

### How to Learn More
1. **Try It**: Run `start_web.bat`
2. **Read Code**: Start with `main.py` and `src/agents/router.py`
3. **Explore Docs**: Check `docs/` folder for warehouse procedures
4. **Generate Data**: Run `python generate_data.py` to see data generation

### Future Enhancements
Interested in contributing or deploying? See "Real-World Potential" section above.

---

**Thank you!**

---

## Appendix: Quick Reference Commands

```bash
# Installation
uv sync

# Generate Database
uv run python generate_data.py

# Launch Web UI
uv run streamlit run web_app.py

# Launch CLI
uv run python main.py

# Test MCP Server
uv run python test_mcp_server.py

# Run MCP Server Standalone
uv run python run_mcp_server.py
```

---

*Document Created: March 31, 2026*  
*Project: Warehouse AI Assistant Capstone*  
*Author: Generated for presentation purposes*
