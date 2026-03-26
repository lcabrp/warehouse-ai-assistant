"""
Warehouse MCP Server - FastMCP Implementation
==============================================

This FastMCP server exposes warehouse database queries as LLM-callable tools.
Based on Unit 6 patterns: FastMCP + SQLite + Structured Outputs.

Key Design Decisions:
1. **Stateless HTTP Mode**: Scales better than stdio for production
2. **Context Injection**: Database connection managed via lifespan
3. **Structured Outputs**: Using dicts (can upgrade to Pydantic later)
4. **Read-Only Queries**: Safety - no UPDATE/DELETE operations
5. **Parameterized Queries**: SQL injection protection

Architecture:
    LLM → (tool call) → FastMCP Server → SQLite → warehouse.db
    LLM ← (results)  ← FastMCP Server ← SQLite ← warehouse.db
"""

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from ..config import settings


# ==============================================================================
# Database Connection Management
# ==============================================================================

class WarehouseDB:
    """
    Light wrapper around SQLite connection for warehouse.db.
    
    Why a wrapper?
    - Encapsulates connection logic
    - Easier to mock for testing
    - Could swap for SQLAlchemy later if needed
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(self.db_path)
        # Return rows as dictionaries for easier JSON serialization
        self.conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            query: SQL SELECT statement
            params: Query parameters (for safe parameterization)
        
        Returns:
            List of dictionaries representing rows
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        # Convert Row objects to dicts
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ==============================================================================
# FastMCP Server Setup with Lifespan Context
# ==============================================================================

@asynccontextmanager
async def lifespan(server: FastMCP):
    """
    Lifespan context manager for database connection.
    
    This pattern from Unit 6 ensures:
    1. Database connects when server starts
    2. Connection stays open during requests
    3. Database disconnects cleanly on shutdown
    
    The connection is injected into tool functions via Context parameter.
    
    Note: Using stderr for logging to avoid interfering with stdio MCP protocol.
    """
    import sys
    print(f"🔌 Connecting to warehouse database: {settings.database_path}", file=sys.stderr)
    db = WarehouseDB(str(settings.database_path))
    db.connect()
    
    try:
        # Yield the database to be available in request context
        yield {"db": db}
    finally:
        print("🔌 Closing warehouse database connection", file=sys.stderr)
        db.close()


# Initialize FastMCP server
mcp = FastMCP(
    "Warehouse Operations MCP",
    lifespan=lifespan,
    stateless_http=True,  # Production-ready mode
    json_response=True    # Return JSON for easy parsing
)


# ==============================================================================
# MCP Tools - Warehouse Database Queries
# ==============================================================================

@mcp.tool()
def search_orders(
    order_number: Optional[str] = None,
    status: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    days_back: int = 30,
    ctx: Context = None
) -> dict:
    """
    Search for orders with flexible filtering.
    
    Use this tool when the user asks about orders, shipments, or order status.
    Examples:
    - "Show me recent orders"
    - "Find order ORD-100523"
    - "What orders are delayed?"
    
    Args:
        order_number: Specific order number (e.g., 'ORD-100523')
        status: Order status (Open, Released, Shipped, Delayed, Backorder)
        warehouse_id: Filter by warehouse (1=Louisville, 2=Dallas, 3=Reno)
        days_back: How many days to look back (default: 30)
        ctx: MCP context (provides database connection)
    
    Returns:
        Dictionary with 'orders' list and 'count'
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    # Build dynamic query based on provided filters
    query = """
        SELECT 
            o.order_id,
            o.order_number,
            o.order_date,
            o.promised_ship_date,
            o.actual_ship_date,
            o.order_status,
            o.priority,
            w.warehouse_name,
            o.customer_region
        FROM orders o
        JOIN warehouses w ON o.warehouse_id = w.warehouse_id
        WHERE o.order_date >= ?
    """
    
    # Calculate date threshold
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    params = [cutoff_date]
    
    # Add optional filters
    if order_number:
        query += " AND o.order_number LIKE ?"
        params.append(f"%{order_number}%")
    
    if status:
        query += " AND o.order_status = ?"
        params.append(status)
    
    if warehouse_id:
        query += " AND o.warehouse_id = ?"
        params.append(warehouse_id)
    
    query += " ORDER BY o.order_date DESC LIMIT 50"
    
    results = db.execute_query(query, tuple(params))
    
    return {
        "orders": results,
        "count": len(results),
        "filters_applied": {
            "order_number": order_number,
            "status": status,
            "warehouse_id": warehouse_id,
            "days_back": days_back
        }
    }


