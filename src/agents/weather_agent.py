"""
Weather & Web Search Agent - Tavily Integration
================================================

This agent uses Tavily's web search to gather external information:
- Weather conditions that might affect shipments
- News about transportation disruptions
- Regional events impacting deliveries
- Carrier delays or issues

Based on Unit 7 Lab patterns: Multi-agent with web search tools.

Architecture:
    User Question about weather/delays
        ↓
    [Tavily Search Tool] → Web Search → Real-time info
        ↓
    Agent formats answer with sources
"""

import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tavily import TavilyClient

from ..config import settings


# ==============================================================================
# Tavily Search Tool
# ==============================================================================

def create_tavily_search_tool():
    """
    Create a Tavily search tool for weather and transportation info.
    
    Returns:
        Callable tool that the agent can use for web searches
    """
    from langchain_core.tools import tool
    
    # Initialize Tavily client using settings
    tavily_api_key = settings.tavily_api_key
    if not tavily_api_key or tavily_api_key == "your-tavily-api-key-here":
        raise ValueError(
            "TAVILY_API_KEY not set in .env file. "
            "Get your API key from: https://app.tavily.com/"
        )
    
    tavily_client = TavilyClient(api_key=tavily_api_key)
    
    @tool
    def search_web(query: str) -> str:
        """
        Search the web for current information about weather, news, or transportation.
        
        Use this tool to find:
        - Current weather conditions in specific locations
        - News about transportation delays or disruptions  
        - Carrier service issues or alerts
        - Regional events affecting deliveries
        
        Args:
            query: The search query (e.g., "weather in Chicago today", 
                   "FedEx delays March 2026", "highway closures California")
        
        Returns:
            Formatted search results with sources
        """
        try:
            # Use Tavily's advanced search
            results = tavily_client.search(
                query=query,
                search_depth="advanced",  # More comprehensive results
                max_results=5,
                include_answer=True,  # Get Tavily's AI-generated summary
            )
            
            # Format the response
            response_parts = []
            
            # Add Tavily's AI summary if available
            if results.get('answer'):
                response_parts.append(f"**Summary:** {results['answer']}\n")
            
            # Add top search results
            if results.get('results'):
                response_parts.append("**Sources:**")
                for i, result in enumerate(results['results'][:3], 1):
                    title = result.get('title', 'No title')
                    content = result.get('content', '')[:200]  # First 200 chars
                    url = result.get('url', '')
                    response_parts.append(
                        f"\n{i}. **{title}**\n   {content}...\n   Source: {url}"
                    )
            
            return "\n".join(response_parts) if response_parts else "No results found."
            
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    return search_web


# ==============================================================================
# Weather Agent Creation
# ==============================================================================

async def create_weather_agent():
    """
    Create weather/web search agent with Tavily tool.
    
    This agent can:
    - Search for current weather conditions
    - Find news about transportation disruptions
    - Research carrier delays or issues
    - Provide context for why shipments might be delayed
    
    Returns:
        Configured LangChain ReAct agent with Tavily search
    """
    print("🌐 Initializing Weather/Web Search Agent (Tavily)...")
    
    # Initialize LLM for weather agent
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0.3,  # Balanced: factual but can interpret results
    )
    
    # Create Tavily search tool
    try:
        tavily_tool = create_tavily_search_tool()
        tools = [tavily_tool]
    except ValueError as e:
        print(f"   ⚠️  Warning: {e}")
        print(f"   Weather agent will be created without search capability.")
        tools = []
    
    # System prompt for weather agent
    system_prompt = """You are a weather and transportation information specialist for warehouse operations.

Your job is to search the web for current information that might explain shipment delays:

1. **Weather Conditions**: Search for weather in specific cities/regions affecting deliveries
2. **Transportation News**: Find news about highway closures, carrier delays, or disruptions
3. **Regional Events**: Discover events (storms, strikes, etc.) impacting logistics

**When using search results:**
- Always cite your sources (include URLs)
- Provide current, factual information
- Explain how the information relates to warehouse operations
- If asked about specific orders, combine weather info with order context

**Example Queries You Might Handle:**
- "What's the weather in Chicago?" → Search and report current conditions
- "Are there any FedEx delays?" → Search for carrier service alerts
- "Why might deliveries to California be delayed?" → Search for weather/news in California

**Important:**
- Use the search_web tool for current information
- Don't make up weather data - always search first
- Clearly indicate when information is from web search
"""
    
    # Create agent using same pattern as SQL and RAG agents  
    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    
    print(f"   ✅ Weather agent ready with {len(tools)} tool(s)")
    print(f"   🔍 Can search web: {'Yes' if tools else 'No (Tavily key missing)'}")
    
    return agent


# ==============================================================================
# Helper Function for Direct Weather Queries
# ==============================================================================

async def get_weather_info(location: str) -> str:
    """
    Quick helper to get weather for a specific location.
    
    Args:
        location: City or region (e.g., "Chicago", "Southern California")
    
    Returns:
        Weather information or error message
    """
    try:
        tavily_tool = create_tavily_search_tool()
        query = f"current weather in {location}"
        result = tavily_tool.invoke(query)
        return result
    except Exception as e:
        return f"Could not retrieve weather: {str(e)}"
