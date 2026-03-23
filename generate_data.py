import sqlite3
import random
import uuid
from datetime import datetime, timedelta
import os

try:
    from faker import Faker
except ImportError:
    print("Please install faker: `uv pip install faker` or `pip install faker`")
    exit(1)

# ==============================================================================
# AI Warehouse Operations Assistant - Synthetic Data Generator
# ==============================================================================
# Now powered by `Faker` to guarantee hyper-realistic textual data (Suppliers, 
# Employee names, Tracking numbers) rather than sterile generated IDs. 
# We've also adopted the legacy 'wms_data_gen' time-series logic to simulate
# `labor_metrics` and `shipments`!
# ==============================================================================

DB_PATH = "data/warehouse.db"
fake = Faker()
Faker.seed(42)
random.seed(42)

def setup_database(
    num_items=2000,           
    num_locations_per_wh=2000,
    num_orders=10000,         
    num_exceptions=500        
):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Initializing Enhanced Database Schema...")
    cur.executescript("""
        DROP TABLE IF EXISTS labor_metrics;
        DROP TABLE IF EXISTS shipments;
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

        -- NEW: Labor Metrics Table to simulate picking operations
        CREATE TABLE labor_metrics (
            metric_id INTEGER PRIMARY KEY, 
            employee_name TEXT, 
            task_type TEXT, 
            warehouse_id INTEGER,
            units_processed INTEGER, 
            start_time TEXT, 
            end_time TEXT,
            error_count INTEGER,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        );

        -- NEW: Shipments Table linked directly to Carriers and Orders
        CREATE TABLE shipments (
            shipment_id INTEGER PRIMARY KEY, 
            tracking_number TEXT UNIQUE,
            order_id INTEGER, 
            carrier TEXT, 
            planned_date TEXT, 
            actual_date TEXT, 
            delay_flag INTEGER,
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

    # Use Faker for Suppliers and Item Names
    categories = ['Apparel', 'Footwear', 'Accessories', 'Packing Supplies']
    suppliers = [fake.company() for _ in range(20)]
    
    items = []
    for i in range(1, num_items + 1):
        category = random.choice(categories)
        sku = f"{category[:3].upper()}-{10000 + i}"
        item_name = f"{fake.catch_phrase().title()} {category}"
        unit_cost = round(random.uniform(5.50, 150.00), 2)
        reorder_point = random.randint(10, 150)
        safety_stock = int(reorder_point * 1.5)
        supplier = random.choice(suppliers)
        items.append((i, sku, item_name, category, unit_cost, reorder_point, safety_stock, supplier, 1))
        
    cur.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", items)

    print("Generating Inventory Data (This may take a second)...")
    inventory = []
    inv_id = 1
    snapshot_date = datetime.now().strftime('%Y-%m-%d')
    
    for item in items:
        item_id = item[0]
        reorder_point = item[5]
        for w_id in range(1, 4):
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

    print("Generating Orders, Order Lines, Shipments, and Labor Metrics...")
    regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West']
    priorities = ['Standard', 'Standard', 'Standard', 'Rush', 'VIP']
    order_statuses = ['Open', 'Released', 'Shipped', 'Shipped', 'Delayed', 'Backorder']
    carriers = ['UPS', 'FedEx', 'USPS', 'DHL', 'LaserShip']
    
    # Generate a fixed roster of 50 warehouse employees
    employees = [fake.name() for _ in range(50)]
    
    orders = []
    order_lines = []
    shipments = []
    labor_metrics = []
    
    order_line_id = 1
    shipment_id = 1
    metric_id = 1
    
    for i in range(1, num_orders + 1):
        order_number = f"ORD-{100000 + i}"
        w_id = random.randint(1, 3)
        o_status = random.choice(order_statuses)
        
        # Chronological logical flow
        days_ago = random.randint(0, 60)
        order_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        promised_date = order_date + timedelta(days=random.choice([2, 3, 5]))
        
        actual_date = None
        if o_status == 'Shipped':
            # Simulating picking time to create highly accurate 'labor_metrics' log
            picker = random.choice(employees)
            start_pick = order_date + timedelta(hours=random.randint(1, 12))
            
            total_ordered_qty = 0
            lines_to_create = random.randint(1, 5)
            
            for _ in range(lines_to_create):
                item_id = random.randint(1, num_items)
                ordered_qty = random.randint(1, 15)
                total_ordered_qty += ordered_qty
                
                order_lines.append((order_line_id, i, item_id, ordered_qty, ordered_qty, 0, 'Shipped'))
                order_line_id += 1
                
            end_pick = start_pick + timedelta(minutes=random.randint(5, 45) * lines_to_create)
            
            # Very low error rate unless it's a rush order
            errors = 1 if (random.random() < 0.05) else 0 
            
            labor_metrics.append((metric_id, picker, "Picking", w_id, total_ordered_qty, start_pick.strftime('%Y-%m-%d %H:%M:%S'), end_pick.strftime('%Y-%m-%d %H:%M:%S'), errors))
            metric_id += 1
            
            # Create Shipment
            actual_date = (end_pick + timedelta(hours=random.randint(2, 24))).strftime('%Y-%m-%d %H:%M:%S')
            delay_flag = 1 if datetime.strptime(actual_date, '%Y-%m-%d %H:%M:%S') > promised_date else 0
            
            carrier = random.choice(carriers)
            tracking = fake.unique.bothify(text='1Z##################' if carrier == 'UPS' else '############')
            shipments.append((shipment_id, tracking, i, carrier, promised_date.strftime('%Y-%m-%d %H:%M:%S'), actual_date, delay_flag))
            shipment_id += 1

        else:
            # Not shipped yet, just generate lines
            for _ in range(random.randint(1, 5)):
                item_id = random.randint(1, num_items)
                ordered_qty = random.randint(1, 15)
                
                if o_status == 'Backorder':
                    shipped = random.randint(0, ordered_qty - 1)
                    backorder = ordered_qty - shipped
                    l_status = 'Backorder'
                else:
                    shipped, backorder = 0, 0
                    l_status = 'Open' if o_status in ('Open', 'Delayed') else 'Allocated'
                    
                order_lines.append((order_line_id, i, item_id, ordered_qty, shipped, backorder, l_status))
                order_line_id += 1

        
        region = random.choice(regions)
        priority = random.choice(priorities)
        orders.append((i, order_number, w_id, order_date.strftime('%Y-%m-%d %H:%M:%S'), 
                       promised_date.strftime('%Y-%m-%d %H:%M:%S'), actual_date, region, priority, o_status))
                       
            
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)
    cur.executemany("INSERT INTO order_lines VALUES (?, ?, ?, ?, ?, ?, ?)", order_lines)
    cur.executemany("INSERT INTO shipments VALUES (?, ?, ?, ?, ?, ?, ?)", shipments)
    cur.executemany("INSERT INTO labor_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", labor_metrics)

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
    print(f"   Generated: {len(shipments)} active shipments and {len(labor_metrics)} labor metrics")
    print(f"   Generated: {num_exceptions} operational exceptions")

if __name__ == "__main__":
    setup_database()