@mcp.tool()
def get_order_details(order_number: str, ctx: Context = None) -> dict:
    """
    Get complete details for a specific order including line items.
    
    Use this when the user asks for details about a specific order.
    Examples:
    - "Tell me about order ORD-100523"
    - "What items are in order ORD-105000?"
    
    Args:
        order_number: The order number (e.g., 'ORD-100523')
        ctx: MCP context
    
    Returns:
        Dictionary with order header and line items
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    # Get order header
    header_query = """
        SELECT 
            o.*,
            w.warehouse_name,
            w.warehouse_code
        FROM orders o
        JOIN warehouses w ON o.warehouse_id = w.warehouse_id
        WHERE o.order_number = ?
    """
    header = db.execute_query(header_query, (order_number,))
    
    if not header:
        return {"error": f"Order {order_number} not found"}
    
    # Get order lines
    lines_query = """
        SELECT 
            ol.order_line_id,
            ol.ordered_qty,
            ol.shipped_qty,
            ol.backordered_qty,
            ol.line_status,
            i.sku,
            i.item_name,
            i.category
        FROM order_lines ol
        JOIN items i ON ol.item_id = i.item_id
        WHERE ol.order_id = ?
    """
    lines = db.execute_query(lines_query, (header[0]["order_id"],))
    
    return {
        "order": header[0],
        "line_items": lines,
        "total_lines": len(lines)
    }


@mcp.tool()
def check_inventory(
    item_sku: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    status: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Check current inventory levels across warehouses.
    
    Use this when the user asks about stock, inventory, or availability.
    Examples:
    - "What's the inventory for SKU APP-10500?"
    - "Show me low stock items"
    - "Check inventory at Dallas warehouse"
    
    Args:
        item_sku: Specific item SKU (e.g., 'APP-10500')
        warehouse_id: Filter by warehouse (1, 2, or 3)
        status: Inventory status (CRITICAL, LOW, OK, OVERSTOCK)
        ctx: MCP context
    
    Returns:
        Dictionary with inventory records
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    query = """
        SELECT 
            inv.inventory_id,
            inv.snapshot_date,
            i.sku,
            i.item_name,
            i.category,
            w.warehouse_name,
            inv.on_hand_qty,
            inv.allocated_qty,
            inv.available_qty,
            inv.inbound_qty,
            inv.inventory_status,
            l.bin_code
        FROM inventory inv
        JOIN items i ON inv.item_id = i.item_id
        JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
        LEFT JOIN locations l ON inv.location_id = l.location_id
        WHERE 1=1
    """
    
    params = []
    
    if item_sku:
        query += " AND i.sku LIKE ?"
        params.append(f"%{item_sku}%")
    
    if warehouse_id:
        query += " AND inv.warehouse_id = ?"
        params.append(warehouse_id)
    
    if status:
        query += " AND inv.inventory_status = ?"
        params.append(status)
    
    query += " ORDER BY inv.inventory_status DESC, inv.on_hand_qty ASC LIMIT 100"
    
    results = db.execute_query(query, tuple(params))
    
    return {
        "inventory_records": results,
        "count": len(results)
    }


@mcp.tool()
def get_shipment_status(order_number: Optional[str] = None, delayed_only: bool = False, ctx: Context = None) -> dict:
    """
    Get shipment tracking information and identify delays.
    
    Use this when the user asks about shipments, tracking, or delays.
    Examples:
    - "Show me delayed shipments"
    - "What's the tracking number for order ORD-100523?"
    - "Which carrier is used for order X?"
    
    Args:
        order_number: Specific order number to look up
        delayed_only: If True, only show shipments that are delayed
        ctx: MCP context
    
    Returns:
        Dictionary with shipment records
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    query = """
        SELECT 
            s.shipment_id,
            s.tracking_number,
            s.carrier,
            s.planned_date,
            s.actual_date,
            s.delay_flag,
            o.order_number,
            o.customer_region,
            o.priority
        FROM shipments s
        JOIN orders o ON s.order_id = o.order_id
        WHERE 1=1
    """
    
    params = []
    
    if order_number:
        query += " AND o.order_number = ?"
        params.append(order_number)
    
    if delayed_only:
        query += " AND s.delay_flag = 1"
    
    query += " ORDER BY s.actual_date DESC LIMIT 50"
    
    results = db.execute_query(query, tuple(params))
    
    return {
        "shipments": results,
        "count": len(results),
        "delayed_count": sum(1 for r in results if r.get("delay_flag") == 1)
    }


