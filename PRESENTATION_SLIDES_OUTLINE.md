# Warehouse AI Assistant - Presentation Slides Outline
## Ready-to-Convert PowerPoint Structure

---

## Slide 1: Title Slide
**Title:** Warehouse AI Assistant  
**Subtitle:** An Intelligent Multi-Agent System for Operations Management  
**Your Name**  
**Date:** March 31, 2026  
**Course:** AI Capstone Project

---

## Slide 2: The Problem
**Title:** The Challenge in Modern Warehouses

**Content:**
- 📊 **Data Silos**: Database queries vs. Document searches
- ⏱️ **Time-Consuming**: Multiple systems to check
- 🆕 **Training Gap**: New employees need quick answers
- ⏰ **24/7 Operations**: Immediate answers needed

**Visual:** Icon grid showing scattered information sources

**Speaker Notes:**
- Staff waste 5-10 minutes per query across multiple systems
- New hires need weeks of training
- Night shift has limited supervisor support

---

## Slide 3: Real-World Example
**Title:** A Common Scenario

**Content:**
```
Warehouse Associate: "Scanner broke in Zone B"

Current Process:
1. Stop working ❌
2. Find supervisor (5-10 min) ❌
3. Look through manual ❌
4. Call IT (wait time) ❌

With AI Assistant:
1. Ask AI ✅
2. Get instant answer ✅
3. Back to work ✅
```

**Visual:** Before/After comparison diagram

---

## Slide 4: Our Solution
**Title:** Intelligent Multi-Agent AI System

**Content:**
✅ **Automatic Routing** - Questions go to the right expert  
✅ **Database Queries** - Live operational data  
✅ **Document Search** - Procedures & policies  
✅ **Information Synthesis** - Combined insights  
✅ **Two Interfaces** - Web UI + CLI

**Visual:** System overview diagram with icons

---

## Slide 5: Architecture Overview
**Title:** How It Works

**Visual:** 
```
User Question
      ↓
[Router/Classifier]
      ↓
   ┌──┴──┐──────┐
   ↓     ↓      ↓
  SQL   RAG   BOTH
   ↓     ↓      ↓
Database Docs Combined
```

**Key Points:**
- LLM-based intelligent routing
- Specialized agents for specific tasks
- Can combine multiple sources

---

## Slide 6: Technology Stack
**Title:** Technologies & Tools Used

### Core Technologies
- **Python 3.13** - Modern async/await
- **OpenAI GPT-4o-mini** - LLM reasoning
- **SQLite** - Warehouse database
- **Faker** - Realistic data generation

### AI Frameworks  
- **LangChain** - Agent orchestration
- **LangGraph** - Multi-agent workflows
- **FastMCP** - Tool calling protocol
- **Tavily** - Web search for weather/news

### Interfaces
- **Streamlit** - Professional web UI
- **asyncio** - CLI interface

**Visual:** Tech stack icons arranged in layers

---

## Slide 7: Course Integration
**Title:** Building on Course Foundations

| Unit | Concept | Our Implementation |
|------|---------|-------------------|
| **Unit 4** | RAG | 2-tier chunking, vector search, 46 chunks |
| **Unit 6** | MCP | FastMCP server, 6 database tools |
| **Unit 7** | Agents | ReAct pattern, multi-agent routing |
| **Unit 7** | LangGraph | Workflow orchestration |
| **Unit 7** | Tavily | Weather/news search for shipment context |

**Key Message:** Not just theory - production implementation

---

## Slide 8: Project Structure
**Title:** Professional Code Organization

```
warehouse-ai-assistant/
├── src/                    # Application code
│   ├── agents/            # SQL, RAG, Router
│   ├── tools/             # MCP server
│   ├── rag/               # Vector store
│   └── config/            # Settings
├── data/                   # Database (3.18 MB)
├── docs/                   # 5 SOPs (46 chunks)
├── main.py                 # CLI entry point
└── web_app.py             # Web UI entry point
```

**Key Points:**
- Modular design
- Separation of concerns
- Easily extensible

---

## Slide 9: Data Generation
**Title:** Realistic Warehouse Data

### Generated with Faker Library
- 🏢 **3 Warehouses** with 4,000 locations
- 📦 **10,000 Orders** with realistic patterns
- 📊 **2,000 SKUs** (Apparel, Electronics, etc.)
- 🚚 **10,000 Shipments** with tracking
- ⚠️ **500 Exceptions** (operational issues)
- 📈 **Labor Metrics** (time-series productivity)

