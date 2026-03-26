"""
MCP Server Launcher
===================
Simple wrapper to launch the warehouse MCP server.
This file exists at the root level for easy subprocess launching.
"""

if __name__ == "__main__":
    # Import and run the MCP server
    from src.tools.warehouse_mcp import mcp
    import asyncio
    
    # Run the MCP server in stdio mode (for subprocess communication)
    asyncio.run(mcp.run_stdio_async())
