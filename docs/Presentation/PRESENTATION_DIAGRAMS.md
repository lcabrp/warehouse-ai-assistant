# Visual Diagrams for Presentation
## Warehouse AI Assistant - Copy-Paste Ready Mermaid Diagrams

These diagrams can be:
1. Rendered in GitHub/GitLab markdown
2. Converted to images using https://mermaid.live
3. Embedded in presentation slides
4. Printed as handouts

---

## Diagram 1: System Architecture Overview

```mermaid
graph TB
    A[👤 User] --> B{Interface}
    B -->|Web| C[Streamlit UI<br/>Port 8501]
    B -->|CLI| D[Terminal Interface<br/>asyncio]
    
    C --> E[Router/Classifier]
    D --> E
    
    E --> F{Question<br/>Classification}
    
    F -->|SQL| G[SQL Agent<br/>LangChain ReAct]
    F -->|RAG| H[RAG Agent<br/>LangChain ReAct]
    F -->|BOTH| I[Sequential +<br/>Synthesis]
    
    G --> J[MCP Server<br/>FastMCP]
    J --> K[(SQLite DB<br/>warehouse.db<br/>10K orders)]
    
    H --> L[Vector Store<br/>InMemoryVectorStore]
    L --> M[📄 Documentation<br/>5 Markdown Files<br/>46 Chunks]
    
    I --> G
    I --> H
    I --> N[Synthesis LLM<br/>Combine Results]
    
    G --> O[Response]
    H --> O
    N --> O
    O --> A
    
    style A fill:#e1f5ff
    style E fill:#fff4e1
    style G fill:#2196F3,color:#fff
    style H fill:#4CAF50,color:#fff
    style N fill:#FF9800,color:#fff
    style O fill:#e1ffe7
```

---

## Diagram 2: Multi-Agent Routing Flow

```mermaid
flowchart LR
    A[User Question] --> B[Router]
    B --> C{Classifier LLM}
    
    C -->|Data Query| D[SQL Agent]
    C -->|Procedure Query| E[RAG Agent]
    C -->|Needs Both| F[Both Mode]
    
    D --> G[MCP Tools]
    G --> H[(Database)]
    H --> I[Data Response]
    
    E --> J[Vector Search]
    J --> K[📚 Documents]
    K --> L[Doc Response<br/>+Citations]
    
    F --> M[1. SQL Agent]
    M --> N[2. RAG Agent]
    N --> O[3. Synthesis]
    O --> P[Combined<br/>Response]
    
    I --> Q[Final Answer]
    L --> Q
    P --> Q
    
    style C fill:#FFE4B5
    style D fill:#ADD8E6
    style E fill:#90EE90
    style F fill:#FFB366
```

---

## Diagram 3: MCP Tool Architecture

```mermaid
graph TD
    A[SQL Agent] --> B[LangChain MCP Adapter]
    B --> C[MCP Server<br/>FastMCP]
    
    C --> D[Lifespan Manager]
    D --> E[(SQLite Connection)]
    
    C --> F[search_orders]
    C --> G[get_order_details]
    C --> H[check_inventory]
    C --> I[get_shipment_status]
    C --> J[get_exceptions]
    C --> K[get_labor_metrics]
    
    F --> L{Parameterized<br/>SQL Queries}
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> E
    E --> M[Query Results]
    M --> N[JSON Response]
    N --> B
    B --> A
    
    style C fill:#FFA500,color:#fff
    style E fill:#4682B4,color:#fff
    style L fill:#32CD32,color:#fff
```

---

## Diagram 4: RAG Pipeline

```mermaid
flowchart TB
    A[📄 Markdown Files<br/>5 Documents] --> B[Markdown Header<br/>Splitter]
    
    B --> C[Preserves Structure<br/># and ## headers]
    C --> D[Recursive Text<br/>Splitter]
    D --> E[46 Chunks<br/>1000 chars each<br/>200 char overlap]
    
    E --> F[OpenAI Embeddings<br/>text-embedding-3-small]
    F --> G[InMemory<br/>Vector Store]
    
    H[User Question] --> I[Embed Query]
    I --> J[Similarity Search]
    J --> G
    
    G --> K[Top 3 Chunks<br/>with scores]
    K --> L[Format with<br/>Source Citations]
    L --> M[RAG Agent<br/>Response]
    
    style A fill:#90EE90
    style E fill:#FFE4B5
    style G fill:#ADD8E6
    style M fill:#98FB98
```