**Total Database Size:** 3.18 MB  
**Total Records:** ~23,000

**Visual:** Database schema diagram

**Key Message:** Production-quality data, not toy examples

---

## Slide 10: Entry Points
**Title:** Two Ways to Interact

### Web Interface (Streamlit)
```bash
start_web.bat
→ http://localhost:8501
```
✨ Visual, color-coded agents  
📋 Example questions  
💬 Conversation history  

### Command Line Interface
```bash
start_cli.bat
→ Terminal interaction
```
⚡ Fast and lightweight  
🖥️ Works anywhere  
🔧 Scriptable  

**Visual:** Side-by-side screenshots

---

## Slide 11: SQL Agent
**Title:** Database Query Agent

**Purpose:** Query structured warehouse data

### 6 MCP Tools Available:
1. `search_orders` - Find orders by criteria
2. `get_order_details` - Full order info
3. `check_inventory` - Stock levels
4. `get_shipment_status` - Tracking info
5. `get_exceptions` - Operational issues
6. `get_labor_metrics` - Productivity data

**Example:**  
User: *"What orders are delayed?"*  
→ SQL Agent → MCP Tool → Database → Structured Answer

**Visual:** Flow diagram with example

---

## Slide 12: RAG Agent
**Title:** Document Retrieval Agent

**Purpose:** Search procedures and policies

### Document Processing:
- **5 Markdown Files** (SOPs, troubleshooting, policies)
- **2-Tier Chunking** (header-based + recursive)
- **46 Semantic Chunks** with embeddings
- **text-embedding-3-small** for search

**Example:**  
User: *"How do I fix a broken scanner?"*  
→ RAG Agent → Vector Search → Procedure + Source Citation

**Visual:** RAG pipeline diagram

---

## Slide 13: Router & Synthesis
**Title:** Intelligent Orchestration

### Classification
LLM determines: **SQL | RAG | BOTH**

### Synthesis (when BOTH)
1. Execute SQL Agent → Get data
2. Execute RAG Agent → Get procedures
3. Synthesis LLM → Combine into coherent answer

**Example:**  
*"Show critical inventory and explain replenishment policy"*
- SQL: Gets inventory data
- RAG: Gets policy document
- Synthesizer: Creates combined answer

**Visual:** Flow diagram showing synthesis

---

## Slide 14: Key Modules
**Title:** Core Components

### 1. Router (`router.py`)
- Classifies questions
- Routes to appropriate agent(s)
- Synthesizes multi-source answers

### 2. SQL Agent (`sql_agent.py`)
- LangChain ReAct agent
- Calls MCP tools
- Temperature=0 (deterministic)

### 3. RAG Agent (`rag_agent.py`)
- Semantic document search
- Source citations
- Top-3 chunk retrieval

### 4. MCP Server (`warehouse_mcp.py`)
- FastMCP implementation
- 6 database tools
- Read-only, secure queries

---

## Slide 15: DEMO - Web Interface
**Title:** Live Demonstration

### Demo Flow:
1. **SQL Query:**  
   *"What orders are delayed?"*  
   → Blue badge (SQL Agent)

2. **RAG Query:**  
   *"How to troubleshoot RF scanner?"*  
   → Green badge (RAG Agent)

3. **Combined Query:**  
   *"Critical inventory + replenishment policy"*  
   → Orange badge (Both Agents)

4. **Context:**  
   *"What about shoes specifically?"*  
   → Maintains conversation history

**[LIVE DEMO]**

---

## Slide 16: DEMO - CLI
**Title:** Command Line Interface

```bash
$ uv run python main.py

🏭 WAREHOUSE AI ASSISTANT
========================
Type 'help' for examples

You: What exceptions are open?

AI: There are 13 open exceptions:
- 5 Scanner Issues
- 3 Damaged Goods
- 2 Missing Items
- 2 Wrong Location
- 1 Quality Issue
```

**Key Point:** Same backend, different interface

**[LIVE DEMO if time]**

---

## Slide 17: Real-World Potential
**Title:** Path to Production

### Immediate Augmentation (2-3 weeks)
✅ Add authentication & user roles  
✅ Persistent vector store (ChromaDB)  
✅ Write operations (create/update data)  
✅ Audit logging  

