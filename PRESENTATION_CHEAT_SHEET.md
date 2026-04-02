# Presentation Quick Reference Sheet
## Warehouse AI Assistant - Live Demo Cheat Sheet

---

## 🚀 Setup Commands (Run BEFORE Presentation)

```bash
# 1. Navigate to project
cd e:\Projects\warehouse-ai-assistant

# 2. Ensure dependencies installed
uv sync

# 3. Verify .env file exists with API key
# (Check this!)

# 4. Generate fresh database
uv run python generate_data.py

# 5. Test web interface works
uv run streamlit run web_app.py
# Open browser to http://localhost:8501
# Test one question, then close

# 6. Clear any cached state
rm -rf __pycache__
rm -rf src/__pycache__
```

---

## 🎯 Demo Flow (5 minutes)

### Web Interface Demo

**Launch:**
```bash
start_web.bat
```
or
```bash
uv run streamlit run web_app.py
```

**Demo Questions (Copy-Paste These):**

1. **SQL Query** (Shows blue badge)
   ```
   What orders are delayed?
   ```
   **Point out:** "Notice the blue badge - the router automatically selected the SQL Agent"

2. **RAG Query** (Shows green badge)
   ```
   How do I troubleshoot a broken RF scanner?
   ```
   **Point out:** "Green badge - RAG Agent searched our documentation and cited the source"

3. **Weather Query** (Shows purple/weather badge)
   ```
   What's the weather like in Louisville today?
   ```
   **Point out:** "Weather Agent uses Tavily to search real-time web information. Louisville is one of our warehouse locations."

4. **Combined SQL + Weather** (Shows combined badge)
   ```
   Are there weather conditions affecting our Dallas warehouse shipments?
   ```
   **Point out:** "Combines database query with weather search - correlates delays with conditions. Dallas is our TX fulfillment center."

5. **Location-Specific Query**
   ```
   Show me critical inventory at our Reno warehouse
   ```
   **Point out:** "SQL query with location filter - Reno is our NV distribution center"

5. **Clear and Different Topic**
   ```
   What is the cycle count procedure?
   ```
   **Point out:** "Handles topic changes smoothly"

---

### CLI Demo (Optional - 2 minutes)

**Launch:**
```bash
start_cli.bat
```
or
```bash
uv run python main.py
```

**Commands:**
```bash
> help
> What exceptions are open?
> exit
```

**Point out:** "Same backend, different interface. Shows modularity."

---

## 🗣️ Key Talking Points

### Problem We're Solving
"Warehouse operations require both **data** (what's happening) and **procedures** (how to handle it). Currently these are scattered across multiple systems. Our AI assistant unifies them with natural language."

### Why Multi-Agent
"Instead of one chatbot trying to do everything, we have specialized agents:
- SQL Agent: Optimized for database queries
- RAG Agent: Optimized for document search
- Router: Decides which to use and combines results

Like having a data analyst AND a documentation expert on call 24/7."

### Course Integration
"This builds on **4 course units**:
- Unit 4: RAG with 2-tier chunking and embeddings
- Unit 6: MCP server with 6 database tools
- Unit 7: ReAct agents and multi-agent routing
- Unit 7: LangGraph for orchestration"

### Real Data
"We generated **10,000 realistic orders** using the Faker library - not toy data. Product names, tracking numbers, employee names all look professional. This could go into production tomorrow."

### Production Path
"Clear path to production:
- Add authentication (2 weeks)
- Connect to real WMS (3-4 weeks)
- Deploy as internal tool (1 week)

Estimated **$650K/year ROI** for a 50-person warehouse."

---

## 📊 Key Metrics to Mention

- **Code:** 1,500+ lines Python, 8 modules
- **Data:** 3.18 MB database, 10,000 orders, ~23,000 total records
- **AI:** 3 agents, 6 MCP tools, 46 document chunks
- **Docs:** 10+ markdown files, ~50 pages documentation
- **Time:** SQL queries ~2-3 sec, RAG ~2-4 sec, Combined ~5-7 sec

---

## 🎨 Visual Aids to Show

### Architecture Diagram
Show the flow:
```
User → Router/Classifier → [SQL | RAG | BOTH] → Response
              ↓              ↓      ↓      ↓
         LLM Decision    Database  Docs  Combined
```

### Project Structure
```
warehouse-ai-assistant/
├── src/agents/     ← Core AI agents
├── src/tools/      ← MCP server
├── src/rag/        ← Vector search
├── data/           ← SQLite DB
├── docs/           ← Knowledge base
├── main.py         ← CLI entry
└── web_app.py      ← Web entry
```

### Tech Stack Icons
- Python 3.13
- OpenAI GPT-4o-mini
- LangChain / LangGraph
- FastMCP
- Streamlit
- SQLite

---

## ❓ Anticipated Questions & Answers

### Q: "Why not just use ChatGPT?"
**A:** "ChatGPT doesn't have access to our warehouse data or our specific procedures. We needed a system that:
1. Queries our live database
2. Searches our SOPs
3. Combines them intelligently
4. Maintains conversation context
This is a specialized domain system, not a general chatbot."

### Q: "How does the router decide which agent to use?"
**A:** "It uses an LLM classifier with clear examples. For instance:
- 'What orders are delayed?' → Data query → SQL Agent
- 'How to fix scanner?' → Procedural → RAG Agent
- 'Why is order X delayed and what do I do?' → Both → Sequential execution + synthesis

The LLM understands nuance better than regex or keyword matching."