---

## Diagram 5: Database Schema

```mermaid
erDiagram
    WAREHOUSES ||--o{ LOCATIONS : contains
    WAREHOUSES ||--o{ ORDERS : receives
    LOCATIONS ||--o{ INVENTORY : stores
    ITEMS ||--o{ INVENTORY : tracked_in
    ITEMS ||--o{ ORDER_LINES : included_in
    ORDERS ||--o{ ORDER_LINES : contains
    ORDERS ||--|| SHIPMENTS : has
    ORDERS ||--o{ EXCEPTIONS : may_have
    WAREHOUSES ||--o{ LABOR_METRICS : tracks
    
    WAREHOUSES {
        int warehouse_id PK
        string name
        string location
    }
    
    LOCATIONS {
        int location_id PK
        int warehouse_id FK
        string aisle
        string bin
    }
    
    ITEMS {
        int item_id PK
        string sku
        string description
        string category
    }
    
    INVENTORY {
        int inventory_id PK
        int item_id FK
        int location_id FK
        int quantity
        int reorder_point
    }
    
    ORDERS {
        int order_id PK
        string order_number
        int warehouse_id FK
        string status
        date order_date
    }
    
    ORDER_LINES {
        int line_id PK
        int order_id FK
        int item_id FK
        int quantity
    }
    
    SHIPMENTS {
        int shipment_id PK
        int order_id FK
        string tracking_number
        string carrier
        date ship_date
    }
    
    EXCEPTIONS {
        int exception_id PK
        int order_id FK
        string type
        string status
        date created
    }
    
    LABOR_METRICS {
        int metric_id PK
        int warehouse_id FK
        date date
        float picks_per_hour
        int total_picks
    }
```

---

## Diagram 6: Conversation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as Router
    participant C as Classifier LLM
    participant S as SQL Agent
    participant A as RAG Agent
    participant M as MCP Server
    participant V as Vector Store
    participant Y as Synthesizer
    
    U->>R: "Critical inventory + replenishment policy?"
    R->>C: Classify question
    C-->>R: Classification: BOTH
    
    Note over R: Sequential execution mode
    
    R->>S: Execute SQL agent
    S->>M: Call check_inventory()
    M-->>S: Inventory data
    S-->>R: SQL results
    
    R->>A: Execute RAG agent
    A->>V: Similarity search
    V-->>A: Policy chunks
    A-->>R: RAG results with sources
    
    R->>Y: Synthesize(SQL_results, RAG_results)
    Y-->>R: Combined answer
    R-->>U: "Here are 10 critical items...<br/>According to policy..."
    
    Note over U,Y: Total time: ~5-7 seconds
```

---

## Diagram 7: Project Structure Tree

```mermaid
graph TD
    A[warehouse-ai-assistant/] --> B[src/]
    A --> C[data/]
    A --> D[docs/]
    A --> E[Entry Points]
    A --> F[Config Files]
    
    B --> G[agents/]
    B --> H[tools/]
    B --> I[rag/]
    B --> J[config/]
    
    G --> K[router.py<br/>sql_agent.py<br/>rag_agent.py]
    H --> L[warehouse_mcp.py<br/>MCP Server]
    I --> M[document_loader.py<br/>vector_store.py]
    J --> N[settings.py<br/>Centralized Config]
    
    C --> O[warehouse.db<br/>3.18 MB<br/>10K orders]
    
    D --> P[5 Markdown Files<br/>SOPs & Policies<br/>46 chunks]
    
    E --> Q[main.py<br/>web_app.py<br/>run_mcp_server.py]
    
    F --> R[pyproject.toml<br/>.env<br/>README.md]
    
    style A fill:#FFE4B5
    style B fill:#ADD8E6
    style G fill:#90EE90
    style H fill:#FFA500
    style I fill:#98FB98