### Enterprise Features (3-6 months)
✅ Multi-warehouse support  
✅ Real-time WMS integration  
✅ Mobile interface  
✅ Notification system (Slack/Teams)  

### Advanced AI (Future)
✅ Fine-tuned models  
✅ Computer vision (damaged goods)  
✅ Autonomous actions  

---

## Slide 18: ROI Estimate
**Title:** Potential Financial Impact

### Assumptions:
- 50-person warehouse
- 20 queries per person per day
- 5 minutes saved per query
- $30/hour average wage

### Calculation:
```
50 people × 20 queries × 5 min = 83 hours/day
83 hours × $30/hour = $2,500/day
$2,500 × 260 work days = $650,000/year
```

### Additional Benefits:
- Faster training (reduced onboarding costs)
- Fewer errors (quality improvements)
- Better decision-making (data access)
- 24/7 availability (no bottlenecks)

---

## Slide 19: Use Case Examples
**Title:** Real Scenarios

### 1. Operations Floor
**Associate:** *"Scanner broken in Zone B"*  
**AI:** Instant troubleshooting + logs exception + checks backup availability

### 2. Customer Service
**Rep:** *"Status of order ORD-102459?"*  
**AI:** Full order details + delay reason + escalation policy

### 3. Management
**Manager:** *"Yesterday's productivity trends?"*  
**AI:** Metrics + correlates with equipment issues + recommendations

### 4. Training
**New Hire:** *"How to do cycle count?"*  
**AI:** Step-by-step procedure + shows assigned tasks

---

## Slide 20: Project Metrics
**Title:** By the Numbers

### Code & Structure
- 📝 **1,500+ lines** of Python
- 🧩 **8 modules** (agents, tools, RAG)
- 🚪 **4 entry points** (CLI, Web, MCP, QuickStart)

### Data
- 💾 **3.18 MB** database
- 📊 **~23,000 records** across 9 tables
- 📦 **10,000 orders** (realistic patterns)

### AI Components
- 🤖 **3 agents** (Router, SQL, RAG)
- 🔧 **6 MCP tools** (database operations)
- 📚 **46 document chunks** (semantic search)

### Documentation
- 📄 **10+ markdown files**
- 📖 **~50 pages** of documentation

---

## Slide 21: Technical Highlights
**Title:** What Makes This Special

### 1. Multi-Agent Architecture
Not a single chatbot - specialized agents with intelligent routing

### 2. Real Data
10,000 orders generated with Faker - production-ready quality

### 3. Production Patterns
- Modular structure
- Error handling
- Security (read-only, parameterized queries)
- Token management

### 4. Course Integration
RAG + MCP + Agents + LangGraph working together

### 5. Dual Interface
Professional web UI and CLI from same codebase

---

## Slide 22: Lessons Learned
**Title:** Key Takeaways

### Technical Insights
✅ **Multi-agent routing** more effective than single agent  
✅ **LLM classification** beats regex/keyword matching  
✅ **Synthesis step** crucial for combining sources  
✅ **Realistic data** reveals real-world challenges  

### Development Process
✅ **Modular structure** enables parallel development  
✅ **Clear separation** makes debugging easier  
✅ **Good documentation** speeds up development  

### AI/ML Specific
✅ **Temperature=0** for deterministic data queries  
✅ **Source citations** critical for trust  
✅ **Token management** prevents context overflow  

---

## Slide 23: Challenges Overcome
**Title:** Problems Solved

### 1. Question Classification
**Challenge:** Determining which agent to use  
**Solution:** LLM-based classifier with clear examples

### 2. Multi-Source Synthesis
**Challenge:** Combining database + documents coherently  
**Solution:** Dedicated synthesis LLM with structured prompts

### 3. Source Attribution
**Challenge:** RAG agent not citing sources  
**Solution:** Include sources in chunk metadata, format in results

### 4. Token Management
**Challenge:** Long conversations exceed context limits  
**Solution:** Truncate to last 20 messages (from Unit 7)

### 5. Realistic Data
**Challenge:** Toy data doesn't test real scenarios  
**Solution:** Faker library for production-quality synthetic data

---

## Slide 24: What's Different from Course
**Title:** Beyond the Basics

