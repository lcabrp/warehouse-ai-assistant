# 🚀 How to Launch Your Warehouse AI Assistant

## Both Interfaces Are Ready!

You have **two fully functional interfaces** for your capstone project.

---

## 1️⃣ Web Interface (Recommended for Presentation)

### Launch Command:
```bash
uv run streamlit run web_app.py
```

**OR** just double-click: `start_web.bat`

### Access:
Open your browser to: **http://localhost:8501**

### Features:
- ✨ Interactive chat with full conversation history
- 🎨 Color-coded agent badges (SQL=Blue, RAG=Green, BOTH=Orange)
- 📋 Built-in example questions in sidebar
- 🧹 Clear conversation button
- 📱 Professional responsive design

### Perfect for:
- ✅ Capstone presentation/demo
- ✅ Showing multi-agent routing visually
- ✅ Impressing evaluators

---

## 2️⃣ CLI Interface (Command Line)

### Launch Command:
```bash
uv run python main.py
```

**OR** just double-click: `start_cli.bat`

### Features:
- 💻 Terminal-based interaction
- ❓ Type `help` for example questions
- 🚪 Type `exit` or `quit` to close
- ⚡ Fast and lightweight

### Perfect for:
- ✅ Quick testing
- ✅ Demonstrating both interfaces
- ✅ Server environments without GUI

---

## 🎯 Quick Start

1. **First time setup:**
   ```bash
   uv sync
   ```

2. **Launch web interface:**
   ```bash
   uv run streamlit run web_app.py
   ```

3. **Open browser:**
   Go to http://localhost:8501

4. **Start chatting!**
   Try: "What orders are delayed?"

---

## ⚠️ Troubleshooting

### "Command not found" error?
Make sure you're in the project directory:
```bash
cd warehouse-ai-assistant
```

### "Module not found" error?
Run:
```bash
uv sync
```

### Database not found?
Generate it:
```bash
uv run python generate_data.py
```

### API key error?
Check your `.env` file has:
```
OPENAI_API_KEY=sk-...
```

---

## 📊 Testing Both Interfaces

### Test the Web Interface:
1. Run: `uv run streamlit run web_app.py`
2. Open: http://localhost:8501
3. Ask: "What orders are delayed?"
4. See the **blue SQL badge** appear
5. Get structured data results

### Test the CLI:
1. Run: `uv run python main.py`
2. Type: `help`
3. See example questions
4. Ask a question
5. Type: `exit` to quit

---

## 🎥 For Your Video Demo

**Show both interfaces in your video:**

1. **Start with Web Interface** (more impressive)
   - Show the clean UI
   - Demonstrate SQL query (data badge)
   - Demonstrate RAG query (procedure badge)
   - Demonstrate BOTH query (synthesis badge)

2. **Then show CLI** (optional, shows versatility)
   - Quick demonstration
   - Shows you built multiple interfaces

3. **Highlight key features:**
   - Multi-agent routing
   - Information synthesis
   - Multiple data sources
   - Clean code architecture

---

## ✅ You're Ready!

Both interfaces are **fully functional** and production-ready.

**For your presentation, use the web interface** - it's more visual and impressive!