```

---

## Diagram 8: Course Integration Map

```mermaid
mindmap
    root((Warehouse<br/>AI Assistant))
        Unit 4: RAG
            Document Loading
            Chunking Strategy
                Header-based
                Recursive
            Embeddings
                text-embedding-3-small
            Vector Store
                InMemoryVectorStore
            Semantic Search
        Unit 6: MCP
            FastMCP Server
            6 Database Tools
            Context Management
                Lifespan pattern
            Structured Outputs
            Tool Definitions
        Unit 7: Agents
            ReAct Pattern
                SQL Agent
                RAG Agent
            Multi-Agent System
            LangChain Integration
            Tool Calling
        Unit 7: LangGraph
            Agent Orchestration
            Routing Logic
            Message History
            Token Management
        Additional
            Faker for Data
            Streamlit UI
            asyncio CLI
```

---

## Diagram 9: Data Flow - SQL Query

```mermaid
flowchart LR
    A["🙋 User:<br/>'What orders<br/>are delayed?'"] --> B[Router]
    B --> C{Classifier}
    C --> D["Decision:<br/>SQL Agent"]
    
    D --> E[SQL Agent<br/>Receives Question]
    E --> F["ReAct Loop<br/>Thinks"]
    F --> G["Tool Call:<br/>search_orders<br/>(status='DELAYED')"]
    
    G --> H[MCP Client]
    H --> I[MCP Server]
    I --> J["SQL Query:<br/>SELECT * FROM orders<br/>WHERE status='DELAYED'"]
    J --> K[(warehouse.db)]
    
    K --> L["Results:<br/>50 delayed orders"]
    L --> I
    I --> H
    H --> G
    
    G --> M["Agent Formats<br/>Response"]
    M --> N["Final Answer with<br/>Order Details"]
    N --> O[Router]
    O --> P["🙋 User sees<br/>structured list"]
    
    style A fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#2196F3,color:#fff
    style K fill:#4682B4,color:#fff
    style P fill:#e1ffe7
```

---

## Diagram 10: Data Flow - RAG Query

```mermaid
flowchart LR
    A["🙋 User:<br/>'How to fix<br/>broken scanner?'"] --> B[Router]
    B --> C{Classifier}
    C --> D["Decision:<br/>RAG Agent"]
    
    D --> E[RAG Agent<br/>Receives Question]
    E --> F["ReAct Loop<br/>Thinks"]
    F --> G["Tool Call:<br/>search_documents<br/>(query=question)"]
    
    G --> H["Embed Query<br/>text-embedding-3-small"]
    H --> I[Vector Store<br/>Similarity Search]
    I --> J["Top 3 Chunks:<br/>Equipment_Troubleshooting.md"]
    
    J --> K["Format with<br/>Source Citations"]
    K --> L["Return:<br/>Procedure + Source"]
    L --> F
    
    F --> M["Agent Formats<br/>with Citations"]
    M --> N["Final Answer:<br/>Steps + Document"]
    N --> O[Router]
    O --> P["🙋 User sees<br/>instructions + source"]
    
    style A fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#4CAF50,color:#fff
    style I fill:#9370DB,color:#fff
    style P fill:#e1ffe7
```

---

## Diagram 11: Data Flow - Both Agents

```mermaid
flowchart TB
    A["🙋 User:<br/>'Critical inventory +<br/>replenishment policy'"] --> B[Router]
    B --> C{Classifier}
    C --> D["Decision:<br/>BOTH"]
    
    D --> E["Step 1:<br/>SQL Agent"]
    E --> F[MCP Tools]
    F --> G[(Database)]
    G --> H["Inventory Data"]
    
    D --> I["Step 2:<br/>RAG Agent"]
    I --> J[Vector Search]
    J --> K[📚 Documents]
    K --> L["Policy Text"]
    
    H --> M[Synthesis LLM]
    L --> M
    
    M --> N["Prompt:<br/>Combine data + policy<br/>into coherent answer"]
    N --> O["Synthesized Response<br/>• Data table<br/>• Policy explanation<br/>• Combined insights"]
    
    O --> P[Router]
    P --> Q["🙋 User sees<br/>integrated answer"]
    
    style A fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#FF9800,color:#fff
    style M fill:#9370DB,color:#fff
    style Q fill:#e1ffe7