| Aspect | Course Examples | Our Project |
|--------|----------------|-------------|
| **Data** | Simple CSV files | 9-table relational DB |
| **Structure** | Single-file scripts | Modular src/ architecture |
| **Scope** | Generic chatbots | Domain-specific system |
| **Interface** | CLI only | Professional web UI + CLI |
| **Routing** | Single agent | Multi-agent with synthesis |
| **Scale** | Hundreds of records | 10,000+ orders |

**Key Message:** Production-quality implementation of course concepts

---

## Slide 25: Future Enhancements
**Title:** What's Next

### Short Term (If Continuing Project)
1. **Persistent Vector Store** - ChromaDB for document updates
2. **User Authentication** - Role-based access control
3. **Write Operations** - Create/update capabilities
4. **Extended Testing** - Unit tests, integration tests
5. **Deployment** - Docker containerization

### Long Term (Real Production)
1. **Live WMS Integration** - Connect to actual warehouse systems
2. **Mobile App** - React Native or PWA
3. **Voice Interface** - Hands-free for warehouse floor
4. **Analytics Dashboard** - Insights and trends
5. **Multi-Language** - Support for diverse workforce

---

## Slide 26: Comparison to Market
**Title:** Competitive Landscape

### Traditional WMS (Warehouse Management Systems)
❌ Complex interfaces, extensive training required  
❌ Scattered information across modules  
❌ Documentation in separate systems  
❌ Limited natural language capability  

### Our AI Assistant
✅ Natural language - no training needed  
✅ Single point of access for all info  
✅ Combines data + documentation automatically  
✅ Available 24/7  
✅ Learns from conversation context  

### Market Opportunity
- Growing warehouse automation market
- Demand for AI in logistics
- Can be SaaS product or enterprise add-on

---

## Slide 27: Code Quality Highlights
**Title:** Professional Standards

### Architecture Decisions
```python
src/
├── agents/      # Single responsibility
├── tools/       # MCP server isolation
├── rag/         # RAG pipeline separate
└── config/      # Centralized settings
```

### Best Practices
✅ **Type hints** throughout  
✅ **Docstrings** on all functions  
✅ **Error handling** with try/except  
✅ **Async/await** for performance  
✅ **Environment variables** for secrets  

### Security
✅ **Read-only queries** (no DELETE/UPDATE)  
✅ **Parameterized SQL** (injection protection)  
✅ **API keys** in .env (not committed)  

---

## Slide 28: Testing Strategy
**Title:** Validation & Quality Assurance

### Manual Testing
✅ **Agent Routing** - Verified SQL/RAG/BOTH classification  
✅ **Tool Calling** - All 6 MCP tools tested  
✅ **Document Retrieval** - Top-3 chunks verified  
✅ **Synthesis** - Combined answers checked  
✅ **Context** - Multi-turn conversations tested  

### Test Scenarios
| Category | Tests | Status |
|----------|-------|--------|
| SQL Queries | 5 scenarios | ✅ Pass |
| RAG Queries | 5 scenarios | ✅ Pass |
| Combined | 3 scenarios | ✅ Pass |
| Context | 4 scenarios | ✅ Pass |

### Known Limitations
- No persistence (by design)
- Read-only operations (safety)
- Static data (demo limitation)

---

## Slide 29: Documentation
**Title:** Comprehensive Project Docs

### Created Documentation:
1. **README.md** - Project overview, architecture  
2. **PRESENTATION.md** - This presentation (detailed)  
3. **PRESENTATION_SLIDES_OUTLINE.md** - Slide structure  
4. **PROGRESS_SUMMARY.md** - Development log  
5. **HOW_TO_LAUNCH.md** - Quick start guide  
6. **REQUIREMENTS_COMPLIANCE.md** - Rubric checklist  
7. **MCP_ARCHITECTURE.md** - MCP technical docs (moved to project root)

### Knowledge Base:
5 warehouse operation documents (46 chunks total)

### Code Comments:
Extensive inline documentation explaining "why" not just "what"

---

## Slide 30: Quick Demo Commands
**Title:** Try It Yourself

### Setup (One-Time)
```bash
cd warehouse-ai-assistant
uv sync
echo "OPENAI_API_KEY=sk-..." > .env
uv run python generate_data.py
```

### Launch Web Interface
```bash
uv run streamlit run web_app.py
# Open: http://localhost:8501
```

### Launch CLI
```bash
uv run python main.py
```