@mcp.tool()
def get_exceptions(
    severity: Optional[str] = None,
    exception_type: Optional[str] = None,
    status: Optional[str] = None,
    days_back: int = 7,
    ctx: Context = None
) -> dict:
    """
    Query operational exceptions (problems that occurred in the warehouse).
    
    Use this when the user asks about problems, errors, or issues.
    Examples:
    - "What exceptions happened today?"
    - "Show me critical issues"
    - "Are there any scanner problems?"
    
    Args:
        severity: Filter by severity (Low, Medium, High, Critical)
        exception_type: Type of exception (Low Stock, Delayed Shipment, Scanner Issue, etc.)
        status: Exception status (Open, In Progress, Resolved)
        days_back: How many days to look back (default: 7)
        ctx: MCP context
    
    Returns:
        Dictionary with exception records
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    query = """
        SELECT 
            e.exception_id,
            e.exception_type,
            e.severity,
            e.exception_status,
            e.created_at,
            e.resolved_at,
            e.notes,
            w.warehouse_name,
            i.sku,
            o.order_number
        FROM exceptions e
        JOIN warehouses w ON e.warehouse_id = w.warehouse_id
        LEFT JOIN items i ON e.item_id = i.item_id
        LEFT JOIN orders o ON e.order_id = o.order_id
        WHERE e.created_at >= ?
    """
    
    params = [cutoff_date]
    
    if severity:
        query += " AND e.severity = ?"
        params.append(severity)
    
    if exception_type:
        query += " AND e.exception_type = ?"
        params.append(exception_type)
    
    if status:
        query += " AND e.exception_status = ?"
        params.append(status)
    
    query += " ORDER BY e.severity DESC, e.created_at DESC LIMIT 50"
    
    results = db.execute_query(query, tuple(params))
    
    return {
        "exceptions": results,
        "count": len(results)
    }


@mcp.tool()
def get_labor_metrics(
    employee_name: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    days_back: int = 7,
    ctx: Context = None
) -> dict:
    """
    Query labor productivity metrics for warehouse employees.
    
    Use this when the user asks about employee performance, productivity, or picking efficiency.
    Examples:
    - "How is John Smith performing?"
    - "Show me picking productivity"
    - "Who are the top pickers?"
    
    Args:
        employee_name: Specific employee name
        warehouse_id: Filter by warehouse
        days_back: How many days to look back (default: 7)
        ctx: MCP context
    
    Returns:
        Dictionary with labor metrics and aggregated statistics
    """
    db: WarehouseDB = ctx.request_context.lifespan_context["db"]
    
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    query = """
        SELECT 
            lm.metric_id,
            lm.employee_name,
            lm.task_type,
            lm.units_processed,
            lm.start_time,
            lm.end_time,
            lm.error_count,
            w.warehouse_name,
            -- Calculate duration in minutes
            CAST((julianday(lm.end_time) - julianday(lm.start_time)) * 24 * 60 AS INTEGER) as duration_minutes
        FROM labor_metrics lm
        JOIN warehouses w ON lm.warehouse_id = w.warehouse_id
        WHERE lm.start_time >= ?
    """
    
    params = [cutoff_date]
    
    if employee_name:
        query += " AND lm.employee_name LIKE ?"
        params.append(f"%{employee_name}%")
    
    if warehouse_id:
        query += " AND lm.warehouse_id = ?"
        params.append(warehouse_id)
    
    query += " ORDER BY lm.start_time DESC LIMIT 100"
    
    results = db.execute_query(query, tuple(params))
    
    # Calculate aggregate statistics
    if results:
        total_units = sum(r["units_processed"] for r in results)
        total_errors = sum(r["error_count"] for r in results)
        total_minutes = sum(r["duration_minutes"] for r in results)
        avg_units_per_hour = (total_units / total_minutes * 60) if total_minutes > 0 else 0
    else:
        total_units = total_errors = total_minutes = avg_units_per_hour = 0
    
    return {
        "metrics": results,
        "count": len(results),
        "summary": {
            "total_units_processed": total_units,
            "total_errors": total_errors,
            "average_units_per_hour": round(avg_units_per_hour, 2)
        }
    }


# ==============================================================================
# Starlette App Export
# ==============================================================================

# Export the Starlette app (this is what gets mounted in production)
# Using streamable_http_app from FastMCP for HTTP-based MCP protocol
app = mcp.streamable_http_app

# For development/testing
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting Warehouse MCP Server on http://{settings.mcp_host}:{settings.mcp_port}")
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