```

---

## Diagram 12: Technology Stack Layers

```mermaid
graph TB
    subgraph "User Layer"
        A[Web Browser]
        B[Terminal/CLI]
    end
    
    subgraph "Interface Layer"
        C[Streamlit<br/>Port 8501]
        D[asyncio<br/>CLI Handler]
    end
    
    subgraph "Orchestration Layer"
        E[Router/Classifier]
        F[LangGraph]
    end
    
    subgraph "Agent Layer"
        G[SQL Agent<br/>LangChain ReAct]
        H[RAG Agent<br/>LangChain ReAct]
    end
    
    subgraph "Tool Layer"
        I[MCP Server<br/>FastMCP]
        J[Vector Store<br/>InMemoryVectorStore]
    end
    
    subgraph "Data Layer"
        K[(SQLite<br/>warehouse.db)]
        L[📄 Markdown Docs<br/>46 chunks]
    end
    
    subgraph "AI Layer"
        M[OpenAI GPT-4o-mini<br/>LLM]
        N[text-embedding-3-small<br/>Embeddings]
    end
    
    A --> C
    B --> D
    C --> E
    D --> E
    E --> F
    F --> G
    F --> H
    G --> I
    H --> J
    I --> K
    J --> L
    G -.uses.-> M
    H -.uses.-> M
    E -.uses.-> M
    J -.uses.-> N
    
    style A fill:#e1f5ff
    style C fill:#FFB6C1
    style E fill:#FFE4B5
    style G fill:#ADD8E6
    style H fill:#90EE90
    style K fill:#4682B4,color:#fff
    style M fill:#FF6347,color:#fff
```

---

## Diagram 13: ROI Calculation Flow

```mermaid
graph LR
    A[50 Employees] --> B[20 Queries/Day Each]
    B --> C[1,000 Queries/Day Total]
    C --> D[5 Minutes Saved per Query]
    D --> E[5,000 Minutes = ~83 Hours/Day]
    E --> F[$30/Hour Average Wage]
    F --> G[$2,500 Saved per Day]
    G --> H[260 Work Days/Year]
    H --> I[$650,000/Year ROI]
    
    style A fill:#e1f5ff
    style I fill:#90EE90
```

---

## Diagram 14: Production Deployment Path

```mermaid
timeline
    title Production Roadmap
    
    section Phase 1 (Weeks 1-3)
        Week 1 : Persistent Vector Store (ChromaDB)
               : Authentication System (JWT)
        Week 2 : Write Operations (MCP tools)
               : Audit Logging
        Week 3 : Testing & Security Review
               : Documentation Updates
    
    section Phase 2 (Months 2-4)
        Month 2 : Multi-warehouse Support
                : Role-based Access Control
        Month 3 : Real-time WMS Integration
                : API Connections
        Month 4 : Mobile Interface (PWA)
                : Notification System
    
    section Phase 3 (Months 5-6)
        Month 5 : Advanced Analytics Dashboard
                : Predictive Forecasting
        Month 6 : Performance Optimization
                : Production Deployment
```

---

## How to Use These Diagrams

### Option 1: Render in Markdown
- GitHub/GitLab automatically render Mermaid
- Just include in your README.md or presentation markdown

### Option 2: Convert to Images
1. Go to https://mermaid.live
2. Copy-paste diagram code
3. Export as PNG/SVG
4. Insert into PowerPoint/Keynote

### Option 3: Use in Reveal.js
```html
<section data-markdown>
    <textarea data-template>
        ```mermaid
        [paste diagram here]
        ```
    </textarea>
</section>
```

### Option 4: Documentation
- Include in technical documentation
- Add to project wiki
- Share with stakeholders

---

## Diagram Customization Tips

### Change Colors
```mermaid
style NodeName fill:#HEX_COLOR,color:#TEXT_COLOR
```

### Add Icons (if supported)
```mermaid
graph TD
    A[📊 Data] --> B[🤖 AI] --> C[👤 User]
```

### Adjust Layout
- `TB` = Top to Bottom
- `LR` = Left to Right
- `RL` = Right to Left
- `BT` = Bottom to Top

---

**These diagrams make your presentation visual and professional!**

Choose 2-3 key diagrams for your slides, keep the rest as backup.

Recommended core diagrams:
1. **System Architecture Overview** (Diagram 1) - Shows everything
2. **Multi-Agent Routing** (Diagram 2) - Core innovation
3. **Project Structure** (Diagram 7) - Code organization

---

*Created: March 31, 2026*  
*Mermaid Version: Compatible with GitHub/GitLab*