### Q: "What about hallucinations?"
**A:** "Great question. We mitigate this several ways:
1. SQL Agent uses tools - returns actual database data, not generated text
2. RAG Agent is instructed to answer ONLY from retrieved documents
3. Both agents cite their sources
4. Temperature=0 for deterministic responses
5. All data is grounded in either database or documents"

### Q: "Can it write to the database?"
**A:** "Not currently - by design for safety. All queries are read-only. For production, we'd add authenticated write operations with proper permissions:
- Operators can create exceptions
- Managers can update order status
- etc.
But we'd do this through controlled MCP tools with audit logging."

### Q: "Why not use a bigger model like GPT-4?"
**A:** "GPT-4o-mini is perfect for this use case:
1. Fast enough (2-4 sec responses)
2. Accurate for tool calling and routing
3. Cost-effective for production (90% cheaper than GPT-4)
4. We're using tools for facts, not relying on model knowledge

For production, this means lower costs without sacrificing quality."

### Q: "How would you handle multiple warehouses?"
**A:** "Easy extensions:
1. Add warehouse_id filter to all queries
2. User authentication tied to warehouse access
3. Update prompts to be warehouse-aware
4. Multi-tenancy in vector store (filter by warehouse)

The architecture supports this - just configuration changes."

### Q: "What about data privacy?"
**A:** "Current setup: Data stays local (SQLite), only queries/results go to OpenAI API.

For production with sensitive data:
1. Use Azure OpenAI (data residency guarantees)
2. Or self-hosted LLM (Llama 3, etc.)
3. Encrypt data at rest
4. Audit logging for compliance
5. Role-based access control"

### Q: "How long did this take to build?"
**A:** "About [X] weeks:
- Week 1: Database design + data generation
- Week 2: MCP server + SQL agent
- Week 3: RAG pipeline + RAG agent
- Week 4: Router + web interface + testing

Building on course concepts made it much faster than starting from scratch."

---

## 🚨 Troubleshooting During Demo

### If API Key Error
**Show:** `.env` file (hide actual key)
**Say:** "Just authentication - the architecture is solid"
**Backup:** Have spare API key ready

### If Database Not Found
**Run:** `uv run python generate_data.py`
**Say:** "Demo data generation - uses Faker for realistic data"
**Backup:** Have pre-generated warehouse.db ready

### If Slow Response
**Say:** "This is calling the OpenAI API - normal latency. In production we'd add caching for common queries."
**Backup:** Have screenshot of successful response ready

### If Wrong Agent Selected
**Say:** "Interesting edge case - the classifier is probabilistic. This shows the LLM decision-making process. We could refine the classifier prompt to handle this better."
**Positive Spin:** "Shows transparency in how the system works"

### If Internet Down
**Backup Plan:**
1. Show recorded demo video
2. Walk through screenshots
3. Show code structure instead

---

## 🎬 Presentation Structure (20 min)

| Time | Section | Key Points |
|------|---------|------------|
| 0-2 min | Problem | Warehouse data silos, time waste |
| 2-4 min | Solution | Multi-agent AI system overview |
| 4-9 min | **DEMO** | Web UI: 3-4 example queries |
| 9-12 min | Architecture | Diagram, explain routing |
| 12-15 min | Tech Stack | Course integration, tools used |
| 15-17 min | Code | Show structure, key modules |
| 17-19 min | Real-World | Production path, ROI |
| 19-20 min | Q&A | Questions |

**Time Management Tip:** If running long, skip CLI demo and code walkthrough. Prioritize live web demo.

---

## 💡 Presentation Tips

### Energy & Delivery
- **Speak with enthusiasm** about solving real problems
- **Pause after showing results** to let them sink in
- **Make eye contact** (camera for virtual)
- **Use hand gestures** to emphasize points

### Demo Best Practices
- **Narrate what you're doing:** "I'm going to type a complex question that needs both data and procedures..."
- **Point out key features:** "Notice the orange badge here..."
- **Show, don't tell:** Let the system speak for itself
- **Explain delays:** "While this is thinking, it's calling the OpenAI API..."

### Handling Nerves
- **Deep breaths** before starting
- **Have water nearby**
- **Smile** - it comes through in your voice
- **Remember:** You know this better than anyone in the room

### Virtual Presentation
- **Test screen share** beforehand
- **Close unnecessary tabs/apps**
- **Mute notifications**
- **Position camera at eye level**
- **Good lighting** on your face

---

## ✅ Pre-Presentation Checklist

**30 Minutes Before:**
- [ ] Test API key is working
- [ ] Database generated and exists
- [ ] Web interface launches successfully
- [ ] Test one query end-to-end
- [ ] Close all unnecessary applications
- [ ] Mute phone/notifications
- [ ] Have water nearby
- [ ] Open presentation slides
- [ ] Open this cheat sheet
- [ ] Open VS Code with project
- [ ] Terminal ready with cd to project directory

**5 Minutes Before:**
- [ ] Deep breaths
- [ ] Review demo questions
- [ ] Smile
- [ ] You've got this!

---

## 🎯 Closing Strong

**Final Message:**
"This project demonstrates that AI agents aren't just a theoretical concept - they solve real business problems. We built a production-quality system that could save a warehouse $650K per year, using concepts from our course. The path from capstone to production is clear, and I'm excited to potentially take it there.

Thank you. Questions?"

**Remember:**
- You built something impressive
- You understand it deeply
- You can explain it clearly
- This is production-quality work

**Good luck!** 🚀

---

## 📞 Emergency Contacts

**Course Instructor:** [Name/Email]
**Tech Support:** [If applicable]
**Backup Presenter:** [If team project]

---

**Last Updated:** March 31, 2026  
**Next Review:** Just before presentation!