### Example Questions
- "What orders are delayed?"
- "How to fix a broken scanner?"
- "Critical inventory + replenishment policy?"

---

## Slide 31: Architecture Deep Dive
**Title:** Technical Architecture (Detail)

### Component Interaction
```
User Input (Web/CLI)
    ↓
WarehouseRouter
    ├─ classify_question() → LLM decision
    ├─ route_to_agent()
    │   ├─ SQL Agent
    │   │   └─ MCP Client → MCP Server → SQLite
    │   ├─ RAG Agent
    │   │   └─ Vector Store → Document Chunks
    │   └─ Both
    │       ├─ SQL Agent (data)
    │       ├─ RAG Agent (docs)
    │       └─ synthesis_llm (combine)
    └─ return response
```

### Key Technologies per Layer
- **Interface:** Streamlit, asyncio
- **Orchestration:** LangGraph, LangChain
- **Tools:** FastMCP, langchain-mcp-adapters
- **Data:** SQLite, InMemoryVectorStore
- **AI:** OpenAI GPT-4o-mini, text-embedding-3-small

---

## Slide 32: Data Model Detail
**Title:** Database Schema

### Core Tables
```sql
warehouses (2)
  ├─ locations (4,000)
  └─ items (2,000)

orders (10,000)
  ├─ order_lines (20,000+)
  ├─ shipments (10,000)
  └─ exceptions (500)

inventory (4,000+)
  └─ links items + locations

labor_metrics (time-series)
```

### Relationships
- Orders → Order Lines (1:many)
- Orders → Shipments (1:1)
- Items → Inventory → Locations (many:many)
- Warehouses → Locations (1:many)

**Key:** Realistic foreign key relationships, proper normalization

---

## Slide 33: RAG Pipeline Detail
**Title:** Document Processing Flow

### Step 1: Load Markdown Files
```python
docs = load_markdown_files("docs/")
# 5 files: SOPs, troubleshooting, policies
```

### Step 2: Two-Tier Chunking
```python
# Tier 1: Header-based (preserve structure)
MarkdownHeaderTextSplitter([("#", "Header1"), ("##", "Header2")])

# Tier 2: Recursive (handle large sections)
RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200)
```

### Step 3: Embed & Store
```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(chunks)  # 46 chunks
```

### Step 4: Search
```python
results = vector_store.similarity_search_with_score(query, k=3)
# Returns top 3 chunks with relevance scores
```

---

## Slide 34: MCP Tools Detail
**Title:** Database Tools Available

### 1. search_orders
**Parameters:** status, warehouse_id, start_date, end_date  
**Returns:** List of matching orders

### 2. get_order_details
**Parameters:** order_number  
**Returns:** Full order + all line items

### 3. check_inventory
**Parameters:** item_id, warehouse_id, low_stock  
**Returns:** Stock levels and locations

### 4. get_shipment_status
**Parameters:** order_number, tracking_number  
**Returns:** Carrier, tracking, delivery dates

### 5. get_exceptions
**Parameters:** status, exception_type  
**Returns:** Operational issues list

### 6. get_labor_metrics
**Parameters:** start_date, end_date, warehouse_id  
**Returns:** Productivity statistics

---

## Slide 35: Conclusion
**Title:** Project Summary

### What We Built
✅ Intelligent multi-agent AI system  
✅ Solves real warehouse operations problems  
✅ Production-quality code architecture  
✅ Realistic data (10,000 orders)  
✅ Two professional interfaces  

### Course Integration
✅ RAG (Unit 4) - Chunking, embeddings, search  
✅ MCP (Unit 6) - FastMCP server, 6 tools  
✅ Agents (Unit 7) - ReAct pattern, routing  
✅ LangGraph (Unit 7) - Multi-agent orchestration  

### Real-World Potential
✅ Clear path to production  
✅ $650K/year estimated ROI  
✅ Can be deployed in actual warehouses  

---

## Slide 36: Thank You & Questions
**Title:** Questions?

### Project Repository
`e:\Projects\warehouse-ai-assistant`

### Quick Links
- 📖 **Full Documentation:** README.md
- 🚀 **Quick Start:** HOW_TO_LAUNCH.md
- 📊 **Development Log:** PROGRESS_SUMMARY.md
- 📋 **This Presentation:** PRESENTATION.md

### Try It
```bash
start_web.bat  # Web interface
start_cli.bat  # CLI interface
```

