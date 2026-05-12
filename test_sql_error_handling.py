"""
Test Script for SQL Agent Error Handling
=========================================

Tests the granular error handling added to the SQL agent and WarehouseDB.
Validates that specific database errors are caught and translated into
appropriate user-facing error messages.

Run this script to verify error handling behavior before connecting to agents.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.warehouse_mcp import (
    WarehouseDB,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseQueryTimeoutError,
)
from src.config import settings


def test_connection_error():
    """Test DatabaseConnectionError handling."""
    print("=" * 70)
    print("TEST 1: Connection Error - Invalid Database Path")
    print("=" * 70)
    
    try:
        db = WarehouseDB("/nonexistent/path/database.db")
        db.connect()
        print("❌ FAILED: Should have raised DatabaseConnectionError")
        return False
    except DatabaseConnectionError as e:
        print(f"✅ PASSED: Correctly raised DatabaseConnectionError")
        print(f"   Error message: {e}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Raised wrong exception type: {type(e).__name__}")
        print(f"   Error: {e}")
        return False


def test_valid_connection():
    """Test successful connection."""
    print("\n" + "=" * 70)
    print("TEST 2: Valid Connection")
    print("=" * 70)
    
    if not settings.database_path.exists():
        print(f"⚠️  SKIPPED: Database not found at {settings.database_path}")
        print("   Run 'python generate_data.py' to create test database")
        return True
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        print(f"✅ PASSED: Successfully connected to database")
        print(f"   Database path: {settings.database_path}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: Connection failed: {e}")
        return False


def test_query_error():
    """Test DatabaseQueryError handling - malformed query."""
    print("\n" + "=" * 70)
    print("TEST 3: Query Error - Invalid SQL Syntax")
    print("=" * 70)
    
    if not settings.database_path.exists():
        print(f"⚠️  SKIPPED: Database not found")
        return True
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        
        # Try to execute invalid SQL
        try:
            db.execute_query("SELECT * FROM nonexistent_table WHERE invalid syntax")
            print("❌ FAILED: Should have raised DatabaseQueryError")
            return False
        except DatabaseQueryError as e:
            print(f"✅ PASSED: Correctly raised DatabaseQueryError")
            print(f"   Error message: {e}")
            print(f"   SQL Error detail: {e.sql_error}")
            return True
        finally:
            db.close()
    
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {type(e).__name__}: {e}")
        return False


def test_valid_query():
    """Test successful query execution."""
    print("\n" + "=" * 70)
    print("TEST 4: Valid Query Execution")
    print("=" * 70)
    
    if not settings.database_path.exists():
        print(f"⚠️  SKIPPED: Database not found")
        return True
    
    try:
        db = WarehouseDB(str(settings.database_path))
        db.connect()
        
        # Execute a simple valid query
        results = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"
        )
        
        print(f"✅ PASSED: Successfully executed query")
        print(f"   Returned {len(results)} results")
        if results:
            print(f"   Sample tables: {[r.get('name', 'N/A') for r in results[:3]]}")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ FAILED: Query failed: {type(e).__name__}: {e}")
        return False


def test_connection_not_established():
    """Test error when query attempted without connection."""
    print("\n" + "=" * 70)
    print("TEST 5: Connection Not Established Error")
    print("=" * 70)
    
    try:
        db = WarehouseDB(str(settings.database_path))
        # Don't call connect() - connection is not established
        
        try:
            db.execute_query("SELECT 1")
            print("❌ FAILED: Should have raised DatabaseConnectionError")
            return False
        except DatabaseConnectionError as e:
            print(f"✅ PASSED: Correctly raised DatabaseConnectionError")
            print(f"   Error message: {e}")
            return True
    
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  SQL Agent Error Handling - Test Suite".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    tests = [
        ("Connection Error", test_connection_error),
        ("Valid Connection", test_valid_connection),
        ("Query Error", test_query_error),
        ("Valid Query", test_valid_query),
        ("No Connection Error", test_connection_not_established),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {test_name}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
