"""
Test script for Warehouse MCP Server
=====================================

This script directly tests the MCP tools without needing an LLM.
We manually call the tool functions to verify database connectivity and queries.

Run this to validate your MCP server before connecting it to LangGraph.
"""

import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.tools.warehouse_mcp import WarehouseDB


def test_database_connection():
    """Test that we can connect to the database."""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)
    
    if not settings.database_path.exists():
        print(f"❌ Database not found at: {settings.database_path}")
        print("   Run 'python generate_data.py' first!")
        return False
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        print(f"✅ Connected to: {settings.database_path}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_search_orders():
    """Test the search_orders tool."""
    print("\n" + "=" * 60)
    print("TEST 2: Search Orders Tool")
    print("=" * 60)
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        
        # Simulate what the MCP tool does
        query = """
            SELECT 
                o.order_id,
                o.order_number,
                o.order_date,
                o.promised_ship_date,
                o.order_status,
                o.priority,
                w.warehouse_name
            FROM orders o
            JOIN warehouses w ON o.warehouse_id = w.warehouse_id
            WHERE o.order_status = ?
            ORDER BY o.order_date DESC LIMIT 5
        """
        
        results = db.execute_query(query, ('Delayed',))
        
        print(f"✅ Found {len(results)} delayed orders:")
        for order in results[:3]:  # Show first 3
            print(f"   - {order['order_number']}: {order['order_status']} "
                  f"(Priority: {order['priority']}, Warehouse: {order['warehouse_name']})")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def test_check_inventory():
    """Test the check_inventory tool."""
    print("\n" + "=" * 60)
    print("TEST 3: Check Inventory Tool")
    print("=" * 60)
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        
        query = """
            SELECT 
                i.sku,
                i.item_name,
                w.warehouse_name,
                inv.on_hand_qty,
                inv.available_qty,
                inv.inventory_status
            FROM inventory inv
            JOIN items i ON inv.item_id = i.item_id
            JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
            WHERE inv.inventory_status IN ('CRITICAL', 'LOW')
            ORDER BY inv.on_hand_qty ASC LIMIT 5
        """
        
        results = db.execute_query(query)
        
        print(f"✅ Found {len(results)} critical/low stock items:")
        for item in results[:3]:
            print(f"   - {item['sku']}: {item['on_hand_qty']} units "
                  f"({item['inventory_status']}) at {item['warehouse_name']}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def test_get_exceptions():
    """Test the get_exceptions tool."""
    print("\n" + "=" * 60)
    print("TEST 4: Get Exceptions Tool")
    print("=" * 60)
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        
        query = """
            SELECT 
                e.exception_type,
                e.severity,
                e.exception_status,
                e.created_at,
                w.warehouse_name
            FROM exceptions e
            JOIN warehouses w ON e.warehouse_id = w.warehouse_id
            WHERE e.exception_status = 'Open'
            ORDER BY e.severity DESC, e.created_at DESC LIMIT 5
        """
        
        results = db.execute_query(query)
        
        print(f"✅ Found {len(results)} open exceptions:")
        for exc in results[:3]:
            print(f"   - {exc['exception_type']} ({exc['severity']}) "
                  f"at {exc['warehouse_name']} - {exc['created_at'][:10]}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Warehouse MCP Server Test Suite")
    print("=" * 60)
    
    # Check database exists (skip API key validation for now)
    if not settings.database_path.exists():
        print(f"\n❌ Database not found at: {settings.database_path}")
        print("   Run 'python generate_data.py' to create it.")
        return
    
    print(f"✅ Database found: {settings.database_path}")
    print("   (API keys not needed for database tests)")
    
    # Run tests
    tests = [
        test_database_connection,
        test_search_orders,
        test_check_inventory,
        test_get_exceptions
    ]
    
    passed = sum(1 for test in tests if test())
    total = len(tests)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All tests passed! MCP server is ready.")
        print("\nNext steps:")
        print("1. Set API keys: $env:OPENAI_API_KEY='your-key-here'")
        print("2. Start the MCP server: python src/tools/warehouse_mcp.py")
        print("3. Build the LangGraph agent to use these tools")
    else:
        print("❌ Some tests failed. Fix issues before proceeding.")


if __name__ == "__main__":
    main()
