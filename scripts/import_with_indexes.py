#!/usr/bin/env python
"""
1. Create indexes for fast MATCH
2. Import Company → Product relations
"""
import json
import time
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

BATCH_SIZE = 5000

def read_jsonl(filepath):
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main():
    print("Connecting to Neo4j...", flush=True)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # Step 1: Create indexes
            print("\n[1/3] Creating indexes...", flush=True)
            
            indexes = [
                "CREATE INDEX company_name_idx IF NOT EXISTS FOR (c:Company) ON (c.name)",
                "CREATE INDEX product_name_idx IF NOT EXISTS FOR (p:Product) ON (p.name)",
                "CREATE INDEX industry_name_idx IF NOT EXISTS FOR (i:Industry) ON (i.name)",
            ]
            
            for idx_query in indexes:
                print(f"  Running: {idx_query}", flush=True)
                session.run(idx_query)
            
            print("  Indexes created! Waiting for them to be online...", flush=True)
            time.sleep(5)  # wait for indexes to be available
            
            # Step 2: Check if Company→Product relations already exist (from partial import)
            print("\n[2/3] Checking existing relations...", flush=True)
            result = session.run("MATCH ()-[r:HAS_PRODUCT]->() RETURN count(r) AS cnt")
            existing = result.single()['cnt']
            print(f"  Existing HAS_PRODUCT relations: {existing}", flush=True)
            
            if existing >= 68003:
                print("  All relations already imported! Done.", flush=True)
                return
            
            # Step 3: Import remaining relations
            print("\n[3/3] Importing Company → Product relations...", flush=True)
            comp_prod = read_jsonl('/Users/xinyuan/projects/financial_kg/data/company_product.json')
            print(f"  Loaded {len(comp_prod)} relations", flush=True)
            
            # Skip already imported (MATCH will handle dedup since we use CREATE not MERGE)
            # Actually, since the previous import may have partially succeeded, we need to be careful
            # Let's use MERGE to avoid duplicates
            print("  Using MERGE to avoid duplicates...", flush=True)
            
            start_time = time.time()
            for i in range(0, len(comp_prod), BATCH_SIZE):
                batch = comp_prod[i:i+BATCH_SIZE]
                query = """
                UNWIND $batch AS row
                MATCH (c:Company {name: row.company_name})
                MATCH (p:Product {name: row.product_name})
                MERGE (c)-[r:HAS_PRODUCT]->(p)
                SET r.rel_type = row.rel, r.product_type = row.product_type
                """
                session.run(query, batch=batch)
                done = min(i+BATCH_SIZE, len(comp_prod))
                elapsed = time.time() - start_time
                print(f"  Comp→Product: {done}/{len(comp_prod)} ({elapsed:.1f}s)", flush=True)

            # Verify
            result = session.run("MATCH ()-[r:HAS_PRODUCT]->() RETURN count(r) AS cnt")
            print(f"\n  Total HAS_PRODUCT relations: {result.single()['cnt']}", flush=True)

        print("\n" + "=" * 60, flush=True)
        print("✅ Import complete! Open http://localhost:7474 to visualize.", flush=True)

    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        raise
    finally:
        driver.close()

if __name__ == '__main__':
    main()
