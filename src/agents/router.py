"""  
Warehouse AI Assistant Router
==============================

This router determines which agent(s) should handle a user question:
- SQL Agent: For data queries (orders, inventory, shipments, metrics)
- RAG Agent: For procedural questions (how-to, troubleshooting, policies)
- Weather Agent: For external information (weather, news, transportation disruptions)
- Combined: For questions requiring multiple agents

Architecture (Based on Unit 7 Multi-Agent Pattern):
    User Question
        ↓
    [Router / Classifier]
        ↓
    Decision:
    - SQL only → SQL Agent → Answer
    - RAG only → RAG Agent → Answer
    - Weather only → Weather Agent → Answer
    - Combined → Multiple Agents → Synthesize → Answer

Key Design:
- Uses LLM to classify questions (not regex/keywords)
- Maintains conversation history
- Can call multiple agents together if needed
- Token management applied throughout
"""

import asyncio
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..agents.sql_agent import create_sql_agent
from ..agents.rag_agent import create_rag_agent
from ..agents.weather_agent import create_weather_agent


# ==============================================================================
# Agent Type Classification
# ==============================================================================

class AgentType(Enum):
    """Types of agents that can handle questions."""
    SQL = "sql"
    RAG = "rag"
    WEATHER = "weather"
    SQL_WEATHER = "sql_weather"  # Data + weather correlation
    ALL = "all"  # SQL + RAG + Weather


# ==============================================================================
# Router Class
# ==============================================================================

