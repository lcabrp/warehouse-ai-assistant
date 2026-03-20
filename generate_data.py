import sqlite3
import random
from datetime import datetime, timedelta
import os

# ==============================================================================
# AI Warehouse Operations Assistant - Synthetic Data Generator
# ==============================================================================
#
# WHY PARAMETERS & SCALE?
# By parameterizing the script, we can govern the exact data volume. 
# While 30 locations is a tiny sandbox, a real small/mid-size operational 
# warehouse has thousands of active SKUs and locations across Pick and Bulk zones.
#
# The defaults below represent a realistic "mid-size" operation (2,000 items,
# combined 6,000 storage locations, and 10,000 active/historical orders).
# This perfectly mimics real complexity while keeping the local warehouse.db 
# file small enough (~15-25MB) to easily commit to GitHub without breaking limits.
# ==============================================================================

DB_PATH = "data/warehouse.db"

def setup_database(
    num_items=2000,           # Represents a healthy small/mid-size SKU catalog
    num_locations_per_wh=2000,# ~6,000 total locations across the network
    num_orders=10000,         # Plenty of historical depth for the AI to query
    num_exceptions=500        # Enough variety to test the Synthesizer logic
):
    """
    Creates the complete 7-table schema and generates interconnected synthetic 
    operational data scaled to mimic a mid-size real-world warehouse.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Initializing Database Schema...")
    cur.executescript("""
        DROP TABLE IF EXISTS exceptions;
        DROP TABLE IF EXISTS order_lines;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS inventory;
        DROP TABLE IF EXISTS items;
        DROP TABLE IF EXISTS locations;
        DROP TABLE IF EXISTS warehouses;

        CREATE TABLE warehouses (
            warehouse_id INTEGER PRIMARY KEY,
            warehouse_code TEXT UNIQUE,
            warehouse_name TEXT,
            city TEXT,
            state TEXT,
            timezone TEXT,
            is_active INTEGER
        );

        CREATE TABLE locations (
            location_id INTEGER PRIMARY KEY,
            warehouse_id INTEGER,
            zone TEXT,
            aisle TEXT,
            bay TEXT,
            level TEXT,
            bin_code TEXT,
            location_type TEXT,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        );

        CREATE TABLE items (
            item_id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE,
            item_name TEXT,
            category TEXT,
            unit_cost REAL,
            reorder_point INTEGER,
            safety_stock INTEGER,
            supplier_name TEXT,
            is_active INTEGER
        );

        CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY,
            snapshot_date TEXT,
            warehouse_id INTEGER,
            location_id INTEGER,
            item_id INTEGER,
            on_hand_qty INTEGER,
            allocated_qty INTEGER,
            available_qty INTEGER,
            inbound_qty INTEGER,
            inventory_status TEXT,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
            FOREIGN KEY (location_id) REFERENCES locations(location_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            order_number TEXT UNIQUE,
            warehouse_id INTEGER,
            order_date TEXT,
            promised_ship_date TEXT,
            actual_ship_date TEXT,
            customer_region TEXT,
            priority TEXT,
            order_status TEXT,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        );

        CREATE TABLE order_lines (
            order_line_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            item_id INTEGER,
            ordered_qty INTEGER,
            shipped_qty INTEGER,
            backordered_qty INTEGER,
            line_status TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        );

        CREATE TABLE exceptions (
            exception_id INTEGER PRIMARY KEY,
            warehouse_id INTEGER,
            item_id INTEGER,
            order_id INTEGER,
            exception_type TEXT,
            severity TEXT,
            created_at TEXT,
            resolved_at TEXT,
            exception_status TEXT,
            notes TEXT,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    """)

    print("Generating Warehouses, Locations, and Items...")
    warehouses = [
        (1, 'SDF1', 'Louisville Hub', 'Louisville', 'KY', 'EST', 1),
        (2, 'DFW1', 'Dallas Fulfillment', 'Dallas', 'TX', 'CST', 1),
        (3, 'RNO1', 'Reno Distribution', 'Reno', 'NV', 'PST', 1)
    ]
    cur.executemany("INSERT INTO warehouses VALUES (?, ?, ?, ?, ?, ?, ?)", warehouses)

    zones = ['A', 'BULK', 'PACK', 'PICK', 'STAGE']
    location_types = ['PICK', 'BULK', 'STAGE', 'PACK']
    locations = []
    loc_id = 1
    
    # Pre-bucketing locations by warehouse so the inventory loop is incredibly fast O(1) 
    # instead of doing a list comprehension O(N) 3 * 2000 times.
    locations_by_wh = {1: [], 2: [], 3: []}

    for w in warehouses:
        w_id = w[0]
        for _ in range(num_locations_per_wh):
            zone = random.choice(zones)
            loc_type = 'PICK' if zone == 'PICK' else 'BULK' if zone == 'BULK' else random.choice(location_types)
            aisle = f"{random.randint(1, 40):02d}"
            bay = f"{random.randint(1, 50):02d}"
            level = f"{random.randint(1, 8):02d}"
            bin_code = f"{zone}-{aisle}-{bay}-{level}"
            
            loc_tuple = (loc_id, w_id, zone, aisle, bay, level, bin_code, loc_type)
            locations.append(loc_tuple)
            locations_by_wh[w_id].append(loc_tuple)
            loc_id += 1
            
    cur.executemany("INSERT INTO locations VALUES (?, ?, ?, ?, ?, ?, ?, ?)", locations)

    categories = ['Apparel', 'Footwear', 'Accessories', 'Packing Supplies']
    suppliers = ['Supplier A', 'Global Goods', 'EcoPack Logistics', 'Apex Apparel']
    items = []
    
    for i in range(1, num_items + 1):
        category = random.choice(categories)
        sku = f"{category[:3].upper()}-{10000 + i}"
        unit_cost = round(random.uniform(5.50, 150.00), 2)
        reorder_point = random.randint(10, 150)
        safety_stock = int(reorder_point * 1.5)
        supplier = random.choice(suppliers)
        items.append((i, sku, f"Item {sku}", category, unit_cost, reorder_point, safety_stock, supplier, 1))
        
    cur.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", items)

    print("Generating Inventory Data (This may take a second)...")
    inventory = []
    inv_id = 1
    snapshot_date = datetime.now().strftime('%Y-%m-%d')
    
    for item in items:
        item_id = item[0]
        reorder_point = item[5]
        
        for w_id in range(1, 4):
            # Fast O(1) random choice using our pre-bucketed dictionary
            wh_locations = locations_by_wh[w_id]
            loc = random.choice(wh_locations) if wh_locations else None
            loc_id = loc[0] if loc else None
            
            on_hand = random.randint(0, 500)
            allocated = random.randint(0, min(50, on_hand))
            available = on_hand - allocated
            inbound = random.choice([0, 0, 0, 50, 100, 250]) 
            status = 'CRITICAL' if on_hand == 0 else 'LOW' if on_hand < reorder_point else 'OVERSTOCK' if on_hand > 400 else 'OK'
            
            inventory.append((inv_id, snapshot_date, w_id, loc_id, item_id, on_hand, allocated, available, inbound, status))
            inv_id += 1
            
    cur.executemany("INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", inventory)

    print("Generating Orders and Order Lines...")
    regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West']
    priorities = ['Standard', 'Standard', 'Standard', 'Rush', 'VIP']
    order_statuses = ['Open', 'Released', 'Shipped', 'Shipped', 'Delayed', 'Backorder']
    
    orders = []
    order_lines = []
    order_line_id = 1
    
    for i in range(1, num_orders + 1):
        order_number = f"ORD-{100000 + i}"
        w_id = random.randint(1, 3)
        o_status = random.choice(order_statuses)
        days_ago = random.randint(0, 60)
        order_date = datetime.now() - timedelta(days=days_ago)
        promised_date = order_date + timedelta(days=random.choice([2, 3, 5]))
        
        actual_date = (order_date + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S') if o_status == 'Shipped' else None
        region = random.choice(regions)
        priority = random.choice(priorities)
        
        orders.append((i, order_number, w_id, order_date.strftime('%Y-%m-%d %H:%M:%S'), 
                       promised_date.strftime('%Y-%m-%d %H:%M:%S'), actual_date, region, priority, o_status))
        
        for _ in range(random.randint(1, 5)):
            item_id = random.randint(1, num_items)
            ordered_qty = random.randint(1, 15)
            
            if o_status == 'Shipped':
                shipped, backorder, l_status = ordered_qty, 0, 'Shipped'
            elif o_status == 'Backorder':
                shipped = random.randint(0, ordered_qty - 1)
                backorder = ordered_qty - shipped
                l_status = 'Backorder'
            else:
                shipped, backorder = 0, 0
                l_status = 'Open' if o_status in ('Open', 'Delayed') else 'Allocated'
                
            order_lines.append((order_line_id, i, item_id, ordered_qty, shipped, backorder, l_status))
            order_line_id += 1
            
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)
    cur.executemany("INSERT INTO order_lines VALUES (?, ?, ?, ?, ?, ?, ?)", order_lines)

    print("Generating Exception Logs...")
    exception_types = ['Low Stock', 'Delayed Shipment', 'Scanner Issue', 'Inventory Discrepancy', 'Damaged Goods', 'Cycle Count Variance']
    severities = ['Low', 'Medium', 'High', 'Critical']
    exception_statuses = ['Open', 'In Progress', 'Resolved', 'Resolved']
    
    exceptions = []
    for i in range(1, num_exceptions + 1):
        w_id = random.randint(1, 3)
        item_id = random.randint(1, num_items) if random.random() > 0.3 else None
        order_id = random.randint(1, num_orders) if random.random() > 0.5 else None
        
        e_type = random.choice(exception_types)
        severity = random.choice(severities)
        status = random.choice(exception_statuses)
        
        created_dt = datetime.now() - timedelta(days=random.randint(0, 30))
        resolved_dt = (created_dt + timedelta(hours=random.randint(1, 72))).strftime('%Y-%m-%d %H:%M:%S') if status == 'Resolved' else None
        notes = f"System generated {e_type} exception"
        
        exceptions.append((i, w_id, item_id, order_id, e_type, severity, 
                           created_dt.strftime('%Y-%m-%d %H:%M:%S'), resolved_dt, status, notes))

    cur.executemany("INSERT INTO exceptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", exceptions)

    conn.commit()
    conn.close()
    
    print(f"\n✅ Database successfully initialized at {DB_PATH}")
    print(f"   Generated: {len(warehouses)} warehouses, {len(locations)} locations, {num_items} items")
    print(f"   Generated: {len(inventory)} inventory records, {num_orders} orders ({len(order_lines)} lines)")
    print(f"   Generated: {num_exceptions} operational exceptions")

if __name__ == "__main__":
    setup_database()
