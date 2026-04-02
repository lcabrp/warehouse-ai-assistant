"""
Warehouse AI Assistant - Web Interface
======================================

Streamlit-based web GUI for the warehouse operations AI assistant.

Usage:
    streamlit run web_app.py
    
    Then open: http://localhost:8501
"""

import asyncio
import streamlit as st
from src.agents.router import create_router


# Page configuration
st.set_page_config(
    page_title="Warehouse AI Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .sql-agent {
        background-color: #2196F3;
        color: white;
    }
    .rag-agent {
        background-color: #4CAF50;
        color: white;
    }
    .weather-agent {
        background-color: #9C27B0;
        color: white;
    }
    .combined-agents {
        background-color: #FF9800;
        color: white;
    }
    .both-agents {
        background-color: #FF9800;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "router" not in st.session_state:
    st.session_state.router = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False


@st.cache_resource
def get_router():
    """Initialize router (cached to avoid reloading)."""
    return asyncio.run(create_router())


# Sidebar
with st.sidebar:
    st.title("🏭 Warehouse AI")
    st.markdown("---")
    
    st.subheader("About")
    st.markdown("""
    This AI assistant helps you with:
    - **📊 Data Queries** (orders, inventory, metrics)
    - **📚 Procedures** (troubleshooting, policies)
    - **🌐 Weather/News** (external conditions affecting operations)
    - **🔄 Combined Insights** (data + procedures + weather)
    """)
    
    st.markdown("---")
    
    st.subheader("Example Questions")
    
    with st.expander("📊 Data Queries (SQL Agent)"):
        st.markdown("""
        - What orders are delayed?
        - Show me critical inventory items at Louisville
        - How many open exceptions are there at our Dallas warehouse?
        - What is the status of order ORD-102459?
        - Show me productivity metrics for Reno for the last 7 days
        """)
    
    with st.expander("📚 Procedures (RAG Agent)"):
        st.markdown("""
        - How do I fix a broken RF scanner?
        - What is the cycle count procedure?
        - How do I troubleshoot conveyor jams?
        - What are the replenishment rules?
        - How do I handle damaged goods?
        """)
    
    with st.expander("🌐 Weather/News (Weather Agent)"):
        st.markdown("""
        - What's the weather in Louisville today?
        - Are there any transportation delays affecting Dallas?
        - Check weather conditions in Reno
        - Are there any FedEx service alerts this week?
        """)
    
    with st.expander("🔄 Combined (Multiple Agents)"):
        st.markdown("""
        - Why is order ORD-102459 delayed and what's the escalation procedure?
        - Show me critical inventory and explain the replenishment policy
        - Are weather conditions affecting our shipments to Louisville?
        - What exceptions are open at Dallas and how should I handle them?
        """)
    
    st.markdown("---")
    
    if st.button("Clear Conversation", type="secondary"):
        st.session_state.messages = []
        if st.session_state.router:
            st.session_state.router.conversation_history = []
        st.rerun()


# Main content
st.title("🏭 Warehouse AI Assistant")
st.markdown("Ask me anything about warehouse operations, inventory, orders, or procedures.")

# Initialize router
if not st.session_state.initialized:
    with st.spinner("🔧 Initializing AI Assistant... (loading database and documents)"):
        try:
            st.session_state.router = get_router()
            st.session_state.initialized = True
            st.success("✅ Assistant ready!")
        except Exception as e:
            st.error(f"❌ Failed to initialize: {e}")
            st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Show agent badge for assistant messages
        if message["role"] == "assistant" and "agent_type" in message:
            agent_type = message["agent_type"]
            if agent_type == "SQL":
                st.markdown('<span class="agent-badge sql-agent">📊 SQL Agent</span>', unsafe_allow_html=True)
            elif agent_type == "RAG":
                st.markdown('<span class="agent-badge rag-agent">📚 RAG Agent</span>', unsafe_allow_html=True)
            elif agent_type == "WEATHER":
                st.markdown('<span class="agent-badge weather-agent">🌐 Weather Agent</span>', unsafe_allow_html=True)
            elif agent_type in ["SQL_WEATHER", "ALL", "BOTH"]:
                st.markdown('<span class="agent-badge combined-agents">🔄 Combined Agents</span>', unsafe_allow_html=True)
        
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about warehouse operations..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Classify the question first to show which agent
                agent_type = asyncio.run(st.session_state.router.classify_question(prompt))
                agent_name = agent_type.value.upper()
                
                # Show agent badge
                if agent_name == "SQL":
                    st.markdown('<span class="agent-badge sql-agent">📊 SQL Agent</span>', unsafe_allow_html=True)
                elif agent_name == "RAG":
                    st.markdown('<span class="agent-badge rag-agent">📚 RAG Agent</span>', unsafe_allow_html=True)
                elif agent_name == "WEATHER":
                    st.markdown('<span class="agent-badge weather-agent">🌐 Weather Agent</span>', unsafe_allow_html=True)
                elif agent_name in ["SQL_WEATHER", "ALL", "BOTH"]:
                    st.markdown('<span class="agent-badge combined-agents">🔄 Combined Agents</span>', unsafe_allow_html=True)
                
                # Get response
                response = asyncio.run(st.session_state.router.route_question(prompt))
                
                # Display response
                st.markdown(response)
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "agent_type": agent_name
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.875rem;'>
    <p>Powered by: OpenAI GPT-4o-mini • LangGraph • FastMCP • Tavily • SQLite</p>
    <p>Multi-Agent System: SQL Agent + RAG Agent + Weather Agent + Intelligent Router</p>
</div>
""", unsafe_allow_html=True)