class WarehouseRouter:
    """
    Routes questions to appropriate agent(s).
    
    This is the entry point for the entire warehouse AI assistant.
    Users interact with this, and it decides which specialized agent to use.
    """
    
    def __init__(self):
        """Initialize the router."""
        self.classifier_llm = None
        self.sql_agent = None
        self.rag_agent = None
        self.weather_agent = None
        self.conversation_history = []
        
    async def initialize(self):
        """
        Async initialization to set up classifier and agents.
        
        Steps:
        1. Initialize classifier LLM (for routing decisions)
        2. Initialize SQL agent
        3. Initialize RAG agent
        4. Initialize Weather agent (Tavily)
        """
        print("🔧 Initializing Warehouse AI Assistant Router...")
        print("=" * 60)
        
        # 1. Classifier LLM - used to decide which agent to use
        # Temperature 0 for consistent classification
        self.classifier_llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
        )
        print("✅ Classifier LLM initialized")
        
        # 2. Initialize SQL agent
        print("\n📊 Initializing SQL Agent...")
        self.sql_agent = await create_sql_agent()
        
        # 3. Initialize RAG agent  
        print("\n📚 Initializing RAG Agent...")
        self.rag_agent = await create_rag_agent()
        
        # 4. Initialize Weather agent (Tavily)
        print("\n🌐 Initializing Weather/Web Search Agent...")
        try:
            self.weather_agent = await create_weather_agent()
        except Exception as e:
            print(f"   ⚠️  Weather agent initialization failed: {e}")
            print(f"   Continuing without weather capabilities.")
            self.weather_agent = None
        
        print("\n" + "=" * 60)
        print("✅ Warehouse AI Assistant is ready!")
        print()
    
    async def classify_question(self, question: str) -> AgentType:
        """
        Classify which agent should handle the question.
        
        Uses LLM to intelligently decide based on question content.
        This is better than keyword matching because it understands context.
        
        Args:
            question: User's question
        
        Returns:
            AgentType indicating which agent(s) to use
        """
        # Build context from recent conversation history
        context_info = ""
        if self.conversation_history:
            recent_history = self.conversation_history[-3:]  # Last 3 exchanges
            context_info = "\n\nRECENT CONVERSATION CONTEXT:\n"
            for i, entry in enumerate(recent_history, 1):
                context_info += f"{i}. Q: {entry['question']} → Routed to: {entry['agent'].upper()}\n"
            context_info += "\nIMPORTANT: If the current question is a follow-up (like 'What about X?' or 'How about Y?'), maintain the same agent type unless the context clearly changes.\n"
        
        # System prompt that guides classification
        classification_prompt = SystemMessage(content=f"""You are a question classifier for a warehouse operations AI assistant.

You have three specialized agents available:

1. **SQL Agent** - Queries warehouse database for:
   - Order information and status
   - Inventory levels and locations
   - Shipment tracking and delays
   - Operational exceptions (issues, problems)
   - Labor metrics and productivity
   - Any question requiring specific DATA from the system

2. **RAG Agent** - Searches warehouse procedures/documentation for:
   - How-to procedures (cycle counts, replenishment)
   - Troubleshooting guides (equipment, scanners, conveyors)
   - Policies and guidelines
   - Operational procedures
   - Any question about HOW to do something

3. **WEATHER Agent** - Searches web for external information:
   - Current weather conditions in specific locations
   - News about transportation disruptions or delays
   - Carrier service alerts or issues
   - Regional events affecting shipments
   - Any question requiring CURRENT EXTERNAL information

4. **SQL_WEATHER** - Questions combining internal data with weather:
   - "Why are deliveries to Chicago delayed?" (needs order data + weather)
   - "Are shipments affected by weather?" (needs shipment data + weather check)

5. **ALL** - Questions requiring data + procedures + weather:
   - Complex questions needing all three sources

Classification Rules:
- Use WEATHER for questions about weather, news, or external conditions
- Use SQL_WEATHER when you need to correlate order/shipment data with weather
- Use SQL for pure data queries (no weather context)
- Use RAG for procedural questions
- Use ALL only when explicitly needing all three sources
- For follow-up questions ("What about X?", "How about Y?"), maintain context from previous question{context_info}

Respond with ONLY ONE WORD: "SQL" or "RAG" or "WEATHER" or "SQL_WEATHER" or "ALL"
""")
        
        # Ask classifier to categorize
        user_message = HumanMessage(content=f"Classify this question: {question}")
        
        response = await self.classifier_llm.ainvoke([classification_prompt, user_message])
        
        # Parse response
        classification = response.content.strip().upper()
        
        if "ALL" in classification:
            return AgentType.ALL
        elif "SQL_WEATHER" in classification or "SQL WEATHER" in classification:
            return AgentType.SQL_WEATHER
        elif "SQL" in classification:
            return AgentType.SQL
        elif "RAG" in classification:
            return AgentType.RAG
        elif "WEATHER" in classification:
            return AgentType.WEATHER
        else:
            # Default to RAG for unclear cases (safer than SQL)
            return AgentType.RAG
    
    async def route_question(self, question: str) -> str:
        """
        Main routing logic - classify and forward to appropriate agent(s).
        
        Args:
            question: User's question
        
        Returns:
            Agent's answer
        
        Flow:
        1. Classify question
        2. Route to agent(s)
        3. Get answer(s)
        4. Synthesize if needed (for combined cases)
        5. Return final answer
        """
        # 1. Classify
        agent_type = await self.classify_question(question)
        
        # Store in conversation history
        self.conversation_history.append({
            'question': question,
            'agent': agent_type.value
        })
        
        # Keep only recent history (last 10 exchanges)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        print(f"🎯 Routing to: {agent_type.value.upper()} agent(s)")
        print()
        
        # 2. Route to appropriate agent(s)
        if agent_type == AgentType.SQL:
            answer = await self._execute_sql(question)
            
        elif agent_type == AgentType.RAG:
            answer = await self._execute_rag(question)
            
        elif agent_type == AgentType.WEATHER:
            answer = await self._execute_weather(question)
            
        elif agent_type == AgentType.SQL_WEATHER:
            # Correlate database data with weather info
            print("📊 Getting data from SQL Agent...")
            sql_answer = await self._execute_sql(question)
            
            print("🌐 Getting weather/news information...")
            weather_answer = await self._execute_weather(question)
            
            # Synthesize both answers
            answer = await self._synthesize_multiple(
                question, 
                {
                    "Database Data": sql_answer,
                    "Weather/External Info": weather_answer
                }
            )
            
        elif agent_type == AgentType.ALL:
            # Call all three agents
            print("📊 Getting data from SQL Agent...")
            sql_answer = await self._execute_sql(question)
            
            print("📚 Getting procedures from RAG Agent...")
            rag_answer = await self._execute_rag(question)
            
            print("🌐 Getting weather/news information...")
            weather_answer = await self._execute_weather(question)
            
            # Synthesize all answers
            answer = await self._synthesize_multiple(
                question,
                {
                    "Database Data": sql_answer,
                    "Procedures/Documentation": rag_answer,
                    "Weather/External Info": weather_answer
                }
            )
        
        return answer
    
    async def _execute_sql(self, question: str) -> str:
        """Execute SQL agent query."""
        return await self.sql_agent.query(question)
    
    async def _execute_rag(self, question: str) -> str:
        """Execute RAG agent query."""
        return await self.rag_agent.query(question)
    
    async def _execute_weather(self, question: str) -> str:
        """Execute Weather agent query."""
        if not self.weather_agent:
            return "Weather information is currently unavailable (Tavily API key not configured)."
        
        # Create message for weather agent
        from langgraph.graph import MessagesState
        
        state = {"messages": [HumanMessage(content=question)]}
        result = await self.weather_agent.ainvoke(state)
        
        # Extract the final answer from the messages
        if result and "messages" in result:
            for msg in reversed(result["messages"]):
                # Look for AI message that's the final answer (not a tool call)
                if msg.type == "ai":
                    # Check if this message has tool_calls
                    has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls
                    if not has_tool_calls and msg.content:
                        return msg.content
        
        return "No weather information found."
    
    async def _synthesize_multiple(self, question: str, sources: dict) -> str:
        """
        Synthesize answers from multiple agents into a coherent response.
        
        Args:
            question: Original question
            sources: Dictionary of source_name -> answer pairs
        
        Returns:
            Synthesized answer combining all sources
        """
        # Build the synthesis prompt with all sources
        sources_text = "\n\n".join([
            f"**{source_name}:**\n{answer}"
            for source_name, answer in sources.items()
        ])
        
        synthesis_prompt = f"""You are synthesizing information from multiple sources to answer a user's question.

User's Question: {question}

{sources_text}

Combine these pieces of information into a single, coherent answer that:
1. Directly answers the user's question
2. Integrates all relevant information naturally
3. Is well-organized and easy to understand
4. Cites sources appropriately (e.g., "According to our database...", "Based on current weather...")
5. Highlights any correlations (e.g., if shipments are delayed AND weather is bad)

Provide a comprehensive answer:"""
        
        response = await self.classifier_llm.ainvoke([HumanMessage(content=synthesis_prompt)])
        return response.content
    
    async def chat(self, message: str) -> str:
        """
        Main chat interface with conversation history.
        
        Args:
            message: User's message
        
        Returns:
            Assistant's response
        """
        # Route question and get answer
        # (conversation history is tracked inside route_question)
        answer = await self.route_question(message)
        
        return answer