### Contact
[Your contact information]

---

**END OF PRESENTATION**

---

## Appendix Slides (Backup)

### A1: Token Management Strategy
**Title:** Handling Context Limits

**Problem:** GPT-4o-mini has 128K token limit, but conversations grow

**Solution (from Unit 7):**
```python
def truncate_messages(messages, max_messages=20):
    """Keep only last N messages"""
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages
```

**Applied to:**
- SQL Agent: `state_modifier=truncate_messages`
- RAG Agent: `state_modifier=truncate_messages`
- Router: Manual history trimming

---

### A2: Error Handling Examples
**Title:** Graceful Failure Management

```python
try:
    router = await create_router()
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    print("\n💡 Make sure:")
    print("   1. Database exists: python generate_data.py")
    print("   2. API key is set in .env file")
    print("   3. Dependencies installed: uv sync")
```

**Handles:**
- Missing database
- Invalid API keys
- MCP server failures
- Network issues

---

### A3: Security Considerations
**Title:** Safety & Protection

### SQL Injection Protection
```python
# ✅ Good: Parameterized query
cursor.execute("SELECT * FROM orders WHERE status = ?", (status,))

# ❌ Bad: String interpolation
cursor.execute(f"SELECT * FROM orders WHERE status = '{status}'")
```

### Read-Only Operations
```python
# Only SELECT queries allowed
# No DELETE, UPDATE, INSERT, DROP
```

### API Key Management
```python
# ✅ Good: Environment variable
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Bad: Hardcoded
api_key = "sk-1234567890..."
```

---

### A4: Alternative Approaches Considered
**Title:** Design Decisions

| Decision | Alternative | Why We Chose This |
|----------|-------------|-------------------|
| **Multi-Agent** | Single agent | Better specialization |
| **LLM Routing** | Regex/keywords | More flexible, handles nuance |
| **InMemory Vector Store** | ChromaDB/Pinecone | Simpler, sufficient for 46 chunks |
| **FastMCP** | Custom tools | Protocol standard, reusable |
| **SQLite** | PostgreSQL | Lightweight, portable |
| **Streamlit** | React/Vue | Rapid prototyping, built-in chat |

---

### A5: Performance Metrics
**Title:** Response Times (Approximate)

| Query Type | Avg Time | Breakdown |
|------------|----------|-----------|
| **SQL Only** | 2-3 sec | Routing (0.5s) + MCP (0.5s) + LLM (1-2s) |
| **RAG Only** | 2-4 sec | Routing (0.5s) + Vector (0.3s) + LLM (1-3s) |
| **Both** | 5-7 sec | SQL (2s) + RAG (2s) + Synthesis (1-3s) |

**Bottleneck:** OpenAI API calls (network latency)

**Production Optimizations:**
- Caching for common queries
- Async parallel execution (SQL + RAG simultaneously)
- Local LLM for routing (faster, cheaper)

---

### A6: Scaling Considerations
**Title:** Growing the System

### Current Scale
- 46 document chunks → InMemoryVectorStore ✅
- 10K orders → SQLite ✅
- Single user → No concurrency needed ✅

### At 100K Orders
- SQLite still fine ✅
- Add database indexes ✅
- Connection pooling ✅

### At 1M Orders + 100 Concurrent Users
- Migrate to PostgreSQL 📈
- Horizontal scaling (multiple MCP servers) 📈
- Persistent vector store (Pinecone) 📈
- Load balancer 📈
- Redis caching 📈

**Key:** Architecture supports this growth path

---

## Presentation Tips

### For Virtual Presentations
1. **Test screen sharing** beforehand
2. **Have backup screenshots** in case live demo fails
3. **Record demo video** as failsafe
4. **Mute notifications** during presentation

### For In-Person Presentations
1. **Bring laptop** with everything pre-loaded
2. **Test projector compatibility** early
3. **Have USB backup** of presentation
4. **Internet backup plan** (mobile hotspot)

### Demo Best Practices
1. **Practice demo flow** multiple times
2. **Have example questions ready** (don't improvise)
3. **Reset state** between demos (clear history)
4. **Explain what's happening** during waits

### Handling Questions
1. **Acknowledge limits** honestly
2. **Refer to backup slides** for technical details
3. **Show code** if asked about implementation
4. **Discuss real-world path** enthusiastically