# ==============================================================================
# Helper Functions
# ==============================================================================

async def create_router() -> WarehouseRouter:
    """
    Factory function to create and initialize router.
    
    Usage:
        router = await create_router()
        answer = await router.chat("What orders are delayed?")
    """
    router = WarehouseRouter()
    await router.initialize()
    return router


# ==============================================================================
# CLI Test Interface
# ==============================================================================

async def main():
    """Test the router with various question types."""
    print("=" * 60)
    print("Warehouse AI Assistant Router - Test")
    print("=" * 60)
    print()
    
    # Create router (initializes both agents)
    router = await create_router()
    
    # Test questions covering different agent types
    test_questions = [
        # SQL questions
        ("What orders are delayed?", "Should route to SQL"),
        ("Show me critical inventory items", "Should route to SQL"),
        
        # RAG questions
        ("How do I fix a broken RF scanner?", "Should route to RAG"),
        ("What is the cycle count procedure?", "Should route to RAG"),
        
        # BOTH questions
        ("Why is order ORD-102459 delayed and what's the escalation procedure?", "Should route to BOTH"),
    ]
    
    for question, expected in test_questions:
        print("\n" + "=" * 60)
        print(f"🔍 Question: {question}")
        print(f"   Expected: {expected}")
        print("-" * 60)
        
        try:
            answer = await router.chat(question)
            print(f"💡 Answer:\n{answer}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Router Test Complete")


if __name__ == "__main__":
    asyncio.run(main())
